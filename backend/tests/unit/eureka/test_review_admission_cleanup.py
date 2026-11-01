import copy

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.review_api import router
from public_procurement.eureka.review_cleanup import cleanup_plan, execute_cleanup
from public_procurement.eureka.review_policy import admission
from public_procurement.eureka.review_repositories import (
    ManualProcessReviewRecord,
    ReviewRepository,
)
from public_procurement.eureka.review_services import project, record_review_entry

from .test_human_review import NOW, observation, service


@pytest.mark.parametrize(
    "reason", ["no_metadata_match", "strong_exclusion", "missing_or_invalid_offer_deadline"]
)
def test_discard_without_commercial_evidence_is_not_a_review_candidate(reason):
    item = observation(source="socrata", object="Servicio general institucional")["result"]
    item.update(reason=reason)
    assert not admission(item)["review_candidate"]


def test_unknown_deadline_with_commercial_metadata_can_be_reviewed():
    item = observation(source="socrata", deadline_at=None)["result"]
    item["reason"] = "missing_or_invalid_offer_deadline"
    item.update(admission(item))
    assert item["review_candidate"]
    assert "metadata_catalog_match" in item["review_admission_reasons"]
    svc, _, _ = service([observation(source="socrata", deadline_at=None)])
    svc.repository.data["observations"][0]["result"] = item
    assert "Deadline por verificar" in svc.list({})["items"][0]["review_explanations"]


def test_strong_exclusion_requires_additional_independent_evidence():
    item = observation(object="Compra de papelería para apoyo a obra civil")["result"]
    assert not admission(item)["review_candidate"]
    item["decision"] = {"snapshot": {"confirmed_matches": [{"canonical_fact_id": "real_fact"}]}}
    assert admission(item)["review_candidate"]


@pytest.mark.parametrize("source", ["socrata", "licitaciones_info_cdp"])
def test_both_sources_need_commercial_evidence_and_not_only_basic_metadata(source):
    obs = observation(source=source, object="Información básica suficiente", amount="100000")
    data = {"observations": [obs], "ratings": {}, "alerts": [], "opportunities": {}}
    assert not project(data, {}, NOW)[0]["review_evidence_sufficient"]
    obs["result"]["metadata"]["object"] = "Adquisición de papelería"
    obs["result"]["coverage_incomplete"] = True
    row = project(data, {}, NOW)[0]
    assert row["review_evidence_sufficient"]
    assert row["requires_manual_document_review"]


@pytest.fixture
def cleanup_db():
    engine = create_engine("sqlite://")
    with engine.begin() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        ManualProcessReviewRecord.__table__.create(c)
        for name in ("alert", "radar_run", "facts", "canonicals", "documents"):
            c.execute(text(f'CREATE TABLE eureka."{name}" (id INTEGER PRIMARY KEY)'))
            c.execute(text(f'INSERT INTO eureka."{name}" VALUES (1)'))  # noqa: S608 -- fixed test names
    sessions = sessionmaker(engine)
    observations = []
    for n in (1, 2, 3):
        obs = observation(n, source="socrata", object="Servicio genérico institucional")
        obs["result"]["reason"] = "no_metadata_match"
        observations.append(obs)
    observations.append(observation(4))  # commercial CDP preserved
    observations.append(observation(5, source="socrata"))
    observations[-1]["result"].update(manual_review_reasons=["suspicious_facts"])
    with sessions.begin() as s:
        for n in range(1, 6):
            s.add(
                ManualProcessReviewRecord(
                    canonical_identity=f"secop:CO1.NTC.{n}",
                    manual_note="",
                    review_first_seen_at=NOW,
                    review_first_seen_origin="observed",
                )
            )

    def rebuild():
        with sessions() as s:
            ratings = {
                r.canonical_identity: ReviewRepository.rating(r)
                for r in s.scalars(select(ManualProcessReviewRecord))
            }
        data = {"observations": observations, "ratings": ratings, "alerts": [], "opportunities": {}}
        return cleanup_plan(data, project(data, {}, NOW))

    yield sessions, rebuild, engine
    engine.dispose()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("manual_rating", "high"),
        ("manual_note", "Mi nota"),
        ("manual_note", " "),
        ("reviewed_at", NOW),
        ("reviewed_by", "00000000-0000-0000-0000-000000000001"),
    ],
)
def test_human_work_is_protected_and_excluded_membership_is_not_recreated(cleanup_db, field, value):
    import uuid

    sessions, rebuild, _ = cleanup_db
    if field == "reviewed_by":
        value = uuid.UUID(value)
    with sessions.begin() as s:
        setattr(s.get(ManualProcessReviewRecord, "secop:CO1.NTC.1"), field, value)
    plan = rebuild()
    assert plan["protected_count"] == 1
    assert plan["delete_count"] == 2
    execute_cleanup(sessions, plan, rebuild)
    with sessions() as s:
        assert s.get(ManualProcessReviewRecord, "secop:CO1.NTC.1") is not None
        assert s.get(ManualProcessReviewRecord, "secop:CO1.NTC.2") is None


