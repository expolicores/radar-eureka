import copy
import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.review_api import router
from public_procurement.eureka.review_repositories import (
    ManualProcessReviewRecord,
    ReviewRepository,
)
from public_procurement.eureka.review_services import HumanReviewService, project

NOW = datetime(2026, 10, 21, 20, tzinfo=UTC)  # 15:00 Bogota; MRAM has already closed.


def observation(n=1, source="licitaciones_info_cdp", **changes):
    metadata = {
        "id_ultima_fase": f"CO1.NTC.{n}",
        "codigo_proceso": f"CM-{n}",
        "id_fuente_contract": 3,
        "key_config": "secop2",
        "entity_name": "Concejo",
        "department": "Boyacá",
        "municipality": "Duitama",
        "object": "Papelería y oficina",
        "amount": "8400000",
        "published_at": "2026-10-20T08:46:10",
        "deadline_at": "2026-10-23T09:00:00-05:00",
        **changes,
    }
    return {
        "source": source,
        "run_id": str(uuid.uuid4()),
        "run_at": NOW,
        "regions": ["Boyacá"],
        "result": {
            "secop_id": f"CO1.NTC.{n}",
            "metadata": metadata,
            "stage": "metadata",
            "outcome": "skipped",
            "reason": "limit_deferred",
        },
    }


class Repository:
    def __init__(self, observations):
        self.data = {"observations": observations, "ratings": {}, "alerts": [], "opportunities": {}}

    def read(self, since=None):
        data = copy.deepcopy(self.data)
        if since is not None:
            data["observations"] = [o for o in data["observations"] if o["run_at"] >= since]
        return data

    def save(self, identity, rating, note, user, at):
        self.data["ratings"][identity] = {
            **self.data["ratings"].get(identity, {}),
            "manual_rating": rating,
            "manual_note": note,
            "reviewed_by": user,
            "reviewed_at": at,
        }
        return self.data["ratings"][identity]

    def enter(self, identities, at, origin):
        for identity in identities:
            self.data["ratings"].setdefault(
                identity,
                {
                    "review_first_seen_at": at,
                    "review_first_seen_origin": origin,
                    "manual_rating": None,
                    "manual_note": "",
                    "reviewed_at": None,
                    "reviewed_by": None,
                },
            )
        return self.data["ratings"]


def service(observations):
    repo = Repository(observations)
    # Persisted membership is now required; unknown legacy entry dates remain unknown.
    repo.data["ratings"] = {
        row["canonical_identity"]: {
            "review_first_seen_at": None,
            "review_first_seen_origin": "legacy_unknown",
            "manual_rating": None,
            "manual_note": "",
            "reviewed_at": None,
            "reviewed_by": None,
        }
        for row in project(repo.data, {}, NOW)
    }
    evidence = Mock(return_value={"facts": [], "documents": [], "canonicals": None})
    return HumanReviewService(repo, lambda: {}, evidence, lambda: NOW), repo, evidence


def test_cdp_deferred_and_noneligible_processes_appear_with_human_reason():
    first, second = observation(), observation(2)
    second["result"].update(
        stage="completed",
        outcome="no_alert",
        reason=None,
        decision={"create": False, "snapshot": {"score": 35, "confirmed_matches": []}},
        requires_manual_document_review=True,
        manual_review_reasons=["suspicious_facts"],
    )
    svc, repo, evidence = service([first, second])
    original = copy.deepcopy(repo.data)
    rows = svc.list({})["items"]
    assert len(rows) == 2
    by_code = {r["codigo_proceso"]: r for r in rows}
    assert by_code["CM-1"]["no_alert_reason"] == "Diferido por límite de procesamiento"
    assert (
        by_code["CM-2"]["no_alert_reason"] == "No se confirmaron productos del catálogo comercial"
    )
    assert by_code["CM-2"]["requires_manual_document_review"]
    assert by_code["CM-2"]["score"] == 35
    assert repo.data["observations"] == original["observations"]
    assert all(r["manual_rating"] is None for r in repo.data["ratings"].values())
    evidence.assert_not_called()


def test_socrata_and_cdp_exact_identity_consolidates_sources_runs_and_existing_alert():
    soc = observation(source="socrata")
    soc["result"].pop("metadata")
    soc["result"].update(title="Papeleria", department="Boyacá", published_on="2026-10-20")
    cdp = observation()
    svc, repo, _ = service([soc, cdp])
    repo.data["alerts"] = [
        {"id": "existing", "canonical_identity": "secop:CO1.NTC.1", "snapshot": {}}
    ]
    rows = svc.rows()  # Historical evidence stays available outside the operational inbox.
    assert len(rows) == 1
    assert set(rows[0]["sources"]) == {"socrata", "licitaciones_info_cdp"}
    assert len(rows[0]["history"]) == 2
    assert rows[0]["has_alert"]
    assert rows[0]["alert_ids"] == ["existing"]
    assert svc.list({"source": "socrata"})["total"] == 0
    assert svc.list({"has_alert": False})["total"] == 0


