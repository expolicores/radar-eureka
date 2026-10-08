import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect, text

from .conftest import ALEMBIC_INI

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
def clean_database(database_engine: Engine) -> Engine:
    command.downgrade(_alembic_config(), "base")
    with database_engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    return database_engine


def test_upgrade_registers_initial_revision_only_when_database_is_empty(
    clean_database: Engine,
) -> None:
    # Arrange: base sin tablas
    assert _public_tables(clean_database) == set()
    # Act
    command.upgrade(_alembic_config(), "head")
    # Assert
    assert _versions(clean_database) == [_head()]
    assert _public_tables(clean_database) == {"alembic_version"}


def test_upgrade_changes_nothing_when_run_twice(clean_database: Engine) -> None:
    # Arrange
    command.upgrade(_alembic_config(), "head")
    # Act
    command.upgrade(_alembic_config(), "head")
    # Assert
    assert _versions(clean_database) == [_head()]
    assert _public_tables(clean_database) == {"alembic_version"}
