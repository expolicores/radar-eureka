"""Conservative research projection; never changes Radar or asserts an irregularity."""

import re
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from public_procurement.shared.text import normalize_text


@dataclass(frozen=True)
class Television:
    process_id: str
    entity: str
    description: str
    screen_size_inches: int | None = None
    panel: str | None = None
    resolution: str | None = None
    smart: bool | None = None
    brand: str | None = None
    model: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price_cop: Decimal | None = None
    total_cop: Decimal | None = None
    price_stage: str = "unknown"
    vat_basis: str = "undetermined"
    currency: str = "COP"
    confidence: str = "0"
    evidence: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    published_at: str | None = None
    department: str | None = None
    municipality: str | None = None
    supplier: str | None = None
    price_reliable: bool = False
    price_basis: str = "unknown"
    observation_id: str | None = None
    other_specifications: dict[str, Any] = field(default_factory=dict)
    purchased_at: str | None = None
    purchase_date_source: str | None = None
    purchase_date_evidence: list[dict[str, Any]] = field(default_factory=list)


def positive_decimal(raw: Any) -> Decimal | None:
    try:
        value = Decimal(str(raw))
        return value if value.is_finite() and value > 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def television_specs(description: str) -> dict[str, Any]:
    """Only explicit attributes in the same item; never borrow other rows' specifications."""
    text = normalize_text(description)
    sizes = {int(m[1]) for m in re.finditer(r'\b(\d{2,3})\s*(?:pulgadas?|pulg\b|["″“”])', text)}
    panels = {
        p.upper()
        for p in ("oled", "qled", "mini led", "led", "lcd")
        if re.search(r"\b" + p + r"\b", text)
    }
    if "MINI LED" in panels:
        panels.discard("LED")
    # QLED is not silently normalized as a conventional LED panel.
    resolutions = set()
    if re.search(r"\b(?:4k|uhd|uhd4k)\b|3840\s*[x×]\s*2160", text):
        resolutions.add("4k")
    if re.search(r"\bfull hd\b|1920\s*[x×]\s*1080", text):
        resolutions.add("full_hd")
    if re.search(r"(?<!full )\bhd\b", text):
        resolutions.add("hd")
    resolution = next(iter(resolutions)) if len(resolutions) == 1 else None
    brands = [
        b
        for b in ("samsung", "lg", "hisense", "kalley", "caixun", "tcl", "sony")
        if re.search(r"\b" + b + r"\b", text)
    ]
    model_match = re.search(
        r"\b(?:modelo|model|mod\.?|referencia|ref\.?)[\s:]+([a-z0-9][a-z0-9-]{3,})\b", text
    )
    if not model_match and len(brands) == 1:
        model_match = re.search(r"\b" + brands[0] + r"\s+([a-z0-9-]{5,})\b", text)
    model = (
        model_match[1].upper()
        if model_match and re.search(r"[a-z]", model_match[1]) and re.search(r"\d", model_match[1])
        else None
    )
    return {
        "screen_size_inches": next(iter(sizes)) if len(sizes) == 1 else None,
        "panel": next(iter(panels)) if len(panels) == 1 else None,
        "resolution": resolution,
        "smart": False
        if re.search(r"\b(?:no|sin)\s+(?:es\s+)?smart\s*tv\b|\bsmart\s*tv\s*:\s*no\b", text)
        else True
        if re.search(r"\bsmart(?:\s*tv|v)?\b", text)
        else None,
        "brand": brands[0].upper() if len(brands) == 1 else None,
        "model": model,
    }


def comparability(first: Television, second: Television) -> tuple[str, list[str]]:
    if first.process_id == second.process_id or normalize_text(first.entity) == normalize_text(
        second.entity
    ):
        return "not_comparable", ["requires_different_entities_and_processes"]
    attrs = ("screen_size_inches", "panel", "resolution", "smart")
    if any(
        getattr(first, a) is not None
        and getattr(second, a) is not None
        and getattr(first, a) != getattr(second, a)
        for a in attrs
    ):
        return "not_comparable", ["incompatible_specifications"]
    if first.other_specifications.get("interactive_touchscreen") != second.other_specifications.get(
        "interactive_touchscreen"
    ):
        return "partially_comparable", ["interactive_screen_scope_not_verified"]
    if (
        first.brand
        and second.brand
        and first.model
        and second.model
        and (first.brand, first.model) == (second.brand, second.model)
    ):
        return "same_model", []
    if all(getattr(p, a) is not None for p in (first, second) for a in attrs):
        return "highly_comparable", [
            "different_or_unknown_model",
            "delivery_warranty_scope_unverified",
        ]
    if any(
        getattr(first, a) is not None and getattr(first, a) == getattr(second, a) for a in attrs
    ):
        return "partially_comparable", ["incomplete_specifications"]
    return "not_comparable", ["insufficient_product_evidence"]


