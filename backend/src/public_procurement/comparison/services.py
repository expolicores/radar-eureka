"""Servicios de comparación: recálculo de benchmarks y señales, y lectura de resultados vigentes.

Única puerta de entrada al módulo. Lee compras por `ingestion.services` y observaciones por
`market.services`; nunca sus tablas.
"""

import logging
import uuid
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.ingestion.services import (
    ItemClassification,
    PurchaseQueryService,
    StoredPurchase,
    build_purchase_query_service,
)
from public_procurement.market.services import (
    AcquisitionMethod,
    MarketQueryService,
    Store,
    StoredObservation,
    build_market_query_service,
)
from public_procurement.shared.logging import log_event

from .domain.benchmarks import MarketStatus
from .domain.confidence import ConfidenceLevel, Penalty
from .domain.config import DEFAULT_CONFIG, AnalysisConfig, PenaltyCode
from .domain.evaluation import ItemEvaluation, Outcome, ThresholdRule, evaluate_item
from .domain.facts import ItemFacts, MarketFacts, PriceStatus, PurchaseSource, TvSpec, VatBasis
from .domain.signal_code import signal_code
from .domain.signals import SignalFilters, SignalRow, SignalSort, select_signals
from .domain.summary import purchase_outcome
from .repositories import (
    ComparisonRunRecord,
    ItemComparableRecord,
    ItemComparisonRecord,
    SqlComparisonQueries,
    SqlComparisonRepository,
)

__all__ = [
    "DEFAULT_CONFIG",
    "AnalysisConfig",
    "ComparableView",
    "ComparisonQueryService",
    "ComparisonService",
    "ConfidenceLevel",
    "ItemResult",
    "MarketObservationView",
    "MarketStatus",
    "Outcome",
    "PenaltyCode",
    "PurchaseSource",
    "RunSummary",
    "SignalDetail",
    "SignalFilters",
    "SignalPage",
    "SignalQueryService",
    "SignalRow",
    "SignalSort",
    "SignalSummary",
    "ThresholdRule",
    "VatBasis",
    "build_comparison_query_service",
    "build_comparison_service",
    "build_signal_query_service",
]

logger = logging.getLogger("public_procurement.comparison.services")


@dataclass(frozen=True)
class RunSummary:
    id: uuid.UUID
    config_version_id: str
    evaluated_count: int
    signal_count: int
    outcomes: dict[Outcome, int]


def tv_item_facts(stored: StoredPurchase) -> list[ItemFacts]:
    purchase = stored.purchase
    return [
        ItemFacts(
            purchase_id=stored.id,
            line_number=item.line_number,
            source=PurchaseSource(purchase.source.value),
            source_record_id=purchase.source_record_id,
            reference=purchase.display_reference,
            entity_name=purchase.entity_name,
            signed_on=purchase.signed_on,
            unit_price_cop=item.unit_price_cop,
            price_status=PriceStatus(item.unit_price_status.value),
            vat_basis=VatBasis(item.vat_basis.value),
            spec=TvSpec(
                screen_size_inches=item.attributes.screen_size_inches,
                resolution=item.attributes.resolution.value if item.attributes.resolution else None,
                panel=item.attributes.panel.value if item.attributes.panel else None,
            ),
            brand=item.attributes.brand,
            model=item.attributes.model,
        )
        for item in purchase.items
        if item.classification is ItemClassification.INCLUDED
    ]


def market_facts(stored: StoredObservation) -> MarketFacts:
    observation = stored.observation
    return MarketFacts(
        observation_id=stored.id,
        store=observation.store.value,
        effective_price_cop=observation.effective_price_cop,
        vat_basis=VatBasis(observation.vat_basis.value),
        seller_is_store=observation.seller_is_store,
        has_special_conditions=observation.has_special_conditions,
        observed_on=observation.observed_on,
        spec=TvSpec(observation.screen_size_inches, observation.resolution, observation.panel),
    )


