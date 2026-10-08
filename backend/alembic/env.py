"""Entorno de migraciones. La URL sale de la configuración por ambiente, nunca de alembic.ini."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from public_procurement.comparison import repositories as comparison_repositories  # noqa: F401
from public_procurement.ingestion import repositories as ingestion_repositories  # noqa: F401
from public_procurement.investigation import (
    repositories as investigation_repositories,  # noqa: F401
)
from public_procurement.market import repositories as market_repositories  # noqa: F401
from public_procurement.shared.config import load_settings
from public_procurement.shared.persistence import Base

config = context.config

if config.config_file_name is not None:
    # Sin desactivar los loggers de la aplicación que ya existan (p. ej. en los tests).
    fileConfig(config.config_file_name, disable_existing_loggers=False)

config.set_main_option("sqlalchemy.url", load_settings().database_url.replace("%", "%%"))

# Cada módulo registra sus tablas en Base.metadata al importar su repositorio (arriba).
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, include_schemas=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
