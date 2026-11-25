"""Import operator-provided SECOP II files and resume EN-01 entirely offline."""

import argparse
import hashlib
import json
import re
import stat
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from eureka_nacional_en01 import (
    DOCUMENT_BYTES,
    EXPLORATORY_DOCUMENTS,
    EXPLORATORY_DURATION_SECONDS,
    EXPLORATORY_PER_PROCESS,
    EXPLORATORY_PROCESSES,
    OCR_PER_DOCUMENT,
    OUTPUT_ROOT,
    START_EXTRACTION_MARGIN,
    DownloadState,
    classify_experience,
    document_role,
    document_role_hint,
    extract_document,
    settings_for_run,
    verify_document_type,
    write_json,
)
from spike_licitaciones_info import SpikeDocument

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError

FORMATS = {
    "pdf": (b"%PDF-", "application/pdf"),
    "docx": (
        b"PK\x03\x04",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ),
}
EXTRACTION_CACHE_VERSION = 1


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def archived_inventory(source):
    pending = {
        item["process_reference"]
        for item in read_json(source / "experience_requirements.json")
        if item["status"] in {"not_resolved", "experience_ambiguous"}
    }
    processes = {
        row["process_reference"]: row
        for row in read_json(source / "processes.json")["processes"]
        if row["sampled"] and row.get("source") == "secop2" and row["process_reference"] in pending
    }
    if not 0 < len(processes) <= EXPLORATORY_PROCESSES:
        raise ValueError("Selección archivada fuera de los límites de EN-01.")
    inventories = {
        case["process_reference"]: case["documents"]
        for case in read_json(source / "documents.json")
        if case["process_reference"] in processes
    }
    documents = {}
    for reference, entries in inventories.items():
        for entry in entries:
            identifier, extension = entry["document_id"], entry["extension"]
            if extension not in FORMATS:
                continue
            if not re.fullmatch(r"[0-9]{1,40}", identifier) or identifier in documents:
                raise ValueError("Identificador documental archivado inválido o ambiguo.")
            documents[identifier] = (
                reference,
                SpikeDocument(entry["name"], extension, "", identifier),
            )
    return processes, inventories, documents


@contextmanager
def exclusive_import(output):
    marker = output / ".import.lock"
    with marker.open("x", encoding="utf-8"):
        pass
    try:
        yield
    finally:
        marker.unlink()


def import_file(path, document, state, previous):
    magic, media_type = FORMATS[document.extension]
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise AcquisitionError("invalid_file", "Se requiere un archivo regular.")
    if info.st_size > DOCUMENT_BYTES:
        raise AcquisitionError("too_large", "El archivo supera el límite ordinario.")
    with path.open("rb") as stream:
        payload = stream.read(DOCUMENT_BYTES + 1)
    if len(payload) > DOCUMENT_BYTES:
        raise AcquisitionError("too_large", "El archivo supera el límite ordinario.")
    if not payload.startswith(magic):
        raise AcquisitionError(
            "invalid_content", "La firma no coincide con el formato inventariado."
        )
    digest = hashlib.sha256(payload).hexdigest()
    if previous:
        if previous.sha256 != digest:
            raise AcquisitionError(
                "document_conflict", "El DocumentId ya tiene otros bytes verificados."
            )
        return previous
    stored = state.storage.store(
        (payload,),
        original_name=f"document.{document.extension}",
        content_type=media_type,
        expected_size=len(payload),
        max_bytes=DOCUMENT_BYTES,
    )
    verify_document_type(state.storage, stored, document, DOCUMENT_BYTES)
    state.remember(document, stored)
    return stored


def extract_cached(document, stored, storage, settings, entry, output, ocr_pages):
    cache = output / "extractions"
    cache.mkdir(exist_ok=True)
    path = cache / f"{document.document_id}-{stored.sha256}.json"
    policy = hashlib.sha256(settings.extraction_ocr_config_path.read_bytes()).hexdigest()
    key = [
        EXTRACTION_CACHE_VERSION,
        ocr_pages,
        policy,
        str(settings.extraction_tesseract_cmd),
        str(settings.extraction_tessdata_path),
    ]
    if path.is_file():
        snapshot = read_json(path)
        if snapshot["key"] == key:
            entry.update(snapshot["coverage"])
            entry["fragments"] = [SimpleNamespace(**item) for item in snapshot["fragments"]]
            return True
    extract_document(document, stored, storage, settings, entry, ocr_pages=ocr_pages)
    if not entry.get("error_code") and not entry.get("native_stop_reason"):
        write_json(
            path,
            {
                "key": key,
                "coverage": {name: value for name, value in entry.items() if name != "fragments"},
                "fragments": [
                    {"text": fragment.text, "source_locator": fragment.source_locator}
                    for fragment in entry["fragments"]
                ],
            },
        )
    return False


