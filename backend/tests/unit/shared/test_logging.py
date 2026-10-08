import json
import logging
from datetime import datetime

from public_procurement.shared.correlation import correlation_id_var, request_id_var
from public_procurement.shared.logging import JsonFormatter, log_event

from ...doubles import ListLogHandler


def test_log_event_writes_json_line_with_correlation_fields_when_context_is_set() -> None:
    # Arrange
    handler = ListLogHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("public_procurement.tests.logging")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    correlation_token = correlation_id_var.set("corr-1")
    request_token = request_id_var.set("req-1")
    # Act
    try:
        log_event(logger, "sample_event", duration_ms=12.5)
    finally:
        correlation_id_var.reset(correlation_token)
        request_id_var.reset(request_token)
        logger.removeHandler(handler)
    # Assert
    entry = json.loads(handler.lines[0])
    assert entry["module"] == "public_procurement.tests.logging"
    assert entry["event"] == "sample_event"
    assert entry["correlation_id"] == "corr-1"
    assert entry["request_id"] == "req-1"
    assert entry["level"] == "INFO"
    assert entry["duration_ms"] == 12.5
    assert datetime.fromisoformat(entry["timestamp"]).utcoffset() is not None
