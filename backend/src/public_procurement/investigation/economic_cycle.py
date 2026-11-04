"""Offline, deterministic item economics. No provider calls or persistence side effects.

Canonical concepts are reused with item + stage + document/offer scope. A price
from an evaluation recommendation is never promoted to an awarded price.
"""

import hashlib
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

from public_procurement.shared.text import normalize_text

from .domain.television import Television, positive_decimal, television_specs
from .research_comparison import compare_observations, compare_public_purchases

VERSION = "economic-cycle-v2"
STAGES = (
    "studies_previous",
    "invitation",
    "technical_specification",
    "economic_offer",
    "evaluation_report",
    "award",
    "contract",
    "amendment",
    "other",
    "unknown",
)
ECONOMIC_FIELDS = tuple(
    f"{stage}_{kind}"
    for stage in ("budget", "offer", "evaluated_offer", "awarded", "contract")
    for kind in ("total", "unit_price")
)
STAGE_COLUMN = {
    "studies_previous": "budget",
    "invitation": "budget",
    "technical_specification": "budget",
    "economic_offer": "offer",
    "evaluation_report": "evaluated_offer",
    "award": "awarded",
    "contract": "contract",
}
MONEY = re.compile(r"(?<![\w.,])\$?\s*(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?)(?![\w.,])")
HEAD = re.compile(
    r"^(?:\s*(\d{1,3})\s*[|.)-]?\s*)?(?:\d{8}\s+)?"
    r"(televisor(?:es|e)?|smart\s*tv|tv|celular(?:es)?|smartphone)\b",
    re.I,
)
NEXT_ITEM = re.compile(
    r"\n[ \t]*(?:\d{1,3}[ \t]*[|.)_-]?[ \t]*)?(?:\d{8}[ \t]+)?"
    r"(?:kit(?:robotica|de)?\b|computador\b|impresora\b|videoproyector\b|proyector\b|"
    r"ventilador\b|microfonos?\b|consola\b|parlante\b|"
    r"aire acondicionado\b|televisor(?:es|e)?\b|dispensador\b|abanico\b|congelador\b|valor total\b|"
    r"costo total\b|forma de pago\b|notas adicionales\b|clausula\b|contratista\b|"
    r"\d+\.\d+\.?\s|contacto\b|celular\s*:|correo\b|email\b)",
    re.I,
)


