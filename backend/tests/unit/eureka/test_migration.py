import importlib.util
import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from public_procurement.eureka.repositories import OpportunityRecord
from public_procurement.ingestion.process_repositories import SecopProcessRecord


def test_migration_matches_model_and_reverses_in_memory(monkeypatch) -> None:
    backend = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "eureka_migration", backend / "alembic/versions/0008_eureka_discovery.py"
    )
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("ATTACH DATABASE ':memory:' AS ingestion"))
            connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
            SecopProcessRecord.__table__.create(connection)
            monkeypatch.setattr(migration.op, "execute", lambda sql: None)
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                columns = inspect(connection).get_columns("opportunity", schema="eureka")
                assert {c["name"]: c["nullable"] for c in columns} == {
                    c.name: c.nullable for c in OpportunityRecord.__table__.columns
                }
                unique = inspect(connection).get_unique_constraints("opportunity", schema="eureka")
                assert any(c["column_names"] == ["process_id"] for c in unique)
                migration.downgrade()
            assert inspect(connection).get_table_names(schema="eureka") == []
    finally:
        engine.dispose()


def test_postgres_offline_sql_contains_real_process_fk_and_jsonb() -> None:
    backend = Path(__file__).resolve().parents[3]
    output = io.StringIO()
    config = Config(str(backend / "alembic.ini"), output_buffer=output)
    config.attributes["database_url"] = "postgresql+psycopg://offline@localhost:55432/offline_test"
    command.upgrade(config, "0007_documents_schema:0008_eureka_discovery", sql=True)
    sql = output.getvalue()
    assert "REFERENCES ingestion.secop_process (id)" in sql
    assert "matched_categories JSONB" in sql
