"""Close only frozen exact/high pairs using explicit local evidence directories.

No discovery, inventory requests, downloader, database writes or LLM are available here.
Optional local OCR results must be supplied as an existing fragment receipt.
"""

import argparse
import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from public_procurement.investigation.comparison_readiness import (
    ECONOMIC_STAGE_ORDER,
    build_readiness,
    documentary_award_winners,
    economic_document_priority,
    project_item,
    technical_scope,
)
from public_procurement.investigation.economic_cycle import (
    build_cycles,
    classify_stage,
    extract_rows,
)
from public_procurement.investigation.human_review import recommend_human_review
from public_procurement.investigation.research import ResearchReportStore
from public_procurement.shared.config import Settings


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf8"))


def dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf8")


def collect_local(
    directories: list[Path], identities: set[str]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    fragments: dict[str, dict[str, dict[str, Any]]] = {i: {} for i in identities}
    documents: dict[str, dict[str, Any]] = {}
    for directory in directories:
        sample = load(directory / "sample-result.json")
        for process in sample["processes"]:
            identity = process["process"]["id_del_proceso"]
            if identity not in identities:
                continue
            extractions = {
                e["document"]["document_version_id"]: e for e in process.get("extractions", [])
            }
            for saved in process.get("documents", []):
                version = saved.get("version")
                if not version:
                    continue
                e = extractions.get(version["id"], {})
                entry = {
                    "process_identity": identity,
                    "document_version_id": version["id"],
                    "name": version["original_name"],
                    "sha256": version["sha256"],
                    "selected": True,
                    "downloaded": True,
                    "extraction_status": e.get("status", "not_processed"),
                    "coverage_complete": e.get("diagnostics", {}).get("coverage_complete"),
                    "sha256_source": str(directory / "sample-result.json"),
                }
                previous = documents.get(version["id"])
                if not previous or entry["coverage_complete"] is True:
                    documents[version["id"]] = entry
            path = directory / (identity.replace(".", "-") + "-fragments.json")
            if path.exists():
                for f in load(path):
                    fragments[identity][f["id"]] = f
    return {i: list(fs.values()) for i, fs in fragments.items()}, documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, required=True)
    parser.add_argument("--evidence-directory", type=Path, action="append", default=[])
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--recovery-directory", type=Path)
    args = parser.parse_args()
    baseline = load(args.sample_directory / "economic-cycle.json")
    report = load(args.sample_directory / "research-cycle-report.json")
    scope = technical_scope(baseline)
    identities = set(scope["process_identities"])
    # One explicitly requested conflict case, never admitted as a new pair.
    supplemental = [p for p in baseline["processes"] if p["process_code"] == "MC-002-2026"]
    identities.update(p["process_identity"] for p in supplemental)
    directories = [args.sample_directory, *args.evidence_directory]
    fragments, docs = collect_local(directories, identities)
    review = copy.deepcopy(report)
    review["processes"] = [p for p in review["processes"] if p["id"] in identities]
    args.output_directory.mkdir(parents=True, exist_ok=True)
    document_audit = []
    for p in review["processes"]:
        identity = p["id"]
        local = sorted(
            (d for d in docs.values() if d["process_identity"] == identity),
            key=lambda d: economic_document_priority(d["name"], classify_stage(d["name"])[0]),
        )
        p["documents"] = local
        for d in local:
            fs = [
                f
                for f in fragments[identity]
                if f["document_version_id"] == d["document_version_id"]
            ]
            stage, basis = classify_stage(d["name"], "\n".join(f["text"][:200] for f in fs[:1]))
            if stage not in ECONOMIC_STAGE_ORDER:
                continue
            observations = [
                o for f in fs for o in extract_rows(f, complete=d["coverage_complete"] is True)
            ]
            tv = [o for o in observations if o["normalized_product"] == "televisor"]
            document_audit.append(
                {
                    **d,
                    "stage": stage,
                    "classification_basis": basis,
                    "priority": economic_document_priority(d["name"], stage),
                    "pages_reviewed": sorted(
                        {
                            f["source_locator"].get("page_number")
                            for f in fs
                            if f["source_locator"].get("page_number")
                        }
                    ),
                    "fragment_ids": [f["id"] for f in fs],
                    "item_price_rows": [
                        {
                            "id": o["id"],
                            "description": o["item_description"],
                            "fields": o["fields"],
                            "notes": o["notes"],
                            "evidence": o["evidence"],
                        }
                        for o in tv
                        if any("price" in k or "total" in k for k in o["fields"])
                    ],
                    "finding": "tv_economic_rows_available"
                    if any(any("price" in k for k in o["fields"]) for o in tv)
                    else "no_attributable_tv_unit_price_recovered_in_local_text"
                    if fs
                    else "local_document_without_usable_text",
                }
            )
    reviewed = build_cycles(review, fragments)
    # Reuse frozen observation identities, with an explicit unique overlap of source observations.
    projected = copy.deepcopy(baseline)
    local_cycles = {p["process_identity"]: p for p in reviewed["processes"]}
    ambiguous = []
    for p in projected["processes"]:
        if p["process_identity"] not in local_cycles:
            continue
        current = local_cycles[p["process_identity"]]
        for index, old in enumerate(p["products"]):
            if old["id"] not in scope["observation_ids"] and p["process_code"] != "MC-002-2026":
                continue
            old_ids = {o["id"] for o in old["observations"]}
            matches = [
                i for i in current["products"] if old_ids & {o["id"] for o in i["observations"]}
            ]
            if len(matches) == 1:
                updated = copy.deepcopy(matches[0])
                updated["reviewed_observation_id"] = updated["id"]
                updated["id"] = old["id"]
                p["products"][index] = updated
            elif len(matches) > 1:
                ambiguous.append(old["id"])
                # An ambiguous enrichment link is not a new contradiction in the source.
                # Preserve the baseline; never select one of the alternatives arbitrarily.
                old["readiness_audit_warnings"] = ["ambiguous_local_observation_link"]
        p["document_coverage"] = current["document_coverage"]
    result = build_readiness(
        projected, window_start=report["window_start"], window_before=report["window_before"]
    )
    result["created_at"] = datetime.now(UTC).isoformat()
    result["baseline_sha256"] = hashlib.sha256(
        (args.sample_directory / "economic-cycle.json").read_bytes()
    ).hexdigest()
    result["local_evidence_directories"] = [str(d) for d in directories]
    result["document_audit"] = sorted(
        document_audit, key=lambda d: (d["process_identity"], d["priority"], d["name"])
    )
    result["process_economic_review"] = [
        {
            "process_identity": identity,
            "process_code": next(
                p["process_code"]
                for p in baseline["processes"]
                if p["process_identity"] == identity
            ),
            "review_order": [
                "signed_contract",
                "offer_acceptance",
                "award_act",
                "evaluation_report",
                "winning_offer",
            ],
            "documents": [
                {
                    k: d[k]
                    for k in (
                        "name",
                        "stage",
                        "document_version_id",
                        "pages_reviewed",
                        "coverage_complete",
                        "finding",
                    )
                }
                for d in result["document_audit"]
                if d["process_identity"] == identity
            ],
            "finding": "no_verified_attributable_purchase_price_recovered"
            if not any(
                r["preferred_purchase_price"]
                for r in result["comparison_readiness"]
                if r["process_identity"] == identity
            )
            else "purchase_price_recovered",
        }
        for identity in scope["process_identities"]
    ]
    rows_by_id = {r["observation_id"]: r for r in result["comparison_readiness"]}
    for row in result["comparison_readiness"]:
        checked = [
            d for d in result["document_audit"] if d["process_identity"] == row["process_identity"]
        ]
        globals_ = next(
            p["process_global_contracts"]
            for p in baseline["processes"]
            if p["process_identity"] == row["process_identity"]
        )
        row["economic_blocker"] = (
            "No se recuperó un unitario de compra atribuible a esta observación. "
            "Los totales de contrato/adjudicación disponibles son globales del proceso "
            "y no se dividen por la cantidad de TV."
            if row["preferred_purchase_price"] is None
            else "Precio de compra recuperado."
        )
        if row["unaccepted_offer_unit_price"]:
            row["economic_blocker"] += (
                " Existe unitario de oferta "
                + row["unaccepted_offer_unit_price"]
                + " COP, sin prueba suficiente de aceptación para este ítem."
            )
        row["process_global_totals_not_allocated"] = globals_
        if not row["supplier"]:
            winners = documentary_award_winners(fragments[row["process_identity"]])
            names = {w["supplier"] for w in winners}
            if len(names) == 1:
                row["supplier"] = next(iter(names))
                row["supplier_scope"] = "local_award_document_process_scope_only"
                row["supplier_evidence"] = winners
                row["economic_states"] = [
                    s for s in row["economic_states"] if s != "missing_supplier"
                ]
                row["warnings"] = [
                    w
                    for w in row["warnings"]
                    if w != "supplier_unavailable_not_alone_a_comparison_blocker"
                ]
                row["warnings"].append(
                    "award_winner_does_not_identify_which_quotation_was_accepted"
                )
        row["documents_checked"] = [
            {k: d[k] for k in ("name", "stage", "document_version_id", "pages_reviewed", "finding")}
            for d in checked
        ]
    for pair in result["pairs"]:
        for side, key in zip(("a", "b"), pair["observation_ids"], strict=True):
            pair["economic_blocker_" + side] = rows_by_id[key]["economic_blocker"]
            pair["documents_checked_" + side] = rows_by_id[key]["documents_checked"]
    result["supplemental_conflict_review"] = [
        project_item(p, i, [])
        for p in projected["processes"]
        if p["process_code"] == "MC-002-2026"
        for i in p["products"]
        if "model_reused_for_incompatible_sizes" in i["conflicts"]
    ]
    recommendations = result["comparison_readiness"] + result["supplemental_conflict_review"]
    recovery = (
        load(args.recovery_directory / "inventory-provenance.json")
        if args.recovery_directory
        else {}
    )
    for row in recommendations:
        recovered = recovery.get(row["process_identity"], {})
        if recovered and not recovered.get("contract_ids"):
            row["human_review_reasons"] = sorted(
                set(row["human_review_reasons"] + ["incomplete_document_cycle"])
            )
        if not row["preferred_purchase_price"] and any(
            q["count"] for q in recovered.get("lookups", [])
        ):
            row["human_review_reasons"] = sorted(
                set(row["human_review_reasons"] + ["contract_documents_found_but_not_resolved"])
            )
    for pair in result["pairs"]:
        sides = [rows_by_id[i] for i in pair["observation_ids"]]
        pair["human_review_reasons_a"], pair["human_review_reasons_b"] = [
            r["human_review_reasons"] for r in sides
        ]
        pair["human_review_reasons"] = sorted(
            {reason for r in sides for reason in r["human_review_reasons"]}
        )
    process_reviews = []
    for identity in sorted({r["process_identity"] for r in recommendations}):
        members = [
            r
            for r in recommendations
            if r["process_identity"] == identity and r["human_review_recommended"]
        ]
        if members:
            process_reviews.append(
                {
                    "process_identity": identity,
                    "process_code": members[0]["process_code"],
                    **recommend_human_review(
                        potential=True,
                        ready=False,
                        reasons=[s for r in members for s in r["human_review_reasons"]],
                    ),
                }
            )
    # Explicit regression case, inventory-only; never admitted as a new comparison pair.
    regression = next((p for p in report["processes"] if p["reference"] == "MC-070-2026"), None)
    if (
        args.recovery_directory
        and regression
        and any(d.get("error") == "page_limit" for d in regression["documents"])
    ):
        process_reviews.append(
            {
                "process_identity": regression["id"],
                "process_code": regression["reference"],
                **recommend_human_review(
                    potential=regression["tv_confirmed"],
                    ready=False,
                    reasons=[
                        "oversized_document",
                        "extraction_failure",
                        "contract_documents_found_but_not_resolved",
                    ],
                ),
                "scope": "explicit_contract_key_regression_case_not_comparison_pair",
            }
        )
    result["process_human_review"] = process_reviews
    if args.recovery_directory:
        result["contract_document_recovery"] = load(
            args.recovery_directory / "recovery-summary.json"
        )
        result["document_discovery_provenance"] = recovery
    before_prices = {
        p["process_identity"]
        for p in baseline["processes"]
        if p["process_identity"] in scope["process_identities"]
        and any(i["purchase_price"] for i in p["products"])
    }
    after_prices = {
        r["process_identity"]
        for r in result["comparison_readiness"]
        if r["preferred_purchase_price"]
    }
    result["summary"].update(
        {
            "unit_price_counter_scope": "verified_purchase_prices_in_frozen_pair_observations",
            "human_review_processes": len(process_reviews),
            "human_review_pairs": sum(p["human_review_recommended"] for p in result["pairs"]),
            "additional_documentary_suppliers": len(
                {
                    r["process_identity"]
                    for r in result["comparison_readiness"]
                    if r["supplier_scope"] == "local_award_document_process_scope_only"
                }
            ),
            "additional_processes_with_purchase_price": len(after_prices - before_prices),
            "documents_economically_reviewed": len(document_audit),
            "ambiguous_observation_links": len(ambiguous),
            "conflicts_resolved": sum(
                len(
                    set(i["conflicts"])
                    - set(
                        next(
                            j
                            for q in projected["processes"]
                            for j in q["products"]
                            if j["id"] == i["id"]
                        )["conflicts"]
                    )
                )
                for p in baseline["processes"]
                for i in p["products"]
                if i["id"] in scope["observation_ids"]
            ),
            "unresolved_conflict_observations": sum(
                bool(r["critical_conflicts"]) for r in result["comparison_readiness"]
            ),
            "supplemental_conflicts_unresolved": len(result["supplemental_conflict_review"]),
            "unresolved_conflict_processes": len(
                {
                    r["process_identity"]
                    for r in result["comparison_readiness"] + result["supplemental_conflict_review"]
                    if r["critical_conflicts"]
                }
            ),
            "manual_review_cases_including_supplemental": len(
                {
                    r["process_identity"]
                    for r in result["comparison_readiness"] + result["supplemental_conflict_review"]
                    if r["requires_manual_review"]
                }
            ),
            "network_requests": 0,
            "new_downloads": 0,
            "database_writes": 0,
        }
    )
    pending_path = args.output_directory / "local-ocr-receipt.json"
    if pending_path.exists():
        result["local_ocr_review"] = load(pending_path)
    dump(args.output_directory / "comparison_readiness.json", result)
    dump(args.output_directory / "document_review.json", result["document_audit"])
    dump(args.output_directory / "pair_blockers.json", result["pairs"])
    dump(args.output_directory / "run_summary.json", result["summary"])
    lines = [
        "# Cierre económico de los pares técnicos de 60 días",
        "",
        "```json",
        json.dumps(result["summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "Precios A/B: solo compras verificadas; una celda vacía no se completa "
        "con cotización o total global.",
        "",
        "| Par | Proceso A / observación | Proceso B / observación | Producto A/B | Nivel | "
        "Precio A | Precio B | Estado | Bloqueo A | Bloqueo B | Etapa faltante A/B | "
        "Resolvible localmente | Revisión manual |",
        "|---:|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    def cell(value: Any) -> str:
        return (
            str(value if value is not None else "No recuperado")
            .replace("|", "/")
            .replace("\n", " ")
        )

    for pair in result["pairs"]:
        lines.append(
            "| "
            + " | ".join(
                cell(v)
                for v in (
                    pair["number"],
                    pair["process_code_a"] + " / " + pair["observation_ids"][0][:12],
                    pair["process_code_b"] + " / " + pair["observation_ids"][1][:12],
                    pair["product_a"][:90] + " / " + pair["product_b"][:90],
                    pair["comparability_level"],
                    pair["price_a"],
                    pair["price_b"],
                    pair["status"],
                    pair["economic_blocker_a"] + " Faltantes: " + cell(pair["blockers_a"]),
                    pair["economic_blocker_b"] + " Faltantes: " + cell(pair["blockers_b"]),
                    [pair["missing_document_or_stage_a"], pair["missing_document_or_stage_b"]],
                    pair["deterministically_resolvable_with_available_evidence"],
                    pair["requires_manual_review"],
                )
            )
            + " |"
        )
    lines += [
        "",
        "## Observaciones y documentos",
        "",
        "Cada observación mantiene su ID original. JSON conserva cantidades, proveedor, "
        "alternativas, documentos/páginas/SHA y estado; las repeticiones de procesos son "
        "observaciones diferentes, no nuevas compras.",
    ]
    for row in result["comparison_readiness"] + result["supplemental_conflict_review"]:
        lines += [
            "",
            "### " + row["process_code"] + " / " + row["observation_id"][:12],
            "",
            row["product_description"],
            "",
            "Estado: "
            + row["readiness_status"]
            + "; cantidad: "
            + cell(row["quantity"])
            + "; proveedor: "
            + cell(row["supplier"]),
            "Conflictos: " + cell(row["conflicts"]),
            "Faltantes: " + cell(row["missing_fields"]),
        ]
        lines += [
            "- "
            + cell(e["source_document"])
            + " p."
            + cell(e.get("source_page"))
            + " / "
            + cell(e["extraction_method"])
            for e in row["evidence_refs"]
        ]
    (args.output_directory / "blocker_matrix.md").write_text("\n".join(lines), encoding="utf8")
    if args.publish:
        store = ResearchReportStore(Settings().local_storage_path.parent / "investigation")
        current = store.read()
        if current.get("window_start") != report["window_start"] or {
            p["id"] for p in current["processes"]
        } != {p["id"] for p in report["processes"]}:
            raise ValueError(
                "Current UI report differs from the reviewed baseline; not overwritten"
            )
        current["comparison_readiness"] = result
        by_process = {p["process_identity"]: p for p in process_reviews}
        for process in current["processes"]:
            if process["id"] in by_process:
                process["research_human_review"] = by_process[process["id"]]
        if result["signals"]:
            replacements = {
                p["id"]: p["comparison"] for p in result["pairs"] if p["status"] == "ready"
            }
            current["comparisons"] = [replacements.get(p["id"], p) for p in current["comparisons"]]
            signals = {s["id"]: s for s in current["signals"]}
            signals.update({s["id"]: s for s in result["signals"]})
            current["signals"] = list(signals.values())
            current["signal_status"] = "signals_supported"
            current["summary"]["signals_generated"] = len(signals)
            current["summary"]["comparisons_possible"] = sum(
                p["comparison_eligible"] for p in current["comparisons"]
            )
        # Historical receipts stay immutable; this only updates the local UI projection.
        store.write(current)
    print(json.dumps(result["summary"], ensure_ascii=True))


if __name__ == "__main__":
    main()
