import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from public_procurement.documents.repositories import (
    AcquisitionAttemptRecord,
    DocumentProcessRecord,
    DocumentRecord,
    DocumentVersionRecord,
)


def test_migration_matches_models_in_disposable_memory(monkeypatch) -> None:
    path = Path(__file__).resolve().parents[3] / "alembic/versions/0007_documents_schema.py"
    spec = importlib.util.spec_from_file_location("documents_migration", path)
    assert spec is not None
    assert spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("ATTACH DATABASE ':memory:' AS documents"))
            # SQLite usa ATTACH como esquema; omitir solo CREATE/DROP SCHEMA de PostgreSQL.
            monkeypatch.setattr(migration.op, "execute", lambda sql: None)
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                for model in (
                    DocumentRecord,
                    DocumentProcessRecord,
                    DocumentVersionRecord,
                    AcquisitionAttemptRecord,
                ):
                    columns = inspect(connection).get_columns(
                        model.__tablename__, schema="documents"
                    )
                    assert {c["name"]: c["nullable"] for c in columns} == {
                        c.name: c.nullable for c in model.__table__.columns
                    }
                unique = inspect(connection).get_unique_constraints(
                    "document_version", schema="documents"
                )
                assert any(c["column_names"] == ["document_id", "sha256"] for c in unique)
                migration.downgrade()
            assert inspect(connection).get_table_names(schema="documents") == []
    finally:
        engine.dispose()
