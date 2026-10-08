"""Servicios de exploración: vistas tipadas de solo lectura sobre las compras.

Sin dependencias HTTP: los mismos servicios podrán exponerse como herramientas de agentes.
"""

import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.comparison.services import (
    ComparisonQueryService,
    ItemResult,
    Outcome,
    build_comparison_query_service,
)
from public_procurement.ingestion.services import (
    ItemClassification,
    PurchaseFilterOptions,
    PurchaseItem,
    PurchaseQueryService,
    PurchaseSearchCriteria,
    Source,
    StoredPurchase,
    UnitPriceStatus,
    VatBasis,
    build_purchase_query_service,
)

from .domain.analysis import AnalysisStatus, ComparisonState, ItemState, derive_analysis_status


@dataclass(frozen=True)
class PurchaseSummaryView:
    id: uuid.UUID
    reference: str
    source: Source
    entity_name: str
    entity_department: str
    supplier_name: str
    object_description: str
    modality: str
    total_value_cop: int | None
    signed_on: date
    analysis_status: AnalysisStatus


@dataclass(frozen=True)
class PurchaseListView:
    items: tuple[PurchaseSummaryView, ...]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class PurchaseItemView:
    line_number: int
    description: str
    classification: ItemClassification
    quantity: int | None
    unit_price_cop: int | None
    unit_price_status: UnitPriceStatus
    vat_basis: VatBasis
    screen_size_inches: int | None
    resolution: str | None
    panel: str | None
    brand: str | None
    model: str | None
    comparison_outcome: Outcome | None
    signal_code: str | None


@dataclass(frozen=True)
class PurchaseDetailView:
    summary: PurchaseSummaryView
    proceso_de_compra: str | None
    entity_municipality: str | None
    supplier_nit: str | None
    supplier_is_natural_person: bool
    source_url: str | None
    items: tuple[PurchaseItemView, ...]
    data_cutoff_at: datetime | None


def _item_state(item: PurchaseItem) -> ItemState:
    return ItemState(
        is_tv=item.classification is ItemClassification.INCLUDED,
        price_pending_review=item.unit_price_status is UnitPriceStatus.PENDING_REVIEW,
        price_missing=item.unit_price_cop is None,
        # Sin IVA o indeterminado: no se compara (nunca se asume el 19 %).
        vat_not_comparable=item.vat_basis is not VatBasis.INCLUDED,
    )


_COMPARISON_STATES = {
    Outcome.SIGNAL: ComparisonState.SIGNAL,
    Outcome.NO_SIGNAL: ComparisonState.NO_SIGNAL,
    Outcome.LOW_PRICE_REVIEW: ComparisonState.LOW_PRICE_REVIEW,
    Outcome.INSUFFICIENT_COMPARABLES: ComparisonState.INSUFFICIENT_COMPARABLES,
}


def _summary(stored: StoredPurchase, outcome: Outcome | None) -> PurchaseSummaryView:
    purchase = stored.purchase
    comparison = _COMPARISON_STATES.get(outcome) if outcome else None
    return PurchaseSummaryView(
        id=stored.id,
        reference=purchase.display_reference,
        source=purchase.source,
        entity_name=purchase.entity_name,
        entity_department=purchase.entity_department,
        supplier_name=purchase.supplier_name,
        object_description=purchase.object_description,
        modality=purchase.modality,
        total_value_cop=purchase.total_value_cop,
        signed_on=purchase.signed_on,
        analysis_status=derive_analysis_status(
            [_item_state(item) for item in purchase.items], comparison
        ),
    )


def _item_view(item: PurchaseItem, result: ItemResult | None) -> PurchaseItemView:
    attributes = item.attributes
    return PurchaseItemView(
        line_number=item.line_number,
        description=item.description,
        classification=item.classification,
        quantity=item.quantity,
        unit_price_cop=item.unit_price_cop,
        unit_price_status=item.unit_price_status,
        vat_basis=item.vat_basis,
        screen_size_inches=attributes.screen_size_inches,
        resolution=attributes.resolution.value if attributes.resolution else None,
        panel=attributes.panel.value if attributes.panel else None,
        brand=attributes.brand,
        model=attributes.model,
        comparison_outcome=result.outcome if result else None,
        signal_code=result.signal_code if result else None,
    )


class ExplorationService:
    def __init__(
        self, purchases: PurchaseQueryService, comparisons: ComparisonQueryService
    ) -> None:
        self._purchases = purchases
        self._comparisons = comparisons

    def list_purchases(
        self, criteria: PurchaseSearchCriteria, has_signal: bool | None = None
    ) -> PurchaseListView:
        if has_signal is not None:
            signal_ids = self._comparisons.signal_purchase_ids()
            criteria = (
                replace(criteria, purchase_ids=signal_ids)
                if has_signal
                else replace(criteria, exclude_purchase_ids=signal_ids)
            )
        page = self._purchases.search(criteria)
        outcomes = self._comparisons.purchase_outcomes([stored.id for stored in page.items])
        return PurchaseListView(
            items=tuple(_summary(stored, outcomes.get(stored.id)) for stored in page.items),
            total=page.total,
            page=page.page,
            page_size=page.page_size,
        )

    def get_purchase(self, purchase_id: uuid.UUID) -> PurchaseDetailView | None:
        stored = self._purchases.get(purchase_id)
        if stored is None:
            return None
        purchase = stored.purchase
        outcome = self._comparisons.purchase_outcomes([stored.id]).get(stored.id)
        results = self._comparisons.item_results(stored.id)
        return PurchaseDetailView(
            summary=_summary(stored, outcome),
            proceso_de_compra=purchase.proceso_de_compra,
            entity_municipality=purchase.entity_municipality,
            supplier_nit=purchase.supplier_nit,
            supplier_is_natural_person=purchase.supplier_is_natural_person,
            source_url=purchase.source_url,
            items=tuple(_item_view(item, results.get(item.line_number)) for item in purchase.items),
            data_cutoff_at=self._purchases.latest_cutoff(),
        )

    def filter_options(self) -> PurchaseFilterOptions:
        return self._purchases.filter_options()


def build_exploration_service(session_factory: sessionmaker[Session]) -> ExplorationService:
    return ExplorationService(
        build_purchase_query_service(session_factory),
        build_comparison_query_service(session_factory),
    )
