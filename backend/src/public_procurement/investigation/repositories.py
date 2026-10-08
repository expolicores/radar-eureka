"""Persistencia de los casos en el esquema `investigation`.

Elementos (instantáneas) y notas son de solo inserción; del caso solo cambia `last_activity_at`.
Todas las consultas filtran por dueño.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from public_procurement.shared.persistence import Base

from .domain.case import (
    CaseDetail,
    CaseItem,
    CaseItemKind,
    CaseNote,
    CaseNotFoundError,
    CaseSummary,
    SaveResult,
)

SCHEMA = "investigation"


class CaseRecord(Base):
    __tablename__ = "case"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CaseItemRecord(Base):
    __tablename__ = "case_item"
    __table_args__ = (UniqueConstraint("case_id", "kind", "reference"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.case.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    reference: Mapped[str] = mapped_column(String(64))
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CaseNoteRecord(Base):
    __tablename__ = "case_note"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.case.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlCaseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _owned(self, owner_id: uuid.UUID, case_id: uuid.UUID) -> CaseRecord:
        record = self._session.scalars(
            select(CaseRecord)
            .where(CaseRecord.id == case_id)
            .where(CaseRecord.owner_id == owner_id)
        ).one_or_none()
        if record is None:
            raise CaseNotFoundError
        return record

    def _touch(self, case_id: uuid.UUID, at: datetime) -> None:
        self._session.execute(
            update(CaseRecord).where(CaseRecord.id == case_id).values(last_activity_at=at)
        )

    def create(self, owner_id: uuid.UUID, title: str, at: datetime) -> uuid.UUID:
        record = CaseRecord(
            id=uuid.uuid4(), owner_id=owner_id, title=title, created_at=at, last_activity_at=at
        )
        self._session.add(record)
        self._session.flush()
        return record.id

    def ensure_owned(self, owner_id: uuid.UUID, case_id: uuid.UUID) -> None:
        self._owned(owner_id, case_id)

    def add_item(
        self,
        owner_id: uuid.UUID,
        case_id: uuid.UUID,
        item: CaseItem,
    ) -> SaveResult:
        self._owned(owner_id, case_id)
        exists = self._session.scalar(
            select(func.count())
            .select_from(CaseItemRecord)
            .where(CaseItemRecord.case_id == case_id)
            .where(CaseItemRecord.kind == item.kind.value)
            .where(CaseItemRecord.reference == item.reference)
        )
        if exists:
            return SaveResult.ALREADY_SAVED
        self._session.add(
            CaseItemRecord(
                case_id=case_id,
                kind=item.kind.value,
                reference=item.reference,
                snapshot=item.snapshot,
                saved_at=item.saved_at,
            )
        )
        self._touch(case_id, item.saved_at)
        self._session.flush()
        return SaveResult.SAVED

    def add_note(self, owner_id: uuid.UUID, case_id: uuid.UUID, note: CaseNote) -> None:
        self._owned(owner_id, case_id)
        self._session.add(
            CaseNoteRecord(case_id=case_id, body=note.body, created_at=note.created_at)
        )
        self._touch(case_id, note.created_at)
        self._session.flush()

    def _summary(self, record: CaseRecord) -> CaseSummary:
        items = self._session.scalar(
            select(func.count())
            .select_from(CaseItemRecord)
            .where(CaseItemRecord.case_id == record.id)
        )
        notes = self._session.scalar(
            select(func.count())
            .select_from(CaseNoteRecord)
            .where(CaseNoteRecord.case_id == record.id)
        )
        return CaseSummary(
            id=record.id,
            title=record.title,
            item_count=items or 0,
            note_count=notes or 0,
            created_at=record.created_at,
            last_activity_at=record.last_activity_at,
        )

    def list_for(self, owner_id: uuid.UUID) -> list[CaseSummary]:
        records = self._session.scalars(
            select(CaseRecord)
            .where(CaseRecord.owner_id == owner_id)
            .order_by(CaseRecord.last_activity_at.desc())
        ).all()
        return [self._summary(record) for record in records]

    def get(self, owner_id: uuid.UUID, case_id: uuid.UUID) -> CaseDetail:
        record = self._owned(owner_id, case_id)
        items = self._session.scalars(
            select(CaseItemRecord)
            .where(CaseItemRecord.case_id == case_id)
            .order_by(CaseItemRecord.saved_at)
        ).all()
        notes = self._session.scalars(
            select(CaseNoteRecord)
            .where(CaseNoteRecord.case_id == case_id)
            .order_by(CaseNoteRecord.created_at)
        ).all()
        return CaseDetail(
            summary=self._summary(record),
            items=tuple(
                CaseItem(CaseItemKind(i.kind), i.reference, dict(i.snapshot), i.saved_at)
                for i in items
            ),
            notes=tuple(CaseNote(n.body, n.created_at) for n in notes),
        )
