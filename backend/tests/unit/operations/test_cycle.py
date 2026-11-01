import copy
import json
from contextlib import contextmanager
from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest

from public_procurement.operations.adapters.file_logs import CycleLogs
from public_procurement.operations.services import AutomationCycleService
from public_procurement.shared.config import Settings


class Repository:
    def __init__(self):
        self.rows = {}
        self.busy = False

    def ready(self):
        pass

    @contextmanager
    def lock(self):
        yield None if self.busy else lambda: None

    def save(self, cycle):
        self.rows[cycle["id"]] = copy.deepcopy(cycle)

    def running(self):
        return [copy.deepcopy(r) for r in self.rows.values() if r["status"] == "running"]


def result(status="completed", failures=0, items=None):
    return dict(
        status=status,
        failures=failures,
        processes_seen=len(items or []),
        candidates=0,
        enriched=0,
        alerts_created=0,
        errors=[],
        items=items or [],
    )


@pytest.fixture
def setup(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url="postgresql://unused",
        eureka_radar_start_date=date(2026, 10, 13),
    )
    repository = Repository()
    notify = Mock(
        return_value={"disabled": True, "prepared": 0, "sent": 0, "captured": 0, "failed": 0}
    )
    radar = Mock(return_value=result())
    logs = CycleLogs(tmp_path, 30)
    service = AutomationCycleService(
        repository,
        radar,
        notify,
        logs,
        settings,
        lambda: {"window": {"from": "2026-10-13", "before": "2026-10-15"}},
    )
    return service, repository, radar, notify, tmp_path


def test_success_zero_processes_disabled_and_persistent_logs(setup):
    service, repo, radar, notify, path = setup
    cycle = service.run()
    assert cycle["status"] == "completed"
    assert cycle["notification_summary"]["disabled"]
    assert cycle["metrics"]["secop_records_fetched"] == 0
    assert repo.rows[cycle["id"]] == cycle
    assert len(list(path.glob("*.log"))) == len(list(path.glob("*.json"))) == 1
    assert json.loads(next(path.glob("*.json")).read_text(encoding="utf-8")) == cycle
    radar.assert_called_once()
    notify.assert_called_once()


def test_availability_failure_is_persisted_and_does_not_repeat_run(setup):
    service, repo, radar, notify, _ = setup
    diagnostic = {
        "performed": True,
        "status": "diagnostic_failed",
        "latest_available_date": None,
        "query_window_start": "2026-10-13",
        "query_window_before": "2026-10-15",
    }
    radar.return_value = {**result(), "metrics": {"socrata_availability_diagnostic": diagnostic}}
    cycle = service.run()
    assert cycle["status"] == "completed"
    assert cycle["source_summary"]["socrata_availability_diagnostic"] == diagnostic
    assert repo.rows[cycle["id"]] == cycle
    radar.assert_called_once()
    notify.assert_called_once()


def test_metadata_exclusion_counters_are_reported_without_changing_cycle_policy(setup):
    service, _repo, radar, notify, _path = setup
    output = result(items=[{"reason": "metadata_object_exclusion", "outcome": "no_alert"}])
    output["metrics"] = {
        "metadata_alerts_excluded_by_object": 1,
        "metadata_exclusion_policy_errors": 0,
    }
    radar.return_value = output
    cycle = service.run()
    assert cycle["metrics"]["metadata_alerts_excluded_by_object"] == 1
    assert cycle["reasons"]["metadata_object_exclusion"] == 1
    assert cycle["metrics"]["no_alert"] == 1
    assert cycle["status"] == "completed"
    notify.assert_called_once()


@pytest.mark.parametrize("status", ["failed", "interrupted"])
def test_incomplete_never_dispatches(setup, status):
    service, _repo, radar, notify, _path = setup
    radar.return_value = result(status)
    cycle = service.run()
    assert cycle["status"] == "failed"
    notify.assert_not_called()
    assert cycle["notification_summary"]["reason"] == "radar_incomplete"


def test_operational_limit_warns_without_inventing_technical_failure(setup):
    service, repo, radar, notify, _path = setup
    radar.return_value = result(
        "limited", items=[{"reason": "limit_deferred", "outcome": "skipped"}]
    )
    cycle = service.run()
    assert cycle["status"] == "completed_with_warnings"
    assert cycle["radar_status"] == "limited"
    assert cycle["coverage_complete"] is False
    assert cycle["failures"] == 0
    assert cycle["metrics"]["limit_deferred"] == 1
    assert cycle["errors"][0]["code"] == "radar_limited"
    assert cycle["errors"][0]["severity"] == "warning"
    assert repo.rows[cycle["id"]] == cycle
    notify.assert_not_called()


def test_limit_does_not_hide_a_global_failure(setup):
    service, _repo, radar, notify, _path = setup
    radar.return_value = {
        **result("limited"),
        "errors": [{"stage": "source", "type": "ValueError"}],
    }
    cycle = service.run()
    assert cycle["status"] == "failed"
    assert cycle["failures"] == 1
    notify.assert_not_called()


def test_global_exception_sanitized(setup):
    service, _repo, radar, notify, path = setup
    radar.side_effect = RuntimeError("SECRET_CREDENTIAL_OR_PROVIDER_BODY")
    cycle = service.run()
    assert cycle["status"] == "failed"
    notify.assert_not_called()
    assert "SECRET" not in json.dumps(cycle)
    assert "SECRET" not in next(path.glob("*.log")).read_text()


