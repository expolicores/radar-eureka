from decimal import Decimal

import pytest

from public_procurement.comparison.domain.config import DEFAULT_CONFIG
from public_procurement.comparison.domain.evaluation import Outcome, ThresholdRule, evaluate_item
from public_procurement.comparison.domain.facts import ItemFacts, PriceStatus, VatBasis

from ...builders import MOCKUP_COMPARABLE_PRICES, ItemFactsBuilder, comparables_at

MOCKUP_COMPARABLES = comparables_at(MOCKUP_COMPARABLE_PRICES)
SIX_AT_TWO_MILLION = comparables_at(
    [1_500_000, 1_800_000, 2_000_000, 2_000_000, 2_400_000, 2_600_000]
)


def test_mockup_purchase_is_a_signal_with_iqr_rule_when_compared_with_mockup_sample() -> None:
    # Arrange
    target = ItemFactsBuilder().build()
    # Act
    evaluation = evaluate_item(target, MOCKUP_COMPARABLES, [], DEFAULT_CONFIG)
    # Assert
    assert evaluation.outcome is Outcome.SIGNAL
    assert evaluation.reference is not None
    assert evaluation.reference.rule is ThresholdRule.IQR
    assert evaluation.reference.threshold_cop == 3_867_500
    assert evaluation.reference.deviation_pct == Decimal("73.1")


@pytest.mark.parametrize(
    ("price", "outcome"), [(3_867_500, Outcome.NO_SIGNAL), (3_867_501, Outcome.SIGNAL)]
)
def test_iqr_threshold_is_exclusive_when_price_is_at_the_limit(
    price: int, outcome: Outcome
) -> None:
    # Arrange
    target = ItemFactsBuilder().with_price(price).build()
    # Act
    evaluation = evaluate_item(target, MOCKUP_COMPARABLES, [], DEFAULT_CONFIG)
    # Assert
    assert evaluation.outcome is outcome


@pytest.mark.parametrize(
    ("same_model", "price", "outcome"),
    [
        (True, 2_600_001, Outcome.SIGNAL),
        (True, 2_580_000, Outcome.NO_SIGNAL),
        (False, 3_000_001, Outcome.SIGNAL),
        (False, 2_900_000, Outcome.NO_SIGNAL),
    ],
    ids=["same_model_over_30", "same_model_29", "equivalent_over_50", "equivalent_45"],
)
def test_percentage_rule_applies_when_sample_is_small(
    same_model: bool, price: int, outcome: Outcome
) -> None:
    # Arrange
    target_builder = ItemFactsBuilder().with_price(price)
    comparables: list[ItemFacts] = SIX_AT_TWO_MILLION
    if same_model:
        target_builder = target_builder.with_model("Lumora", "LM65U7000")
        comparables = [
            ItemFactsBuilder()
            .with_model("Lumora", "LM65U7000")
            .with_price(c.unit_price_cop)
            .build()
            for c in SIX_AT_TWO_MILLION
        ]
    # Act
    evaluation = evaluate_item(target_builder.build(), comparables, [], DEFAULT_CONFIG)
    # Assert
    assert evaluation.reference is not None
    assert evaluation.reference.rule is ThresholdRule.PERCENTAGE
    assert evaluation.outcome is outcome


def test_abnormally_low_price_goes_to_quality_review_when_below_lower_fence() -> None:
    # Arrange
    target = ItemFactsBuilder().with_price(1_000_000).build()
    # Act
    evaluation = evaluate_item(target, MOCKUP_COMPARABLES, [], DEFAULT_CONFIG)
    # Assert
    assert evaluation.outcome is Outcome.LOW_PRICE_REVIEW
    assert not evaluation.is_signal


def _high() -> ItemFactsBuilder:
    return ItemFactsBuilder().with_price(9_000_000)


@pytest.mark.parametrize(
    ("target", "outcome"),
    [
        (_high().with_price(None, PriceStatus.NOT_PUBLISHED).build(), Outcome.NO_UNIT_PRICE),
        (_high().with_price(9_000_000, PriceStatus.PENDING_REVIEW).build(), Outcome.QUALITY_REVIEW),
        (_high().with_vat_basis(VatBasis.UNDETERMINED).build(), Outcome.VAT_INCOMPLETE),
        (_high().with_vat_basis(VatBasis.EXCLUDED).build(), Outcome.VAT_INCOMPLETE),
    ],
    ids=["no_price", "price_in_review", "vat_undetermined", "vat_excluded"],
)  # fmt: skip
def test_missing_data_never_produces_a_signal_when_evaluated(
    target: ItemFacts, outcome: Outcome
) -> None:
    # Arrange / Act
    evaluation = evaluate_item(target, MOCKUP_COMPARABLES, [], DEFAULT_CONFIG)
    # Assert
    assert evaluation.outcome is outcome
    assert evaluation.confidence is None


def test_insufficient_comparables_never_produces_a_signal_when_fewer_than_five() -> None:
    # Arrange
    target = ItemFactsBuilder().with_price(9_000_000).build()
    # Act
    evaluation = evaluate_item(target, comparables_at([2_000_000] * 4), [], DEFAULT_CONFIG)
    # Assert
    assert evaluation.outcome is Outcome.INSUFFICIENT_COMPARABLES
    assert evaluation.reference is None
