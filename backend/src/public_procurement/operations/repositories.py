import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from public_procurement.shared.persistence import Base

LOCK_ID = 741045


class CycleSchemaPendingError(RuntimeError):
    pass


class CycleRecord(Base):
    __tablename__ = "automation_cycle"
    __table_args__ = ({"schema": "operations"},)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32))
    radar_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("eureka.radar_run.id"), unique=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))


class CycleRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def ready(self) -> None:
        with self.sessions() as session:
            if session.get_bind().dialect.name == "postgresql" and not session.scalar(
                text("SELECT to_regclass('operations.automation_cycle')")
            ):
                raise CycleSchemaPendingError("Pendiente migración 0016_eureka_operations.")

    @contextmanager
    def lock(self) -> Iterator[Callable[[], None] | None]:
        with self.sessions() as session:
            if session.get_bind().dialect.name != "postgresql":
                raise RuntimeError("El ciclo requiere PostgreSQL advisory locks.")
            held = bool(session.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_ID}))

            def verify() -> None:
                # A lost/replaced connection must not permit progress into the next stage.
                if not session.scalar(
                    text(
                        "SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' "
                        "AND pid=pg_backend_pid() AND objid=:key AND granted)"
                    ),
                    {"key": LOCK_ID},
                ):
                    raise RuntimeError("Lock del coordinador perdido.")

            try:
                yield verify if held else None
            finally:
                if held:
                    session.scalar(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_ID})

    def save(self, cycle: dict[str, Any]) -> None:
        with self.sessions.begin() as session:
            record = session.get(CycleRecord, uuid.UUID(cycle["id"]))
            if record is None:
                record = CycleRecord(id=uuid.UUID(cycle["id"]))
                session.add(record)
            record.started_at = datetime.fromisoformat(cycle["started_at"])
            record.finished_at = (
                datetime.fromisoformat(cycle["finished_at"]) if cycle["finished_at"] else None
            )
            record.heartbeat_at = datetime.fromisoformat(cycle["heartbeat_at"])
            record.status = cycle["status"]
            record.radar_run_id = (
                uuid.UUID(cycle["radar_run_id"]) if cycle.get("radar_linked") else None
            )
            record.payload = dict(cycle)

    def listing(self, limit: int = 25) -> list[dict[str, Any]]:
        with self.sessions() as session:
            return list(
                session.scalars(
                    select(CycleRecord.payload).order_by(CycleRecord.started_at.desc()).limit(limit)
                )
            )

    def running(self) -> list[dict[str, Any]]:
        with self.sessions() as session:
            return list(
                session.scalars(select(CycleRecord.payload).where(CycleRecord.status == "running"))
            )

    def active(self) -> dict[str, Any] | None:
        with self.sessions() as session:
            if session.get_bind().dialect.name == "postgresql" and not session.scalar(
                text(
                    "SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND granted "
                    "AND classid=0 AND objid=:key AND objsubid=1 "
                    "AND database=(SELECT oid FROM pg_database WHERE datname=current_database()))"
                ),
                {"key": LOCK_ID},
            ):
                return None
            return session.scalar(
                select(CycleRecord.payload)
                .where(CycleRecord.status == "running")
                .order_by(CycleRecord.started_at.desc())
                .limit(1)
            )

    def detail(self, identifier: uuid.UUID) -> dict[str, Any]:
        with self.sessions() as session:
            record = session.get(CycleRecord, identifier)
            if record is None:
                raise LookupError("Ciclo no encontrado.")
            return record.payload

    def latest_success(self) -> dict[str, Any] | None:
        with self.sessions() as session:
            return session.scalar(
                select(CycleRecord.payload)
                .where(CycleRecord.status.in_(("completed", "completed_with_warnings")))
                .where(CycleRecord.payload["radar_status"].as_string().is_distinct_from("limited"))
                .order_by(CycleRecord.started_at.desc())
                .limit(1)
            )
