"""Persistencia propia de Radar; sin lecturas SQL de tablas de otros módulos."""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from public_procurement.shared.persistence import Base

from .domain.radar import AlertDecision
from .repositories import JSON_TYPE


class RadarRunRecord(Base):
    __tablename__ = "radar_run"
    __table_args__ = ({"schema": "eureka"},)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24))
    start_date: Mapped[date] = mapped_column(Date)
    before_date: Mapped[date] = mapped_column(Date)
    regions: Mapped[list[str]] = mapped_column(JSON_TYPE)
    rule_version: Mapped[str] = mapped_column(String(64))
    config_hash: Mapped[str] = mapped_column(String(64))
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)
    processes_seen: Mapped[int] = mapped_column(default=0)
    new_processes: Mapped[int] = mapped_column(default=0)
    candidates: Mapped[int] = mapped_column(default=0)
    enriched: Mapped[int] = mapped_column(default=0)
    alerts_created: Mapped[int] = mapped_column(default=0)
    skipped: Mapped[int] = mapped_column(default=0)
    failures: Mapped[int] = mapped_column(default=0)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE)
    source: Mapped[str] = mapped_column(String(32), default="socrata", server_default="socrata")
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, default=dict)


class RadarProcessStateRecord(Base):
    __tablename__ = "radar_process_state"
    __table_args__ = (UniqueConstraint("dataset_id", "secop_id"), {"schema": "eureka"})
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(16))
    secop_id: Mapped[str] = mapped_column(String(128))
    process_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ingestion.secop_process.id"))
    first_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eureka.radar_run.id"))
    last_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eureka.radar_run.id"))
    status: Mapped[str] = mapped_column(String(24))
    stage: Mapped[str] = mapped_column(String(32))
    attempts: Mapped[int]
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RadarRunProcessRecord(Base):
    __tablename__ = "radar_run_process"
    __table_args__ = (UniqueConstraint("run_id", "dataset_id", "secop_id"), {"schema": "eureka"})
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eureka.radar_run.id"), index=True)
    dataset_id: Mapped[str] = mapped_column(String(16))
    secop_id: Mapped[str] = mapped_column(String(128))
    result: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)


class AlertRecord(Base):
    __tablename__ = "alert"
    __table_args__ = (
        UniqueConstraint("opportunity_id", "alert_type", "rule_version"),
        {"schema": "eureka"},
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eureka.opportunity.id"))
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eureka.radar_run.id"))
    alert_type: Mapped[str] = mapped_column(String(32))
    rule_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    priority: Mapped[str] = mapped_column(String(16))
    review_required: Mapped[bool]
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)
    canonical_key: Mapped[str | None] = mapped_column(String(180), unique=True, nullable=True)


COUNTERS = (
    "processes_seen",
    "new_processes",
    "candidates",
    "enriched",
    "alerts_created",
    "skipped",
    "failures",
)


def run_json(record: RadarRunRecord) -> dict[str, Any]:
    names = (
        "id",
        "started_at",
        "finished_at",
        "status",
        "start_date",
        "before_date",
        "regions",
        "rule_version",
        "config_hash",
        "errors",
        "source",
        "metrics",
        *COUNTERS,
    )
    return {name: getattr(record, name) for name in names}


def alert_json(record: AlertRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "opportunity_id": record.opportunity_id,
        "run_id": record.run_id,
        "alert_type": record.alert_type,
        "rule_version": record.rule_version,
        "created_at": record.created_at,
        "priority": record.priority,
        "review_required": record.review_required,
        "reasons": record.reasons,
        "snapshot": record.snapshot,
        "evidence_level": record.snapshot.get("evidence_level", "document_confirmed"),
        "document_status": record.snapshot.get("document_status", "available"),
        "source": record.snapshot.get("source", "socrata"),
    }


class SqlRadarRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    @contextmanager
    def lock(self) -> Iterator[None]:
        # Session-level advisory lock lives on this dedicated connection, not in HTTP workers.
        with self.sessions() as session:
            postgres = session.get_bind().dialect.name == "postgresql"
            if postgres and not session.scalar(select(func.pg_try_advisory_lock(741041))):
                raise RuntimeError("Ya hay una corrida Radar activa.")
            try:
                yield
            finally:
                if postgres:
                    session.scalar(select(func.pg_advisory_unlock(741041)))

    def start(self, run: dict[str, Any], snapshot: dict[str, Any]) -> None:
        with self.sessions.begin() as session:
            # A new lock holder proves an old running run is no longer active.
            for old in session.scalars(
                select(RadarRunRecord).where(
                    RadarRunRecord.status == "running",
                    RadarRunRecord.source == run.get("source", "socrata"),
                )
            ):
                old.status, old.finished_at = "interrupted", run["started_at"]
            session.add(
                RadarRunRecord(
                    **{
                        key: value
                        for key, value in run.items()
                        if key
                        in {
                            "id",
                            "started_at",
                            "finished_at",
                            "status",
                            "start_date",
                            "before_date",
                            "regions",
                            "rule_version",
                            "config_hash",
                            "errors",
                            "source",
                            "metrics",
                            *COUNTERS,
                        }
                    },
                    config_snapshot=snapshot,
                )
            )

    def state(self, dataset: str, secop_id: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            record = session.scalar(
                select(RadarProcessStateRecord).where(
                    RadarProcessStateRecord.dataset_id == dataset,
                    RadarProcessStateRecord.secop_id == secop_id,
                )
            )
            if record and self._legacy_empty_inventory(session, record):
                return {"status": "pending_documents", "attempts": 0, "stage": record.stage}
            return (
                {"status": record.status, "attempts": record.attempts, "stage": record.stage}
                if record
                else None
            )

    @staticmethod
    def _legacy_empty_inventory(session: Session, record: RadarProcessStateRecord) -> bool:
        if record.status != "failed" or record.stage != "documents_sync":
            return False
        result = session.scalar(
            select(RadarRunProcessRecord.result).where(
                RadarRunProcessRecord.run_id == record.last_run_id,
                RadarRunProcessRecord.dataset_id == record.dataset_id,
                RadarRunProcessRecord.secop_id == record.secop_id,
            )
        )
        error = (result or {}).get("error", {})
        return bool(
            error.get("type") == "ValueError"
            and error.get("message")
            == ("No hay inventario documental; el proceso queda reintentable.")
        )

    def claim(self, run_id: uuid.UUID, dataset: str, secop_id: str, at: datetime) -> None:
        with self.sessions.begin() as session:
            record = session.scalar(
                select(RadarProcessStateRecord).where(
                    RadarProcessStateRecord.dataset_id == dataset,
                    RadarProcessStateRecord.secop_id == secop_id,
                )
            )
            if record is None:
                record = RadarProcessStateRecord(
                    id=uuid.uuid4(),
                    dataset_id=dataset,
                    secop_id=secop_id,
                    first_run_id=run_id,
                    attempts=0,
                )
                session.add(record)
            if self._legacy_empty_inventory(session, record):
                record.attempts = 0
            record.attempts += 1
            record.status, record.stage, record.last_run_id, record.updated_at = (
                "processing",
                "candidate",
                run_id,
                at,
            )

    def stage(self, dataset: str, secop_id: str, stage: str, at: datetime) -> None:
        with self.sessions.begin() as session:
            record = session.scalar(
                select(RadarProcessStateRecord).where(
                    RadarProcessStateRecord.dataset_id == dataset,
                    RadarProcessStateRecord.secop_id == secop_id,
                )
            )
            if record:
                record.stage, record.updated_at = stage, at

    def outcome(
        self, run_id: uuid.UUID, item: dict[str, Any], at: datetime, update_state: bool
    ) -> None:
        from .review_services import record_review_entry

        with self.sessions.begin() as session:
            run = session.get(RadarRunRecord, run_id)
            if run is not None:
                record_review_entry(session, item, run.source, at)
            existing = session.scalar(
                select(RadarRunProcessRecord).where(
                    RadarRunProcessRecord.run_id == run_id,
                    RadarRunProcessRecord.dataset_id == item["dataset_id"],
                    RadarRunProcessRecord.secop_id == item["secop_id"],
                )
            )
            if existing:
                existing.result = item
            else:
                session.add(
                    RadarRunProcessRecord(
                        id=uuid.uuid4(),
                        run_id=run_id,
                        dataset_id=item["dataset_id"],
                        secop_id=item["secop_id"],
                        result=item,
                    )
                )
            if update_state:
                record = session.scalar(
                    select(RadarProcessStateRecord).where(
                        RadarProcessStateRecord.dataset_id == item["dataset_id"],
                        RadarProcessStateRecord.secop_id == item["secop_id"],
                    )
                )
                if record:
                    record.status = (
                        "failed"
                        if item["outcome"] == "failed" or item.get("coverage_incomplete")
                        else "completed"
                    )
                    record.stage, record.updated_at = item["stage"], at
                    record.process_id = (
                        uuid.UUID(item["process_id"]) if item.get("process_id") else None
                    )
                    if item.get("document_status") == "unavailable":
                        record.status = "pending_documents"
                        # Ausencia de inventario no consume reintentos de fallos técnicos.
                        record.attempts = 0

    def document_review_history(
        self, source: str, process_reference: str, exclude_run_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        """Read prior operational evidence for the exact source/process, never alert state."""
        with self.sessions() as session:
            rows = session.execute(
                select(RadarRunProcessRecord, RadarRunRecord)
                .join(RadarRunRecord, RadarRunProcessRecord.run_id == RadarRunRecord.id)
                .where(
                    RadarRunRecord.source == source,
                    RadarRunRecord.id != exclude_run_id,
                    RadarRunRecord.finished_at.is_not(None),
                    RadarRunProcessRecord.dataset_id == "licitaciones",
                    RadarRunProcessRecord.secop_id == process_reference,
                )
                .order_by(RadarRunRecord.started_at, RadarRunRecord.id)
            ).all()
            return [
                {
                    "run_id": str(run.id),
                    "result": {
                        key: item.result[key]
                        for key in (
                            "document_review",
                            "requires_manual_document_review",
                            "warnings",
                            "manual_review_reasons",
                        )
                        if key in item.result
                    },
                }
                for item, run in rows
            ]

    def finish(self, run: dict[str, Any]) -> None:
        with self.sessions.begin() as session:
            record = session.get(RadarRunRecord, run["id"])
            if record:
                for key in (*COUNTERS, "status", "finished_at", "errors", "metrics"):
                    if key in run:
                        setattr(record, key, run[key])

    def alert(
        self,
        run_id: uuid.UUID,
        opportunity_id: uuid.UUID,
        version: str,
        decision: AlertDecision,
        at: datetime,
    ) -> bool:
        with self.sessions.begin() as session:
            canonical_key = decision.snapshot.get("canonical_identity")
            existing = session.scalar(
                select(AlertRecord)
                .where(
                    or_(
                        AlertRecord.opportunity_id == opportunity_id,
                        AlertRecord.canonical_key == canonical_key,
                    )
                    if canonical_key
                    else AlertRecord.opportunity_id == opportunity_id,
                    AlertRecord.alert_type == "new_opportunity",
                )
                .with_for_update()
            )
            if existing:
                if (
                    existing.snapshot.get("evidence_level") == "metadata_only"
                    and decision.confirmed
                ):
                    existing.snapshot = {
                        **decision.snapshot,
                        "source": existing.snapshot.get("source", "socrata"),
                        "evidence_source": decision.snapshot.get("source", "socrata"),
                        "initial_metadata_alert": {
                            "snapshot": existing.snapshot,
                            "reasons": existing.reasons,
                        },
                        "evidence_updated_at": at.isoformat(),
                        "evidence_run_id": str(run_id),
                    }
                    existing.reasons = decision.reasons
                    existing.priority = decision.priority
                    existing.review_required = decision.review_required
                return False
            statement = (
                insert(AlertRecord)
                if session.get_bind().dialect.name == "postgresql"
                else _sqlite_insert()
            )
            result = session.execute(
                statement.values(
                    id=uuid.uuid4(),
                    opportunity_id=opportunity_id,
                    run_id=run_id,
                    alert_type="new_opportunity",
                    rule_version=version,
                    created_at=at,
                    priority=decision.priority,
                    review_required=decision.review_required,
                    reasons=decision.reasons,
                    snapshot=decision.snapshot,
                    canonical_key=canonical_key,
                )
                .on_conflict_do_nothing()
                .returning(AlertRecord.id)
            )
            return result.scalar_one_or_none() is not None

    def alert_for_opportunity(self, identifier: uuid.UUID) -> dict[str, Any] | None:
        with self.sessions() as session:
            record = session.scalar(
                select(AlertRecord)
                .where(AlertRecord.opportunity_id == identifier)
                .order_by(AlertRecord.created_at.desc(), AlertRecord.id)
                .limit(1)
            )
            return alert_json(record) if record else None

    def alert_for_canonical(self, canonical_key: str) -> dict[str, Any] | None:
        with self.sessions() as session:
            record = session.scalar(
                select(AlertRecord).where(AlertRecord.canonical_key == canonical_key)
            )
            return alert_json(record) if record else None

    def alerts(self, page: int, page_size: int) -> dict[str, Any]:
        with self.sessions() as session:
            total = session.scalar(select(func.count()).select_from(AlertRecord)) or 0
            rows = session.scalars(
                select(AlertRecord)
                .order_by(AlertRecord.created_at.desc(), AlertRecord.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            return {
                "items": [alert_json(row) for row in rows],
                "total": total,
                "page": page,
                "page_size": page_size,
            }

    def get_alert(self, identifier: uuid.UUID) -> dict[str, Any]:
        with self.sessions() as session:
            record = session.get(AlertRecord, identifier)
            if not record:
                raise LookupError("Alerta no encontrada.")
            return alert_json(record)

    def runs(self, page: int, page_size: int, source: str = "socrata") -> dict[str, Any]:
        with self.sessions() as session:
            total = (
                session.scalar(
                    select(func.count())
                    .select_from(RadarRunRecord)
                    .where(RadarRunRecord.source == source)
                )
                or 0
            )
            rows = session.scalars(
                select(RadarRunRecord)
                .where(RadarRunRecord.source == source)
                .order_by(RadarRunRecord.started_at.desc(), RadarRunRecord.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            return {
                "items": [run_json(row) for row in rows],
                "total": total,
                "page": page,
                "page_size": page_size,
            }

    def get_run(self, identifier: uuid.UUID) -> dict[str, Any]:
        with self.sessions() as session:
            record = session.get(RadarRunRecord, identifier)
            if not record:
                raise LookupError("Corrida no encontrada.")
            result = run_json(record)
            result["config_snapshot"] = record.config_snapshot
            result["items"] = [
                item.result
                for item in session.scalars(
                    select(RadarRunProcessRecord)
                    .where(RadarRunProcessRecord.run_id == identifier)
                    .order_by(RadarRunProcessRecord.secop_id)
                )
            ]
            return result


def _sqlite_insert() -> Any:
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    return sqlite_insert(AlertRecord)
