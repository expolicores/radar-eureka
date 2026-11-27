"""EN-01 focused validation of explicitly authorized pending documents of identified processes.

plan            offline: resolve documents from saved inventories, require the approved batch
                digest, write a target run with a SECOP I queue for the existing batch acquirer.
acquire-secop2  real (needs authorization): direct download; only on HTTP 403 and only for a
                document of the approved plan, the validated Edge stream as fallback.
analyze         offline: joint extraction + existing classifier over every held document.

No feed, inventory or discovery request. No rule changes. One attempt per document.
"""

import argparse
import hashlib
import json
import os
import time
from datetime import UTC, datetime

import eureka_nacional_secop1_flow as secop1
from eureka_nacional_experience import NON_GOVERNING_TITLE, classify_experience, document_title

TARGET_PREFIX = "en01-target_"
PLAN_FILE = "targeted_plan.json"
ATTEMPTS_DIR = "targeted_attempts"
RESULTS_FILE = "validation_results.json"
SUPPORT_OCR_PAGES = 2  # existing per-document OCR for non-governing documents


def write_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def batch_digest(entries):
    """Same digest the operator approved: sorted [source, identity, document_id, locator]."""
    rows = sorted({tuple(row) for row in entries})
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def _inventories(run, stage3=None):
    found = {}
    for path in filter(None, (stage3 and stage3 / "documents.json", run / "documents.json")):
        for case in read_json(path, []):
            found.setdefault(case["process_reference"], case["documents"])
    return found


# ---------------------------------------------------------------- plan (offline)


def build_plan(source, target, document_ids, expected_sha256, *, stage3=None):
    processes = {
        p["process_reference"]: p for p in read_json(source / "processes.json")["processes"]
    }
    inventories = _inventories(source, stage3)
    items = []
    for wanted in document_ids:
        matches = [
            (reference, doc)
            for reference, docs in inventories.items()
            for doc in docs
            if str(doc["document_id"]) == wanted
        ]
        if len(matches) != 1:
            raise ValueError(f"Documento no identificado de forma unica: {wanted}")
        reference, doc = matches[0]
        process = processes[reference]
        source_kind = process["source"]
        if source_kind not in {"secop1", "secop2"} or doc.get("extension") != "pdf":
            raise ValueError("Documento fuera del alcance de la validacion focalizada.")
        locator = doc.get("relative_path") if source_kind == "secop1" else doc.get("url")
        if not locator:
            raise ValueError("Documento sin ruta o URL verificable.")
        items.append(
            {
                "source": source_kind,
                "process_reference": reference,
                "source_identity": process.get("source_identity"),
                "document_id": str(doc["document_id"]),
                "name": doc["name"],
                "extension": "pdf",
                "role": doc.get("role"),
                "locator": locator,
                "displayed_size": doc.get("displayed_size"),
                "displayed_size_bytes": doc.get("displayed_size_bytes"),
            }
        )
    digest = batch_digest(
        [i["source"], i["source_identity"].removeprefix("secop1:"), i["document_id"], i["locator"]]
        for i in items
    )
    if digest != expected_sha256:
        raise ValueError("El lote no coincide con el hash aprobado.")
    target.mkdir(exist_ok=False)
    plan = {
        "source_run": source.name,
        "stage3_run": stage3.name if stage3 else None,
        "batch_sha256": digest,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "network_requests": 0,
        "items": items,
    }
    write_json(target / PLAN_FILE, plan)
    references = {i["process_reference"] for i in items}
    write_json(
        target / "processes.json",
        {
            "scope": "targeted_validation",
            "source_run": source.name,
            "processes": [processes[r] for r in sorted(references)],
        },
    )
    write_json(
        target / "documents.json",
        [{"process_reference": r, "documents": inventories[r]} for r in sorted(references)],
    )
    queue_items = [
        {
            "process_reference": i["process_reference"],
            "constancia": i["source_identity"].removeprefix("secop1:"),
            "document_id": i["document_id"],
            "name": i["name"],
            "extension": "pdf",
            "relative_path": i["locator"],
            "role": i["role"],
            "role_hint": None,
            "displayed_size": i["displayed_size"],
            "displayed_size_bytes": i["displayed_size_bytes"],
            "displayed_size_known": isinstance(i["displayed_size_bytes"], int),
            "targeted_validation": True,
        }
        for i in items
        if i["source"] == "secop1"
    ]
    if queue_items:
        for item in queue_items:
            if secop1.acquisition_size_check(item)[0]:
                raise ValueError("Documento SECOP I sobre el limite de tamano mostrado.")
        secop1.write_queue(target, queue_items, target.name)
    return plan


