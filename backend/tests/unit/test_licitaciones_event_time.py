import copy
from datetime import UTC, datetime, timedelta

from public_procurement.licitaciones_cdp.events import annotate_run, notice

NOW = datetime(2026, 10, 21, 23, 42, 16, tzinfo=UTC)


def test_warning_and_error_have_utc_time_run_and_exact_identity():
    item = {"metadata": {"id_ultima_fase": "CO1.NTC.123", "codigo_proceso": "CM-006-2026"}}
    for code in ("provider_status_deadline_conflict", "extraction_failed"):
        event = notice({"code": code}, "run-1", NOW, item)
        assert event["generated_at"] == "2026-10-21T23:42:16+00:00"
        assert event["run_id"] == "run-1"
        assert event["process_identity"] == "secop:CO1.NTC.123"
        assert event["message"]
        assert event["codigo_proceso"] == "CM-006-2026"


def test_same_warning_is_a_separate_event_in_each_run_and_not_restamped():
    first = notice({"code": "ocr_truncated"}, "run-1", NOW)
    second = notice({"code": "ocr_truncated"}, "run-2", NOW + timedelta(hours=1))
    assert first["generated_at"] != second["generated_at"]
    assert first["run_id"] != second["run_id"]
    assert notice(first, "run-1", NOW + timedelta(hours=3)) == first


def test_historical_event_exposes_unknown_time_without_borrowing_run_dates():
    run = {
        "id": "old-run",
        "started_at": NOW.isoformat(),
        "errors": [{"code": "session_expired"}],
        "metrics": {
            "warnings": [
                {"code": "provider_status_deadline_conflict", "process_reference": "local-1"}
            ]
        },
        "items": [{"secop_id": "local-1", "metadata": {"id_ultima_fase": "CO1.NTC.1"}}],
    }
    original = copy.deepcopy(run)
    result = annotate_run(copy.deepcopy(run))
    assert run == original
    for event in (result["errors"][0], result["metrics"]["warnings"][0]):
        assert event["generated_at"] is None
        assert event["timestamp_status"] == "not_recorded"
        assert event["run_id"] == "old-run"
    assert result["metrics"]["warnings"][0]["process_identity"] == "secop:CO1.NTC.1"


def test_nested_query_errors_preflight_and_process_events_are_annotated():
    run = {
        "id": "run-1",
        "errors": [],
        "metrics": {
            "preflight": {"warnings": [{"code": "provider_ignores_limit"}]},
            "queries": [{"error_code": "network_error", "warnings": [{"code": "transient_retry"}]}],
        },
        "items": [
            {"metadata": {"id_ultima_fase": "CO1.NTC.2"}, "warnings": [{"code": "ocr_truncated"}]}
        ],
    }
    annotate_run(run, NOW)
    events = [
        run["metrics"]["preflight"]["warnings"][0],
        run["metrics"]["queries"][0]["error"],
        run["metrics"]["queries"][0]["warnings"][0],
        run["items"][0]["warnings"][0],
    ]
    assert all(e["generated_at"] == NOW.isoformat() and e["run_id"] == "run-1" for e in events)
    assert events[-1]["process_identity"] == "secop:CO1.NTC.2"
