"""Offline deadline classification and document gating from existing metadata."""

import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import eureka_licitaciones_cdp as flow  # noqa: E402
from licitaciones_candidate_contracts import CandidateProcess  # noqa: E402
from licitaciones_freshness import BOGOTA  # noqa: E402
from licitaciones_search_plan import DEFAULT_PLAN, load_plan, run_plan  # noqa: E402
from licitaciones_validity import apply_validity  # noqa: E402

NOW = datetime(2026, 10, 20, 16, tzinfo=BOGOTA)
ROW = {
    "Link": "https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.1",
    "idContrato": 1,
    "CodigoProceso": "TEST",
    "id_fuente_contract": 3,
    "key_config": "secop2",
    "TextoDepartamento": "Boyacá : Tunja",
    "Objeto": "Refrigerio y papeleria",
    "FechaPublicacion": "2026-10-20 12:00:00",
    "FechaVencimiento": "2026-10-21 10:00:00",
    "EstadoProceso": "Published",
}


@pytest.mark.parametrize(
    ("raw", "status", "expected", "warning"),
    [
        ("2026-10-21 10:00:00", "ClosedForReplies", "open", None),
        ("2026-10-19 10:00:00", "ClosedForReplies", "closed", None),
        ("2026-10-20 16:00:00", "ClosedForReplies", "closed", None),
        (None, "Published", "unknown", None),
        ("", "Published", "unknown", None),
        ("invalid", "Published", "unknown", "invalid_deadline_at"),
        ("2026-10-19 10:00:00", "Published", "closed", "provider_status_deadline_conflict"),
        ("2026-10-20 16:00:00", "abierto", "closed", "provider_status_deadline_conflict"),
    ],
)
def test_deadline_controls_validity_independently_of_provider_state(raw, status, expected, warning):
    source = CandidateProcess.from_source(
        {**ROW, "FechaVencimiento": raw, "EstadoProceso": status}, "1086005"
    ).to_dict()
    source["recent"] = True
    result, counters, warnings = apply_validity([source], NOW)
    assert result[0]["validity_status"] == expected
    assert result[0]["validity_warning"] == warning
    assert result[0]["deadline_timezone"] == "America/Bogota"
    assert result[0]["provider_status"] == status
    assert result[0]["raw_source_reference"]["FechaVencimiento"] == raw
    assert result[0]["raw_source_reference"]["EstadoProceso"] == status
    assert counters[f"secop_ii_{expected}"] == 1
    assert len(warnings) == int(warning is not None)
    assert source["validity_status"] == "unknown"  # annotation does not mutate input


def test_timezone_offset_is_normalized_and_exact_boundary_is_closed():
    source = CandidateProcess.from_source(
        {**ROW, "FechaVencimiento": "2026-10-20T21:00:00Z"}, "1086005"
    ).to_dict()
    source["recent"] = True
    result, _, _ = apply_validity([source], NOW)
    assert result[0]["deadline_at"] == "2026-10-20T16:00:00-05:00"
    assert result[0]["validity_status"] == "closed"


def make_rows():
    return [
        ROW,
        {**ROW, "idContrato": 2, "FechaVencimiento": "2026-10-19 10:00:00"},
        {**ROW, "idContrato": 3, "FechaVencimiento": None},
        {**ROW, "idContrato": 4, "FechaVencimiento": "invalid"},
        {**ROW, "idContrato": 5, "FechaPublicacion": "2026-10-01 12:00:00"},
        {**ROW, "idContrato": 6, "id_fuente_contract": 1, "key_config": "secop1"},
    ]


def client_for(rows):
    client = Mock()
    client.requests = 3
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.side_effect = [{"count": 1, "data": [ROW]}, {"count": len(rows), "data": rows}]
    return client


