"""Un resultado vigente por proceso; la FK es declarativa, no una lectura de tablas ajenas."""

import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from public_procurement.shared.persistence import Base

from .domain.details import StoredOpportunity
from .domain.discovery import OpportunityEvaluation

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class OpportunityRecord(Base):
    __tablename__ = "opportunity"
    __table_args__ = (UniqueConstraint("process_id"), {"schema": "eureka"})
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    process_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ingestion.secop_process.id"))
    score: Mapped[int] = mapped_column(Integer)
    priority_band: Mapped[str] = mapped_column(String(16))
    active: Mapped[bool] = mapped_column(Boolean, index=True)
    state: Mapped[str] = mapped_column(String(16))
    matched_categories: Mapped[list[str]] = mapped_column(JSON_TYPE)
    matched_unspsc: Mapped[list[str]] = mapped_column(JSON_TYPE)
    matched_terms: Mapped[list[str]] = mapped_column(JSON_TYPE)
    matched_context: Mapped[list[str]] = mapped_column(JSON_TYPE)
    penalties: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE)
    reasons: Mapped[list[dict[str, Any]]] = mapped_column(JSON_TYPE)
    review_notes: Mapped[list[str]] = mapped_column(JSON_TYPE)
    rule_version: Mapped[str] = mapped_column(String(64))
    config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlOpportunityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_process(self, process_id: uuid.UUID) -> StoredOpportunity | None:
        record = self.session.scalar(
            select(OpportunityRecord).where(OpportunityRecord.process_id == process_id)
        )
        if record is None:
            return None
        return StoredOpportunity(
            record.id,
            record.process_id,
            record.score,
            record.priority_band,
            tuple(record.matched_categories),
            record.state == "review" or bool(record.review_notes),
            record.rule_version,
            tuple(record.review_notes),
        )

    def save(self, evaluation: OpportunityEvaluation, at: datetime, config: dict[str, Any]) -> None:
        values = asdict(evaluation)
        values.pop("secop_id")
        statement = insert(OpportunityRecord).values(
            id=uuid.uuid4(), discovered_at=at, evaluated_at=at, config_snapshot=config, **values
        )
        self.session.execute(
            statement.on_conflict_do_update(
                index_elements=["process_id"],
                set_={
                    **{key: statement.excluded[key] for key in values if key != "process_id"},
                    "evaluated_at": at,
                    "config_snapshot": config,
                },
            )
        )


class SqlOpportunityQueries:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def get_by_process(self, process_id: uuid.UUID) -> StoredOpportunity | None:
        with self.sessions() as session:
            return SqlOpportunityRepository(session).get_by_process(process_id)

    def get_by_id(self, opportunity_id: uuid.UUID) -> StoredOpportunity | None:
        with self.sessions() as session:
            record = session.get(OpportunityRecord, opportunity_id)
            return (
                SqlOpportunityRepository(session).get_by_process(record.process_id)
                if record
                else None
            )

    def all(self) -> list[StoredOpportunity]:
        with self.sessions() as session:
            records = session.scalars(
                select(OpportunityRecord).order_by(
                    OpportunityRecord.score.desc(), OpportunityRecord.id
                )
            ).all()
            return [
                StoredOpportunity(
                    record.id,
                    record.process_id,
                    record.score,
                    record.priority_band,
                    tuple(record.matched_categories),
                    record.state == "review" or bool(record.review_notes),
                    record.rule_version,
                    tuple(record.review_notes),
                )
                for record in records
            ]
