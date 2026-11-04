"""Pairwise research only. No Radar rules, historical benchmark or market requests."""

import uuid
from collections import Counter
from itertools import combinations
from typing import Any

from public_procurement.comparison.services import DEFAULT_CONFIG
from public_procurement.shared.text import normalize_text

from .domain.television import Television, comparability, compare_pair, purchase_price_usable


def compare_public_purchases(
    products: list[Television], *, window_start: str, window_before: str
) -> dict[str, Any]:
    """60-day transversal comparison, no percentage threshold or macro adjustments."""
    import re
    from datetime import date
    from decimal import Decimal

    def product_class(product: Television) -> str:
        description = normalize_text(product.description)
        if product.other_specifications.get("interactive_touchscreen") or re.search(
            r"tactil|interactiva", description
        ):
            return "interactive_display"
        if product.other_specifications.get("professional_display") or re.search(
            r"\b(?:business|profesional|signage|hotelero|hospitality)\b|24\s*/\s*7", description
        ):
            return "professional_display"
        return "television"

    aliases = {
        "same_model": "exact",
        "highly_comparable": "high",
        "partially_comparable": "partial",
        "not_comparable": "not_comparable",
    }
    pairs: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    start, before = date.fromisoformat(window_start), date.fromisoformat(window_before)
    for first, second in combinations(products, 2):
        if (
            first.process_id == second.process_id
            or re.sub(r"\s+", " ", normalize_text(first.entity)).strip()
            == re.sub(r"\s+", " ", normalize_text(second.entity)).strip()
        ):
            continue
        level, limitations = comparability(first, second)
        same_reference = bool(
            first.model
            and first.model == second.model
            and re.fullmatch(
                r"(?:[A-Z]{0,2}\d{2,3}[A-Z]{1,4}\d{3,6}[A-Z0-9]{0,5}|[A-Z]{1,2}\d{4,6}[A-Z]{1,4})",
                first.model,
            )
            and not (first.brand and second.brand and first.brand != second.brand)
        )
        if same_reference and level in ("highly_comparable", "partially_comparable"):
            level = "same_model"
            limitations.append("exact_explicit_reference_brand_may_be_unknown")
        if product_class(first) != product_class(second):
            level = "not_comparable"
            limitations.append("different_product_class")
        valid = level in ("same_model", "highly_comparable")
        if not all(purchase_price_usable(p) for p in (first, second)):
            valid = False
            limitations.append("purchase_price_or_quantity_not_verified")
        if first.currency != second.currency:
            valid = False
            limitations.append("currency_mismatch")
        units = [
            "UNIT"
            if (p.unit or "").upper() in ("UN", "UNIDAD", "UNIDADES", "UND", "UNIT", "U")
            else p.unit
            for p in (first, second)
        ]
        if not all(units) or units[0] != units[1]:
            valid = False
            limitations.append("unit_basis_not_comparable")
        if first.vat_basis != second.vat_basis and "undetermined" not in (
            first.vat_basis,
            second.vat_basis,
        ):
            valid = False
            limitations.append("tax_basis_mismatch")
        if "undetermined" in (first.vat_basis, second.vat_basis):
            limitations.append("tax_basis_unverified_requires_human_review")
        dates: list[date | None] = []
        for product in (first, second):
            try:
                dates.append(date.fromisoformat((product.purchased_at or "")[:10]))
            except ValueError:
                dates.append(None)
        days = (
            abs((dates[0] - dates[1]).days)
            if dates[0] is not None and dates[1] is not None
            else None
        )
        if days is None:
            valid = False
            limitations.append("purchase_date_unknown_publication_not_substituted")
        elif days > 60 or any(not start <= d < before for d in dates if d):
            valid = False
            limitations.append("purchase_outside_60_day_window")
        pair_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                "research-60d-v1:"
                + ":".join(sorted(str(p.observation_id) for p in (first, second))),
            )
        )
        sides = [
            {
                "entity": p.entity,
                "process_identity": p.process_id,
                "process_code": p.other_specifications.get("process_code"),
                "description": p.description,
                "date": p.purchased_at,
                "date_source": p.purchase_date_source,
                "date_evidence": p.purchase_date_evidence,
                "unit_price": str(p.unit_price_cop) if p.unit_price_cop else None,
                "quantity": str(p.quantity) if p.quantity else None,
                "unit": p.unit,
                "currency": p.currency,
                "tax_basis": p.vat_basis,
                "price_stage": p.price_stage,
                "evidence": p.evidence if valid else [],
                "characteristics": {
                    "product_class": product_class(p),
                    **{
                        k: getattr(p, k)
                        for k in (
                            "brand",
                            "model",
                            "screen_size_inches",
                            "resolution",
                            "smart",
                            "panel",
                        )
                    },
                },
            }
            for p in (first, second)
        ]
        absolute, percentage = None, None
        if valid and first.unit_price_cop and second.unit_price_cop:
            low = min(first.unit_price_cop, second.unit_price_cop)
            absolute = str(abs(first.unit_price_cop - second.unit_price_cop))
            percentage = str(Decimal(absolute) / low * 100)
        limitations += [
            "no_inflation_or_fx_adjustment",
            "temporal_proximity_does_not_guarantee_equal_conditions",
            "accessories_installation_warranty_delivery_conditions_not_fully_verified",
        ]
        limitations += sorted({w for p in (first, second) for w in p.warnings})
        pair = {
            "id": pair_id,
            "processes": [p.process_id for p in (first, second)],
            "entities": [p.entity for p in (first, second)],
            "observation_ids": [p.observation_id for p in (first, second)],
            "comparability": level,
            "comparability_level": aliases[level],
            "comparison_eligible": bool(valid),
            "signal_eligible": bool(valid),
            "signal": bool(valid),
            "days_between": days,
            "sides": sides,
            "unit_price_a_cop": sides[0]["unit_price"],
            "unit_price_b_cop": sides[1]["unit_price"],
            "absolute_difference_cop": absolute,
            "difference_pct": percentage,
            "percentage_reference": "lower_unit_price",
            "limitations": list(dict.fromkeys(limitations)),
        }
        pairs.append(pair)
        if level != "not_comparable":
            groups.append(
                {
                    "comparison_id": pair_id,
                    "level": aliases[level],
                    "processes": pair["processes"],
                    "observation_ids": pair["observation_ids"],
                    "interpretation": "pair_of_observations_not_transitive_cluster",
                }
            )
        if valid:
            signals.append(
                {
                    **pair,
                    "type": "PUBLIC_PRICE_DIFFERENCE",
                    "comparison_id": pair_id,
                    "title": "Diferencia documentada entre precios de compras públicas",
                    "requires_human_review": True,
                    "threshold_pct": None,
                }
            )
    return {
        "comparisons": pairs,
        "signals": signals,
        "comparable_groups": groups,
        "comparability_counts": {
            key: sum(p["comparability_level"] == key for p in pairs)
            for key in ("exact", "high", "partial", "not_comparable")
        },
        "comparisons_possible": sum(p["comparison_eligible"] for p in pairs),
        "comparison_exclusion_reasons": dict(
            Counter(r for p in pairs if not p["comparison_eligible"] for r in p["limitations"])
        ),
    }


