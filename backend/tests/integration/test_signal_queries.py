import pytest
from sqlalchemy import Engine

from public_procurement.comparison.services import (
    ConfidenceLevel,
    SignalFilters,
    SignalQueryService,
    SignalSort,
    build_signal_query_service,
)
from public_procurement.shared.persistence import create_session_factory

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def service(seeded_engine: Engine) -> SignalQueryService:
    return build_signal_query_service(create_session_factory(seeded_engine))


def test_signal_list_returns_current_signals_with_purchase_data_when_recalculated(
    service: SignalQueryService,
) -> None:
    # Arrange / Act
    page = service.list_signals(SignalFilters(text="san rafael"), SignalSort.PRIORITY, 1, 25)
    # Assert
    reference = next(row for row in page.items if row.code == "SG-2026-0142")
    assert reference.entity_name == "Alcaldía Municipal de San Rafael del Valle"
    assert (reference.unit_price_cop, reference.quantity) == (4_950_000, 8)
    assert reference.median_cop > 0
    assert reference.deviation_pct > 0


def test_signal_priority_never_puts_lower_confidence_first_when_listing_all(
    service: SignalQueryService,
) -> None:
    # Arrange
    rank = {ConfidenceLevel.HIGH: 3, ConfidenceLevel.MEDIUM: 2, ConfidenceLevel.LOW: 1}
    # Act
    rows = service.list_signals(SignalFilters(), SignalSort.PRIORITY, 1, 100).items
    # Assert
    ranks = [rank[row.confidence_level] for row in rows]
    assert ranks == sorted(ranks, reverse=True)


def test_summary_matches_current_results_when_recalculated(service: SignalQueryService) -> None:
    # Arrange
    total = service.list_signals(SignalFilters(), SignalSort.PRIORITY, 1, 100).total
    # Act
    summary = service.summary()
    # Assert
    assert summary.signals == total
    assert summary.tv_purchases == sum(summary.tv_purchases_by_source.values())
    assert set(summary.tv_purchases_by_source) == {"secop_ii", "tvec"}
    assert summary.without_source_information > 0
    assert summary.config_version_id == "analitica-v1"
