"""Consolidación exacta y aliases limitados; las discrepancias se conservan como candidatos."""

import hashlib
import json
import re
import uuid
from collections import defaultdict
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import Any

from .domain.canonical import CONSOLIDATION_VERSION, REQUIRED_TYPES, CanonicalFact, CanonicalSummary
from .domain.structured import StructuredFact
from .domain.text import normalize_extracted_text

TYPE_MAP = {
    "product": "PRODUCT",
    "presentation": "PRESENTATION",
    "purchase_item": "PURCHASE_ITEM",
    "item_description": "PURCHASE_ITEM",
    "quantity": "QUANTITY",
    "unit_price_cop": "UNIT_PRICE_COP",
    "total_cop": "TOTAL_COP",
    "official_budget_cop": "BUDGET_COP",
    "unspsc": "UNSPSC",
    "execution_term": "EXECUTION_TERM",
    "delivery_location": "DELIVERY_LOCATION",
    "payment_method": "PAYMENT_METHOD",
    "payment_term": "PAYMENT_TERM",
    "guarantee": "GUARANTEE_REQUIRED",
    "rup": "RUP_REQUIRED",
    "experience": "EXPERIENCE_REQUIRED",
    "payment_percentage": "PAYMENT_PERCENTAGE",
    "operational_observation": "OPERATIONAL_OBSERVATION",
    "brand": "BRAND",
    "delivery_count": "DELIVERY_COUNT",
}


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":"))


def digest_inputs(facts: list[StructuredFact]) -> str:
    return hashlib.sha256(
        stable_json(
            sorted(
                [asdict(fact) for fact in facts],
                key=lambda value: str(value["id"]),
            )
        ).encode()
    ).hexdigest()


def normalized_unit(value: str | None) -> str | None:
    if value is None:
        return None
    folded = normalize_extracted_text(value)
    return {
        "ml": "ml",
        "mililitros": "ml",
        "gr": "g",
        "gr.": "g",
        "g": "g",
        "kg": "kg",
        "l": "l",
        "unidad": "unidad",
        "unidades": "unidad",
        "pack": "PACK",
        "packs": "PACK",
        "paquete": "PAQUETE",
        "paquetes": "PAQUETE",
        "caja": "CAJA",
        "cajas": "CAJA",
        "cop": "COP",
    }.get(folded, folded)


def json_number(value: Any, *, money: bool = False) -> int | str:
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Valor numérico estructurado inválido.") from exc
    if not number.is_finite():
        raise ValueError("Valor numérico no finito.")
    # No redondear centavos silenciosamente: enteros cuando son exactos, decimal string si no.
    if number == number.to_integral():
        return int(number)
    return format(number.normalize(), "f")


def product_name(value: str) -> str:
    name = normalize_extracted_text(value)
    name = re.sub(r"^jugos\b", "jugo", name)
    # Un solo nombre de marca: no reordena libremente palabras ni elimina calificativos.
    tetra = re.fullmatch(r"jugo (?:tetra (?P<before>\w+)|(?P<after>\w+) tetra)", name)
    if tetra:
        name = "jugo " + (tetra["before"] or tetra["after"])
    # Prefijo de clase redundante solo ante nombre + calificativo tradicional explícitos.
    if re.fullmatch(r"ponque \w+ tradicional", name):
        name = name.removeprefix("ponque ")
    return name


def description_key(value: str) -> str:
    text = normalize_extracted_text(value)
    text = re.sub(r"\bgr\.?\b", "g", text)
    text = re.sub(r"(\d)\s*(ml|kg|g)\b", r"\1 \2", text)
    return text


def evidence_identity(fact: StructuredFact) -> tuple[str, ...]:
    return tuple(
        sorted({source["content_fragment_id"] for source in fact.source_locator.get("sources", [])})
    )


def preference(fact: StructuredFact) -> tuple[Decimal, bool, str]:
    structured = any(
        source.get("locator", {}).get("kind") in ("docx_table_cell", "xlsx_cell")
        for source in fact.source_locator.get("sources", [])
    )
    return -fact.confidence, not structured, str(fact.id)


