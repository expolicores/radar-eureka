"""Replay of EN-01 inventories and verified local PDFs, without browser or downloader."""

import argparse
import json
import re
import tempfile
import time
from collections import Counter
from pathlib import Path

from eureka_nacional_en01 import (
    OCR_PER_DOCUMENT,
    OUTPUT_ROOT,
    classify_experience,
    document_role,
    extract_document,
    settings_for_run,
    write_json,
)
from spike_licitaciones_info import SpikeDocument

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError, StoredBinary


def replay(source, output, settings, ocr_pages):
    started = time.monotonic()
    parent_cpu = time.process_time()
    metrics = Counter()
    assertions = Counter()
    classifications = Counter()
    reviews = Counter()
    errors = Counter()
    results = []
    inventory = json.loads((source / "documents.json").read_text(encoding="utf-8"))
    storage = LocalBinaryStorage(source / "binaries")
    for process in inventory:
        documents = []
        for prior in process["documents"]:
            entry = {
                "document_id": prior["document_id"],
                "name": prior["name"],
                "role": document_role(prior["name"]),
                "role_source": "filename",
                "complete": False,
                "status": "not_replayed",
            }
            documents.append(entry)
            if not prior.get("sha256") or prior["extension"] != "pdf":
                continue
            digest = prior["sha256"]
            if not re.fullmatch("[a-f0-9]{64}", digest):
                raise ValueError("Hash documental inválido en el manifiesto.")
            relative = f"sha256/{digest[:2]}/{digest}"
            path = (storage.root / relative).resolve()
            if not path.is_relative_to(storage.root):
                raise ValueError("PDF fuera del almacenamiento local.")
            metrics["pdfs_manifested"] += 1
            try:
                size = path.stat().st_size
                metrics["pdfs_available"] += 1
                metrics["input_bytes"] += size
                stored = StoredBinary(digest, relative, size, "application/pdf")
                doc = SpikeDocument(entry["name"], "pdf", "", entry["document_id"])
                extract_document(doc, stored, storage, settings, entry, ocr_pages=ocr_pages)
            except (AcquisitionError, OSError) as exc:
                code = getattr(exc, "code", type(exc).__name__)
                errors[code] += 1
                entry.update(status="extraction_failed", error_code=code)
                continue
            entry["input_bytes"] = size
            error = entry["error_code"] or entry["native_stop_reason"]
            if error:
                errors[error] += 1
            for key, value in {
                "total_pages": entry["total_pages"],
                "native_pages_visited": entry["native_pages_visited"],
                "native_pages_with_text": len(entry["native_pages"]),
                "processed_pages": len(entry["pages_seen"]),
                "ocr_required_pages": len(entry["ocr_required_pages"]),
                "ocr_pages": len(entry["ocr_pages"]),
                "ocr_success_pages": len(entry["ocr_success_pages"]),
                "pending_pages": len(entry["pending_pages"]),
                "characters": sum(len(f.text) for f in entry["fragments"]),
                "pdfs_complete": int(entry["complete"]),
                "extraction_seconds": entry["extraction_seconds"],
                "native_cpu_seconds": entry["native_cpu_seconds"] or 0,
            }.items():
                metrics[key] += value
        classified_at = time.monotonic()
        result = classify_experience(documents, inventory_complete=bool(documents))
        classification_seconds = time.monotonic() - classified_at
        metrics["classification_seconds"] += classification_seconds
        assertions.update(item["assertion_type"] for item in result["evidence"])
        classifications[result["status"]] += 1
        reviews[result["review_category"]] += 1
        for document in documents:
            document.pop("fragments", None)
        results.append(
            {
                "process_reference": process["process_reference"],
                "classification_seconds": classification_seconds,
                "documents": documents,
                **result,
            }
        )
    resolved = classifications["experience_required"] + classifications["no_experience_required"]
    summary = {
        **{key: round(value, 6) for key, value in metrics.items()},
        "processes": len(results),
        "resolved": resolved,
        "unresolved": len(results) - resolved,
        "assertions": dict(assertions),
        "classifications": dict(classifications),
        "reviews": dict(reviews),
        "errors": dict(errors),
        "ocr_budget_per_pdf": ocr_pages,
        "request_credits": 0,
        "ai_calls": 0,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "parent_cpu_seconds": round(time.process_time() - parent_cpu, 6),
    }
    write_json(output / "replay.json", results)
    write_json(output / "metrics.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--tessdata", type=Path)
    parser.add_argument(
        "--ocr-pages", type=int, choices=range(OCR_PER_DOCUMENT + 1), default=OCR_PER_DOCUMENT
    )
    args = parser.parse_args(argv)
    source = args.source.resolve()
    if OUTPUT_ROOT.resolve() != OUTPUT_ROOT or not source.is_relative_to(OUTPUT_ROOT):
        parser.error("El replay requiere un directorio de corrida dentro de .local.")
    if not (source / "documents.json").is_file():
        parser.error("No se encontró el inventario documental de la corrida.")
    output = Path(tempfile.mkdtemp(prefix="pdf-replay-", dir=OUTPUT_ROOT))
    settings = settings_for_run(output, args.tesseract, args.tessdata, args.ocr_pages)
    summary = replay(source, output, settings, args.ocr_pages)
    print(json.dumps({"output": str(output), **summary}, ensure_ascii=False))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
