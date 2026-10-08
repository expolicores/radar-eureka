from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError

from public_procurement.entrypoints.api.app import create_app
from public_procurement.shared.config import Settings

from ..builders import SettingsBuilder

pytestmark = pytest.mark.integration

WRONG_PASSWORD = "clave_incorrecta"
UNUSED_PORT = 5499


def _skip_if_server_accepts(url: URL) -> None:
    """El PostgreSQL embebido de desarrollo usa autenticación `trust`: acepta cualquier clave."""
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    try:
        with engine.connect():
            pytest.skip("el servidor no valida contraseñas (autenticación trust)")
    except OperationalError:
        return
    finally:
        engine.dispose()


def test_healthz_returns_200_when_real_postgres_is_available(
    database_settings: Settings,
) -> None:
    # Arrange
    app = create_app(database_settings)
    # Act
    with TestClient(app) as client:
        response = client.get("/healthz")
    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.parametrize(
    "break_url",
    [
        lambda url: url.set(port=UNUSED_PORT),
        lambda url: url.set(password=WRONG_PASSWORD),
    ],
    ids=["unused_port", "wrong_password"],
)
def test_healthz_returns_503_without_leaking_secrets_when_postgres_rejects_connection(
    database_settings: Settings,
    read_logs: Callable[[], list[dict[str, Any]]],
    break_url: Callable[[URL], URL],
) -> None:
    # Arrange
    broken_url = break_url(make_url(database_settings.database_url))
    _skip_if_server_accepts(broken_url)
    settings = (
        SettingsBuilder()
        .with_database_url(broken_url.render_as_string(hide_password=False))
        .build()
    )
    app = create_app(settings)
    # Act
    with TestClient(app) as client:
        response = client.get("/healthz")
    # Assert
    assert response.status_code == 503
    assert response.json()["title"] == "Servicio no disponible"
    assert WRONG_PASSWORD not in response.text
    assert all(WRONG_PASSWORD not in str(entry) for entry in read_logs())