def choose_candidates(
    entries: list[tuple[Any, StructuredFact]],
) -> tuple[Any, list[dict[str, Any]]]:
    grouped: dict[str, list[tuple[Any, StructuredFact]]] = defaultdict(list)
    for value, fact in entries:
        if value is not None:
            grouped[stable_json(value)].append((value, fact))
    candidates = []
    for key, group in sorted(grouped.items()):
        preferred = min((fact for _, fact in group), key=preference)
        candidates.append(
            {
                "value": json.loads(key),
                "structured_fact_ids": sorted({str(fact.id) for _, fact in group}),
                "preferred_fact_id": str(preferred.id),
            }
        )
    return (candidates[0]["value"] if len(candidates) == 1 else None), candidates


def normalize_value(fact: StructuredFact) -> Any:
    kind = fact.fact_type
    normalized = fact.normalized_value
    if kind == "product":
        if not isinstance(normalized, dict):
            raise ValueError("Producto sin presentación estructurada verificable.")
        return {
            "name": product_name(fact.string_value or normalized.get("name", "")),
            "presentation_value": json_number(normalized["presentation"]),
            "presentation_unit": normalized_unit(normalized["unit"]),
        }
    if kind in ("presentation", "quantity"):
        return {"value": json_number(fact.numeric_value), "unit": normalized_unit(fact.unit)}
    if kind in ("unit_price_cop", "total_cop", "official_budget_cop"):
        return {"value": json_number(fact.numeric_value, money=True), "unit": "COP"}
    if kind in ("execution_term", "payment_term"):
        days = normalize_extracted_text(fact.unit or "")
        day_kind = (
            "calendar" if "calendario" in days else "business" if "habil" in days else "unknown"
        )
        trigger = normalized.get("trigger") if isinstance(normalized, dict) else None
        return {
            "value": json_number(fact.numeric_value),
            "unit": "days",
            "kind": day_kind,
            "trigger": normalize_extracted_text(trigger) if trigger else None,
        }
    if kind in ("guarantee", "rup", "experience"):
        state = (
            "required"
            if fact.boolean_value is True
            else "not_required"
            if fact.boolean_value is False
            else "unknown"
        )
        return {"state": state, "subject": fact.source_locator.get("subject") or kind}
    if kind == "payment_method":
        return (
            normalized
            if isinstance(normalized, dict)
            else normalize_extracted_text(fact.string_value or "")
        )
    if kind == "unspsc":
        return {"code": fact.string_value}
    if fact.numeric_value is not None:
        return {"value": json_number(fact.numeric_value), "unit": normalized_unit(fact.unit)}
    return normalize_extracted_text(fact.string_value or "")


def item_contexts(
    facts: list[StructuredFact],
) -> tuple[dict[tuple[uuid.UUID, str], str], list[StructuredFact]]:
    groups: dict[tuple[uuid.UUID, str], str] = {}
    items = [fact for fact in facts if fact.fact_type == "purchase_item"]
    for fact in items:
        group = fact.source_locator.get("group_key")
        if group:
            groups[fact.document_version_id, group] = description_key(fact.string_value or "")
    return groups, items


def item_identity(
    fact: StructuredFact, groups: dict[tuple[uuid.UUID, str], str], items: list[StructuredFact]
) -> str | None:
    group = (fact.document_version_id, fact.source_locator.get("group_key"))
    if group in groups:
        return groups[group]
    # Heredar identidad solo si el patrón está contenido en el tramo de una fila.
    matches = set()
    for item in items:
        for source in fact.source_locator.get("sources", []):
            for row_source in item.source_locator.get("sources", []):
                if (
                    source["content_fragment_id"] == row_source["content_fragment_id"]
                    and row_source["fragment_char_start"] <= source["fragment_char_start"]
                    and source["fragment_char_end"] <= row_source["fragment_char_end"]
                ):
                    matches.add(description_key(item.string_value or ""))
    return next(iter(matches)) if len(matches) == 1 else None