def load_plan(target, expected_sha256):
    plan = read_json(target / PLAN_FILE)
    entries = [
        [i["source"], i["source_identity"].removeprefix("secop1:"), i["document_id"], i["locator"]]
        for i in plan["items"]
    ]
    if plan["batch_sha256"] != expected_sha256 or batch_digest(entries) != expected_sha256:
        raise ValueError("Plan alterado o distinto del lote aprobado.")
    return plan


# ---------------------------------------------------------------- SECOP II acquisition (real)


def _attempt_path(target, document_id):
    digest = hashlib.sha256(document_id.encode()).hexdigest()[:32]
    return target / ATTEMPTS_DIR / f"{digest}.json"


def acquire_secop2(target, expected_sha256, *, runner, streaming, client, settings, cdp_url):
    """One direct attempt per approved SECOP II document; stream only after HTTP 403.

    `runner` provides spike/DownloadState/verify_document_type/DOCUMENT_BYTES; `streaming`
    provides fallback_eligible/validate_target/download_stream_pdf/MARKER_NAME."""
    plan = load_plan(target, expected_sha256)
    marker = target.parent / streaming.MARKER_NAME
    if marker.exists():
        raise ValueError("Marcador preventivo presente; no se adquiere.")
    storage = runner.spike.LocalBinaryStorage(target / "binaries")
    state = runner.DownloadState(target, storage)
    report = []
    for item in plan["items"]:
        if item["source"] != "secop2":
            continue
        document = runner.spike.SpikeDocument(
            item["name"], "pdf", item["locator"], item["document_id"]
        )
        streaming.validate_target(document)  # exact RetrieveFile URL for this DocumentId
        if state.cached(document, runner.DOCUMENT_BYTES):
            report.append({"document_id": item["document_id"], "outcome": "already_present"})
            continue
        path = _attempt_path(target, item["document_id"])
        path.parent.mkdir(exist_ok=True)
        try:
            with path.open("x", encoding="utf-8") as handle:
                json.dump(
                    {
                        "document_id": item["document_id"],
                        "state": "reserved",
                        "batch_sha256": plan["batch_sha256"],
                    },
                    handle,
                )
        except FileExistsError:
            report.append({"document_id": item["document_id"], "outcome": "attempt_recorded"})
            continue
        diagnostics = {}
        outcome = {"document_id": item["document_id"], "outcome": "error"}
        started = time.monotonic()
        try:
            try:
                stored = runner.spike.download_document(
                    client, document, storage, settings, diagnostics=diagnostics
                )
                outcome["mechanism"] = "direct"
            except runner.AcquisitionError as direct_error:
                fallback = streaming.fallback_eligible(
                    {"error": direct_error.code, "diagnostics": diagnostics}
                )
                if not fallback:
                    raise
                edge_diagnostics = diagnostics["edge"] = {}
                stored = streaming.download_stream_pdf(
                    document, storage, marker, edge_diagnostics, cdp_url=cdp_url
                )
                outcome["mechanism"] = "edge_cdp_stream_authorized_support"
            runner.verify_document_type(storage, stored, document, runner.DOCUMENT_BYTES)
            state.remember(document, stored)
            outcome.update(
                outcome="stored", sha256=stored.sha256, received_bytes=stored.observed_size
            )
        except runner.AcquisitionError as error:
            outcome.update(outcome="rejected", reason=error.code)
        finally:
            outcome["seconds"] = round(time.monotonic() - started, 3)
            outcome["direct_http_status"] = diagnostics.get("http_status")
            outcome["edge_error"] = (diagnostics.get("edge") or {}).get("error")
            record = read_json(path)
            record.update(state="finished", **outcome)
            write_json(path, record)
            report.append(outcome)
        if marker.exists():
            report.append({"stop_reason": "stream_close_unverified"})
            break
    return report


