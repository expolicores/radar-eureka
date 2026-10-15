import uuid
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from .domain.query import SearchQuery
from .services import SearchQueries

router = APIRouter(prefix="/api/search", tags=["Búsqueda transversal"])


class SearchPageResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    duration_ms: float
    ranking_version: str


def queries(request: Request) -> SearchQueries:
    return cast(SearchQueries, request.app.state.search_queries)


@router.get("", response_model=SearchPageResponse)
def search(
    query: Annotated[SearchQuery, Query()], service: Annotated[SearchQueries, Depends(queries)]
) -> Any:
    return service.search(query)


@router.get("/processes/{process_id}/evidence", response_model=list[dict[str, Any]])
def evidence(
    process_id: uuid.UUID,
    service: Annotated[SearchQueries, Depends(queries)],
    canonical_fact_id: uuid.UUID | None = None,
    fragment_id: uuid.UUID | None = None,
) -> Any:
    if (canonical_fact_id is None) == (fragment_id is None):
        raise HTTPException(422, "Indica canonical_fact_id o fragment_id, exclusivamente.")
    result = service.evidence(process_id, canonical_fact_id, fragment_id)
    if not result:
        raise HTTPException(404, "Evidencia vigente no encontrada para este proceso.")
    return result
