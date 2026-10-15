"""Explicit opt-in guarded *_test database only; never uses development as fallback."""

import os
import threading
import time
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_procurement.entrypoints.api.app import create_app
from public_procurement.eureka.services import build_radar_service
from public_procurement.operations.background import ManualCycleRunner
from public_procurement.operations.repositories import CycleRepository
from public_procurement.operations.services import build_cycle_service
from public_procurement.shared.config import load_settings
from public_procurement.shared.testing import settings_for_test_database


@pytest.fixture
def setup(tmp_path):
    url = os.environ.get("OPERATIONS_ACCEPTANCE_DATABASE_URL")
    if not url:
        pytest.skip("OPERATIONS_ACCEPTANCE_DATABASE_URL required; dedicated *_test only")
    settings = settings_for_test_database(load_settings(test_database_url=url)).model_copy(
        update={
            "eureka_automation_log_path": tmp_path,
            "eureka_notification_enabled": False,
            "eureka_notification_mode": "disabled",
            "eureka_radar_start_date": date(2026, 10, 13),
        }
    )
    engine = create_engine(settings.database_url)
    with engine.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == "0016_eureka_operations"
    sessions = sessionmaker(engine, expire_on_commit=False)
    service = build_cycle_service(sessions, settings)

    def empty_radar(identifier, observer):
        return build_radar_service(sessions, settings, observer=observer).run(
            [],
            start=date(2026, 10, 13),
            before=date(2026, 10, 15),
            regions=("Boyacá", "Casanare"),
            run_id=identifier,
        )

    service.radar = empty_radar
    yield service, settings, sessions
    engine.dispose()


def test_real_lock_busy_audited_and_real_empty_cycle_persists(setup):
    service, settings, sessions = setup
    repository = CycleRepository(sessions)
    with repository.lock() as held:
        assert held is not None
        blocked = service.run()
        assert blocked["status"] == "skipped"
        assert repository.detail(uuid.UUID(blocked["id"]))["reason"] == "already_running"
    first = service.run()
    second = service.run()
    assert first["status"] == second["status"] == "completed"
    assert first["notification_summary"]["disabled"]
    assert repository.detail(uuid.UUID(first["id"]))["radar_linked"]
    with sessions() as c:
        for table in (
            "eureka.alert",
            "notifications.notification",
            "notifications.notification_alert",
        ):
            # This dedicated acceptance database is initially empty of business fixtures.
            assert c.scalar(text(f"SELECT count(*) FROM {table}")) == 0  # noqa: S608 - fixed table allowlist
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/operations/cycles/" + first["id"]).status_code == 200
        response = client.get("/api/operations/status")
        assert response.status_code == 200
        assert response.json()["schema_ready"]


def test_recover_recent_running_without_age_gate(setup):
    service, _settings, _sessions = setup
    cycle = service.run()
    cycle.update(status="running", finished_at=None)
    service.repository.save(cycle)
    assert service.run()["status"] == "completed"
    old = service.repository.detail(uuid.UUID(cycle["id"]))
    assert old["status"] == "failed"
    assert old["errors"][-1]["code"] == "coordinator_interrupted"
    assert old["errors"][-1]["stale_diagnostic"] is False


def test_manual_post_persisted_202_conflict_polling_and_repeat_without_source_calls(setup):
    service, settings, sessions = setup
    empty_radar = service.radar
    entered, release = threading.Event(), threading.Event()

    def controlled_radar(identifier, observer):
        entered.set()
        if not release.wait(10):
            raise RuntimeError("Controlled fixture timed out")
        return empty_radar(identifier, observer)

    service.radar = controlled_radar
    app = create_app(settings)
    app.state.manual_cycle_runner = ManualCycleRunner(
        sessions, settings, factory=lambda *args: service
    )

    def wait_completed(client, identifier):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            response = client.get("/api/operations/cycles/" + identifier)
            if response.json()["status"] == "completed":
                return response.json()
            time.sleep(0.03)
        raise AssertionError("Controlled cycle did not finish")

    try:
        with TestClient(app) as client:
            first = client.post("/api/operations/cycles/manual", json={})
            assert first.status_code == 202
            identifier = first.json()["cycle_id"]
            assert entered.wait(1)
            assert CycleRepository(sessions).detail(uuid.UUID(identifier))["status"] == "running"
            assert client.get("/api/operations/cycles/" + identifier).json()["coordinator_active"]
            duplicate = client.post("/api/operations/cycles/manual", json={})
            assert duplicate.status_code == 409
            assert duplicate.json()["active_cycle_id"] == identifier
            assert (
                CycleRepository(sessions).detail(uuid.UUID(duplicate.json()["cycle_id"]))["reason"]
                == "already_running"
            )
            release.set()
            done = wait_completed(client, identifier)
            assert done["source_summary"]["zero_records_confirmed"]
            assert done["notification_summary"]["disabled"]
            repeated = client.post("/api/operations/cycles/manual", json={})
            assert repeated.status_code == 202
            assert repeated.json()["cycle_id"] != identifier
            assert (
                wait_completed(client, repeated.json()["cycle_id"])["metrics"]["alert_created"] == 0
            )
    finally:
        release.set()