# ---------------------------------------------------------------- joint analysis (offline)


def _held_receipts(plan, source, target):
    receipts = {}
    for run in (source, target):
        for key, record in secop1.load_receipts(run).items():
            receipts.setdefault(key, (run, record))
    return receipts


def validation_reading(classification, documents):
    """Readings derived from the unchanged classifier output and the coverage gaps.

    experiencia_exigida: formal experience_required.
    experiencia_exigida_sin_conclusion_formal: a non-limited EXIGENCIA was observed (for
        instance in the estudio previo) but the classifier did not conclude.
    ausencia_explicita: formal no_experience_required.
    ausencia_explicita_pendiente_de_corroboracion: an explicit waiver was observed only.
    silencio_documental_con_cobertura_suficiente: no clause either way and no coverage gap.
    evidencia_insuficiente: anything else, including silence with unresolved documents.
    """
    status, review = classification["status"], classification["review_category"]
    unresolved = [
        {"document": d["name"], "reason": d["validation_gap"]}
        for d in documents
        if d.get("validation_gap")
    ]
    observed = {
        item["assertion_type"]
        for item in classification.get("evidence", [])
        if item.get("role") in {"primary", "amendment", "support"}
        and item.get("scope") != "limited"
    }
    if status == "experience_required":
        reading = "experiencia_exigida"
    elif status == "no_experience_required":
        reading = "ausencia_explicita"
    elif "EXIGENCIA" in observed and "NEG_CONCLUSIVA" not in observed:
        reading = "experiencia_exigida_sin_conclusion_formal"
    elif "NEG_CONCLUSIVA" in observed and "EXIGENCIA" not in observed:
        reading = "ausencia_explicita_pendiente_de_corroboracion"
    elif (
        review == "documentary_silence"
        and not unresolved
        and not observed
        & {
            "EXIGENCIA",
            "NEG_CONCLUSIVA",
        }
    ):
        reading = "silencio_documental_con_cobertura_suficiente"
    else:
        reading = "evidencia_insuficiente"
    return reading, unresolved


def analyze(target, expected_sha256, *, runner, settings, budget):
    plan = load_plan(target, expected_sha256)
    if (target / RESULTS_FILE).exists():
        raise ValueError("El analisis ya existe; no se sobrescribe.")
    root = target.parent
    source = root / plan["source_run"]
    receipts = _held_receipts(plan, source, target)
    inventories = {
        c["process_reference"]: c["documents"] for c in read_json(target / "documents.json")
    }
    processes = {
        p["process_reference"]: p for p in read_json(target / "processes.json")["processes"]
    }
    results = []
    for reference in sorted(inventories):
        documents = [dict(d) for d in inventories[reference]]
        process = processes[reference]
        for document in documents:
            document["complete"] = False
            document.pop("fragments", None)
            key = f"{document['document_id']}:{document.get('extension')}"
            if document.get("extension") not in {"pdf", "docx"}:
                document["validation_gap"] = "formato_no_procesable"
                continue
            if key not in receipts:
                if document.get("role") in {"primary", "amendment", "support"} or (
                    document.get("role") == "unknown"
                    and not NON_GOVERNING_TITLE.search(document_title(document["name"]))
                ):
                    document["validation_gap"] = "no_descargado"
                continue
            run, record = receipts[key]
            storage = runner.spike.LocalBinaryStorage(run / "binaries")
            spike_document = runner.spike.SpikeDocument(
                document["name"],
                document["extension"],
                document.get("url") or "",
                str(document["document_id"]),
            )
            stored = runner.StoredBinary(**record)
            runner.verify_document_type(storage, stored, spike_document, runner.DOCUMENT_BYTES)
            per_document = (
                secop1.GOVERNING_OCR_PAGES
                if document.get("role") in {"primary", "amendment"}
                else SUPPORT_OCR_PAGES
            )
            secop1.extract_with_ocr_plan(
                runner.extract_document,
                spike_document,
                stored,
                storage,
                settings,
                document,
                budget,
                per_document=per_document,
            )
            document["receipt_run"] = run.name
            if not document["complete"]:
                document["validation_gap"] = "cobertura_incompleta"
        classification = classify_experience(documents, inventory_complete=True)
        reading, unresolved = validation_reading(classification, documents)
        for document in documents:
            document.pop("fragments", None)
        results.append(
            {
                "process_reference": reference,
                "source_identity": process.get("source_identity"),
                "entity": process.get("entity_name"),
                "commercial_priority": process.get("commercial_priority"),
                "commercial_category": process.get("primary_category"),
                "validation_reading": reading,
                "unresolved_dependencies": unresolved,
                "documents": [
                    {
                        k: d.get(k)
                        for k in (
                            "name",
                            "role",
                            "extension",
                            "complete",
                            "total_pages",
                            "pages_seen",
                            "pending_pages",
                            "ocr_pages",
                            "receipt_run",
                            "validation_gap",
                        )
                    }
                    for d in documents
                ],
                **{
                    k: classification[k]
                    for k in (
                        "status",
                        "reason",
                        "review_category",
                        "review_reason",
                        "review_priority",
                        "evidence",
                        "document_coverage",
                    )
                },
            }
        )
    write_json(
        target / RESULTS_FILE,
        {
            "batch_sha256": plan["batch_sha256"],
            "network_requests": 0,
            "ai_calls": 0,
            "results": results,
        },
    )
    return results


