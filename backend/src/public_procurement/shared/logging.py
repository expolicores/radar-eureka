"""Logging estructurado en JSON con `module`, `event`, `correlation_id` y `request_id`."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from .config import LogLevel
from .correlation import correlation_id_var, request_id_var

_FIELDS_ATTRIBUTE = "structured_fields"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "event": record.getMessage(),
            "correlation_id": correlation_id_var.get(),
            "request_id": request_id_var.get(),
        }
        entry.update(getattr(record, _FIELDS_ATTRIBUTE, {}))
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


def configure_logging(level: LogLevel) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.value)


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    exc_info: BaseException | None = None,
    **fields: Any,
) -> None:
    """Registra un evento con nombre estable; `fields` nunca debe llevar correos ni datos L3."""
    logger.log(level, event, exc_info=exc_info, extra={_FIELDS_ATTRIBUTE: fields})