def test_socrata_without_alert_appears_from_persisted_metadata():
    soc = observation(source="socrata")
    soc["result"].pop("metadata")
    soc["result"].update(title="Compra de refrigerios", published_on="2026-10-20")
    _svc, repo, _ = service([soc])
    row = project(
        repo.read(),
        {
            "CO1.NTC.1": {
                "codigo_proceso": "SOC-1",
                "entity_name": "Municipio",
                "department": "Boyacá",
                "deadline_at": "2026-10-23T09:00:00-05:00",
            }
        },
        NOW,
    )[0]
    assert row["codigo_proceso"] == "SOC-1"
    assert row["sources"] == ["socrata"]
    assert not row["has_alert"]


@pytest.mark.parametrize("filters", [{}, {"include_excluded": True}, {"has_alert": True}])
def test_alert_exclusion_is_unconditional_and_preserves_review_notes(filters):
    svc, repo, _ = service([observation()])
    repo.data["ratings"]["secop:CO1.NTC.1"].update(
        manual_rating="high", manual_note="Conservar mi evaluación", reviewed_at=NOW
    )
    repo.data["alerts"] = [
        {
            "id": "existing",
            "canonical_identity": None,
            "snapshot": {"canonical_identity": "secop:CO1.NTC.1"},
        }
    ]
    before = copy.deepcopy(repo.data)
    assert svc.list(filters)["items"] == []
    assert svc.get("secop:CO1.NTC.1")["manual_note"] == "Conservar mi evaluación"
    assert repo.data == before


def test_alerts_are_removed_before_pagination_and_do_not_merge_ntc_req():
    same_number_req = observation(1, source_identity="CO1.REQ.1", codigo_proceso="REQ-1")
    svc, repo, _ = service([observation(), observation(2), same_number_req])
    repo.data["alerts"] = [
        {"id": "existing", "canonical_identity": "secop:CO1.NTC.1", "snapshot": {}}
    ]
    result = svc.list({"page_size": 1})
    assert result["total"] == 2
    assert len(result["items"]) == 1
    identities = {r["canonical_identity"] for r in svc.list({})["items"]}
    assert identities == {"secop:CO1.NTC.2", "secop:CO1.REQ.1"}


def test_existing_review_leaves_inbox_when_alert_is_persisted_without_deleting_history():
    svc, repo, _ = service([observation()])
    assert svc.list({})["total"] == 1
    before = copy.deepcopy(repo.data["ratings"])
    repo.data["alerts"] = [{"id": "new", "canonical_identity": "secop:CO1.NTC.1", "snapshot": {}}]
    assert svc.list({})["total"] == 0
    assert repo.data["ratings"] == before


def test_same_number_ntc_req_are_not_equated():
    a, b = observation(), observation(source="socrata", id_ultima_fase="CO1.REQ.1")
    svc, _, _ = service([a, b])
    assert svc.list({})["total"] == 2


def test_current_deadline_overrides_old_open_flag_and_closed_is_hidden_by_default():
    svc, _, _ = service(
        [
            observation(
                codigo_proceso="MRAM-MC-066-2026",
                deadline_at="2026-10-21T14:00:00-05:00",
                validity_status="open",
            )
        ]
    )
    assert svc.list({})["total"] == 0
    row = svc.list({"validity": "closed"})["items"][0]
    assert row["validity_status"] == "closed"
    assert row["no_alert_reason"] == "Deadline vencido"


def test_stale_outside_scope_and_invalid_are_excluded_but_source_is_not_a_gate():
    stale = observation(published_at="2026-09-01")
    outside = observation(2)
    outside["result"]["reason"] = "outside_region"
    external = observation(3, id_fuente_contract=None, key_config=None)
    invalid = observation(4, id_ultima_fase=None)
    invalid["result"]["secop_id"] = "local-only"
    svc, _, _ = service([stale, outside, external, invalid])
    assert svc.list({})["total"] == 1
    assert svc.list({"include_excluded": True})["total"] == 3


