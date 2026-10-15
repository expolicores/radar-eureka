"""Manual notification preparation/dispatch; never runs Radar or enrichment."""

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import time as daytime
from email.utils import parseaddr
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from public_procurement.shared.config import Settings
from public_procurement.shared.logging import log_event

from .adapters.alerts import PersistedAlertSource
from .adapters.file import DevEmailSender
from .adapters.resend import ResendEmailSender
from .domain.message import (
    STATUSES,
    DeliveryError,
    blocked_attempt,
    compose,
    identity,
    recipient,
    sort_alerts,
    utc,
)
from .ports import AlertSource, EmailSender
from .repositories import DispatcherBusyError as DispatcherBusyError
from .repositories import (
    NotificationAlertRecord,
    NotificationRecord,
    SqlNotificationRepository,
    record_json,
)

logger = logging.getLogger(__name__)


class NotificationSchemaPendingError(RuntimeError):
    pass


def ensure_schema(session: Session) -> None:
    if session.get_bind().dialect.name == "postgresql" and not session.scalar(
        text("SELECT to_regclass('notifications.notification')")
    ):
        raise NotificationSchemaPendingError(
            "Notificaciones pendientes de migración 0015_eureka_notifications."
        )


def base_url(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or any(ord(c) < 33 for c in value)
    ):
        raise ValueError("Base URL inválida: usa HTTP/HTTPS sin credenciales, query ni fragment.")
    return value.rstrip("/")


def digest_window(
    mode: str | None,
    day: date | None,
    now: datetime,
    start: date | None = None,
    before: date | None = None,
) -> tuple[datetime, datetime] | None:
    zone = ZoneInfo("America/Bogota")
    if mode is None:
        if day or start or before:
            raise ValueError("Las fechas requieren --digest.")
        return None
    if mode == "daily":
        if start or before:
            raise ValueError("daily utiliza --date.")
        day = day or (utc(now).astimezone(zone).date() - timedelta(days=1))
        first = datetime.combine(day, daytime.min, zone)
        return first.astimezone(UTC), (first + timedelta(days=1)).astimezone(UTC)
    if mode == "since-last":
        if day or start or before:
            raise ValueError("since-last no requiere fechas: busca alertas no asignadas.")
        return datetime(1970, 1, 1, tzinfo=UTC), utc(now)
    if mode == "window" and start and before and start < before and day is None:
        return datetime.combine(start, daytime.min, zone).astimezone(UTC), datetime.combine(
            before, daytime.min, zone
        ).astimezone(UTC)
    raise ValueError("Digest inválido: daily, since-last o window con fechas ordenadas.")


@dataclass(frozen=True)
class DispatchPolicy:
    enabled: bool = False
    base_url: str = ""
    sender: str = ""
    max_retries: int = 3
    retry_seconds: int = 60
    lease_seconds: int = 300
    idempotency_margin_seconds: int = 60
    max_messages: int = 100
    max_digest_alerts: int = 100