class DirectOnlyClient:
    """download_document reserves provider credits; direct SECOP downloads spend none."""

    def reserve(self, count=1):
        return None


# ---------------------------------------------------------------- CLI


def main(argv=None):
    import eureka_nacional_cdp_stream as streaming
    import eureka_nacional_en01 as runner

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("source_run")
    p_plan.add_argument("--stage3-run")
    p_plan.add_argument("--document", action="append", required=True)
    for p in (p_plan, sub.add_parser("acquire-secop2"), sub.add_parser("analyze")):
        p.add_argument("--expect-sha256", required=True)
        if p is not p_plan:
            p.add_argument("target_run")
    sub.choices["acquire-secop2"].add_argument("--cdp-url", default="http://127.0.0.1:9232")
    sub.choices["analyze"].add_argument("--tesseract", default="tesseract")
    args = parser.parse_args(argv)
    root = runner.OUTPUT_ROOT
    try:
        if args.command == "plan":
            source = secop1.ensure_inside(root, root / secop1.run_dir_name(args.source_run))
            stage3 = (
                secop1.ensure_inside(root, root / secop1.run_dir_name(args.stage3_run))
                if args.stage3_run
                else None
            )
            target = secop1.ensure_inside(root, root / f"{TARGET_PREFIX}{args.source_run[5:]}")
            plan = build_plan(source, target, args.document, args.expect_sha256, stage3=stage3)
            print(
                json.dumps(
                    {
                        "target": target.name,
                        "batch_sha256": plan["batch_sha256"],
                        "items": [
                            [i["source"], i["document_id"], i["name"]] for i in plan["items"]
                        ],
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        target = secop1.ensure_inside(root, root / secop1.run_dir_name(args.target_run))
        if args.command == "acquire-secop2":
            runner.validate_cdp_url(args.cdp_url)
            settings = runner.settings_for_run(target, "tesseract", None)
            client = DirectOnlyClient()
            report = acquire_secop2(
                target,
                args.expect_sha256,
                runner=runner,
                streaming=streaming,
                client=client,
                settings=settings,
                cdp_url=args.cdp_url,
            )
            print(json.dumps(report, ensure_ascii=False))
            return 0
        settings = runner.settings_for_run(target, args.tesseract, None, secop1.PASS_PAGES)
        results = analyze(
            target, args.expect_sha256, runner=runner, settings=settings, budget=secop1.OcrBudget()
        )
        print(
            json.dumps(
                [[r["source_identity"], r["status"], r["validation_reading"]] for r in results],
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, ValueError, runner.spike.SpikeError) as error:
        print(f"EN-01 validacion: {type(error).__name__}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