@pytest.mark.parametrize(
    "filters",
    [
        {"q": "papeleria"},
        {"q": "concejo"},
        {"q": "CM-1"},
        {"department": "boyaca"},
        {"municipality": "duitama"},
        {"amount_min": 8000000, "amount_max": 9000000},
        {"deadline_from": date(2026, 10, 22), "deadline_to": date(2026, 10, 24)},
        {"funnel_state": "limit_deferred"},
        {"has_alert": False},
        {"requires_manual_document_review": False},
    ],
)
def test_basic_filters(filters):
    svc, _, _ = service([observation()])
    assert svc.list(filters)["total"] == 1
    assert svc.list({**filters, "q": "does-not-exist"})["total"] == 0


def test_score_filter_pagination_and_first_entry_order():
    a, b, c = (
        observation(),
        observation(2, deadline_at="2026-10-22T09:00:00-05:00"),
        observation(3, deadline_at=None),
    )
    b["result"]["decision"] = {"create": False, "snapshot": {"score": 35}}
    svc, repo, _ = service([a, b, c])
    repo.data["ratings"]["secop:CO1.NTC.2"] = {
        "review_first_seen_at": NOW,
        "review_first_seen_origin": "observed",
    }
    assert svc.list({"page_size": 1})["items"][0]["codigo_proceso"] == "CM-2"
    assert svc.list({"score_min": 30, "score_max": 40})["total"] == 1
    assert svc.list({"score_min": 40})["total"] == 0


def test_human_rating_and_note_survive_new_runs_without_altering_score_or_decision():
    obs = observation()
    obs["result"]["decision"] = {"create": False, "snapshot": {"score": 35}}
    svc, repo, _ = service([obs])
    decision = copy.deepcopy(obs["result"]["decision"])
    user = uuid.uuid4()
    svc.save("secop:CO1.NTC.1", "medium", "Viable; revisar documentos", user)
    repo.data["observations"].append(observation())
    row = svc.list({})["items"][0]
    assert row["manual_rating"] == "medium"
    assert row["manual_note"] == "Viable; revisar documentos"
    assert row["reviewed_by"] == user
    assert row["reviewed_at"] == NOW
    assert row["score"] == 35
    assert row["decision"] == decision
    assert len(row["history"]) == 2


def test_weekly_list_excludes_old_observations_before_pagination_but_keeps_detail():
    old, edge, recent = observation(1), observation(2), observation(3)
    old["run_at"] = NOW - timedelta(days=7, seconds=1)
    edge["run_at"] = NOW - timedelta(days=7)
    svc, repo, _ = service([old, edge, recent])
    before = copy.deepcopy(repo.data)
    listing = svc.list({"include_excluded": True, "page_size": 1})
    assert listing["total"] == 2
    assert listing["observed_since"] == edge["run_at"].isoformat()
    assert {r["codigo_proceso"] for r in svc.list({})["items"]} == {"CM-2", "CM-3"}
    assert svc.get("secop:CO1.NTC.1")["codigo_proceso"] == "CM-1"
    assert repo.data == before


def test_weekly_list_uses_scoped_metadata_instead_of_full_process_scan():
    svc, _, _ = service([observation()])
    svc.metadata = Mock(side_effect=AssertionError("Full metadata scan must not run"))
    svc.scoped_metadata = Mock(return_value={})
    assert svc.list({})["total"] == 1
    svc.scoped_metadata.assert_called_once()
    svc.metadata.assert_not_called()


def test_process_url_comes_from_persisted_source_reference():
    url = "https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.1"
    svc, _, _ = service([observation(raw_source_reference={"Link": url})])
    assert svc.list({})["items"][0]["source_url"] == url


def test_run_review_filters_before_pagination_and_prioritizes_new_without_alerts():
    new, existing, other, alerted = [observation(n) for n in range(1, 5)]
    run_id = new["run_id"]
    for obs in (existing, alerted):
        obs["run_id"] = run_id
    new["result"]["review_entry"] = {"status": "new"}
    existing["result"]["review_entry"] = {"status": "existing"}
    svc, repo, _ = service([existing, other, alerted, new])
    repo.data["ratings"]["secop:CO1.NTC.1"]["review_first_seen_at"] = NOW - timedelta(hours=1)
    repo.data["ratings"]["secop:CO1.NTC.2"]["review_first_seen_at"] = NOW
    repo.data["alerts"] = [{"id": "a", "canonical_identity": "secop:CO1.NTC.4", "snapshot": {}}]
    result = svc.list({"run_id": run_id, "page_size": 1})
    assert result["total"] == 2
    assert result["items"][0]["codigo_proceso"] == "CM-1"
    assert (
        svc.list({"run_id": run_id, "page_size": 1, "page": 2})["items"][0]["codigo_proceso"]
        == "CM-2"
    )


