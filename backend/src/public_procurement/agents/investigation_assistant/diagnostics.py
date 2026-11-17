"""Allowlisted Foundry diagnostics; no payloads, headers or credential traces."""

import json
import logging
import os
import re
from typing import Any

from dotenv import dotenv_values

logger = logging.getLogger(__name__)


def emit(event: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))


def sanitized_message(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    # Redact configured secrets even when a provider echoes one without a label.
    for key, secret in {**dotenv_values(".env"), **os.environ}.items():
        if secret and any(
            word in key.upper()
            for word in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CONNECTION", "ENDPOINT")
        ):
            value = value.replace(str(secret), "[REDACTED]")
    value = re.sub(r"https?://[^\s\"'<>]+", "[URL]", value, flags=re.I)
    value = re.sub(r"(?i)Bearer\s+[^\s\"',;]+", "Bearer [REDACTED]", value)
    value = re.sub(
        r"(?i)([\"']?(?:[\w-]*(?:key|token|secret|password)|authorization|"
        r"connection[_ -]?string)[\"']?\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
        r"\1[REDACTED]",
        value,
    )
    value = re.sub(r"\beyJ[\w-]+\.[\w-]+\.[\w-]+\b", "[REDACTED]", value)
    value = re.sub(r"(?:[A-Za-z]:[\\/]|/home/|/Users/)[^\s\"']+", "[PATH]", value)
    return " ".join(value.split())[:1200]


def failure(stage: str, error: Exception) -> dict[str, Any]:
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        body = body.get("error", body)
    body = body if isinstance(body, dict) else {}
    code = body.get("code") or getattr(error, "code", None)
    param = body.get("param") or getattr(error, "param", None)
    # A credential exception can contain the entire CLI traceback and token cache
    # details. Do not inspect str(error) or serialize arbitrary SDK objects.
    kind = type(error).__name__
    message = sanitized_message(body.get("message"))
    if not message:
        message = {
            "ClientAuthenticationError": "DefaultAzureCredential no obtuvo una credencial válida.",
            "CredentialUnavailableError": "No hay credencial Azure disponible.",
            "APIConnectionError": "No se pudo conectar con Foundry.",
            "APITimeoutError": "La solicitud a Foundry excedió el tiempo permitido.",
            "ValidationError": "Configuración Foundry ausente o inválida.",
        }.get(kind, "La etapa falló; se omitieron detalles no estructurados por seguridad.")
    status = getattr(error, "status_code", None)
    diagnostic = {
        "stage": stage,
        "exception_class": kind,
        "http_status": status if isinstance(status, int) else None,
        "error_code": code
        if isinstance(code, str) and re.fullmatch(r"[\w.-]{1,100}", code)
        else None,
        "parameter": param
        if isinstance(param, str) and re.fullmatch(r"[\w.\[\]-]{1,100}", param)
        else None,
        "message": message,
    }
    emit("foundry_error", **diagnostic)
    return diagnostic


def configuration(config: Any) -> dict[str, bool]:
    return {
        "project_endpoint_present": bool(config.azure_foundry_project_endpoint),
        "model_deployment_present": bool(config.eureka_foundry_model_deployment),
        "timeout_configured": bool(config.eureka_foundry_timeout_seconds),
        "remote_agent_required": False,
        "client_secret_present": bool(os.getenv("AZURE_CLIENT_SECRET")),
        "tenant_id_present": bool(os.getenv("AZURE_TENANT_ID")),
        "client_id_present": bool(os.getenv("AZURE_CLIENT_ID")),
    }
