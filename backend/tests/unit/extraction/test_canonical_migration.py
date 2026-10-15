import importlib.util
import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from public_procurement.extraction.canonical_repositories import (
    CanonicalEvidenceRecord,
    CanonicalFactRecord,
)


def test_canonical_migration_matches_models_and_reverses_without_other_tables():
    backend = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "canonical_migration", backend / "alembic/versions/0011_fact_consolidation.py"
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
                for model in (CanonicalFactRecord, CanonicalEvidenceRecord):
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


def test_canonical_offline_postgresql_sql_has_normalized_links_and_snapshot_uniqueness():
    output = io.StringIO()
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"), output_buffer=output)
    config.attributes["database_url"] = "postgresql+psycopg://offline@localhost:55432/offline_test"
    command.upgrade(config, "0010_structured_extraction:0011_fact_consolidation", sql=True)
    sql = output.getvalue()
    assert "REFERENCES extraction.structured_fact (id)" in sql
    assert "REFERENCES extraction.canonical_fact (id)" in sql
    assert "uq_canonical_snapshot_fact" in sql
    assert "canonical_value JSONB" in sql