def test_assessment_is_persisted_with_unique_canonical_key():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        ManualProcessReviewRecord.__table__.create(connection)
    sessions = sessionmaker(engine)
    repository = ReviewRepository(sessions)
    user = uuid.uuid4()
    repository.enter(["secop:CO1.NTC.1"], NOW, "observed")
    repository.save("secop:CO1.NTC.1", "high", "Primera nota", user, NOW)
    repository.save("secop:CO1.NTC.1", "discard", "Presupuesto alto", user, NOW + timedelta(days=1))
    with sessions() as session:
        rows = session.scalars(select(ManualProcessReviewRecord)).all()
        assert len(rows) == 1
        assert rows[0].manual_rating == "discard"
        assert rows[0].manual_note == "Presupuesto alto"
        assert rows[0].reviewed_by == user
        assert rows[0].review_first_seen_at.replace(tzinfo=UTC) == NOW


def test_first_entry_survives_second_run_other_source_and_later_human_review():
    svc, repo, _ = service([observation()])
    repo.data["ratings"].clear()
    repo.enter(["secop:CO1.NTC.1"], NOW, "observed")
    first = svc.list({})["items"][0]
    assert first["review_first_seen_at"] == NOW
    assert first["review_first_seen_origin"] == "observed"
    assert first["reviewed_at"] is None
    svc.clock = lambda: NOW + timedelta(hours=1)
    repo.data["observations"].append(observation())
    assert svc.list({})["items"][0]["review_first_seen_at"] == NOW
    repo.data["observations"].append(observation(source="socrata"))
    svc.save("secop:CO1.NTC.1", "high", "Humano", uuid.uuid4())
    rows = svc.list({})["items"]
    assert len(rows) == 1
    assert len(rows[0]["sources"]) == 2
    assert rows[0]["review_first_seen_at"] == NOW
    assert rows[0]["reviewed_at"] == NOW + timedelta(hours=1)


def test_persisted_entry_is_insert_only_across_sources_and_assessments():
    from public_procurement.eureka.review_services import record_review_entry

    engine = create_engine("sqlite://")
    with engine.begin() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        ManualProcessReviewRecord.__table__.create(c)
    sessions = sessionmaker(engine)
    for source, offset in (("socrata", 0), ("licitaciones_info_cdp", 1), ("socrata", 2)):
        with sessions.begin() as session:
            record_review_entry(
                session,
                {**observation()["result"], "review_candidate": True},
                source,
                NOW + timedelta(hours=offset),
            )
    repository = ReviewRepository(sessions)
    repository.save("secop:CO1.NTC.1", "high", "Nota", uuid.uuid4(), NOW + timedelta(hours=3))
    with sessions() as session:
        rows = session.scalars(select(ManualProcessReviewRecord)).all()
        assert len(rows) == 1
        assert rows[0].review_first_seen_at.replace(tzinfo=UTC) == NOW
        assert rows[0].review_first_seen_origin == "observed"
        assert rows[0].reviewed_at.replace(tzinfo=UTC) == NOW + timedelta(hours=3)


def test_legacy_assessment_does_not_invent_entry_time():
    svc, repo, _ = service([observation()])
    repo.data["ratings"]["secop:CO1.NTC.1"] = {
        "review_first_seen_at": None,
        "review_first_seen_origin": "legacy_unknown",
        "manual_rating": "high",
        "reviewed_at": NOW - timedelta(hours=1),
    }
    assert svc.list({})["items"][0]["review_first_seen_at"] is None


def test_api_read_and_assessment_validation_and_server_user():
    svc, _, evidence = service([observation()])
    user = uuid.uuid4()
    app = FastAPI()
    app.include_router(router)
    app.state.human_review_queries = svc
    app.state.current_user_provider = lambda request: user
    with TestClient(app) as client:
        assert client.get("/api/eureka/revision").json()["total"] == 1
        assert client.get("/api/eureka/revision/secop:CO1.NTC.1").status_code == 200
        saved = client.put(
            "/api/eureka/revision/secop:CO1.NTC.1",
            json={"manual_rating": "high", "manual_note": "Nota"},
        )
        assert saved.status_code == 200
        assert saved.json()["reviewed_by"] == str(user)
        assert (
            client.put(
                "/api/eureka/revision/secop:CO1.NTC.1", json={"manual_rating": "invalid"}
            ).status_code
            == 422
        )
        assert (
            client.put("/api/eureka/revision/unknown", json={"manual_note": "x"}).status_code == 404
        )
        assert client.get("/api/eureka/revision?page=0").status_code == 422
        assert client.get("/api/eureka/revision?deadline_from=bad").status_code == 422
    evidence.assert_called_once()
