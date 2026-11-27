"""Offline recomputation of EN-01 findings for an exploration, from stored binaries only.

Stored results do not keep the extracted text that the findings layer needs, so this tool
re-extracts the binaries already held (SHA-256 verified on open, same selective OCR plan as
stage 3 and the targeted analysis, local OCR only), classifies them with the unchanged
classifier and assesses the presentation finding. No network, no downloads, no POST.

Document inventories are layered: stage 1 run, then SECOP I stage 3, then a targeted run;
the later layer replaces the earlier one for the same process. Output is a new file
``findings_recomputed.json`` in the stage 1 run; an existing file is never overwritten.
"""

import argparse
import json
import os

import eureka_nacional_secop1_flow as secop1
from eureka_nacional_experience import classify_experience
from eureka_nacional_findings import assess_finding, load_human_reviews

OUTPUT_FILE = "findings_recomputed.json"
SUPPORT_OCR_PAGES = 2  # same per-document OCR as the targeted analysis for support documents


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def held_receipts(root):
    """Receipts of every run under the experimental root, keyed ``document_id:extension``."""
    runs = sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("en01-"))
    receipts = {}
    for run in runs:
        for key, record in secop1.load_receipts(run).items():
            receipts.setdefault(key, (run, record))
    # Fallback for documents stored without a receipt file: content-addressed path only, and
    # only when that binary exists. ``relative_path`` is a provider path, never a storage path.
    for run in runs:
        for case in read_json(run / "documents.json", []) or []:
            for doc in case.get("documents", []):
                sha = doc.get("sha256")
                key = f"{doc.get('document_id')}:{doc.get('extension')}"
                if not sha or key in receipts:
                    continue
                storage_path = f"sha256/{sha[:2]}/{sha}"
                path = run / "binaries" / storage_path
                if path.is_file():
                    receipts[key] = (
                        run,
                        {
                            "storage_path": storage_path,
                            "sha256": sha,
                            "observed_size": path.stat().st_size,
                            "content_type": "application/pdf",
                        },
                    )
    return receipts


def layered_cases(run, secop1_results=None, targeted=None):
    cases = {}
    for layer, path in (("stage1", run), ("secop1_stage3", secop1_results), ("targeted", targeted)):
        if path is None:
            continue
        for case in read_json(path / "documents.json", []) or []:
            cases[case["process_reference"]] = (layer, case["documents"])
    return cases


def process_index(*runs):
    processes = {}
    for path in filter(None, runs):
        for process in (read_json(path / "processes.json", {}) or {}).get("processes", []):
            processes.setdefault(process["process_reference"], process)
    return processes


def recompute(run, *, runner, settings, secop1_results=None, targeted=None, root=None):
    root = root or run.parent
    receipts = held_receipts(root)
    processes = process_index(run, targeted)
    stored = {
        r["process_reference"]: r for r in read_json(run / "experience_requirements.json", [])
    }
    if secop1_results is not None:
        stored.update(
            {
                r["process_reference"]: r
                for r in read_json(secop1_results / "experience_requirements.json", [])
            }
        )
    if targeted is not None:
        stored.update(
            {
                r["process_reference"]: r
                for r in (read_json(targeted / "validation_results.json", {}) or {}).get(
                    "results", []
                )
            }
        )
    reviews = load_human_reviews()
    rows = []
    for reference, (layer, inventory) in sorted(
        layered_cases(run, secop1_results, targeted).items()
    ):
        if reference not in stored:
            continue  # only processes that were analyzed in the exploration
        budget = secop1.OcrBudget()
        documents = []
        for prior in inventory:
            document = {
                key: prior.get(key)
                for key in ("document_id", "name", "role", "role_hint", "extension")
            }
            document["document_id"] = str(document["document_id"])
            document["complete"] = False
            documents.append(document)
            if document.get("role") == "excluded":
                continue
            if document.get("extension") not in {"pdf", "docx"}:
                document["validation_gap"] = "formato_no_procesable"
                continue
            held = receipts.get(f"{document['document_id']}:{document['extension']}")
            if held is None:
                document["validation_gap"] = "no_descargado"
                continue
            source_run, record = held
            storage = runner.spike.LocalBinaryStorage(source_run / "binaries")
            spike_document = runner.spike.SpikeDocument(
                document["name"], document["extension"], "", document["document_id"]
            )
            binary = runner.StoredBinary(**record)
            try:
                runner.verify_document_type(storage, binary, spike_document, runner.DOCUMENT_BYTES)
                secop1.extract_with_ocr_plan(
                    runner.extract_document,
                    spike_document,
                    binary,
                    storage,
                    settings,
                    document,
                    budget,
                    per_document=(
                        secop1.GOVERNING_OCR_PAGES
                        if document.get("role") in {"primary", "amendment"}
                        else SUPPORT_OCR_PAGES
                    ),
                )
            except Exception as error:
                document["validation_gap"] = f"binario_no_verificado:{type(error).__name__}"
                document["complete"] = False
                continue
            document["receipt_run"] = source_run.name
            if not document["complete"]:
                document["validation_gap"] = "cobertura_incompleta"
        classification = classify_experience(documents, inventory_complete=bool(documents))
        process = processes.get(reference, {})
        previous = stored[reference]
        finding = assess_finding(
            classification,
            documents,
            identifiers=[reference, process.get("source_identity"), previous.get("constancia")],
            human_reviews=reviews,
        )
        rows.append(
            {
                "process_reference": reference,
                "evidence_layer": layer,
                "stored_status": previous.get("status"),
                "stored_review_category": previous.get("review_category"),
                "formal_status_differs_from_stored": previous.get("status")
                != classification["status"],
                "documents": [
                    {
                        key: doc.get(key)
                        for key in (
                            "name",
                            "role",
                            "extension",
                            "complete",
                            "total_pages",
                            "pending_pages",
                            "receipt_run",
                            "validation_gap",
                        )
                    }
                    for doc in documents
                ],
                "finding": finding,
            }
        )
    return rows


def write_new(path, data):
    if path.exists():
        raise FileExistsError(f"{path.name} ya existe; no se sobrescribe.")
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def main(argv=None):
    import eureka_nacional_en01 as runner

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run")
    parser.add_argument("--secop1-results")
    parser.add_argument("--targeted")
    parser.add_argument("--tesseract", default="tesseract")
    args = parser.parse_args(argv)
    root = runner.OUTPUT_ROOT
    try:
        run, stage3, targeted = (
            secop1.ensure_inside(root, root / secop1.run_dir_name(name)) if name else None
            for name in (args.run, args.secop1_results, args.targeted)
        )
    except ValueError as error:
        print(f"EN-01: {error}")
        return 1
    settings = runner.settings_for_run(run, args.tesseract, None, secop1.PASS_PAGES)
    rows = recompute(
        run, runner=runner, settings=settings, secop1_results=stage3, targeted=targeted
    )
    write_new(
        run / OUTPUT_FILE,
        {
            "network_requests": 0,
            "ai_calls": 0,
            "layers": [p.name for p in (run, stage3, targeted) if p is not None],
            "rows": rows,
        },
    )
    print(json.dumps([[r["process_reference"], r["finding"]["category"]] for r in rows]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
