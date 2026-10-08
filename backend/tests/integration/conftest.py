from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine

from public_procurement.comparison.services import build_comparison_service
from public_procurement.ingestion.adapters.seed import SeedPublicDataSource
from public_procurement.ingestion.services import Source, build_ingestion_service
from public_procurement.market.adapters.seed import SeedRetailObservationSource
from public_procurement.market.services import build_market_ingestion_service
from public_procurement.shared.config import Settings, load_settings
from public_procurement.shared.database import create_db_engine
from public_procurement.shared.persistence import create_session_factory

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


@pytest.fixture(scope="session")
def database_settings() -> Settings:
    """Configuración real: requiere DATABASE_URL apuntando a un PostgreSQL 16 disponible."""
    return load_settings()


@pytest.fixture
def database_engine(database_settings: Settings) -> Iterator[Engine]:
    engine = create_db_engine(database_settings)
    yield engine
    engine.dispose()


@pytest.fixture
def migrated_engine(database_engine: Engine) -> Engine:
    """Base vacía con todas las migraciones aplicadas."""
    config = Config(str(ALEMBIC_INI))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return database_engine


def load_seed(engine: Engine) -> None:
    """Mismo flujo que `load-seed` de la CLI: compras, mercado simulado y recálculo."""
    session_factory = create_session_factory(engine)
    service = build_ingestion_service(session_factory)
    for source in (Source.SECOP_II, Source.TVEC):
        service.run(SeedPublicDataSource(source))
    build_market_ingestion_service(session_factory).load(SeedRetailObservationSource())
    build_comparison_service(session_factory).recalculate()


@pytest.fixture(scope="module")
def seeded_engine(database_settings: Settings) -> Iterator[Engine]:
    """Base migrada con la carga seed, compartida por los tests de lectura de un módulo de test."""
    engine = create_db_engine(database_settings)
    config = Config(str(ALEMBIC_INI))
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    load_seed(engine)
    yield engine
    engine.dispose()
