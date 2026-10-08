from datetime import date

import pytest

from public_procurement.comparison.domain.benchmarks import (
    MarketStatus,
    MatchType,
    add_months,
    evaluate_market,
    select_comparables,
)
from public_procurement.comparison.domain.config import DEFAULT_CONFIG
from public_procurement.comparison.domain.facts import ItemFacts, PriceStatus, VatBasis

from ...builders import REFERENCE_SIGNED_ON, ItemFactsBuilder, MarketFactsBuilder, comparables_at

TARGET = ItemFactsBuilder().build()


@pytest.mark.parametrize(
    ("candidate", "comparable"),
    [
        (ItemFactsBuilder().signed_on(date(2026, 5, 14)).build(), True),
        (ItemFactsBuilder().with_spec(55).build(), False),
        (ItemFactsBuilder().with_spec(65, panel="qled").build(), False),
        (ItemFactsBuilder().with_vat_basis(VatBasis.UNDETERMINED).build(), False),
        (ItemFactsBuilder().signed_on(date(2025, 12, 14)).build(), False),
        (ItemFactsBuilder().with_purchase_id(TARGET.purchase_id).with_line_number(2).build(),
         False),
        (ItemFactsBuilder().with_price(2_000_000, PriceStatus.PENDING_REVIEW).build(), False),
    ],
    ids=["equivalent_in_window", "other_size", "other_panel", "vat_unknown", "out_of_window",
         "same_purchase", "price_in_review"],
)  # fmt: skip
def test_select_comparables_keeps_only_valid_candidates_when_mixed(
    candidate: ItemFacts, comparable: bool
) -> None:
    # Arrange
    others = comparables_at([3_000_000] * 5, date(2026, 6, 1))
    # Act
    selection = select_comparables(TARGET, [candidate, *others], DEFAULT_CONFIG)
    # Assert
    assert (candidate in selection.comparables) is comparable


def test_select_comparables_extends_window_to_twelve_months_when_fewer_than_five() -> None:
    # Arrange
    near = comparables_at([3_000_000] * 3, date(2026, 6, 1))
    far = comparables_at([3_100_000] * 3, date(2025, 11, 1))
    # Act
    selection = select_comparables(TARGET, near + far, DEFAULT_CONFIG)
    # Assert
    assert selection.window_months == 12
    assert len(selection.comparables) == 6


def test_select_comparables_prefers_same_model_when_it_reaches_the_minimum() -> None:
    # Arrange
    target = ItemFactsBuilder().with_model("Visionix", "VX65U7000").build()
    same_model = [
        ItemFactsBuilder().with_model("visionix", "vx65u7000").with_price(3_000_000).build()
        for _ in range(5)
    ]
    others = comparables_at([2_800_000] * 6)
    # Act
    selection = select_comparables(target, same_model + others, DEFAULT_CONFIG)
    # Assert
    assert selection.match_type is MatchType.SAME_MODEL
    assert set(selection.comparables) == set(same_model)


def test_add_months_clamps_to_last_day_when_month_is_shorter() -> None:
    # Arrange / Act
    result = add_months(date(2026, 8, 31), -6)
    # Assert
    assert result == date(2026, 2, 28)


def test_market_has_reference_when_three_observations_from_two_stores() -> None:
    # Arrange
    observations = [
        MarketFactsBuilder().with_price(3_000_000).build(),
        MarketFactsBuilder().with_price(3_200_000).build(),
        MarketFactsBuilder().from_store("falabella").with_price(3_400_000).build(),
    ]
    # Act
    market = evaluate_market(TARGET, observations, DEFAULT_CONFIG)
    # Assert
    assert market.status is MarketStatus.REFERENCE
    assert market.reference_cop == 3_200_000
    assert market.store_count == 2


@pytest.mark.parametrize(
    "observations",
    [
        [MarketFactsBuilder().build(), MarketFactsBuilder().from_store("falabella").build()],
        [MarketFactsBuilder().with_price(price).build()
         for price in (3_000_000, 3_100_000, 3_200_000, 3_300_000)],
    ],
    ids=["two_from_two_stores", "four_from_one_store"],
)  # fmt: skip
def test_market_is_limited_and_uses_highest_observation_when_below_minimum(
    observations: list,  # type: ignore[type-arg]
) -> None:
    # Arrange / Act
    market = evaluate_market(TARGET, observations, DEFAULT_CONFIG)
    # Assert
    assert market.status is MarketStatus.LIMITED
    assert market.reference_cop == max(o.effective_price_cop for o in observations)


def test_market_is_unavailable_when_observations_are_not_usable() -> None:
    # Arrange
    observations = [
        MarketFactsBuilder().from_third_party_seller().build(),
        MarketFactsBuilder().with_special_conditions().build(),
        MarketFactsBuilder().observed_on(add_months(REFERENCE_SIGNED_ON, 2)).build(),
    ]
    # Act
    market = evaluate_market(TARGET, observations, DEFAULT_CONFIG)
    # Assert
    assert market.status is MarketStatus.UNAVAILABLE
    assert market.reference_cop is None
