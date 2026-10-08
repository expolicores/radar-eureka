import pytest
from sqlalchemy import Engine, func, select

from public_procurement.comparison.repositories import (
    ItemComparableRecord,
    ItemComparisonRecord,
    ItemMarketObservationRecord,
)
from public_procurement.comparison.services import build_comparison_service
from public_procurement.shared.persistence import create_session_factory

from .conftest import load_seed

pytestmark = pytest.mark.integration


def _scalar(engine: Engine, statement: object) -> int:
    with engine.connect() as connection:
        return int(connection.execute(statement).scalar_one())  # type: ignore[call-overload]


def test_recalculation_inserts_a_new_current_version_when_run_twice(
    migrated_engine: Engine,
) -> None:
    # Arrange
    load_seed(migrated_engine)
    first_total = _scalar(migrated_engine, select(func.count()).select_from(ItemComparisonRecord))
    # Act
    build_comparison_service(create_session_factory(migrated_engine)).recalculate()
    # Assert
    total = _scalar(migrated_engine, select(func.count()).select_from(ItemComparisonRecord))
    current = _scalar(
        migrated_engine,
        select(func.count())
        .select_from(ItemComparisonRecord)
        .where(ItemComparisonRecord.is_current),
    )
    assert total == 2 * first_total
    assert current == first_total
    versions = _scalar(
        migrated_engine, select(func.count(func.distinct(ItemComparisonRecord.config_version_id)))
    )
    assert versions == 1


def test_recalculation_links_every_comparable_and_market_observation_when_compared(
    migrated_engine: Engine,
) -> None:
    # Arrange / Act
    load_seed(migrated_engine)
    # Assert
    with migrated_engine.connect() as connection:
        comparisons = connection.execute(
            select(
                ItemComparisonRecord.id,
                ItemComparisonRecord.comparable_count,
                ItemComparisonRecord.market_observation_count,
            ).where(ItemComparisonRecord.median_cop.is_not(None))
        ).all()
        comparable_links = {
            comparison_id: count
            for comparison_id, count in connection.execute(
                select(ItemComparableRecord.comparison_id, func.count()).group_by(
                    ItemComparableRecord.comparison_id
                )
            ).tuples()
        }
        market_links = {
            comparison_id: count
            for comparison_id, count in connection.execute(
                select(ItemMarketObservationRecord.comparison_id, func.count()).group_by(
                    ItemMarketObservationRecord.comparison_id
                )
            ).tuples()
        }
    assert comparisons
    assert all(comparable_links.get(row.id, 0) == row.comparable_count for row in comparisons)
    assert all(market_links.get(row.id, 0) == row.market_observation_count for row in comparisons)


def test_signals_have_unique_codes_and_never_come_from_missing_data_when_recalculated(
    migrated_engine: Engine,
) -> None:
    # Arrange / Act
    load_seed(migrated_engine)
    # Assert
    with migrated_engine.connect() as connection:
        signals = connection.execute(
            select(
                ItemComparisonRecord.signal_code,
                ItemComparisonRecord.median_cop,
                ItemComparisonRecord.confidence_score,
            )
            .where(ItemComparisonRecord.is_current)
            .where(ItemComparisonRecord.outcome == "signal")
        ).all()
    codes = [row.signal_code for row in signals]
    assert signals
    assert len(set(codes)) == len(codes)
    assert all(row.median_cop is not None and row.confidence_score is not None for row in signals)
    assert "SG-2026-0142" in codes