def consolidate(
    process_id: uuid.UUID,
    facts: list[StructuredFact],
    version: str = CONSOLIDATION_VERSION,
) -> CanonicalSummary:
    if any(fact.process_id != process_id or fact.id is None for fact in facts):
        raise ValueError("La consolidación requiere hechos persistidos del mismo proceso.")
    unknown = {fact.fact_type for fact in facts} - TYPE_MAP.keys()
    if unknown:
        raise ValueError(
            "Tipos de hechos no soportados; se requiere revisar las reglas de consolidación."
        )
    digest = digest_inputs(facts)
    groups, items = item_contexts(facts)
    buckets: dict[tuple[str, str], list[StructuredFact]] = defaultdict(list)
    for fact in facts:
        kind = TYPE_MAP[fact.fact_type]
        identity = "process"
        if fact.fact_type in ("purchase_item", "item_description"):
            identity = item_identity(fact, groups, items) or description_key(
                fact.string_value or ""
            )
        elif fact.fact_type in ("quantity", "unit_price_cop", "total_cop"):
            identity = item_identity(fact, groups, items) or "unscoped"
        elif fact.fact_type == "product":
            identity = stable_json(normalize_value(fact))
        elif fact.fact_type == "presentation":
            identity = stable_json(
                {
                    "product": product_name(fact.source_locator.get("subject") or ""),
                    **normalize_value(fact),
                }
            )
        elif fact.fact_type in ("guarantee", "rup", "experience"):
            identity = fact.source_locator.get("subject") or fact.fact_type
        elif fact.fact_type in ("operational_observation", "brand"):
            identity = stable_json(normalize_value(fact))
        key = hashlib.sha256(identity.encode()).hexdigest()
        buckets[kind, key].append(fact)
    results = []
    for (kind, key), sources in sorted(buckets.items()):
        payload: dict[str, Any]
        ids = tuple(sorted({fact.id for fact in sources if fact.id is not None}, key=str))
        evidence_sets = [set(evidence_identity(fact)) for fact in sources]
        corroborated = any(
            first and second and first.isdisjoint(second)
            for first, second in combinations(evidence_sets, 2)
        )
        confidence = max(fact.confidence for fact in sources)
        if kind == "PURCHASE_ITEM":
            field_entries: dict[str, list[tuple[Any, StructuredFact]]] = defaultdict(list)
            for fact in sources:
                value = fact.normalized_value
                if fact.fact_type == "item_description":
                    field_entries["description"].append(
                        (description_key(fact.string_value or ""), fact)
                    )
                    continue
                if not isinstance(value, dict):
                    raise ValueError("Ítem sin campos estructurados.")
                for field, raw in value.items():
                    if raw is None:
                        continue
                    normalized = (
                        description_key(str(raw))
                        if field == "description"
                        else normalized_unit(str(raw))
                        if field == "unit"
                        else json_number(raw)
                    )
                    field_entries[field].append((normalized, fact))
            value = {}
            field_candidates = {}
            for field, entries in sorted(field_entries.items()):
                selected, candidates = choose_candidates(entries)
                value[field] = selected
                field_candidates[field] = candidates
            conflict = any(len(candidates) > 1 for candidates in field_candidates.values())
            payload = {
                "value": value,
                "field_candidates": field_candidates,
                "field_sources": {
                    field: sorted({str(fact.id) for _, fact in entries})
                    for field, entries in field_entries.items()
                },
                "field_confidence": {
                    field: str(max(fact.confidence for _, fact in entries))
                    for field, entries in field_entries.items()
                },
            }
        else:
            value, candidates = choose_candidates(
                [(normalize_value(fact), fact) for fact in sources]
            )
            conflict = len(candidates) > 1
            payload = {"value": value, "candidates": candidates}
        payload.update(corroborated=corroborated and not conflict, review_required=conflict)
        identifier = uuid.uuid5(process_id, f"{version}:{digest}:{kind}:{key}")
        results.append(
            CanonicalFact(
                identifier,
                process_id,
                kind,
                key,
                payload,
                confidence,
                "conflict" if conflict else "confirmed",
                version,
                digest,
                ids,
            )
        )
    missing = tuple(
        kind for kind in REQUIRED_TYPES if not any(f.canonical_type == kind for f in results)
    )
    return CanonicalSummary(tuple(results), len(facts), missing)
