"""Respuestas de error en *problem details* y manejo de excepciones no controladas."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from public_procurement.shared.logging import log_event
from public_procurement.shared.problem_details import PROBLEM_JSON_MEDIA_TYPE, ProblemDetails

logger = logging.getLogger("public_procurement.entrypoints.api.errors")


def problem_response(problem: ProblemDetails) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(),
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    log_event(
        logger,
        "unhandled_error",
        logging.ERROR,
        exc_info=exc,
        error_type=type(exc).__name__,
        path=request.url.path,
    )
    return problem_response(
        ProblemDetails(
            title="Error interno",
            status=500,
            detail="Ocurrió un error inesperado. Intenta de nuevo más tarde.",
        )
    )


STATUS_TITLES = {
    400: "Solicitud inválida",
    401: "No autenticado",
    403: "Acceso denegado",
    404: "No encontrado",
    405: "Método no permitido",
    409: "Conflicto",
    422: "Regla de negocio no cumplida",
    503: "Servicio no disponible",
}


async def handle_http_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        return await handle_unexpected_error(request, exc)
    title = STATUS_TITLES.get(exc.status_code, "Error")
    detail = exc.detail if isinstance(exc.detail, str) else title
    return problem_response(
        ProblemDetails(
            title=title,
            status=exc.status_code,
            detail=detail,
        )
    )


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await handle_unexpected_error(request, exc)
    locations = [error["loc"] for error in exc.errors() if error.get("loc")]
    names = sorted({str(location[-1]) for location in locations})
    # Los datos del cuerpo JSON son «campos»; los de la URL, «parámetros».
    noun = "campo" if locations and all(loc[0] == "body" for loc in locations) else "parámetro"
    detail = (
        f"El {noun} «{names[0]}» no es válido."
        if len(names) == 1
        else f"Los {noun}s «" + "», «".join(names) + "» no son válidos."
    )
    return problem_response(ProblemDetails(title="Solicitud inválida", status=400, detail=detail))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
