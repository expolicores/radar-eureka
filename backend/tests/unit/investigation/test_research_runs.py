import json
import threading
import time
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from public_procurement.investigation.research import ResearchReportStore
from public_procurement.investigation.research_api import router
from public_procurement.investigation.run_background import ManualResearchRunner
from public_procurement.investigation.run_contracts import ResearchRunRequest
from public_procurement.investigation.run_pipeline import ExistingResearchPipeline

DATES = {"start_date": "2026-10-01", "end_date": "2026-10-31"}


def report(**summary):
    return {
        "schema_version": "research-proof-v1",
        "source": "socrata_secop",
        "processes": [],
        "comparisons": [],
        "signals": [],
        "summary": summary,
        "window_start": "2026-10-01",
        "window_before": "2026-11-01",
    }


def wait_done(runner, identifier):
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        run = runner.get(identifier)
        if run.status in {"completed", "completed_with_warnings", "failed"}:
            return run
        time.sleep(0.01)
    pytest.fail("Worker did not finish")


def client_for(runner):
    app = FastAPI()
    app.state.manual_research_runner = runner
    app.state.research_reports = ResearchReportStore(runner.directory)
    app.include_router(router)
    return TestClient(app)


def test_inclusive_dates_and_bogota_utc_bounds():
    window = ResearchRunRequest(**DATES)
    start, before = window.utc_bounds()
    assert start == datetime(2026, 10, 1, 5, tzinfo=UTC)
    assert before == datetime(2026, 11, 1, 5, tzinfo=UTC)
    one = ResearchRunRequest(start_date="2026-10-01", end_date="2026-10-01")
    assert (one.utc_bounds()[1] - one.utc_bounds()[0]).days == 1


@pytest.mark.parametrize(
    "data",
    [
        {"start_date": "2026-11-01", "end_date": "2026-10-31"},
        {"start_date": "2026-10-01"},
        {"end_date": "2026-10-31"},
        {"start_date": "2026-02-30", "end_date": "2026-03-01"},
        {"start_date": "2026-01-01", "end_date": "2026-10-31"},
        {**DATES, "region": "Boyaca"},
        {**DATES, "script": "untrusted.py"},
        {**DATES, "output_directory": "../../escape"},
        {"start_date": 0, "end_date": 0},
    ],
)
def test_invalid_dates_or_non_date_configuration_rejected(data):
    with pytest.raises(ValidationError):
        ResearchRunRequest.model_validate(data)


