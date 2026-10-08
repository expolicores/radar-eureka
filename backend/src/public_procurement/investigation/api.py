"""API de casos de investigación (privados del dueño): solo entrada y salida."""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from .services import (
    CaseDetail,
    CaseItemKind,
    CaseNotFoundError,
    CaseSummary,
    InvalidCaseDataError,
    InvestigationError,
    InvestigationService,
    ReferenceNotFoundError,
    SaveResult,
)

router = APIRouter(prefix="/api/v1/cases", tags=["Casos de investigación"])


def get_investigation_service(request: Request) -> InvestigationService:
    service: InvestigationService = request.app.state.investigation_service
    return service


def get_owner_id(request: Request) -> uuid.UUID:
    """Usuario actual; lo resuelve la raíz de composición (usuario demo hasta `identity`)."""
    provider: Callable[[Request], uuid.UUID] = request.app.state.current_user_provider
    return provider(request)


ServiceDependency = Annotated[InvestigationService, Depends(get_investigation_service)]
OwnerDependency = Annotated[uuid.UUID, Depends(get_owner_id)]


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class CaseItemCreate(BaseModel):
    kind: CaseItemKind
    reference: str = Field(min_length=1, max_length=64)


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5_000)


class CaseSummaryResponse(BaseModel):
    id: uuid.UUID
    title: str
    item_count: int
    note_count: int
    created_at: datetime
    last_activity_at: datetime


class CaseItemResponse(BaseModel):
    kind: CaseItemKind
    reference: str
    snapshot: dict[str, Any]
    saved_at: datetime


class NoteResponse(BaseModel):
    body: str
    created_at: datetime


class CaseDetailResponse(CaseSummaryResponse):
    items: list[CaseItemResponse]
    notes: list[NoteResponse]


def _summary(summary: CaseSummary) -> CaseSummaryResponse:
    return CaseSummaryResponse.model_validate(summary, from_attributes=True)


def _detail(detail: CaseDetail) -> CaseDetailResponse:
    return CaseDetailResponse(
        **_summary(detail.summary).model_dump(),
        items=[CaseItemResponse.model_validate(i, from_attributes=True) for i in detail.items],
        notes=[NoteResponse.model_validate(n, from_attributes=True) for n in detail.notes],
    )


def _http_error(error: InvestigationError) -> HTTPException:
    if isinstance(error, CaseNotFoundError):
        return HTTPException(status_code=404, detail="Caso no encontrado")
    if isinstance(error, ReferenceNotFoundError):
        return HTTPException(status_code=404, detail="La señal o la compra no existe")
    if isinstance(error, InvalidCaseDataError):
        return HTTPException(status_code=400, detail=f"El campo «{error.field}» no es válido.")
    return HTTPException(status_code=400, detail="Solicitud inválida")


@router.get("", response_model=list[CaseSummaryResponse], summary="Mis casos")
def list_cases(service: ServiceDependency, owner_id: OwnerDependency) -> list[CaseSummaryResponse]:
    return [_summary(summary) for summary in service.list_cases(owner_id)]


@router.post("", response_model=CaseDetailResponse, status_code=201, summary="Crear un caso")
def create_case(
    body: CaseCreate, service: ServiceDependency, owner_id: OwnerDependency
) -> CaseDetailResponse:
    try:
        return _detail(service.create_case(owner_id, body.title))
    except InvestigationError as error:
        raise _http_error(error) from error


@router.get("/{case_id}", response_model=CaseDetailResponse, summary="Abrir un caso")
def get_case(
    case_id: uuid.UUID, service: ServiceDependency, owner_id: OwnerDependency
) -> CaseDetailResponse:
    try:
        return _detail(service.get_case(owner_id, case_id))
    except InvestigationError as error:
        raise _http_error(error) from error


@router.post(
    "/{case_id}/items",
    response_model=CaseDetailResponse,
    status_code=201,
    summary="Guardar una señal o una compra como instantánea",
)
def save_item(
    case_id: uuid.UUID,
    body: CaseItemCreate,
    service: ServiceDependency,
    owner_id: OwnerDependency,
) -> CaseDetailResponse:
    try:
        result, detail = service.save_item(owner_id, case_id, body.kind, body.reference)
    except InvestigationError as error:
        raise _http_error(error) from error
    if result is SaveResult.ALREADY_SAVED:
        # Regla de negocio (sin duplicados en un caso): 422, no conflicto de versión.
        raise HTTPException(status_code=422, detail="Ese elemento ya está guardado en el caso")
    return _detail(detail)


@router.post(
    "/{case_id}/notes",
    response_model=CaseDetailResponse,
    status_code=201,
    summary="Agregar una nota",
)
def add_note(
    case_id: uuid.UUID,
    body: NoteCreate,
    service: ServiceDependency,
    owner_id: OwnerDependency,
) -> CaseDetailResponse:
    try:
        return _detail(service.add_note(owner_id, case_id, body.body))
    except InvestigationError as error:
        raise _http_error(error) from error
