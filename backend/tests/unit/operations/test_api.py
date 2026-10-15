import uuid
from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from public_procurement.entrypoints.api.app import create_app
from public_procurement.operations import services
from public_procurement.operations.repositories import CycleSchemaPendingError
from public_procurement.shared.config import Settings


def settings(**kwargs):
    return Settings(
        _env_file=None,
        database_url="postgresql+psycopg://unused@localhost/unused",
        eureka_radar_start_date=date(2026, 10, 13),
        **kwargs,
    )


def test_health_missing_schema_and_read_only_endpoints(monkeypatch):
    monkeypatch.setattr(
        services, "scheduler_status", lambda _: {"status": "unknown", "next_run": None}
    )
    monkeypatch.setattr(
        services, "ocr_runtime_status", lambda _: {"available": True, "language": "spa"}
    )
    sessions = Mock()
    sessions.return_value.__enter__ = Mock(return_value=Mock())
    sessions.return_value.__exit__ = Mock(return_value=False)
    queries = services.OperationsQueries(sessions, settings())
    queries.repository = Mock()
    queries.repository.ready.side_effect = CycleSchemaPendingError("migration pending")
    app = create_app(settings())
    app.state.operations_queries = queries
    with TestClient(app) as client:
        response = client.get("/api/operations/status")
        assert response.status_code == 200
        assert response.json()["diagnostic"] == "migration_0016_pending"
        assert response.json()["scheduler"]["status"] == "unknown"
        assert client.get("/api/operations/cycles").status_code == 503
        assert client.post("/api/operations/status").status_code == 405
        queries.repository.ready.side_effect = None
        queries.repository.listing.return_value = []
        assert client.get("/api/operations/cycles").json() == []
        queries.repository.detail.side_effect = LookupError("not found")
        assert (
            client.get("/api/operations/cycles/11111111-1111-4111-8111-111111111111").status_code
            == 404
        )


@pytest.mark.parametrize("start", [None, date(2099, 1, 1)])
def test_preflight_requires_explicit_nonfuture_start(start):
    with pytest.raises(ValueError, match="EUREKA_RADAR_START_DATE"):
        services.preflight(settings().model_copy(update={"eureka_radar_start_date": start}), Mock())


def test_preflight_only_queries_config_db_ocr(monkeypatch):
    monkeypatch.setattr(services, "ocr_runtime_status", lambda _: {"available": True})
    remote = Mock(side_effect=AssertionError("SECOP forbidden"))
    monkeypatch.setattr(services, "fetch_secop_processes", remote)
    session = Mock()
    session.scalar.return_value = None
    sessions = Mock()
    sessions.return_value.__enter__ = Mock(return_value=session)
    sessions.return_value.__exit__ = Mock(return_value=False)
    result = services.preflight(settings(), sessions, datetime(2026, 10, 14, 20, tzinfo=UTC))
    assert result["kind"] == "preflight_configuration_dry_run"
    assert result["secop_queried"] is False
    assert result["schema_ready"] is False
    assert result["window"]["from"] == "2026-10-13"
    assert result["window"]["before"] == "2026-10-15"
    assert all("INSERT" not in str(c) for c in session.execute.call_args_list)
    remote.assert_not_called()


def test_status_exposes_loaded_config_shared_with_manual_runner_without_secop(monkeypatch):
    configured = settings().model_copy(
        update={
            "eureka_radar_start_date": date(2026, 10, 5),
            "eureka_radar_max_processes": 2500,
            "eureka_radar_regions": "Boyacá,Casanare,Distrito Capital de Bogotá",
        }
    )
    remote = Mock(side_effect=AssertionError("No SECOP in configuration checks"))
    monkeypatch.setattr(services, "fetch_secop_processes", remote)
    monkeypatch.setattr(
        services, "scheduler_status", lambda _: {"status": "not_registered", "next_run": None}
    )
    monkeypatch.setattr(services, "ocr_runtime_status", lambda _: {"available": True})
    sessions = Mock()
    sessions.return_value.__enter__ = Mock(return_value=Mock())
    sessions.return_value.__exit__ = Mock(return_value=False)
    queries = services.OperationsQueries(sessions, configured)
    queries.repository = Mock()
    queries.repository.ready.side_effect = CycleSchemaPendingError("pending")
    app = create_app(configured)
    assert app.state.manual_cycle_runner.settings is app.state.operations_queries.settings
    app.state.operations_queries = queries
    with TestClient(app) as client:
        response = client.get("/api/operations/status")
        assert response.status_code == 200
        config = response.json()["execution_config"]
        assert config["start_date"] == "2026-10-05"
        assert config["before_exclusive"] is True
        assert config["max_processes"] == 2500
        assert config["regions"] == ["Boyacá", "Casanare", "Distrito Capital de Bogotá"]
    remote.assert_not_called()


def test_manual_radar_receives_configured_limit_without_calling_real_pipeline(monkeypatch):
    configured = settings(eureka_radar_max_processes=2500)
    radar = Mock()
    radar.config.page_size = 200
    radar.config.max_pages = 100
    monkeypatch.setattr(services, "build_radar_service", Mock(return_value=radar))
    remote = Mock(return_value=iter(()))
    monkeypatch.setattr(services, "fetch_secop_processes", remote)
    service = services.build_cycle_service(Mock(), configured)
    service.radar(uuid.uuid4(), Mock())
    assert radar.run.call_args.kwargs["max_processes"] == 2500
    remote.assert_not_called()
