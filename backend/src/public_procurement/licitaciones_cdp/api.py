"""Manual operational endpoints; clients cannot alter source policies."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/eureka/licitaciones-cdp", tags=["Licitaciones.info (CDP)"])


class CdpRunResponse(BaseModel):
    id: uuid.UUID
    source: str = "licitaciones_info_cdp"
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)


class CdpRunsResponse(BaseModel):
    items: list[CdpRunResponse]
    total: int
    page: int
    page_size: int


@router.post("/runs", status_code=202)
def start_run(request: Request) -> dict[str, Any]:
    try:
        return dict(request.app.state.manual_cdp_runner.start())
    except RuntimeError as error:
        raise HTTPException(409, str(error)) from error


@router.get("/runs", response_model=CdpRunsResponse)
def runs(
    request: Request, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)
) -> dict[str, Any]:
    return dict(request.app.state.cdp_queries.runs(page, page_size))


@router.get("/runs/{identifier}", response_model=CdpRunResponse)
def get_run(identifier: uuid.UUID, request: Request) -> dict[str, Any]:
    try:
        return dict(request.app.state.cdp_queries.get_run(identifier))
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
