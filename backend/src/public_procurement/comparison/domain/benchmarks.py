"""Selección de comparables (Benchmark 1) y observaciones de mercado (Benchmark 2)."""

import calendar
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum

from .config import AnalysisConfig
from .facts import ItemFacts, MarketFacts, PriceStatus, VatBasis
from .statistics import Distribution, deviation_pct, to_cop

COMPARABLE_PRICE_STATUSES = frozenset({PriceStatus.EXPLICIT, PriceStatus.DERIVED})


class MatchType(StrEnum):
    SAME_MODEL = "same_model"
    EQUIVALENT = "equivalent"


class MarketStatus(StrEnum):
    REFERENCE = "reference"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def is_comparable_candidate(target: ItemFacts, candidate: ItemFacts) -> bool:
    """Otra compra, mismo televisor equivalente, precio utilizable y misma base tributaria."""
    return (
        candidate.purchase_id != target.purchase_id
        and target.spec.is_complete
        and candidate.spec == target.spec
        and candidate.unit_price_cop is not None
        and candidate.price_status in COMPARABLE_PRICE_STATUSES
        and candidate.vat_basis is VatBasis.INCLUDED
    )


def _within(target: date, candidate: date, months: int) -> bool:
    return add_months(target, -months) <= candidate <= add_months(target, months)


@dataclass(frozen=True)
class ComparableSelection:
    comparables: tuple[ItemFacts, ...]
    match_type: MatchType
    window_months: int


def select_comparables(
    target: ItemFacts, candidates: Iterable[ItemFacts], config: AnalysisConfig
) -> ComparableSelection:
    """Mismo modelo si alcanza el mínimo; si no, equivalentes. Ventana ±6 meses, ampliable a ±12."""
    pool = [c for c in candidates if is_comparable_candidate(target, c)]
    for months in (config.window_months, config.extended_window_months):
        in_window = [c for c in pool if _within(target.signed_on, c.signed_on, months)]
        same_model = [c for c in in_window if target.model_key and c.model_key == target.model_key]
        if len(same_model) >= config.min_comparables:
            return ComparableSelection(tuple(same_model), MatchType.SAME_MODEL, months)
        if len(in_window) >= config.min_comparables:
            return ComparableSelection(tuple(in_window), MatchType.EQUIVALENT, months)
    in_window = [
        c for c in pool if _within(target.signed_on, c.signed_on, config.extended_window_months)
    ]
    return ComparableSelection(
        tuple(in_window), MatchType.EQUIVALENT, config.extended_window_months
    )


def distribution_of(comparables: Sequence[ItemFacts]) -> Distribution:
    return Distribution.of([c.unit_price_cop for c in comparables if c.unit_price_cop is not None])


@dataclass(frozen=True)
class MarketBenchmark:
    status: MarketStatus
    observations: tuple[MarketFacts, ...]
    reference_cop: int | None
    deviation_pct: Decimal | None

    @property
    def store_count(self) -> int:
        return len({observation.store for observation in self.observations})


def is_usable_observation(
    target: ItemFacts, observation: MarketFacts, config: AnalysisConfig
) -> bool:
    window = timedelta(days=config.market_window_days)
    return (
        observation.spec == target.spec
        and observation.seller_is_store
        and not observation.has_special_conditions
        and observation.vat_basis is VatBasis.INCLUDED
        and abs(observation.observed_on - target.signed_on) <= window
    )


def evaluate_market(
    target: ItemFacts, observations: Iterable[MarketFacts], config: AnalysisConfig
) -> MarketBenchmark:
    """Referencia con ≥ 3 observaciones de ≥ 2 tiendas; si no, limitada o no disponible."""
    usable = tuple(o for o in observations if is_usable_observation(target, o, config))
    price = target.unit_price_cop
    if not usable or price is None:
        return MarketBenchmark(MarketStatus.UNAVAILABLE, usable, None, None)
    stores = {o.store for o in usable}
    if len(usable) >= config.market_min_observations and len(stores) >= config.market_min_stores:
        median = Distribution.of([o.effective_price_cop for o in usable]).median
        return MarketBenchmark(
            MarketStatus.REFERENCE, usable, to_cop(median), deviation_pct(price, median)
        )
    # Evidencia limitada: no es «precio de mercado»; se compara contra la observación más alta.
    highest = max(o.effective_price_cop for o in usable)
    return MarketBenchmark(
        MarketStatus.LIMITED, usable, highest, deviation_pct(price, Decimal(highest))
    )
