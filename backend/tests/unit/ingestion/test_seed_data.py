from collections import Counter
from datetime import date

from public_procurement.ingestion.adapters.seed import SeedPublicDataSource
from public_procurement.ingestion.adapters.seed_data import SEED_CUTOFF_AT, generate_seed_purchases
from public_procurement.ingestion.domain.purchase import (
    ItemClassification,
    Purchase,
    Source,
    UnitPriceStatus,
    VatBasis,
    build_purchase,
)


def _purchases() -> list[Purchase]:
    return [build_purchase(record) for record in generate_seed_purchases()]


def test_seed_generates_between_1000_and_1500_purchases_from_both_sources_when_loaded() -> None:
    # Arrange / Act
    purchases = _purchases()
    by_source = Counter(purchase.source for purchase in purchases)
    # Assert
    assert 1_000 <= len(purchases) <= 1_500
    assert by_source[Source.SECOP_II] > 300
    assert by_source[Source.TVEC] > 800
    assert all(date(2023, 1, 1) <= p.signed_on <= SEED_CUTOFF_AT.date() for p in purchases)
    assert all(purchase.items for purchase in purchases)


def test_seed_has_unique_source_identities_when_generated() -> None:
    # Arrange / Act
    purchases = _purchases()
    identities = {(p.source, p.source_record_id) for p in purchases}
    # Assert
    assert len(identities) == len(purchases)


def test_seed_produces_the_same_dataset_when_generated_twice() -> None:
    # Arrange
    generate_seed_purchases.cache_clear()
    first = generate_seed_purchases()
    generate_seed_purchases.cache_clear()
    # Act
    second = generate_seed_purchases()
    # Assert
    assert first == second


def test_seed_contains_mockup_reference_purchase_when_generated() -> None:
    # Arrange / Act
    reference = next(p for p in _purchases() if p.id_contrato == "CO1.PCCNTR.0000142")
    tv, accessory = reference.items
    # Assert
    assert reference.entity_department == "Valle del Cauca"
    assert reference.supplier_nit == "900.000.142-1"
    assert reference.modality == "Mínima cuantía"
    assert reference.total_value_cop == 39_600_000
    assert reference.signed_on == date(2026, 8, 14)
    assert (tv.classification, tv.quantity, tv.unit_price_cop) == (
        ItemClassification.INCLUDED,
        8,
        4_950_000,
    )
    assert tv.vat_basis is VatBasis.INCLUDED
    assert tv.attributes.screen_size_inches == 65
    assert accessory.classification is ItemClassification.EXCLUDED_ACCESSORY


def test_seed_includes_explicit_missing_data_states_when_generated() -> None:
    # Arrange
    items = [item for p in _purchases() for item in p.items]
    # Act
    statuses = Counter(item.unit_price_status for item in items)
    vat = Counter(item.vat_basis for item in items)
    # Assert
    assert statuses[UnitPriceStatus.NOT_PUBLISHED] > 0
    assert statuses[UnitPriceStatus.PENDING_REVIEW] > 0
    assert vat[VatBasis.UNDETERMINED] > 0
    assert all(
        item.unit_price_cop is None
        for item in items
        if item.unit_price_status is UnitPriceStatus.NOT_PUBLISHED
    )


def test_seed_amounts_are_integer_cop_when_generated() -> None:
    # Arrange
    purchases = _purchases()
    # Act
    amounts = [p.total_value_cop for p in purchases] + [
        item.unit_price_cop for p in purchases for item in p.items
    ]
    # Assert
    assert all(amount is None or type(amount) is int for amount in amounts)


def test_seed_never_carries_natural_person_documents_when_generated() -> None:
    # Arrange / Act
    natural_people = [p for p in _purchases() if p.supplier_is_natural_person]
    # Assert
    assert natural_people
    assert all(p.supplier_nit is None for p in natural_people)


def test_seed_source_returns_only_its_own_purchases_when_fetched() -> None:
    # Arrange
    source = SeedPublicDataSource(Source.TVEC)
    # Act
    purchases = list(source.fetch_purchases())
    # Assert
    assert purchases
    assert {purchase.source for purchase in purchases} == {Source.TVEC}
    assert source.cutoff_at == SEED_CUTOFF_AT
