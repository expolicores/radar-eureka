from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import Engine

from public_procurement.exploration.domain.analysis import AnalysisStatus
from public_procurement.exploration.services import (
    ExplorationService,
    PurchaseSummaryView,
    build_exploration_service,
)
from public_procurement.ingestion.services import (
    ItemClassification,
    PurchaseSearchCriteria,
    PurchaseSort,
    Source,
    ValueRange,
    VatBasis,
)
from public_procurement.shared.persistence import create_session_factory
from public_procurement.shared.text import normalize_text

pytestmark = pytest.mark.integration

REFERENCE = "CO1.PCCNTR.0000142"
CUTOFF = datetime(2026, 10, 6, 8, 10, tzinfo=UTC)


@pytest.fixture(scope="module")
def service(seeded_engine: Engine) -> ExplorationService:
    return build_exploration_service(create_session_factory(seeded_engine))


def _all(
    service: ExplorationService, criteria: PurchaseSearchCriteria | None = None
) -> list[PurchaseSummaryView]:
    """Recorre todas las páginas de una búsqueda."""
    base = criteria or PurchaseSearchCriteria()
    items: list[PurchaseSummaryView] = []
    page = 1
    while True:
        view = service.list_purchases(replace(base, page=page, page_size=100))
        items.extend(view.items)
        if page * 100 >= view.total:
            return items
        page += 1


