"""Persistencia propia de procesos: upsert atómico sin tocar compras ni ítems existentes."""

import uuid
from dataclasses import asdict
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Date, DateTime, String, Text, UniqueConstraint, or_, select
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from public_procurement.shared.persistence import Base
from public_procurement.shared.text import normalize_text

from .domain.process import ProcessQuery, ProcessSyncResult, SecopProcess


class SecopProcessRecord(Base):
    __tablename__ = "secop_process"
    __table_args__ = (UniqueConstraint("dataset_id", "id_del_proceso"), {"schema": "ingestion"})

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[str] = mapped_column(String(16))
    id_del_proceso: Mapped[str] = mapped_column(String(128))
    id_del_portafolio: Mapped[str | None] = mapped_column(String(128), index=True)
    reference: Mapped[str | None] = mapped_column(Text)
    entity_name: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(Text)
    municipality: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    modality: Mapped[str | None] = mapped_column(Text)
    phase: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    published_on: Mapped[date | None] = mapped_column(Date, index=True)
    last_published_on: Mapped[date | None] = mapped_column(Date)
    base_price_cop: Mapped[int | None] = mapped_column(BigInteger)
    category_code: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    offer_deadline_raw: Mapped[Any | None] = mapped_column(
        JSON(none_as_null=True).with_variant(JSONB(none_as_null=True), "postgresql"), nullable=True
    )


class ProcessSyncRunRecord(Base):
    __tablename__ = "process_sync_run"
    __table_args__ = ({"schema": "ingestion"},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    read_count: Mapped[int]
    unique_count: Mapped[int]
    changed_count: Mapped[int]
    published_from: Mapped[date | None] = mapped_column(Date)
    published_before: Mapped[date | None] = mapped_column(Date)
    portfolio_id: Mapped[str | None] = mapped_column(String(128))


class SqlProcessRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find(self, reference: str) -> tuple[uuid.UUID, str, str | None] | None:
        try:
            process_id = uuid.UUID(reference)
        except ValueError:
            condition = SecopProcessRecord.id_del_proceso == reference
        else:
            condition = SecopProcessRecord.id == process_id
        record = self._session.scalars(
            select(SecopProcessRecord).where(
                condition, SecopProcessRecord.dataset_id == "p6dx-8zbt"
            )
        ).one_or_none()
        if record is None:
            return None
        return record.id, record.id_del_proceso, record.id_del_portafolio

    def read_page(
        self,
        reference: str | None,
        department: str | None,
        after: uuid.UUID | None,
        page_size: int,
    ) -> list[tuple[uuid.UUID, SecopProcess]]:
        query = select(SecopProcessRecord).where(SecopProcessRecord.dataset_id == "p6dx-8zbt")
        if reference:
            try:
                identifier = uuid.UUID(reference)
            except ValueError:
                query = query.where(SecopProcessRecord.id_del_proceso == reference)
            else:
                query = query.where(SecopProcessRecord.id == identifier)
        if department:
            from sqlalchemy import func

            query = query.where(
                func.translate(func.lower(SecopProcessRecord.department), "áéíóúüñ", "aeiouun")
                == normalize_text(department.strip())
            )
        if after is not None:
            query = query.where(SecopProcessRecord.id > after)
        records = self._session.scalars(
            query.order_by(SecopProcessRecord.id).limit(page_size)
        ).all()
        fields = tuple(SecopProcess.__dataclass_fields__)
        return [
            (record.id, SecopProcess(**{name: getattr(record, name) for name in fields}))
            for record in records
        ]

    def save_all(self, processes: list[SecopProcess], acquired_at: datetime) -> int:
        changed = 0
        for process in processes:
            values = asdict(process)
            statement = insert(SecopProcessRecord).values(
                id=uuid.uuid4(), acquired_at=acquired_at, **values
            )
            mutable = {
                key: statement.excluded[key]
                for key in values
                if key not in ("dataset_id", "id_del_proceso")
            }
            upsert = statement.on_conflict_do_update(
                index_elements=["dataset_id", "id_del_proceso"],
                set_={**mutable, "acquired_at": acquired_at},
                where=or_(
                    *(
                        getattr(SecopProcessRecord, key).is_distinct_from(value)
                        for key, value in mutable.items()
                    )
                ),
            ).returning(SecopProcessRecord.id)
            changed += int(self._session.scalar(upsert) is not None)
        return changed

    def add_run(self, result: ProcessSyncResult, query: ProcessQuery) -> None:
        self._session.add(
            ProcessSyncRunRecord(
                **asdict(result),
                published_from=query.published_from,
                published_before=query.published_before,
                portfolio_id=query.portfolio_id,
            )
        )
        self._session.flush()
