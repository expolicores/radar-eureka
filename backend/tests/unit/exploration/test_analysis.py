import pytest

from public_procurement.exploration.domain.analysis import (
    AnalysisStatus,
    ComparisonState,
    ItemState,
    derive_analysis_status,
)

from ...builders import ItemStateBuilder


@pytest.mark.parametrize(
    ("items", "expected"),
    [
        ([ItemStateBuilder().not_tv().without_price().build()], AnalysisStatus.EXCLUDED),
        ([], AnalysisStatus.EXCLUDED),
        (
            [ItemStateBuilder().with_price_pending_review().with_non_comparable_vat().build()],
            AnalysisStatus.QUALITY_REVIEW,
        ),
        ([ItemStateBuilder().without_price().build()], AnalysisStatus.NO_UNIT_PRICE),
        ([ItemStateBuilder().with_non_comparable_vat().build()], AnalysisStatus.VAT_INCOMPLETE),
        (
            [
                ItemStateBuilder().build(),
                ItemStateBuilder().not_tv().with_non_comparable_vat().build(),
            ],
            AnalysisStatus.PENDING_COMPARISON,
        ),
    ],
    ids=[
        "only_service",
        "no_items",
        "quality_review",
        "no_price",
        "vat_incomplete",
        "comparable",
    ],
)
def test_derive_analysis_status_follows_precedence_when_items_differ(
    items: list[ItemState], expected: AnalysisStatus
) -> None:
    # Arrange / Act
    status = derive_analysis_status(items)
    # Assert
    assert status is expected


def test_derive_analysis_status_ignores_excluded_items_when_tv_item_is_comparable() -> None:
    # Arrange
    tv = ItemStateBuilder().build()
    accessory_without_price = ItemStateBuilder().not_tv().without_price().build()
    # Act
    status = derive_analysis_status([tv, accessory_without_price])
    # Assert
    assert status is AnalysisStatus.PENDING_COMPARISON


@pytest.mark.parametrize(
    ("comparison", "expected"),
    [
        (ComparisonState.SIGNAL, AnalysisStatus.WITH_SIGNAL),
        (ComparisonState.NO_SIGNAL, AnalysisStatus.COMPARED_NO_SIGNAL),
        (ComparisonState.LOW_PRICE_REVIEW, AnalysisStatus.QUALITY_REVIEW),
        (ComparisonState.INSUFFICIENT_COMPARABLES, AnalysisStatus.INSUFFICIENT_COMPARABLES),
    ],
)
def test_derive_analysis_status_uses_comparison_when_tv_item_is_comparable(
    comparison: ComparisonState, expected: AnalysisStatus
) -> None:
    # Arrange
    items = [ItemStateBuilder().build()]
    # Act
    status = derive_analysis_status(items, comparison)
    # Assert
    assert status is expected


def test_signal_takes_precedence_over_missing_data_when_another_tv_item_lacks_price() -> None:
    # Arrange
    items = [ItemStateBuilder().build(), ItemStateBuilder().with_non_comparable_vat().build()]
    # Act
    status = derive_analysis_status(items, ComparisonState.SIGNAL)
    # Assert
    assert status is AnalysisStatus.WITH_SIGNAL