def test_missing_offer_deadline_counts_as_prefilter_rejection_and_preserves_trace(setup):
    service, _repo, radar, _notify, path = setup
    diagnostic = {
        "reason": "missing_or_invalid_offer_deadline",
        "field": "fecha_de_recepcion_de",
        "raw_value": "-",
        "rule": "valid_offer_deadline_required",
        "outcome": "skipped",
        "stage": "metadata",
        "secop_id": "P",
    }

    def execute(identifier, observe):
        observe("secop_received", {})
        observe("process_result", diagnostic)
        return result(items=[diagnostic])

    radar.side_effect = execute
    cycle = service.run()
    assert cycle["status"] == "completed"
    assert cycle["metrics"]["prefilter_rejected"] == 1
    assert cycle["reasons"][diagnostic["reason"]] == 1
    event = next(e for e in cycle["events"] if e["event"] == "process_result")
    for key in ("reason", "field", "raw_value", "rule"):
        assert event[key] == diagnostic[key]
    saved = json.loads(next(path.glob("*.json")).read_text(encoding="utf-8"))
    assert saved["events"] == cycle["events"]


def test_individual_document_failure_warns_but_dispatches(setup):
    service, _repo, radar, notify, _path = setup

    def execute(identifier, observe):
        observe("stage", {"name": "documents_sync", "secop_id": "P"})
        observe("process_result", {"reason": None, "outcome": "failed", "stage": "documents_sync"})
        return result("partial", 1, [{"outcome": "failed"}])

    radar.side_effect = execute
    cycle = service.run()
    assert cycle["status"] == "completed_with_warnings"
    assert cycle["metrics"]["document_errors"] == 1
    assert cycle["metrics"]["document_sync_failed"] == 1
    notify.assert_called_once()


def test_metadata_only_is_operational_warning_not_technical_failure(setup):
    service, _repo, radar, _notify, _path = setup

    def execute(identifier, observe):
        observe(
            "process_result",
            {
                "outcome": "alert",
                "stage": "documents_pending",
                "document_status": "unavailable",
                "secop_id": "P",
            },
        )
        return result(items=[{"outcome": "alert", "reason": "documents_unavailable"}])

    radar.side_effect = execute
    cycle = service.run()
    assert cycle["status"] == "completed_with_warnings"
    assert cycle["failures"] == 0
    assert cycle["errors"][0]["code"] == "documents_unavailable"
    assert cycle["errors"][0]["severity"] == "warning"


@pytest.mark.parametrize(("ocr", "processed"), [("ocr_success", 1), ("ocr_unavailable", 0)])
def test_ocr_metrics(setup, ocr, processed):
    service, _repo, radar, _notify, _path = setup

    def execute(identifier, observe):
        observe(
            "extraction_result",
            {
                "ocr": ocr,
                "processed": processed,
                "required": 1,
                "native": False,
                "failed": not processed,
                "ocr_seconds": 0.5,
            },
        )
        return result("partial" if not processed else "completed", int(not processed))

    radar.side_effect = execute
    cycle = service.run()
    assert cycle["metrics"]["ocr_required"] == 1
    assert cycle["metrics"]["extraction_ocr"] == processed
    assert cycle["metrics"]["ocr_unavailable"] == int(not processed)
    assert cycle["durations_ms"]["ocr"] == 500


def test_capture_and_notification_failure_summary(setup):
    service, _repo, _radar, notify, _path = setup
    notify.return_value = {"prepared": 1, "captured": 1}
    cycle = service.run()
    assert cycle["metrics"]["notification_captured"] == 1
    notify.return_value = {"prepared": 1, "failed": 1}
    assert service.run()["status"] == "completed_with_warnings"
    notify.side_effect = TimeoutError("secret")
    cycle = service.run()
    assert cycle["status"] == "completed_with_warnings"
    assert cycle["metrics"]["notification_failed"] == 1


def test_busy_is_audited_without_running_stages(setup):
    service, repo, radar, notify, _path = setup
    repo.busy = True
    cycle = service.run()
    assert cycle["status"] == "skipped"
    assert cycle["reason"] == "already_running"
    assert cycle["id"] in repo.rows
    radar.assert_not_called()
    notify.assert_not_called()


def test_recovery_uses_lock_not_age_and_restarts_once(setup):
    service, repo, _radar, _notify, _path = setup
    old = service.run()
    old.update(status="running", finished_at=None, heartbeat_at=datetime.now(UTC).isoformat())
    repo.save(old)
    repo.busy = True
    service.run()
    assert repo.rows[old["id"]]["status"] == "running"
    repo.busy = False
    service.run()
    recovered = repo.rows[old["id"]]
    assert recovered["status"] == "failed"
    assert recovered["errors"][-1]["code"] == "coordinator_interrupted"
    assert recovered["errors"][-1]["stale_diagnostic"] is False


def test_dry_run_never_creates_rows_or_files_or_runs_stages(setup):
    service, repo, radar, notify, path = setup
    assert service.run(dry_run=True)["window"]["from"] == "2026-10-13"
    assert repo.rows == {}
    assert list(path.iterdir()) == []
    radar.assert_not_called()
    notify.assert_not_called()


def test_scheduled_disabled_leaves_manual_available(setup):
    service, _repo, radar, _notify, _path = setup
    assert service.run(trigger="scheduled")["reason"] == "automation_disabled"
    radar.assert_not_called()
    assert service.run()["status"] == "completed"


def test_log_failure_not_silently_success(setup):
    service, repo, _radar, _notify, _path = setup
    service.logs = Mock()
    service.logs.write.side_effect = OSError("disk full SECRET")
    cycle = service.run()
    assert cycle["status"] == "completed_with_warnings"
    assert any(e["code"] == "log_write_failed" for e in cycle["errors"])
    assert "SECRET" not in json.dumps(repo.rows)
