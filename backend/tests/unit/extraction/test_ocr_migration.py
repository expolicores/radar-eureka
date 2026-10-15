import importlib.util
import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from public_procurement.extraction.repositories import ExtractionDiagnosticRecord


def test_diagnostics_migration_is_additive_and_matches_model():
    backend = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "ocr_migration", backend / "alembic/versions/0013_ocr_diagnostics.py"
    )
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS extraction"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            columns = inspect(connection).get_columns(
                "extraction_run_diagnostic", schema="extraction"
            )
            assert {c["name"]: c["nullable"] for c in columns} == {
                c.name: c.nullable for c in ExtractionDiagnosticRecord.__table__.columns
            }
            migration.downgrade()
        assert inspect(connection).get_table_names(schema="extraction") == []
    engine.dispose()


def test_postgresql_migration_sql_only_creates_diagnostic_table():
    output = io.StringIO()
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"), output_buffer=output)
    config.attributes["database_url"] = "postgresql+psycopg://offline@localhost:55432/offline_test"
    command.upgrade(config, "0012_eureka_radar:0013_ocr_diagnostics", sql=True)
    sql = output.getvalue()
    assert "CREATE TABLE extraction.extraction_run_diagnostic" in sql
    assert "payload JSONB" in sql
    assert "REFERENCES extraction.extraction_run (id)" in sql
    assert "ALTER TABLE" not in sql
    assert "DELETE FROM" not in sql