def test_cleanup_is_exact_id_idempotent_and_does_not_touch_history_or_evidence(cleanup_db):
    sessions, rebuild, engine = cleanup_db
    plan = rebuild()
    assert plan["before"] == 5
    assert plan["delete_count"] == 3
    result = execute_cleanup(sessions, plan, rebuild)
    assert result["deleted"] == 3
    assert rebuild()["before"] == 2
    assert rebuild()["delete_count"] == 0
    assert execute_cleanup(sessions, plan, rebuild)["deleted"] == 0
    with engine.connect() as c:
        for name in ("alert", "radar_run", "facts", "canonicals", "documents"):
            count = c.execute(text(f'SELECT count(*) FROM eureka."{name}"')).scalar()  # noqa: S608 -- fixed test names
            assert count == 1


def test_human_edit_after_audit_aborts_cleanup(cleanup_db):
    sessions, rebuild, _ = cleanup_db
    plan = rebuild()
    with sessions.begin() as s:
        s.get(ManualProcessReviewRecord, "secop:CO1.NTC.2").manual_note = "Edición posterior"
    with pytest.raises(ValueError, match="selection changed"):
        execute_cleanup(sessions, plan, rebuild)
    assert rebuild()["before"] == 5


def test_delete_error_rolls_back_every_membership_deletion(cleanup_db):
    sessions, rebuild, engine = cleanup_db
    plan = rebuild()

    def fail_after_delete(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("DELETE"):
            raise RuntimeError("simulated failure after SQL delete")

    event.listen(engine, "after_cursor_execute", fail_after_delete)
    try:
        with pytest.raises(RuntimeError, match="simulated failure"):
            execute_cleanup(sessions, plan, rebuild)
    finally:
        event.remove(engine, "after_cursor_execute", fail_after_delete)
    assert rebuild()["before"] == 5


def test_api_removed_membership_disappears_while_run_history_survives():
    svc, repo, _ = service([observation(source="socrata")])
    history = copy.deepcopy(repo.data["observations"])
    app = FastAPI()
    app.include_router(router)
    app.state.human_review_queries = svc
    with TestClient(app) as client:
        assert client.get("/api/eureka/revision").json()["total"] == 1
        repo.data["ratings"].clear()
        response = client.get("/api/eureka/revision")
        assert response.json()["total"] == 0
        assert response.headers["cache-control"] == "no-store"
    assert repo.data["observations"] == history


def test_record_entry_requires_explicit_review_candidate(cleanup_db):
    sessions, _, _ = cleanup_db
    item = observation(99)["result"]
    with sessions.begin() as session:
        assert record_review_entry(session, item, "socrata", NOW) is None
        item.update(admission(item))
        assert record_review_entry(session, item, "socrata", NOW)["status"] == "new"


def test_human_assessment_is_kept_but_hard_rejection_is_hidden_from_default_tray():
    svc, repo, _ = service([observation(source="socrata", object="Servicio genérico")])
    assert svc.list({})["total"] == 0
    repo.data["ratings"]["secop:CO1.NTC.1"]["manual_note"] = "Revisar personalmente"
    assert svc.list({})["total"] == 0
    row = svc.list({"include_excluded": True})["items"][0]
    assert row["review_protected_by_human"]
    assert row["manual_note"] == "Revisar personalmente"
