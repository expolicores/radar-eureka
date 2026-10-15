"""Notification outbox, membership uniqueness and bounded attempt history."""

import copy
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from public_procurement.shared.persistence import Base

from .domain.message import DeliveryError, DeliveryReceipt, blocked_attempt, identity, retry_at, utc

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class NotificationRecord(Base):
    __tablename__ = "notification"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        UniqueConstraint(
            "id", "recipient", "channel", "delivery_scope", name="uq_notification_membership_parent"
        ),
        CheckConstraint(
            "status IN ('pending','processing','captured','sent','retryable','failed','skipped')",
            name="status",
        ),
        CheckConstraint("delivery_scope IN ('capture','real')", name="scope"),
        CheckConstraint("channel='email'", name="channel"),
        CheckConstraint(
            "recipient=lower(recipient) AND recipient=trim(recipient)", name="recipient_normalized"
        ),
        CheckConstraint("notification_type IN ('immediate','digest')", name="type"),
        CheckConstraint("attempt_count>=0 AND retry_count>=0", name="attempts"),
        Index("ix_notification_ready", "delivery_scope", "status", "next_retry_at"),
        Index("ix_notification_created", "created_at", "id"),
        {"schema": "notifications"},
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    alert_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("eureka.alert.id"))
    channel: Mapped[str] = mapped_column(String(16))
    recipient: Mapped[str] = mapped_column(String(254))
    notification_type: Mapped[str] = mapped_column(String(16))
    delivery_scope: Mapped[str] = mapped_column(String(16))
    delivery_mode: Mapped[str] = mapped_column(String(16))
    provider: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_idempotency_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_ambiguous: Mapped[bool]
    attempt_count: Mapped[int]
    retry_count: Mapped[int]
    provider_message_id: Mapped[str | None] = mapped_column(String(256))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    payload_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)
    attempt_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE)
    idempotency_key: Mapped[str] = mapped_column(String(64))
    digest_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    digest_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationAlertRecord(Base):
    __tablename__ = "notification_alert"
    __table_args__ = (
        ForeignKeyConstraint(
            ["notification_id", "recipient", "channel", "delivery_scope"],
            [
                "notifications.notification.id",
                "notifications.notification.recipient",
                "notifications.notification.channel",
                "notifications.notification.delivery_scope",
            ],
        ),
        UniqueConstraint(
            "alert_id", "recipient", "channel", "delivery_scope", name="uq_notification_alert_claim"
        ),
        Index("ix_notification_alert_alert_id", "alert_id"),
        {"schema": "notifications"},
    )
    notification_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eureka.alert.id"), primary_key=True)
    recipient: Mapped[str] = mapped_column(String(254))
    channel: Mapped[str] = mapped_column(String(16))
    delivery_scope: Mapped[str] = mapped_column(String(16))


def record_json(record: NotificationRecord) -> dict[str, Any]:
    return {
        column.name: copy.deepcopy(getattr(record, column.name))
        for column in NotificationRecord.__table__.columns
    }


class DispatcherBusyError(RuntimeError):
    pass


