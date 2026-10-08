"""Lista priorizada de señales que merecen revisión: filtros y órdenes (reglas puras)."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from public_procurement.shared.text import normalize_text

from .confidence import ConfidenceLevel

CONFIDENCE_RANK = {ConfidenceLevel.HIGH: 3, ConfidenceLevel.MEDIUM: 2, ConfidenceLevel.LOW: 1}


class SignalSort(StrEnum):
    PRIORITY = "priority"
    DEVIATION = "deviation"
    VALUE = "value"
    DATE = "date"


@dataclass(frozen=True)
class SignalRow:
    """Una señal vigente con los datos de la compra que la explican."""

    code: str
    purchase_id: uuid.UUID
    line_number: int
    purchase_reference: str
    source: str
    entity_name: str
    entity_department: str
    supplier_name: str
    supplier_nit: str | None
    item_description: str
    quantity: int | None
    unit_price_cop: int
    median_cop: int
    deviation_pct: Decimal
    match_type: str
    confidence_level: ConfidenceLevel
    confidence_score: int
    signed_on: date


@dataclass(frozen=True)
class SignalFilters:
    text: str | None = None
    department: str | None = None
    source: str | None = None
    confidence: ConfidenceLevel | None = None
    year: int | None = None


def _matches(row: SignalRow, filters: SignalFilters) -> bool:
    if filters.text and filters.text.strip():
        needle = normalize_text(filters.text.strip())
        haystack = " ".join(
            (
                row.code,
                row.purchase_reference,
                row.entity_name,
                row.supplier_name,
                row.supplier_nit or "",
                row.item_description,
            )
        )
        if needle not in normalize_text(haystack):
            return False
    return (
        (filters.department is None or row.entity_department == filters.department)
        and (filters.source is None or row.source == filters.source)
        and (filters.confidence is None or row.confidence_level is filters.confidence)
        and (filters.year is None or row.signed_on.year == filters.year)
    )


def _sort_key(row: SignalRow, sort: SignalSort) -> tuple[Decimal, Decimal, str]:
    """Clave ascendente; las magnitudes van negadas para ordenar de mayor a menor."""
    if sort is SignalSort.DEVIATION:
        return (-row.deviation_pct, Decimal(0), row.code)
    if sort is SignalSort.VALUE:
        return (Decimal(-row.unit_price_cop), Decimal(0), row.code)
    if sort is SignalSort.DATE:
        return (Decimal(-row.signed_on.toordinal()), Decimal(0), row.code)
    # Prioridad: confianza alta primero y, dentro del nivel, mayor desviación.
    return (Decimal(-CONFIDENCE_RANK[row.confidence_level]), -row.deviation_pct, row.code)


def select_signals(
    rows: Sequence[SignalRow], filters: SignalFilters, sort: SignalSort
) -> list[SignalRow]:
    matching = [row for row in rows if _matches(row, filters)]
    return sorted(matching, key=lambda row: _sort_key(row, sort))
