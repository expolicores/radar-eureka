"""SECOP I stages for the national EN-01 runner. Opt-in via --include-secop1.

Stage 1 (runner, habitual session): inventory through the existing provider endpoint and a
persistent queue of governing PDFs. Nothing is downloaded here.
Stage 3 (offline): extraction and classification from verified receipts only, with a
selective multi-pass OCR plan for scanned governing PDFs. No provider or SECOP request.
Stage 2 (acquisition) lives in eureka_nacional_secop1_acquire.py.
"""

import hashlib
import json
import re
import time
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

from eureka_nacional_cdp_stream import DOCUMENT_BYTES
from eureka_nacional_experience import (
    classify_experience,
    document_priority,
    normalized,
)
from eureka_nacional_secop1_inventory import CONSTANCIA, normalize_document
from licitaciones_cdp_runtime import DOCUMENT_ENDPOINT
from spike_licitaciones_info import SpikeError

QUEUE_FILE = "secop1_queue.json"
RECEIPTS_FILE = "download_receipts.json"
MAX_SECOP1_PROCESSES = 5
MAX_INVENTORY_PAGES = 10
SECOP1_HEADERS = ["nombre", "tipo", "tamano", "fecha publicacion del documento", "documento"]
OPENER = re.compile(r"""^\s*window\.openDocumentoSecop1\(\s*"([^"\\<>]{1,512})"\s*\)\s*;?\s*$""")
EXTENSION_ICON = re.compile(r"/img/extensiones/([a-z0-9]{1,8})\.svg")
DISPLAYED_SIZE = re.compile(r"^\s*([0-9]{1,6}(?:[.,][0-9]{1,3})?)\s*(KB|MB|GB|B)\s*$", re.I)
GOVERNING_ROLES = {"primary", "amendment"}


def _plain(text):
    folded = unicodedata.normalize("NFD", str(text or ""))
    return "".join(c for c in folded if unicodedata.category(c) != "Mn").casefold().strip()


class _Cell(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.onclicks, self.images, self.text = [], [], []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a":
            self.onclicks.append(values.get("onclick") or "")
        elif tag == "img":
            self.images.append(values.get("src") or "")

    def handle_data(self, data):
        self.text.append(data)


def displayed_size_bytes(text):
    """Approximate size shown by the provider (binary units); evidence, never a limit check."""
    match = DISPLAYED_SIZE.match("".join(_Cell(text).text))
    if not match:
        return None
    factor = {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3}[match[2].lower()]
    return round(float(match[1].replace(",", ".")) * factor)


def phase_is_explicit_null(row):
    """idUltimaFase may be null only when the provider record states it explicitly."""
    return isinstance(row, dict) and "idUltimaFase" in row and row["idUltimaFase"] is None


def constancia_of(process):
    identity = str(process.get("source_identity") or "")
    constancia = identity.removeprefix("secop1:")
    return (
        constancia if identity.startswith("secop1:") and CONSTANCIA.fullmatch(constancia) else None
    )


def inventory_ready(process):
    """Stage-1 eligibility of a SECOP I process for one inventory request."""
    keys = process.get("inventory_keys") or {}
    phase_ok = bool(keys.get("idUltimaFase")) or (
        keys.get("idUltimaFase") is None and process.get("phase_explicit_null") is True
    )
    return bool(
        process.get("source") == "secop1"
        and constancia_of(process)
        and keys.get("idContrato")
        and keys.get("id_fuente_contract")
        and phase_ok
    )


def parse_secop1_page(body, constancia):
    """Parse one provider inventory page for SECOP I. Unknown contracts raise SpikeError."""
    if not isinstance(body, dict) or body.get("status") != 1:
        raise SpikeError("Estado documental SECOP I desconocido.")
    table = body.get("documentos")
    if table == []:
        return [], [], body.get("cantidad")
    if not isinstance(table, dict) or [_plain(h) for h in table.get("encabezados") or []] != (
        SECOP1_HEADERS
    ):
        raise SpikeError("Contrato de tabla documental SECOP I desconocido.")
    rows = table.get("campos")
    if not isinstance(rows, list):
        raise SpikeError("Filas documentales SECOP I desconocidas.")
    documents, issues = [], []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, list) or len(row) != 5 or not all(isinstance(c, str) for c in row):
            issues.append({"row": index, "code": "invalid_row"})
            continue
        link, icon = _Cell(row[4]), _Cell(row[1])
        opener = OPENER.match(link.onclicks[0]) if len(link.onclicks) == 1 else None
        extension = EXTENSION_ICON.fullmatch(icon.images[0]) if len(icon.images) == 1 else None
        if not opener or not extension:
            issues.append({"row": index, "code": "ambiguous_document_control"})
            continue
        name = "".join(_Cell(row[0]).text).strip()
        path = opener[1]
        try:
            document = normalize_document(
                {
                    "name": name,
                    "extension": extension[1],
                    "relative_path": path,
                    "size_bytes": None,
                },
                constancia,
            )
        except ValueError as error:
            issues.append({"row": index, "code": str(error)})
            continue
        document.update(
            relative_path=path,
            displayed_size="".join(_Cell(row[2]).text).strip()[:20],
            displayed_size_bytes=displayed_size_bytes(row[2]),
            url=None,
            status="not_selected",
        )
        documents.append(document)
    return documents, issues, body.get("cantidad")


