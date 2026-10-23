"""Offline plan tests; fake CDP, no provider, documents, OCR or DB."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import eureka_licitaciones_cdp as flow  # noqa: E402
import licitaciones_cdp_runtime as runtime  # noqa: E402
import licitaciones_search_plan as plans  # noqa: E402

ROW = {
    "Link": "https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.42",
    "idContrato": 42,
    "CodigoProceso": "TEST-2026",
    "id_fuente_contract": 3,
    "key_config": "secop2",
    "TextoDepartamento": "Boyacá : Tunja",
    "Objeto": "Refrigerios, papeleria y aseo",
    "FechaPublicacion": "2026-10-20 13:00:00",
    "FechaVencimiento": "2026-10-30 09:00:00",
    "EstadoProceso": "Published",
}


@pytest.fixture
def config(tmp_path):
    value = json.loads(plans.DEFAULT_PLAN.read_text(encoding="utf-8"))
    ids = tmp_path / "boyaca.txt"
    ids.write_text(",".join(str(i) for i in range(123)), encoding="utf-8")
    value["regions"]["boyaca"]["ids_file"] = str(ids)
    value["unspsc"]["catalog_file"] = str(SCRIPTS.parent / "config/eureka_radar.v1.json")
    return value


def load(config, tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return plans.load_plan(path)


def client_for(bodies):
    client = Mock()
    client.requests = 0
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.side_effect = [{"count": 31, "data": [ROW]}, *bodies]
    return client


def summary(tmp_path):
    return json.loads((tmp_path / "search_plan_summary.json").read_text(encoding="utf-8"))


def test_external_only_preflight_accepts_useful_aggregator_metadata(config, tmp_path):
    plan = load(config, tmp_path)
    client = client_for([])
    client.post.side_effect = None
    client.post.return_value = {
        "count": 31,
        "data": [
            {
                **ROW,
                "Link": "https://fao.taleo.net/jobs",
                "CodigoProceso": None,
                "id_fuente_contract": None,
                "key_config": None,
            }
        ]
        * 30,
    }
    events, wait = [], Mock()
    assert plans.run_plan(client, plan, tmp_path, wait, events.append) == 0
    result = summary(tmp_path)
    assert result["stop_reason"] is None
    assert result["preflight"]["preflight_status"] == "healthy"
    assert result["preflight"]["rows_total"] == 30
    assert "action" not in result
    assert any(e.get("preflight_status") == "healthy" for e in events)
    assert result["total_queries_executed"] == 6
    assert client.post.call_count == 7
    assert wait.call_count == 5


def test_config_reuses_locations_columns_and_existing_catalog(config, tmp_path):
    plan = load(config, tmp_path)
    assert len(plan["searches"]) == 6
    assert plan["searches"][0]["payload"] == runtime.load_payload(
        Path(config["regions"]["boyaca"]["ids_file"]), "refrigerio", 30
    )
    casanare = plan["searches"][3]["payload"]
    assert casanare["query"]["ubicacion_filter"].split(",") == [
        str(i) for i in range(4009001, 4009020)
    ]
    catalog = json.loads(Path(config["unspsc"]["catalog_file"]).read_text(encoding="utf-8"))
    assert set(plan["unspsc_catalog_codes"]) == {
        code for family in catalog["families"] for code in family["unspsc"]
    }
    assert "80141607" in plan["unspsc_catalog_codes"]
    assert plan["unspsc"]["status"] == "pending_remote_mapping"
    assert all(
        set(s["payload"]["query"]) == {"Objeto", "ubicacion_filter"} for s in plan["searches"]
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: c["searches"].append(
            {"id": "seventh", "region": "boyaca", "object_term": "aseo"}
        ),
        lambda c: c["limits"].update(max_queries_per_run=7),
        lambda c: c["limits"].update(page=2),
        lambda c: c["limits"].update(limit=31),
        lambda c: c["limits"].update(max_retries=2),
        lambda c: c["pauses"].update(sleep_between_queries=0),
        lambda c: c["regions"]["casanare"]["ids"].__setitem__(0, "9999999"),
        lambda c: c["searches"][0].update(Portal="secop2"),
        lambda c: c["unspsc"].update(status="validated", remote_key="UNSPSC"),
    ],
)
def test_unsafe_or_unvalidated_plan_rejected_before_connection(config, tmp_path, mutation):
    mutation(config)
    with pytest.raises(runtime.SpikeError):
        load(config, tmp_path)


def test_sequential_queries_waits_dedup_and_provenance(config, tmp_path):
    plan = load(config, tmp_path)
    timeline = []
    client = client_for([])

    def post(path, payload):
        timeline.append(("post", payload["query"].get("Objeto")))
        region = (
            "Casanare : Yopal"
            if payload["query"].get("ubicacion_filter", "").startswith("4009")
            else "Boyacá : Tunja"
        )
        return {"count": 31, "data": [{**ROW, "TextoDepartamento": region}]}

    client.post.side_effect = post
    plan["pauses"]["sleep_between_queries"] = 5

    def wait(seconds):
        timeline.append(("wait", seconds))

    assert plans.run_plan(client, plan, tmp_path, wait, lambda _: None) == 0
    result = summary(tmp_path)
    assert result["total_queries_executed"] == result["successful_queries"] == 6
    assert result["total_rows_received"] == 6
    assert result["unique_processes"] == result["unique_secop_ii"] == 1
    assert result["duplicates_across_queries"] == 5
    assert timeline == [
        ("post", None),
        ("post", "refrigerio"),
        ("wait", 5),
        ("post", "papeleria"),
        ("wait", 5),
        ("post", "aseo"),
        ("wait", 5),
        ("post", "refrigerio"),
        ("wait", 5),
        ("post", "papeleria"),
        ("wait", 5),
        ("post", "aseo"),
    ]
    discovery = json.loads((tmp_path / "discovery.json").read_text(encoding="utf-8"))
    process = discovery["processes"][0]
    assert len(process["matched_searches"]) == 6
    assert process["matched_objects"] == ["refrigerio", "papeleria", "aseo"]
    assert process["matched_regions"] == ["boyaca", "casanare"]
    assert process["matched_unspsc"] == []
    assert not (tmp_path / "documents.json").exists()
    assert not (tmp_path / "extraction.json").exists()
    assert not (tmp_path / "binaries").exists()


def test_pending_unspsc_is_never_sent_or_claimed_as_match(config, tmp_path):
    config["searches"] = config["searches"][:1]
    config["searches"][0]["unspsc"] = ["50192703"]
    plan = load(config, tmp_path)
    client = client_for([{"count": 1, "data": [ROW]}])
    assert plans.run_plan(client, plan, tmp_path, Mock(), Mock()) == 0
    payload = client.post.call_args.args[1]
    assert set(payload["query"]) == {"Objeto", "ubicacion_filter"}
    warnings = summary(tmp_path)["queries"][0]["warnings"]
    assert len(warnings) == 1
    assert warnings[0]["code"] == "pending_remote_mapping"
    assert warnings[0]["filter_sent"] is False
    assert warnings[0]["generated_at"]


@pytest.mark.parametrize("stage", ["preflight", "discovery"])
def test_expired_session_aborts_immediately(config, tmp_path, stage):
    plan = load(config, tmp_path)
    error = runtime.CandidateError("session_expired", runtime.MANUAL_LOGIN)
    client = client_for([error])
    if stage == "preflight":
        client.bootstrap.side_effect = error
    assert plans.run_plan(client, plan, tmp_path, Mock(), Mock()) == 12
    result = summary(tmp_path)
    assert result["stop_reason"] == "session_expired"
    assert result["total_queries_executed"] == int(stage == "discovery")
    assert client.post.call_count == (2 if stage == "discovery" else 0)


def transient_error():
    error = runtime.CandidateError("invalid_response", "Unavailable")
    error.transient = True
    error.http_status = 503
    return error


def test_single_transient_retry_then_abort_preserves_partial_results(config, tmp_path):
    plan = load(config, tmp_path)
    client = client_for([{"count": 1, "data": [ROW]}, transient_error(), transient_error()])
    wait = Mock()
    assert plans.run_plan(client, plan, tmp_path, wait, Mock()) == 17
    result = summary(tmp_path)
    assert result["stop_reason"] == "repeated_provider_failure"
    assert result["successful_queries"] == result["failed_queries"] == 1
    assert result["unique_processes"] == 1
    assert result["queries"][1]["attempts"] == 2
    assert client.post.call_count == 4  # preflight + success + two attempts
    assert wait.call_count == 2  # between queries and retry


def test_transient_failure_can_recover_with_one_retry(config, tmp_path):
    config["searches"] = config["searches"][:1]
    plan = load(config, tmp_path)
    client = client_for([transient_error(), {"count": 1, "data": [ROW]}])
    wait = Mock()
    assert plans.run_plan(client, plan, tmp_path, wait, Mock()) == 0
    wait.assert_called_once_with(4)
    assert summary(tmp_path)["queries"][0]["attempts"] == 2


@pytest.mark.parametrize(
    ("body", "queries", "reason"),
    [
        ({"count": 1337370, "data": [ROW]}, 1, "generic_dataset"),
        ("bad JSON", 2, "repeated_invalid_response"),
        ({"count": 31, "data": [ROW] * 31}, 2, "repeated_invalid_response"),
    ],
)
def test_provider_invalid_responses_stop_without_retry(config, tmp_path, body, queries, reason):
    plan = load(config, tmp_path)
    client = client_for([body, body])
    assert plans.run_plan(client, plan, tmp_path, Mock(), Mock()) != 0
    result = summary(tmp_path)
    assert result["total_queries_executed"] == queries
    assert result["stop_reason"] == reason
    assert all(query["attempts"] == 1 for query in result["queries"])


def test_filtered_empty_result_is_valid_after_health_probe(config, tmp_path):
    config["searches"] = config["searches"][:1]
    client = client_for([{"count": 0, "data": []}])
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, Mock(), Mock()) == 0
    assert summary(tmp_path)["unique_processes"] == 0


def test_plan_accepts_27_of_30_enriched_and_reports_skipped_rows(config, tmp_path):
    config["searches"] = config["searches"][:1]
    rows = [{**ROW, "idContrato": i} for i in range(1, 28)] + [
        {**ROW, "id_fuente_contract": None, "key_config": None}
    ] * 3
    client = client_for([{"count": 30, "data": rows}])
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, Mock(), Mock()) == 0
    result = summary(tmp_path)
    assert result["total_rows_received"] == 30
    assert result["unique_secop_ii"] == 27
    assert not result["queries"][0]["warnings"]  # Missing source hints are not invalid rows.


def test_rate_limit_aborts_without_retry_or_next_search(config, tmp_path):
    error = runtime.CandidateError("invalid_response", "Rate limited")
    error.http_status = 429
    client = client_for([error])
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, Mock(), Mock()) == 17
    assert summary(tmp_path)["stop_reason"] == "rate_limited"
    assert client.post.call_count == 2


def test_first_invalid_query_can_recover_without_replaying_it(config, tmp_path):
    config["searches"] = config["searches"][:2]
    client = client_for(["bad JSON", {"count": 1, "data": [ROW]}])
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, Mock(), Mock()) == 2
    result = summary(tmp_path)
    assert result["status"] == "completed_with_errors"
    assert result["successful_queries"] == result["failed_queries"] == 1
    assert result["unique_processes"] == 1
    assert result["stop_reason"] is None


def test_zero_retries_stops_on_first_transient_failure(config, tmp_path):
    config["limits"]["max_retries"] = 0
    client = client_for([transient_error()])
    wait = Mock()
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, wait, Mock()) == 17
    wait.assert_not_called()
    assert summary(tmp_path)["queries"][0]["attempts"] == 1


def test_unexpected_query_failure_is_recorded_without_secret_exception_text(config, tmp_path):
    client = client_for([RuntimeError("sensitive-content")])
    events = []
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, Mock(), events.append) == 1
    result = summary(tmp_path)
    assert result["failed_queries"] == 1
    assert result["queries"][0]["status"] == "failed"
    assert "sensitive-content" not in json.dumps(result) + json.dumps(events)


def test_local_region_object_and_secop_ii_filter(config, tmp_path):
    config["searches"] = config["searches"][:1]
    rows = [
        ROW,
        {**ROW, "idContrato": 43, "id_fuente_contract": 1, "key_config": "other"},
        {**ROW, "idContrato": 44, "id_fuente_contract": 1},
        {**ROW, "idContrato": 45, "Objeto": "Combustible"},
        {**ROW, "idContrato": 46, "TextoDepartamento": "Casanare : Yopal"},
        ROW,
    ]
    client = client_for([{"count": 6, "data": rows}])
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, Mock(), Mock()) == 0
    result = summary(tmp_path)
    assert result["unique_processes"] == 3
    assert result["unique_secop_ii"] == 2
    assert result["duplicates_across_queries"] == 0  # within-query duplicate excluded


def test_missing_id_falls_back_to_source_profile_codigo(config, tmp_path):
    config["searches"] = config["searches"][:2]
    client = client_for([{"count": 1, "data": [{**ROW, "idContrato": None}]}] * 2)
    assert plans.run_plan(client, load(config, tmp_path), tmp_path, Mock(), Mock()) == 0
    assert summary(tmp_path)["unique_processes"] == 1
    assert summary(tmp_path)["duplicates_across_queries"] == 1


@pytest.mark.parametrize(
    ("status", "timeout", "transient"),
    [(503, False, True), (None, True, True), (200, False, False), (429, False, False)],
)
def test_transport_exposes_only_safe_retry_metadata(status, timeout, transient):
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.return_value = {"status": status, "timeout": timeout, "password": "secret"}
    events = []
    client = runtime.PageClient(page, "1086005", events.append)
    with pytest.raises(runtime.CandidateError) as error:
        client.post("/cliente/contratos/get-info/MP?perfiles=1086005", {"query": {}})
    assert error.value.transient == transient
    assert error.value.http_status == status
    assert "secret" not in json.dumps(events)


def test_cli_plan_bypasses_settings_ocr_and_old_pipeline(config, tmp_path, monkeypatch):
    plan = load(config, tmp_path)
    page = Mock()
    playwright = Mock()
    playwright.__enter__ = Mock(return_value=playwright)
    playwright.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("playwright.sync_api.sync_playwright", lambda: playwright)
    monkeypatch.setattr(flow, "connect_browser", lambda *a: Mock())
    monkeypatch.setattr(flow, "find_page", lambda *a: page)
    monkeypatch.setattr(flow, "LOCAL", tmp_path / "output")
    monkeypatch.setattr(flow, "load_plan", lambda _: plan)
    monkeypatch.setattr(
        flow.spike, "Settings", Mock(side_effect=AssertionError("Settings forbidden"))
    )
    monkeypatch.setattr(flow, "check_ocr", Mock(side_effect=AssertionError("OCR forbidden")))
    monkeypatch.setattr(flow, "run", Mock(side_effect=AssertionError("Full pipeline forbidden")))
    run = Mock(return_value=0)
    monkeypatch.setattr(flow, "run_plan", run)
    assert (
        flow.main(["--discovery-plan-only", "--search-plan", "offline.json", "--recent-days", "10"])
        == 0
    )
    assert run.call_args.args[1] is plan
    assert run.call_args.kwargs["recent_days"] == 10
    run.call_args.args[3](5)
    page.wait_for_timeout.assert_called_once_with(5000)


def test_search_plan_cannot_accidentally_enter_full_mode():
    with pytest.raises(SystemExit):
        flow.main(["--search-plan", "offline.json"])