def test_list_returns_first_page_sorted_by_signed_date_when_no_filters(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    view = service.list_purchases(PurchaseSearchCriteria())
    # Assert
    assert len(view.items) == 25
    assert 1_000 <= view.total <= 1_500
    dates = [item.signed_on for item in view.items]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.parametrize(
    ("text", "expected_reference"),
    [
        ("alcaldia municipal de san rafael", REFERENCE),
        ("TECNOLOGÍA ANDINA", REFERENCE),
        ("900.000.142-1", REFERENCE),
        (REFERENCE, REFERENCE),
        ("166000", "Orden 166000"),
    ],
)
def test_search_ignores_case_and_accents_across_fields_when_text_is_given(
    service: ExplorationService, text: str, expected_reference: str
) -> None:
    # Arrange
    criteria = PurchaseSearchCriteria(text=text)
    # Act
    references = [item.reference for item in _all(service, criteria)]
    # Assert
    assert expected_reference in references


def test_search_by_exact_reference_returns_only_that_purchase_when_reference_is_unique(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    view = service.list_purchases(PurchaseSearchCriteria(text=REFERENCE))
    # Assert
    assert [item.reference for item in view.items] == [REFERENCE]


def test_filters_combine_when_department_and_modality_are_given(
    service: ExplorationService,
) -> None:
    # Arrange
    criteria = PurchaseSearchCriteria(department="Valle del Cauca", modality="Mínima cuantía")
    # Act
    items = _all(service, criteria)
    # Assert
    assert items
    assert all(item.entity_department == "Valle del Cauca" for item in items)
    assert all(item.modality == "Mínima cuantía" for item in items)


def test_source_filter_returns_only_tvec_orders_when_source_is_tvec(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    view = service.list_purchases(PurchaseSearchCriteria(source=Source.TVEC, page_size=100))
    # Assert
    assert view.total > 800
    assert {item.source for item in view.items} == {Source.TVEC}


@pytest.mark.parametrize(
    ("value_range", "low", "high"),
    [
        (ValueRange.LT_20M, 0, 19_999_999),
        (ValueRange.BETWEEN_20M_100M, 20_000_000, 100_000_000),
        (ValueRange.GT_100M, 100_000_001, 10**15),
    ],
)
def test_value_range_filter_keeps_values_inside_the_range_when_given(
    service: ExplorationService, value_range: ValueRange, low: int, high: int
) -> None:
    # Arrange / Act
    items = _all(service, PurchaseSearchCriteria(value_range=value_range))
    # Assert
    assert items
    assert all(item.total_value_cop is not None for item in items)
    assert all(low <= (item.total_value_cop or 0) <= high for item in items)


def test_date_filter_keeps_purchases_inside_the_range_when_dates_are_given(
    service: ExplorationService,
) -> None:
    # Arrange
    criteria = PurchaseSearchCriteria(signed_from=date(2026, 1, 1), signed_to=date(2026, 6, 30))
    # Act
    items = _all(service, criteria)
    # Assert
    assert items
    assert all(date(2026, 1, 1) <= item.signed_on <= date(2026, 6, 30) for item in items)


def test_sort_by_value_descending_orders_values_when_requested(
    service: ExplorationService,
) -> None:
    # Arrange
    criteria = PurchaseSearchCriteria(sort=PurchaseSort.VALUE_DESC, page_size=100)
    # Act
    view = service.list_purchases(criteria)
    # Assert
    values = [item.total_value_cop or 0 for item in view.items]
    assert values == sorted(values, reverse=True)


def test_search_without_matches_returns_empty_page_when_text_does_not_exist(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    view = service.list_purchases(PurchaseSearchCriteria(text="zzzz-no-existe"))
    # Assert
    assert (view.items, view.total) == ((), 0)


def test_search_escapes_wildcards_when_text_contains_percent(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    view = service.list_purchases(PurchaseSearchCriteria(text="%"))
    # Assert
    assert view.total == 0


def test_detail_returns_items_and_cutoff_when_purchase_exists(service: ExplorationService) -> None:
    # Arrange
    summary = service.list_purchases(PurchaseSearchCriteria(text=REFERENCE)).items[0]
    # Act
    detail = service.get_purchase(summary.id)
    # Assert
    assert detail is not None
    assert detail.summary.total_value_cop == 39_600_000
    tv, accessory = detail.items
    assert (tv.classification, tv.quantity, tv.unit_price_cop) == (
        ItemClassification.INCLUDED,
        8,
        4_950_000,
    )
    assert tv.vat_basis is VatBasis.INCLUDED
    assert tv.screen_size_inches == 65
    assert accessory.classification is ItemClassification.EXCLUDED_ACCESSORY
    assert detail.data_cutoff_at == CUTOFF


def test_analysis_statuses_cover_every_compared_state_when_seed_is_recalculated(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    statuses = {item.analysis_status for item in _all(service)}
    # Assert: tras el recálculo ningún televisor queda «pendiente de comparación».
    assert statuses == set(AnalysisStatus) - {AnalysisStatus.PENDING_COMPARISON}


def test_reference_purchase_has_signal_when_seed_is_recalculated(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    view = service.list_purchases(PurchaseSearchCriteria(text=REFERENCE))
    # Assert
    assert view.items[0].analysis_status is AnalysisStatus.WITH_SIGNAL


@pytest.mark.parametrize("has_signal", [True, False])
def test_signal_filter_splits_purchases_when_requested(
    service: ExplorationService, has_signal: bool
) -> None:
    # Arrange
    criteria = PurchaseSearchCriteria(page_size=100)
    # Act
    view = service.list_purchases(criteria, has_signal=has_signal)
    # Assert
    with_signal = {item.analysis_status is AnalysisStatus.WITH_SIGNAL for item in view.items}
    assert with_signal == {has_signal}


def test_filter_options_list_sources_departments_and_cutoff_when_seed_is_loaded(
    service: ExplorationService,
) -> None:
    # Arrange / Act
    options = service.filter_options()
    # Assert
    assert options.sources == (Source.SECOP_II, Source.TVEC)
    assert "Valle del Cauca" in options.departments
    assert len(set(options.departments)) == len(options.departments)
    assert list(options.departments) == sorted(options.departments, key=normalize_text)
    assert "Mínima cuantía" in options.modalities
    assert options.data_cutoff_at == CUTOFF