def fetch_secop1_inventory(client, process, *, max_pages=MAX_INVENTORY_PAGES):
    """One inventory per process through the existing endpoint; paginates like SECOP II
    but stops as soon as the provider's declared count is reached."""
    constancia = constancia_of(process)
    if not inventory_ready(process):
        raise SpikeError("Claves documentales SECOP I no verificadas.")
    keys = process["inventory_keys"]
    payload = {key: keys.get(key) for key in ("idContrato", "id_fuente_contract", "idUltimaFase")}
    documents, issues, signatures = {}, [], set()
    for page in range(1, max_pages + 1):
        rows, page_issues, declared = parse_secop1_page(
            client.post(DOCUMENT_ENDPOINT, {**payload, "page": page}), constancia
        )
        issues.extend({"page": page, **issue} for issue in page_issues)
        if not rows and not page_issues:
            return list(documents.values()), issues, declared
        signature = tuple(doc["document_id"] for doc in rows)
        if signature in signatures:
            raise SpikeError("Pagina documental SECOP I repetida; inventario incompleto.")
        signatures.add(signature)
        for document in rows:
            documents[document["document_id"]] = document
        if isinstance(declared, int) and len(documents) + len(issues) >= declared:
            return list(documents.values()), issues, declared
    if max_pages < MAX_INVENTORY_PAGES:
        raise SpikeError("secop1_inventory_page_budget")
    raise SpikeError("Limite de paginas SECOP I; inventario incompleto.")


def governing_document(documents):
    """The single governing PDF to queue, by title role and the existing ranking."""
    candidates = [
        doc
        for doc in documents
        if doc["extension"] == "pdf"
        and (doc["role"] in GOVERNING_ROLES or doc.get("role_hint") == "primary")
    ]
    candidates.sort(key=lambda doc: document_priority(doc["name"], doc["role"], doc["role_hint"]))
    return candidates[0] if candidates else None


def acquisition_size_check(document):
    """Admission of a governing PDF to the automatic acquisition queue by displayed size.

    The provider shows a rounded binary size (MB = MiB). Only a displayed size strictly above
    the download limit excludes the document. An unknown or unparseable size is never
    invented: the document is admitted and flagged, and the strict limit on received bytes
    still applies during streaming. Commercial eligibility and experience status are untouched.
    """
    shown = document.get("displayed_size_bytes")
    if not isinstance(shown, int) or shown <= 0:
        return None, False
    if shown > DOCUMENT_BYTES:
        return "displayed_size_over_limit", True
    return None, True


