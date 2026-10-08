"""Middleware que resuelve los identificadores de correlación y registra cada solicitud."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from public_procurement.shared.correlation import (
    CORRELATION_HEADER,
    REQUEST_HEADER,
    correlation_id_var,
    request_id_var,
    resolve_identifier,
)
from public_procurement.shared.logging import log_event

from .errors import handle_unexpected_error

logger = logging.getLogger("public_procurement.entrypoints.api.middleware")


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = resolve_identifier(request.headers.get(CORRELATION_HEADER))
        request_id = resolve_identifier(request.headers.get(REQUEST_HEADER))
        correlation_token = correlation_id_var.set(correlation_id)
        request_token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            try:
                response = await call_next(request)
            except Exception as exc:
                # Las excepciones no controladas llegan aquí antes que al handler de la app;
                # se responden aquí para conservar las cabeceras de correlación.
                response = await handle_unexpected_error(request, exc)
            response.headers[CORRELATION_HEADER] = correlation_id
            response.headers[REQUEST_HEADER] = request_id
            log_event(
                logger,
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            return response
        finally:
            correlation_id_var.reset(correlation_token)
            request_id_var.reset(request_token)
