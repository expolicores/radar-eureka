import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from .background import ManualCycleStartError
from .repositories import CycleSchemaPendingError

router = APIRouter(prefix="/api/operations", tags=["Operations"])


class ExecutionConfiguration(BaseModel):
    start_date: date | None
    before_date: date
    before_exclusive: bool
    timezone: str
    regions: list[str]
    max_processes: int


class OperationalStatus(BaseModel):
    execution_config: ExecutionConfiguration
    db_connected: bool
    schema_ready: bool
    latest: dict[str, Any] | None
    latest_success: dict[str, Any] | None
    latest_alert: Any = None
    automation_enabled: bool
    notification_mode: str
    notification_enabled: bool
    scheduler: dict[str, Any]
    next_theoretical: str
    ocr: dict[str, Any]
    diagnostic: str | None = None
    active_cycle: dict[str, Any] | None = None


class ManualCycleAccepted(BaseModel):
    cycle_id: uuid.UUID
    status: str
    started_at: str
    reason: str | None = None


class ManualCycleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


@router.post("/cycles/manual", response_model=ManualCycleAccepted, status_code=202)
def manual(request: Request, command: ManualCycleRequest) -> Any:
    try:
        result = request.app.state.manual_cycle_runner.start()
    except ManualCycleStartError:
        return JSONResponse(
            status_code=503,
            media_type="application/problem+json",
            content={
                "code": "manual_start_failed",
                "stage": "preflight",
                "title": "No se pudo iniciar la corrida",
                "status": 503,
                "detail": "No se pudo iniciar/persistir la corrida. "
                "Revisar DB y configuración; no se confirmó inicio de Radar.",
            },
        )
    if result["status"] == "skipped":
        active = request.app.state.operations_queries.repository.active()
        result["active_cycle_id"] = active["id"] if active else None
        return JSONResponse(status_code=409, content=result)
    return result


@router.get("/status", response_model=OperationalStatus)
def status(request: Request) -> Any:
    return request.app.state.operations_queries.status()


@router.get("/cycles", response_model=list[dict[str, Any]])
def cycles(request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 25) -> Any:
    repository = request.app.state.operations_queries.repository
    try:
        repository.ready()
        return repository.listing(limit)
    except CycleSchemaPendingError as error:
        raise HTTPException(503, str(error)) from None


@router.get("/cycles/{identifier}", response_model=dict[str, Any])
def detail(request: Request, identifier: uuid.UUID) -> Any:
    repository = request.app.state.operations_queries.repository
    try:
        repository.ready()
        result = dict(repository.detail(identifier))
        active = repository.active() if result["status"] == "running" else None
        result["coordinator_active"] = bool(active and active["id"] == result["id"])
        return result
    except CycleSchemaPendingError as error:
        raise HTTPException(503, str(error)) from None
    except LookupError as error:
        raise HTTPException(404, str(error)) from None
