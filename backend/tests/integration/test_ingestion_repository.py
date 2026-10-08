import pytest
from sqlalchemy import Engine, func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from public_procurement.ingestion.domain.purchase import ItemClassification
from public_procurement.ingestion.repositories import (
    IngestionRunRecord,
    PurchaseItemRecord,
    PurchaseRecord,
    to_domain_purchase,
)
from public_procurement.shared.persistence import Base, create_session_factory

from .conftest import load_seed

pytestmark = pytest.mark.integration


def _count(engine: Engine, model: type[Base]) -> int:
    with engine.connect() as connection:
        return int(connection.execute(select(func.count()).select_from(model)).scalar_one())


def test_load_seed_persists_purchases_and_one_run_per_source_when_database_is_empty(
    migrated_engine: Engine,
) -> None:
    # Arrange / Act
    load_seed(migrated_engine)
    # Assert
    purchases = _count(migrated_engine, PurchaseRecord)
    assert 1_000 <= purchases <= 1_500
    with migrated_engine.connect() as connection:
        runs = connection.execute(
            select(
                IngestionRunRecord.source,
                IngestionRunRecord.read_count,
                IngestionRunRecord.new_count,
            )
        ).all()
    assert {run.source for run in runs} == {"secop_ii", "tvec"}
    assert sum(run.new_count for run in runs) == purchases
    assert all(run.read_count == run.new_count for run in runs)


def test_load_seed_does_not_duplicate_when_run_twice(migrated_engine: Engine) -> None:
    # Arrange
    load_seed(migrated_engine)
    purchases = _count(migrated_engine, PurchaseRecord)
    items = _count(migrated_engine, PurchaseItemRecord)
    # Act
    load_seed(migrated_engine)
    # Assert
    assert _count(migrated_engine, PurchaseRecord) == purchases
    assert _count(migrated_engine, PurchaseItemRecord) == items
    with migrated_engine.connect() as connection:
        latest = connection.execute(
            select(IngestionRunRecord.new_count)
            .order_by(IngestionRunRecord.started_at.desc())
            .limit(2)
        ).scalars()
        assert list(latest) == [0, 0]


def test_reference_purchase_round_trips_through_the_database_when_loaded(
    migrated_engine: Engine,
) -> None:
    # Arrange
    load_seed(migrated_engine)
    session = create_session_factory(migrated_engine)()
    # Act
    record = session.scalars(
        select(PurchaseRecord).where(PurchaseRecord.id_contrato == "CO1.PCCNTR.0000142")
    ).one()
    purchase = to_domain_purchase(record)
    session.close()
    # Assert
    assert purchase.total_value_cop == 39_600_000
    assert [item.classification for item in purchase.items] == [
        ItemClassification.INCLUDED,
        ItemClassification.EXCLUDED_ACCESSORY,
    ]
    assert purchase.items[0].unit_price_cop == 4_950_000


def test_schema_rejects_natural_person_document_when_inserted(migrated_engine: Engine) -> None:
    # Arrange
    statement = text(
        "INSERT INTO ingestion.purchase (id, source, id_contrato, entity_name, entity_department,"
        " supplier_name, supplier_nit, supplier_is_natural_person, object_description, modality,"
        " signed_on) VALUES (gen_random_uuid(), 'secop_ii', 'CO1.PCCNTR.9999999', 'Entidad',"
        " 'Meta', 'Persona', :document, true, 'Objeto', 'Mínima cuantía', '2026-01-01')"
    )
    # Act / Assert
    with (
        pytest.raises(IntegrityError, match="natural_person_without_document"),
        migrated_engine.begin() as connection,
    ):
        connection.execute(statement, {"document": "1.234.567.890"})


def test_schema_has_no_personal_document_columns_when_inspected(migrated_engine: Engine) -> None:
    # Arrange / Act
    columns = {
        column["name"] for column in inspect(migrated_engine).get_columns("purchase", "ingestion")
    }
    # Assert
    assert not {"supplier_document", "documento_proveedor", "cedula"} & columns
