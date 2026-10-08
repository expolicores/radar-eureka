"""`GET /healthz`: salud y disponibilidad del servicio, incluida la conexión a PostgreSQL."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import Engine

from public_procurement.shared.database import DatabaseStatus, check_database
from public_procurement.shared.problem_details import ProblemDetails

from .dependencies import get_engine
from .errors import problem_response

router = APIRouter()

DATABASE_UNAVAILABLE = ProblemDetails(
    title="Servicio no disponible",
    status=503,
    detail="No fue posible verificar la conexión con la base de datos.",
)


class HealthStatus(BaseModel):
    status: str
    database: DatabaseStatus


@router.get(
    "/healthz",
    response_model=HealthStatus,
    responses={503: {"model": ProblemDetails, "description": "Base de datos no disponible"}},
)
def healthz(engine: Annotated[Engine, Depends(get_engine)]) -> HealthStatus | JSONResponse:
    if check_database(engine) is DatabaseStatus.UNAVAILABLE:
        return problem_response(DATABASE_UNAVAILABLE)
    return HealthStatus(status="ok", database=DatabaseStatus.OK)
