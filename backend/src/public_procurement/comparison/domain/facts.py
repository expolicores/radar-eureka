"""Hechos de entrada de la comparación, propios de este módulo (sin el dominio de otros)."""

import uuid
from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class PurchaseSource(StrEnum):
    SECOP_II = "secop_ii"
    TVEC = "tvec"


class PriceStatus(StrEnum):
    EXPLICIT = "explicit"
    DERIVED = "derived"
    NOT_PUBLISHED = "not_published"
    PENDING_REVIEW = "pending_review"


class VatBasis(StrEnum):
    INCLUDED = "included"
    EXCLUDED = "excluded"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class TvSpec:
    """Lo que hace equivalentes a dos televisores."""

    screen_size_inches: int | None
    resolution: str | None
    panel: str | None

    @property
    def is_complete(self) -> bool:
        return None not in (self.screen_size_inches, self.resolution, self.panel)


@dataclass(frozen=True)
class ItemFacts:
    """Ítem de televisor de una compra, tal como lo necesita la comparación."""

    purchase_id: uuid.UUID
    line_number: int
    source: PurchaseSource
    source_record_id: str
    reference: str
    entity_name: str
    signed_on: date
    unit_price_cop: int | None
    price_status: PriceStatus
    vat_basis: VatBasis
    spec: TvSpec
    brand: str | None
    model: str | None

    @property
    def model_key(self) -> tuple[str, str] | None:
        if self.brand and self.model:
            return (self.brand.strip().lower(), self.model.strip().lower())
        return None


@dataclass(frozen=True)
class MarketFacts:
    """Observación de mercado, tal como la necesita el Benchmark 2."""

    observation_id: uuid.UUID
    store: str
    effective_price_cop: int
    vat_basis: VatBasis
    seller_is_store: bool
    has_special_conditions: bool
    observed_on: date
    spec: TvSpec
