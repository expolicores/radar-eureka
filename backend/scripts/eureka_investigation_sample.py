"""Run an explicit Socrata research selection through the existing document services.

Selection/inventory/contract JSON are acquisition receipts, not public UI data. This
command does not discover more processes or invoke Radar, CDP, alerts or Web Search.
"""

import argparse
import json
import time
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from public_procurement.documents.services import SourceDocument, build_document_service
from public_procurement.extraction.services import (
    TV_RESEARCH_CANONICAL_VERSION,
    ConsolidationService,
    build_extraction_service,
    build_tv_research_structured_service,
)
from public_procurement.ingestion.adapters.socrata_processes import map_process
from public_procurement.ingestion.services import ProcessQuery, build_process_ingestion_service
from public_procurement.investigation.research import document_stage
from public_procurement.shared.config import Settings
from public_procurement.shared.database import create_db_engine
from public_procurement.shared.persistence import create_session_factory
from public_procurement.shared.text import normalize_text


def selected_document(name: str) -> bool:
    value = normalize_text(name)
    if any(
        t in value
        for t in ("cedula", "certificacion bancaria", "hoja de vida", "antecedentes", "rut ")
    ):
        return False
    return document_stage(name) in ("contract", "specifications", "award", "offer") or any(
        term in value
        for term in ("anexo", "ficha tecnica", "especifica", "pliego", "presupuesto", "cotizac")
    )


class ReceiptInventory:
    def __init__(self, documents: list[dict[str, Any]], *, already_selected: bool = False) -> None:
        self.documents = documents
        self.already_selected = already_selected

    def fetch(self, portfolio: str) -> list[SourceDocument]:
        return [
            SourceDocument(
                **{
                    **d,
                    "fecha_carga": datetime.fromisoformat(d["fecha_carga"])
                    if d["fecha_carga"]
                    else None,
                }
            )
            for d in self.documents
            if (self.already_selected or selected_document(d["original_name"]))
            and d["portfolio_id"] == portfolio
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    out = args.sample_directory.resolve()
    if (out / "sample-result.json").exists():
        raise ValueError("La muestra ya finalizó; no se ejecuta otra corrida implícita.")
    selection = json.loads((out / "selection.json").read_text(encoding="utf-8"))
    inventories = json.loads((out / "inventories.json").read_text(encoding="utf-8"))
    chosen_path = out / "selected-documents.json"
    chosen_documents = (
        json.loads(chosen_path.read_text(encoding="utf-8")) if chosen_path.exists() else None
    )
    start, before = (
        date.fromisoformat(selection["window_start"]),
        date.fromisoformat(selection["window_before"]),
    )
    processes = [map_process(row) for row in selection["rows"]]
    if len({p.identity for p in processes}) != len(processes):
        raise ValueError("Selección con identidades repetidas.")
    if any(
        p.published_on is None
        or not start <= p.published_on < before
        or p.status not in selection.get("mature_statuses", ["Seleccionado"])
        for p in processes
    ):
        raise ValueError("Proceso fuera de ventana o sin el estado maduro seleccionado.")
    settings = Settings()
    sessions = create_session_factory(create_db_engine(settings))
    build_process_ingestion_service(sessions).persist(
        processes, ProcessQuery(published_from=start, published_before=before)
    )
    result: dict[str, Any] = {
        "source": "socrata_secop",
        "inventory_provenance_file": str(out / "inventory-provenance.json")
        if (out / "inventory-provenance.json").exists()
        else None,
        "started_at": datetime.now(UTC),
        "window_start": str(start),
        "window_before": str(before),
        "selection": selection,
        "processes": [],
        "research_policy": "research-pair-v2",
        "comparison_policy": selection.get("research_policy", "research-pair-v2"),
    }

    def dump(name: str, data: Any) -> None:
        temporary = out / (name + ".tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        temporary.replace(out / name)

    for row in selection["rows"]:
        ref = row["id_del_proceso"]
        item: dict[str, Any] = {
            "process": row,
            "inventory": inventories.get(ref, []),
            "errors": [],
            "extractions": [],
        }
        result["processes"].append(item)
        print("PROCESS", ref, flush=True)
        try:
            if ref not in inventories:
                raise ValueError(
                    "Inventario Socrata no disponible; no se sustituye por otra fuente."
                )
            docs = build_document_service(
                sessions,
                settings,
                inventory=ReceiptInventory(
                    chosen_documents.get(ref, [])
                    if chosen_documents is not None
                    else inventories[ref],
                    already_selected=chosen_documents is not None,
                ),
                limit_to_synced=True,
            )
            selected = docs.sync(ref)
            item["selected_documents"] = [asdict(d) for d in selected]
            item["reused_downloads"] = sum(
                docs.latest_version(d.id) is not None for d in docs.list_documents(ref)
            )
            print("DOCUMENTS", len(selected), "REUSED", item["reused_downloads"], flush=True)
            item["download"] = asdict(docs.download(ref, only_missing=True))
            item["documents"] = [
                {
                    "document": asdict(d),
                    "version": asdict(v) if (v := docs.latest_version(d.id)) else None,
                }
                for d in docs.list_documents(ref)
            ]
            print("DOWNLOAD", item["download"], flush=True)
            dump("sample-progress.json", result)
            extraction = build_extraction_service(sessions, settings, document_service=docs)
            for e in extraction.extract_process(ref):
                payload = asdict(e)
                payload.pop("fragments", None)
                item["extractions"].append(payload)
                print(
                    "EXTRACT",
                    str(e.document.document_id),
                    e.status.value,
                    e.page_count,
                    "reused" if e.reused else "new",
                    flush=True,
                )
                dump("sample-progress.json", result)
            structured = build_tv_research_structured_service(
                sessions, settings, content=extraction
            )
            facts, inserted = structured.extract(ref)
            item["facts"] = [asdict(f) for f in structured.list_facts(ref)]
            item["research_facts_inserted"] = inserted
            item["canonicals"] = (
                asdict(
                    ConsolidationService(sessions, structured, TV_RESEARCH_CANONICAL_VERSION).run(
                        ref
                    )
                )
                if facts
                else {"facts": []}
            )
            _, fragments = extraction.content_for_process(ref)
            dump(ref.replace(".", "-") + "-fragments.json", [asdict(f) for f in fragments])
            print("FACTS", len(facts), "CANONICALS", len(item["canonicals"]["facts"]), flush=True)
        except Exception as exc:
            item["errors"].append({"type": type(exc).__name__, "message": str(exc)[:240]})
            print("PROCESS_ERROR", ref, type(exc).__name__, flush=True)
        dump("sample-progress.json", result)
        time.sleep(1)
    result["finished_at"] = datetime.now(UTC)
    dump("sample-result.json", result)
    print("COMPLETE", flush=True)


if __name__ == "__main__":
    main()