def assign_signal_codes(evaluations: list[ItemEvaluation]) -> dict[tuple[uuid.UUID, int], str]:
    signals = [evaluation for evaluation in evaluations if evaluation.is_signal]
    per_purchase = Counter(evaluation.target.purchase_id for evaluation in signals)
    codes: dict[tuple[uuid.UUID, int], str] = {}
    for evaluation in signals:
        target = evaluation.target
        line = target.line_number if per_purchase[target.purchase_id] > 1 else None
        codes[(target.purchase_id, target.line_number)] = signal_code(
            target.source, target.source_record_id, target.signed_on.year, line
        )
    return codes


class _SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.comparisons = SqlComparisonRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        finally:
            self._session.close()


class ComparisonService:
    def __init__(
        self,
        purchases: PurchaseQueryService,
        market: MarketQueryService,
        session_factory: sessionmaker[Session],
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._purchases = purchases
        self._market = market
        self._session_factory = session_factory
        self._clock = clock

    def recalculate(self, config: AnalysisConfig = DEFAULT_CONFIG) -> RunSummary:
        """Recalcula todas las comparaciones; inserta una nueva versión vigente (relanzable)."""
        started_at = self._clock()
        items = [
            facts for stored in self._purchases.all_purchases() for facts in tv_item_facts(stored)
        ]
        observations = [market_facts(stored) for stored in self._market.all_observations()]
        # Índices por televisor equivalente: cada ítem solo se compara con su grupo.
        items_by_spec: dict[TvSpec, list[ItemFacts]] = defaultdict(list)
        for item in items:
            items_by_spec[item.spec].append(item)
        observations_by_spec: dict[TvSpec, list[MarketFacts]] = defaultdict(list)
        for observation in observations:
            observations_by_spec[observation.spec].append(observation)

        evaluations = [
            evaluate_item(item, items_by_spec[item.spec], observations_by_spec[item.spec], config)
            for item in items
        ]
        codes = assign_signal_codes(evaluations)
        outcomes = Counter(evaluation.outcome for evaluation in evaluations)
        run = ComparisonRunRecord(
            id=uuid.uuid4(),
            config_version_id=config.id,
            started_at=started_at,
            finished_at=self._clock(),
            evaluated_count=len(evaluations),
            signal_count=outcomes[Outcome.SIGNAL],
        )
        with _SqlUnitOfWork(self._session_factory) as unit_of_work:
            unit_of_work.comparisons.save_run(run, evaluations, codes)
        log_event(
            logger,
            "comparison_run_finished",
            config_version_id=config.id,
            evaluated_count=run.evaluated_count,
            signal_count=run.signal_count,
        )
        return RunSummary(run.id, config.id, run.evaluated_count, run.signal_count, dict(outcomes))


@dataclass(frozen=True)
class ItemResult:
    outcome: Outcome
    signal_code: str | None


class ComparisonQueryService:
    """Lectura de resultados vigentes para otros módulos (exploración) y futuras herramientas."""

    def __init__(self, queries: SqlComparisonQueries) -> None:
        self._queries = queries

    def purchase_outcomes(self, purchase_ids: list[uuid.UUID]) -> dict[uuid.UUID, Outcome]:
        """Resultado vigente más relevante de cada compra (las no comparadas no aparecen)."""
        result: dict[uuid.UUID, Outcome] = {}
        for purchase_id, outcomes in self._queries.current_outcomes(purchase_ids).items():
            outcome = purchase_outcome(outcomes)
            if outcome is not None:
                result[purchase_id] = outcome
        return result

    def signal_purchase_ids(self) -> frozenset[uuid.UUID]:
        return self._queries.signal_purchase_ids()

    def item_results(self, purchase_id: uuid.UUID) -> dict[int, ItemResult]:
        """Resultado vigente por línea de la compra (ítems de televisor comparados)."""
        return {
            line: ItemResult(outcome, code)
            for line, outcome, code in self._queries.item_results(purchase_id)
        }


def build_comparison_service(session_factory: sessionmaker[Session]) -> ComparisonService:
    return ComparisonService(
        build_purchase_query_service(session_factory),
        build_market_query_service(session_factory),
        session_factory,
    )


def build_comparison_query_service(
    session_factory: sessionmaker[Session],
) -> ComparisonQueryService:
    return ComparisonQueryService(SqlComparisonQueries(session_factory))


RESOLUTION_LABELS = {"hd": "HD", "full_hd": "Full HD", "uhd_4k": "4K", "uhd_8k": "8K"}
PANEL_LABELS = {"led": "LED", "qled": "QLED", "oled": "OLED"}


@dataclass(frozen=True)
class SignalPage:
    items: tuple[SignalRow, ...]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class SignalSummary:
    """Indicadores de la lista de señales (recálculo vigente)."""

    tv_purchases_by_source: dict[str, int]
    signals_by_confidence: dict[ConfidenceLevel, int]
    incomplete_comparisons: int
    without_source_information: int
    config_version_id: str | None
    data_cutoff_at: datetime | None

    @property
    def tv_purchases(self) -> int:
        return sum(self.tv_purchases_by_source.values())

    @property
    def signals(self) -> int:
        return sum(self.signals_by_confidence.values())


def _item_label(stored: StoredPurchase, line_number: int) -> tuple[str, int | None]:
    item = next(i for i in stored.purchase.items if i.line_number == line_number)
    attributes = item.attributes
    parts = ["TV"]
    if attributes.screen_size_inches:
        parts.append(f'{attributes.screen_size_inches}"')
    if attributes.resolution:
        parts.append(
            RESOLUTION_LABELS.get(attributes.resolution.value, attributes.resolution.value)
        )
    if attributes.panel:
        parts.append(PANEL_LABELS.get(attributes.panel.value, attributes.panel.value))
    label = " ".join(parts)
    if attributes.model:
        label += f" · mod. {attributes.model}"
    return label, item.quantity


def _required[T](value: T | None, field: str) -> T:
    """Una señal siempre tiene precio, referencia y confianza: si faltan, el dato está corrupto."""
    if value is None:
        raise ValueError(f"signal_without_{field}")
    return value


def _signal_row(record: ItemComparisonRecord, stored: StoredPurchase) -> SignalRow:
    purchase = stored.purchase
    description, quantity = _item_label(stored, record.line_number)
    return SignalRow(
        code=_required(record.signal_code, "code"),
        purchase_id=record.purchase_id,
        line_number=record.line_number,
        purchase_reference=purchase.display_reference,
        source=purchase.source.value,
        entity_name=purchase.entity_name,
        entity_department=purchase.entity_department,
        supplier_name=purchase.supplier_name,
        supplier_nit=purchase.supplier_nit,
        item_description=description,
        quantity=quantity,
        unit_price_cop=_required(record.unit_price_cop, "unit_price"),
        median_cop=_required(record.median_cop, "median"),
        deviation_pct=_required(record.deviation_pct, "deviation"),
        match_type=_required(record.match_type, "match_type"),
        confidence_level=ConfidenceLevel(_required(record.confidence_level, "confidence")),
        confidence_score=_required(record.confidence_score, "confidence_score"),
        signed_on=purchase.signed_on,
    )


@dataclass(frozen=True)
class ComparableView:
    purchase_id: uuid.UUID
    source: PurchaseSource
    reference: str
    entity_name: str
    signed_on: date
    unit_price_cop: int
    same_model: bool


@dataclass(frozen=True)
class MarketObservationView:
    store: Store
    product_description: str
    effective_price_cop: int
    list_price_cop: int | None
    observed_on: date
    method: AcquisitionMethod


@dataclass(frozen=True)
class SignalDetail:
    """Todo lo que explica una señal (FR-065), leído de lo guardado en el recálculo vigente."""

    signal: SignalRow
    modality: str
    vat_basis: VatBasis
    config_version_id: str
    threshold_rule: ThresholdRule
    window_months: int
    q1_cop: int
    q3_cop: int
    threshold_cop: int
    comparables: tuple[ComparableView, ...]
    market_status: MarketStatus
    market_reference_cop: int | None
    market_deviation_pct: Decimal | None
    market_observations: tuple[MarketObservationView, ...]
    penalties: tuple[Penalty, ...]
    data_cutoff_at: datetime | None


def _comparable_view(record: ItemComparableRecord) -> ComparableView:
    return ComparableView(
        purchase_id=record.purchase_id,
        source=PurchaseSource(record.source),
        reference=record.reference,
        entity_name=record.entity_name,
        signed_on=record.signed_on,
        unit_price_cop=record.unit_price_cop,
        same_model=record.same_model,
    )


def _observation_view(stored: StoredObservation) -> MarketObservationView:
    observation = stored.observation
    return MarketObservationView(
        store=observation.store,
        product_description=observation.product_description,
        effective_price_cop=observation.effective_price_cop,
        list_price_cop=observation.list_price_cop,
        observed_on=observation.observed_on,
        method=observation.method,
    )


class SignalQueryService:
    """Lista priorizada, indicadores y detalle de señales vigentes (API y futuras herramientas)."""

    def __init__(
        self,
        queries: SqlComparisonQueries,
        purchases: PurchaseQueryService,
        market: MarketQueryService,
    ) -> None:
        self._queries = queries
        self._purchases = purchases
        self._market = market

    def get_signal(self, code: str) -> SignalDetail | None:
        found = self._queries.current_by_code(code)
        if found is None:
            return None
        record = found.record
        stored = self._purchases.get(record.purchase_id)
        if stored is None:
            return None
        item = next(i for i in stored.purchase.items if i.line_number == record.line_number)
        observations = self._market.get_many([link.observation_id for link in found.observations])
        return SignalDetail(
            signal=_signal_row(record, stored),
            modality=stored.purchase.modality,
            vat_basis=VatBasis(item.vat_basis.value),
            config_version_id=record.config_version_id,
            threshold_rule=ThresholdRule(_required(record.threshold_rule, "threshold_rule")),
            window_months=_required(record.window_months, "window"),
            q1_cop=_required(record.q1_cop, "q1"),
            q3_cop=_required(record.q3_cop, "q3"),
            threshold_cop=_required(record.threshold_cop, "threshold"),
            comparables=tuple(_comparable_view(c) for c in found.comparables),
            market_status=MarketStatus(_required(record.market_status, "market_status")),
            market_reference_cop=record.market_reference_cop,
            market_deviation_pct=record.market_deviation_pct,
            market_observations=tuple(_observation_view(o) for o in observations),
            penalties=tuple(
                Penalty(PenaltyCode(p["code"]), str(p["label"]), int(p["points"]))
                for p in record.penalties
            ),
            data_cutoff_at=self._purchases.latest_cutoff(),
        )

    def _rows(self) -> list[SignalRow]:
        records = self._queries.current_signals()
        purchases = self._purchases.get_many([record.purchase_id for record in records])
        return [
            _signal_row(record, purchases[record.purchase_id])
            for record in records
            if record.purchase_id in purchases
        ]

    def list_signals(
        self, filters: SignalFilters, sort: SignalSort, page: int, page_size: int
    ) -> SignalPage:
        rows = select_signals(self._rows(), filters, sort)
        start = (page - 1) * page_size
        return SignalPage(tuple(rows[start : start + page_size]), len(rows), page, page_size)

    def summary(self) -> SignalSummary:
        by_outcome, by_confidence = self._queries.current_counts()
        run = self._queries.latest_run()
        return SignalSummary(
            tv_purchases_by_source={
                source.value: count
                for source, count in self._purchases.tv_purchase_counts().items()
            },
            signals_by_confidence={
                level: by_confidence.get(level.value, 0) for level in ConfidenceLevel
            },
            incomplete_comparisons=by_outcome.get(Outcome.VAT_INCOMPLETE, 0)
            + by_outcome.get(Outcome.INSUFFICIENT_COMPARABLES, 0),
            without_source_information=by_outcome.get(Outcome.NO_UNIT_PRICE, 0),
            config_version_id=run.config_version_id if run else None,
            data_cutoff_at=self._purchases.latest_cutoff(),
        )


def build_signal_query_service(session_factory: sessionmaker[Session]) -> SignalQueryService:
    return SignalQueryService(
        SqlComparisonQueries(session_factory),
        build_purchase_query_service(session_factory),
        build_market_query_service(session_factory),
    )
