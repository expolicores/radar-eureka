"""HTTP de solo lectura, compuesto sobre los mismos servicios de CLI."""

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from .services import EurekaHttpQueries

router = APIRouter(prefix="/api/eureka/opportunities", tags=["Eureka"])
radar_router = APIRouter(prefix="/api/eureka", tags=["Radar Eureka"])


def get_radar_queries(request: Request) -> Any:
    return request.app.state.radar_queries


RadarQueries = Annotated[Any, Depends(get_radar_queries)]


class SecopPresentation(BaseModel):
    secop_id: str
    reference: str | None = None
    description: str | None = None
    source_url: str | None = None


class EurekaAlertResponse(BaseModel):
    id: uuid.UUID
    opportunity_id: uuid.UUID
    run_id: uuid.UUID
    alert_type: str
    rule_version: str
    created_at: datetime
    priority: str
    review_required: bool
    reasons: list[dict[str, Any]]
    snapshot: dict[str, Any]
    process: SecopPresentation | None = None


class EurekaAlertsResponse(BaseModel):
    items: list[EurekaAlertResponse]
    total: int
    page: int
    page_size: int


class RadarRunResponse(BaseModel):
    id: uuid.UUID
    started_at: datetime
    finished_at: datetime | None
    status: str
    start_date: date
    before_date: date
    regions: list[str]
    rule_version: str
    config_hash: str
    processes_seen: int
    new_processes: int
    candidates: int
    enriched: int
    alerts_created: int
    skipped: int
    failures: int
    errors: list[dict[str, Any]]


class RadarRunsResponse(BaseModel):
    items: list[RadarRunResponse]
    total: int
    page: int
    page_size: int


class RadarRunDetailResponse(RadarRunResponse):
    config_snapshot: dict[str, Any]
    items: list[dict[str, Any]]


@radar_router.get("/alerts", response_model=EurekaAlertsResponse)
def alerts(
    service: RadarQueries,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Any:
    return service.alerts(page, page_size)


@radar_router.get("/alerts/{alert_id}", response_model=EurekaAlertResponse)
def alert(alert_id: uuid.UUID, service: RadarQueries) -> Any:
    try:
        return service.get_alert(alert_id)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


@radar_router.get("/radar-runs", response_model=RadarRunsResponse)
def radar_runs(
    service: RadarQueries,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Any:
    return service.runs(page, page_size)


@radar_router.get("/radar-runs/{run_id}", response_model=RadarRunDetailResponse)
def radar_run(run_id: uuid.UUID, service: RadarQueries) -> Any:
    try:
        return service.get_run(run_id)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


def get_eureka_queries(request: Request) -> EurekaHttpQueries:
    return request.app.state.eureka_queries  # type: ignore[no-any-return]


Service = Annotated[EurekaHttpQueries, Depends(get_eureka_queries)]


class EurekaSummaryResponse(SecopPresentation):
    opportunity_id: uuid.UUID
    process_id: uuid.UUID
    title: str | None
    entity: str | None
    department: str | None
    municipality: str | None
    budget: int | str | None
    category: list[str]
    score: int
    priority: str
    review_required: bool
    enrichment_status: str
    product_match: bool | None
    published_at: date | None


class EurekaListResponse(BaseModel):
    items: list[EurekaSummaryResponse]
    total: int
    page: int
    page_size: int


class EurekaDetailsResponse(BaseModel):
    process_id: uuid.UUID
    secop_id: str
    opportunity_id: uuid.UUID | None
    category: list[str]
    score: int | None
    priority: str | None
    scoring_rule_version: str | None
    review_required: bool
    enrichment_status: str
    commercial: dict[str, Any]
    execution: dict[str, Any]
    payment: dict[str, Any]
    requirements: dict[str, Any]
    quality: dict[str, Any]
    commercial_profile: dict[str, Any]
    evidence: dict[str, Any]


class EurekaDetailResponse(BaseModel):
    opportunity: EurekaSummaryResponse
    details: EurekaDetailsResponse


class EurekaEvidenceResponse(BaseModel):
    canonical_fact_id: uuid.UUID
    structured_fact_id: uuid.UUID
    document_version_id: uuid.UUID
    content_fragment_id: uuid.UUID | None
    evidence_text: str
    source_locator: dict[str, Any]
    confidence: str
    corroborated: bool
    rule_name: str
    rule_version: str


@router.get("", response_model=EurekaListResponse)
def opportunities(
    service: Service,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    priority: Literal["high", "medium", "low"] | None = None,
    department: str | None = None,
    category: str | None = None,
    review_required: bool | None = None,
) -> Any:
    return service.listing(page, page_size, priority, department, category, review_required)


@router.get("/{opportunity_id}", response_model=EurekaDetailResponse)
def detail(opportunity_id: uuid.UUID, service: Service) -> Any:
    try:
        return service.detail(opportunity_id)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


@router.get("/{opportunity_id}/evidence", response_model=list[EurekaEvidenceResponse])
def evidence(opportunity_id: uuid.UUID, canonical_fact_id: uuid.UUID, service: Service) -> Any:
    try:
        return service.evidence(opportunity_id, canonical_fact_id)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
