import threading
import time
import uuid
from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from public_procurement.entrypoints.api.app import create_app
from public_procurement.operations.background import ManualCycleRunner, ManualCycleStartError

from .test_cycle import result


def wait_for(predicate):
    deadline = time.monotonic() + 4
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError("worker did not finish")
        time.sleep(0.01)


def test_post_202_after_persisting_and_before_pipeline_finishes(setup):
    service, repo, radar, notify, _path = setup
    entered, release = threading.Event(), threading.Event()

    def blocked(*args):
        entered.set()
        assert release.wait(4)
        return result()

    radar.side_effect = blocked
    runner = ManualCycleRunner(None, service.settings, factory=lambda *args: service)
    app = create_app(service.settings)
    app.state.manual_cycle_runner = runner
    try:
        with TestClient(app) as client:
            response = client.post("/api/operations/cycles/manual", json={})
            assert response.status_code == 202
            identifier = response.json()["cycle_id"]
            assert uuid.UUID(identifier)
            assert repo.rows[identifier]["status"] == "running"
            assert entered.wait(1)
            assert not release.is_set()
            release.set()
            wait_for(lambda: repo.rows[identifier]["status"] == "completed")
            notify.assert_called_once()
            assert repo.rows[identifier]["notification_summary"]["disabled"]
    finally:
        release.set()


def test_ui_worker_captures_daily_window_once_without_using_env_start(setup):
    service, repo, _radar, _notify, _path = setup
    factory = Mock(return_value=service)
    runner = ManualCycleRunner(
        None,
        service.settings,
        factory=factory,
        clock=lambda: datetime(2026, 10, 16, 20, tzinfo=UTC),
    )
    result = runner.start()
    wait_for(lambda: repo.rows[result["cycle_id"]]["status"] == "completed")
    factory.assert_called_once_with(
        None, service.settings, (date(2026, 10, 14), date(2026, 10, 17))
    )


def test_global_lock_conflict_409_and_audited_skip(setup):
    service, repo, radar, notify, _path = setup
    repo.busy = True
    runner = ManualCycleRunner(None, service.settings, factory=lambda *args: service)
    app = create_app(service.settings)
    app.state.manual_cycle_runner = runner
    app.state.operations_queries.repository = Mock()
    app.state.operations_queries.repository.active.return_value = {"id": "active-fixture"}
    with TestClient(app) as client:
        response = client.post("/api/operations/cycles/manual", json={})
        assert response.status_code == 409
        payload = response.json()
        assert payload["reason"] == "already_running"
        assert payload["active_cycle_id"] == "active-fixture"
        assert repo.rows[payload["cycle_id"]]["status"] == "skipped"
        radar.assert_not_called()
        notify.assert_not_called()


def test_body_cannot_override_filters_and_preflight_failure_sanitized(setup):
    service, _repo, _radar, _notify, _path = setup
    app = create_app(service.settings)
    runner = Mock()
    app.state.manual_cycle_runner = runner
    with TestClient(app) as client:
        assert (
            client.post(
                "/api/operations/cycles/manual", json={"from_date": "2020-01-01"}
            ).status_code
            == 400
        )
        runner.start.assert_not_called()
        runner.start.side_effect = ManualCycleStartError("SECRET_CONNECTION_STRING")
        response = client.post("/api/operations/cycles/manual", json={})
        assert response.status_code == 503
        assert response.json()["stage"] == "preflight"
        assert "SECRET" not in response.text


def test_startup_timeout_cancels_before_radar(setup):
    service, repo, radar, notify, _path = setup
    release = threading.Event()

    def preflight():
        assert release.wait(4)
        return {"window": {}}

    service.preflight_check = preflight
    runner = ManualCycleRunner(
        None, service.settings, factory=lambda *args: service, startup_timeout=0.02
    )
    try:
        with pytest.raises(ManualCycleStartError, match="timeout"):
            runner.start()
    finally:
        release.set()
    wait_for(lambda: bool(repo.rows) and next(iter(repo.rows.values()))["status"] == "failed")
    radar.assert_not_called()
    notify.assert_not_called()


def test_restart_releases_worker_lock_but_not_false_active_from_running_rows(setup):
    service, _repo, radar, _notify, _path = setup
    runner = ManualCycleRunner(None, service.settings, factory=lambda *args: service)
    runner.close()
    with pytest.raises(ManualCycleStartError, match="shutting down"):
        runner.start()
    radar.assert_not_called()


def test_background_preflight_failure_is_sanitized_and_never_runs_pipeline(setup):
    service, repo, radar, notify, path = setup

    def fail(*args):
        raise ValueError("SECRET_DATABASE_URL")

    runner = ManualCycleRunner(
        None, service.settings.model_copy(update={"eureka_automation_log_path": path}), factory=fail
    )
    with pytest.raises(ManualCycleStartError, match="Could not persist"):
        runner.start()
    assert not repo.rows
    radar.assert_not_called()
    notify.assert_not_called()
    wait_for(lambda: bool(list(path.glob("*.log"))))
    assert "SECRET" not in next(path.glob("*.log")).read_text(encoding="utf-8")
