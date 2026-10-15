import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.config import DEFAULT_CONFIG
from public_procurement.eureka.repositories import OpportunityRecord
from public_procurement.eureka.services import EurekaService, build_eureka_service
from public_procurement.ingestion.process_repositories import SecopProcessRecord

from .test_discovery import facts


@pytest.fixture
def sessions():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        # Emular las funciones de texto de PostgreSQL en la base efímera.
        connection.connection.driver_connection.create_function(
            "translate",
            3,
            lambda value, source, target: (
                value.translate(str.maketrans(source, target)) if value is not None else None
            ),
        )
        connection.connection.driver_connection.create_function(
            "lower", 1, lambda value: value.lower() if value is not None else None
        )
        connection.execute(text("ATTACH DATABASE ':memory:' AS ingestion"))
        connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        SecopProcessRecord.__table__.create(connection)
        OpportunityRecord.__table__.create(connection)
    yield sessionmaker(engine, expire_on_commit=False)
    engine.dispose()


class Source:
    def __init__(self, process):
        self.process = process

    def iter_processes(self, reference, department):
        yield self.process


def test_idempotence_updates_data_and_rules_preserving_identity_and_discovery_time(
    sessions,
) -> None:
    now = datetime(2026, 10, 12, tzinfo=UTC)
    source = Source(facts(title="Papelería"))
    service = EurekaService(sessions, source, clock=lambda: now)
    list(service.evaluate(reference="CO1.REQ.1"))
    with sessions() as session:
        row = session.scalar(select(OpportunityRecord))
        identifier, discovered_at = row.id, row.discovered_at
    list(service.evaluate(reference="CO1.REQ.1"))
    source.process = replace(source.process, base_price_cop=4_000_000)
    now += timedelta(hours=1)
    updated_rules = replace(
        DEFAULT_CONFIG,
        version="eureka-discovery-v2",
        weights=replace(DEFAULT_CONFIG.weights, product=40),
    )
    result = next(service.evaluate(reference="CO1.REQ.1", config=updated_rules))
    with sessions() as session:
        row = session.scalar(select(OpportunityRecord))
        assert session.scalar(select(func.count()).select_from(OpportunityRecord)) == 1
        assert row.id == identifier
        assert row.discovered_at == discovered_at
        assert row.evaluated_at > discovered_at
        assert row.score == result.score == 50
        assert row.rule_version == "eureka-discovery-v2"
        assert row.config_snapshot["weights"]["product"] == 40
        assert row.reasons[0]["points"] == 40


def test_dry_run_does_not_insert_or_update(sessions) -> None:
    source = Source(facts(title="Papelería"))
    service = EurekaService(sessions, source)
    list(service.evaluate(reference="CO1.REQ.1", dry_run=True))
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(OpportunityRecord)) == 0
    list(service.evaluate(reference="CO1.REQ.1"))
    source.process = replace(source.process, title="Sin coincidencias")
    list(service.evaluate(reference="CO1.REQ.1", dry_run=True))
    with sessions() as session:
        assert session.scalar(select(OpportunityRecord.score)) == 30


def test_real_ingestion_adapter_reads_batch_and_uuid_without_changing_processes(sessions) -> None:
    identifier = uuid.uuid4()
    with sessions.begin() as session:
        session.add(
            SecopProcessRecord(
                id=identifier,
                dataset_id="p6dx-8zbt",
                id_del_proceso="CO1.REQ.1",
                department="Boyacá",
                title="Papelería",
                acquired_at=datetime.now(UTC),
            )
        )
        session.add(
            SecopProcessRecord(
                id=uuid.uuid4(),
                dataset_id="p6dx-8zbt",
                id_del_proceso="CO1.REQ.2",
                department="Casanare",
                title="Refrigerios",
                acquired_at=datetime.now(UTC),
            )
        )
    service = build_eureka_service(sessions)
    result = list(service.evaluate(department="BOYACA", dry_run=True))
    assert len(result) == 1
    assert result[0].process_id == identifier
    assert next(service.evaluate(reference=str(identifier), dry_run=True)).score == 30
    assert next(service.evaluate(reference="CO1.REQ.1", dry_run=True)).score == 30
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(SecopProcessRecord)) == 2


def test_closed_result_can_replace_active_without_deleting_source(sessions) -> None:
    source = Source(facts(title="Papelería"))
    service = EurekaService(sessions, source)
    list(service.evaluate(reference="CO1.REQ.1"))
    source.process = replace(source.process, status="Vencido")
    list(service.evaluate(reference="CO1.REQ.1"))
    with sessions() as session:
        assert session.scalar(select(OpportunityRecord.active)) is False
        assert session.scalar(select(OpportunityRecord.state)) == "closed"


def test_missing_process_and_ambiguous_filters_fail(sessions) -> None:
    service = build_eureka_service(sessions)
    with pytest.raises(ValueError, match="exactamente"):
        list(service.evaluate())
    with pytest.raises(ValueError, match="no encontrado"):
        list(service.evaluate(reference="CO1.REQ.unknown", dry_run=True))
