"""Persistencia de la comparación en el esquema `comparison`.

Resultados de solo inserción: cada recálculo inserta una fila por ítem con `config_version_id` y
solo cambia el metadato de vigencia (`is_current`) de las anteriores, nunca sus valores (ADR-012).
"""

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from public_procurement.shared.persistence import Base

from .domain.evaluation import ItemEvaluation, Outcome
from .domain.statistics import to_cop

SCHEMA = "comparison"


class ComparisonRunRecord(Base):
    __tablename__ = "comparison_run"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    config_version_id: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evaluated_count: Mapped[int] = mapped_column(Integer)
    signal_count: Mapped[int] = mapped_column(Integer)


class ItemComparisonRecord(Base):
    __tablename__ = "item_comparison"
    __table_args__ = (
        Index("ix_comparison_item_comparison_current_outcome", "is_current", "outcome"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.comparison_run.id"))
    config_version_id: Mapped[str] = mapped_column(String(32))
    is_current: Mapped[bool] = mapped_column(Boolean)
    # Identificadores estables de la compra (otro esquema: sin llave foránea).
    purchase_id: Mapped[uuid.UUID] = mapped_column(index=True)
    line_number: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(32))
    signal_code: Mapped[str | None] = mapped_column(String(32), index=True)
    unit_price_cop: Mapped[int | None] = mapped_column(BigInteger)
    match_type: Mapped[str | None] = mapped_column(String(16))
    window_months: Mapped[int | None] = mapped_column(Integer)
    comparable_count: Mapped[int] = mapped_column(Integer)
    threshold_rule: Mapped[str | None] = mapped_column(String(16))
    q1_cop: Mapped[int | None] = mapped_column(BigInteger)
    median_cop: Mapped[int | None] = mapped_column(BigInteger)
    q3_cop: Mapped[int | None] = mapped_column(BigInteger)
    threshold_cop: Mapped[int | None] = mapped_column(BigInteger)
    low_threshold_cop: Mapped[int | None] = mapped_column(BigInteger)
    deviation_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 1))
    market_status: Mapped[str | None] = mapped_column(String(16))
    market_reference_cop: Mapped[int | None] = mapped_column(BigInteger)
    market_deviation_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 1))
    market_observation_count: Mapped[int] = mapped_column(Integer)
    market_store_count: Mapped[int] = mapped_column(Integer)
    confidence_score: Mapped[int | None] = mapped_column(Integer)
    confidence_level: Mapped[str | None] = mapped_column(String(16))
    penalties: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ItemComparableRecord(Base):
    """Vínculo con cada compra comparable usada (con copia de lo que se mostró)."""

    __tablename__ = "item_comparable"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    comparison_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.item_comparison.id"), index=True
    )
    purchase_id: Mapped[uuid.UUID] = mapped_column()
    line_number: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(16))
    reference: Mapped[str] = mapped_column(String(64))
    entity_name: Mapped[str] = mapped_column(Text)
    signed_on: Mapped[date] = mapped_column(Date)
    unit_price_cop: Mapped[int] = mapped_column(BigInteger)
    same_model: Mapped[bool] = mapped_column(Boolean)


class ItemMarketObservationRecord(Base):
    """Vínculo con cada observación de mercado usada en el Benchmark 2."""

    __tablename__ = "item_market_observation"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    comparison_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.item_comparison.id"), index=True
    )
    observation_id: Mapped[uuid.UUID] = mapped_column()
    effective_price_cop: Mapped[int] = mapped_column(BigInteger)