def _id(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", normalize_text(value)).strip()


def money(raw: str) -> Decimal | None:
    value = raw.strip().replace("$", "").replace(" ", "")
    if re.search(r"[.,]\d{2}$", value):
        value = re.sub(r"[.,]", "", value[:-3]) + "." + value[-2:]
    else:
        value = re.sub(r"[.,]", "", value)
    try:
        return positive_decimal(Decimal(value))
    except InvalidOperation:
        return None


def classify_stage(name: str, text: str = "") -> tuple[str, str]:
    """Specific filename wins; content fallback must be a heading, not a citation."""
    patterns = (
        ("amendment", r"\badenda\b|\botrosi\b|modificaci[oó]n contractual"),
        ("evaluation_report", r"evaluaci[oó]n|\bevaluacion\b"),
        ("award", r"aceptaci[oó]n.*oferta|adjudicaci[oó]n|oferta seleccionada"),
        ("contract", r"\bcontrato\b|\bpccntr\b|clausulado|co1[_ .]pccntr"),
        ("studies_previous", r"estudios? previos?|estudio de mercado|analisis del sector"),
        ("technical_specification", r"especificacion|ficha tecnica|anexo tecnico"),
        ("economic_offer", r"oferta economica|cotizaci[oó]n|\bcotizacion\b|propuesta economica"),
        ("invitation", r"invitaci[oó]n|\binvitacion\b|pliego"),
        ("other", r"\bcdp\b|acta de inicio|disponibilidad presupuestal"),
    )
    folded = normalize_text(name)
    if "oferta seleccionada" in folded:
        return "economic_offer", "selected_offer_filename_is_not_an_award_act"
    for stage, pattern in patterns:
        if re.search(pattern, folded):
            if stage == "contract":
                heading = _norm(text[:1800])
                if re.search(r"\basunto\s*:\s*cotizacion\b", heading) or re.search(
                    r"(?im)^\s*cotizaci[oó]n\s+(?:no\.?\s*)?\d+\s*$", text[:1800]
                ):
                    return "economic_offer", "embedded_quotation_heading"
                if re.search(r"(?im)^\s*estudios?\s+previos?\s*$", text[:1800]):
                    return "studies_previous", "embedded_studies_heading"
            return stage, "filename_rule"
    for line in text.splitlines()[:15]:
        heading = normalize_text(line.strip())
        if not 3 < len(heading) < 100:
            continue
        for stage, pattern in patterns:
            if re.fullmatch(r"(?:informe de |resolucion de |anexo \d*\s*)?" + pattern, heading):
                return stage, "text_heading_rule"
    return "unknown", "no_unambiguous_classification"


def _specs(description: str) -> dict[str, Any]:
    specs = television_specs(description)
    if specs["model"] is None:
        reference = re.search(
            r"\b(?:[a-z]{0,2}\d{2,3}[a-z]{1,4}\d{3,6}[a-z0-9]{0,5}|"
            r"[a-z]{1,2}\d{4,6}[a-z]{1,4})\b",
            _norm(description[:250]),
        )
        if reference:
            specs["model"] = reference[0].upper()
    if re.search(r"\b(?:celular|smartphone)\b", normalize_text(description)):
        brand = re.search(r"\b(xiaomi|samsung|motorola|apple|honor)\b", normalize_text(description))
        model = re.search(
            r"\b(?:redmi\s+\d+[a-z]?|galaxy\s+[a-z]\d+)\b", normalize_text(description)
        )
        specs.update(
            brand=brand[1].upper() if brand else None, model=model[0].upper() if model else None
        )
    return specs


def _evidence(fragment: dict[str, Any], excerpt: str, stage: str, rule: str) -> dict[str, Any]:
    loc = fragment.get("source_locator") or {}
    # Bounded item text only: never serialize the whole page or legal/person sections.
    return {
        "source_stage": stage,
        "source_document": fragment["original_name"],
        "source_page": loc.get("page_number"),
        "fragment_id": fragment.get("id"),
        "document_version_id": fragment.get("document_version_id"),
        "input_sha256": loc.get("input_sha256"),
        "extraction_method": loc.get("extraction_method") or loc.get("extractor_name") or "unknown",
        "source_locator": loc,
        "evidence_text": excerpt[:900],
        "rule": rule,
    }


def _supplier(text: str) -> str | None:
    match = re.search(
        r"(?:proponente|oferente|proveedor|contratista)\s*:\s*([^\n;]{4,100})", text, re.I
    )
    if not match:
        return None
    return (
        re.split(r"\b(?:nit|cedula|cédula|identificaci[oó]n|tel[eé]fono)\b", match[1], flags=re.I)[
            0
        ].strip()
        or None
    )


def _offer_reference(text: str) -> str | None:
    match = re.search(
        r"\boferta(?: economica)?(?: aceptada)?\s*(?:no\.?|numero|referencia|:)\s*"
        r"([a-z0-9][a-z0-9-]{2,35})\b",
        _norm(text),
    )
    return match[1].upper() if match else None


def _cell(
    value: Any,
    evidence: dict[str, Any],
    *,
    origin: str = "explicit",
    confidence: str = "0.85",
    inputs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    # Decimal formatting is not a data conflict (3 and 3.00 are the same quantity).
    numeric = positive_decimal(value)
    canonical_value = format(numeric.normalize(), "f") if numeric is not None else str(value)
    return {
        "value": canonical_value,
        "value_origin": origin,
        "confidence": confidence,
        "evidence": [evidence],
        "calculation_inputs": inputs or [],
    }


def _quantity(prefix: str, suffix: str, header: str, leading: str | None) -> Decimal | None:
    # Never treat inches, item number or a process-wide quantity as row quantity.
    pipe_quantity = re.search(r"\|\s*(\d{1,4})\s*\|?\s*$", suffix)
    if pipe_quantity:
        return positive_decimal(pipe_quantity[1])
    quantity_unit = re.search(
        r"(?:\s|\|)(\d{1,4}(?:[.,]00)?)\s+(?:unidad(?:es)?|und|un)\s*$", suffix
    )
    if quantity_unit:
        return positive_decimal(quantity_unit[1].replace(",", "."))
    trailing = re.search(
        r"(?:\b(?:unidad(?:es)?|und|un|u)\b\s*[|:]?\s*)?(\d{1,4}(?:[.,]00)?)\s*[|]*\s*$", suffix
    )
    if trailing and (
        re.search(r"\bcant(?:idad)?\b", header)
        or re.search(r"\b(?:unidad(?:es)?|und|un)\b", suffix)
    ):
        return positive_decimal(trailing[1].replace(",", "."))
    explicit = re.search(r"\bcantidad\s*[:=]\s*(\d{1,4})\b", suffix)
    if explicit:
        return positive_decimal(explicit[1])
    # A row-leading digit is quantity ONLY when the table explicitly starts Cant then Producto.
    if leading and re.search(r"\bcant(?:idad)?\b.{0,40}\b(?:producto|descripcion)\b", header):
        return positive_decimal(leading)
    literal = re.search(r"\b(un|uno|dos|tres|cuatro|cinco|catorce)\s*\((\d+)\)\s*$", prefix)
    return positive_decimal(literal[2]) if literal else None


def extract_rows(
    fragment: dict[str, Any],
    *,
    complete: bool = True,
    quantity_header: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Explicit product-headed rows; no process-global money divided by item count."""
    text = fragment["text"]
    stage, classification = classify_stage(fragment["original_name"], text)
    folded = normalize_text(text)
    if re.search(
        r"\b(?:experiencia contractual|certificado de experiencia|factura de venta)\b", folded
    ):
        return []
    rows = []
    for start in re.finditer(r"(?m)^.*$", text):
        head = HEAD.match(start[0])
        if not head:
            continue
        if re.match(r"\s*(?:celular|smartphone)\s*:", start[0], re.I):
            continue  # Telephone contact, not a product.
        before = text[max(0, start.start() - 700) : start.start()]
        header = _norm(before)
        if quantity_header and "cantidad" not in header:
            header = "descripcion unidad cantidad " + header
        window = text[start.start() : start.start() + 1100]
        stop = NEXT_ITEM.search(window, max(len(start[0]), 1))
        if stop:
            window = window[: stop.start()]
        vertical_next_row = re.search(r"\n\s*\d{1,3}\s*\n\s*\d{8}\s*\n", window)
        if vertical_next_row:
            window = window[: vertical_next_row.start()]
        window = re.split(
            r"\b(?:CEDULA|CÉDULA|NIT|CONTACTO|CORREO|EMAIL|REPRESENTANTE|SUPERVISOR|FIRMA)\b",
            window,
            flags=re.I,
        )[0]
        amounts = [(m, money(m[1])) for m in MONEY.finditer(window)]
        amounts = [(m, v) for m, v in amounts if v and v >= 1000]
        description_end = amounts[0][0].start() if amounts else min(len(window), 550)
        description = window[head.start(2) : description_end].strip(" \n")
        q = _quantity(_norm(before[-70:]), _norm(description), header, head[1])
        if q is None and re.search(r"\bcant(?:idad)?\b.{0,40}\b(?:producto|descripcion)\b", header):
            next_line_quantity = re.search(r"\n\s*(\d{1,4})\s*\|", description)
            if next_line_quantity:
                q = positive_decimal(next_line_quantity[1])
        # Extract quantity before stripping the trailing table cells.
        if q is not None:
            description = re.sub(
                r"\s+[|]*\s*(?:(?:unidad(?:es)?|und|un)\s+)?\d{1,4}(?:[.,]00)?\s*[|]*\s*$",
                "",
                description,
                flags=re.I,
            )
        specs = _specs(description)
        if re.search(r"\btelevisor y reproductor\b", normalize_text(description)):
            continue  # A support/mount referring to a TV is not the TV itself.
        if not specs["screen_size_inches"] and not specs["model"] and not q:
            continue
        if q is None and not (
            len(amounts) == 1
            and re.search(r"\btotal\b", header)
            and not re.search(r"(?:valor|precio)\s*unit|valorunitario|price per unit", header)
        ):
            # Unresolved specification excerpts are already preserved by the
            # existing facts projection; don't manufacture rows from narrative.
            continue
        notes = []
        if not specs["screen_size_inches"] and not specs["model"]:
            notes.append("aggregate_item_scope_unresolved")
        if not complete:
            notes.append("partial_document_coverage")
        if (
            len(
                re.findall(
                    r"\b(?:samsung|lg|tcl|hisense|kalley|caixun|sony)\b",
                    normalize_text(description),
                )
            )
            > 1
            and not specs["brand"]
        ):
            notes.append("conflicting_brand_in_row")
        mixed = bool(
            re.search(
                r"\b(?:kit de robotica|computadores?|aire acondicionado|"
                r"cableado|instalacion de red)\b",
                normalize_text(description),
            )
        )
        if mixed:
            notes.append("mixed_product_bundle")
        ev = _evidence(fragment, window[: description_end + 150], stage, "explicit_product_table")
        if quantity_header:
            ev["quantity_header_evidence"] = quantity_header
        fields = {}
        if q and "aggregate_item_scope_unresolved" not in notes:
            fields["quantity"] = _cell(q, ev)
        unit = re.search(r"\b(unidad(?:es)?|und|un)\b", normalize_text(window[:description_end]))
        if unit:
            fields["unit"] = _cell("UNIDAD", ev)
        col = STAGE_COLUMN.get(stage)
        explicit_unit = bool(
            re.search(
                r"(?:valor|precio|vr\.?|v\.?)\s*unit(?:ario)?\b|valorunitario|price per unit",
                header,
            )
        )
        explicit_total = bool(re.search(r"\b(?:total|vr\.? total)\b", header))
        if (
            col
            and not mixed
            and not q
            and len(amounts) == 1
            and explicit_total
            and not explicit_unit
        ):
            fields[col + "_total"] = _cell(amounts[0][1], ev)
            notes.append("item_total_without_same_row_quantity")
        if q and col and not mixed and "aggregate_item_scope_unresolved" not in notes:
            secop_estimated_actual = bool(
                re.search(
                    r"precio unitario estimado\s+precio unitario\s+precio total estimado", header
                )
            )
            if (
                secop_estimated_actual
                and len(amounts) == 4
                and abs(q * (amounts[0][1] or Decimal(0)) - (amounts[2][1] or Decimal(0))) <= 1
                and abs(q * (amounts[1][1] or Decimal(0)) - (amounts[3][1] or Decimal(0))) <= 1
            ):
                ev["rule"] = "secop_explicit_estimated_and_actual_columns"
                fields["budget_unit_price"] = _cell(amounts[0][1], ev)
                fields["budget_total"] = _cell(amounts[2][1], ev)
                fields[col + "_unit_price"] = _cell(amounts[1][1], ev)
                fields[col + "_total"] = _cell(amounts[3][1], ev)
            elif (
                len(amounts) == 2
                and not secop_estimated_actual
                and (explicit_unit or stage == "economic_offer")
                and abs(q * (amounts[0][1] or Decimal(0)) - (amounts[1][1] or Decimal(0)))
                <= Decimal("1")
            ):
                fields[col + "_unit_price"] = _cell(amounts[0][1], ev)
                fields[col + "_total"] = _cell(amounts[1][1], ev)
            elif len(amounts) == 1 and explicit_total and not explicit_unit:
                fields[col + "_total"] = _cell(amounts[0][1], ev)
            elif amounts:
                notes.append("ambiguous_price_columns_or_arithmetic")
        elif amounts:
            notes.append("quantity_or_item_scope_unresolved")
        if stage == "evaluation_report":
            notes.append("evaluation_is_not_award")
        if stage == "unknown":
            notes.append("unknown_document_stage")
        if not amounts and q is None and not any(specs.values()):
            continue
        vertical_position = re.search(r"(?:^|\n)\s*(\d{1,3})\s*\n\s*\d{8}\s*$", before)
        row = {
            "id": _id(
                [
                    ev.get("input_sha256") or ev["document_version_id"],
                    ev["source_page"],
                    description,
                    fields,
                ]
            ),
            "item_description": description,
            "normalized_product": "televisor"
            if "tv" in normalize_text(head[2]) or "televisor" in normalize_text(head[2])
            else "telefono_inteligente",
            "item_number": (head[1] or (vertical_position[1] if vertical_position else None))
            if not re.search(r"\bcant(?:idad)?\b.{0,40}\b(?:producto|descripcion)\b", header)
            else None,
            "brand": specs.pop("brand"),
            "model": specs.pop("model"),
            "specifications": specs,
            "fields": fields,
            "bidder": _supplier(text[:1500]),
            "offer_reference": ev["document_version_id"],
            "explicit_offer_reference": _offer_reference(text[:1800]),
            "acceptance_explicit": stage == "award"
            and bool(re.search(r"aceptacion de oferta|se acepta la oferta", _norm(text[:1800]))),
            "source_stage": stage,
            "classification_basis": classification,
            "evidence": [ev],
            "notes": notes,
            "vat_basis": "included"
            if re.search(r"\b(?:iva incluido|incluye iva)\b", normalize_text(window))
            else "undetermined",
        }
        rows.append(row)
    return rows


def from_existing_product(
    product: dict[str, Any], fragments: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Reuse existing facts/spec excerpts without promoting ambiguous prior row rules."""
    evidence = product.get("evidence") or []
    if not evidence:
        return None
    entry = evidence[0]
    sources = (entry.get("source_locator") or {}).get("sources") or []
    source = sources[0] if sources else entry
    fragment_id = source.get("content_fragment_id") or entry.get("fragment_id")
    fragment = fragments.get(str(fragment_id))
    if not fragment:
        return None
    stage, basis = classify_stage(fragment["original_name"], fragment["text"])
    if re.search(
        r"\b(?:factura|experiencia contractual|certificado de experiencia)\b",
        normalize_text(fragment["text"]),
    ):
        return None
    ev = _evidence(fragment, product["description"], stage, "existing_fact_or_specification")
    ev["fact_id"] = entry.get("fact_id")
    ev["canonical_ids"] = entry.get("canonical_ids", [])
    fields = {}
    for field in ("quantity", "unit"):
        if product.get(field) is not None:
            fields[field] = _cell(product[field], ev, confidence=product["confidence"])
    col = STAGE_COLUMN.get(stage)
    if product.get("price_reliable") and col:
        for field, source_field in (("unit_price", "unit_price_cop"), ("total", "total_cop")):
            if product.get(source_field) is not None:
                fields[col + "_" + field] = _cell(
                    product[source_field], ev, confidence=product["confidence"]
                )
    return {
        "id": product["observation_id"],
        "item_description": product["description"],
        "normalized_product": "televisor",
        "item_number": None,
        "brand": product.get("brand"),
        "model": product.get("model"),
        "specifications": {
            k: product.get(k) for k in ("screen_size_inches", "resolution", "panel", "smart")
        },
        "fields": fields,
        "bidder": _supplier(fragment["text"][:1500]),
        "offer_reference": fragment["document_version_id"],
        "explicit_offer_reference": _offer_reference(fragment["text"][:1800]),
        "acceptance_explicit": False,
        "source_stage": stage,
        "classification_basis": basis,
        "evidence": [ev],
        "notes": list(product.get("warnings", [])),
        "vat_basis": product.get("vat_basis", "undetermined"),
    }


def match_item(first: dict[str, Any], second: dict[str, Any]) -> str | None:
    if first["normalized_product"] != second["normalized_product"]:
        return None
    same_position = bool(
        first.get("item_number") and first["item_number"] == second.get("item_number")
    )
    if first.get("item_number") and second.get("item_number") and not same_position:
        return None
    # Position needs a shared specific attribute even to identify a conflict.
    shared = [
        k
        for k, v in first["specifications"].items()
        if v is not None and second["specifications"].get(k) == v
    ]
    clashes = [
        k
        for k, v in first["specifications"].items()
        if v is not None
        and second["specifications"].get(k) is not None
        and second["specifications"][k] != v
    ]
    if clashes:
        return "position_with_specification_conflict" if same_position and shared else None
    if first.get("brand") and second.get("brand") and first["brand"] != second["brand"]:
        return "position_with_brand_conflict" if same_position and shared else None
    if first.get("model") and second.get("model"):
        if first["model"] == second["model"] and first.get("brand") == second.get("brand"):
            return "same_explicit_brand_model"
        return "position_with_model_conflict" if same_position and shared else None
    a, b = _norm(first["item_description"]), _norm(second["item_description"])
    if a == b and len(a) >= 18:
        return "same_normalized_description"
    tokens_a, tokens_b = set(re.findall(r"\w+", a)), set(re.findall(r"\w+", b))
    words_a, words_b = re.findall(r"\w+", a), re.findall(r"\w+", b)
    if (
        "screen_size_inches" in shared
        and len(shared) >= 3
        and len(words_a) >= 18
        and words_a[:18] == words_b[:18]
    ):
        return "same_specific_attributes_and_explicit_description_prefix"
    if (
        len(shared) >= 3
        and "screen_size_inches" in shared
        and len(tokens_a & tokens_b) >= 15
        and len(tokens_a & tokens_b) / len(tokens_a | tokens_b) >= 0.92
    ):
        return "same_specific_attributes_and_near_identical_description"
    if same_position and "screen_size_inches" in shared:
        return "same_position_and_size"
    # Complete matching TV attributes, with at least a matching brand, not size alone.
    if len(shared) == 4 and first.get("brand") and first["brand"] == second.get("brand"):
        return "same_brand_and_explicit_specifications"
    return None


def derive_unit_price(
    total: dict[str, Any] | None,
    quantity: dict[str, Any] | None,
    *,
    single_item_scope: bool,
    conflicts: bool = False,
) -> dict[str, Any] | None:
    if not total or not quantity or not single_item_scope or conflicts:
        return None
    t, q = positive_decimal(total["value"]), positive_decimal(quantity["value"])
    if not t or not q:
        return None
    return {
        "value": str(t / q),
        "value_origin": "calculated",
        "confidence": "0.8",
        "formula": "item_total / item_quantity",
        "evidence": total["evidence"] + quantity["evidence"],
        "calculation_inputs": [{"field": "item_total", **total}, {"field": "quantity", **quantity}],
    }


def reconstruct(
    process: dict[str, Any], observations: list[dict[str, Any]], coverage: list[dict[str, Any]]
) -> dict[str, Any]:
    """Keep each alternative, scope canonical keys, and OR conflicts across stages."""
    groups: list[dict[str, Any]] = []
    seen = set()
    for obs in observations:
        if obs["id"] in seen:
            continue
        seen.add(obs["id"])
        candidates = [
            (g, match_item(g["observations"][0], obs))
            for g in groups
            if all(match_item(member, obs) for member in g["observations"])
        ]
        matches = [(g, reason) for g, reason in candidates if reason]
        if len(matches) == 1:
            group, reason = matches[0]
            group["links"].append({"observation_id": obs["id"], "basis": reason})
            group["observations"].append(obs)
        else:
            groups.append(
                {
                    "observations": [obs],
                    "links": [],
                    "notes": ["ambiguous_item_association"] if len(matches) > 1 else [],
                }
            )
    products = []
    for group in groups:
        members = group["observations"]
        first = members[0]
        fields: dict[str, Any] = {}
        conflicts = []
        notes = list(group["notes"])
        for field in (
            "quantity",
            "unit",
            "brand",
            "model",
            *ECONOMIC_FIELDS,
            "bidder",
            "awarded_supplier",
            "evaluated_bidder",
            "contracted_supplier",
        ):
            alternatives = []
            for obs in members:
                cell = obs["fields"].get(field)
                if field == "brand" and "conflicting_brand_in_row" in obs["notes"]:
                    for brand in sorted(
                        set(
                            re.findall(
                                r"\b(?:samsung|lg|tcl|hisense|kalley|caixun|sony)\b",
                                _norm(obs["item_description"]),
                            )
                        )
                    ):
                        alternatives.append(
                            {
                                **_cell(brand.upper(), obs["evidence"][0]),
                                "observation_id": obs["id"],
                                "offer_reference": obs["offer_reference"],
                                "bidder": obs.get("bidder"),
                                "source_stage": obs["source_stage"],
                            }
                        )
                if field in ("brand", "model") and obs.get(field):
                    cell = _cell(obs[field], obs["evidence"][0])
                role_stage = {
                    "bidder": "economic_offer",
                    "evaluated_bidder": "evaluation_report",
                    "awarded_supplier": "award",
                    "contracted_supplier": "contract",
                }
                if obs["source_stage"] == role_stage.get(field) and obs.get("bidder"):
                    cell = _cell(obs["bidder"], obs["evidence"][0])
                if cell:
                    alternatives.append(
                        {
                            **cell,
                            "observation_id": obs["id"],
                            "offer_reference": obs["offer_reference"],
                            "bidder": obs.get("bidder"),
                            "source_stage": obs["source_stage"],
                        }
                    )
            values = {a["value"] for a in alternatives}
            # Different offers are expected alternatives, not silently selected winners.
            known_bidders = {_norm(a["bidder"]) for a in alternatives if a.get("bidder")}
            same_bidder = len(known_bidders) == 1 and all(a.get("bidder") for a in alternatives)
            offer_variants = (
                field.startswith(("offer_", "evaluated_offer_")) and not same_bidder
            ) or field in ("bidder", "evaluated_bidder")
            status = (
                "absent"
                if not values
                else "confirmed"
                if len(values) == 1
                else "uncertain"
                if offer_variants
                else "conflicting"
            )
            if status == "conflicting":
                conflicts.append(field)
            fields[field] = {
                "value": next(iter(values)) if len(values) == 1 else None,
                "status": status,
                "alternatives": alternatives,
            }
        spec_variants = {
            k: {
                o["specifications"].get(k)
                for o in members
                if o["specifications"].get(k) is not None
            }
            for k in first["specifications"]
        }
        conflicts += [
            "specifications." + k for k, values in spec_variants.items() if len(values) > 1
        ]
        notes += list(dict.fromkeys(n for o in members for n in o["notes"]))
        # Derivation is per observation and same row, NEVER across a global contract total.
        for column in ("budget", "offer", "evaluated_offer", "awarded", "contract"):
            target = fields[column + "_unit_price"]
            for obs in members:
                total, qty = obs["fields"].get(column + "_total"), obs["fields"].get("quantity")
                explicit = obs["fields"].get(column + "_unit_price")
                calculated = derive_unit_price(
                    total,
                    qty,
                    single_item_scope="mixed_product_bundle" not in obs["notes"],
                    conflicts=bool(conflicts),
                )
                if explicit and calculated:
                    if abs(Decimal(explicit["value"]) - Decimal(calculated["value"])) > Decimal(
                        "0.01"
                    ):
                        conflicts.append(column + "_arithmetic")
                    for alternative in target["alternatives"]:
                        if alternative["observation_id"] == obs["id"]:
                            alternative["arithmetic_verification"] = {
                                "calculated_value": calculated["value"],
                                "matches_explicit": abs(
                                    Decimal(explicit["value"]) - Decimal(calculated["value"])
                                )
                                <= Decimal("0.01"),
                                "calculation_inputs": calculated["calculation_inputs"],
                            }
                    continue
                if not explicit and calculated:
                    a = {
                        **calculated,
                        "observation_id": obs["id"],
                        "offer_reference": obs["offer_reference"],
                        "bidder": obs.get("bidder"),
                        "source_stage": obs["source_stage"],
                    }
                    target["alternatives"].append(a)
            # A linked row in another page/document may provide quantity. It must
            # have the same legal stage (and offer identity for an offer); a
            # requested budget quantity does not prove the contractual quantity.
            totals = fields[column + "_total"]
            if (
                not target["alternatives"]
                and totals["status"] == "confirmed"
                and fields["quantity"]["status"] == "confirmed"
                and not conflicts
            ):
                for total_cell in totals["alternatives"]:
                    qty_cells = [
                        q
                        for q in fields["quantity"]["alternatives"]
                        if (
                            q["source_stage"] == total_cell["source_stage"]
                            and (
                                column not in ("offer", "evaluated_offer")
                                or q["offer_reference"] == total_cell["offer_reference"]
                            )
                        )
                    ]
                    if not qty_cells:
                        continue
                    derived = derive_unit_price(
                        total_cell,
                        qty_cells[0],
                        single_item_scope=True,
                    )
                    if derived:
                        target["alternatives"].append(
                            {
                                **derived,
                                "observation_id": total_cell["observation_id"],
                                "offer_reference": total_cell["offer_reference"],
                                "bidder": total_cell.get("bidder"),
                                "source_stage": total_cell["source_stage"],
                                "quantity_observation_id": qty_cells[0]["observation_id"],
                            }
                        )
            values = {a["value"] for a in target["alternatives"]}
            target["value"] = next(iter(values)) if len(values) == 1 else None
            target["status"] = (
                "absent"
                if not values
                else "confirmed"
                if len(values) == 1
                else "uncertain"
                if column in ("offer", "evaluated_offer")
                and (
                    len({a.get("bidder") for a in target["alternatives"]}) != 1
                    or any(not a.get("bidder") for a in target["alternatives"])
                )
                else "conflicting"
            )
            if target["status"] == "conflicting":
                conflicts.append(column + "_unit_price")
        awarded, contractual = (
            fields["awarded_unit_price"]["value"],
            fields["contract_unit_price"]["value"],
        )
        if awarded and contractual and Decimal(awarded) != Decimal(contractual):
            conflicts.append("award_contract_unit_price_disagreement")
        price = None
        for column in ("contract", "awarded"):
            candidate = fields[column + "_unit_price"]
            blocking_conflicts = [c for c in conflicts if not c.startswith("budget_")]
            if candidate["value"] and candidate["status"] == "confirmed" and not blocking_conflicts:
                allowed = [
                    a
                    for a in candidate["alternatives"]
                    if _purchase_evidence_valid(a, members, process)
                ]
                if allowed:
                    price = {
                        "column": column + "_unit_price",
                        "value": candidate["value"],
                        "evidence": allowed,
                        "origin": allowed[0]["value_origin"],
                    }
                    if conflicts:
                        notes.append("earlier_budget_conflicts_preserved_manual_review")
                    break
        # Recommendations and equal global amounts never establish acceptance.
        if price is None and not conflicts:
            price = accepted_offer_price(process, members, fields["offer_unit_price"])
            if price is None:
                price = accepted_offer_price(process, members, fields["evaluated_offer_unit_price"])
        if price is None:
            notes.append("no_verified_purchase_unit_price")
        if not group["links"] and len(members) == 1:
            notes.append("no_cross_stage_link")
        item_id = _id([process["id"], sorted(o["id"] for o in members)])
        scoped_canonicals = [
            {
                "id": _id([item_id, "PURCHASE_ITEM"]),
                "canonical_type": "PURCHASE_ITEM",
                "canonical_key": item_id,
                "value": first["item_description"],
                "evidence": [e for o in members for e in o["evidence"]],
                "scope": "research_projection_not_global_canonical",
            }
        ]
        for field, state in fields.items():
            concept = (
                "PURCHASE_ITEM"
                if field == "item_description"
                else "QUANTITY"
                if field == "quantity"
                else "UNIT_PRICE_COP"
                if field.endswith("unit_price")
                else "TOTAL_COP"
                if field.endswith("total")
                else field.upper()
            )
            if field == "budget_total":
                concept = "BUDGET_COP"
            for a in state["alternatives"]:
                scoped_canonicals.append(
                    {
                        "id": _id([item_id, field, a]),
                        "canonical_type": concept,
                        "canonical_key": f"{item_id}:{field}:{a['offer_reference']}",
                        "field": field,
                        "status": state["status"],
                        "value": a["value"],
                        "value_origin": a["value_origin"],
                        "evidence": a["evidence"],
                        "scope": "research_projection_not_global_canonical",
                    }
                )
        products.append(
            {
                "id": item_id,
                "process_identity": process["id"],
                "process_code": process["reference"],
                "item_description": first["item_description"],
                "normalized_product": first["normalized_product"],
                "brand": fields["brand"]["value"],
                "model": fields["model"]["value"],
                "specifications": {
                    k: next(iter(v)) if len(v) == 1 else None for k, v in spec_variants.items()
                },
                "specification_evidence": {
                    k: [
                        {"value": o["specifications"][k], "evidence": o["evidence"]}
                        for o in members
                        if o["specifications"].get(k) is not None
                    ]
                    for k in spec_variants
                },
                "other_specifications": {
                    "interactive_touchscreen": any(
                        re.search(r"\b(?:tactil|interactiva)\b", _norm(o["item_description"]))
                        for o in members
                    ),
                    "professional_display": any(
                        re.search(
                            r"\b(?:business|profesional|signage|hotelero|hospitality)\b|24\s*/\s*7",
                            _norm(o["item_description"]),
                        )
                        for o in members
                    ),
                },
                "quantity": fields["quantity"]["value"],
                "unit": fields["unit"]["value"],
                **{k: fields[k]["value"] for k in ECONOMIC_FIELDS},
                "bidder": fields["bidder"]["value"],
                "awarded_supplier": fields["awarded_supplier"]["value"],
                "evaluated_bidder": fields["evaluated_bidder"]["value"],
                "contracted_supplier": fields["contracted_supplier"]["value"],
                "fields": fields,
                "observations": members,
                "links": group["links"],
                "canonical_projection": scoped_canonicals,
                "conflict_status": "conflicting"
                if conflicts
                else "uncertain"
                if price is None
                else "confirmed",
                "conflicts": sorted(set(conflicts)),
                "notes": list(dict.fromkeys(notes)),
                "purchase_price": price,
                "requires_manual_review": bool(conflicts or price is None),
            }
        )
    for product in products:
        reference = product["model"]
        if not reference:
            continue
        peers = [p for p in products if p["model"] == reference]
        sizes = {
            p["specifications"].get("screen_size_inches")
            for p in peers
            if p["specifications"].get("screen_size_inches")
        }
        if len(sizes) > 1:
            product["conflicts"].append("model_reused_for_incompatible_sizes")
            product["conflict_status"] = "conflicting"
            product["requires_manual_review"] = True
            product["purchase_price"] = None
            product["fields"]["model"]["status"] = "conflicting"
            product["model_conflict_evidence"] = [
                {
                    "item_id": p["id"],
                    "specifications": p["specifications"],
                    "evidence": [e for o in p["observations"] for e in o["evidence"]],
                }
                for p in peers
            ]
    return {
        "process_identity": process["id"],
        "process_code": process["reference"],
        "document_coverage": coverage,
        "products": products,
        "process_global_contracts": [
            {
                "id": c.get("id_contrato"),
                "total": c.get("valor_del_contrato"),
                "supplier": c.get("proveedor_adjudicado"),
                "signed_at": c.get("fecha_de_firma"),
                "scope": "process_global_not_allocated_to_items",
                "source": "socrata_jbjy-vk9h",
            }
            for c in process.get("contracts", [])
        ],
    }


def _purchase_evidence_valid(
    alternative: dict[str, Any], observations: list[dict[str, Any]], process: dict[str, Any]
) -> bool:
    obs = next(o for o in observations if o["id"] == alternative["observation_id"])
    if any(
        n in obs["notes"]
        for n in (
            "partial_document_coverage",
            "mixed_product_bundle",
            "conflicting_brand_in_row",
            "source_reference_unverified",
            "document_scope_conflict",
            "aggregate_item_scope_unresolved",
        )
    ):
        return False
    document = next(
        (
            d
            for d in process.get("documents", [])
            if d["name"] == obs["evidence"][0]["source_document"]
        ),
        None,
    )
    if document and document.get("coverage_complete") is False:
        return False
    verified_versions = process.get("verified_document_versions")
    if verified_versions is not None:
        return obs["evidence"][0]["document_version_id"] in verified_versions.get(
            obs["source_stage"], []
        )
    if obs["source_stage"] == "contract":
        return obs["evidence"][0]["source_document"] in process.get(
            "verified_contract_documents", []
        )
    return obs["source_stage"] == "award" and obs["evidence"][0]["source_document"] in process.get(
        "verified_award_documents", []
    )


def accepted_offer_price(
    process: dict[str, Any], members: list[dict[str, Any]], field: dict[str, Any]
) -> dict[str, Any] | None:
    """Explicit acceptance + same offer reference, supplier, product and quantity."""
    candidates = []
    for a in field["alternatives"]:
        offer = next(o for o in members if o["id"] == a["observation_id"])
        if offer["source_stage"] not in ("economic_offer", "evaluation_report") or not offer.get(
            "explicit_offer_reference"
        ):
            continue
        if not offer.get("bidder") or any(n != "evaluation_is_not_award" for n in offer["notes"]):
            continue
        for acceptance in members:
            if not acceptance.get("acceptance_explicit") or not acceptance.get("bidder"):
                continue
            if acceptance["evidence"][0]["source_document"] not in process.get(
                "verified_award_documents", []
            ):
                continue
            if process.get("verified_document_versions") is not None and (
                acceptance["evidence"][0]["document_version_id"]
                not in process["verified_document_versions"].get("award", [])
            ):
                continue
            if (
                acceptance.get("explicit_offer_reference") == offer["explicit_offer_reference"]
                and _norm(acceptance["bidder"]) == _norm(offer["bidder"])
                and acceptance["fields"].get("quantity", {}).get("value")
                == offer["fields"].get("quantity", {}).get("value")
                and offer["fields"].get("quantity")
                and match_item(acceptance, offer)
                and not acceptance["notes"]
            ):
                candidates.append({**a, "acceptance_evidence": acceptance["evidence"]})
    if len({a["value"] for a in candidates}) != 1:
        return None
    return {
        "column": "accepted_offer_unit_price",
        "value": candidates[0]["value"],
        "origin": candidates[0]["value_origin"],
        "evidence": candidates,
    }


def verified_documents(
    process: dict[str, Any],
    fragments: list[dict[str, Any]],
    stage: str,
    *,
    return_versions: bool = False,
) -> list[str]:
    """Verify the exact document, not an unrelated document of the same process."""
    documents: dict[tuple[str, str], list[str]] = {}
    for f in fragments:
        if classify_stage(f["original_name"], f["text"])[0] == stage:
            documents.setdefault((f["document_version_id"], f["original_name"]), []).append(
                f["text"]
            )
    result = []
    compact_ref = re.sub(r"[^a-z0-9]", "", normalize_text(process["reference"]))
    for (version, name), pages in documents.items():
        content = re.sub(r"[^a-z0-9]", "", normalize_text(name + " " + " ".join(pages)))
        current_reference = len(compact_ref) >= 6 and compact_ref in content
        if stage == "award" and current_reference:
            result.append(version if return_versions else name)
        elif stage == "contract":
            for contract in process.get("contracts", []):
                if not contract.get("fecha_de_firma"):
                    continue
                identifier = re.sub(
                    r"[^a-z0-9]", "", normalize_text(contract.get("id_contrato") or "")
                )
                if (len(identifier) >= 6 and identifier in content) or (
                    current_reference and len(process["contracts"]) == 1
                ):
                    result.append(version if return_versions else name)
                    break
    return result


def purchase_date_for_item(
    process: dict[str, Any], chosen: dict[str, Any] | None
) -> tuple[str | None, list[dict[str, Any]]]:
    """Exact contract identity; publication is never a substitute for purchase date."""
    if not chosen:
        return None, []
    used_documents = {
        e.get("source_document") for a in chosen["evidence"] for e in a.get("evidence", [])
    }
    signed = []
    for contract in process.get("contracts", []):
        identifier = re.sub(r"[^a-z0-9]", "", _norm(contract.get("id_contrato") or ""))
        if contract.get("fecha_de_firma") and (
            len(process["contracts"]) == 1
            or any(
                identifier and identifier in re.sub(r"[^a-z0-9]", "", _norm(name or ""))
                for name in used_documents
            )
        ):
            signed.append(contract)
    values = {c["fecha_de_firma"] for c in signed}
    evidence = [
        {
            "source": "socrata_jbjy-vk9h",
            "id_contrato": c.get("id_contrato"),
            "field": "fecha_de_firma",
            "value": c["fecha_de_firma"],
        }
        for c in signed
    ]
    return (next(iter(values)) if len(values) == 1 else None), evidence


def build_cycles(
    report: dict[str, Any], fragments_by_process: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    cycles = []
    comparison_products = []
    policy_60d = report.get("comparison_policy") == "research-60d-v1"
    for process in report["processes"]:
        if not process.get("tv_confirmed"):
            continue
        fragments = fragments_by_process.get(process["id"], [])
        by_id = {str(f["id"]): f for f in fragments}
        observations = []
        coverage = []
        verified = dict(process)

        verified["verified_contract_documents"] = verified_documents(process, fragments, "contract")
        verified["verified_award_documents"] = verified_documents(process, fragments, "award")
        verified["verified_document_versions"] = {
            stage: verified_documents(process, fragments, stage, return_versions=True)
            for stage in ("contract", "award")
        }
        for doc in process["documents"]:
            fs = [f for f in fragments if f["original_name"] == doc["name"]]
            stage, basis = classify_stage(doc["name"], "\n".join(f["text"][:500] for f in fs[:1]))
            coverage.append(
                {
                    "stage": stage,
                    "classification_basis": basis,
                    "document": doc["name"],
                    "selected": doc["selected"],
                    "downloaded": doc["downloaded"],
                    "extraction_status": doc["extraction_status"],
                    "coverage_complete": doc["coverage_complete"],
                    "pages_with_text": sorted(
                        {
                            f["source_locator"].get("page_number")
                            for f in fs
                            if f["source_locator"].get("page_number") is not None
                        }
                    ),
                }
            )
        quantity_headers: dict[str, dict[str, Any]] = {}
        ordered_fragments = sorted(
            fragments,
            key=lambda f: (f["original_name"], f["source_locator"].get("page_number") or 0),
        )
        for f in ordered_fragments:
            table_heading = re.search(r"descripcion\s+unidad\s+cantidad", _norm(f["text"]))
            if table_heading:
                quantity_headers[f["original_name"]] = _evidence(
                    f,
                    "Descripción Unidad Cantidad",
                    classify_stage(f["original_name"])[0],
                    "continued_quantity_table_header",
                )
            header = quantity_headers.get(f["original_name"])
            if header and (
                (f["source_locator"].get("page_number") or 0) - (header.get("source_page") or 0) > 2
            ):
                header = None
            source_doc: dict[str, Any] = next(
                (d for d in process["documents"] if d["name"] == f["original_name"]), {}
            )
            observations.extend(
                extract_rows(
                    f,
                    complete=source_doc.get("coverage_complete") is not False,
                    quantity_header=header,
                )
            )
        for product in process["products"]:
            obs = from_existing_product(product, by_id)
            if obs:
                observations.append(obs)
        cycle = reconstruct(verified, observations, coverage)
        for product in cycle["products"]:
            matched_suppliers = {
                c.get("proveedor_adjudicado")
                for c in process.get("contracts", [])
                if c.get("proveedor_adjudicado")
                and len(process["contracts"]) == 1
                and any(
                    o["source_stage"] == "contract"
                    and o["evidence"][0]["document_version_id"]
                    in verified["verified_document_versions"]["contract"]
                    for o in product["observations"]
                )
            }
            if len(matched_suppliers) == 1 and not product["contracted_supplier"]:
                supplier = next(iter(matched_suppliers))
                contract = process["contracts"][0]
                ev = {
                    "source_stage": "contract",
                    "source_document": "Socrata jbjy-vk9h",
                    "source_page": None,
                    "extraction_method": "provider_metadata",
                    "evidence_text": (
                        "Proveedor publicado para el contrato vinculado por identidad exacta."
                    ),
                    "source_locator": {
                        "dataset": "jbjy-vk9h",
                        "id_contrato": contract.get("id_contrato"),
                        "field": "proveedor_adjudicado",
                    },
                }
                alternative = {
                    **_cell(supplier, ev, confidence="1.0"),
                    "source_stage": "contract",
                    "observation_id": None,
                    "offer_reference": contract.get("id_contrato"),
                    "bidder": None,
                }
                product["contracted_supplier"] = supplier
                product["fields"]["contracted_supplier"] = {
                    "value": supplier,
                    "status": "confirmed",
                    "alternatives": [alternative],
                }
        cycles.append(cycle)
        for product in cycle["products"]:
            if product["normalized_product"] != "televisor":
                continue
            chosen = product["purchase_price"]
            spec = product["specifications"]
            purchased_at, date_evidence = purchase_date_for_item(process, chosen)
            product["purchase_date"] = purchased_at
            product["purchase_date_source"] = (
                "socrata_jbjy-vk9h_fecha_de_firma" if purchased_at else None
            )
            product["purchase_date_evidence"] = date_evidence
            critical = [c for c in product["conflicts"] if not c.startswith("budget_")]
            comparison_products.append(
                Television(
                    process_id=process["id"],
                    entity=process["entity"],
                    description=product["item_description"],
                    **spec,
                    brand=product["brand"],
                    model=product["model"],
                    quantity=positive_decimal(product["quantity"]),
                    unit=product["unit"],
                    unit_price_cop=positive_decimal(chosen["value"]) if chosen else None,
                    price_reliable=chosen is not None,
                    price_stage="contract"
                    if chosen and chosen["column"].startswith("contract")
                    else "award"
                    if chosen
                    else "unknown",
                    published_at=process["published_at"],
                    observation_id=product["id"],
                    evidence=chosen["evidence"] if chosen else [],
                    warnings=(
                        (
                            ["conflicting_canonical"]
                            if (critical if policy_60d else product["conflicts"])
                            else []
                        )
                        + (
                            ["noncritical_budget_conflict_preserved"]
                            if policy_60d
                            and any(c.startswith("budget_") for c in product["conflicts"])
                            else []
                        )
                    ),
                    vat_basis=product["observations"][0]["vat_basis"],
                    other_specifications={
                        **product["other_specifications"],
                        "process_code": process["reference"],
                    },
                    purchased_at=purchased_at,
                    purchase_date_source=product["purchase_date_source"],
                    purchase_date_evidence=date_evidence,
                )
            )
    all_records = [p for c in cycles for p in c["products"]]
    all_items = (
        [p for p in all_records if p["normalized_product"] == "televisor"]
        if policy_60d
        else all_records
    )
    comparison = (
        compare_public_purchases(
            comparison_products,
            window_start=report["window_start"],
            window_before=report["window_before"],
        )
        if policy_60d
        else compare_observations(comparison_products)
    )
    total = len(all_items)
    priced = sum(p["purchase_price"] is not None for p in all_items)
    return {
        "version": VERSION,
        "source": "socrata_secop_existing_fragments",
        "processes": cycles,
        "summary": {
            "processes": len(cycles),
            "products": total,
            "all_product_records_including_context": len(all_records),
            "economic_fields_completed": dict(
                Counter(k for p in all_items for k in ECONOMIC_FIELDS if p[k] is not None)
            ),
            "products_with_any_economics": sum(
                any(p[k] for k in ECONOMIC_FIELDS) for p in all_items
            ),
            "products_with_document_links": sum(bool(p["links"]) for p in all_items),
            "products_with_cross_stage_links": sum(
                len({o["source_stage"] for o in p["observations"]}) >= 2 for p in all_items
            ),
            "verified_purchase_unit_prices": priced,
            "automatic_comparison_ready_prices": sum(
                p["purchase_price"] is not None
                and not any(
                    not (policy_60d and conflict.startswith("budget_"))
                    for conflict in p["conflicts"]
                )
                for p in all_items
            ),
            "processes_with_verified_purchase_unit_price": sum(
                any(
                    p["purchase_price"]
                    and (not policy_60d or p["normalized_product"] == "televisor")
                    for p in c["products"]
                )
                for c in cycles
            ),
            "products_with_conflicts": sum(bool(p["conflicts"]) for p in all_items),
            "manual_review_products": sum(p["requires_manual_review"] for p in all_items),
            "purchase_price_resolution_pct": round(100 * priced / total, 2) if total else 0,
            "process_purchase_price_resolution_pct": round(
                100
                * sum(
                    any(
                        p["purchase_price"]
                        and (not policy_60d or p["normalized_product"] == "televisor")
                        for p in c["products"]
                    )
                    for c in cycles
                )
                / len(cycles),
                2,
            )
            if cycles
            else 0,
            "processes_with_any_item_economics": sum(
                any(
                    (not policy_60d or p["normalized_product"] == "televisor")
                    and any(p[k] is not None for k in ECONOMIC_FIELDS)
                    for p in c["products"]
                )
                for c in cycles
            ),
            "denominator": "reconstructed_product_records_not_national_population",
        },
        **comparison,
    }
