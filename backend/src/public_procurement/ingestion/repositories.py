"""Persistencia de la ingesta (SQLAlchemy 2) en el esquema PostgreSQL `ingestion`.

El repositorio mapea entre los modelos de tabla y las entidades del dominio, que no conocen el ORM.
"""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ColumnElement,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Select,
    String,
    Text,
    UniqueConstraint,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship, selectinload, sessionmaker

from public_procurement.shared.persistence import Base
from public_procurement.shared.text import normalize_text

from .domain.purchase import (
    IngestionRunResult,
    ItemClassification,
    Panel,
    Purchase,
    PurchaseItem,
    Resolution,
    Source,
    TvAttributes,
    UnitPriceStatus,
    VatBasis,
)
from .domain.search import (
    HIGH_VALUE_LIMIT_COP,
    LOW_VALUE_LIMIT_COP,
    PurchaseFilterOptions,
    PurchasePage,
    PurchaseSearchCriteria,
    PurchaseSort,
    StoredPurchase,
    ValueRange,
)

SCHEMA = "ingestion"


class PurchaseRecord(Base):
    __tablename__ = "purchase"
    __table_args__ = (
        UniqueConstraint("source", "id_contrato"),
        UniqueConstraint("source", "identificador_de_la_orden"),
        CheckConstraint(
            "(source = 'secop_ii' AND id_contrato IS NOT NULL"
            " AND identificador_de_la_orden IS NULL)"
            " OR (source = 'tvec' AND identificador_de_la_orden IS NOT NULL"
            " AND id_contrato IS NULL)",
            name="source_identifier",
        ),
        CheckConstraint(
            "NOT supplier_is_natural_person OR supplier_nit IS NULL",
            name="natural_person_without_document",
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(16))
    id_contrato: Mapped[str | None] = mapped_column(String(64))
    identificador_de_la_orden: Mapped[str | None] = mapped_column(String(64))
    proceso_de_compra: Mapped[str | None] = mapped_column(String(64))
    entity_name: Mapped[str] = mapped_column(Text)
    entity_department: Mapped[str] = mapped_column(String(64))
    entity_municipality: Mapped[str | None] = mapped_column(String(128))
    supplier_name: Mapped[str] = mapped_column(Text)
    supplier_nit: Mapped[str | None] = mapped_column(String(32))
    supplier_is_natural_person: Mapped[bool] = mapped_column(Boolean)
    object_description: Mapped[str] = mapped_column(Text)
    modality: Mapped[str] = mapped_column(String(96))
    total_value_cop: Mapped[int | None] = mapped_column(BigInteger)
    signed_on: Mapped[date] = mapped_column(Date, index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    items: Mapped[list["PurchaseItemRecord"]] = relationship(
        back_populates="purchase",
        cascade="all, delete-orphan",
        order_by="PurchaseItemRecord.line_number",
    )


class PurchaseItemRecord(Base):
    __tablename__ = "purchase_item"
    __table_args__ = (UniqueConstraint("purchase_id", "line_number"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    purchase_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.purchase.id", ondelete="CASCADE")
    )
    line_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    classification: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[int | None] = mapped_column(Integer)
    unit_price_cop: Mapped[int | None] = mapped_column(BigInteger)
    unit_price_status: Mapped[str] = mapped_column(String(32))
    vat_basis: Mapped[str] = mapped_column(String(32))
    screen_size_inches: Mapped[int | None] = mapped_column(Integer)
    resolution: Mapped[str | None] = mapped_column(String(16))
    panel: Mapped[str | None] = mapped_column(String(16))
    is_smart: Mapped[bool | None] = mapped_column(Boolean)
    brand: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(64))
    purchase: Mapped[PurchaseRecord] = relationship(back_populates="items")


class IngestionRunRecord(Base):
    __tablename__ = "ingestion_run"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(16), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    read_count: Mapped[int] = mapped_column(Integer)
    new_count: Mapped[int] = mapped_column(Integer)
    updated_count: Mapped[int] = mapped_column(Integer)


def _purchase_values(purchase: Purchase) -> dict[str, object]:
    return {
        "source": purchase.source.value,
        "id_contrato": purchase.id_contrato,
        "identificador_de_la_orden": purchase.identificador_de_la_orden,
        "proceso_de_compra": purchase.proceso_de_compra,
        "entity_name": purchase.entity_name,
        "entity_department": purchase.entity_department,
        "entity_municipality": purchase.entity_municipality,
        "supplier_name": purchase.supplier_name,
        "supplier_nit": purchase.supplier_nit,
        "supplier_is_natural_person": purchase.supplier_is_natural_person,
        "object_description": purchase.object_description,
        "modality": purchase.modality,
        "total_value_cop": purchase.total_value_cop,
        "signed_on": purchase.signed_on,
        "source_url": purchase.source_url,
    }


def _item_values(item: PurchaseItem) -> dict[str, object]:
    attributes = item.attributes
    return {
        "line_number": item.line_number,
        "description": item.description,
        "classification": item.classification.value,
        "quantity": item.quantity,
        "unit_price_cop": item.unit_price_cop,
        "unit_price_status": item.unit_price_status.value,
        "vat_basis": item.vat_basis.value,
        "screen_size_inches": attributes.screen_size_inches,
        "resolution": attributes.resolution.value if attributes.resolution else None,
        "panel": attributes.panel.value if attributes.panel else None,
        "is_smart": attributes.is_smart,
        "brand": attributes.brand,
        "model": attributes.model,
    }


def _apply(record: object, values: dict[str, object]) -> bool:
    changed = False
    for name, value in values.items():
        if getattr(record, name) != value:
            setattr(record, name, value)
            changed = True
    return changed


def to_domain_item(record: PurchaseItemRecord) -> PurchaseItem:
    return PurchaseItem(
        line_number=record.line_number,
        description=record.description,
        classification=ItemClassification(record.classification),
        quantity=record.quantity,
        unit_price_cop=record.unit_price_cop,
        unit_price_status=UnitPriceStatus(record.unit_price_status),
        vat_basis=VatBasis(record.vat_basis),
        attributes=TvAttributes(
            screen_size_inches=record.screen_size_inches,
            resolution=Resolution(record.resolution) if record.resolution else None,
            panel=Panel(record.panel) if record.panel else None,
            is_smart=record.is_smart,
            brand=record.brand,
            model=record.model,
        ),
    )


def to_domain_purchase(record: PurchaseRecord) -> Purchase:
    return Purchase(
        source=Source(record.source),
        id_contrato=record.id_contrato,
        identificador_de_la_orden=record.identificador_de_la_orden,
        proceso_de_compra=record.proceso_de_compra,
        entity_name=record.entity_name,
        entity_department=record.entity_department,
        entity_municipality=record.entity_municipality,
        supplier_name=record.supplier_name,
        supplier_nit=record.supplier_nit,
        supplier_is_natural_person=record.supplier_is_natural_person,
        object_description=record.object_description,
        modality=record.modality,
        total_value_cop=record.total_value_cop,
        signed_on=record.signed_on,
        source_url=record.source_url,
        items=tuple(to_domain_item(item) for item in record.items),
    )


def _record_key(record: PurchaseRecord) -> str:
    identifier = (
        record.id_contrato
        if record.source == Source.SECOP_II.value
        else record.identificador_de_la_orden
    )
    return identifier or ""


class SqlPurchaseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_all(self, source: Source, purchases: list[Purchase]) -> tuple[int, int]:
        """Inserta o actualiza por identidad de origen; devuelve (nuevas, actualizadas)."""
        existing = {
            _record_key(record): record
            for record in self._session.scalars(
                select(PurchaseRecord)
                .where(PurchaseRecord.source == source.value)
                .options(selectinload(PurchaseRecord.items))
            )
        }
        new_count = updated_count = 0
        for purchase in purchases:
            record = existing.get(purchase.source_record_id)
            if record is None:
                record = PurchaseRecord(**_purchase_values(purchase))
                record.items = [PurchaseItemRecord(**_item_values(item)) for item in purchase.items]
                self._session.add(record)
                new_count += 1
                continue
            changed = _apply(record, _purchase_values(purchase))
            items_by_line = {item.line_number: item for item in record.items}
            for item in purchase.items:
                item_record = items_by_line.pop(item.line_number, None)
                if item_record is None:
                    record.items.append(PurchaseItemRecord(**_item_values(item)))
                    changed = True
                else:
                    changed = _apply(item_record, _item_values(item)) or changed
            for orphan in items_by_line.values():
                record.items.remove(orphan)
                changed = True
            updated_count += int(changed)
        self._session.flush()
        return new_count, updated_count

    def add_run(self, run: IngestionRunResult) -> None:
        self._session.add(
            IngestionRunRecord(
                source=run.source.value,
                started_at=run.started_at,
                finished_at=run.finished_at,
                cutoff_at=run.cutoff_at,
                read_count=run.read_count,
                new_count=run.new_count,
                updated_count=run.updated_count,
            )
        )
        self._session.flush()


# Búsqueda sin tildes con funciones del núcleo de PostgreSQL (no requiere la extensión unaccent).
_ACCENTED = "áéíóúüñ"
_PLAIN = "aeiouun"
_SEARCHABLE_COLUMNS = (
    PurchaseRecord.entity_name,
    PurchaseRecord.supplier_name,
    PurchaseRecord.supplier_nit,
    PurchaseRecord.object_description,
    PurchaseRecord.id_contrato,
    PurchaseRecord.identificador_de_la_orden,
)


def _text_condition(text: str) -> ColumnElement[bool]:
    needle = normalize_text(text.strip())
    return or_(
        *(
            func.translate(func.lower(column), _ACCENTED, _PLAIN).contains(needle, autoescape=True)
            for column in _SEARCHABLE_COLUMNS
        )
    )


def _filtered(criteria: PurchaseSearchCriteria) -> Select[PurchaseRecord]:
    query = select(PurchaseRecord)
    if criteria.text and criteria.text.strip():
        query = query.where(_text_condition(criteria.text))
    if criteria.source:
        query = query.where(PurchaseRecord.source == criteria.source.value)
    if criteria.modality:
        query = query.where(PurchaseRecord.modality == criteria.modality)
    if criteria.department:
        query = query.where(PurchaseRecord.entity_department == criteria.department)
    if criteria.value_range is ValueRange.LT_20M:
        query = query.where(PurchaseRecord.total_value_cop < LOW_VALUE_LIMIT_COP)
    elif criteria.value_range is ValueRange.BETWEEN_20M_100M:
        query = query.where(
            PurchaseRecord.total_value_cop.between(LOW_VALUE_LIMIT_COP, HIGH_VALUE_LIMIT_COP)
        )
    elif criteria.value_range is ValueRange.GT_100M:
        query = query.where(PurchaseRecord.total_value_cop > HIGH_VALUE_LIMIT_COP)
    if criteria.signed_from:
        query = query.where(PurchaseRecord.signed_on >= criteria.signed_from)
    if criteria.signed_to:
        query = query.where(PurchaseRecord.signed_on <= criteria.signed_to)
    if criteria.purchase_ids is not None:
        query = query.where(PurchaseRecord.id.in_(criteria.purchase_ids))
    if criteria.exclude_purchase_ids:
        query = query.where(PurchaseRecord.id.not_in(criteria.exclude_purchase_ids))
    return query


_ORDER: dict[PurchaseSort, ColumnElement[Any]] = {
    PurchaseSort.SIGNED_DESC: PurchaseRecord.signed_on.desc(),
    PurchaseSort.SIGNED_ASC: PurchaseRecord.signed_on.asc(),
    PurchaseSort.VALUE_DESC: PurchaseRecord.total_value_cop.desc().nulls_last(),
    PurchaseSort.VALUE_ASC: PurchaseRecord.total_value_cop.asc().nulls_last(),
}


class SqlPurchaseQueries:
    """Consultas de solo lectura sobre las compras; una sesión por consulta."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def search(self, criteria: PurchaseSearchCriteria) -> PurchasePage:
        filtered = _filtered(criteria)
        with self._session_factory() as session:
            total = session.scalar(select(func.count()).select_from(filtered.subquery())) or 0
            records = session.scalars(
                filtered.options(selectinload(PurchaseRecord.items))
                .order_by(_ORDER[criteria.sort], PurchaseRecord.id)
                .offset(criteria.offset)
                .limit(criteria.page_size)
            ).all()
            items = tuple(
                StoredPurchase(record.id, to_domain_purchase(record)) for record in records
            )
        return PurchasePage(
            items=items, total=total, page=criteria.page, page_size=criteria.page_size
        )

    def get_many(self, purchase_ids: list[uuid.UUID]) -> dict[uuid.UUID, StoredPurchase]:
        if not purchase_ids:
            return {}
        with self._session_factory() as session:
            records = session.scalars(
                select(PurchaseRecord)
                .where(PurchaseRecord.id.in_(purchase_ids))
                .options(selectinload(PurchaseRecord.items))
            ).all()
            return {
                record.id: StoredPurchase(record.id, to_domain_purchase(record))
                for record in records
            }

    def tv_purchase_counts(self) -> dict[Source, int]:
        """Compras con al menos un ítem de televisor, por fuente."""
        has_tv = (
            select(PurchaseItemRecord.purchase_id)
            .where(PurchaseItemRecord.classification == ItemClassification.INCLUDED.value)
            .distinct()
        )
        with self._session_factory() as session:
            rows = session.execute(
                select(PurchaseRecord.source, func.count())
                .where(PurchaseRecord.id.in_(has_tv))
                .group_by(PurchaseRecord.source)
            ).tuples()
            return {Source(source): count for source, count in rows}

    def all_purchases(self) -> tuple[StoredPurchase, ...]:
        with self._session_factory() as session:
            records = session.scalars(
                select(PurchaseRecord).options(selectinload(PurchaseRecord.items))
            ).all()
            return tuple(
                StoredPurchase(record.id, to_domain_purchase(record)) for record in records
            )

    def get(self, purchase_id: uuid.UUID) -> StoredPurchase | None:
        with self._session_factory() as session:
            record = session.scalars(
                select(PurchaseRecord)
                .where(PurchaseRecord.id == purchase_id)
                .options(selectinload(PurchaseRecord.items))
            ).one_or_none()
            return None if record is None else StoredPurchase(record.id, to_domain_purchase(record))

    def latest_cutoff(self) -> datetime | None:
        with self._session_factory() as session:
            return session.scalar(select(func.max(IngestionRunRecord.cutoff_at)))

    def filter_options(self) -> PurchaseFilterOptions:
        with self._session_factory() as session:
            sources = session.scalars(
                select(PurchaseRecord.source).distinct().order_by(PurchaseRecord.source)
            ).all()
            modalities = session.scalars(
                select(PurchaseRecord.modality).distinct().order_by(PurchaseRecord.modality)
            ).all()
            departments = session.scalars(
                select(PurchaseRecord.entity_department)
                .distinct()
                .order_by(PurchaseRecord.entity_department)
            ).all()
        return PurchaseFilterOptions(
            sources=tuple(Source(source) for source in sources),
            modalities=tuple(modalities),
            departments=tuple(departments),
            data_cutoff_at=self.latest_cutoff(),
        )
