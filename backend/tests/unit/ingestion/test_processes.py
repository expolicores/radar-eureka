import importlib.util
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.ingestion.domain.process import ProcessQuery, SecopProcess, unique_processes
from public_procurement.ingestion.process_repositories import (
    ProcessSyncRunRecord,
    SecopProcessRecord,
)
from public_procurement.ingestion.services import ProcessIngestionService


def process(identifier="CO1.REQ.11172521", portfolio="CO1.BDOS.10985405") -> SecopProcess:
    return SecopProcess(
        identifier,
        portfolio,
        "012-2026",
        "Entidad",
        "Boyacá",
        "Covarachía",
        "Compra",
        None,
        "Mínima cuantía",
        "Presentación de oferta",
        "Publicado",
        date(2026, 10, 7),
        None,
        1_000_000,
        None,
        None,
    )


@pytest.fixture
def sessions():
    # Base efímera en memoria: jamás usa DATABASE_URL ni PostgreSQL de desarrollo.
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS ingestion"))
        SecopProcessRecord.__table__.create(connection)
        ProcessSyncRunRecord.__table__.create(connection)
    yield sessionmaker(engine, expire_on_commit=False)
    engine.dispose()


class ProcessSource:
    def __init__(self, values):
        self.values = values

    def fetch_processes(self, query):
        yield from self.values


def test_identity_distinguishes_processes_sharing_portfolio() -> None:
    first, second = process(), process("CO1.REQ.999")
    assert first.identity != second.identity
    assert len(unique_processes([first, first, second])) == 2


def test_conflicting_duplicates_are_rejected() -> None:
    first = process()
    with pytest.raises(ValueError, match="contradictorias"):
        unique_processes([first, replace(first, status="Cerrado")])


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"published_from": date(2026, 10, 1)},
        {"published_from": date(2026, 10, 8), "published_before": date(2026, 10, 1)},
        {"portfolio_id": " "},
        {"portfolio_id": "P", "page_size": 0},
        {"portfolio_id": "P", "max_pages": 0},
    ],
)
def test_unbounded_or_invalid_query_is_rejected(kwargs) -> None:
    with pytest.raises(ValueError, match=r".+"):
        ProcessQuery(**kwargs)


def test_repeated_sync_is_idempotent_and_updates_preserve_identity(sessions) -> None:
    service = ProcessIngestionService(sessions, clock=lambda: datetime(2026, 10, 12, tzinfo=UTC))
    first = process()
    query = ProcessQuery(portfolio_id=first.id_del_portafolio)
    result = service.run(ProcessSource([first, first]), query)
    assert (result.read_count, result.unique_count, result.changed_count) == (2, 1, 1)
    with sessions() as session:
        identifier = session.scalar(select(SecopProcessRecord.id))
    repeated = service.run(ProcessSource([first]), query)
    assert repeated.changed_count == 0
    changed = service.run(ProcessSource([replace(first, status="Cerrado")]), query)
    assert changed.changed_count == 1
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(SecopProcessRecord)) == 1
        assert session.scalar(select(SecopProcessRecord.id)) == identifier
        assert session.scalar(select(SecopProcessRecord.status)) == "Cerrado"
        assert session.scalar(select(func.count()).select_from(ProcessSyncRunRecord)) == 3


def test_network_failure_does_not_open_transaction(sessions) -> None:
    class FailingSource:
        def fetch_processes(self, query):
            yield process()
            raise RuntimeError("Socrata no disponible")

    with pytest.raises(RuntimeError, match="no disponible"):
        ProcessIngestionService(sessions).run(FailingSource(), ProcessQuery(portfolio_id="P"))
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(SecopProcessRecord)) == 0
        assert session.scalar(select(func.count()).select_from(ProcessSyncRunRecord)) == 0


def test_conflict_rolls_back_whole_sync(sessions) -> None:
    first = process()
    with pytest.raises(ValueError, match="contradictorias"):
        ProcessIngestionService(sessions).run(
            ProcessSource([first, replace(first, status="Cerrado")]), ProcessQuery(portfolio_id="P")
        )
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(SecopProcessRecord)) == 0


def test_migration_matches_process_models_and_reverses_in_memory() -> None:
    migration_path = (
        Path(__file__).resolve().parents[3] / "alembic/versions/0006_ingestion_processes.py"
    )
    spec = importlib.util.spec_from_file_location("process_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("ATTACH DATABASE ':memory:' AS ingestion"))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                inspector = inspect(connection)
                for model in (SecopProcessRecord, ProcessSyncRunRecord):
                    actual = {
                        c["name"]: c["nullable"]
                        for c in inspector.get_columns(model.__tablename__, schema="ingestion")
                    }
                    assert actual == {c.name: c.nullable for c in model.__table__.columns}
                constraints = inspector.get_unique_constraints("secop_process", schema="ingestion")
                assert any(
                    c["column_names"] == ["dataset_id", "id_del_proceso"] for c in constraints
                )
                migration.downgrade()
            assert inspect(connection).get_table_names(schema="ingestion") == []
    finally:
        engine.dispose()
