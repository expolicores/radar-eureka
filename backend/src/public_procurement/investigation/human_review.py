"""Human research recommendation, separate from commercial review or confirmed signals."""

from enum import StrEnum
from typing import Any


class HumanReviewReason(StrEnum):
    MISSING_ITEMIZED_PRICE = "missing_itemized_contract_price"
    MISSING_ACCEPTED_OFFER = "missing_accepted_offer"
    AMBIGUOUS_PRODUCT = "ambiguous_product_identity"
    CONFLICTING_REFERENCE = "conflicting_product_reference"
    GLOBAL_VALUE = "global_contract_value_without_item_breakdown"
    MISSING_QUANTITY = "missing_quantity"
    INCOMPLETE_CYCLE = "incomplete_document_cycle"
    UNRESOLVED_RELATIONSHIP = "unresolved_document_relationship"
    EXTRACTION_FAILURE = "extraction_failure"
    OVERSIZED = "oversized_document"
    AMBIGUOUS_WINNER = "ambiguous_winning_offer"
    CONTRACT_DOCS_UNRESOLVED = "contract_documents_found_but_not_resolved"


def recommend_human_review(
    *, potential: bool, ready: bool, reasons: list[str], discarded: bool = False
) -> dict[str, Any]:
    recommended = bool(potential and not discarded and not ready and reasons)
    return {
        "review_status": "human_review_recommended"
        if recommended
        else "not_applicable"
        if discarded or not potential
        else "not_required",
        "human_review_recommended": recommended,
        "human_review_reasons": sorted(set(reasons)) if recommended else [],
    }


def review_reasons(row: dict[str, Any], coverage: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    conflicts = row.get("critical_conflicts", [])
    if "model_reused_for_incompatible_sizes" in conflicts:
        reasons.append(HumanReviewReason.CONFLICTING_REFERENCE)
    elif any(c in ("brand", "model") or c.startswith("specifications.") for c in conflicts):
        reasons.append(HumanReviewReason.AMBIGUOUS_PRODUCT)
    if not row.get("preferred_purchase_price"):
        if not row.get("contract_unit_price") and not row.get("awarded_unit_price"):
            reasons.append(HumanReviewReason.MISSING_ITEMIZED_PRICE)
            if row.get("supplier_evidence"):
                reasons.append(HumanReviewReason.GLOBAL_VALUE)
        if row.get("unaccepted_offer_unit_price"):
            reasons += [
                HumanReviewReason.MISSING_ACCEPTED_OFFER,
                HumanReviewReason.AMBIGUOUS_WINNER,
            ]
    if row.get("quantity") is None:
        reasons.append(HumanReviewReason.MISSING_QUANTITY)
    if "ambiguous_local_observation_link" in row.get("warnings", []):
        reasons.append(HumanReviewReason.UNRESOLVED_RELATIONSHIP)
    for d in coverage:
        if d.get("selected") and d.get("extraction_status") in ("failed", "requires_ocr"):
            reasons.append(HumanReviewReason.EXTRACTION_FAILURE)
        if d.get("selected") and d.get("coverage_complete") is False:
            reasons.append(HumanReviewReason.INCOMPLETE_CYCLE)
    return sorted(set(reasons))