def test_post_returns_persisted_run_without_waiting_then_retrieves_result(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def execute(window, directory, stage):
        stage("discovery")
        entered.set()
        assert release.wait(4)
        assert window.model_dump(mode="json") == DATES
        return report(processes_found=3)

    runner = ManualResearchRunner(tmp_path, execute)
    client = client_for(runner)
    try:
        response = client.post("/api/v1/investigation/runs", json=DATES)
        assert response.status_code == 202
        assert response.json()["status"] == "queued"
        identifier = response.json()["run_id"]
        assert entered.wait(2)
        active = client.get(f"/api/v1/investigation/runs/{identifier}").json()
        assert active["status"] == "running"
        assert active["stage"] == "discovery"
        assert client.get("/api/v1/investigation/runs/active").json()["run_id"] == identifier
        repeated = client.post("/api/v1/investigation/runs", json=DATES)
        assert repeated.json()["run_id"] == identifier
        assert (
            client.post(
                "/api/v1/investigation/runs", json={**DATES, "end_date": "2026-10-30"}
            ).status_code
            == 409
        )
        release.set()
        done = wait_done(runner, identifier)
        assert done.status == "completed"
        assert done.finished_at is not None
        assert done.counts["processes_found"] == 3
        assert done.result_url == f"/explorar?run={identifier}"
        result = client.get(f"/api/v1/investigation/research?run_id={identifier}")
        assert result.json()["investigation_run_id"] == identifier
        assert client.get("/api/v1/investigation/runs/active").json() is None
        reopened = ManualResearchRunner(tmp_path, Mock())
        assert reopened.get(identifier).status == "completed"
    finally:
        release.set()
        runner.close()


def test_partial_result_completes_with_warnings(tmp_path):
    runner = ManualResearchRunner(tmp_path, lambda *_: report(documents_failed=2))
    run = runner.start(ResearchRunRequest(**DATES))
    done = wait_done(runner, run.run_id)
    assert done.status == "completed_with_warnings"
    assert done.warnings == ["documents_failed"]
    assert done.result_url is not None


def test_pipeline_failure_safe_and_previous_results_not_overwritten(tmp_path):
    store = ResearchReportStore(tmp_path)
    store.write(report())
    old = store.path.read_bytes()

    def fail(*_):
        raise RuntimeError("secret=DO_NOT_EXPOSE")

    runner = ManualResearchRunner(tmp_path, fail)
    done = wait_done(runner, runner.start(ResearchRunRequest(**DATES)).run_id)
    assert done.status == "failed"
    assert done.errors == ["pipeline_failed"]
    assert "DO_NOT_EXPOSE" not in done.model_dump_json()
    assert store.path.read_bytes() == old


def test_second_backend_does_not_interrupt_live_worker_or_publish_after_close(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def execute(*_):
        entered.set()
        assert release.wait(4)
        return report()

    first = ManualResearchRunner(tmp_path, execute)
    run = first.start(ResearchRunRequest(**DATES))
    try:
        assert entered.wait(2)
        second = ManualResearchRunner(tmp_path, Mock())
        assert second.get(run.run_id).status == "running"
        second.close()
        assert first.get(run.run_id).status == "running"
        first.close()
        release.set()
        assert first.get(run.run_id).status == "failed"
        assert first.get(run.run_id).errors == ["backend_restarted"]
        assert not ResearchReportStore(tmp_path).path.exists()
    finally:
        release.set()


def test_restart_recovery_and_safe_unknown_run(tmp_path):
    runner = ManualResearchRunner(tmp_path, Mock())
    request = ResearchRunRequest(**DATES)
    from public_procurement.investigation.run_contracts import ResearchRun

    start, before = request.utc_bounds()
    run = ResearchRun(
        run_id=uuid4(),
        status="running",
        **request.model_dump(),
        window_start_at=start,
        window_before_at=before,
        created_at=datetime.now(UTC),
    )
    runner._save(run)
    recovered = ManualResearchRunner(tmp_path, Mock())
    assert recovered.get(run.run_id).errors == ["backend_restarted"]
    client = client_for(recovered)
    assert client.get(f"/api/v1/investigation/runs/{uuid4()}").status_code == 404
    assert client.get("/api/v1/investigation/runs/../../escape").status_code == 404
    assert (
        client.post("/api/v1/investigation/runs", json={**DATES, "shell": "echo bad"}).status_code
        == 422
    )
    assert client.get("/api/v1/investigation/runs/policy").json()["max_window_days"] == 60


def test_existing_pipeline_calls_only_fixed_steps_and_exclusive_next_day(tmp_path, monkeypatch):
    calls = []

    class Loader:
        def create_module(self, spec):
            return None

        def exec_module(self, module):
            module.main = lambda argv: calls.append((module.__name__, argv))

    import importlib.util

    original = importlib.util.spec_from_file_location
    monkeypatch.setattr(
        importlib.util,
        "spec_from_file_location",
        lambda name, path: original(name, path, loader=Loader()),
    )
    (tmp_path / "research-cycle-report.json").write_text(json.dumps(report()), encoding="utf8")
    stages = []
    ExistingResearchPipeline()(ResearchRunRequest(**DATES), tmp_path, stages.append)
    assert len(calls) == 4
    assert stages == ["discovery", "documents_extraction", "research_report", "economic_cycle"]
    assert calls[0][1][-5:] == ["--before", "2026-11-01", "--days", "31", "--prepare"]
    assert all("--publish" not in argv for _, argv in calls)


def test_empty_discovery_prepares_empty_receipts_without_contract_request(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[3] / "scripts" / "eureka_investigation_discover.py"
    spec = importlib.util.spec_from_file_location("empty_discovery_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = Mock()
    source._page.return_value = []
    monkeypatch.setattr(module, "SocrataProcessSource", lambda: source)
    network = Mock(side_effect=AssertionError("No contract request for empty selection"))
    monkeypatch.setattr(module, "urlopen", network)
    module.main(
        ["--sample-directory", str(tmp_path), "--before", "2026-11-01", "--days", "31", "--prepare"]
    )
    assert json.loads((tmp_path / "selection.json").read_text(encoding="utf8"))["rows"] == []
    assert json.loads((tmp_path / "inventories.json").read_text(encoding="utf8")) == {}
    assert json.loads((tmp_path / "selected-documents.json").read_text(encoding="utf8")) == {}
    network.assert_not_called()
