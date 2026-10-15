import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect, text

from public_procurement.shared.config import Settings

from .conftest import ALEMBIC_INI, migration_config

pytestmark = pytest.mark.integration


def _alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def _head() -> str:
    head = ScriptDirectory.from_config(_alembic_config()).get_current_head()
    assert head is not None
    return head


def _public_tables(engine: Engine) -> set[str]:
    return set(inspect(engine).get_table_names(schema="public"))


def _versions(engine: Engine) -> list[str]:
    with engine.connect() as connection:
        return list(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())


@pytest.fixture
def clean_database(database_engine: Engine, database_settings: Settings) -> Engine:
    command.downgrade(migration_config(database_settings), "base")
    with database_engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    return database_engine


def test_upgrade_registers_initial_revision_only_when_database_is_empty(
    clean_database: Engine,
    database_settings: Settings,
) -> None:
    # Arrange: base sin tablas
    assert _public_tables(clean_database) == set()
    # Act
    command.upgrade(migration_config(database_settings), "head")
    # Assert
    assert _versions(clean_database) == [_head()]
    assert _public_tables(clean_database) == {"alembic_version"}


def test_upgrade_changes_nothing_when_run_twice(
    clean_database: Engine, database_settings: Settings
) -> None:
    # Arrange
    command.upgrade(migration_config(database_settings), "head")
    # Act
    command.upgrade(migration_config(database_settings), "head")
    # Assert
    assert _versions(clean_database) == [_head()]
    assert _public_tables(clean_database) == {"alembic_version"}


def test_radar_schema_has_historical_jsonb_identity_and_module_relations(migrated_engine):
    from sqlalchemy.dialects.postgresql import JSONB

    inspector = inspect(migrated_engine)
    assert {"radar_run", "radar_process_state", "radar_run_process", "alert"}.issubset(
        inspector.get_table_names(schema="eureka")
    )
    constraints = inspector.get_unique_constraints("alert", schema="eureka")
    assert any(
        item["column_names"] == ["opportunity_id", "alert_type", "rule_version"]
        for item in constraints
    )
    fields = {
        item["name"]: item["type"] for item in inspector.get_columns("alert", schema="eureka")
    }
    assert isinstance(fields["reasons"], JSONB)
    assert isinstance(fields["snapshot"], JSONB)
    foreign_keys = inspector.get_foreign_keys("radar_process_state", schema="eureka")
    assert any(
        item["referred_schema"] == "ingestion" and item["referred_table"] == "secop_process"
        for item in foreign_keys
    )
