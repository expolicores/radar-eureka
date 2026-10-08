from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.entrypoints.api.app import create_app
from public_procurement.entrypoints.api.dependencies import get_engine
from public_procurement.shared.config import MissingConfigurationError

from ...doubles import SECRET_IN_DRIVER_MESSAGE, UnavailableDatabaseEngine

CLIENT_HEADERS = {
    "X-Correlation-ID": "3f2b8c1e-7a4d-4e9b-9c11-5d2a6f8e0b47",
    "X-Request-ID": "a91c0d5e-2b7f-4c3a-8e64-1f9d7b2c4e08",
}
ReadLogs = Callable[[], list[dict[str, Any]]]


def _request_log(read_logs: ReadLogs) -> dict[str, Any]:
    return next(entry for entry in read_logs() if entry["event"] == "request_completed")


def test_healthz_returns_200_when_database_is_available(client: TestClient) -> None:
    # Arrange / Act
    response = client.get("/healthz")
    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_healthz_returns_503_problem_details_when_database_is_unavailable(
    app: FastAPI, client: TestClient
) -> None:
    # Arrange
    app.dependency_overrides[get_engine] = UnavailableDatabaseEngine
    # Act
    response = client.get("/healthz", headers=CLIENT_HEADERS)
    # Assert
    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Servicio no disponible",
        "status": 503,
        "detail": "No fue posible verificar la conexión con la base de datos.",
    }
    assert response.headers["X-Correlation-ID"] == CLIENT_HEADERS["X-Correlation-ID"]
    assert response.headers["X-Request-ID"] == CLIENT_HEADERS["X-Request-ID"]


def test_healthz_logs_unavailable_database_without_secrets_when_database_fails(
    app: FastAPI, client: TestClient, read_logs: ReadLogs
) -> None:
    # Arrange
    app.dependency_overrides[get_engine] = UnavailableDatabaseEngine
    # Act
    client.get("/healthz", headers=CLIENT_HEADERS)
    # Assert
    entries = read_logs()
    failure = next(entry for entry in entries if entry["event"] == "database_unavailable")
    assert failure["error_type"] == "OperationalError"
    assert failure["correlation_id"] == CLIENT_HEADERS["X-Correlation-ID"]
    assert failure["request_id"] == CLIENT_HEADERS["X-Request-ID"]
    assert all(SECRET_IN_DRIVER_MESSAGE not in str(entry) for entry in entries)


def test_healthz_reuses_correlation_headers_in_response_and_log_when_they_are_valid(
    client: TestClient, read_logs: ReadLogs
) -> None:
    # Arrange / Act
    response = client.get("/healthz", headers=CLIENT_HEADERS)
    # Assert
    assert response.headers["X-Correlation-ID"] == CLIENT_HEADERS["X-Correlation-ID"]
    assert response.headers["X-Request-ID"] == CLIENT_HEADERS["X-Request-ID"]
    entry = _request_log(read_logs)
    assert entry["module"] == "public_procurement.entrypoints.api.middleware"
    assert entry["correlation_id"] == CLIENT_HEADERS["X-Correlation-ID"]
    assert entry["request_id"] == CLIENT_HEADERS["X-Request-ID"]
    assert entry["status_code"] == 200


@pytest.mark.parametrize(
    ("headers", "reused"),
    [
        ({}, set()),
        ({"X-Correlation-ID": CLIENT_HEADERS["X-Correlation-ID"]}, {"X-Correlation-ID"}),
        ({"X-Correlation-ID": "", "X-Request-ID": ""}, set()),
    ],
    ids=["no_headers", "only_correlation", "empty_headers"],
)
def test_healthz_generates_missing_or_invalid_correlation_headers_when_requested(
    client: TestClient, read_logs: ReadLogs, headers: dict[str, str], reused: set[str]
) -> None:
    # Arrange / Act
    response = client.get("/healthz", headers=headers)
    # Assert
    entry = _request_log(read_logs)
    for header, log_field in (
        ("X-Correlation-ID", "correlation_id"),
        ("X-Request-ID", "request_id"),
    ):
        value = response.headers[header]
        assert value
        assert entry[log_field] == value
        if header in reused:
            assert value == headers[header]
        else:
            assert value != headers.get(header)


def test_healthz_generates_different_identifiers_when_two_requests_have_no_headers(
    client: TestClient,
) -> None:
    # Arrange / Act
    first = client.get("/healthz")
    second = client.get("/healthz")
    # Assert
    assert first.headers["X-Correlation-ID"] != second.headers["X-Correlation-ID"]
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


def test_create_app_fails_with_spanish_message_when_database_url_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Arrange: directorio sin .env y entorno sin DATABASE_URL
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Act
    with pytest.raises(MissingConfigurationError) as error:
        create_app()
    # Assert
    assert str(error.value) == "Falta la variable de entorno obligatoria: DATABASE_URL."