def inventory_digest(documents):
    rows = sorted((d["document_id"], d["name"], d["extension"]) for d in documents)
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode("utf-8")).hexdigest()


def analyze_secop1_inventory(client, process, metrics, documents, *, max_pages=MAX_INVENTORY_PAGES):
    """Stage 1 for one SECOP I process: inventory and at most one queued governing PDF."""
    found, issues, declared = fetch_secop1_inventory(client, process, max_pages=max_pages)
    metrics["secop1_inventories"] += 1
    documents.extend(found)
    for document in found:
        document["selection"] = "document_limit"
    item = None
    if issues:
        stop = "secop1_inventory_issues"
    elif not found:
        stop = "empty_inventory"
    elif (governing := governing_document(found)) is None:
        stop = "governing_document_not_identified"
    elif (size_reason := acquisition_size_check(governing)[0]) is not None:
        governing.update(selection=size_reason, status="excluded_from_acquisition")
        stop = f"governing_{size_reason}"
    else:
        governing.update(selection="queued", status="queued_for_acquisition")
        item = {
            "process_reference": process["process_reference"],
            "constancia": constancia_of(process),
            "document_id": governing["document_id"],
            "name": governing["name"],
            "extension": governing["extension"],
            "relative_path": governing["relative_path"],
            "role": governing["role"],
            "role_hint": governing.get("role_hint"),
            "displayed_size": governing.get("displayed_size"),
            "displayed_size_bytes": governing.get("displayed_size_bytes"),
            "displayed_size_known": acquisition_size_check(governing)[1],
            "commercial_priority": process.get("commercial_priority"),
            "inventory_declared_count": declared,
            "inventory_sha256": inventory_digest(found),
        }
        metrics["secop1_queued"] += 1
        stop = "secop1_queued_for_acquisition"
    return stop, item, [{"stage": "inventory", **issue} for issue in issues]


