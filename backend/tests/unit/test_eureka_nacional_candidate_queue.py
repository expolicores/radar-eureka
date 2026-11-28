"""Offline tests for the candidate queue and the commercial recomputation of a stored run.

The stored run is produced by a simulated discovery-only run with the v2 profile; the queue
recomputes it with the current (v3) profile without any network request."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import eureka_nacional_candidate_queue as queue_tool  # noqa: E402
import eureka_nacional_commercial as commercial  # noqa: E402
import eureka_nacional_en01 as en01  # noqa: E402
import eureka_nacional_window_reevaluation as window  # noqa: E402
from licitaciones_freshness import BOGOTA  # noqa: E402

CUTOFF = datetime(2026, 11, 19, 12, tzinfo=BOGOTA)
V2 = commercial.load_commercial_profile(
    Path(__file__).resolve().parents[2] / "config" / "eureka_nacional_commercial.v2.json"
)


def notice(identifier, obj, deadline, department="Boyacá"):
    return {
        "idContrato": identifier,
        "id_fuente_contract": 3,
        "idUltimaFase": f"CO1.NTC.{identifier}",
        "CodigoProceso": f"SIMULADO-{identifier}",
        "TextoDepartamento": department,
        "Objeto": obj,
        "FechaPublicacion": "2026-11-18 13:00:00",
        "FechaVencimiento": deadline,
        "Link": f"https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.{identifier}",
    }


NOTICES = [
    notice(1, "Adquisición de computadores portátiles para la institución", "2026-11-21 09:00:00"),
    notice(2, "Suministro de papelería y útiles de oficina", "2026-11-20 10:00:00", "Huila"),
    notice(3, "Adquisición de una motobomba portátil para emergencias", "2026-11-20 08:00:00"),
    notice(4, "Servicio de aseo y cafetería", "2026-11-22 08:00:00", "Nariño"),
    notice(
        5,
        "Prestación de servicios logísticos para la organización de la semana de la juventud",
        "2026-11-20 12:00:00",
        "Cauca",
    ),
]


@pytest.fixture
def stored_run(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "check_session", Mock())
    client = SimpleNamespace(
        post=lambda _path, _payload: {"count": len(NOTICES), "data": NOTICES},
        profile_id="1234567",
        deadline=time.monotonic() + 360,
        requests=1,
    )
    args = SimpleNamespace(
        discovery_pages=1,
        documents=1,
        processes=1,
        recent_days=2,
        discovery_only=True,
        include_secop1=False,
        secop1_processes=0,
    )
    run = tmp_path / "en01-sim"
    run.mkdir()
    assert en01.run(client, args, None, run, now=CUTOFF, profile=V2) == 0
    return run


def stored(run):
    data = json.loads((run / "processes.json").read_text(encoding="utf-8"))
    return {p["source_identity"]: p for p in data["processes"]}


def test_replay_keeps_the_stored_assessment_and_recompute_uses_the_current_profile(stored_run):
    # Act
    replayed = window.reevaluate(stored_run, 2)
    recomputed = window.reevaluate(stored_run, 2, replay_commercial=False)

    # Assert
    original = {i for i, p in stored(stored_run).items() if not p["excluded_reason"]}
    assert {r["source_identity"] for r in replayed["rows"] if not r["excluded_reason"]} == original
    assert replayed["summary"]["commercial_profile"] is None
    assert recomputed["summary"]["commercial_profile"] == "eureka-nacional-commercial-v3"
    assert recomputed["summary"]["descriptions_stored"] is False
    assert recomputed["summary"]["network_requests"] == 0
    rows = {r["source_identity"]: r for r in recomputed["rows"]}
    assert rows["CO1.NTC.3"]["excluded_reason"] is not None
    assert rows["CO1.NTC.1"]["primary_category"] == "informatica"


def test_queue_reconciles_every_original_candidate_and_orders_by_closing(stored_run):
    # Act
    result = queue_tool.build_queue(stored_run, 2)

    # Assert
    assert result["network_requests"] == 0
    assert sum(result["reconciliation"].values()) == result["original_eligible"]
    excluded = {e["source_identity"]: e for e in result["excluded_now"]}
    assert "CO1.NTC.3" in excluded
    assert excluded["CO1.NTC.3"]["reason"]
    identities = [entry["source_identity"] for entry in result["queue"]]
    assert "CO1.NTC.4" not in identities  # a pure service never enters the queue
    deadlines = [entry["deadline_at"] for entry in result["queue"]]
    assert deadlines == sorted(deadlines)
    assert all(e["experience"] == "undetermined_until_documents_are_read" for e in result["queue"])
    assert all(e["inventory"] == "none" for e in result["queue"])


def test_queue_keeps_mixed_candidates_visible_and_marked(stored_run):
    result = queue_tool.build_queue(stored_run, 2)

    entries = {entry["source_identity"]: entry for entry in result["queue"]}

    assert entries["CO1.NTC.5"]["commercial_confidence"] == "mixed_review"
    assert entries["CO1.NTC.1"]["commercial_confidence"] == "goods"


def test_queue_attaches_known_inventory_from_earlier_runs(stored_run):
    # Arrange: an earlier run inventoried notice 2.
    earlier = stored_run.parent / "en01-earlier"
    earlier.mkdir()
    process = stored(stored_run)["CO1.NTC.2"]
    (earlier / "processes.json").write_text(json.dumps({"processes": [process]}), "utf-8")
    (earlier / "documents.json").write_text(
        json.dumps([{"process_reference": process["process_reference"], "documents": [{}]}]),
        "utf-8",
    )

    # Act
    result = queue_tool.build_queue(stored_run, 2)

    # Assert
    entries = {entry["source_identity"]: entry for entry in result["queue"]}
    assert entries["CO1.NTC.2"]["inventory"] == "complete"
