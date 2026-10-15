import importlib.util
import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from public_procurement.extraction.structured_repositories import StructuredFactRecord


def test_structured_migration_matches_model_and_is_reversible_in_memory():
    backend = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "structured_migration",
        backend / "alembic/versions/0010_structured_extraction.py",
    )
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("ATTACH DATABASE ':memory:' AS extraction"))
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                columns = inspect(connection).get_columns("structured_fact", schema="extraction")
                assert {c["name"]: c["nullable"] for c in columns} == {
                    c.name: c.nullable for c in StructuredFactRecord.__table__.columns
                }
                migration.downgrade()
            assert inspect(connection).get_table_names(schema="extraction") == []
    finally:
        engine.dispose()


def test_structured_postgresql_sql_is_offline_and_has_traceability_and_unique_key():
    output = io.StringIO()
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"), output_buffer=output)
    config.attributes["database_url"] = "postgresql+psycopg://offline@localhost:55432/offline_test"
    command.upgrade(config, "0009_extraction_schema:0010_structured_extraction", sql=True)
    sql = output.getvalue()
    assert "REFERENCES extraction.content_fragment (id)" in sql
    assert "REFERENCES documents.document_version (id)" in sql
    assert "uq_structured_fact_evidence" in sql
    assert "source_locator JSONB" in sql
