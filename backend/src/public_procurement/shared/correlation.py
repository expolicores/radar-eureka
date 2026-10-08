"""Identificadores de correlación y de solicitud, propagados por contexto a logs y respuestas."""

import re
import uuid
from contextvars import ContextVar

CORRELATION_HEADER = "X-Correlation-ID"
REQUEST_HEADER = "X-Request-ID"

# Valor aceptado desde el cliente: corto y sin caracteres que permitan inyectar líneas en los logs.
_VALID_IDENTIFIER = re.compile(r"[A-Za-z0-9._:-]{1,128}")

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def resolve_identifier(header_value: str | None) -> str:
    """Reutiliza el valor recibido si es válido; si no llega o no es válido, genera uno nuevo."""
    if header_value is not None and _VALID_IDENTIFIER.fullmatch(header_value):
        return header_value
    return str(uuid.uuid4())
