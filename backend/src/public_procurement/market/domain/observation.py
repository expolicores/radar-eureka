"""Observaciones de precio de mercado (retail), trazables e inmutables."""

import uuid
from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Store(StrEnum):
    ALKOSTO = "alkosto"
    FALABELLA = "falabella"


class AcquisitionMethod(StrEnum):
    SITEMAP = "sitemap"
    STRUCTURED_DATA = "structured_data"
    MANUAL = "manual"
    SIMULATED = "simulated"


class MarketVatBasis(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class MarketObservation:
    """Registro mínimo trazable de una observación (FR-042)."""

    store: Store
    source_reference: str
    product_description: str
    brand: str | None
    model: str | None
    ean: str | None
    screen_size_inches: int
    resolution: str
    panel: str
    effective_price_cop: int
    list_price_cop: int | None
    vat_basis: MarketVatBasis
    seller_is_store: bool
    has_special_conditions: bool
    observed_on: date
    method: AcquisitionMethod

    def __post_init__(self) -> None:
        if self.effective_price_cop <= 0:
            raise ValueError("effective_price_must_be_positive")


@dataclass(frozen=True)
class StoredObservation:
    id: uuid.UUID
    observation: MarketObservation
