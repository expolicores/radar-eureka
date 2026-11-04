"""Derived, offline readiness for a frozen list of technical pairs. No acquisition."""

import re
from collections import Counter
from typing import Any

from .domain.television import Television, positive_decimal
from .human_review import recommend_human_review, review_reasons
from .research_comparison import compare_public_purchases

ECONOMIC_STAGE_ORDER = (
    "contract",
    "award",
    "evaluation_report",
    "economic_offer",
)


def economic_document_priority(name: str, stage: str) -> float:
    folded = name.casefold()
    if stage == "contract":
        return 1 if "firmado" in folded else 1.1
    if stage == "award":
        return 2 if "aceptaci" in folded else 3
    return {"evaluation_report": 4, "economic_offer": 5}.get(stage, 99)


def documentary_award_winners(fragments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """An explicit operative award clause identifies a supplier, never its item price."""
    from .economic_cycle import classify_stage

    winners = []
    for f in fragments:
        if classify_stage(f["original_name"], f["text"])[0] != "award":
            continue
        match = re.search(
            r"\bART[ÍI]CULO\s+PRIMERO\b.*?\bAdjudicar\b.*?\ba\s+"
            r"([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9 &.,\n-]{3,140}S\.?\s*A\.?\s*S\.?)\s*,\s*NIT",
            f["text"],
            re.S,
        )
        if match:
            winners.append(
                {
                    "supplier": re.sub(r"\s+", " ", match[1]).strip(),
                    "scope": "process_award_not_item_price_or_offer_identity",
                    "source_document": f["original_name"],
                    "source_page": f["source_locator"].get("page_number"),
                    "fragment_id": f["id"],
                    "document_version_id": f["document_version_id"],
                    "input_sha256": f["source_locator"].get("input_sha256"),
                    "extraction_method": f["source_locator"].get("extraction_method"),
                    "evidence_text": match[1],
                }
            )
    return winners


def technical_scope(cycle: dict[str, Any]) -> dict[str, Any]:
    pairs = [p for p in cycle["comparisons"] if p.get("comparability_level") in ("exact", "high")]
    return {
        "pairs": pairs,
        "process_identities": sorted({i for p in pairs for i in p["processes"]}),
        "observation_ids": sorted({i for p in pairs for i in p["observation_ids"]}),
    }


def _evidence_refs(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep item excerpts, not complete legal pages or provider bank sections."""
    result: dict[tuple[Any, ...], dict[str, Any]] = {}
    for obs in item["observations"]:
        for evidence in obs["evidence"]:
            key = (
                evidence.get("document_version_id"),
                evidence.get("fragment_id"),
                evidence.get("source_page"),
                evidence.get("evidence_text"),
            )
            result[key] = evidence
    return list(result.values())


def _complete_provenance(price: dict[str, Any] | None) -> bool:
    if not price:
        return False
    alternatives = price.get("evidence", [])
    return bool(alternatives) and all(
        bool(a.get("evidence"))
        and all(
            all(e.get(k) for k in ("source_document", "document_version_id", "input_sha256"))
            and bool(e.get("extraction_method"))
            and bool(e.get("source_page") or e.get("source_locator"))
            for e in a["evidence"]
        )
        and (
            a.get("value_origin") != "calculated"
            or (
                len(a.get("calculation_inputs", [])) >= 2
                and all(v.get("evidence") for v in a["calculation_inputs"])
            )
        )
        for a in alternatives
    )


def project_item(
    process: dict[str, Any], item: dict[str, Any], groups: list[dict[str, Any]]
) -> dict[str, Any]:
    """Trust only prices already validated by the economic cycle, never raw offers."""
    price = item.get("purchase_price")
    # Budget-only disagreements remain visible but do not override an explicit purchase.
    critical = [c for c in item["conflicts"] if not c.startswith("budget_")]
    product_conflicts = [
        c
        for c in critical
        if c.startswith("specifications.")
        or c in ("brand", "model")
        or c == "model_reused_for_incompatible_sizes"
    ]
    price_conflicts = [c for c in critical if "price" in c or "total" in c]
    missing, states, warnings = [], [], []
    if not price:
        missing.append("verified_item_purchase_unit_price")
        states += ["missing_contract_price", "missing_awarded_price"]
        if item.get("offer_unit_price") or item.get("evaluated_offer_unit_price"):
            missing.append("proof_of_winning_offer_acceptance")
    quantity_ok = bool(
        positive_decimal(item.get("quantity"))
        and item.get("unit")
        and price
        and "quantity" not in critical
        and "unit" not in critical
    )
    if not quantity_ok:
        missing.append("verified_purchase_quantity_and_unit")
        states.append("missing_quantity")
    provenance_ok = _complete_provenance(price)
    if not provenance_ok:
        missing.append("purchase_price_provenance")
    if not item.get("purchase_date"):
        missing.append("verified_purchase_date")
    supplier = item.get("contracted_supplier") or item.get("awarded_supplier")
    supplier_scope = "item_economic_cycle" if supplier else None
    contracts = process.get("process_global_contracts", [])
    suppliers = {c.get("supplier") for c in contracts if c.get("supplier")}
    if not supplier and len(contracts) == 1 and len(suppliers) == 1:
        supplier = next(iter(suppliers))
        supplier_scope = "process_contract_metadata_not_offer_acceptance"
    if not supplier:
        warnings.append("supplier_unavailable_not_alone_a_comparison_blocker")
        states.append("missing_supplier")
    if product_conflicts:
        states.append("product_conflict")
    if price_conflicts:
        states.append("price_conflict")
    documents = [d for d in process["document_coverage"] if d.get("downloaded")]
    economic_docs = [d for d in documents if d["stage"] in ECONOMIC_STAGE_ORDER]
    if not economic_docs:
        missing.append("local_economic_document")
        states.append("document_missing")
    ready = bool(price and not critical and not missing)
    status = (
        "ready_for_comparison"
        if ready
        else "manual_review"
        if critical
        else "document_missing"
        if not economic_docs
        else "missing_contract_price"
        if not price
        else "missing_quantity"
        if not quantity_ok
        else "manual_review"
    )
    if ready:
        states.insert(0, status)
    accepted = price if price and price["column"] == "accepted_offer_unit_price" else None
    result = {
        "process_identity": process["process_identity"],
        "process_code": process["process_code"],
        "observation_id": item["id"],
        "normalized_product": item["normalized_product"],
        "product_description": item["item_description"],
        "specifications": item["specifications"],
        "brand": item.get("brand"),
        "model": item.get("model"),
        "comparability_group": [g["id"] for g in groups],
        "comparability_level": sorted({g["comparability_level"] for g in groups}),
        "quantity": item.get("quantity"),
        "unit": item.get("unit"),
        "quantity_verified_for_purchase": quantity_ok,
        "quantity_evidence": item.get("fields", {}).get("quantity"),
        "contract_unit_price": item.get("contract_unit_price"),
        "awarded_unit_price": item.get("awarded_unit_price"),
        "accepted_offer_unit_price": accepted["value"] if accepted else None,
        "unaccepted_offer_unit_price": item.get("offer_unit_price"),
        "preferred_purchase_price": price["value"] if price else None,
        "preferred_price_stage": price["column"].removesuffix("_unit_price") if price else None,
        "preferred_price_field": price["column"] if price else None,
        "value_origin": price["origin"] if price else None,
        "preferred_price_evidence": price["evidence"] if price else [],
        "supplier": supplier,
        "supplier_scope": supplier_scope,
        "supplier_evidence": contracts if supplier_scope and contracts else [],
        "purchase_date": item.get("purchase_date"),
        "purchase_date_evidence": item.get("purchase_date_evidence", []),
        "missing_fields": missing,
        "missing_document_or_stage": (
            ["itemized_signed_contract", "itemized_award_or_proven_accepted_offer"]
            if not price
            else []
        ),
        "conflicts": item["conflicts"],
        "critical_conflicts": critical,
        "economic_states": list(dict.fromkeys(states)),
        "evidence_refs": _evidence_refs(item),
        "readiness_status": status,
        "requires_manual_review": not ready,
        "deterministically_resolvable_with_available_evidence": ready,
        "warnings": warnings + item.get("readiness_audit_warnings", []),
        "resolvability_scope": "current_deterministic_rules_and_reviewed_local_evidence",
    }
    result["economic_readiness_status"] = status
    result.update(
        recommend_human_review(
            potential=bool(groups) or bool(product_conflicts),
            ready=ready,
            reasons=review_reasons(result, process["document_coverage"]),
            discarded=item["normalized_product"] != "televisor",
        )
    )
    if result["human_review_recommended"]:
        result["readiness_status"] = "human_review_recommended"
    result["requires_manual_review"] = result["human_review_recommended"]
    return result


def _television(process: dict[str, Any], item: dict[str, Any], entity: str) -> Television:
    price = item.get("purchase_price")
    column = price["column"] if price else ""
    return Television(
        process_id=process["process_identity"],
        entity=entity,
        description=item["item_description"],
        **item["specifications"],
        brand=item.get("brand"),
        model=item.get("model"),
        quantity=positive_decimal(item.get("quantity")),
        unit=item.get("unit"),
        unit_price_cop=positive_decimal(price["value"]) if price else None,
        price_reliable=bool(price),
        price_stage="contract"
        if column.startswith("contract")
        else "award"
        if price
        else "unknown",
        purchased_at=item.get("purchase_date"),
        purchase_date_source=item.get("purchase_date_source"),
        purchase_date_evidence=item.get("purchase_date_evidence", []),
        evidence=price["evidence"] if price else [],
        warnings=["conflicting_canonical"]
        if any(not c.startswith("budget_") for c in item["conflicts"])
        else [],
        observation_id=item["id"],
        vat_basis=item["observations"][0].get("vat_basis", "undetermined"),
        other_specifications={
            **item.get("other_specifications", {}),
            "process_code": process["process_code"],
        },
    )


def build_readiness(
    cycle: dict[str, Any], *, window_start: str, window_before: str
) -> dict[str, Any]:
    scope = technical_scope(cycle)
    by_id = {
        item["id"]: (p, item)
        for p in cycle["processes"]
        for item in p["products"]
        if item["id"] in scope["observation_ids"]
    }
    if len(by_id) != len(scope["observation_ids"]):
        raise ValueError("Frozen technical pair refers to an unavailable observation")
    rows = [
        project_item(p, i, [g for g in scope["pairs"] if key in g["observation_ids"]])
        for key, (p, i) in sorted(by_id.items())
    ]
    ready_by_id = {r["observation_id"]: r for r in rows}
    pairs, signals = [], []
    for number, original in enumerate(scope["pairs"], 1):
        ids = original["observation_ids"]
        a, b = (ready_by_id[i] for i in ids)
        assessed = compare_public_purchases(
            [
                _television(*by_id[i], entity)
                for i, entity in zip(ids, original["entities"], strict=True)
            ],
            window_start=window_start,
            window_before=window_before,
        )["comparisons"]
        comparison = assessed[0] if assessed else None
        ca, cb = bool(a["critical_conflicts"]), bool(b["critical_conflicts"])
        status = (
            "technical_mismatch"
            if not comparison or comparison["comparability_level"] not in ("exact", "high")
            else "manual_review"
            if ca and cb
            else "conflict_a"
            if ca
            else "conflict_b"
            if cb
            else "missing_both_prices"
            if not a["preferred_purchase_price"] and not b["preferred_purchase_price"]
            else "missing_price_a"
            if not a["preferred_purchase_price"]
            else "missing_price_b"
            if not b["preferred_purchase_price"]
            else "ready"
            if comparison["comparison_eligible"]
            and all(r["readiness_status"] == "ready_for_comparison" for r in (a, b))
            else "manual_review"
        )
        pair = {
            "number": number,
            "id": original["id"],
            "processes": original["processes"],
            "observation_ids": ids,
            "process_code_a": a["process_code"],
            "process_code_b": b["process_code"],
            "product_a": a["product_description"],
            "product_b": b["product_description"],
            "comparability_level": original["comparability_level"],
            "price_a": a["preferred_purchase_price"],
            "price_b": b["preferred_purchase_price"],
            "status": status,
            "blockers_a": a["missing_fields"] + a["critical_conflicts"],
            "blockers_b": b["missing_fields"] + b["critical_conflicts"],
            "missing_document_or_stage_a": a["missing_document_or_stage"],
            "missing_document_or_stage_b": b["missing_document_or_stage"],
            "deterministically_resolvable_with_available_evidence": status == "ready",
            "requires_manual_review": status != "ready",
            "comparison": comparison if status == "ready" else None,
        }
        pair["blocking_status"] = status
        pair.update(
            recommend_human_review(
                potential=status != "technical_mismatch",
                ready=status == "ready",
                reasons=a["human_review_reasons"] + b["human_review_reasons"],
            )
        )
        pair["human_review_reasons_a"] = a["human_review_reasons"]
        pair["human_review_reasons_b"] = b["human_review_reasons"]
        if pair["human_review_recommended"]:
            pair["status"] = "human_review_recommended"
        pair["requires_manual_review"] = pair["human_review_recommended"]
        pairs.append(pair)
        if status == "ready" and comparison:
            signals.append(
                {
                    **comparison,
                    "type": "PUBLIC_PRICE_DIFFERENCE",
                    "title": "Diferencia documentada entre precios de compras públicas",
                    "threshold_pct": None,
                    "requires_human_review": True,
                }
            )
    return {
        "version": "comparison-readiness-v2",
        "source": "local_secop_evidence",
        "window_start": window_start,
        "window_before": window_before,
        "scope": {k: v for k, v in scope.items() if k != "pairs"},
        "summary": {
            "initial_pairs": len(pairs),
            "initial_exact": sum(p["comparability_level"] == "exact" for p in pairs),
            "initial_high": sum(p["comparability_level"] == "high" for p in pairs),
            "unique_processes": len(scope["process_identities"]),
            "unique_observations": len(rows),
            "pairs_ready": sum(p["status"] == "ready" for p in pairs),
            "valid_comparisons": len(signals),
            "signals_generated": len(signals),
            "explicit_unit_prices": sum(
                r["preferred_purchase_price"] is not None and r["value_origin"] == "explicit"
                for r in rows
            ),
            "calculated_unit_prices": sum(
                r["preferred_purchase_price"] is not None and r["value_origin"] == "calculated"
                for r in rows
            ),
            "manual_review_observations": sum(r["requires_manual_review"] for r in rows),
            "manual_review_processes": len(
                {r["process_identity"] for r in rows if r["requires_manual_review"]}
            ),
            "pair_statuses": dict(Counter(p["status"] for p in pairs)),
            "blocking_statuses": dict(Counter(p["blocking_status"] for p in pairs)),
            "readiness_statuses": dict(Counter(r["readiness_status"] for r in rows)),
        },
        "comparison_readiness": rows,
        "pairs": pairs,
        "signals": signals,
    }
