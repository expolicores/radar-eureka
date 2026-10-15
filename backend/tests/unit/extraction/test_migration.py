import importlib.util
import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from public_procurement.extraction.repositories import ContentFragmentRecord, ExtractionRunRecord


def test_migration_matches_models_and_reverses_in_memory(monkeypatch) -> None:
    backend = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "extraction_migration", backend / "alembic/versions/0009_extraction_schema.py"
    )
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("ATTACH DATABASE ':memory:' AS extraction"))
            monkeypatch.setattr(migration.op, "execute", lambda sql: None)
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                for model in (ExtractionRunRecord, ContentFragmentRecord):
                    columns = inspect(connection).get_columns(
                        model.__tablename__, schema="extraction"
                    )
                    assert {c["name"]: c["nullable"] for c in columns} == {
                        c.name: c.nullable for c in model.__table__.columns
                    }
                migration.downgrade()
            assert inspect(connection).get_table_names(schema="extraction") == []
    finally:
        engine.dispose()


def test_postgresql_sql_contains_version_fk_and_idempotency_index() -> None:
    output = io.StringIO()
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"), output_buffer=output)
    config.attributes["database_url"] = "postgresql+psycopg://offline@localhost:55432/offline_test"
    command.upgrade(config, "0008_eureka_discovery:0009_extraction_schema", sql=True)
    sql = output.getvalue()
    assert "REFERENCES documents.document_version (id)" in sql
    assert "CREATE UNIQUE INDEX uq_extraction_claim" in sql
    assert "source_locator JSONB" in sql
