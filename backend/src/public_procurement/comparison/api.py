"""API de señales que merecen revisión: solo entrada y salida; la lógica vive en `services.py`.

Una señal no es una conclusión: los textos de la API nunca usan términos acusatorios (FR-064).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel

from public_procurement.market.services import AcquisitionMethod, Store

from .services import (
    ComparableView,
    ConfidenceLevel,
    MarketObservationView,
    MarketStatus,
    PenaltyCode,
    PurchaseSource,
    SignalDetail,
    SignalFilters,
    SignalQueryService,
    SignalRow,
    SignalSort,
    ThresholdRule,
    VatBasis,
)

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

router = APIRouter(prefix="/api/v1/signals", tags=["Señales que merecen revisión"])


def get_signal_service(request: Request) -> SignalQueryService:
    """La raíz de composición (`create_app`) deja el servicio en `app.state`."""
    service: SignalQueryService = request.app.state.signal_service
    return service


ServiceDependency = Annotated[SignalQueryService, Depends(get_signal_service)]


class Signal(BaseModel):
    code: str
    purchase_id: uuid.UUID
    line_number: int
    purchase_reference: str
    source: PurchaseSource
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


class SignalList(BaseModel):
    items: list[Signal]
    total: int
    page: int
    page_size: int


class SignalSummaryResponse(BaseModel):
    tv_purchases: int
    tv_purchases_by_source: dict[str, int]
    signals: int
    signals_by_confidence: dict[ConfidenceLevel, int]
    incomplete_comparisons: int
    without_source_information: int
    config_version_id: str | None
    data_cutoff_at: datetime | None


def _signal(row: SignalRow) -> Signal:
    return Signal.model_validate(row, from_attributes=True)


@router.get("", response_model=SignalList, summary="Lista priorizada de señales vigentes")
def list_signals(
    service: ServiceDependency,
    q: Annotated[
        str | None, Query(max_length=200, description="Entidad, proveedor, NIT, ítem o código")
    ] = None,
    department: Annotated[str | None, Query(max_length=64)] = None,
    source: PurchaseSource | None = None,
    confidence: ConfidenceLevel | None = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    sort: SignalSort = SignalSort.PRIORITY,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> SignalList:
    filters = SignalFilters(
        text=q,
        department=department,
        source=source.value if source else None,
        confidence=confidence,
        year=year,
    )
    result = service.list_signals(filters, sort, page, page_size)
    return SignalList(
        items=[_signal(row) for row in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/summary", response_model=SignalSummaryResponse, summary="Indicadores de las señales")
def signal_summary(service: ServiceDependency) -> SignalSummaryResponse:
    summary = service.summary()
    return SignalSummaryResponse(
        tv_purchases=summary.tv_purchases,
        tv_purchases_by_source=summary.tv_purchases_by_source,
        signals=summary.signals,
        signals_by_confidence=summary.signals_by_confidence,
        incomplete_comparisons=summary.incomplete_comparisons,
        without_source_information=summary.without_source_information,
        config_version_id=summary.config_version_id,
        data_cutoff_at=summary.data_cutoff_at,
    )


class Comparable(BaseModel):
    purchase_id: uuid.UUID
    source: PurchaseSource
    reference: str
    entity_name: str
    signed_on: date
    unit_price_cop: int
    same_model: bool


class MarketObservation(BaseModel):
    store: Store
    product_description: str
    effective_price_cop: int
    list_price_cop: int | None
    observed_on: date
    method: AcquisitionMethod


class ConfidencePenalty(BaseModel):
    code: PenaltyCode
    label: str
    points: int


class SignalDetailResponse(BaseModel):
    signal: Signal
    modality: str
    vat_basis: VatBasis
    config_version_id: str
    threshold_rule: ThresholdRule
    window_months: int
    q1_cop: int
    q3_cop: int
    threshold_cop: int
    comparables: list[Comparable]
    market_status: MarketStatus
    market_reference_cop: int | None
    market_deviation_pct: Decimal | None
    market_observations: list[MarketObservation]
    penalties: list[ConfidencePenalty]
    data_cutoff_at: datetime | None


def _comparable(view: ComparableView) -> Comparable:
    return Comparable.model_validate(view, from_attributes=True)


def _observation(view: MarketObservationView) -> MarketObservation:
    return MarketObservation.model_validate(view, from_attributes=True)


def _detail(detail: SignalDetail) -> SignalDetailResponse:
    return SignalDetailResponse(
        signal=_signal(detail.signal),
        modality=detail.modality,
        vat_basis=detail.vat_basis,
        config_version_id=detail.config_version_id,
        threshold_rule=detail.threshold_rule,
        window_months=detail.window_months,
        q1_cop=detail.q1_cop,
        q3_cop=detail.q3_cop,
        threshold_cop=detail.threshold_cop,
        comparables=[_comparable(c) for c in detail.comparables],
        market_status=detail.market_status,
        market_reference_cop=detail.market_reference_cop,
        market_deviation_pct=detail.market_deviation_pct,
        market_observations=[_observation(o) for o in detail.market_observations],
        penalties=[
            ConfidencePenalty(code=p.code, label=p.label, points=p.points) for p in detail.penalties
        ],
        data_cutoff_at=detail.data_cutoff_at,
    )


@router.get(
    "/{code}",
    response_model=SignalDetailResponse,
    summary="Detalle reproducible de una señal",
    responses={404: {"description": "Señal no encontrada"}},
)
def get_signal(
    code: Annotated[str, Path(max_length=32, pattern=r"^SG-\d{4}-[0-9A-Z-]+$")],
    service: ServiceDependency,
) -> SignalDetailResponse:
    detail = service.get_signal(code)
    if detail is None:
        raise HTTPException(status_code=404, detail="Señal no encontrada")
    return _detail(detail)
