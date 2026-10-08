"""Conexión a PostgreSQL y verificación de disponibilidad."""

import logging
from enum import StrEnum

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .config import Settings
from .logging import log_event

CONNECT_TIMEOUT_SECONDS = 3

logger = logging.getLogger("public_procurement.shared.database")


class DatabaseStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )


def check_database(engine: Engine) -> DatabaseStatus:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # Solo el tipo de error: el mensaje del driver puede incluir host o usuario.
        log_event(logger, "database_unavailable", logging.WARNING, error_type=type(exc).__name__)
        return DatabaseStatus.UNAVAILABLE
    return DatabaseStatus.OK
