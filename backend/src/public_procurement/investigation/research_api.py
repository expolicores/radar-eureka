"""Local research proof: reads a sanitized completed report; never runs ingestion."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/v1/investigation", tags=["Investigación SECOP"])


@router.get("/research")
def research_report(request: Request) -> dict[str, Any]:
    try:
        report: dict[str, Any] = request.app.state.research_reports.read()
        return report
    except (ValueError, OSError):
        raise HTTPException(503, "No fue posible leer el informe investigativo local.") from None
