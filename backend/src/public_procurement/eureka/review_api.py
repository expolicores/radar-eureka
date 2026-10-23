"""Read existing evidence and save human assessments only."""

from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/eureka/revision", tags=["Merecen Revisión"])


class Assessment(BaseModel):
    manual_rating: Literal["high", "medium", "low", "discard"] | None = None
    manual_note: str = Field(default="", max_length=5000)


@router.get("")
def list_reviews(
    request: Request,
    q: str | None = Query(None, max_length=200),
    source: Literal["socrata", "licitaciones_info_cdp"] | None = None,
    validity: Literal["active", "open", "closed", "unknown", "all"] = "active",
    department: str | None = None,
    municipality: str | None = None,
    funnel_state: str | None = None,
    score_min: float | None = None,
    score_max: float | None = None,
    amount_min: float | None = Query(None, ge=0),
    amount_max: float | None = Query(None, ge=0),
    deadline_from: date | None = None,
    deadline_to: date | None = None,
    has_alert: bool | None = None,
    requires_manual_document_review: bool | None = None,
    include_excluded: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> dict[str, Any]:
    filters = {k: v for k, v in locals().items() if k != "request"}
    return dict(request.app.state.human_review_queries.list(filters))


@router.get("/{identity}")
def review_detail(identity: str, request: Request) -> dict[str, Any]:
    try:
        return dict(request.app.state.human_review_queries.get(identity))
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


@router.put("/{identity}")
def assess(identity: str, body: Assessment, request: Request) -> dict[str, Any]:
    try:
        return dict(
            request.app.state.human_review_queries.save(
                identity,
                body.manual_rating,
                body.manual_note,
                request.app.state.current_user_provider(request),
            )
        )
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
