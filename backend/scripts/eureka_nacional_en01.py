"""EN-01: bounded national SECOP II supply sampling with local, deterministic evidence."""

import argparse
import hashlib
import json
import re
import tempfile
import time
from collections import Counter, deque
from itertools import islice
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import eureka_nacional_cdp_stream as streaming
import spike_licitaciones_info as spike
from eureka_nacional_commercial import (
    DEFAULT_PROFILE,
    assess_commercial,
    commercial_metrics,
    fraction,
    load_commercial_profile,
    parse_unspsc,
    plain,
    selection_rank,
)
from eureka_nacional_experience import (
    ASSERTION_TYPES,
    NEG,
    REQ,
    STATUSES,
    classify_experience,
    document_cover_metadata,
    document_priority,
    document_role,
    document_role_hint,
)
from licitaciones_candidate_contracts import CandidateProcess
from licitaciones_cdp_runtime import (
    CandidateError,
    PageClient,
    check_session,
    connect_browser,
    fetch_inventory,
    find_page,
    validate_cdp_url,
    validate_discovery,
    write_json,
)
from licitaciones_freshness import apply_freshness, local_now
from licitaciones_sources import document_capable, process_identity, source_kind
from licitaciones_validity import apply_validity

from public_procurement.documents.domain.document import AcquisitionError, StoredBinary
from public_procurement.licitaciones_cdp.configuration import (
    ProfileConfigurationError,
    resolve_profile_id,
)

DISCOVERY_PAGE_SIZE = 30
GEOGRAPHY_SOURCE = "Licitaciones.info"
NATIONAL_LOCATION_COUNT = 1130
DEFAULT_GEOGRAPHY = Path(__file__).with_name(
    "eureka_nacional_geography(from_licitaciones_info).v1.json"
)
OCR_PER_DOCUMENT = 2
REQUEST_CREDITS = 60
DURATION_SECONDS = 360
EXPLORATORY_PROCESSES = 15
EXPLORATORY_DISCOVERY_PAGES = 8
EXPLORATORY_DOCUMENTS = 24
EXPLORATORY_PER_PROCESS = 3
EXPLORATORY_REQUEST_CREDITS = 200
EXPLORATORY_DURATION_SECONDS = 720
DEPRIORITIZED_SAMPLE_SIZE = 3
FAVORABLE_RESERVE = 4
START_EXTRACTION_MARGIN = 50
MIB = 1024 * 1024
DOCUMENT_BYTES = streaming.DOCUMENT_BYTES
MAX_GOVERNING_PDF_MIB = 16
OUTPUT_ROOT = spike.ROOT.parent / ".local" / "eureka-nacional-spike"


class BudgetReached(spike.SpikeError):
    pass


class SmokeClient(PageClient):
    def __init__(self, page, profile_id, deadline, *, request_limit=REQUEST_CREDITS):
        super().__init__(page, profile_id, lambda _event: None)
        self.deadline = deadline
        self.request_limit = request_limit

    def reserve(self, count=1):
        if time.monotonic() + 25 > self.deadline:
            raise BudgetReached("duration_budget")
        if self.requests + count > self.request_limit:
            raise BudgetReached("request_budget")
        super().reserve(count)


def safe_public_url(value, identifier):
    try:
        parts = urlsplit(str(value or ""))
        spike.validate_url(str(value or ""))
        match = parse_qs(parts.query).get(identifier, [""])[0]
    except (AcquisitionError, ValueError):
        return None
    query = urlencode({identifier: match}) if re.fullmatch(r"[\w.-]{1,80}", match) else ""
    return urlunsplit(("https", "community.secop.gov.co", parts.path, query, ""))


def load_national_locations(path=DEFAULT_GEOGRAPHY):
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise spike.SpikeError(
            "No se pudo leer la configuraci\u00f3n geogr\u00e1fica nacional."
        ) from error
    if not isinstance(config, dict) or config.get("source") != GEOGRAPHY_SOURCE:
        raise spike.SpikeError(
            "La geograf\u00eda nacional debe identificar a Licitaciones.info como fuente."
        )

    ids = config.get("location_ids")
    if (
        not isinstance(ids, list)
        or config.get("location_count") != NATIONAL_LOCATION_COUNT
        or len(ids) != NATIONAL_LOCATION_COUNT
        or not all(isinstance(item, str) and re.fullmatch(r"[0-9]+", item) for item in ids)
        or len(set(ids)) != NATIONAL_LOCATION_COUNT
    ):
        raise spike.SpikeError(
            "Se requieren los 1.130 identificadores de ubicaci\u00f3n capturados, \u00fanicos."
        )
    return tuple(ids)


def load_analyzed_secop_ids(root, run_names):
    ids = set()
    for name in run_names:
        if not re.fullmatch(r"en01-[a-z0-9_]+", name):
            raise spike.SpikeError("Se requiere el nombre local de una corrida EN-01.")
        run_path = root / name
        if run_path.resolve() != run_path:
            raise spike.SpikeError("Historial fuera del almacenamiento local de EN-01.")
        try:
            rows = json.loads((run_path / "processes.json").read_text(encoding="utf-8"))
            results = json.loads(
                (run_path / "experience_requirements.json").read_text(encoding="utf-8")
            )
            discovered = {row["process_reference"]: row for row in rows["processes"]}
            if not results:
                raise ValueError
            for result in results:
                row = discovered[result["process_reference"]]
                identity = row.get("source_identity")
                if row["source"] != "secop2" or not re.fullmatch(r"CO1\.NTC\.\d+", identity or ""):
                    raise ValueError
                ids.add(identity)
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
            raise spike.SpikeError(
                f"Historial {name} incompleto o sin referencia comparable SECOP II."
            ) from error
    return frozenset(ids)


