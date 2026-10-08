"""Evaluación de un ítem: Benchmark 1, regla híbrida de señal, precios bajos, B2 y confianza.

Una «señal que merece revisión» prioriza revisión humana: no es una conclusión (FR-063, FR-064).
"""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from .benchmarks import (
    ComparableSelection,
    MarketBenchmark,
    MarketStatus,
    MatchType,
    distribution_of,
    evaluate_market,
    select_comparables,
)
from .confidence import Confidence, compute_confidence
from .config import AnalysisConfig, PenaltyCode
from .facts import ItemFacts, MarketFacts, PriceStatus, VatBasis
from .statistics import Distribution, deviation_pct, to_cop


class Outcome(StrEnum):
    SIGNAL = "signal"
    NO_SIGNAL = "no_signal"
    LOW_PRICE_REVIEW = "low_price_review"
    INSUFFICIENT_COMPARABLES = "insufficient_comparables"
    VAT_INCOMPLETE = "vat_incomplete"
    NO_UNIT_PRICE = "no_unit_price"
    QUALITY_REVIEW = "quality_review"


class ThresholdRule(StrEnum):
    IQR = "iqr"
    PERCENTAGE = "percentage"


@dataclass(frozen=True)
class Reference:
    """Benchmark 1 con muestra suficiente: estadísticos, umbrales y desviación."""

    distribution: Distribution
    rule: ThresholdRule
    threshold_cop: int
    low_threshold_cop: int
    deviation_pct: Decimal


@dataclass(frozen=True)
class ItemEvaluation:
    target: ItemFacts
    outcome: Outcome
    selection: ComparableSelection | None
    reference: Reference | None
    market: MarketBenchmark | None
    confidence: Confidence | None

    @property
    def is_signal(self) -> bool:
        return self.outcome is Outcome.SIGNAL


def _without_comparison(target: ItemFacts, outcome: Outcome) -> ItemEvaluation:
    return ItemEvaluation(target, outcome, None, None, None, None)


def _is_homogeneous(distribution: Distribution, config: AnalysisConfig) -> bool:
    return (
        distribution.count >= config.homogeneous_min_comparables
        and distribution.median > 0
        and distribution.iqr / distribution.median <= config.homogeneous_max_iqr_ratio
    )


def _reference(price: int, selection: ComparableSelection, config: AnalysisConfig) -> Reference:
    distribution = distribution_of(selection.comparables)
    if _is_homogeneous(distribution, config):
        spread = config.outlier_iqr_factor * distribution.iqr
        return Reference(
            distribution=distribution,
            rule=ThresholdRule.IQR,
            threshold_cop=to_cop(distribution.q3 + spread),
            low_threshold_cop=to_cop(distribution.q1 - spread),
            deviation_pct=deviation_pct(price, distribution.median),
        )
    threshold_pct = (
        config.same_model_threshold_pct
        if selection.match_type is MatchType.SAME_MODEL
        else config.equivalent_threshold_pct
    )
    return Reference(
        distribution=distribution,
        rule=ThresholdRule.PERCENTAGE,
        threshold_cop=to_cop(distribution.median * (1 + threshold_pct / 100)),
        low_threshold_cop=to_cop(distribution.median * config.low_price_median_ratio),
        deviation_pct=deviation_pct(price, distribution.median),
    )


def _penalties(
    target: ItemFacts,
    selection: ComparableSelection,
    reference: Reference,
    market: MarketBenchmark,
    config: AnalysisConfig,
) -> list[PenaltyCode]:
    codes: list[PenaltyCode] = []
    if selection.match_type is MatchType.EQUIVALENT:
        codes.append(PenaltyCode.EQUIVALENT_MATCH)
    if target.price_status is PriceStatus.DERIVED:
        codes.append(PenaltyCode.DERIVED_PRICE)
    if market.status is MarketStatus.LIMITED:
        codes.append(PenaltyCode.MARKET_LIMITED)
    elif market.status is MarketStatus.UNAVAILABLE:
        codes.append(PenaltyCode.MARKET_UNAVAILABLE)
    if len(selection.comparables) < config.few_comparables_below:
        codes.append(PenaltyCode.FEW_COMPARABLES)
    if selection.window_months > config.window_months:
        codes.append(PenaltyCode.EXTENDED_WINDOW)
    if reference.rule is ThresholdRule.PERCENTAGE:
        codes.append(PenaltyCode.PERCENTAGE_RULE)
    return codes


def evaluate_item(
    target: ItemFacts,
    candidates: Iterable[ItemFacts],
    observations: Iterable[MarketFacts],
    config: AnalysisConfig,
) -> ItemEvaluation:
    price = target.unit_price_cop
    # Datos faltantes: estado explícito, nunca señal.
    if target.price_status is PriceStatus.PENDING_REVIEW:
        return _without_comparison(target, Outcome.QUALITY_REVIEW)
    if price is None:
        return _without_comparison(target, Outcome.NO_UNIT_PRICE)
    if target.vat_basis is not VatBasis.INCLUDED:
        return _without_comparison(target, Outcome.VAT_INCOMPLETE)

    selection = select_comparables(target, candidates, config)
    market = evaluate_market(target, observations, config)
    if len(selection.comparables) < config.min_comparables:
        return ItemEvaluation(
            target, Outcome.INSUFFICIENT_COMPARABLES, selection, None, market, None
        )

    reference = _reference(price, selection, config)
    if price > reference.threshold_cop:
        outcome = Outcome.SIGNAL
    elif price < reference.low_threshold_cop:
        outcome = Outcome.LOW_PRICE_REVIEW
    else:
        outcome = Outcome.NO_SIGNAL
    confidence = compute_confidence(
        _penalties(target, selection, reference, market, config), config
    )
    return ItemEvaluation(target, outcome, selection, reference, market, confidence)
