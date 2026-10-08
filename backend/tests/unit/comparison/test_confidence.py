from public_procurement.comparison.domain.confidence import ConfidenceLevel
from public_procurement.comparison.domain.config import DEFAULT_CONFIG, PenaltyCode
from public_procurement.comparison.domain.evaluation import evaluate_item
from public_procurement.comparison.domain.facts import PriceStatus

from ...builders import (
    MOCKUP_COMPARABLE_PRICES,
    ItemFactsBuilder,
    MarketFactsBuilder,
    comparables_at,
)


def test_confidence_is_medium_when_equivalent_match_and_limited_market() -> None:
    # Arrange
    target = ItemFactsBuilder().build()
    market = [MarketFactsBuilder().build()]
    # Act
    evaluation = evaluate_item(
        target, comparables_at(MOCKUP_COMPARABLE_PRICES), market, DEFAULT_CONFIG
    )
    # Assert
    assert evaluation.confidence is not None
    assert evaluation.confidence.score == 70
    assert evaluation.confidence.level is ConfidenceLevel.MEDIUM
    assert [p.code for p in evaluation.confidence.penalties] == [
        PenaltyCode.EQUIVALENT_MATCH,
        PenaltyCode.MARKET_LIMITED,
    ]


def test_confidence_is_full_when_same_model_and_market_reference_and_enough_comparables() -> None:
    # Arrange
    target = ItemFactsBuilder().with_model("Orbis", "OB65U7000").build()
    comparables = [
        ItemFactsBuilder().with_model("Orbis", "OB65U7000").with_price(price).build()
        for price in MOCKUP_COMPARABLE_PRICES[:12]
    ]
    market = [
        MarketFactsBuilder().with_price(3_000_000).build(),
        MarketFactsBuilder().with_price(3_100_000).build(),
        MarketFactsBuilder().from_store("falabella").with_price(3_200_000).build(),
    ]
    # Act
    evaluation = evaluate_item(target, comparables, market, DEFAULT_CONFIG)
    # Assert
    assert evaluation.confidence is not None
    assert (evaluation.confidence.score, evaluation.confidence.level) == (100, ConfidenceLevel.HIGH)
    assert evaluation.confidence.penalties == ()


def test_confidence_is_low_when_penalties_accumulate() -> None:
    # Arrange
    target = ItemFactsBuilder().with_price(4_000_000, PriceStatus.DERIVED).build()
    comparables = comparables_at([1_500_000, 1_800_000, 2_000_000, 2_000_000, 2_400_000, 2_600_000])
    # Act
    evaluation = evaluate_item(target, comparables, [], DEFAULT_CONFIG)
    # Assert
    assert evaluation.confidence is not None
    assert evaluation.confidence.score == 35
    assert evaluation.confidence.level is ConfidenceLevel.LOW
    assert {p.code for p in evaluation.confidence.penalties} == {
        PenaltyCode.EQUIVALENT_MATCH,
        PenaltyCode.DERIVED_PRICE,
        PenaltyCode.MARKET_UNAVAILABLE,
        PenaltyCode.FEW_COMPARABLES,
        PenaltyCode.PERCENTAGE_RULE,
    }
