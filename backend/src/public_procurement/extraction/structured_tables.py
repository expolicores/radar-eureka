"""Reconstrucción conservadora de filas: columnas identificadas por encabezados explícitos."""

import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .domain.content import EvidenceFragment
from .domain.text import normalize_extracted_text

AMOUNT = r"\d{1,3}(?:[.'\u2019]\d{3})+(?:,(?:\d{2}|oo))?|\d+(?:,\d{2})?"
UNIT = r"packs?|unidades?|cajas?|paquetes?|piezas?|pares?|bolsas?|kits?"


def parse_cop(value: str) -> Decimal | None:
    cleaned = value.strip().replace("$", "").strip()
    if not re.fullmatch(AMOUNT, cleaned, re.IGNORECASE):
        return None
    cleaned = re.sub(r"[.'\u2019]", "", cleaned).replace(",oo", ",00").replace(",OO", ",00")
    try:
        return Decimal(cleaned.replace(",", "."))
    except InvalidOperation:
        return None


def unit_name(value: str) -> str:
    value = normalize_extracted_text(value)
    if value == "unidades":
        return "UNIDAD"
    if value == "pares":
        return "PAR"
    return value.removesuffix("s").upper()


@dataclass(frozen=True)
class ItemRow:
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal | None
    total: Decimal | None
    sources: tuple[EvidenceFragment, ...]
    group: str
    confidence: str
    span: tuple[int, int] | None = None
    header_sources: tuple[EvidenceFragment, ...] = ()


HEADERS = {
    "item": "item",
    "descripcion": "description",
    "producto": "description",
    "descripcion del bien o servicio": "description",
    "descripcion del item": "description",
    "cant": "quantity",
    "cantidad": "quantity",
    "unidad": "unit",
    "unidad de medida": "unit",
    "valor unitario": "unit_price",
    "precio unitario": "unit_price",
    "valor total": "total",
    "total": "total",
}


def table_items(fragments: list[EvidenceFragment]) -> list[ItemRow]:
    tables: dict[tuple[str, str, str], dict[int, dict[int, list[EvidenceFragment]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for fragment in fragments:
        loc = fragment.source_locator
        table = loc.get("table_number")
        sheet = loc.get("sheet_name")
        row, column = loc.get("row_number"), loc.get("column_number")
        # XLSX locators from 3B-1 carry A1; use its explicit coordinate, not row inference.
        if sheet is not None and (row is None or column is None):
            coordinate = re.fullmatch(r"([A-Z]+)(\d+)", loc.get("cell_range", ""))
            if coordinate:
                row = int(coordinate[2])
                column = 0
                for letter in coordinate[1]:
                    column = column * 26 + ord(letter) - ord("A") + 1
        if (table is None and sheet is None) or row is None or column is None:
            continue
        key = (
            str(fragment.document_version_id),
            str(fragment.extraction_run_id),
            f"table:{table}" if table is not None else f"sheet:{sheet}",
        )
        tables[key][int(row)][int(column)].append(fragment)
    results = []
    for key, rows in tables.items():
        mapping: dict[str, int] = {}
        header_sources: tuple[EvidenceFragment, ...] = ()
        for row_number, cells in sorted(rows.items()):
            texts = {
                column: "".join(f.text for f in sorted(values, key=lambda f: f.ordinal))
                for column, values in cells.items()
            }
            detected = {
                HEADERS[normalize_extracted_text(text)]: column
                for column, text in texts.items()
                if normalize_extracted_text(text) in HEADERS
            }
            if {"description", "quantity", "unit"} <= detected.keys():
                mapping = detected
                header_sources = tuple(f for column in sorted(cells) for f in cells[column])
                continue
            if not mapping or not all(
                mapping[k] in texts for k in ("description", "quantity", "unit")
            ):
                continue
            description = texts[mapping["description"]].strip()
            quantity = texts[mapping["quantity"]].strip()
            unit = normalize_extracted_text(texts[mapping["unit"]])
            if (
                not description
                or not re.fullmatch(r"\d+(?:[.,]\d+)?", quantity)
                or not re.fullmatch(UNIT, unit)
            ):
                continue
            sources = tuple(f for column in sorted(cells) for f in cells[column])
            results.append(
                ItemRow(
                    description,
                    Decimal(quantity.replace(",", ".")),
                    unit_name(unit),
                    parse_cop(texts.get(mapping.get("unit_price", -1), "")),
                    parse_cop(texts.get(mapping.get("total", -1), "")),
                    sources,
                    ":".join(key) + f":row:{row_number}",
                    "1.0",
                    header_sources=header_sources,
                )
            )
    return results