def discover(client, args, now, discovery, profile, locations):
    location_filter = ",".join(locations)
    payload = spike.build_process_payload(location_filter, None, DISCOVERY_PAGE_SIZE)
    discovery["geography"] = {
        "source": GEOGRAPHY_SOURCE,
        "location_count": len(locations),
        "ubicacion_filter_sha256": hashlib.sha256(location_filter.encode("ascii")).hexdigest(),
    }
    candidates = {}
    signatures = set()
    extra_pages = getattr(args, "conditional_extra_feed_pages", 0)
    provider_fields = {
        "unspsc_shapes": Counter(),
        "unspsc_rows_parsed": 0,
        "description_rows": 0,
        "modality_rows": 0,
    }
    discovery["provider_fields"] = provider_fields
    try:
        for page in range(1, args.discovery_pages + extra_pages + 1):
            if (
                page > args.discovery_pages
                and len(select_processes(candidates, args, now, {}, profile)) >= args.processes
            ):
                discovery["stop_reason"] = "eligible_target_reached"
                break
            body = client.post(
                f"/cliente/contratos/get-info/MP?perfiles={client.profile_id}",
                {**payload, "page": page},
            )
            rows = validate_discovery(body, DISCOVERY_PAGE_SIZE, validate_dates=False)
            signature = frozenset(str(row["idContrato"]) for row in rows)
            discovery["pages"].append(
                {"page": page, "provider_count": int(body["count"]), "received": len(rows)}
            )
            if signature in signatures:
                discovery["duplicates"] += len(rows)
                discovery["stop_reason"] = "provider_repeated_page"
                break
            signatures.add(signature)
            for row in rows:
                candidate = CandidateProcess.from_source(row, client.profile_id)
                process = candidate.to_dict()
                kind = source_kind(process)
                identity = process_identity(process)
                key = identity or candidate.reference
                raw_unspsc = row.get("UNSPSC")
                unspsc = parse_unspsc(raw_unspsc)
                provider_fields["unspsc_shapes"][
                    "missing" if raw_unspsc is None else type(raw_unspsc).__name__
                ] += 1
                provider_fields["unspsc_rows_parsed"] += bool(unspsc)
                description = next(
                    (
                        row[field]
                        for field in ("Descripcion", "Descripci\u00f3n", "DescripcionProceso")
                        if isinstance(row.get(field), str) and row[field].strip()
                    ),
                    "",
                )
                modality = row.get("modalidad") or row.get("Modalidad")
                provider_fields["description_rows"] += bool(description)
                provider_fields["modality_rows"] += isinstance(modality, str) and bool(
                    modality.strip()
                )
                if key in candidates:
                    discovery["duplicates"] += 1
                    existing = candidates[key]
                    existing["unspsc"] = sorted(set(existing["unspsc"]) | set(unspsc))
                    if not existing["description"]:
                        existing["description"] = description
                    continue
                phase = candidate.id_ultima_fase
                if not phase and identity and identity.startswith("CO1.NTC."):
                    phase = identity
                process.update(
                    source=kind,
                    source_identity=identity,
                    source_url=safe_public_url(row.get("Link"), "noticeUID"),
                    modality=modality,
                    unspsc=unspsc,
                    description=description,
                    inventory_capable=document_capable(process),
                    inventory_keys={
                        "idContrato": row["idContrato"],
                        "id_fuente_contract": row.get("id_fuente_contract"),
                        "idUltimaFase": phase,
                    },
                )
                candidates[key] = process
            if not rows or page * DISCOVERY_PAGE_SIZE >= int(body["count"]):
                discovery["stop_reason"] = "provider_end"
                break
        else:
            discovery["stop_reason"] = "page_budget"
    finally:
        sample = select_processes(candidates, args, now, discovery, profile)
    return sample


def select_processes(candidates, args, now, discovery, profile):
    processes, _, _ = apply_freshness(list(candidates.values()), args.recent_days, now)
    processes, _, _ = apply_validity(processes, now)
    preferred = {plain(value) for value in profile.preferred_modalities}
    terminal = {plain(value) for value in profile.terminal_states}
    buckets = {}
    excluded_samples = {}
    analyzed_ids = getattr(args, "excluded_secop_ids", frozenset())
    for process in processes:
        process.pop("raw_source_reference")
        process.update(
            assess_commercial(
                profile, process["object"], process.pop("description"), process["unspsc"]
            )
        )
        process["preferred_modality"] = plain(process["modality"]) in preferred
        provider_terminal = plain(process["provider_status"]).removeprefix("proceso ") in terminal
        if provider_terminal:
            process["validity_status"] = "closed"
            process["validity_warning"] = "terminal_provider_status"
        process["supply_prefilter_match"] = (
            process["recent"] and process["commercial_exclusion"] is None
        )
        reason = process["commercial_exclusion"]
        if not process["recent"]:
            reason = "outside_publication_window"
        elif not reason and (process["source"] != "secop2" or not process["inventory_capable"]):
            reason = "inventory_unavailable_for_source"
        if (
            not reason
            and getattr(args, "exploratory", False)
            and process["validity_status"] == "closed"
        ):
            reason = "closed_process"
        if not reason and analyzed_ids:
            identity = process["source_identity"] or ""
            if not re.fullmatch(r"CO1\.NTC\.\d+", identity):
                reason = "secop_notice_identity_unverified"
            elif identity in analyzed_ids:
                reason = "previously_analyzed_secop"
        process["excluded_reason"] = reason
        process["sampled"] = False
        if reason:
            examples = excluded_samples.setdefault(reason, [])
            if len(examples) < 2:
                examples.append(process["process_reference"])
            continue
        departments = buckets.setdefault(selection_rank(process), {})
        department = plain(process["department"])
        departments.setdefault(department, deque()).append(process)
    sample = []
    for rank in sorted(buckets):
        departments = buckets[rank]
        while departments and len(sample) < args.processes:
            for department, queue in list(departments.items()):
                process = queue.popleft()
                process["sampled"] = True
                sample.append(process)
                if not queue:
                    del departments[department]
                if len(sample) == args.processes:
                    break
        if len(sample) == args.processes:
            break
    discovery["processes"] = processes
    discovery["exclusion_review_sample"] = excluded_samples
    return sample


OCR_TOPIC = re.compile(r"\b(?:experiencia|requisitos? habilitantes?|acreditacion)\b")
OCR_PAGE_REFERENCE = re.compile(r"\b(?:paginas?|pags?\.?)\s+(\d+)\b")
OCR_INDEX_ENTRY = re.compile(r"(?:\.\s*){3,}(\d+)\s*$")
OCR_INDEX_MARKER = re.compile(r"(?:\.\s*){3,}|\b(?:indice|tabla de contenido)\b")