class SqlNotificationRepository:
    def __init__(self, sessions: sessionmaker[Session]):
        self.sessions = sessions

    @contextmanager
    def lock(self) -> Iterator[None]:
        with self.sessions() as session:
            postgres = session.get_bind().dialect.name == "postgresql"
            if postgres and not session.scalar(select(func.pg_try_advisory_lock(741044))):
                raise DispatcherBusyError("Ya hay un dispatcher activo; esta ejecución no enviará.")
            try:
                yield
            finally:
                if postgres:
                    session.scalar(select(func.pg_advisory_unlock(741044)))

    def assigned(self, alerts: list[uuid.UUID], address: str, scope: str) -> set[uuid.UUID]:
        with self.sessions() as session:
            return set(
                session.scalars(
                    select(NotificationAlertRecord.alert_id).where(
                        NotificationAlertRecord.alert_id.in_(alerts),
                        NotificationAlertRecord.recipient == address,
                        NotificationAlertRecord.channel == "email",
                        NotificationAlertRecord.delivery_scope == scope,
                    )
                )
            )

    def prepare(
        self,
        alerts: list[dict[str, Any]],
        address: str,
        scope: str,
        provider: str,
        kind: str,
        payload: dict[str, Any],
        at: datetime,
        window: tuple[datetime, datetime] | None,
    ) -> uuid.UUID | None:
        key = identity(alerts, address, scope, kind, window)
        identifier = uuid.uuid5(uuid.NAMESPACE_URL, "eureka-notification:" + key)
        try:
            with self.sessions.begin() as session:
                session.add(
                    NotificationRecord(
                        id=identifier,
                        alert_id=uuid.UUID(str(alerts[0]["id"])) if kind == "immediate" else None,
                        recipient=address,
                        channel="email",
                        notification_type=kind,
                        delivery_scope=scope,
                        delivery_mode=provider,
                        provider=provider,
                        status="pending",
                        created_at=at,
                        updated_at=at,
                        attempt_count=0,
                        retry_count=0,
                        delivery_ambiguous=False,
                        payload_snapshot=payload,
                        attempt_history=[],
                        idempotency_key=key,
                        digest_from=window[0] if window else None,
                        digest_to=window[1] if window else None,
                    )
                )
                session.flush()
                session.add_all(
                    NotificationAlertRecord(
                        notification_id=identifier,
                        alert_id=uuid.UUID(str(a["id"])),
                        recipient=address,
                        channel="email",
                        delivery_scope=scope,
                    )
                    for a in alerts
                )
            return identifier
        except IntegrityError as error:
            # Atomic rollback includes the message: a lost membership race cannot
            # leave an orphan digest or replace an existing frozen payload.
            code = getattr(error.orig, "sqlstate", None)
            sqlite_code = getattr(error.orig, "sqlite_errorcode", None)
            if code != "23505" and sqlite_code not in (1555, 2067):
                raise
            return None

    def get(self, identifier: uuid.UUID) -> dict[str, Any] | None:
        with self.sessions() as session:
            value = session.get(NotificationRecord, identifier)
            return record_json(value) if value else None

    def ready(
        self,
        scope: str,
        addresses: list[str],
        at: datetime,
        retry: bool,
        alert_id: uuid.UUID | None = None,
        selection_ids: list[uuid.UUID] | None = None,
        digest_only: bool = False,
    ) -> list[dict[str, Any]]:
        with self.sessions() as session:
            statement = select(NotificationRecord).where(
                NotificationRecord.delivery_scope == scope,
                NotificationRecord.recipient.in_(addresses),
                NotificationRecord.status.in_(("pending", "retryable") if retry else ("pending",)),
            )
            if alert_id:
                statement = statement.where(
                    NotificationRecord.id.in_(
                        select(NotificationAlertRecord.notification_id).where(
                            NotificationAlertRecord.alert_id == alert_id
                        )
                    )
                )
            if selection_ids is not None:
                statement = statement.where(
                    NotificationRecord.id.in_(
                        select(NotificationAlertRecord.notification_id).where(
                            NotificationAlertRecord.alert_id.in_(selection_ids)
                        )
                    )
                )
            if digest_only:
                statement = statement.where(NotificationRecord.notification_type == "digest")
            return [
                record_json(r)
                for r in session.scalars(
                    statement.order_by(NotificationRecord.created_at, NotificationRecord.id)
                )
                if r.next_retry_at is None or utc(r.next_retry_at) <= at
            ]

    def stale(
        self,
        scope: str,
        at: datetime,
        lease_seconds: int,
        addresses: list[str],
        alert_id: uuid.UUID | None = None,
        selection_ids: list[uuid.UUID] | None = None,
        digest_only: bool = False,
    ) -> list[dict[str, Any]]:
        with self.sessions() as session:
            statement = select(NotificationRecord).where(
                NotificationRecord.delivery_scope == scope,
                NotificationRecord.status == "processing",
                NotificationRecord.processing_started_at <= at - timedelta(seconds=lease_seconds),
                NotificationRecord.recipient.in_(addresses),
            )
            if alert_id:
                statement = statement.where(
                    NotificationRecord.id.in_(
                        select(NotificationAlertRecord.notification_id).where(
                            NotificationAlertRecord.alert_id == alert_id
                        )
                    )
                )
            if selection_ids is not None:
                statement = statement.where(
                    NotificationRecord.id.in_(
                        select(NotificationAlertRecord.notification_id).where(
                            NotificationAlertRecord.alert_id.in_(selection_ids)
                        )
                    )
                )
            if digest_only:
                statement = statement.where(NotificationRecord.notification_type == "digest")
            return [record_json(r) for r in session.scalars(statement)]

    def recover(
        self,
        scope: str,
        at: datetime,
        lease_seconds: int,
        max_retries: int,
        addresses: list[str],
        alert_id: uuid.UUID | None = None,
        selection_ids: list[uuid.UUID] | None = None,
        digest_only: bool = False,
    ) -> list[dict[str, Any]]:
        recovered = []
        ids = [
            r["id"]
            for r in self.stale(
                scope, at, lease_seconds, addresses, alert_id, selection_ids, digest_only
            )
        ]
        with self.sessions.begin() as session:
            for r in session.scalars(
                select(NotificationRecord).where(
                    NotificationRecord.id.in_(ids),
                    NotificationRecord.status == "processing",
                )
            ):
                history = copy.deepcopy(r.attempt_history)
                if history and history[-1]["result"] == "started":
                    started = datetime.fromisoformat(history[-1]["timestamp"])
                    history[-1].update(
                        result="interrupted",
                        finished_at=at.isoformat(),
                        duration_ms=None,
                        observed_elapsed_ms=round((at - utc(started)).total_seconds() * 1000, 3),
                        error_code="processing_interrupted",
                        error_message="Resultado de envío no confirmado.",
                    )
                r.attempt_history = history
                r.delivery_ambiguous = scope == "real"
                unsafe = scope == "real" and (
                    r.provider_idempotency_until is None or at >= utc(r.provider_idempotency_until)
                )
                exhausted = r.attempt_count >= max_retries + 1
                r.status = "failed" if unsafe or exhausted else "retryable"
                r.error_code = (
                    "delivery_unknown_review"
                    if unsafe
                    else ("retry_exhausted" if exhausted else "processing_interrupted")
                )
                r.error_message = (
                    "Envío interrumpido: requiere revisión."
                    if r.status == "failed"
                    else "Envío interrumpido: reintento idempotente disponible."
                )
                r.updated_at = at
                r.next_retry_at = at if r.status == "retryable" else None
                r.failed_at = at if r.status == "failed" else r.failed_at
                r.processing_started_at = None
                recovered.append({"id": str(r.id), "status": r.status, "error_code": r.error_code})
        return recovered

    def begin_attempt(
        self,
        identifier: uuid.UUID,
        at: datetime,
        provider: str,
        idempotency_seconds: int | None,
        max_retries: int,
        margin_seconds: int = 0,
    ) -> dict[str, Any] | None:
        with self.sessions.begin() as session:
            r = session.scalar(
                select(NotificationRecord)
                .where(NotificationRecord.id == identifier)
                .with_for_update()
            )
            if r is None or r.status not in ("pending", "retryable"):
                return None
            reason = blocked_attempt(record_json(r), provider, at, max_retries, margin_seconds)
            if reason:
                r.status = "failed"
                r.failed_at = r.updated_at = at
                r.next_retry_at = None
                r.error_code = reason
                r.error_message = "Reintento automático bloqueado; se requiere revisión."
                return None
            if r.attempt_count == 0 and idempotency_seconds is not None:
                r.provider_idempotency_until = at + timedelta(seconds=idempotency_seconds)
            r.attempt_count += 1
            r.retry_count = max(0, r.attempt_count - 1)
            r.status = "processing"
            r.processing_started_at = r.updated_at = at
            r.attempt_history = [
                *r.attempt_history,
                {
                    "timestamp": at.isoformat(),
                    "provider": provider,
                    "attempt_number": r.attempt_count,
                    "duration_ms": None,
                    "result": "started",
                    "status_code": None,
                    "error_code": None,
                    "error_message": None,
                    "provider_message_id": None,
                },
            ]
            return record_json(r)

    def complete(
        self,
        identifier: uuid.UUID,
        at: datetime,
        duration_ms: float,
        receipt: DeliveryReceipt | None,
        error: DeliveryError | None,
        max_retries: int,
        retry_seconds: int,
    ) -> dict[str, Any]:
        with self.sessions.begin() as session:
            r = session.get(NotificationRecord, identifier)
            if r is None or r.status != "processing":
                raise RuntimeError("Intento de notificación no activo.")
            history = copy.deepcopy(r.attempt_history)
            r.updated_at = at
            r.processing_started_at = None
            if receipt is not None:
                r.status = "captured" if r.delivery_scope == "capture" else "sent"
                r.provider_message_id = receipt.message_id
                r.error_code = r.error_message = None
                r.next_retry_at = None
                r.delivery_ambiguous = False
                if r.status == "sent":
                    r.sent_at = at
                else:
                    r.captured_at = at
            elif error is not None:
                r.delivery_ambiguous = r.delivery_ambiguous or error.ambiguous
                r.status = (
                    "retryable"
                    if error.retryable and r.attempt_count < max_retries + 1
                    else "failed"
                )
                r.error_code = (
                    error.code
                    if r.status == "retryable" or not error.retryable
                    else "retry_exhausted"
                )
                r.error_message = error.message
                r.failed_at = at
                r.next_retry_at = (
                    retry_at(at, r.attempt_count, retry_seconds, error.retry_after)
                    if r.status == "retryable"
                    else None
                )
            else:
                raise ValueError("El intento requiere resultado.")
            history[-1].update(
                result=r.status,
                finished_at=at.isoformat(),
                duration_ms=round(duration_ms, 3),
                error_code=error.code if error else None,
                error_message=error.message if error else None,
                status_code=error.status_code
                if error
                else (receipt.status_code if receipt else None),
                provider_message_id=receipt.message_id if receipt else None,
            )
            r.attempt_history = history
            return record_json(r)
