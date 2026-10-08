from datetime import date

import pytest

from public_procurement.comparison.domain.confidence import ConfidenceLevel
from public_procurement.comparison.domain.signals import (
    SignalFilters,
    SignalRow,
    SignalSort,
    select_signals,
)

from ...builders import SignalRowBuilder


def _row(code: str, confidence: ConfidenceLevel, deviation: str) -> SignalRow:
    return (
        SignalRowBuilder()
        .with_code(code)
        .with_confidence(confidence)
        .with_deviation(deviation)
        .build()
    )


def _rows() -> list[SignalRow]:
    return [
        _row("A", ConfidenceLevel.MEDIUM, "90.0"),
        _row("B", ConfidenceLevel.HIGH, "50.0"),
        _row("C", ConfidenceLevel.HIGH, "70.0"),
        _row("D", ConfidenceLevel.LOW, "120.0"),
    ]


def test_priority_orders_by_confidence_then_deviation_when_no_sort_is_chosen() -> None:
    # Arrange
    rows = _rows()
    # Act
    selected = select_signals(rows, SignalFilters(), SignalSort.PRIORITY)
    # Assert
    assert [row.code for row in selected] == ["C", "B", "A", "D"]


def test_deviation_sort_ignores_confidence_when_chosen() -> None:
    # Arrange
    rows = _rows()
    # Act
    selected = select_signals(rows, SignalFilters(), SignalSort.DEVIATION)
    # Assert
    assert [row.code for row in selected] == ["D", "A", "C", "B"]


@pytest.mark.parametrize(
    ("sort", "expected"),
    [(SignalSort.VALUE, ["Y", "X"]), (SignalSort.DATE, ["X", "Y"])],
)
def test_value_and_date_sorts_are_descending_when_chosen(
    sort: SignalSort, expected: list[str]
) -> None:
    # Arrange
    rows = [
        SignalRowBuilder().with_code("X").with_price(2_000_000).signed_on(date(2026, 9, 1)).build(),
        SignalRowBuilder().with_code("Y").with_price(6_000_000).signed_on(date(2024, 1, 1)).build(),
    ]
    # Act
    selected = select_signals(rows, SignalFilters(), sort)
    # Assert
    assert [row.code for row in selected] == expected


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        (SignalFilters(text="san rafael"), "SR"),
        (SignalFilters(text="SG-2026-0001"), "SG-2026-0001"),
        (SignalFilters(department="Antioquia"), "SG-2026-0001"),
        (SignalFilters(source="tvec"), "SG-2026-0001"),
        (SignalFilters(confidence=ConfidenceLevel.HIGH), "SG-2026-0001"),
        (SignalFilters(year=2024), "SG-2026-0001"),
    ],
    ids=["text_without_accents", "code", "department", "source", "confidence", "year"],
)
def test_filters_keep_only_matching_signals_when_given(
    filters: SignalFilters, expected: str
) -> None:
    # Arrange
    rows = [
        SignalRowBuilder().with_code("SR").with_entity("Alcaldía Municipal de San Rafael").build(),
        SignalRowBuilder()
        .with_code("SG-2026-0001")
        .with_entity("Gobernación Demo")
        .in_department("Antioquia")
        .from_tvec()
        .with_confidence(ConfidenceLevel.HIGH)
        .signed_on(date(2024, 5, 1))
        .build(),
    ]
    # Act
    selected = select_signals(rows, filters, SignalSort.PRIORITY)
    # Assert
    assert [row.code for row in selected] == [expected]
