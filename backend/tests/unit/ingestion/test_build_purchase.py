import pytest

from public_procurement.ingestion.domain.purchase import (
    NATURAL_PERSON_SUPPLIER_NAME,
    ItemClassification,
    Source,
    UnitPriceStatus,
    VatBasis,
    build_purchase,
)

from ...builders import SourceItemBuilder, SourcePurchaseBuilder


def test_build_purchase_classifies_each_item_when_contract_is_mixed() -> None:
    # Arrange
    record = (
        SourcePurchaseBuilder()
        .with_items(
            SourceItemBuilder().build(),
            SourceItemBuilder()
            .with_line_number(2)
            .with_description("Soporte de pared para TV")
            .build(),
        )
        .build()
    )
    # Act
    purchase = build_purchase(record)
    # Assert
    assert [item.classification for item in purchase.items] == [
        ItemClassification.INCLUDED,
        ItemClassification.EXCLUDED_ACCESSORY,
    ]
    assert purchase.has_tv_items


def test_build_purchase_drops_unit_price_when_source_does_not_publish_it() -> None:
    # Arrange
    item = SourceItemBuilder().with_unit_price(4_950_000, UnitPriceStatus.NOT_PUBLISHED).build()
    record = SourcePurchaseBuilder().with_items(item).build()
    # Act
    purchase = build_purchase(record)
    # Assert
    assert purchase.items[0].unit_price_cop is None
    assert purchase.items[0].unit_price_status is UnitPriceStatus.NOT_PUBLISHED


def test_build_purchase_keeps_undetermined_vat_when_source_does_not_state_it() -> None:
    # Arrange
    item = SourceItemBuilder().with_vat_basis(VatBasis.UNDETERMINED).build()
    # Act
    purchase = build_purchase(SourcePurchaseBuilder().with_items(item).build())
    # Assert
    assert purchase.items[0].vat_basis is VatBasis.UNDETERMINED
    assert purchase.items[0].unit_price_cop == 4_950_000


def test_build_purchase_hides_document_when_supplier_is_natural_person() -> None:
    # Arrange
    record = SourcePurchaseBuilder().with_natural_person_supplier("1.234.567.890").build()
    # Act
    purchase = build_purchase(record)
    # Assert
    assert purchase.supplier_nit is None
    assert purchase.supplier_name == NATURAL_PERSON_SUPPLIER_NAME
    assert purchase.supplier_is_natural_person


def test_build_purchase_keeps_source_identifier_untransformed_when_source_is_tvec() -> None:
    # Arrange
    record = SourcePurchaseBuilder().from_tvec("166021").build()
    # Act
    purchase = build_purchase(record)
    # Assert
    assert purchase.source is Source.TVEC
    assert purchase.identificador_de_la_orden == "166021"
    assert purchase.id_contrato is None
    assert purchase.source_record_id == "166021"


def test_build_purchase_rejects_record_when_secop_contract_has_no_id_contrato() -> None:
    # Arrange
    record = SourcePurchaseBuilder().with_identifier("").build()
    # Act / Assert
    with pytest.raises(ValueError, match="secop_purchase_without_id_contrato"):
        build_purchase(record)