def _comparison_record(
    run_id: uuid.UUID, config_version_id: str, evaluation: ItemEvaluation, signal_code: str | None
) -> ItemComparisonRecord:
    target, selection, reference = evaluation.target, evaluation.selection, evaluation.reference
    market, confidence = evaluation.market, evaluation.confidence
    distribution = reference.distribution if reference else None
    return ItemComparisonRecord(
        id=uuid.uuid4(),
        run_id=run_id,
        config_version_id=config_version_id,
        is_current=True,
        purchase_id=target.purchase_id,
        line_number=target.line_number,
        outcome=evaluation.outcome.value,
        signal_code=signal_code,
        unit_price_cop=target.unit_price_cop,
        match_type=selection.match_type.value if selection else None,
        window_months=selection.window_months if selection else None,
        comparable_count=len(selection.comparables) if selection else 0,
        threshold_rule=reference.rule.value if reference else None,
        q1_cop=to_cop(distribution.q1) if distribution else None,
        median_cop=to_cop(distribution.median) if distribution else None,
        q3_cop=to_cop(distribution.q3) if distribution else None,
        threshold_cop=reference.threshold_cop if reference else None,
        low_threshold_cop=reference.low_threshold_cop if reference else None,
        deviation_pct=reference.deviation_pct if reference else None,
        market_status=market.status.value if market else None,
        market_reference_cop=market.reference_cop if market else None,
        market_deviation_pct=market.deviation_pct if market else None,
        market_observation_count=len(market.observations) if market else 0,
        market_store_count=market.store_count if market else 0,
        confidence_score=confidence.score if confidence else None,
        confidence_level=confidence.level.value if confidence else None,
        penalties=[
            {"code": p.code.value, "label": p.label, "points": p.points}
            for p in (confidence.penalties if confidence else ())
        ],
    )


class SqlComparisonRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_run(
        self,
        run: ComparisonRunRecord,
        evaluations: list[ItemEvaluation],
        signal_codes: dict[tuple[uuid.UUID, int], str],
    ) -> None:
        # Las versiones anteriores dejan de ser vigentes; sus valores no se tocan.
        self._session.execute(
            update(ItemComparisonRecord)
            .where(ItemComparisonRecord.is_current)
            .values(is_current=False)
        )
        self._session.add(run)
        self._session.flush()
        records = [
            _comparison_record(
                run.id,
                run.config_version_id,
                evaluation,
                signal_codes.get((evaluation.target.purchase_id, evaluation.target.line_number)),
            )
            for evaluation in evaluations
        ]
        self._session.add_all(records)
        self._session.flush()  # los vínculos necesitan las comparaciones ya insertadas
        for record, evaluation in zip(records, evaluations, strict=True):
            self._session.add_all(_links(record.id, evaluation))
        self._session.flush()


def _links(
    comparison_id: uuid.UUID, evaluation: ItemEvaluation
) -> list[ItemComparableRecord | ItemMarketObservationRecord]:
    links: list[ItemComparableRecord | ItemMarketObservationRecord] = []
    target = evaluation.target
    if evaluation.selection and evaluation.reference:
        # Los comparables siempre tienen precio (lo exige la selección); sin precio no se vinculan.
        links.extend(
            ItemComparableRecord(
                comparison_id=comparison_id,
                purchase_id=comparable.purchase_id,
                line_number=comparable.line_number,
                source=comparable.source,
                reference=comparable.reference,
                entity_name=comparable.entity_name,
                signed_on=comparable.signed_on,
                unit_price_cop=comparable.unit_price_cop,
                same_model=comparable.model_key is not None
                and comparable.model_key == target.model_key,
            )
            for comparable in evaluation.selection.comparables
            if comparable.unit_price_cop is not None
        )
    if evaluation.market:
        links.extend(
            ItemMarketObservationRecord(
                comparison_id=comparison_id,
                observation_id=observation.observation_id,
                effective_price_cop=observation.effective_price_cop,
            )
            for observation in evaluation.market.observations
        )
    return links


@dataclass(frozen=True)
class CurrentSignal:
    record: ItemComparisonRecord
    comparables: list[ItemComparableRecord]
    observations: list[ItemMarketObservationRecord]