def compare_observations(products: list[Television]) -> dict[str, Any]:
    pairs = []
    groups = []
    signals = []
    for first, second in combinations(products, 2):
        if first.process_id == second.process_id or first.entity == second.entity:
            continue
        pair = compare_pair(first, second, research_v2=True)
        pair.pop("products", None)
        pair["observation_ids"] = [first.observation_id, second.observation_id]
        pair["unit_price_a_cop"] = str(first.unit_price_cop) if first.unit_price_cop else None
        pair["unit_price_b_cop"] = str(second.unit_price_cop) if second.unit_price_cop else None
        pair["percentage_reference"] = "lower_unit_price"
        pair["id"] = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                "research-pair-v2:" + ":".join(sorted(str(i) for i in pair["observation_ids"])),
            )
        )
        pairs.append(pair)
        if pair["comparability"] != "not_comparable":
            groups.append(
                {
                    "comparison_id": pair["id"],
                    "level": pair["comparability"],
                    "processes": pair["processes"],
                    "observation_ids": pair["observation_ids"],
                    "interpretation": "compatible_pair_not_a_transitive_cluster",
                }
            )
        threshold = (
            DEFAULT_CONFIG.same_model_threshold_pct
            if pair["comparability"] == "same_model"
            else DEFAULT_CONFIG.equivalent_threshold_pct
        )
        if pair.get("signal_eligible") and pair["difference_pct"] is not None:
            from decimal import Decimal

            if Decimal(pair["difference_pct"]) >= threshold:
                signals.append(
                    {
                        "id": pair["id"],
                        "type": "public_purchase_price_difference",
                        "title": (
                            "Diferencia relevante de precio entre compras públicas comparables"
                        ),
                        "comparison_id": pair["id"],
                        "processes": pair["processes"],
                        "entities": pair["entities"],
                        "difference_pct": pair["difference_pct"],
                        "absolute_difference_cop": pair["absolute_difference_cop"],
                        "comparability": pair["comparability"],
                        "threshold_pct": str(threshold),
                        "requires_human_review": True,
                        "limitations": [
                            *pair["limitations"],
                            "indicator_not_a_conclusion_of_irregularity",
                        ],
                    }
                )
                pair["signal"] = True
    reasons = Counter(reason for pair in pairs for reason in pair["limitations"])
    return {
        "comparisons": pairs,
        "comparable_groups": groups,
        "signals": signals,
        "comparability_counts": dict(Counter(p["comparability"] for p in pairs)),
        "comparison_exclusion_reasons": dict(reasons),
        "comparisons_possible": sum(bool(p.get("comparison_eligible")) for p in pairs),
    }