class NotificationDispatcher:
    def __init__(
        self,
        repository: SqlNotificationRepository,
        source: AlertSource,
        sender: EmailSender,
        policy: DispatchPolicy,
    ) -> None:
        self.repository, self.source, self.sender, self.policy = repository, source, sender, policy

    def run(
        self,
        recipients: list[str],
        *,
        alert_id: uuid.UUID | None = None,
        window: tuple[datetime, datetime] | None = None,
        digest: bool = False,
        retry: bool = False,
        dry_run: bool = False,
        allow_real_send: bool = False,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        at = utc(now or datetime.now(UTC))
        report: dict[str, Any] = {
            "dry_run": dry_run,
            "delivery_scope": self.sender.scope,
            "prepared": 0,
            "sent": 0,
            "captured": 0,
            "failed": 0,
            "retryable": 0,
            "skipped": 0,
            "recovered": [],
            "items": [],
            "preview": [],
            "disabled": not self.policy.enabled,
        }
        if not self.policy.enabled and not dry_run:
            return report
        if self.sender.scope == "real" and not dry_run and not allow_real_send:
            raise ValueError(
                "Envío real no autorizado; usa dry-run o file. No se prepararon notificaciones."
            )
        addresses = list(dict.fromkeys(recipient(value) for value in recipients))
        if not addresses:
            raise ValueError("Configura al menos un destinatario.")
        url = base_url(self.policy.base_url)
        if self.policy.sender:
            if any(ord(c) < 32 for c in self.policy.sender):
                raise ValueError("Remitente inválido: contiene controles de encabezado.")
            recipient(parseaddr(self.policy.sender)[1])
        if self.policy.lease_seconds <= 0:
            raise ValueError("El lease debe ser positivo.")
        alerts = list(self.source.alerts(alert_id, window))
        if alert_id and not alerts:
            raise LookupError("Alerta persistida no encontrada.")
        kind = "digest" if digest else "immediate"
        selection_ids = [uuid.UUID(str(a["id"])) for a in alerts] if digest else None
        if dry_run:
            self._prepare(alerts, addresses, url, kind, window, at, report, True)
            ready = self.repository.ready(
                self.sender.scope, addresses, at, retry, alert_id, selection_ids, digest
            )
            for r in self.repository.stale(
                self.sender.scope,
                at,
                self.policy.lease_seconds,
                addresses,
                alert_id,
                selection_ids,
                digest,
            ):
                unsafe = r["delivery_scope"] == "real" and (
                    r["provider_idempotency_until"] is None
                    or at + timedelta(seconds=self.policy.idempotency_margin_seconds)
                    >= utc(r["provider_idempotency_until"])
                )
                exhausted = r["attempt_count"] >= self.policy.max_retries + 1
                changed = r["provider"] != self.sender.provider
                status = "failed" if unsafe or exhausted or changed else "retryable"
                report["recovered"].append({"id": str(r["id"]), "would_status": status})
                if retry and status == "retryable":
                    r["delivery_ambiguous"] = self.sender.scope == "real"
                    ready.append(r)
            report["preview"].extend(
                {
                    "existing_notification_id": str(r["id"]),
                    "payload": r["payload_snapshot"],
                    "idempotency_key": r["idempotency_key"],
                    "created_at": r["created_at"],
                    "notification_id": str(r["id"]),
                    "blocked_reason": blocked_attempt(
                        r,
                        self.sender.provider,
                        at,
                        self.policy.max_retries,
                        self.policy.idempotency_margin_seconds,
                    ),
                }
                for r in ready
            )
            report["preview"].sort(key=lambda p: (utc(p["created_at"]), p["notification_id"]))
            count = 0
            for preview in report["preview"]:
                if self.sender.scope == "real" and (
                    not getattr(self.sender, "configured", True)
                    or not preview["payload"].get("from")
                ):
                    preview["blocked_reason"] = (
                        preview.get("blocked_reason") or "provider_configuration"
                    )
                preview["would_send"] = (
                    not preview.get("blocked_reason") and count < self.policy.max_messages
                )
                if preview["would_send"]:
                    count += 1
            return report
        with self.repository.lock():
            report["recovered"] = self.repository.recover(
                self.sender.scope,
                at,
                self.policy.lease_seconds,
                self.policy.max_retries,
                addresses,
                alert_id,
                selection_ids,
                digest,
            )
            for recovered in report["recovered"]:
                if recovered["status"] == "failed" or not retry:
                    report[recovered["status"]] += 1
                    value = self.repository.get(uuid.UUID(recovered["id"]))
                    if value:
                        report["items"].append(self._summary(value))
            self._prepare(alerts, addresses, url, kind, window, at, report, False)
            for r in self.repository.ready(
                self.sender.scope, addresses, at, retry, alert_id, selection_ids, digest
            )[: self.policy.max_messages]:
                attempt = self.repository.begin_attempt(
                    r["id"],
                    at if now else datetime.now(UTC),
                    self.sender.provider,
                    self.sender.idempotency_seconds,
                    self.policy.max_retries,
                    self.policy.idempotency_margin_seconds,
                )
                if attempt is None:
                    value = self.repository.get(r["id"])
                    if value and value["status"] == "failed":
                        report["failed"] += 1
                        report["items"].append(self._summary(value))
                    continue
                receipt = None
                error = None
                started = time.perf_counter()
                try:
                    receipt = self.sender.send(
                        attempt["payload_snapshot"], attempt["idempotency_key"]
                    )
                except DeliveryError as failure:
                    error = failure
                except Exception:
                    error = DeliveryError(
                        "provider_unexpected",
                        "Resultado del proveedor no confirmado.",
                        retryable=True,
                        ambiguous=self.sender.scope == "real",
                    )
                duration = (time.perf_counter() - started) * 1000
                # An explicit now is a deterministic clock for isolated tests.
                finished = at if now else datetime.now(UTC)
                result = self.repository.complete(
                    r["id"],
                    finished,
                    duration,
                    receipt,
                    error,
                    self.policy.max_retries,
                    self.policy.retry_seconds,
                )
                report[result["status"]] += 1
                report["items"].append(self._summary(result))
                log_event(
                    logger,
                    "notification_attempt",
                    notification_id=str(r["id"]),
                    alert_ids=[a["id"] for a in r["payload_snapshot"]["alerts"]],
                    recipient="sha256:" + hashlib.sha256(r["recipient"].encode()).hexdigest(),
                    provider=self.sender.provider,
                    attempt=result["attempt_count"],
                    status=result["status"],
                    duration_ms=round(duration, 3),
                    error_code=result["error_code"],
                    digest_total=len(r["payload_snapshot"]["alerts"]),
                )
        return report

    def _prepare(
        self,
        alerts: list[dict[str, Any]],
        addresses: list[str],
        url: str,
        kind: str,
        window: tuple[datetime, datetime] | None,
        at: datetime,
        report: dict[str, Any],
        dry_run: bool,
    ) -> None:
        for address in addresses:
            ids = [uuid.UUID(str(a["id"])) for a in alerts]
            assigned = self.repository.assigned(ids, address, self.sender.scope)
            # Capture remains separate, but digests never preview an alert already
            # assigned to a REAL notification for this recipient.
            if self.sender.scope == "capture" and kind == "digest":
                assigned |= self.repository.assigned(ids, address, "real")
            available = sort_alerts([a for a in alerts if uuid.UUID(str(a["id"])) not in assigned])
            report["skipped"] += len(assigned)
            size = self.policy.max_digest_alerts if kind == "digest" else 1
            for start in range(0, len(available), size):
                if report["prepared"] >= self.policy.max_messages:
                    return
                group = available[start : start + size]
                payload = compose(group, address, url, kind, self.policy.sender)
                if dry_run:
                    key = identity(group, address, self.sender.scope, kind, window)
                    report["preview"].append(
                        {
                            "payload": payload,
                            "notification_type": kind,
                            "created_at": at,
                            "idempotency_key": key,
                            "notification_id": str(
                                uuid.uuid5(uuid.NAMESPACE_URL, "eureka-notification:" + key)
                            ),
                        }
                    )
                    report["prepared"] += 1
                else:
                    identifier = self.repository.prepare(
                        group,
                        address,
                        self.sender.scope,
                        self.sender.provider,
                        kind,
                        payload,
                        at,
                        window,
                    )
                    if identifier:
                        report["prepared"] += 1
                    else:
                        report["skipped"] += len(group)

    @staticmethod
    def _summary(value: dict[str, Any]) -> dict[str, Any]:
        return {
            k: value[k]
            for k in (
                "id",
                "status",
                "recipient",
                "notification_type",
                "attempt_count",
                "retry_count",
                "provider_message_id",
                "error_code",
            )
        }


def build_notification_dispatcher(
    sessions: sessionmaker[Session], settings: Settings
) -> NotificationDispatcher:
    sender: EmailSender
    if settings.eureka_notification_mode == "resend":
        sender = ResendEmailSender(
            settings.resend_api_key.get_secret_value(), settings.eureka_notification_timeout_seconds
        )
    else:
        sender = DevEmailSender(settings.eureka_notification_capture_path)
    if (
        settings.eureka_notification_processing_lease_seconds
        <= settings.eureka_notification_timeout_seconds
    ):
        raise ValueError("El lease debe superar el timeout del proveedor.")
    policy = DispatchPolicy(
        enabled=settings.eureka_notification_enabled
        and settings.eureka_notification_mode != "disabled",
        base_url=settings.eureka_notification_base_url,
        sender=settings.resend_from_email,
        max_retries=settings.eureka_notification_max_retries,
        retry_seconds=settings.eureka_notification_retry_seconds,
        lease_seconds=settings.eureka_notification_processing_lease_seconds,
        idempotency_margin_seconds=max(
            settings.eureka_notification_idempotency_margin_seconds,
            int(settings.eureka_notification_timeout_seconds) + 1,
        ),
        max_messages=settings.eureka_notification_max_messages,
        max_digest_alerts=settings.eureka_notification_digest_max_alerts,
    )
    return NotificationDispatcher(
        SqlNotificationRepository(sessions), PersistedAlertSource(sessions), sender, policy
    )


class NotificationQueries:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def listing(self, page: int, page_size: int, filters: dict[str, Any]) -> dict[str, Any]:
        with self.sessions() as session:
            if session.get_bind().dialect.name == "postgresql":
                session.execute(text("SET TRANSACTION READ ONLY"))
            ensure_schema(session)
            statement = select(NotificationRecord)
            for key in ("status", "channel", "recipient", "delivery_scope"):
                if filters.get(key):
                    statement = statement.where(getattr(NotificationRecord, key) == filters[key])
            if filters.get("alert_id"):
                statement = statement.where(
                    NotificationRecord.id.in_(
                        select(NotificationAlertRecord.notification_id).where(
                            NotificationAlertRecord.alert_id == filters["alert_id"]
                        )
                    )
                )
            if filters.get("created_from"):
                statement = statement.where(
                    NotificationRecord.created_at >= filters["created_from"]
                )
            if filters.get("created_before"):
                statement = statement.where(
                    NotificationRecord.created_at < filters["created_before"]
                )
            total = session.scalar(select(func.count()).select_from(statement.subquery())) or 0
            rows = session.scalars(
                statement.order_by(NotificationRecord.created_at.desc(), NotificationRecord.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            items = []
            for r in rows:
                item = record_json(r)
                alerts = item.pop("payload_snapshot")["alerts"]
                item.pop("attempt_history")
                item["alert_ids"] = [a["id"] for a in alerts]
                items.append(item)
            counts = dict.fromkeys(STATUSES, 0)
            for status, count in session.execute(
                select(NotificationRecord.status, func.count()).group_by(NotificationRecord.status)
            ):
                counts[status] = count
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "counts": counts,
            }

    def detail(self, identifier: uuid.UUID) -> dict[str, Any]:
        with self.sessions() as session:
            if session.get_bind().dialect.name == "postgresql":
                session.execute(text("SET TRANSACTION READ ONLY"))
            ensure_schema(session)
            r = session.get(NotificationRecord, identifier)
            if r is None:
                raise LookupError("Notificación no encontrada.")
            return record_json(r)
