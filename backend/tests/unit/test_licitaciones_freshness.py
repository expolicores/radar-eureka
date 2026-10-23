"""Local clock and fake provider only; no live source, storage or OCR."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import eureka_licitaciones_cdp as flow  # noqa: E402
import licitaciones_freshness as freshness  # noqa: E402
import licitaciones_search_plan as plans  # noqa: E402

NOW = datetime(2026, 10, 20, 16, tzinfo=freshness.BOGOTA)
ROW = {
    "Link": "https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.1",
    "idContrato": 1,
    "CodigoProceso": "TEST",
    "id_fuente_contract": 3,
    "key_config": "secop2",
    "TextoDepartamento": "Boyacá : Tunja",
    "Objeto": "Compra de refrigerios",
    "FechaPublicacion": NOW.isoformat(),
    "FechaVencimiento": "2026-10-30 09:00:00",
    "EstadoProceso": "Published",
}


def process(published):
    return {
        "process_reference": "licitaciones_info:1086005:1",
        "published_at": published,
        "id_fuente_contract": "3",
        "key_config": "secop2",
    }


@pytest.mark.parametrize(("age", "recent"), [(0, True), (6, True), (7, True), (8, False)])
def test_publication_age(age, recent):
    source = process((NOW - timedelta(days=age)).isoformat())
    rows, metrics, warnings = freshness.apply_freshness([source], 7, NOW)
    assert rows[0]["age_days"] == age
    assert rows[0]["recent"] is recent
    assert metrics["unique_processes_recent"] == int(recent)
    assert not warnings
    assert "recent" not in source


@pytest.mark.parametrize("published", ["invalid", None, "2026-02-30", ""])
def test_invalid_publication_is_preserved_and_warns(published):
    rows, metrics, warnings = freshness.apply_freshness([process(published)], 7, NOW)
    assert rows[0]["published_at"] == published
    assert rows[0]["age_days"] is None
    assert rows[0]["recent"] is False
    assert metrics["invalid_published_at"] == metrics["stale_processes"] == 1
    assert warnings[0]["code"] == "invalid_published_at"


def test_future_publication_is_not_candidate_and_warns():
    rows, metrics, warnings = freshness.apply_freshness(
        [process((NOW + timedelta(days=1)).isoformat())], 7, NOW
    )
    assert rows[0]["age_days"] == -1
    assert rows[0]["recent"] is False
    assert metrics["invalid_published_at"] == 0
    assert warnings[0]["code"] == "future_published_at"


def test_naive_bogota_and_aware_utc_have_same_age_and_boundary_is_exact():
    dates = ["2026-10-13T16:00:00", "2026-10-13T21:00:00Z", "2026-10-13T15:59:59"]
    rows, _, _ = freshness.apply_freshness([process(p) for p in dates], 7, NOW)
    assert [p["recent"] for p in rows] == [True, True, False]
    assert rows[0]["age_days"] == rows[1]["age_days"] == 7


def make_plan(tmp_path, days=7):
    config = json.loads(plans.DEFAULT_PLAN.read_text(encoding="utf-8"))
    ids = tmp_path / "boyaca.txt"
    ids.write_text(",".join(str(n) for n in range(123)), encoding="utf-8")
    config["regions"]["boyaca"]["ids_file"] = str(ids)
    config["unspsc"]["catalog_file"] = str(SCRIPTS.parent / "config/eureka_radar.v1.json")
    config["searches"] = config["searches"][:1]
    config["default_recent_days"] = days
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return plans.load_plan(path)


def client_for(rows):
    client = Mock()
    client.requests = 3
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.side_effect = [{"count": 1, "data": [ROW]}, {"count": len(rows), "data": rows}]
    return client


def test_plan_preserves_history_invalid_dates_and_provenance_without_extra_requests(tmp_path):
    plan = make_plan(tmp_path)
    rows = [
        ROW,
        {**ROW, "idContrato": 2, "FechaPublicacion": (NOW - timedelta(days=8)).isoformat()},
        {**ROW, "idContrato": 3, "FechaPublicacion": "bad-date"},
        {**ROW, "idContrato": 4, "FechaPublicacion": (NOW + timedelta(days=1)).isoformat()},
    ]
    client = client_for(rows)
    assert plans.run_plan(client, plan, tmp_path, Mock(), Mock(), now=NOW) == 0
    saved = json.loads((tmp_path / "discovery.json").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "search_plan_summary.json").read_text(encoding="utf-8"))
    assert len(saved["processes"]) == len(saved["eligible_total"]) == 4
    assert len(saved["eligible"]) == 1
    assert saved["processes"][2]["published_at"] == "bad-date"
    assert all(p["matched_searches"] == ["boyaca-refrigerio"] for p in saved["processes"])
    assert summary["unique_processes_total"] == summary["secop_ii_total"] == 4
    assert summary["unique_processes_recent"] == summary["secop_ii_recent"] == 1
    assert summary["stale_processes"] == 3
    assert summary["invalid_published_at"] == 1
    assert len(summary["warnings"]) == 2  # not duplicated by repeated saves
    assert summary["status"] == "completed_with_warnings"
    assert client.post.call_count == 2
    payload = client.post.call_args.args[1]
    assert set(payload["query"]) == {"Objeto", "ubicacion_filter"}
    assert not (tmp_path / "documents.json").exists()


def test_only_invalid_discovery_dates_do_not_abort_after_healthy_preflight(tmp_path):
    plan = make_plan(tmp_path)
    client = client_for([{**ROW, "FechaPublicacion": None}])
    assert plans.run_plan(client, plan, tmp_path, Mock(), Mock(), now=NOW) == 0
    summary = json.loads((tmp_path / "search_plan_summary.json").read_text(encoding="utf-8"))
    assert summary["invalid_published_at"] == 1
    assert summary["unique_processes_total"] == 1


@pytest.mark.parametrize(
    ("configured", "override", "recent"), [(7, None, 0), (10, None, 1), (10, 7, 0)]
)
def test_plan_configuration_and_explicit_override(tmp_path, configured, override, recent):
    plan = make_plan(tmp_path, configured)
    client = client_for([{**ROW, "FechaPublicacion": (NOW - timedelta(days=8)).isoformat()}])
    assert (
        plans.run_plan(client, plan, tmp_path, Mock(), Mock(), now=NOW, recent_days=override) == 0
    )
    summary = json.loads((tmp_path / "search_plan_summary.json").read_text(encoding="utf-8"))
    assert summary["unique_processes_recent"] == recent


@pytest.mark.parametrize("days", [7, 10])
def test_full_pipeline_only_opens_documents_for_recent_processes(monkeypatch, tmp_path, days):
    rows = [
        ROW,
        {**ROW, "idContrato": 2, "FechaPublicacion": (NOW - timedelta(days=8)).isoformat()},
        {**ROW, "idContrato": 3, "FechaPublicacion": "bad-date"},
    ]
    client = client_for(rows)
    monkeypatch.setattr(flow, "PageClient", lambda *a: client)
    monkeypatch.setattr(flow, "load_payload", lambda *a: {})
    inventory = Mock(return_value=[])
    monkeypatch.setattr(flow, "fetch_inventory", inventory)
    download, extract = Mock(), Mock()
    monkeypatch.setattr(flow.spike, "download_document", download)
    monkeypatch.setattr(flow.spike, "run_existing_extractor", extract)
    monkeypatch.setattr(flow.spike, "summarize_result", lambda *a: {"structured_facts": []})
    args = SimpleNamespace(
        profile_id="1086005",
        term="refrigerio",
        max_processes=30,
        max_document_processes=3,
        max_documents=2,
        location_ids_file=tmp_path,
        recent_days=days,
    )
    assert flow.run(Mock(), args, Mock(), tmp_path, {}, now=NOW) == 0
    assert [call.args[1]["idContrato"] for call in inventory.call_args_list] == (
        [1] if days == 7 else [1, 2]
    )
    download.assert_not_called()
    extract.assert_not_called()
    saved = json.loads((tmp_path / "discovery.json").read_text(encoding="utf-8"))
    assert len(saved["processes"]) == 3
    assert saved["processes"][2]["recent"] is False
    assert len(saved["eligible"]) == (1 if days == 7 else 2)
    assert client.post.call_count == 2


@pytest.mark.parametrize("days", ["0", "-1", "seven"])
def test_invalid_cli_recent_days_rejected_before_browser(days):
    with pytest.raises(SystemExit):
        flow.main(["--discovery-plan-only", "--recent-days", days])


def test_stale_only_full_run_never_opens_inventory_or_downloads(monkeypatch, tmp_path):
    client = client_for([{**ROW, "FechaPublicacion": (NOW - timedelta(days=8)).isoformat()}])
    monkeypatch.setattr(flow, "PageClient", lambda *a: client)
    monkeypatch.setattr(flow, "load_payload", lambda *a: {})
    inventory, download, extract = Mock(), Mock(), Mock()
    monkeypatch.setattr(flow, "fetch_inventory", inventory)
    monkeypatch.setattr(flow.spike, "download_document", download)
    monkeypatch.setattr(flow.spike, "run_existing_extractor", extract)
    args = SimpleNamespace(
        profile_id="1086005",
        term="refrigerio",
        max_processes=30,
        max_document_processes=3,
        max_documents=2,
        location_ids_file=tmp_path,
        recent_days=7,
    )
    assert flow.run(Mock(), args, Mock(), tmp_path, {}, now=NOW) == 0
    inventory.assert_not_called()
    download.assert_not_called()
    extract.assert_not_called()
    assert json.loads((tmp_path / "documents.json").read_text()) == []
    assert json.loads((tmp_path / "run_summary.json").read_text())["stale_processes"] == 1