def test_full_flow_retains_closed_and_unknown_but_selects_only_recent_secop_open(
    monkeypatch, tmp_path
):
    client = client_for(make_rows())
    monkeypatch.setattr(flow, "PageClient", lambda *a: client)
    monkeypatch.setattr(flow, "load_payload", lambda *a: {})
    inventory = Mock(return_value=[])
    monkeypatch.setattr(flow, "fetch_inventory", inventory)
    monkeypatch.setattr(flow.spike, "summarize_result", lambda *a: {"structured_facts": []})
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
    assert [c.args[1]["idContrato"] for c in inventory.call_args_list] == [1]
    discovery = json.loads((tmp_path / "discovery.json").read_text(encoding="utf-8"))
    summary = json.loads((tmp_path / "run_summary.json").read_text(encoding="utf-8"))
    assert len(discovery["processes"]) == 6
    assert len(discovery["eligible_total"]) == 6
    assert len(discovery["eligible_recent"]) == 5
    assert len(discovery["eligible"]) == 2
    assert summary["secop_ii_recent"] == 4
    assert summary["secop_ii_open"] == summary["secop_ii_closed"] == 1
    assert summary["secop_ii_unknown"] == 2
    assert summary["provider_status_deadline_conflicts"] == 1
    assert summary["status"] == "completed_with_warnings"
    assert not summary["errors"]
    assert client.post.call_count == 2


def make_plan(tmp_path):
    config = json.loads(DEFAULT_PLAN.read_text(encoding="utf-8"))
    path = tmp_path / "boyaca.txt"
    path.write_text(",".join(str(n) for n in range(123)), encoding="utf-8")
    config["regions"]["boyaca"]["ids_file"] = str(path)
    config["unspsc"]["catalog_file"] = str(SCRIPTS.parent / "config/eureka_radar.v1.json")
    config["searches"] = config["searches"][:2]
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return load_plan(path)


def test_plan_query_and_consolidated_counts_dedup_warnings_and_keep_provenance(tmp_path):
    rows = make_rows()
    client = client_for(rows)
    client.post.side_effect = [
        {"count": 1, "data": [ROW]},
        {"count": 6, "data": rows},
        {"count": 6, "data": rows},
    ]
    assert run_plan(client, make_plan(tmp_path), tmp_path, Mock(), Mock(), now=NOW) == 0
    summary = json.loads((tmp_path / "search_plan_summary.json").read_text(encoding="utf-8"))
    discovery = json.loads((tmp_path / "discovery.json").read_text(encoding="utf-8"))
    for entry in [summary, *summary["queries"]]:
        assert entry["secop_ii_recent"] == 4
        assert entry["secop_ii_open"] == entry["secop_ii_closed"] == 1
        assert entry["secop_ii_unknown"] == 2
        assert entry["provider_status_deadline_conflicts"] == 1
    assert len(summary["warnings"]) == 2  # conflict+invalid, once per consolidated process
    assert all(len(q["warnings"]) == 2 for q in summary["queries"])
    assert len(discovery["eligible"]) == 2
    assert len(discovery["eligible_recent"]) == 5
    assert all(len(p["matched_searches"]) == 2 for p in discovery["processes"])
    assert client.post.call_count == 3  # preflight+two searches; no detail calls
    assert all(
        set(c.args[1]["query"]) <= {"Objeto", "ubicacion_filter"}
        for c in client.post.call_args_list
    )
    assert not (tmp_path / "documents.json").exists()


def test_conflicts_on_stale_or_non_secop_rows_stay_in_evidence_not_recent_counters():
    source = CandidateProcess.from_source(
        {**ROW, "FechaVencimiento": "2026-10-19 10:00:00"}, "1086005"
    ).to_dict()
    a = {**source, "recent": False}
    b = {**source, "recent": True, "id_fuente_contract": "1", "key_config": "other"}
    processes, counts, warnings = apply_validity([a, b], NOW)
    assert all(p["validity_warning"] == "provider_status_deadline_conflict" for p in processes)
    assert counts["secop_ii_recent"] == counts["provider_status_deadline_conflicts"] == 0
    assert not warnings