class SqlComparisonQueries:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def current_outcomes(
        self, purchase_ids: list[uuid.UUID] | None = None
    ) -> dict[uuid.UUID, list[Outcome]]:
        query = select(ItemComparisonRecord.purchase_id, ItemComparisonRecord.outcome).where(
            ItemComparisonRecord.is_current
        )
        if purchase_ids is not None:
            query = query.where(ItemComparisonRecord.purchase_id.in_(purchase_ids))
        outcomes: dict[uuid.UUID, list[Outcome]] = {}
        with self._session_factory() as session:
            for purchase_id, outcome in session.execute(query).tuples():
                outcomes.setdefault(purchase_id, []).append(Outcome(outcome))
        return outcomes

    def signal_purchase_ids(self) -> frozenset[uuid.UUID]:
        with self._session_factory() as session:
            ids = session.scalars(
                select(ItemComparisonRecord.purchase_id)
                .where(ItemComparisonRecord.is_current)
                .where(ItemComparisonRecord.outcome == Outcome.SIGNAL.value)
                .distinct()
            ).all()
        return frozenset(ids)

    def current_signals(self) -> list[ItemComparisonRecord]:
        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(ItemComparisonRecord)
                    .where(ItemComparisonRecord.is_current)
                    .where(ItemComparisonRecord.outcome == Outcome.SIGNAL.value)
                ).all()
            )

    def current_counts(self) -> tuple[dict[Outcome, int], dict[str, int]]:
        """Ítems vigentes por resultado y señales vigentes por nivel de confianza."""
        with self._session_factory() as session:
            by_outcome = {
                Outcome(outcome): count
                for outcome, count in session.execute(
                    select(ItemComparisonRecord.outcome, func.count())
                    .where(ItemComparisonRecord.is_current)
                    .group_by(ItemComparisonRecord.outcome)
                ).tuples()
            }
            by_confidence = {
                str(level): count
                for level, count in session.execute(
                    select(ItemComparisonRecord.confidence_level, func.count())
                    .where(ItemComparisonRecord.is_current)
                    .where(ItemComparisonRecord.outcome == Outcome.SIGNAL.value)
                    .group_by(ItemComparisonRecord.confidence_level)
                ).tuples()
            }
        return by_outcome, by_confidence

    def current_by_code(self, code: str) -> CurrentSignal | None:
        """Resultado vigente de una señal con sus vínculos (comparables y observaciones)."""
        with self._session_factory() as session:
            record = session.scalars(
                select(ItemComparisonRecord)
                .where(ItemComparisonRecord.is_current)
                .where(ItemComparisonRecord.signal_code == code)
            ).one_or_none()
            if record is None:
                return None
            comparables = list(
                session.scalars(
                    select(ItemComparableRecord)
                    .where(ItemComparableRecord.comparison_id == record.id)
                    .order_by(ItemComparableRecord.unit_price_cop)
                ).all()
            )
            observations = list(
                session.scalars(
                    select(ItemMarketObservationRecord).where(
                        ItemMarketObservationRecord.comparison_id == record.id
                    )
                ).all()
            )
        return CurrentSignal(record, comparables, observations)

    def item_results(self, purchase_id: uuid.UUID) -> list[tuple[int, Outcome, str | None]]:
        with self._session_factory() as session:
            rows = session.execute(
                select(
                    ItemComparisonRecord.line_number,
                    ItemComparisonRecord.outcome,
                    ItemComparisonRecord.signal_code,
                )
                .where(ItemComparisonRecord.is_current)
                .where(ItemComparisonRecord.purchase_id == purchase_id)
            ).tuples()
            return [(line, Outcome(outcome), code) for line, outcome, code in rows]

    def latest_run(self) -> ComparisonRunRecord | None:
        with self._session_factory() as session:
            return session.scalars(
                select(ComparisonRunRecord)
                .order_by(ComparisonRunRecord.finished_at.desc())
                .limit(1)
            ).one_or_none()