def ocr_bookmark_pages(stream):
    """Read explicit experience and habilitation destinations without OCR."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return []
    pages = []
    try:
        pdf = pdfium.PdfDocument(stream)
        try:
            for bookmark in islice(pdf.get_toc(max_depth=4), 128):
                title = spike.normalized(bookmark.get_title() or "")
                if re.search(r"\b(?:experiencia|requisitos? habilitantes?)\b", title) and (
                    destination := bookmark.get_dest()
                ):
                    pages.append(destination.get_index() + 1)
        finally:
            pdf.close()
    except (OSError, ValueError, pdfium.PdfiumError):
        return []
    return pages


def select_ocr_pages(native, low_text, budget, *, bookmarks=()):
    if not budget or native.error_code:
        return []
    visited = native.diagnostics.get("native_pages_visited", 0)
    candidates = set(low_text).intersection(range(1, visited + 1))
    scores = {}

    def prefer(page, rank):
        if page in candidates and rank < scores.get(page, 10):
            scores[page] = rank

    for page in bookmarks:
        prefer(page, 0)

    for fragment in native.fragments:
        number = fragment.page_number
        for raw in fragment.text.splitlines():
            line = spike.normalized(raw).strip()
            if not OCR_TOPIC.search(line):
                continue
            if target := OCR_PAGE_REFERENCE.search(line) or OCR_INDEX_ENTRY.search(line):
                prefer(int(target[1]), 0)
            if OCR_INDEX_MARKER.search(line):
                prefer(number, 1)
            elif len(line) <= 110:
                prefer(number, 1)
                prefer(number + 1, 2)
                prefer(number - 1, 3)
    name = native.document.original_name
    role = document_role(name)
    if role == "primary" or document_role_hint(name, role) == "primary":
        prefer(1, 4)
        if len(candidates) == visited:
            # For a fully unreadable rector, reserve at most the cover continuation.
            prefer(2, 5)
    return sorted(scores, key=lambda page: (scores[page], page))[:budget]


def extract_document(document, stored, storage, settings, entry, *, ocr_pages=OCR_PER_DOCUMENT):
    def choose_ocr_pages(native, low_text):
        bookmarks = ()
        if ocr_pages and low_text and not native.error_code and isinstance(stored, StoredBinary):
            with storage.open_verified(
                stored.storage_path,
                stored.sha256,
                stored.observed_size,
                settings.document_max_bytes,
            ) as stream:
                bookmarks = ocr_bookmark_pages(stream)
        return select_ocr_pages(native, low_text, ocr_pages, bookmarks=bookmarks)

    detail, fragments = spike.run_existing_extractor(
        document, stored, storage, settings, select_ocr_pages=choose_ocr_pages
    )
    diagnostics = detail.get("diagnostics", {})
    is_docx = document.extension == "docx"
    total = detail["page_count"]
    quality = diagnostics.get("native_quality", [])
    native_useful = {page["page_number"] for page in quality if not page["ocr_required"]}
    native_text = {
        f.source_locator["page_number"]
        for f in fragments
        if f.source_locator.get("extraction_method") == "native_pdf_text"
    }
    if not quality:
        native_useful = native_text
    ocr_success = set(diagnostics.get("successful_pages", []))
    processed = native_useful | ocr_success
    pending = set(range(1, total + 1)) - processed
    incomplete_from = diagnostics.get("native_incomplete_from")
    if incomplete_from is not None:
        pending.update(range(incomplete_from, total + 1))
    visited = diagnostics.get("native_pages_visited", total)
    selected = set(diagnostics.get("required_pages", []))
    if is_docx:
        cover = "\n".join(
            f.text
            for f in fragments
            if f.source_locator.get("kind") == "docx_paragraph"
            and f.source_locator.get("block_index", 0) <= 10
        )
    else:
        cover = "\n".join(f.text for f in fragments if f.source_locator.get("page_number") == 1)
    cover_role, cover_metadata = document_cover_metadata(cover)
    if (
        cover_role == "excluded"
        or (cover_role and entry["role"] == "unknown")
        or (cover_role == "support" and entry["role"] == "primary")
    ):
        entry.update(role=cover_role, role_source="cover", role_hint=None)
    if is_docx:
        docx_fragments = sum(
            f.source_locator.get("kind") in {"docx_paragraph", "docx_table_cell"} for f in fragments
        )
        content_complete = detail["status"] == "completed" and bool(docx_fragments)
    else:
        docx_fragments = 0
        content_complete = bool(total and not pending and not detail.get("error_code"))
    entry.update(
        cover_metadata=cover_metadata,
        coverage_unit="docx_fragment" if is_docx else "pdf_page",
        docx_fragments=docx_fragments,
        content_complete=content_complete,
        complete=content_complete and not entry.get("role_hint"),
        status=diagnostics.get("status", detail["status"]),
        pages_seen=sorted(processed),
        total_pages=total,
        native_pages=sorted(native_text),
        native_pages_visited=visited,
        ocr_required_pages=[
            p["page_number"] for p in quality if p["ocr_required"] and p["page_number"] <= visited
        ],
        ocr_pages=detail.get("ocr_pages", []),
        ocr_success_pages=sorted(ocr_success),
        ocr_omitted_pages=diagnostics.get("omitted_pages", []),
        ocr_unselected_pages=[
            p["page_number"]
            for p in quality
            if p["ocr_required"]
            and p["page_number"] <= visited
            and p["page_number"] not in selected
        ],
        ocr_diagnostics=diagnostics.get("pages", []),
        pending_pages=sorted(pending),
        error_code=detail.get("error_code"),
        native_stop_reason=diagnostics.get("native_stop_reason"),
        native_page_errors=diagnostics.get("native_page_errors", []),
        native_cpu_seconds=diagnostics.get("native_cpu_seconds"),
        extraction_seconds=detail["elapsed_seconds"],
        fragments=fragments,
    )


def progressive_stop(classification, governing_pdf_pending):
    if classification["status"] in {"experience_required", "no_experience_required"}:
        return "formal_conclusion"
    if classification["review_category"] == "explicit_requirement":
        return "applicable_requirement_in_governing_pdf"
    if classification["review_category"] == "documentary_silence" and not governing_pdf_pending:
        return "silence_secondary_review"
    return None


def corroboration_rank(entry):
    if entry["role"] in {"primary", "amendment"} or entry.get("role_hint") == "primary":
        return 0
    title = plain(entry["name"])
    if (
        entry["role"] == "support"
        and not re.search(r"\b(?:formatos?|formularios?)\b", title)
        and re.search(r"\b(?:habilitantes?|experiencia|estudios? previos?|requisitos?)\b", title)
    ):
        return 1
    return 2


def supports_document(entry):
    return entry["role"] != "excluded" and (
        entry["extension"] == "pdf"
        or (
            entry["extension"] == "docx"
            and (entry["role"] in {"primary", "amendment"} or entry.get("role_hint") == "primary")
        )
    )


def document_settings(settings, entry, governing_pdf_max_bytes):
    if (
        entry["extension"] == "pdf"
        and (entry["role"] == "primary" or entry.get("role_hint") == "primary")
        and DOCUMENT_BYTES < governing_pdf_max_bytes <= MAX_GOVERNING_PDF_MIB * MIB
    ):
        return settings.model_copy(
            update={
                "document_max_bytes": governing_pdf_max_bytes,
                "extraction_max_bytes": governing_pdf_max_bytes,
            }
        )
    return settings


def verify_document_type(storage, stored, document, max_bytes):
    if not isinstance(stored, StoredBinary) or document.extension not in {"pdf", "docx"}:
        return
    expected = b"%PDF-" if document.extension == "pdf" else b"PK\x03\x04"
    with storage.open_verified(
        stored.storage_path, stored.sha256, stored.observed_size, max_bytes
    ) as stream:
        if stream.read(len(expected)) != expected:
            raise AcquisitionError(
                "invalid_content", "El binario no coincide con el tipo anunciado."
            )


class DownloadState:
    def __init__(
        self, output, storage, *, edge_enabled=False, source=None, cdp_url="http://127.0.0.1:9232"
    ):
        self.output = output
        self.storage = storage
        self.edge_enabled = edge_enabled
        self.cdp_url = cdp_url
        self.stream_marker = output.parent / streaming.MARKER_NAME
        self.failed_processes = []
        self.receipts_path = output / "download_receipts.json"
        self.receipts = (
            json.loads(self.receipts_path.read_text(encoding="utf-8"))
            if self.receipts_path.is_file()
            else {}
        )

        self.previous_storage = spike.LocalBinaryStorage(source / "binaries") if source else None
        self.previous_hashes = (
            {
                f"{doc['document_id']}:{doc['extension']}": doc["sha256"]
                for case in json.loads((source / "documents.json").read_text(encoding="utf-8"))
                for doc in case["documents"]
                if re.fullmatch(r"[a-f0-9]{64}", doc.get("sha256") or "")
            }
            if source
            else {}
        )

    def key(self, document):
        return f"{document.document_id}:{document.extension}"

    def cached(self, document, max_bytes):
        key = self.key(document)
        if record := self.receipts.get(key):
            try:
                stored = StoredBinary(**record)
                verify_document_type(self.storage, stored, document, max_bytes)
                return stored
            except (AcquisitionError, TypeError):
                pass
        digest = self.previous_hashes.get(key)
        if not digest:
            return None
        path = f"sha256/{digest[:2]}/{digest}"
        try:
            size = (self.previous_storage.root / path).stat().st_size
            with self.previous_storage.open_verified(path, digest, size, max_bytes) as stream:
                stored = self.storage.store(
                    iter(lambda: stream.read(65536), b""),
                    original_name=f"{document.original_name}.{document.extension}",
                    content_type="application/octet-stream",
                    expected_size=size,
                    max_bytes=max_bytes,
                )
            verify_document_type(self.storage, stored, document, max_bytes)
        except (AcquisitionError, OSError):
            return None
        self.remember(document, stored)
        return stored

    def remember(self, document, stored):
        if isinstance(stored, StoredBinary):
            self.receipts[self.key(document)] = {
                "storage_path": stored.storage_path,
                "sha256": stored.sha256,
                "observed_size": stored.observed_size,
                "content_type": stored.content_type,
            }
            write_json(self.receipts_path, self.receipts)

    def record_failure(self, process):
        self.failed_processes.append(process)
        self.failed_processes = self.failed_processes[-3:]
        return len(self.failed_processes) == 3 and len(set(self.failed_processes)) >= 2


def can_stream_fallback(document, role, direct_error, diagnostics):
    if (
        role != "primary"
        or streaming.is_notice(document.original_name)
        or not streaming.fallback_eligible({"error": direct_error.code, "diagnostics": diagnostics})
    ):
        return False
    try:
        streaming.validate_target(document)
    except AcquisitionError:
        diagnostics["edge_skipped"] = "unverified_target"
        return False
    return True


def analyze_documents(
    client,
    process,
    storage,
    settings,
    allowance,
    metrics,
    documents,
    errors,
    *,
    ocr_pages=OCR_PER_DOCUMENT,
    exploratory=False,
    ordinary_allowance=None,
    governing_pdf_max_bytes=DOCUMENT_BYTES,
    download_state=None,
):
    if download_state and download_state.stream_marker.exists():
        raise BudgetReached("download_close_unverified")
    inventory = fetch_inventory(client, process["inventory_keys"])
    if not inventory:
        return "empty_inventory"
    metrics["with_inventory"] += 1
    all_documents = {}
    for document in inventory:
        role = document_role(document.original_name)
        all_documents[document.document_id] = {
            "document_id": document.document_id,
            "name": document.original_name,
            "url": safe_public_url(document.source_url, "DocumentId"),
            "extension": document.extension,
            "role": role,
            "role_hint": document_role_hint(document.original_name, role),
            "role_source": "filename",
            "status": "not_selected",
            "complete": False,
        }
    documents.extend(all_documents.values())
    eligible = sorted(
        (
            document
            for document in inventory
            if supports_document(all_documents[document.document_id])
        ),
        key=lambda document: document_priority(
            document.original_name,
            all_documents[document.document_id]["role"],
            all_documents[document.document_id]["role_hint"],
        ),
    )
    for entry in documents:
        entry["selection"] = (
            "irrelevant_document"
            if entry["role"] == "excluded"
            else "unsupported_format"
            if not supports_document(entry)
            else "document_limit"
        )
    prior_limit = False
    attempted = 0
    reviewed_document = False
    while eligible and attempted < allowance:
        corroborating = False
        if reviewed_document:
            classification = classify_experience(documents)
            if exploratory:
                stop = progressive_stop(
                    classification,
                    any(
                        corroboration_rank(all_documents[doc.document_id]) == 0 for doc in eligible
                    ),
                )
                if stop:
                    return stop
                if classification["review_category"] == "explicit_favorable":
                    eligible.sort(
                        key=lambda doc: corroboration_rank(all_documents[doc.document_id])
                    )
                    if corroboration_rank(all_documents[eligible[0].document_id]) == 2:
                        return "no_pertinent_corroborating_pdf"
                    corroborating = True
                elif ordinary_allowance is not None and attempted >= ordinary_allowance:
                    return "ordinary_download_allowance"
            elif classification["status"] in {"experience_required", "no_experience_required"}:
                return "formal_conclusion"
        document = eligible.pop(0)
        reviewed_document = True
        if time.monotonic() + START_EXTRACTION_MARGIN + 12 > client.deadline:
            raise BudgetReached("duration_budget")
        entry = all_documents[document.document_id]
        entry["selection"] = "selected"
        entry["selection_reason"] = (
            "corroborate_explicit_absence"
            if corroborating
            else "alternative_after_limit"
            if prior_limit
            else "priority"
        )
        scoped_settings = document_settings(settings, entry, governing_pdf_max_bytes)
        entry["document_max_bytes"] = (
            scoped_settings.document_max_bytes if scoped_settings is not None else DOCUMENT_BYTES
        )
        stage = "download"
        diagnostics = {}
        try:
            stored = (
                download_state.cached(document, entry["document_max_bytes"])
                if download_state
                else None
            )
            if stored:
                diagnostics["mechanism"] = "verified_cache"
                metrics["documents_reused"] += 1
            else:
                attempted += 1
                metrics["documents_attempted"] += 1
                try:
                    stored = spike.download_document(
                        client, document, storage, scoped_settings, diagnostics=diagnostics
                    )
                except AcquisitionError as direct_error:
                    available = (
                        allowance
                        if corroborating or ordinary_allowance is None
                        else (min(allowance, ordinary_allowance))
                    )
                    if not (
                        download_state
                        and download_state.edge_enabled
                        and attempted < available
                        and can_stream_fallback(document, entry["role"], direct_error, diagnostics)
                    ):
                        raise
                    if (
                        time.monotonic() + streaming.OPERATION_MARGIN + START_EXTRACTION_MARGIN
                        >= client.deadline
                    ):
                        diagnostics["edge_skipped"] = "duration_budget"
                        raise
                    try:
                        client.reserve(1)
                    except BudgetReached:
                        diagnostics["edge_skipped"] = "budget"
                        raise direct_error from None
                    attempted += 1
                    metrics["documents_attempted"] += 1
                    metrics["edge_attempts"] += 1
                    edge_diagnostics = diagnostics["edge"] = {}
                    stored = streaming.download_stream_pdf(
                        document,
                        storage,
                        download_state.stream_marker,
                        edge_diagnostics,
                        cdp_url=download_state.cdp_url,
                    )
                    diagnostics["mechanism"] = "edge_cdp_stream"
                    metrics["edge_downloaded"] += 1
                verify_document_type(storage, stored, document, entry["document_max_bytes"])
                metrics["documents_downloaded"] += 1
                metrics["bytes_downloaded"] += stored.observed_size
                if download_state:
                    download_state.remember(document, stored)
                    download_state.failed_processes.clear()
            metrics["governing_downloads"] += entry["role"] == "primary"
            entry["sha256"] = stored.sha256
            stage = "extraction"
            if time.monotonic() + START_EXTRACTION_MARGIN > client.deadline:
                entry["status"] = "extraction_not_started"
                raise BudgetReached("duration_budget")
            counted_governing = entry["role"] == "primary"
            extract_document(document, stored, storage, scoped_settings, entry, ocr_pages=ocr_pages)
            metrics["governing_downloads"] += int(entry["role"] == "primary") - int(
                counted_governing
            )
            metrics["native_cpu_seconds"] += entry.get("native_cpu_seconds") or 0
            metrics["extraction_seconds"] += entry["extraction_seconds"]
            code = entry["error_code"] or entry["native_stop_reason"]
            prior_limit = code in {
                "too_large",
                "text_limit",
                "fragment_limit",
                "memory_limit",
                "native_time_limit",
                "timeout",
                "reader_failed",
            }
            metrics["documents_processed"] += bool(entry["fragments"])
            metrics["docx_fragments"] += entry["docx_fragments"]
            metrics["pages_reported"] += entry["total_pages"]
            metrics["pages_with_text"] += len(entry["pages_seen"])
            metrics["ocr_pages_reported"] += len(entry["ocr_pages"])
            metrics["native_pages_with_text"] += len(entry["native_pages"])
            metrics["pending_pages"] += len(entry["pending_pages"])
            if code:
                metrics["extraction_failures"] += 1
                errors.append(
                    {
                        "stage": stage,
                        "code": code,
                        "document_id": document.document_id,
                    }
                )
        except BudgetReached:
            if stage == "download":
                metrics["documents_attempted"] -= 1
                entry["status"] = "download_not_started"
            raise
        except (AcquisitionError, spike.SpikeError, OSError) as error:
            code = getattr(error, "code", type(error).__name__)
            prior_limit = code in {"page_limit", "too_large"}
            entry.update(status=f"{stage}_failed", error_code=code)
            failure = {"stage": stage, "code": code, "document_id": document.document_id}
            if stage == "download" and diagnostics:
                failure["download_diagnostics"] = diagnostics
            errors.append(failure)
            metrics[f"{stage}_failures"] += 1
            if stage == "download" and download_state and download_state.stream_marker.exists():
                raise BudgetReached("download_close_unverified") from None
            if (
                stage == "download"
                and download_state
                and download_state.record_failure(process.get("process_reference", ""))
            ):
                raise BudgetReached("download_circuit_open") from None
        finally:
            if diagnostics:
                entry["download_diagnostics"] = diagnostics
            if corroborating and entry["status"] != "download_not_started":
                metrics["corroboration_attempts"] += 1

    if exploratory and reviewed_document:
        stop = progressive_stop(
            classify_experience(documents),
            any(corroboration_rank(all_documents[doc.document_id]) == 0 for doc in eligible),
        )
        if stop:
            return stop
    return "process_download_allowance" if eligible else "eligible_pdfs_exhausted"


def metrics_summary(discovery, results, metrics, client, started, profile):
    counts = Counter(result["status"] for result in results)
    analyzed = len(results)
    resolved = counts["experience_required"] + counts["no_experience_required"]
    supply = sum(p["supply_prefilter_match"] for p in discovery["processes"])
    eligible = sum(p["excluded_reason"] is None for p in discovery["processes"])
    assertions = Counter(
        item["assertion_type"] for result in results for item in result["evidence"]
    )
    review = Counter(result["review_category"] for result in results)
    exclusions = Counter(p["excluded_reason"] for p in discovery["processes"])

    return {
        "assertions": {kind: assertions[kind] for kind in ASSERTION_TYPES},
        "processes_with_explicit_requirement": sum(
            any(e["assertion_type"] == REQ for e in r["evidence"]) for r in results
        ),
        "processes_with_explicit_absence": sum(
            any(e["assertion_type"] == NEG for e in r["evidence"]) for r in results
        ),
        "documentary_silence": review["documentary_silence"],
        "deprioritized_cases": review["explicit_requirement"],
        "contradictions": sum(r["reason"] == "conflicting_clauses" for r in results),
        "unresolved": analyzed - resolved,
        "document_stop_reasons": dict(Counter(r["document_stop_reason"] for r in results)),
        "review_categories": dict(review),
        "review_prioritized": sum(r["review_priority"] <= 3 for r in results),
        "human_verified_errors": None,
        **metrics,
        **commercial_metrics(discovery["processes"], results, profile),
        "discovered_rows": sum(page["received"] for page in discovery["pages"]),
        "duplicates": discovery["duplicates"],
        "unique_processes": len(discovery["processes"]),
        "excluded_by_reason": {key: value for key, value in exclusions.items() if key},
        "supply_candidates": supply,
        "inventory_eligible": eligible,
        "eligible_before_history": eligible
        + exclusions["previously_analyzed_secop"]
        + exclusions["secop_notice_identity_unverified"],
        "history_secop_id_count": discovery.get("history_secop_id_count", 0),
        "sampled": sum(p["sampled"] for p in discovery["processes"]),
        "analyzed": analyzed,
        "selected_not_analyzed": sum(p["sampled"] for p in discovery["processes"]) - analyzed,
        "resolved": resolved,
        "classification": {status: counts[status] for status in STATUSES},
        "by_validity": {
            status: dict(Counter(r["status"] for r in results if r["validity_status"] == status))
            for status in ("open", "closed", "unknown")
        },
        "no_experience_rate_among_resolved": fraction(counts["no_experience_required"], resolved),
        "experience_rate_among_resolved": fraction(counts["experience_required"], resolved),
        "resolution_rate": fraction(resolved, analyzed),
        "unresolved_rate": fraction(analyzed - resolved, analyzed),
        "candidate_yield": fraction(counts["no_experience_required"], supply),
        "request_credits_used": client.requests,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "ai_calls": 0,
        "human_reviewed": 0,
    }


def run(client, args, settings, output, *, now=None, profile=None, locations=None):
    profile = profile or load_commercial_profile()
    locations = load_national_locations() if locations is None else locations
    started, parent_cpu, now = time.monotonic(), time.process_time(), now or local_now()
    exploratory = getattr(args, "exploratory", False)
    governing_pdf_max_bytes = getattr(args, "governing_pdf_max_mib", 10) * MIB
    per_process = EXPLORATORY_PER_PROCESS if exploratory else 2
    discovery = {
        "scope": "national_explicit_location_filter",
        "history_secop_id_count": len(getattr(args, "excluded_secop_ids", ())),
        "commercial_profile": {
            "version": profile.version,
            "sha256": profile.fingerprint,
            "catalog_version": profile.catalog["version"],
        },
        "cutoff": now.isoformat(),
        "date_field": "FechaPublicacion",
        "recent_days": args.recent_days,
        "pages": [],
        "processes": [],
        "duplicates": 0,
    }
    results, inventories, errors = [], [], []
    metrics = Counter(
        dict.fromkeys(
            (
                "with_inventory",
                "documents_attempted",
                "documents_downloaded",
                "documents_reused",
                "edge_attempts",
                "edge_downloaded",
                "governing_downloads",
                "corroboration_attempts",
                "native_cpu_seconds",
                "extraction_seconds",
                "download_failures",
                "extraction_failures",
                "documents_processed",
                "docx_fragments",
                "bytes_downloaded",
                "pages_reported",
                "native_pages_with_text",
                "pending_pages",
                "pages_with_text",
                "ocr_pages_reported",
                "unique_document_hashes",
            ),
            0,
        )
    )
    hashes = set()
    status = "failed"
    exit_code = 1
    try:
        if (output.parent / streaming.MARKER_NAME).exists():
            raise BudgetReached("download_close_unverified")
        resume = getattr(args, "resume_snapshot", None)
        if resume is None:
            check_session(client, client.profile_id, aggregator=True)
            sample = discover(client, args, now, discovery, profile, locations)
        else:
            sample = [{**row, "sampled": True} for row in resume[: args.processes]]
            discovery.update(
                scope="resume_saved_selection",
                processes=sample,
                stop_reason="saved_selection",
                resumed_from=args.resume_inventory_from,
            )
        write_json(output / "processes.json", discovery)
        storage = spike.LocalBinaryStorage(output / "binaries")
        download_state = DownloadState(
            output,
            storage,
            edge_enabled=getattr(args, "edge_stream_fallback", False),
            source=getattr(args, "resume_source", None),
            cdp_url=getattr(args, "cdp_url", "http://127.0.0.1:9232"),
        )
        favorable_reserve = min(FAVORABLE_RESERVE, max(0, args.documents - len(sample)))
        for index, process in enumerate(sample):
            reference = process["process_reference"]
            documents, process_errors = [], []
            remaining = args.documents - metrics["documents_attempted"]
            future_first_attempts = len(sample) - index - 1
            allowance = min(per_process, remaining, max(1, remaining - future_first_attempts))
            ordinary_allowance = None
            if exploratory:
                reserve_left = max(0, favorable_reserve - metrics["corroboration_attempts"])
                ordinary_allowance = min(
                    2, allowance, max(1, remaining - future_first_attempts - reserve_left)
                )
            stop = None
            request_start = client.requests
            process_start = time.monotonic()
            downloads_before = metrics["documents_downloaded"]
            ocr_before = metrics["ocr_pages_reported"]
            document_stop = "inventory_failed"
            try:
                document_stop = analyze_documents(
                    client,
                    process,
                    storage,
                    settings,
                    allowance,
                    metrics,
                    documents,
                    process_errors,
                    ocr_pages=getattr(args, "ocr_pages", OCR_PER_DOCUMENT),
                    exploratory=exploratory,
                    ordinary_allowance=ordinary_allowance,
                    governing_pdf_max_bytes=governing_pdf_max_bytes,
                    download_state=download_state,
                )
            except (BudgetReached, CandidateError) as error:
                if (
                    resume is None
                    or isinstance(error, BudgetReached)
                    or error.code in {"session_expired", "invalid_tab"}
                ):
                    stop = error
                document_stop = error.code if isinstance(error, CandidateError) else str(error)
                process_errors.append(
                    {
                        "stage": "pipeline",
                        "code": error.code if isinstance(error, CandidateError) else str(error),
                    }
                )
            except (AcquisitionError, spike.SpikeError, OSError) as error:
                process_errors.append(
                    {"stage": "inventory", "code": getattr(error, "code", type(error).__name__)}
                )
            if allowance == 0:
                process_errors.append({"stage": "selection", "code": "document_budget"})
            classification = classify_experience(documents, inventory_complete=bool(documents))
            if resume is not None and classification["status"] in {
                "experience_required",
                "no_experience_required",
            }:
                completed_path = output / "resume_completed.json"
                completed = (
                    json.loads(completed_path.read_text(encoding="utf-8"))
                    if completed_path.is_file()
                    else {}
                )
                completed[reference] = classification
                write_json(completed_path, completed)
            if not documents and not process_errors:
                classification["reason"] = "empty_inventory"
                classification["review_reason"] = "empty_inventory"
            for document in documents:
                document.pop("fragments", None)
                if document.get("sha256"):
                    hashes.add(document["sha256"])
            inventories.append({"process_reference": reference, "documents": documents})
            results.append(
                {
                    "run_id": output.name,
                    "process_reference": reference,
                    "validity_status": process["validity_status"],
                    "department": process["department"],
                    "document_stop_reason": document_stop,
                    "commercial_category": process["primary_category"],
                    "commercial_priority": process["commercial_priority"],
                    "operational_cost": {
                        "elapsed_seconds": round(time.monotonic() - process_start, 3),
                        "request_credits": client.requests - request_start,
                        "downloads": metrics["documents_downloaded"] - downloads_before,
                        "ocr_pages_reported": metrics["ocr_pages_reported"] - ocr_before,
                    },
                    "coverage": {
                        "inventory_available": bool(documents),
                        "documents_complete": sum(d["complete"] for d in documents),
                    },
                    **classification,
                }
            )
            errors.extend({"process_reference": reference, **error} for error in process_errors)
            if stop:
                raise stop
        complete = (
            len(sample) == args.processes
            and discovery["stop_reason"] != "provider_repeated_page"
            and not errors
        )
        status, exit_code = ("completed", 0) if complete else ("partial", 2)
    except BudgetReached as error:
        status, exit_code = "partial", 2
        errors.append({"stage": "budget", "code": str(error)})
    except CandidateError as error:
        exit_code = error.exit_code
        errors.append({"stage": "cdp", "code": error.code, "criterion": error.criterion})
    except KeyboardInterrupt:
        status, exit_code = "partial", 2
        errors.append({"stage": "run", "code": "interrupted"})
    except (spike.SpikeError, OSError) as error:
        errors.append({"stage": "run", "code": type(error).__name__})
    finally:
        if exploratory:
            deprioritized = []
            covered_departments = set()
            candidates = [r for r in results if r["review_category"] == "explicit_requirement"]
            for result in candidates:
                department = plain(result["department"])
                if department not in covered_departments:
                    deprioritized.append(result)
                    covered_departments.add(department)
            deprioritized.extend(r for r in candidates if r not in deprioritized)
            deprioritized = deprioritized[:DEPRIORITIZED_SAMPLE_SIZE]
            write_json(output / "deprioritized_review_sample.json", deprioritized)
            metrics["deprioritized_review_sample"] = len(deprioritized)
        metrics["unique_document_hashes"] = len(hashes)
        limits = {
            "processes": args.processes,
            "discovery_pages": args.discovery_pages,
            "conditional_extra_feed_pages": getattr(args, "conditional_extra_feed_pages", 0),
            "documents": args.documents,
            "documents_per_process": per_process,
            "favorable_reserve_max": FAVORABLE_RESERVE if exploratory else 0,
            "document_max_bytes": DOCUMENT_BYTES,
            "governing_pdf_max_bytes": governing_pdf_max_bytes,
            "native_pages_per_pdf": None,
            "ocr_pages_per_pdf": getattr(args, "ocr_pages", OCR_PER_DOCUMENT),
            "ocr_pages_per_run_upper_bound": args.documents
            * getattr(args, "ocr_pages", OCR_PER_DOCUMENT),
            "request_credits": EXPLORATORY_REQUEST_CREDITS if exploratory else REQUEST_CREDITS,
            "duration_seconds": EXPLORATORY_DURATION_SECONDS if exploratory else DURATION_SECONDS,
            "ai_calls": 0,
        }
        summary = {
            "run_id": output.name,
            "status": status,
            "limits": limits,
            "parent_cpu_seconds": round(time.process_time() - parent_cpu, 3),
            **metrics_summary(discovery, results, metrics, client, started, profile),
        }
        for filename, data in (
            ("processes.json", discovery),
            ("documents.json", inventories),
            ("experience_requirements.json", results),
            ("review_queue.json", sorted(results, key=lambda result: result["review_priority"])),
            ("metrics.json", summary),
            ("errors.json", errors),
        ):
            write_json(output / filename, data)
        (output / "summary.md").write_text(
            f"# EN-01 · {output.name}\n\n"
            f"- Estado: {status}\n"
            f"- Procesos analizados: {summary['analyzed']} de {summary['sampled']} seleccionados\n"
            f"- Procesos resueltos: {summary['resolved']}\n"
            f"- Documentos descargados: {summary['documents_downloaded']}\n"
            f"- Revisión humana: pendiente\n",
            encoding="utf-8",
        )
    return exit_code


def settings_for_run(output, tesseract, tessdata, ocr_pages=OCR_PER_DOCUMENT):
    policy = spike.load_ocr_policy(spike.ROOT / "config" / "extraction_ocr.v1.json")
    policy = policy.model_copy(
        update={
            "fallback_language": "spa",
            "max_ocr_pages": max(1, ocr_pages),
            "page_timeout_seconds": 6,
            "document_timeout_seconds": 14,
            "max_retry_attempts": 0,
        }
    )
    policy_path = output / "ocr_policy.json"
    write_json(policy_path, policy.model_dump())
    return spike.Settings(
        _env_file=None,
        database_url="disabled://no-db",
        document_timeout_seconds=12,
        document_max_bytes=DOCUMENT_BYTES,
        extraction_max_bytes=DOCUMENT_BYTES,
        extraction_timeout_seconds=12,
        extraction_ocr_enabled=True,
        extraction_ocr_config_path=policy_path,
        extraction_tesseract_cmd=tesseract,
        extraction_tessdata_path=tessdata,
    )


def load_resume_snapshot(source):
    rows = json.loads((source / "processes.json").read_text(encoding="utf-8"))["processes"]
    results = json.loads((source / "experience_requirements.json").read_text(encoding="utf-8"))
    recorded = {result["process_reference"]: result["status"] for result in results}
    pending = [
        row
        for row in rows
        if row.get("sampled")
        and row.get("source") == "secop2"
        and recorded.get(row["process_reference"], "not_resolved")
        in {"not_resolved", "experience_ambiguous"}
        and all(
            row.get("inventory_keys", {}).get(key)
            for key in ("idContrato", "id_fuente_contract", "idUltimaFase")
        )
    ]
    result_order = {reference: index for index, reference in enumerate(recorded)}
    return sorted(
        pending,
        key=lambda row: result_order.get(row["process_reference"], len(result_order)),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exploratory", action="store_true", help="Presupuesto EN-01.4.")
    parser.add_argument(
        "--edge-stream-fallback",
        "--edge-download-fallback",
        action="store_true",
        help="Streaming CDP optativo para PDF rectores tras HTTP 403 directo.",
    )
    parser.add_argument(
        "--resume-inventory-from",
        metavar="CORRIDA",
        help="Reanudar procesos pendientes de una corrida local sin consultar el feed.",
    )
    parser.add_argument(
        "--exclude-analyzed-from",
        action="append",
        default=[],
        metavar="CORRIDA",
        help="Excluir avisos SECOP II analizados en una corrida local EN-01. Repetible.",
    )
    parser.add_argument("--processes", type=int)
    parser.add_argument("--documents", type=int)
    parser.add_argument("--discovery-pages", type=int)
    parser.add_argument(
        "--conditional-extra-feed-pages",
        type=int,
        choices=range(3),
        default=0,
        help="Páginas adicionales solo si faltan candidatos inéditos tras las ocho iniciales.",
    )
    parser.add_argument("--recent-days", type=int, choices=range(1, 61), default=30)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9232")
    parser.add_argument(
        "--governing-pdf-max-mib",
        type=int,
        choices=range(10, MAX_GOVERNING_PDF_MIB + 1),
        default=10,
        help="Tope optativo, solo para PDF de rector o candidato a rector.",
    )
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--tessdata", type=Path)
    parser.add_argument(
        "--ocr-pages", type=int, choices=range(OCR_PER_DOCUMENT + 1), default=OCR_PER_DOCUMENT
    )
    parser.add_argument(
        "--profile-id", help="Override de LICITACIONES_PROFILE_ID para esta ejecucion."
    )
    parser.add_argument("--commercial-profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--geography", type=Path, default=DEFAULT_GEOGRAPHY)
    args = parser.parse_args(argv)
    if args.exploratory:
        defaults = (EXPLORATORY_PROCESSES, EXPLORATORY_DOCUMENTS, EXPLORATORY_DISCOVERY_PAGES)
        limits = (range(1, defaults[0] + 1), range(1, defaults[1] + 1), range(1, defaults[2] + 1))
    else:
        defaults = (5, 5, 4)
        limits = (range(5, 11), range(5, 8), range(1, 7))
    for name, default, allowed in zip(
        ("processes", "documents", "discovery_pages"), defaults, limits, strict=True
    ):
        value = getattr(args, name)
        value = default if value is None else value
        if value not in allowed:
            parser.error(
                f"--{name.replace('_', '-')} debe estar entre {allowed.start} y {allowed.stop - 1}."
            )
        setattr(args, name, value)
    if not args.exploratory and args.governing_pdf_max_mib > 10:
        parser.error("El tope opcional de PDF rectores requiere --exploratory.")
    if args.exploratory and args.documents < args.processes:
        parser.error("EN-01.4 reserva al menos un intento documental por proceso.")
    if args.conditional_extra_feed_pages and (
        not args.exploratory
        or args.discovery_pages != EXPLORATORY_DISCOVERY_PAGES
        or args.processes != EXPLORATORY_PROCESSES
        or not args.exclude_analyzed_from
    ):
        parser.error("Las páginas adicionales requieren 8 páginas, 15 procesos e historial local.")
    try:
        args.excluded_secop_ids = load_analyzed_secop_ids(OUTPUT_ROOT, args.exclude_analyzed_from)
        if args.resume_inventory_from:
            if not re.fullmatch(r"en01-[a-z0-9_]+", args.resume_inventory_from):
                raise ValueError("Nombre de corrida histórica inválido.")
            source = OUTPUT_ROOT / args.resume_inventory_from
            args.resume_source = source
            if source.resolve() != source:
                raise ValueError("Historial fuera del almacenamiento local.")
            args.resume_snapshot = load_resume_snapshot(source)
            if not args.resume_snapshot:
                raise spike.SpikeError("La corrida no contiene procesos pendientes verificables.")
        profile_id = resolve_profile_id(args.profile_id)
        validate_cdp_url(args.cdp_url)
        profile = load_commercial_profile(args.commercial_profile)
        locations = load_national_locations(args.geography)
        from playwright.sync_api import sync_playwright

        if OUTPUT_ROOT.resolve() != OUTPUT_ROOT:
            raise ValueError("Ruta de salida fuera del directorio experimental.")
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        if args.resume_inventory_from:
            output = OUTPUT_ROOT / f"en01-resume_{args.resume_inventory_from[5:]}"
            if output.resolve() != output or output == source:
                raise ValueError("Salida de reanudación inválida.")
            output.mkdir(exist_ok=True)
            previous = output / "resume_completed.json"
            if previous.is_file():
                finished = set(json.loads(previous.read_text(encoding="utf-8")))
                args.resume_snapshot = [
                    row for row in args.resume_snapshot if row["process_reference"] not in finished
                ]
                if not args.resume_snapshot:
                    print("Los procesos de la selección local ya están resueltos.")
                    return 0
        else:
            output = Path(tempfile.mkdtemp(prefix="en01-", dir=OUTPUT_ROOT))
        print(json.dumps({"output": str(output)}), flush=True)
        duration = EXPLORATORY_DURATION_SECONDS if args.exploratory else DURATION_SECONDS
        credits = EXPLORATORY_REQUEST_CREDITS if args.exploratory else REQUEST_CREDITS
        deadline = time.monotonic() + duration
        settings = settings_for_run(output, args.tesseract, args.tessdata, args.ocr_pages)
        with sync_playwright() as playwright:
            browser = connect_browser(playwright, args.cdp_url)
            return run(
                SmokeClient(find_page(browser), profile_id, deadline, request_limit=credits),
                args,
                settings,
                output,
                profile=profile,
                locations=locations,
            )
    except ProfileConfigurationError as error:
        print(f"EN-01: {error}")
        return 1
    except spike.SpikeError as error:
        print(f"EN-01: {error.code}" if isinstance(error, CandidateError) else f"EN-01: {error}")
        return error.exit_code if isinstance(error, CandidateError) else 1
    except Exception as error:
        # Provider and reader exceptions can include response content or local paths.
        print(f"EN-01: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
