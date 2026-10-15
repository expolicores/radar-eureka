import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.eureka.services import notification_alerts


class PersistedAlertSource:
    def __init__(self, sessions: sessionmaker[Session]):
        self.sessions = sessions

    def alerts(
        self, alert_id: uuid.UUID | None, window: tuple[datetime, datetime] | None
    ) -> Iterable[dict[str, Any]]:
        return notification_alerts(self.sessions, alert_id, window)
