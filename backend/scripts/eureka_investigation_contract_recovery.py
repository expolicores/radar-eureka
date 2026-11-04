"""Bounded contract-key inventory fallback for the existing seven research processes.

Produces normal sample receipts for at most two NEW economic documents per process.
MC-070 is an inventory-only regression case, never added to comparison pairs.
No general discovery, binary download, extraction, scoring or Radar in this command.
"""

import argparse
import json
import time
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from typing import Any

from public_procurement.documents.services import SourceDocument, build_document_inventory_source
from public_procurement.investigation.comparison_readiness import economic_document_priority
from public_procurement.investigation.document_recovery import recover_inventory
from public_procurement.investigation.economic_cycle import classify_stage


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf8"))


def source_document(data: dict[str, Any]) -> SourceDocument:
    values = {f.name: data[f.name] for f in fields(SourceDocument)}
    if isinstance(values["fecha_carga"], str):
        values["fecha_carga"] = datetime.fromisoformat(values["fecha_carga"])
    return SourceDocument(**values)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, required=True)
    parser.add_argument("--readiness-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_directory
    out.mkdir(parents=True, exist_ok=True)

    def dump(name: str, data: Any) -> None:
        (out / name).write_text(
            json.dumps(data, default=str, ensure_ascii=False, indent=2), encoding="utf8"
        )

    base = load(args.sample_directory / "selection.json")
    inventory = load(args.sample_directory / "inventories.json")
    contracts = load(args.sample_directory / "contracts-by-identity.json")
    scope = set(
        load(args.readiness_directory / "comparison_readiness.json")["scope"]["process_identities"]
    )
    selected = [p for p in base["rows"] if p["id_del_proceso"] in scope]
    if len(scope) != 7 or len(selected) != 7:
        raise ValueError("This closure is restricted to the existing seven process identities")
    probe = next(p for p in base["rows"] if p["referencia_del_proceso"] == "MC-070-2026")
    source = build_document_inventory_source()
    receipts = (
        load(out / "recovery-progress.json") if (out / "recovery-progress.json").exists() else {}
    )
    for receipt in receipts.values():
        for origins in receipt["discovery_provenance"].values():
            for origin in origins:
                origin.setdefault(
                    "lookup_mode",
                    "existing_inventory_receipt"
                    if origin["kind"] == "process_identifier"
                    else "official_identifier_lookup",
                )
    frozen_probe = args.readiness_directory / "mc070-correct-contract-inventory.json"

    class CachedProbe:
        def fetch(self, portfolio_id: str) -> list[SourceDocument]:
            return source.fetch(portfolio_id)

        def fetch_by_contract(self, contract_id: str) -> list[SourceDocument]:
            if contract_id == "CO1.PCCNTR.10103437" and frozen_probe.exists():
                return [source_document(d) for d in load(frozen_probe)]
            return source.fetch_by_contract(contract_id)

    for p in [*selected, probe]:
        ref = p["id_del_proceso"]
        if ref in receipts:
            continue
        cs = [c for c in contracts["rows"] if c["proceso_de_compra"] == p["id_del_portafolio"]]
        result = recover_inventory(
            CachedProbe(),
            portfolio_id=p["id_del_portafolio"],
            contracts=cs,
            cached_documents=[source_document(d) for d in inventory[ref]],
        )
        result["process_identity"] = ref
        result["process_code"] = p["referencia_del_proceso"]
        result["contract_ids"] = [c["id_contrato"] for c in cs]
        if not cs:
            result["warnings"].append(
                {"reason": "contract_identifier_unavailable_in_existing_metadata"}
            )
        receipts[ref] = result
        dump("recovery-progress.json", receipts)
        print(
            json.dumps(
                {
                    k: result[k]
                    for k in (
                        "process_code",
                        "primary_count",
                        "merged_count",
                        "additional_document_ids",
                    )
                }
            ),
            flush=True,
        )
        time.sleep(4)
    chosen, merged, rows = {}, {}, []
    for p in selected:
        ref = p["id_del_proceso"]
        receipt = receipts[ref]
        merged[ref] = receipt["documents"]
        additional = set(receipt["additional_document_ids"])
        candidates = [
            d
            for d in merged[ref]
            if d["id_documento"] in additional
            and classify_stage(d["original_name"])[0]
            in ("contract", "award", "evaluation_report", "economic_offer")
        ]
        candidates.sort(
            key=lambda d: (
                economic_document_priority(
                    d["original_name"], classify_stage(d["original_name"])[0]
                ),
                d["id_documento"],
            )
        )
        chosen[ref] = candidates[:2]
        if chosen[ref]:
            rows.append(p)
    dump("inventories.json", merged)
    dump("selected-documents.json", chosen)
    dump("contracts-by-identity.json", contracts)
    dump(
        "selection.json",
        {
            **base,
            "rows": rows,
            "contract_fallback": True,
            "frozen_comparison_processes": sorted(scope),
        },
    )
    dump("inventory-provenance.json", receipts)
    dump(
        "recovery-summary.json",
        {
            "pair_processes": 7,
            "regression_processes": 1,
            "additional_documents": sum(len(receipts[i]["additional_document_ids"]) for i in scope),
            "new_economic_documents_selected": sum(len(ds) for ds in chosen.values()),
            "processes_selected": len(rows),
            "max_new_documents_per_process": 2,
            "general_discovery_requests": 0,
        },
    )


if __name__ == "__main__":
    main()
