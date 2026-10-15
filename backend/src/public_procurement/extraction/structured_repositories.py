import uuid
from dataclasses import fields
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from public_procurement.shared.persistence import Base

from .domain.structured import StructuredFact
from .repositories import JSON_TYPE


class StructuredFactRecord(Base):
    __tablename__ = "structured_fact"
    __table_args__ = (
        UniqueConstraint(
            "process_id",
            "document_version_id",
            "rule_version",
            "fingerprint",
            name="uq_structured_fact_evidence",
        ),
        {"schema": "extraction"},
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    process_id: Mapped[uuid.UUID] = mapped_column(index=True)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.document_version.id"), index=True
    )
    content_fragment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extraction.content_fragment.id")
    )
    fact_type: Mapped[str] = mapped_column(String(64))
    string_value: Mapped[str | None] = mapped_column(Text)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    boolean_value: Mapped[bool | None]
    unit: Mapped[str | None] = mapped_column(String(64))
    normalized_value: Mapped[Any] = mapped_column(JSON_TYPE, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    evidence_text: Mapped[str] = mapped_column(Text)
    source_locator: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)
    rule_name: Mapped[str] = mapped_column(String(64))
    rule_version: Mapped[str] = mapped_column(String(64))
    fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def as_fact(record: StructuredFactRecord) -> StructuredFact:
    return StructuredFact(
        **{field.name: getattr(record, field.name) for field in fields(StructuredFact)}
    )


class SqlStructuredRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, facts: list[StructuredFact], at: datetime) -> int:
        inserted = 0
        for fact in facts:
            values = {field.name: getattr(fact, field.name) for field in fields(StructuredFact)}
            values.update(id=uuid.uuid4(), created_at=at)
            statement = (
                insert(StructuredFactRecord)
                .values(**values)
                .on_conflict_do_nothing(
                    index_elements=[
                        "process_id",
                        "document_version_id",
                        "rule_version",
                        "fingerprint",
                    ],
                )
                .returning(StructuredFactRecord.id)
            )
            inserted += int(self.session.scalar(statement) is not None)
        return inserted

    def list_facts(self, process_id: uuid.UUID, version: str | None = None) -> list[StructuredFact]:
        statement = select(StructuredFactRecord).where(
            StructuredFactRecord.process_id == process_id
        )
        if version is not None:
            statement = statement.where(StructuredFactRecord.rule_version == version)
        records = self.session.scalars(
            statement.order_by(
                StructuredFactRecord.fact_type,
                StructuredFactRecord.created_at,
                StructuredFactRecord.id,
            )
        ).all()
        return [as_fact(record) for record in records]
