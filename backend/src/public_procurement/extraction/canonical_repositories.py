import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from public_procurement.shared.persistence import Base

from .domain.canonical import CanonicalFact
from .domain.structured import StructuredFact
from .repositories import JSON_TYPE
from .structured_repositories import StructuredFactRecord, as_fact


class CanonicalFactRecord(Base):
    __tablename__ = "canonical_fact"
    __table_args__ = (
        UniqueConstraint(
            "process_id",
            "rule_version",
            "input_digest",
            "canonical_type",
            "canonical_key",
            name="uq_canonical_snapshot_fact",
        ),
        {"schema": "extraction"},
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    process_id: Mapped[uuid.UUID] = mapped_column(index=True)
    canonical_type: Mapped[str] = mapped_column(String(64))
    canonical_key: Mapped[str] = mapped_column(String(64))
    canonical_value: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)
    confidence: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    status: Mapped[str] = mapped_column(String(32))
    rule_version: Mapped[str] = mapped_column(String(64))
    input_digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CanonicalEvidenceRecord(Base):
    __tablename__ = "canonical_fact_evidence"
    __table_args__ = ({"schema": "extraction"},)
    canonical_fact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extraction.canonical_fact.id"), primary_key=True
    )
    structured_fact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extraction.structured_fact.id"), primary_key=True
    )


class SqlCanonicalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, facts: tuple[CanonicalFact, ...], at: datetime) -> int:
        inserted = 0
        for fact in facts:
            statement = (
                insert(CanonicalFactRecord)
                .values(
                    id=fact.id,
                    process_id=fact.process_id,
                    canonical_type=fact.canonical_type,
                    canonical_key=fact.canonical_key,
                    canonical_value=fact.canonical_value,
                    confidence=fact.confidence,
                    status=fact.status,
                    rule_version=fact.rule_version,
                    input_digest=fact.input_digest,
                    created_at=at,
                    updated_at=at,
                )
                .on_conflict_do_nothing(
                    index_elements=[
                        "process_id",
                        "rule_version",
                        "input_digest",
                        "canonical_type",
                        "canonical_key",
                    ]
                )
                .returning(CanonicalFactRecord.id)
            )
            inserted += int(self.session.scalar(statement) is not None)
            for identifier in fact.evidence_ids:
                self.session.execute(
                    insert(CanonicalEvidenceRecord)
                    .values(
                        canonical_fact_id=fact.id,
                        structured_fact_id=identifier,
                    )
                    .on_conflict_do_nothing(
                        index_elements=["canonical_fact_id", "structured_fact_id"]
                    )
                )
        return inserted

    def list_facts(
        self, process_id: uuid.UUID, version: str | None = None, digest: str | None = None
    ) -> tuple[CanonicalFact, ...]:
        statement = select(CanonicalFactRecord).where(CanonicalFactRecord.process_id == process_id)
        if version is not None:
            statement = statement.where(CanonicalFactRecord.rule_version == version)
        if digest is not None:
            statement = statement.where(CanonicalFactRecord.input_digest == digest)
        records = self.session.scalars(
            statement.order_by(
                CanonicalFactRecord.rule_version,
                CanonicalFactRecord.input_digest,
                CanonicalFactRecord.canonical_type,
                CanonicalFactRecord.canonical_key,
            )
        ).all()
        links = (
            self.session.execute(
                select(CanonicalEvidenceRecord).where(
                    CanonicalEvidenceRecord.canonical_fact_id.in_(
                        [record.id for record in records]
                    ),
                )
            )
            .scalars()
            .all()
        )
        return tuple(
            CanonicalFact(
                r.id,
                r.process_id,
                r.canonical_type,
                r.canonical_key,
                r.canonical_value,
                r.confidence,
                r.status,
                r.rule_version,
                r.input_digest,
                tuple(
                    sorted(
                        (
                            link.structured_fact_id
                            for link in links
                            if link.canonical_fact_id == r.id
                        ),
                        key=str,
                    )
                ),
            )
            for r in records
        )

    def evidence(self, process_id: uuid.UUID, canonical_id: uuid.UUID) -> list[StructuredFact]:
        records = self.session.scalars(
            select(StructuredFactRecord)
            .join(
                CanonicalEvidenceRecord,
                CanonicalEvidenceRecord.structured_fact_id == StructuredFactRecord.id,
            )
            .join(
                CanonicalFactRecord,
                CanonicalFactRecord.id == CanonicalEvidenceRecord.canonical_fact_id,
            )
            .where(
                CanonicalFactRecord.id == canonical_id,
                CanonicalFactRecord.process_id == process_id,
            )
            .order_by(StructuredFactRecord.id)
        ).all()
        return [as_fact(record) for record in records]
