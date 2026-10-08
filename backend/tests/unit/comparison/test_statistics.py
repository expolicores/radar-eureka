from decimal import Decimal

from public_procurement.comparison.domain.statistics import Distribution, deviation_pct, to_cop

from ...builders import MOCKUP_COMPARABLE_PRICES


def test_distribution_reproduces_mockup_quartiles_when_using_linear_interpolation() -> None:
    # Arrange
    prices = MOCKUP_COMPARABLE_PRICES
    # Act
    distribution = Distribution.of(prices)
    # Assert
    assert distribution.count == 14
    assert to_cop(distribution.q1) == 2_630_000
    assert to_cop(distribution.median) == 2_860_000
    assert to_cop(distribution.q3) == 3_125_000


def test_iqr_threshold_matches_mockup_when_factor_is_one_and_a_half() -> None:
    # Arrange
    distribution = Distribution.of(MOCKUP_COMPARABLE_PRICES)
    # Act
    threshold = distribution.q3 + Decimal("1.5") * distribution.iqr
    # Assert
    assert to_cop(threshold) == 3_867_500


def test_deviation_is_rounded_to_one_decimal_when_price_exceeds_median() -> None:
    # Arrange
    median = Decimal(2_860_000)
    # Act
    deviation = deviation_pct(4_950_000, median)
    # Assert
    assert deviation == Decimal("73.1")
