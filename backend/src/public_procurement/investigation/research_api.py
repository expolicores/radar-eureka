"""Local research reads and bounded manual investigation runs."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from .market_runs import ManualMarketRunner, MarketRun, MarketRunRequest
from .run_background import ManualResearchRunner, ResearchBusyError
from .run_contracts import MAX_RESEARCH_DAYS, ResearchRun, ResearchRunRequest

router = APIRouter(prefix="/api/v1/investigation", tags=["Investigación SECOP"])


@router.get("/research")
def research_report(request: Request, run_id: UUID | None = None) -> dict[str, Any]:
    try:
        if run_id is not None:
            return _runner(request).result(run_id)
        report: dict[str, Any] = request.app.state.research_reports.read()
        return report
    except FileNotFoundError:
        raise HTTPException(404, "Resultado de corrida no disponible.") from None
    except (ValueError, OSError):
        raise HTTPException(503, "No fue posible leer el informe investigativo local.") from None


def _runner(request: Request) -> ManualResearchRunner:
    runner: ManualResearchRunner | None = getattr(request.app.state, "manual_research_runner", None)
    if runner is None:
        raise HTTPException(503, "Ejecución investigativa no disponible.")
    return runner


@router.get("/runs/policy")
def research_run_policy() -> dict[str, Any]:
    return {"max_window_days": MAX_RESEARCH_DAYS, "inclusive": True, "timezone": "America/Bogota"}


@router.get("/runs/active", response_model=ResearchRun | None)
def active_research_run(request: Request) -> ResearchRun | None:
    try:
        return _runner(request).active()
    except (ValueError, OSError):
        raise HTTPException(503, "No fue posible leer la corrida activa.") from None


@router.post("/runs", response_model=ResearchRun, status_code=202)
def start_research_run(body: ResearchRunRequest, request: Request) -> ResearchRun:
    try:
        return _runner(request).start(body)
    except ResearchBusyError:
        raise HTTPException(
            409, "Ya hay una corrida activa o el backend está reiniciándose."
        ) from None
    except (OSError, RuntimeError):
        raise HTTPException(
            503, "No fue posible registrar la corrida. Consulte la corrida activa."
        ) from None


@router.get("/runs/{run_id}", response_model=ResearchRun)
def get_research_run(run_id: UUID, request: Request) -> ResearchRun:
    try:
        return _runner(request).get(run_id)
    except FileNotFoundError:
        raise HTTPException(404, "Corrida no encontrada.") from None
    except (ValueError, OSError):
        raise HTTPException(503, "No fue posible leer el estado de la corrida.") from None


@router.get("/private-market")
def private_market_report(request: Request, run_id: UUID | None = None) -> dict[str, Any]:
    from .market_benchmark.presentation import present_market_reports
    from .market_benchmark.service import MarketReportStore

    try:
        if run_id is not None:
            return _market_runner(request).result(run_id)
        return present_market_reports(
            MarketReportStore(request.app.state.research_reports.path.parent).read()
        )
    except FileNotFoundError:
        raise HTTPException(404, "Resultado privado no disponible.") from None
    except (ValueError, OSError):
        raise HTTPException(503, "No fue posible leer el benchmark privado local.") from None


def _market_runner(request: Request) -> ManualMarketRunner:
    runner: ManualMarketRunner | None = getattr(request.app.state, "manual_market_runner", None)
    if runner is None:
        raise HTTPException(503, "Ejecución de mercado privado no disponible.")
    return runner


@router.get("/market-runs/{run_id}/research")
def market_research_result(run_id: UUID, request: Request) -> dict[str, Any]:
    try:
        return _market_runner(request).research_result(run_id)
    except FileNotFoundError:
        raise HTTPException(404, "Resultado de corrida privada no disponible.") from None
    except (ValueError, OSError):
        raise HTTPException(
            503, "No fue posible leer la evidencia pública de esta corrida."
        ) from None


@router.get("/market-runs/active", response_model=MarketRun | None)
def active_market_run(request: Request) -> MarketRun | None:
    try:
        return _market_runner(request).active()
    except (ValueError, OSError):
        raise HTTPException(503, "No fue posible leer la corrida privada activa.") from None


@router.post("/market-runs", response_model=MarketRun, status_code=202)
def start_market_run(body: MarketRunRequest, request: Request) -> MarketRun:
    try:
        return _market_runner(request).start(body)
    except LookupError:
        raise HTTPException(
            404, "El producto no tiene evidencia pública formalizada disponible."
        ) from None
    except ResearchBusyError:
        raise HTTPException(409, "Ya existe una corrida de mercado privado activa.") from None
    except (ValueError, OSError, RuntimeError):
        raise HTTPException(
            503, "No se pudo confirmar el inicio; consulte la corrida activa."
        ) from None


@router.get("/market-runs/{run_id}", response_model=MarketRun)
def get_market_run(run_id: UUID, request: Request) -> MarketRun:
    try:
        return _market_runner(request).get(run_id)
    except FileNotFoundError:
        raise HTTPException(404, "Corrida privada no encontrada.") from None
    except (ValueError, OSError):
        raise HTTPException(503, "No fue posible consultar el estado privado.") from None
