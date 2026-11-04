"""Publish the completed real sample offline; no network, OCR, alerts or scoring."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from public_procurement.investigation.research import ResearchReportStore, build_report
from public_procurement.shared.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument(
        "--refresh-research-facts",
        action="store_true",
        help="Offline: versioned research rules on existing fragments; no OCR or downloads",
    )
    args = parser.parse_args()
    directory = args.sample_directory.resolve()
    sample_path = directory / "sample-result.json"
    if not args.refresh_research_facts and (directory / "sample-research.json").exists():
        sample_path = directory / "sample-research.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    audit_path = directory / "acquisition-audit.json"
    if audit_path.exists():
        errors = {
            r["id_documento"]: r["error_code"]
            for r in json.loads(audit_path.read_text(encoding="utf-8"))
            if r["status"] == "failed"
        }
        for process in sample["processes"]:
            process["download_errors"] = errors
    if args.refresh_research_facts:
        from public_procurement.extraction.services import (
            TV_RESEARCH_CANONICAL_VERSION,
            ConsolidationService,
            build_extraction_service,
            build_tv_research_structured_service,
        )
        from public_procurement.shared.database import create_db_engine
        from public_procurement.shared.persistence import create_session_factory

        settings = Settings()
        sessions = create_session_factory(create_db_engine(settings))
        for process in sample["processes"]:
            reference = process["process"]["id_del_proceso"]
            if sample.get("research_policy") == "research-pair-v2":
                from eureka_investigation_sample import ReceiptInventory

                from public_procurement.documents.services import build_document_service

                docs = build_document_service(
                    sessions,
                    settings,
                    inventory=ReceiptInventory(
                        process["selected_documents"], already_selected=True
                    ),
                    limit_to_synced=True,
                )
                docs.sync(reference, dry_run=True)
                content = build_extraction_service(sessions, settings, document_service=docs)
                structured = build_tv_research_structured_service(
                    sessions, settings, content=content
                )
            else:
                structured = build_tv_research_structured_service(sessions, settings)
            consolidation = ConsolidationService(
                sessions, structured, TV_RESEARCH_CANONICAL_VERSION
            )
            facts, inserted = structured.extract(reference)
            facts = structured.list_facts(reference)
            process["facts"] = [asdict(f) for f in facts]
            process["research_facts_inserted"] = inserted
            if facts:
                process["canonicals"] = asdict(consolidation.run(reference))
        (directory / "sample-research.json").write_text(
            json.dumps(sample, default=str, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    contracts = json.loads((directory / "contracts-by-identity.json").read_text(encoding="utf-8"))
    fragments = {
        p["process"]["id_del_proceso"]: json.loads(path.read_text(encoding="utf-8"))
        if (
            path := directory
            / (p["process"]["id_del_proceso"].replace(".", "-") + "-fragments.json")
        ).exists()
        else []
        for p in sample["processes"]
    }
    report = build_report(sample, contracts["rows"], fragments)
    (directory / "research-report.json").write_text(
        json.dumps(report, default=str, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.publish:
        ResearchReportStore(Settings().local_storage_path.parent / "investigation").write(report)
    print(
        json.dumps(
            {
                "processes": len(report["processes"]),
                "signals": len(report["signals"]),
                "signal_status": report["signal_status"],
                "published": args.publish,
            }
        )
    )


if __name__ == "__main__":
    main()
