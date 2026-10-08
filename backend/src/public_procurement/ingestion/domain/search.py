"""Criterios y resultados de la búsqueda de compras (lado de lectura de la ingesta)."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from .purchase import Purchase, Source

LOW_VALUE_LIMIT_COP = 20_000_000
HIGH_VALUE_LIMIT_COP = 100_000_000
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25


class ValueRange(StrEnum):
    LT_20M = "lt_20m"
    BETWEEN_20M_100M = "between_20m_100m"
    GT_100M = "gt_100m"


class PurchaseSort(StrEnum):
    SIGNED_DESC = "signed_desc"
    SIGNED_ASC = "signed_asc"
    VALUE_DESC = "value_desc"
    VALUE_ASC = "value_asc"


@dataclass(frozen=True)
class PurchaseSearchCriteria:
    text: str | None = None
    source: Source | None = None
    modality: str | None = None
    department: str | None = None
    value_range: ValueRange | None = None
    signed_from: date | None = None
    signed_to: date | None = None
    # Restricción por compras (p. ej. «con señal» / «sin señal», calculadas por otro módulo).
    purchase_ids: frozenset[uuid.UUID] | None = None
    exclude_purchase_ids: frozenset[uuid.UUID] | None = None
    sort: PurchaseSort = PurchaseSort.SIGNED_DESC
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page_must_be_positive")
        if not 1 <= self.page_size <= MAX_PAGE_SIZE:
            raise ValueError("page_size_out_of_range")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True)
class StoredPurchase:
    """Compra persistida con su identificador interno."""

    id: uuid.UUID
    purchase: Purchase


@dataclass(frozen=True)
class PurchasePage:
    items: tuple[StoredPurchase, ...]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class PurchaseFilterOptions:
    sources: tuple[Source, ...]
    modalities: tuple[str, ...]
    departments: tuple[str, ...]
    data_cutoff_at: datetime | None
