"""Errores de la API en formato *problem details* (RFC 9457), con textos en español."""

from pydantic import BaseModel, ConfigDict

PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"


class ProblemDetails(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str = "about:blank"
    title: str
    status: int
    detail: str
