"""Timestamp diagnostic events without changing query/filter behavior."""

from datetime import UTC, datetime


def timed_warning(value):
    return {"generated_at": datetime.now(UTC).isoformat(), **value}
