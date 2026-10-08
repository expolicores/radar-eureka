"""Persistencia del mercado en el esquema `market`: observaciones de solo inserción."""

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.schema import UniqueConstraint

from public_procurement.shared.persistence import Base

from .domain.observation import (
    AcquisitionMethod,
    MarketObservation,
    MarketVatBasis,
    Store,
    StoredObservation,
)

SCHEMA = "market"


class ObservationRecord(Base):
    __tablename__ = "observation"
    __table_args__ = (UniqueConstraint("store", "source_reference"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    store: Mapped[str] = mapped_column(String(32))
    source_reference: Mapped[str] = mapped_column(String(128))
    product_description: Mapped[str] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(64))
    ean: Mapped[str | None] = mapped_column(String(14))
    screen_size_inches: Mapped[int] = mapped_column(Integer)
    resolution: Mapped[str] = mapped_column(String(16))
    panel: Mapped[str] = mapped_column(String(16))
    effective_price_cop: Mapped[int] = mapped_column(BigInteger)
    list_price_cop: Mapped[int | None] = mapped_column(BigInteger)
    vat_basis: Mapped[str] = mapped_column(String(16))
    seller_is_store: Mapped[bool] = mapped_column(Boolean)
    has_special_conditions: Mapped[bool] = mapped_column(Boolean)
    observed_on: Mapped[date] = mapped_column(Date, index=True)
    method: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def _values(observation: MarketObservation) -> dict[str, object]:
    return {
        "store": observation.store.value,
        "source_reference": observation.source_reference,
        "product_description": observation.product_description,
        "brand": observation.brand,
        "model": observation.model,
        "ean": observation.ean,
        "screen_size_inches": observation.screen_size_inches,
        "resolution": observation.resolution,
        "panel": observation.panel,
        "effective_price_cop": observation.effective_price_cop,
        "list_price_cop": observation.list_price_cop,
        "vat_basis": observation.vat_basis.value,
        "seller_is_store": observation.seller_is_store,
        "has_special_conditions": observation.has_special_conditions,
        "observed_on": observation.observed_on,
        "method": observation.method.value,
    }


def to_domain_observation(record: ObservationRecord) -> StoredObservation:
    return StoredObservation(
        id=record.id,
        observation=MarketObservation(
            store=Store(record.store),
            source_reference=record.source_reference,
            product_description=record.product_description,
            brand=record.brand,
            model=record.model,
            ean=record.ean,
            screen_size_inches=record.screen_size_inches,
            resolution=record.resolution,
            panel=record.panel,
            effective_price_cop=record.effective_price_cop,
            list_price_cop=record.list_price_cop,
            vat_basis=MarketVatBasis(record.vat_basis),
            seller_is_store=record.seller_is_store,
            has_special_conditions=record.has_special_conditions,
            observed_on=record.observed_on,
            method=AcquisitionMethod(record.method),
        ),
    )


class SqlObservationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_new(self, observations: list[MarketObservation]) -> int:
        """Inserta solo las nuevas (tienda + referencia), nunca sobrescribe; devuelve cuántas."""
        existing = {
            (store, reference)
            for store, reference in self._session.execute(
                select(ObservationRecord.store, ObservationRecord.source_reference)
            ).tuples()
        }
        new = [
            ObservationRecord(**_values(observation))
            for observation in observations
            if (observation.store.value, observation.source_reference) not in existing
        ]
        self._session.add_all(new)
        self._session.flush()
        return len(new)


class SqlObservationQueries:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def all_observations(self) -> tuple[StoredObservation, ...]:
        with self._session_factory() as session:
            records = session.scalars(
                select(ObservationRecord).order_by(ObservationRecord.observed_on)
            ).all()
            return tuple(to_domain_observation(record) for record in records)

    def get_many(self, ids: list[uuid.UUID]) -> tuple[StoredObservation, ...]:
        if not ids:
            return ()
        with self._session_factory() as session:
            records = session.scalars(
                select(ObservationRecord)
                .where(ObservationRecord.id.in_(ids))
                .order_by(ObservationRecord.observed_on)
            ).all()
            return tuple(to_domain_observation(record) for record in records)
