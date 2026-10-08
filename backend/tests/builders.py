"""Test Data Builders compartidos."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Self

from public_procurement.comparison.domain.confidence import ConfidenceLevel
from public_procurement.comparison.domain.facts import (
    ItemFacts,
    MarketFacts,
    PriceStatus,
    PurchaseSource,
    TvSpec,
)
from public_procurement.comparison.domain.facts import VatBasis as FactsVatBasis
from public_procurement.comparison.domain.signals import SignalRow
from public_procurement.exploration.domain.analysis import ItemState
from public_procurement.ingestion.domain.purchase import (
    Resolution,
    Source,
    SourceItem,
    SourcePurchase,
    TvAttributes,
    UnitPriceStatus,
    VatBasis,
)
from public_procurement.shared.config import AppEnvironment, LogLevel, Settings

LOCAL_DATABASE_URL = (
    "postgresql+psycopg://procurement:procurement_local@localhost:5432/public_procurement"
)


class SettingsBuilder:
    def __init__(self) -> None:
        self._database_url = LOCAL_DATABASE_URL
        self._app_env = AppEnvironment.LOCAL
        self._log_level = LogLevel.INFO

    def with_database_url(self, database_url: str) -> Self:
        self._database_url = database_url
        return self

    def with_app_env(self, app_env: AppEnvironment) -> Self:
        self._app_env = app_env
        return self

    def with_log_level(self, log_level: LogLevel) -> Self:
        self._log_level = log_level
        return self

    def build(self) -> Settings:
        return Settings(
            _env_file=None,  # type: ignore[call-arg]
            database_url=self._database_url,
            app_env=self._app_env,
            log_level=self._log_level,
        )


class SourceItemBuilder:
    def __init__(self) -> None:
        self._line_number = 1
        self._description = 'Televisor Smart TV 65", resolución 4K UHD, panel LED'
        self._quantity: int | None = 8
        self._unit_price_cop: int | None = 4_950_000
        self._unit_price_status = UnitPriceStatus.EXPLICIT
        self._vat_basis = VatBasis.INCLUDED

    def with_line_number(self, line_number: int) -> Self:
        self._line_number = line_number
        return self

    def with_description(self, description: str) -> Self:
        self._description = description
        return self

    def with_unit_price(self, unit_price_cop: int | None, status: UnitPriceStatus) -> Self:
        self._unit_price_cop = unit_price_cop
        self._unit_price_status = status
        return self

    def with_vat_basis(self, vat_basis: VatBasis) -> Self:
        self._vat_basis = vat_basis
        return self

    def build(self) -> SourceItem:
        return SourceItem(
            line_number=self._line_number,
            description=self._description,
            quantity=self._quantity,
            unit_price_cop=self._unit_price_cop,
            unit_price_status=self._unit_price_status,
            vat_basis=self._vat_basis,
            attributes=TvAttributes(
                screen_size_inches=65, resolution=Resolution.UHD_4K, is_smart=True
            ),
        )


class SourcePurchaseBuilder:
    def __init__(self) -> None:
        self._source = Source.SECOP_II
        self._identifier = "CO1.PCCNTR.0000142"
        self._entity_name = "Alcaldía Municipal de San Rafael del Valle"
        self._supplier_name = "Tecnología Andina Demo S.A.S."
        self._supplier_nit: str | None = "900.000.142-1"
        self._natural_person = False
        self._total_value_cop: int | None = 39_600_000
        self._items: tuple[SourceItem, ...] = (SourceItemBuilder().build(),)

    def from_tvec(self, identificador_de_la_orden: str) -> Self:
        self._source = Source.TVEC
        self._identifier = identificador_de_la_orden
        return self

    def with_identifier(self, identifier: str) -> Self:
        self._identifier = identifier
        return self

    def with_entity_name(self, entity_name: str) -> Self:
        self._entity_name = entity_name
        return self

    def with_natural_person_supplier(self, document: str) -> Self:
        self._supplier_name = "Juana Pérez Demo"
        self._supplier_nit = document
        self._natural_person = True
        return self

    def with_items(self, *items: SourceItem) -> Self:
        self._items = items
        return self

    def build(self) -> SourcePurchase:
        is_secop = self._source is Source.SECOP_II
        return SourcePurchase(
            source=self._source,
            id_contrato=self._identifier if is_secop else None,
            identificador_de_la_orden=None if is_secop else self._identifier,
            proceso_de_compra="CO1.REQ.0031026" if is_secop else None,
            entity_name=self._entity_name,
            entity_department="Valle del Cauca",
            entity_municipality="San Rafael del Valle",
            supplier_name=self._supplier_name,
            supplier_nit=self._supplier_nit,
            supplier_is_natural_person=self._natural_person,
            object_description="Adquisición de televisores para las aulas",
            modality="Mínima cuantía",
            total_value_cop=self._total_value_cop,
            signed_on=date(2026, 8, 14),
            source_url=None,
            items=self._items,
        )


class ItemStateBuilder:
    """Ítem para el estado del análisis; por defecto, un televisor comparable."""

    def __init__(self) -> None:
        self._is_tv = True
        self._price_pending_review = False
        self._price_missing = False
        self._vat_not_comparable = False

    def not_tv(self) -> Self:
        self._is_tv = False
        return self

    def with_price_pending_review(self) -> Self:
        self._price_pending_review = True
        return self

    def without_price(self) -> Self:
        self._price_missing = True
        return self

    def with_non_comparable_vat(self) -> Self:
        self._vat_not_comparable = True
        return self

    def build(self) -> ItemState:
        return ItemState(
            is_tv=self._is_tv,
            price_pending_review=self._price_pending_review,
            price_missing=self._price_missing,
            vat_not_comparable=self._vat_not_comparable,
        )


TV_65_4K_LED = TvSpec(screen_size_inches=65, resolution="uhd_4k", panel="led")
REFERENCE_SIGNED_ON = date(2026, 8, 14)


class ItemFactsBuilder:
    """Ítem de televisor para la comparación; por defecto, la compra de referencia del mockup."""

    def __init__(self) -> None:
        self._purchase_id = uuid.uuid4()
        self._line_number = 1
        self._source = PurchaseSource.SECOP_II
        self._source_record_id = "CO1.PCCNTR.0000142"
        self._signed_on = REFERENCE_SIGNED_ON
        self._unit_price_cop: int | None = 4_950_000
        self._price_status = PriceStatus.EXPLICIT
        self._vat_basis = FactsVatBasis.INCLUDED
        self._spec = TV_65_4K_LED
        self._brand: str | None = None
        self._model: str | None = None

    def with_purchase_id(self, purchase_id: uuid.UUID) -> Self:
        self._purchase_id = purchase_id
        return self

    def with_line_number(self, line_number: int) -> Self:
        self._line_number = line_number
        return self

    def from_tvec(self, order: str) -> Self:
        self._source = PurchaseSource.TVEC
        self._source_record_id = order
        return self

    def signed_on(self, signed_on: date) -> Self:
        self._signed_on = signed_on
        return self

    def with_price(
        self, unit_price_cop: int | None, status: PriceStatus = PriceStatus.EXPLICIT
    ) -> Self:
        self._unit_price_cop = unit_price_cop
        self._price_status = status
        return self

    def with_vat_basis(self, vat_basis: FactsVatBasis) -> Self:
        self._vat_basis = vat_basis
        return self

    def with_spec(self, size: int, resolution: str = "uhd_4k", panel: str = "led") -> Self:
        self._spec = TvSpec(size, resolution, panel)
        return self

    def with_model(self, brand: str, model: str) -> Self:
        self._brand, self._model = brand, model
        return self

    def build(self) -> ItemFacts:
        return ItemFacts(
            purchase_id=self._purchase_id,
            line_number=self._line_number,
            source=self._source,
            source_record_id=self._source_record_id,
            reference=self._source_record_id,
            entity_name="Entidad Demo",
            signed_on=self._signed_on,
            unit_price_cop=self._unit_price_cop,
            price_status=self._price_status,
            vat_basis=self._vat_basis,
            spec=self._spec,
            brand=self._brand,
            model=self._model,
        )


def comparables_at(prices: list[int], signed_on: date = REFERENCE_SIGNED_ON) -> list[ItemFacts]:
    """Compras comparables (65", 4K, LED, IVA incluido) firmadas en la fecha dada."""
    return [ItemFactsBuilder().with_price(price).signed_on(signed_on).build() for price in prices]


MOCKUP_COMPARABLE_PRICES = [
    2_350_000, 2_480_000, 2_550_000, 2_610_000, 2_690_000, 2_750_000, 2_820_000,
    2_900_000, 2_980_000, 3_050_000, 3_150_000, 3_290_000, 3_400_000, 3_600_000,
]  # fmt: skip


class MarketFactsBuilder:
    """Observación de mercado utilizable; por defecto, de Alkosto el día de la compra."""

    def __init__(self) -> None:
        self._store = "alkosto"
        self._price = 3_199_900
        self._observed_on = REFERENCE_SIGNED_ON
        self._seller_is_store = True
        self._special = False
        self._vat_basis = FactsVatBasis.INCLUDED
        self._spec = TV_65_4K_LED

    def from_store(self, store: str) -> Self:
        self._store = store
        return self

    def with_price(self, price: int) -> Self:
        self._price = price
        return self

    def observed_on(self, observed_on: date) -> Self:
        self._observed_on = observed_on
        return self

    def from_third_party_seller(self) -> Self:
        self._seller_is_store = False
        return self

    def with_special_conditions(self) -> Self:
        self._special = True
        return self

    def build(self) -> MarketFacts:
        return MarketFacts(
            observation_id=uuid.uuid4(),
            store=self._store,
            effective_price_cop=self._price,
            vat_basis=self._vat_basis,
            seller_is_store=self._seller_is_store,
            has_special_conditions=self._special,
            observed_on=self._observed_on,
            spec=self._spec,
        )


class SignalRowBuilder:
    """Señal vigente lista para la lista priorizada; por defecto, la del mockup."""

    def __init__(self) -> None:
        self._code = "SG-2026-0142"
        self._source = "secop_ii"
        self._entity_name = "Alcaldía Municipal de San Rafael del Valle"
        self._department = "Valle del Cauca"
        self._unit_price_cop = 4_950_000
        self._deviation = Decimal("73.1")
        self._confidence = ConfidenceLevel.MEDIUM
        self._signed_on = REFERENCE_SIGNED_ON

    def with_code(self, code: str) -> Self:
        self._code = code
        return self

    def from_tvec(self) -> Self:
        self._source = "tvec"
        return self

    def in_department(self, department: str) -> Self:
        self._department = department
        return self

    def with_entity(self, entity_name: str) -> Self:
        self._entity_name = entity_name
        return self

    def with_price(self, unit_price_cop: int) -> Self:
        self._unit_price_cop = unit_price_cop
        return self

    def with_deviation(self, deviation: str) -> Self:
        self._deviation = Decimal(deviation)
        return self

    def with_confidence(self, confidence: ConfidenceLevel) -> Self:
        self._confidence = confidence
        return self

    def signed_on(self, signed_on: date) -> Self:
        self._signed_on = signed_on
        return self

    def build(self) -> SignalRow:
        return SignalRow(
            code=self._code,
            purchase_id=uuid.uuid4(),
            line_number=1,
            purchase_reference="CO1.PCCNTR.0000142",
            source=self._source,
            entity_name=self._entity_name,
            entity_department=self._department,
            supplier_name="Tecnología Andina Demo S.A.S.",
            supplier_nit="900.000.142-1",
            item_description='TV 65" 4K LED',
            quantity=8,
            unit_price_cop=self._unit_price_cop,
            median_cop=2_860_000,
            deviation_pct=self._deviation,
            match_type="equivalent",
            confidence_level=self._confidence,
            confidence_score=60,
            signed_on=self._signed_on,
        )
