"""API de exploración de compras: solo entrada y salida; la lógica vive en `services.py`."""

import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from public_procurement.comparison.services import Outcome
from public_procurement.ingestion.services import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    ItemClassification,
    PurchaseSearchCriteria,
    PurchaseSort,
    Source,
    UnitPriceStatus,
    ValueRange,
    VatBasis,
)

from .domain.analysis import AnalysisStatus
from .services import ExplorationService, PurchaseDetailView, PurchaseSummaryView

router = APIRouter(prefix="/api/v1/purchases", tags=["Exploración de compras"])


def get_exploration_service(request: Request) -> ExplorationService:
    """La raíz de composición (`create_app`) deja el servicio en `app.state`."""
    service: ExplorationService = request.app.state.exploration_service
    return service


ServiceDependency = Annotated[ExplorationService, Depends(get_exploration_service)]


class PurchaseSummary(BaseModel):
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


class PurchaseList(BaseModel):
    items: list[PurchaseSummary]
    total: int
    page: int
    page_size: int


class PurchaseItem(BaseModel):
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


class PurchaseDetail(PurchaseSummary):
    proceso_de_compra: str | None
    entity_municipality: str | None
    supplier_nit: str | None
    supplier_is_natural_person: bool
    source_url: str | None
    items: list[PurchaseItem]
    data_cutoff_at: datetime | None


class FilterOptions(BaseModel):
    sources: list[Source]
    modalities: list[str]
    departments: list[str]
    data_cutoff_at: datetime | None


def _summary(view: PurchaseSummaryView) -> PurchaseSummary:
    return PurchaseSummary.model_validate(view, from_attributes=True)


def _detail(view: PurchaseDetailView) -> PurchaseDetail:
    return PurchaseDetail(
        **_summary(view.summary).model_dump(),
        proceso_de_compra=view.proceso_de_compra,
        entity_municipality=view.entity_municipality,
        supplier_nit=view.supplier_nit,
        supplier_is_natural_person=view.supplier_is_natural_person,
        source_url=view.source_url,
        items=[PurchaseItem.model_validate(item, from_attributes=True) for item in view.items],
        data_cutoff_at=view.data_cutoff_at,
    )


@router.get("", response_model=PurchaseList, summary="Listar compras con búsqueda y filtros")
def list_purchases(
    service: ServiceDependency,
    q: Annotated[
        str | None, Query(max_length=200, description="Entidad, proveedor, NIT u objeto")
    ] = None,
    source: Source | None = None,
    modality: Annotated[str | None, Query(max_length=96)] = None,
    department: Annotated[str | None, Query(max_length=64)] = None,
    value_range: ValueRange | None = None,
    signed_from: date | None = None,
    signed_to: date | None = None,
    has_signal: Annotated[
        bool | None, Query(description="Con señal vigente (true) o sin ella")
    ] = None,
    sort: PurchaseSort = PurchaseSort.SIGNED_DESC,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> PurchaseList:
    criteria = PurchaseSearchCriteria(
        text=q,
        source=source,
        modality=modality,
        department=department,
        value_range=value_range,
        signed_from=signed_from,
        signed_to=signed_to,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    view = service.list_purchases(criteria, has_signal)
    return PurchaseList(
        items=[_summary(item) for item in view.items],
        total=view.total,
        page=view.page,
        page_size=view.page_size,
    )


@router.get("/filters", response_model=FilterOptions, summary="Opciones de filtro y fecha de corte")
def filter_options(service: ServiceDependency) -> FilterOptions:
    options = service.filter_options()
    return FilterOptions(
        sources=list(options.sources),
        modalities=list(options.modalities),
        departments=list(options.departments),
        data_cutoff_at=options.data_cutoff_at,
    )


@router.get(
    "/{purchase_id}",
    response_model=PurchaseDetail,
    summary="Ficha de una compra",
    responses={404: {"description": "Compra no encontrada"}},
)
def get_purchase(purchase_id: uuid.UUID, service: ServiceDependency) -> PurchaseDetail:
    view = service.get_purchase(purchase_id)
    if view is None:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return _detail(view)