def resume(source, output, manifest, settings, *, ocr_pages=OCR_PER_DOCUMENT):
    started = time.monotonic()
    processes, inventories, documents = archived_inventory(source)
    submissions = read_json(manifest)
    if not isinstance(submissions, list) or len(submissions) > EXPLORATORY_DOCUMENTS:
        raise ValueError("El manifiesto debe listar hasta 24 documentos.")
    paths = {}
    for item in submissions:
        identifier = item["document_id"]
        if not isinstance(identifier, str) or identifier not in documents or identifier in paths:
            raise ValueError(
                "DocumentId duplicado o sin correspondencia en el inventario archivado."
            )
        reference, _ = documents[identifier]
        if item["process_reference"] != reference:
            raise ValueError("El DocumentId no pertenece al proceso indicado.")
        path = item["file"]
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Cada documento requiere una ruta local.")
        path = Path(path)
        if path.drive.startswith("\\\\") or str(path).startswith(("\\\\", "//")):
            raise ValueError("El manifiesto requiere archivos locales, sin rutas de red.")
        paths[identifier] = manifest.parent / path

    state = DownloadState(output, LocalBinaryStorage(output / "binaries"))
    selected = set(paths) | {
        identifier
        for identifier, (_, document) in documents.items()
        if state.key(document) in state.receipts
    }
    per_process = Counter(documents[identifier][0] for identifier in selected)
    if len(selected) > EXPLORATORY_DOCUMENTS or any(
        count > EXPLORATORY_PER_PROCESS for count in per_process.values()
    ):
        raise ValueError("Se excedió el presupuesto de 24 documentos o tres por proceso.")

    metrics, errors, results, coverage = Counter(), [], [], []
    for reference, process in processes.items():
        entries = []
        for archived in inventories.get(reference, []):
            identifier = archived["document_id"]
            role = document_role(archived["name"])
            entry = {
                "document_id": identifier,
                "name": archived["name"],
                "extension": archived["extension"],
                "role": role,
                "role_hint": document_role_hint(archived["name"], role),
                "role_source": "filename",
                "complete": False,
                "status": "not_imported",
            }
            entries.append(entry)
            if identifier not in selected:
                continue
            document = documents[identifier][1]
            stored = state.cached(document, DOCUMENT_BYTES)
            if time.monotonic() - started + START_EXTRACTION_MARGIN >= EXPLORATORY_DURATION_SECONDS:
                entry["status"] = "duration_budget"
                metrics["deferred"] += 1
                continue
            if identifier in paths:
                try:
                    prior = stored
                    stored = import_file(paths[identifier], document, state, prior)
                    metrics["already_imported" if prior else "imported"] += 1
                except (AcquisitionError, OSError) as error:
                    errors.append(
                        {
                            "process_reference": reference,
                            "document_id": identifier,
                            "stage": "import",
                            "code": getattr(error, "code", type(error).__name__),
                        }
                    )
                    if stored is None:
                        entry["status"] = "import_rejected"
            if stored is None:
                if entry["status"] != "import_rejected":
                    entry["status"] = "stored_copy_unavailable"
                    errors.append(
                        {
                            "process_reference": reference,
                            "document_id": identifier,
                            "stage": "import",
                            "code": "stored_copy_unavailable",
                        }
                    )
                continue
            entry.update(
                provenance="manual_portal_download",
                sha256=stored.sha256,
                bytes=stored.observed_size,
            )
            try:
                reused = extract_cached(
                    document, stored, state.storage, settings, entry, output, ocr_pages
                )
                entry["extraction_reused"] = reused
                metrics["extractions_reused" if reused else "extractions_run"] += 1
                metrics["ocr_pages_this_run"] += 0 if reused else len(entry.get("ocr_pages", []))
            except (AcquisitionError, OSError) as error:
                entry.update(
                    status="extraction_failed",
                    error_code=getattr(error, "code", type(error).__name__),
                )
            if entry.get("error_code") or entry.get("native_stop_reason"):
                errors.append(
                    {
                        "process_reference": reference,
                        "document_id": identifier,
                        "stage": "extraction",
                        "code": entry.get("error_code") or entry["native_stop_reason"],
                    }
                )
        classification = classify_experience(entries, inventory_complete=bool(entries))
        for entry in entries:
            entry.pop("fragments", None)
        coverage.append({"process_reference": reference, "documents": entries})
        results.append(
            {
                "process_reference": reference,
                "codigo_proceso": process["codigo_proceso"],
                "commercial_category": process.get("primary_category"),
                "commercial_priority": process.get("commercial_priority"),
                **classification,
            }
        )
    summary = {
        "source_run": source.name,
        "processes": len(results),
        "with_inventory": sum(bool(i["documents"]) for i in coverage),
        "document_limit": DOCUMENT_BYTES,
        "ocr_pages_per_pdf": ocr_pages,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "request_credits": 0,
        "ai_calls": 0,
        "statuses": dict(Counter(row["status"] for row in results)),
        "errors": len(errors),
        **dict(metrics),
    }
    for name, data in (
        ("documents", coverage),
        ("experience_requirements", results),
        ("review_queue", sorted(results, key=lambda row: row["review_priority"])),
        ("errors", errors),
        ("metrics", summary),
    ):
        write_json(output / f"{name}.json", data)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-inventory-from", required=True, metavar="CORRIDA")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--tessdata", type=Path)
    parser.add_argument(
        "--ocr-pages", type=int, choices=range(OCR_PER_DOCUMENT + 1), default=OCR_PER_DOCUMENT
    )
    args = parser.parse_args(argv)
    name = args.resume_inventory_from
    if not re.fullmatch(r"en01-[a-z0-9_]+", name):
        parser.error("Nombre de corrida histórica inválido.")
    source = OUTPUT_ROOT / name
    output = OUTPUT_ROOT / f"en01-manual_{name[5:]}"
    try:
        if source.resolve() != source or output.resolve() != output:
            raise ValueError("Ruta fuera del almacenamiento experimental.")
        output.mkdir(parents=True, exist_ok=True)
        with exclusive_import(output):
            settings = settings_for_run(output, args.tesseract, args.tessdata, args.ocr_pages)
            result = resume(source, output, args.manifest, settings, ocr_pages=args.ocr_pages)
        print(json.dumps({"output": output.name, **result}))
        return 2 if result["errors"] or result.get("deferred") else 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"EN-01 importación: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