def write_queue(output, items, run_id):
    queue = {
        "run_id": run_id,
        "source": "secop1",
        "max_posts": min(MAX_SECOP1_PROCESSES, len(items)),
        "items": items,
    }
    queue["batch_sha256"] = batch_digest(queue)
    (output / QUEUE_FILE).write_text(
        json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return queue


def batch_digest(queue):
    """Digest the operator confirms: exactly these documents, at most max_posts POSTs."""
    core = {
        "run_id": queue["run_id"],
        "max_posts": queue["max_posts"],
        "items": [
            [item["process_reference"], item["document_id"], item["relative_path"]]
            for item in queue["items"]
        ],
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()


def load_queue(output):
    queue = json.loads((output / QUEUE_FILE).read_text(encoding="utf-8"))
    if queue.get("batch_sha256") != batch_digest(queue) or queue["max_posts"] > (
        MAX_SECOP1_PROCESSES
    ):
        raise SpikeError("Cola SECOP I alterada o fuera de limites.")
    for item in queue["items"]:
        if not CONSTANCIA.fullmatch(item["constancia"]) or not item["document_id"].startswith(
            f"secop1:{item['constancia']}:"
        ):
            raise SpikeError("Identidad documental SECOP I invalida en la cola.")
    return queue


# ---------------------------------------------------------------- stage 1 recovery

RECOVERY_PREFIX = "en01-secop1inv_"


def recover_secop1_inventories(client, source, output, constancias, *, is_fatal):
    """Inventory only SECOP I processes already selected in `source`, limited to an explicit
    allowlist of constancias. No feed, no discovery, no commercial re-filtering, no downloads.

    The caller bounds `client` to one request per constancia; pagination beyond that budget
    stops the recovery. `is_fatal(error)` decides budget/session errors that stop the loop.
    """
    raw = (source / "processes.json").read_bytes()
    discovery = json.loads(raw.decode("utf-8"))
    selected = [
        p
        for p in discovery["processes"]
        if p.get("source") == "secop1" and p.get("sampled") and p.get("excluded_reason") is None
    ]
    by_constancia = {constancia_of(p): p for p in selected}
    if len(set(constancias)) != len(constancias) or any(
        c not in by_constancia for c in constancias
    ):
        raise SpikeError("Constancias fuera de la seleccion persistida.")
    processes = [by_constancia[c] for c in constancias]
    metrics = {"secop1_inventories": 0, "secop1_queued": 0}
    inventories, errors, items, outcomes = [], [], [], []
    stopped = None
    for process in processes:
        reference = process["process_reference"]
        documents, process_errors = [], []
        if stopped is not None:
            stop = f"not_attempted_after_{stopped}"
        else:
            try:
                # One inventory request per authorized process; never another's credit.
                stop, item, issues = analyze_secop1_inventory(
                    client, process, metrics, documents, max_pages=1
                )
                process_errors.extend(issues)
                if item:
                    items.append(item)
            except SpikeError as error:
                code = getattr(error, "code", None) or str(error)
                if is_fatal(error):
                    stopped = code
                    stop = code
                else:
                    stop = "inventory_failed"
                process_errors.append({"stage": "inventory", "code": code})
        inventories.append({"process_reference": reference, "documents": documents})
        outcomes.append(
            {
                "process_reference": reference,
                "constancia": constancia_of(process),
                "entity_name": process.get("entity_name"),
                "department": process.get("department"),
                "inventory_documents": len(documents),
                "queued": any(i["process_reference"] == reference for i in items),
                "stop_reason": stop,
            }
        )
        errors.extend({"process_reference": reference, **e} for e in process_errors)
    queue = write_queue(output, items, output.name)
    summary = {
        "run_id": output.name,
        "scope": "secop1_inventory_recovery",
        "recovered_from": source.name,
        "source_processes_sha256": hashlib.sha256(raw).hexdigest(),
        "authorized_constancias": list(constancias),
        "request_credits_used": client.requests,
        "request_credit_limit": client.request_limit,
        "feed_requests": 0,
        "downloads": 0,
        "posts": 0,
        "stopped_by": stopped,
        **metrics,
        "batch_sha256": queue["batch_sha256"],
        "processes": outcomes,
    }
    recovered = {
        "scope": "secop1_inventory_recovery",
        "recovered_from": source.name,
        "processes": processes,
    }
    for name, data in (
        ("processes.json", recovered),
        ("documents.json", inventories),
        ("errors.json", errors),
        ("metrics.json", summary),
    ):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    return summary


# ---------------------------------------------------------------- offline queue rebuild

REBUILD_FILE = "secop1_queue_rebuild.json"


def rebuild_queue(run):
    """Re-derive the queue from the inventories already saved in `run`, with the current
    admission rules. No request of any kind. The previous queue is archived, never deleted;
    processes and inventories are not modified."""
    previous = load_queue(run)
    inventories = {
        case["process_reference"]: case["documents"]
        for case in json.loads((run / "documents.json").read_text(encoding="utf-8"))
    }
    processes = {
        p["process_reference"]: p
        for p in json.loads((run / "processes.json").read_text(encoding="utf-8"))["processes"]
    }
    items, decisions = [], []
    for old in previous["items"]:
        reference = old["process_reference"]
        documents = inventories.get(reference, [])
        governing = governing_document(documents)
        if governing is None or governing["document_id"] != old["document_id"]:
            raise SpikeError("La cola guardada no coincide con su inventario.")
        reason, known = acquisition_size_check(governing)
        decisions.append(
            {
                "process_reference": reference,
                "constancia": old["constancia"],
                "document_id": old["document_id"],
                "name": old["name"],
                "displayed_size": governing.get("displayed_size"),
                "displayed_size_bytes": governing.get("displayed_size_bytes"),
                "decision": reason or "queued",
                "commercial_priority": processes.get(reference, {}).get("commercial_priority"),
            }
        )
        if reason is None:
            items.append({**old, "displayed_size_known": known})
    archive = run / f"secop1_queue.superseded-{previous['batch_sha256'][:16]}.json"
    if not archive.exists():
        archive.write_bytes((run / QUEUE_FILE).read_bytes())
    queue = write_queue(run, items, previous["run_id"])
    record = {
        "previous_batch_sha256": previous["batch_sha256"],
        "batch_sha256": queue["batch_sha256"],
        "rule": "displayed_size_over_limit",
        "document_max_bytes": DOCUMENT_BYTES,
        "network_requests": 0,
        "decisions": decisions,
    }
    (run / REBUILD_FILE).write_text(json.dumps(record, ensure_ascii=False, indent=2), "utf-8")
    return queue, record


# ---------------------------------------------------------------- OCR plan (stage 3)

OCR_TOPIC = re.compile(r"\b(?:experiencia|requisitos? habilitantes?|acreditacion)\b")
PAGE_REFERENCE = re.compile(r"\b(?:paginas?|pags?\.?|folios?)\s+(\d{1,4})\b")
INDEX_ENTRY = re.compile(r"(?:\.\s*){3,}(\d{1,4})\s*$")
GOVERNING_OCR_PAGES = 12
RUN_OCR_PAGES = 60
RUN_OCR_SECONDS = 360
PASS_PAGES = 2  # keeps each pass within the existing 14 s OCR document timeout
INITIAL_WINDOW = (1, 2, 3)


class OcrBudget:
    def __init__(self, pages=RUN_OCR_PAGES, seconds=RUN_OCR_SECONDS):
        self.pages_left = pages
        self.deadline = time.monotonic() + seconds
        self.limits = {"pages": pages, "seconds": seconds}

    def take(self, wanted):
        if time.monotonic() >= self.deadline:
            return 0
        return max(0, min(wanted, self.pages_left))

    def spend(self, pages):
        self.pages_left -= pages


def ocr_targets(fragments, total_pages):
    """Pages that the text itself points to for habilitation or experience."""
    ranked = {}

    def prefer(page, rank):
        if 1 <= page <= total_pages and rank < ranked.get(page, 10):
            ranked[page] = rank

    for fragment in fragments:
        page = fragment.source_locator.get("page_number") or 0
        for raw in fragment.text.splitlines():
            line = normalized(raw).strip()
            if not OCR_TOPIC.search(line):
                continue
            if target := PAGE_REFERENCE.search(line) or INDEX_ENTRY.search(line):
                prefer(int(target[1]), 0)
                prefer(int(target[1]) + 1, 1)
            elif len(line) <= 110 and page:
                # A heading: its section usually continues on the following pages.
                prefer(page + 1, 1)
                prefer(page + 2, 2)
    return [page for page, _ in sorted(ranked.items(), key=lambda item: (item[1], item[0]))]


def next_pass(tried, candidates, targets, remaining):
    """Only pages without usable text are planned: located ones first, then the initial
    window, then the remaining candidates in order. Tried pages are never planned again."""
    pool = [page for page in sorted(candidates) if page not in tried]
    order = [*targets, *INITIAL_WINDOW, *pool]
    plan = []
    for page in order:
        if page in pool and page not in plan:
            plan.append(page)
        if len(plan) == min(PASS_PAGES, remaining):
            break
    return plan


def merge_pass(merged, entry, pass_number):
    """Accumulate page coverage across passes; a page keeps its first successful text."""
    pages = {f.source_locator.get("page_number") for f in merged["fragments"]}
    new = [f for f in entry["fragments"] if f.source_locator.get("page_number") not in pages]
    merged["fragments"] = sorted(
        merged["fragments"] + new, key=lambda f: f.source_locator.get("page_number") or 0
    )
    merged["seen"] |= set(entry["pages_seen"])
    merged["ocr_pages"] |= set(entry["ocr_pages"])
    merged["ocr_success"] |= set(entry["ocr_success_pages"])
    merged["extraction_seconds"] += entry["extraction_seconds"] or 0
    merged["passes"].append(
        {
            "pass": pass_number,
            "requested": entry.get("ocr_plan", []),
            "ocr_success": entry["ocr_success_pages"],
            "status": entry["status"],
            "error_code": entry.get("error_code"),
        }
    )


def extract_with_ocr_plan(
    extract,
    document,
    stored,
    storage,
    settings,
    entry,
    budget,
    *,
    per_document=GOVERNING_OCR_PAGES,
    classify=classify_experience,
):
    """Multi-pass selective OCR over the existing extractor. Partial coverage stays partial:
    pending pages keep the document incomplete, so silence is never read as absence.

    Pass 0 reads native text only (no OCR budget) to learn which pages lack usable text;
    every later pass plans exclusively among those pages.
    """
    base = dict(entry)
    merged = {
        "fragments": [],
        "seen": set(),
        "ocr_pages": set(),
        "ocr_success": set(),
        "extraction_seconds": 0.0,
        "passes": [],
    }
    first, candidates, skipped, allowance, stop = None, set(), set(), per_document, None
    while stop is None:
        if first is None:
            plan = []
        else:
            granted = budget.take(min(PASS_PAGES, allowance))
            if not granted:
                stop = "document_ocr_budget" if allowance <= 0 else "run_ocr_budget"
                break
            tried = merged["seen"] | merged["ocr_pages"] | skipped
            targets = ocr_targets(merged["fragments"], first["total_pages"])
            plan = next_pass(tried, candidates, targets, granted)
            if not plan:
                stop = "pages_exhausted"
                break
        current = dict(base)
        extract(
            document,
            stored,
            storage,
            settings,
            current,
            ocr_pages=max(1, len(plan)),
            page_plan=plan,
        )
        current["ocr_plan"] = plan
        spent = len(current["ocr_pages"])
        budget.spend(spent)
        allowance -= spent
        # A planned page the extractor did not process is never planned again.
        skipped |= set(plan) - set(current["ocr_pages"])
        merge_pass(merged, current, len(merged["passes"]) + 1)
        if first is None:
            first = current
            if current.get("error_code") or not current["total_pages"]:
                stop = "extraction_failed" if current.get("error_code") else "no_pages"
                break
            candidates = set(range(1, first["total_pages"] + 1)) - merged["seen"]
        if not set(range(1, first["total_pages"] + 1)) - merged["seen"]:
            stop = "document_complete"
        elif current.get("error_code"):
            stop = "ocr_pass_failed"
        else:
            probe = {**first, "fragments": merged["fragments"], "complete": False}
            outcome = classify([probe])
            if outcome["status"] == "experience_required" or (
                outcome["review_category"] == "explicit_requirement"
            ):
                stop = "explicit_requirement_found"
    total = first["total_pages"] if first else 0
    pending = sorted(set(range(1, total + 1)) - merged["seen"])
    complete = bool(total) and not pending and not (first or {}).get("error_code")
    entry.update(first or {})
    entry.update(
        fragments=merged["fragments"],
        pages_seen=sorted(merged["seen"]),
        ocr_pages=sorted(merged["ocr_pages"]),
        ocr_success_pages=sorted(merged["ocr_success"]),
        pending_pages=pending,
        content_complete=complete,
        complete=complete and not entry.get("role_hint"),
        extraction_seconds=round(merged["extraction_seconds"], 3),
        ocr_passes=merged["passes"],
        ocr_candidates=sorted(candidates),
        ocr_unprocessed_planned=sorted(skipped),
        ocr_stop_reason=stop,
        ocr_policy={
            "per_document": per_document,
            "pass_pages": PASS_PAGES,
            "run_limits": budget.limits,
        },
    )
    entry.pop("ocr_plan", None)
    return entry


def load_receipts(output):
    path = output / RECEIPTS_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def run_dir_name(value):
    if not re.fullmatch(r"en01-[a-z0-9_]+", value or ""):
        raise ValueError("Nombre de corrida invalido.")
    return value


def evidence_pages(classification):
    pages = {}
    for item in classification.get("evidence", []):
        pages.setdefault(item.get("document_id"), set()).add(item.get("page"))
    return {key: sorted(p for p in value if p) for key, value in pages.items()}


def ensure_inside(root: Path, path: Path):
    if path.resolve() != path or not path.is_relative_to(root):
        raise ValueError("Ruta fuera del almacenamiento experimental.")
    return path


# ---------------------------------------------------------------- stage 3: offline resume


def resume_secop1(
    source, output, *, settings, budget, runner, per_document=GOVERNING_OCR_PAGES, only=None
):
    """Extract and classify queued SECOP I processes from verified receipts only.

    No provider, feed, inventory or SECOP request: documents without a receipt stay pending.
    Results are written to a new directory; the source run is never modified.
    """
    started = time.monotonic()
    queue = load_queue(source)
    receipts = load_receipts(source)
    inventories = {
        case["process_reference"]: case["documents"]
        for case in json.loads((source / "documents.json").read_text(encoding="utf-8"))
    }
    processes = {
        p["process_reference"]: p
        for p in json.loads((source / "processes.json").read_text(encoding="utf-8"))["processes"]
    }
    storage = runner.spike.LocalBinaryStorage(source / "binaries")
    results, cases, errors = [], [], []
    metrics = {
        "secop1_processes": 0,
        "secop1_receipts_used": 0,
        "secop1_download_pending": 0,
        "secop1_pages_reported": 0,
        "secop1_pages_seen": 0,
        "secop1_ocr_pages": 0,
        "secop1_pending_pages": 0,
        "secop1_extraction_seconds": 0.0,
        "secop1_receipt_rejected": 0,
    }
    selected = [i for i in queue["items"] if only is None or i["constancia"] in only]
    if only is not None and {i["constancia"] for i in selected} != set(only):
        raise SpikeError("Constancia fuera de la cola SECOP I.")
    for item in selected:
        reference = item["process_reference"]
        documents = [dict(doc) for doc in inventories.get(reference, [])]
        metrics["secop1_processes"] += 1
        stop = "download_pending"
        for document in documents:
            if document["document_id"] != item["document_id"]:
                continue
            record = receipts.get(f"{item['document_id']}:{item['extension']}")
            if not record:
                metrics["secop1_download_pending"] += 1
                document["status"] = "download_pending"
                break
            spike_document = runner.spike.SpikeDocument(
                item["name"], item["extension"], "", item["document_id"]
            )
            try:
                stored = runner.StoredBinary(**record)
                runner.verify_document_type(storage, stored, spike_document, runner.DOCUMENT_BYTES)
            except (runner.AcquisitionError, TypeError, OSError) as error:
                metrics["secop1_receipt_rejected"] += 1
                document["status"] = "receipt_rejected"
                errors.append(
                    {
                        "process_reference": reference,
                        "stage": "receipt",
                        "code": getattr(error, "code", type(error).__name__),
                    }
                )
                stop = "receipt_rejected"
                break
            metrics["secop1_receipts_used"] += 1
            document["sha256"] = stored.sha256
            extract_with_ocr_plan(
                runner.extract_document,
                spike_document,
                stored,
                storage,
                settings,
                document,
                budget,
                per_document=per_document,
            )
            metrics["secop1_pages_reported"] += document["total_pages"]
            metrics["secop1_pages_seen"] += len(document["pages_seen"])
            metrics["secop1_ocr_pages"] += len(document["ocr_pages"])
            metrics["secop1_pending_pages"] += len(document["pending_pages"])
            metrics["secop1_extraction_seconds"] += document["extraction_seconds"]
            stop = f"ocr_{document['ocr_stop_reason']}"
            break
        classification = classify_experience(documents, inventory_complete=bool(documents))
        for document in documents:
            document.pop("fragments", None)
        process = processes.get(reference, {})
        cases.append({"process_reference": reference, "documents": documents})
        results.append(
            {
                "run_id": output.name,
                "source_run": source.name,
                "source": "secop1",
                "process_reference": reference,
                "constancia": item["constancia"],
                "department": process.get("department"),
                "validity_status": process.get("validity_status"),
                "commercial_category": process.get("primary_category"),
                "commercial_priority": process.get("commercial_priority"),
                "document_stop_reason": stop,
                "evidence_pages_by_document": evidence_pages(classification),
                **classification,
            }
        )
    statuses = {}
    for result in results:
        statuses[result["status"]] = statuses.get(result["status"], 0) + 1
    summary = {
        "run_id": output.name,
        "source_run": source.name,
        "source": "secop1",
        "batch_sha256": queue["batch_sha256"],
        "only_constancias": sorted(only) if only is not None else None,
        "network_requests": 0,
        "ai_calls": 0,
        "ocr_budget": {**budget.limits, "pages_left": budget.pages_left},
        "per_document_ocr_pages": per_document,
        "classification": statuses,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        **{k: round(v, 3) if isinstance(v, float) else v for k, v in metrics.items()},
    }
    for name, data in (
        ("documents.json", cases),
        ("experience_requirements.json", results),
        ("review_queue.json", sorted(results, key=lambda r: r["review_priority"])),
        ("metrics.json", summary),
        ("errors.json", errors),
    ):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    return summary


def main(argv=None):
    import argparse

    import eureka_nacional_en01 as runner

    parser = argparse.ArgumentParser(description="EN-01 SECOP I etapa 3: reanudacion offline.")
    parser.add_argument("run", help="Corrida de la etapa 1 (en01-...).")
    parser.add_argument(
        "--rebuild-queue",
        action="store_true",
        help="Regenerar la cola desde los inventarios guardados, sin peticiones.",
    )
    parser.add_argument(
        "--only-constancia",
        action="append",
        metavar="CONSTANCIA",
        help="Reevaluar solo estas constancias de la cola, en un directorio propio.",
    )
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--tessdata", type=Path)
    parser.add_argument(
        "--governing-ocr-pages",
        type=int,
        choices=range(1, GOVERNING_OCR_PAGES + 1),
        default=GOVERNING_OCR_PAGES,
    )
    args = parser.parse_args(argv)
    try:
        root = runner.OUTPUT_ROOT
        source = ensure_inside(root, root / run_dir_name(args.run))
        if args.rebuild_queue:
            if (source / "secop1_attempts").exists():
                print("EN-01 SECOP I: el lote ya tiene intentos; no se regenera.")
                return 1
            queue, record = rebuild_queue(source)
            print(
                json.dumps(
                    {
                        "batch_sha256": queue["batch_sha256"],
                        "previous_batch_sha256": record["previous_batch_sha256"],
                        "max_posts": queue["max_posts"],
                        "decisions": [
                            [d["constancia"], d["decision"]] for d in record["decisions"]
                        ],
                    }
                )
            )
            return 0
        only = args.only_constancia
        if only and not all(CONSTANCIA.fullmatch(c) for c in only):
            raise ValueError("Constancia invalida.")
        suffix = "_" + "_".join(sorted(c.replace("-", "") for c in only)) if only else ""
        output = ensure_inside(root, root / f"en01-secop1_{args.run[5:]}{suffix}")
        if (output / "metrics.json").exists():
            print("EN-01 SECOP I: la reanudacion ya existe; no se sobrescribe.")
            return 1
        output.mkdir(exist_ok=True)
        settings = runner.settings_for_run(output, args.tesseract, args.tessdata, PASS_PAGES)
        summary = resume_secop1(
            source,
            output,
            settings=settings,
            budget=OcrBudget(),
            runner=runner,
            per_document=args.governing_ocr_pages,
            only=only,
        )
    except (OSError, ValueError, SpikeError) as error:
        print(f"EN-01 SECOP I: {type(error).__name__}")
        return 1
    print(json.dumps({"output": str(output), "classification": summary["classification"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