def purchase_price_usable(product: Television) -> bool:
    return bool(
        product.price_reliable
        and positive_decimal(product.quantity)
        and positive_decimal(product.unit_price_cop)
        and product.evidence
        and product.price_stage in ("contract", "award")
        and not any(
            w in product.warnings
            for w in (
                "conflicting_canonical",
                "mixed_product_bundle",
                "price_conflict_same_stage",
                "document_scope_conflict",
                "partial_document_coverage",
                "unsigned_or_unverified_contract",
                "award_price_unverified",
                "service_not_purchase",
                "source_reference_unverified",
            )
        )
    )


def _unit_key(unit: str | None) -> str:
    value = (unit or "").upper()
    return "UNIT" if value in ("UNIDAD", "UNIDADES", "UND", "UN", "UNIT", "U") else value


def compare_pair(
    first: Television, second: Television, *, research_v2: bool = False
) -> dict[str, Any]:
    level, limitations = comparability(first, second)
    result: dict[str, Any] = {
        "processes": [first.process_id, second.process_id],
        "entities": [first.entity, second.entity],
        "comparability": level,
        "limitations": list(limitations),
        "absolute_difference_cop": None,
        "difference_pct": None,
        "signal": False,
    }
    price_a, price_b = (
        positive_decimal(first.unit_price_cop),
        positive_decimal(second.unit_price_cop),
    )
    if price_a is None or price_b is None:
        result["limitations"].append("missing_documented_unit_price")
    elif research_v2 and any(not p.quantity or not p.price_reliable for p in (first, second)):
        result["limitations"].append("unreliable_price_or_quantity")
    elif research_v2 and not all(purchase_price_usable(p) for p in (first, second)):
        result["limitations"].append("purchase_price_not_confirmed")
    elif research_v2 and first.currency != second.currency:
        result["limitations"].append("currency_mismatch")
    elif (
        research_v2
        and first.unit
        and second.unit
        and _unit_key(first.unit) != _unit_key(second.unit)
    ):
        result["limitations"].append("unit_basis_mismatch")
    elif (
        research_v2
        and first.vat_basis != second.vat_basis
        and "undetermined" not in (first.vat_basis, second.vat_basis)
    ):
        result["limitations"].append("tax_basis_mismatch")
    elif level in ("same_model", "highly_comparable"):
        low, high = sorted((price_a, price_b))
        result["absolute_difference_cop"] = str(high - low)
        result["difference_pct"] = str((high / low - 1) * 100)
    if any(p.vat_basis == "undetermined" for p in (first, second)):
        result["limitations"].append("tax_basis_unverified")
    if any(p.price_stage not in ("contract", "award") for p in (first, second)):
        result["limitations"].append("purchase_price_not_confirmed")
    if not research_v2:
        result["limitations"].append("pairwise_observation_not_sufficient_for_signal")
    else:
        from datetime import date

        if first.unit is None or second.unit is None:
            result["limitations"].append("unit_basis_unverified")
        elif _unit_key(first.unit) != _unit_key(second.unit):
            result["limitations"].append("unit_basis_mismatch")

        if first.published_at and second.published_at:
            distance = abs(
                (
                    date.fromisoformat(first.published_at[:10])
                    - date.fromisoformat(second.published_at[:10])
                ).days
            )
            result["publication_distance_days"] = distance
            if distance > 30:
                result["limitations"].append("outside_research_temporal_window")
        else:
            result["limitations"].append("unknown_publication_distance")
        if first.currency != second.currency:
            result["limitations"].append("currency_mismatch")
        if first.vat_basis != second.vat_basis:
            result["limitations"].append("tax_basis_mismatch")
        result["comparison_eligible"] = bool(
            level in ("same_model", "highly_comparable")
            and result["difference_pct"] is not None
            and all(p.price_stage in ("contract", "award") and p.evidence for p in (first, second))
            and not any(
                w in p.warnings
                for p in (first, second)
                for w in (
                    "conflicting_canonical",
                    "mixed_product_bundle",
                    "price_conflict_same_stage",
                    "document_scope_conflict",
                    "partial_document_coverage",
                    "unsigned_or_unverified_contract",
                    "award_price_unverified",
                )
            )
        )
        result["signal_eligible"] = bool(
            result["comparison_eligible"]
            and not any(
                "cross_document_canonical_conflict_preserved" in p.warnings for p in (first, second)
            )
            and not any(
                x in result["limitations"]
                for x in (
                    "tax_basis_unverified",
                    "tax_basis_mismatch",
                    "currency_mismatch",
                    "outside_research_temporal_window",
                    "unknown_publication_distance",
                    "delivery_warranty_scope_unverified",
                    "unit_basis_unverified",
                    "unit_basis_mismatch",
                )
            )
        )
        result["limitations"] = list(dict.fromkeys(result["limitations"]))
    result["products"] = [asdict(first), asdict(second)]
    return result
