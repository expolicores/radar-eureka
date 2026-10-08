import json
import logging
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.entrypoints.api.app import create_app
from public_procurement.entrypoints.api.dependencies import get_engine
from public_procurement.shared.logging import JsonFormatter

from .builders import SettingsBuilder
from .doubles import AvailableDatabaseEngine, ListLogHandler


@pytest.fixture
def app() -> FastAPI:
    application = create_app(SettingsBuilder().build())
    application.dependency_overrides[get_engine] = AvailableDatabaseEngine
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def read_logs() -> Iterator[Callable[[], list[dict[str, Any]]]]:
    """Devuelve las líneas de log JSON de la aplicación escritas durante la prueba."""
    # En el logger del paquete, no en el raíz: configure_logging reemplaza los handlers del raíz.
    handler = ListLogHandler()
    handler.setFormatter(JsonFormatter())
    package_logger = logging.getLogger("public_procurement")
    package_logger.addHandler(handler)
    yield lambda: [json.loads(line) for line in handler.lines]
    package_logger.removeHandler(handler)
