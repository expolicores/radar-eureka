"""Public-services-backed historical alert reads; no alert generation."""

import uuid
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session, sessionmaker

from .radar_repositories import AlertRecord, alert_json


def alerts(
    sessions: sessionmaker[Session],
    alert_id: uuid.UUID | None,
    window: tuple[datetime, datetime] | None,
) -> Iterator[dict[str, Any]]:
    cursor = None
    while True:
        with sessions() as session:
            statement = (
                select(AlertRecord).order_by(AlertRecord.created_at, AlertRecord.id).limit(250)
            )
            if alert_id:
                statement = statement.where(AlertRecord.id == alert_id)
            if window:
                statement = statement.where(
                    AlertRecord.created_at >= window[0], AlertRecord.created_at < window[1]
                )
            if cursor:
                statement = statement.where(tuple_(AlertRecord.created_at, AlertRecord.id) > cursor)
            rows = list(session.scalars(statement))
            batch = [alert_json(row) for row in rows]
            if rows:
                cursor = (rows[-1].created_at, rows[-1].id)
        yield from batch
        if len(batch) < 250:
            return
