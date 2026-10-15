from collections.abc import Iterable
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from .domain.message import DeliveryReceipt


class EmailSender(Protocol):
    provider: str
    scope: str
    idempotency_seconds: int | None

    def send(self, payload: dict[str, Any], key: str) -> DeliveryReceipt: ...


class AlertSource(Protocol):
    def alerts(
        self, alert_id: UUID | None, window: tuple[datetime, datetime] | None
    ) -> Iterable[dict[str, Any]]: ...
