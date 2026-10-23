"""Offline aggregator admission, capability routing and human review; no network or DB."""

import copy
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from public_procurement.eureka.review_services import project
from public_procurement.licitaciones_cdp.adapters import (
    LicitacionesInfoSource,
    provider_identity,
    provider_metadata,
)
from public_procurement.licitaciones_cdp.events import annotate_run

from .eureka.test_human_review import NOW, observation
from .test_licitaciones_operations import candidate, service


@pytest.mark.parametrize(
    ("kind", "link"),
    [
        ("secop2", "https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.1"),
        (
            "secop1",
            "https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia=26-13-123",
        ),
        ("fao", "https://fao.taleo.net/jobs"),
        ("universidad", "https://universidad.edu.co/convocatorias/1"),
        ("unknown", ""),
    ],
)
def test_all_sources_can_advance_without_new_commercial_rules(monkeypatch, kind, link):
    row = candidate(key_config=kind, id_ultima_fase=None, raw_source_reference={"Link": link})
    svc, repo, pipeline = service(monkeypatch, [row])
    run = svc.run()
    pipeline.enrich.assert_called_once()
    assert run["metrics"]["processed"] == 1
    assert repo.items[row["process_reference"]]["metadata"]["provider_source"] == kind
    assert all(item.get("reason") != "not_secop_ii" for item in run["items"])


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"recent": False}, "stale"),
        ({"validity_status": "closed"}, "validity_closed"),
        ({"department": "Antioquia"}, "outside_local_scope"),
        ({"object": ""}, "incomplete_row"),
    ],
)
def test_unchanged_operational_gates(monkeypatch, changes, reason):
    svc, _, pipeline = service(monkeypatch, [candidate(**changes)])
    run = svc.run()
    pipeline.enrich.assert_not_called()
    assert run["items"][0]["reason"] == reason
    assert not run["items"][0]["review_candidate"]
    assert run["metrics"]["event_groups"]["discard"][0]["code"] == reason


@pytest.mark.parametrize("verified", [False, True])
def test_external_inventory_only_when_strategy_is_verified(monkeypatch, verified):
    source = LicitacionesInfoSource(Mock())
    row = candidate(
        key_config="fao",
        raw_source_reference={"Link": "https://fao.org/1"},
        document_capability={"strategy": "licitaciones_inventory", "verified": verified},
    )
    key = provider_identity(row)
    source.processes = {key: row}
    source.client = Mock()
    monkeypatch.setattr(
        source.modules["freshness"], "apply_freshness", lambda *args: ([row], {}, [])
    )
    monkeypatch.setattr(source.modules["validity"], "apply_validity", lambda *args: ([row], {}, []))
    inventory = Mock(return_value=[])
    monkeypatch.setattr(source.modules["cdp_runtime"], "fetch_inventory", inventory)
    assert source.fetch(key) == []
    assert inventory.call_count == int(verified)
    source.client.post.assert_not_called()


@pytest.mark.parametrize(
    "warning",
    ["suspicious_fact", "ocr_truncated", "missing_documents", "metadata_only", "unknown_source"],
)
def test_useful_warning_enters_review_with_readable_reason_and_exact_identity(warning):
    obs = observation(
        id_ultima_fase=None,
        source_identity="licitaciones_info:1086005:77",
        provider_source="unknown",
    )
    obs["result"].update(warnings=[{"code": warning}], reason=None, outcome="no_alert")
    data = {
        "observations": [obs, copy.deepcopy(obs)],
        "ratings": {},
        "alerts": [],
        "opportunities": {},
    }
    rows = project(data, {}, NOW)
    assert len(rows) == 1
    assert rows[0]["canonical_identity"] == "licitaciones_info:1086005:77"
    assert rows[0]["review_evidence_sufficient"]
    assert rows[0]["review_explanations"]
    assert rows[0]["last_run_id"] == obs["run_id"]


def test_warning_with_garbage_metadata_is_not_reviewable():
    obs = observation(object="", entity_name=None)
    obs["result"]["warnings"] = [{"code": "suspicious_fact"}]
    assert (
        project({"observations": [obs], "ratings": {}, "alerts": [], "opportunities": {}}, {}, NOW)
        == []
    )


def test_cli_discovery_does_not_require_source_accessory_fields():
    import licitaciones_cdp_runtime as runtime

    row = {
        "idContrato": 1,
        "Objeto": "Papeleria",
        "TextoDepartamento": "Boyaca",
        "FechaPublicacion": "2026-10-22 09:00:00",
        "id_fuente_contract": None,
        "key_config": None,
    }
    assert runtime.validate_discovery({"count": 1, "data": [row]}, 30) == [row]
    assert (
        runtime.validate_aggregator_response({"count": 1, "data": [row]}, 30)["preflight_status"]
        == "healthy"
    )


def test_aggregator_probe_keeps_80_percent_threshold_and_rejects_bad_dates():
    import licitaciones_cdp_runtime as runtime

    row = {
        "idContrato": 1,
        "Objeto": "Papeleria",
        "TextoDepartamento": "Boyaca",
        "FechaPublicacion": "bad-date",
    }
    with pytest.raises(runtime.CandidateError, match="80%"):
        runtime.validate_aggregator_response({"count": 1, "data": [row]}, 30)


def test_event_groups_preserve_generation_time_and_run_identity():
    run = {
        "id": "run-1",
        "metrics": {"warnings": [{"code": "outside_local_scope"}, {"code": "ocr_truncated"}]},
        "errors": [{"code": "network_error"}],
        "items": [],
    }
    now = datetime(2026, 10, 22, tzinfo=UTC)
    annotate_run(run, now)
    groups = run["metrics"]["event_groups"]
    assert [e["code"] for e in groups["discard"]] == ["outside_local_scope"]
    assert [e["code"] for e in groups["warning"]] == ["ocr_truncated"]
    assert [e["code"] for e in groups["error"]] == ["network_error"]
    for entries in groups.values():
        assert entries[0]["run_id"] == "run-1"
        assert entries[0]["generated_at"] == now.isoformat()


def test_secop_constancy_exact_identity_and_provider_ids_do_not_invent_equivalence():
    first = provider_metadata(
        candidate(
            key_config="secopI",
            id_ultima_fase=None,
            raw_source_reference={
                "Link": "https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia=26-13-14824613"
            },
        )
    )
    assert first["provider_source"] == "secop1"
    assert first["source_identity"] == "secop1:26-13-14824613"
    assert not first["document_capable"]
    external = provider_metadata(
        candidate(key_config="fao", id_ultima_fase=None, raw_source_reference={})
    )
    assert external["source_identity"] == "licitaciones_info:1086005:1"
