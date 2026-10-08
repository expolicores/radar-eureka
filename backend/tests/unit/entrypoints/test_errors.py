from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _fail() -> None:
    raise RuntimeError("detalle interno que no debe salir")


def test_unexpected_error_logs_traceback_with_correlation_when_endpoint_fails(
    app: FastAPI, read_logs: Callable[[], list[dict[str, Any]]]
) -> None:
    # Arrange
    app.add_api_route("/boom", _fail)
    # Act
    with TestClient(app) as client:
        client.get("/boom", headers={"X-Correlation-ID": "corr-500"})
    # Assert
    entry = next(entry for entry in read_logs() if entry["event"] == "unhandled_error")
    assert entry["error_type"] == "RuntimeError"
    assert entry["correlation_id"] == "corr-500"
    assert "Traceback" in entry["exception"]


def test_unexpected_error_returns_500_problem_details_with_headers_when_endpoint_fails(
    app: FastAPI,
) -> None:
    # Arrange
    app.add_api_route("/boom", _fail)
    headers = {"X-Correlation-ID": "corr-500", "X-Request-ID": "req-500"}
    # Act
    with TestClient(app) as client:
        response = client.get("/boom", headers=headers)
    # Assert
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Error interno"
    assert "detalle interno" not in response.text
    assert "Traceback" not in response.text
    assert response.headers["X-Correlation-ID"] == "corr-500"
    assert response.headers["X-Request-ID"] == "req-500"
