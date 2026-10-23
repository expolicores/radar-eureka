import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.domain.radar import AlertDecision
from public_procurement.eureka.radar_repositories import (
    COUNTERS,
    AlertRecord,
    RadarProcessStateRecord,
    RadarRunProcessRecord,
    RadarRunRecord,
    SqlRadarRepository,
)


def test_sql_repository_identity_alert_uniqueness_and_snapshot_history():
    engine = create_engine("sqlite://")
    with engine.connect() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        # SQLite cannot enforce cross-schema FKs; PostgreSQL validation covers those separately.
        for table in (
            RadarRunRecord.__table__,
            RadarProcessStateRecord.__table__,
            RadarRunProcessRecord.__table__,
            AlertRecord.__table__,
        ):
            table.create(connection)
    repository = SqlRadarRepository(sessionmaker(engine, expire_on_commit=False))
    at = datetime.now(UTC)
    run = {
        "id": uuid.uuid4(),
        "started_at": at,
        "finished_at": None,
        "status": "running",
        "start_date": date(2026, 10, 7),
        "before_date": date(2026, 10, 14),
        "regions": ["Boyacá"],
        "rule_version": "v1",
        "config_hash": "hash",
        "errors": [],
        **dict.fromkeys(COUNTERS, 0),
    }
    with repository.lock():
        repository.start(run, {"score_gate": False})
        repository.claim(run["id"], "p6dx-8zbt", "process", at)
        repository.stage("p6dx-8zbt", "process", "extraction", at)
        assert repository.state("p6dx-8zbt", "process")["attempts"] == 1
        decision = AlertDecision(True, True, "high", True, [{"code": "product"}], {"score": 65})
        opportunity = uuid.uuid4()
        assert repository.alert(run["id"], opportunity, "v1", decision, at)
        assert not repository.alert(run["id"], opportunity, "v1", decision, at)
        decision.snapshot["score"] = 1
        assert repository.alerts(1, 25)["items"][0]["snapshot"]["score"] == 65
        repository.outcome(
            run["id"],
            {
                "dataset_id": "p6dx-8zbt",
                "secop_id": "process",
                "stage": "completed",
                "outcome": "alert",
            },
            at,
            True,
        )
        run["status"], run["finished_at"] = "completed", at
        repository.finish(run)
        assert repository.state("p6dx-8zbt", "process")["status"] == "completed"
        assert len(repository.get_run(run["id"])["items"]) == 1
        retry = {**run, "id": uuid.uuid4(), "status": "running", "finished_at": None}
        repository.start(retry, {"score_gate": False})
        repository.claim(retry["id"], "p6dx-8zbt", "process", at)
        repository.outcome(
            retry["id"],
            {
                "dataset_id": "p6dx-8zbt",
                "secop_id": "process",
                "stage": "completed",
                "outcome": "alert",
                "coverage_incomplete": True,
            },
            at,
            True,
        )
        assert repository.state("p6dx-8zbt", "process")["status"] == "failed"
        assert repository.alerts(1, 25)["items"][0]["snapshot"]["score"] == 65
    engine.dispose()


@pytest.mark.parametrize(
    ("message", "retryable"),
    [
        ("No hay inventario documental; el proceso queda reintentable.", True),
        ("Socrata HTTP 503", False),
    ],
)
def test_only_legacy_empty_inventory_recovers_exhausted_attempts_without_backfill(
    message, retryable
):
    engine = create_engine("sqlite://")
    with engine.begin() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        for model in (RadarRunRecord, RadarProcessStateRecord, RadarRunProcessRecord, AlertRecord):
            model.__table__.create(c)
    sessions = sessionmaker(engine, expire_on_commit=False)
    repo = SqlRadarRepository(sessions)
    at = datetime(2026, 10, 16, tzinfo=UTC)
    run_id = uuid.uuid4()
    run = {
        "id": run_id,
        "started_at": at,
        "finished_at": None,
        "status": "running",
        "start_date": date(2026, 10, 13),
        "before_date": date(2026, 10, 17),
        "regions": ["Casanare"],
        "rule_version": "v1",
        "config_hash": "hash",
        "errors": [],
        **dict.fromkeys(COUNTERS, 0),
    }
    repo.start(run, {})
    repo.claim(run_id, "p6dx-8zbt", "P", at)
    repo.outcome(
        run_id,
        {
            "dataset_id": "p6dx-8zbt",
            "secop_id": "P",
            "stage": "documents_sync",
            "outcome": "failed",
            "error": {"type": "ValueError", "message": message},
        },
        at,
        True,
    )
    with sessions.begin() as s:
        state = s.query(RadarProcessStateRecord).one()
        state.attempts = 3
    effective = repo.state("p6dx-8zbt", "P")
    assert effective["status"] == ("pending_documents" if retryable else "failed")
    assert effective["attempts"] == (0 if retryable else 3)
    with sessions() as s:
        assert s.query(RadarProcessStateRecord).one().attempts == 3
        assert s.query(RadarProcessStateRecord).one().status == "failed"
    if retryable:
        repo.claim(run_id, "p6dx-8zbt", "P", at)
        assert repo.state("p6dx-8zbt", "P")["attempts"] == 1
    engine.dispose()


def test_provisional_alert_is_upgraded_in_place_and_preserves_initial_snapshot():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        for model in (RadarRunRecord, RadarProcessStateRecord, RadarRunProcessRecord, AlertRecord):
            model.__table__.create(connection)
    repository = SqlRadarRepository(sessionmaker(engine, expire_on_commit=False))
    at = datetime(2026, 10, 16, tzinfo=UTC)
    opportunity, first_run, next_run = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    run = {
        "id": first_run,
        "started_at": at,
        "finished_at": None,
        "status": "running",
        "start_date": date(2026, 10, 13),
        "before_date": date(2026, 10, 17),
        "regions": ["Casanare"],
        "rule_version": "v1",
        "config_hash": "hash",
        "errors": [],
        **dict.fromkeys(COUNTERS, 0),
    }
    repository.start(run, {})
    repository.claim(first_run, "p6dx-8zbt", "P", at)
    repository.outcome(
        first_run,
        {
            "dataset_id": "p6dx-8zbt",
            "secop_id": "P",
            "outcome": "alert",
            "stage": "documents_pending",
            "document_status": "unavailable",
        },
        at,
        True,
    )
    assert repository.state("p6dx-8zbt", "P")["status"] == "pending_documents"
    assert repository.state("p6dx-8zbt", "P")["attempts"] == 0
    provisional = AlertDecision(
        True,
        False,
        "medium",
        True,
        [{"code": "candidate_match"}],
        {"evidence_level": "metadata_only", "document_status": "unavailable", "score": 65},
    )
    assert repository.alert(first_run, opportunity, "v1", provisional, at)
    before = repository.alerts(1, 25)["items"][0]
    assert not repository.alert(next_run, opportunity, "v1", provisional, at)
    confirmed = AlertDecision(
        True,
        True,
        "high",
        False,
        [{"code": "document_evidence"}],
        {"evidence_level": "document_confirmed", "document_status": "available", "score": 65},
    )
    assert not repository.alert(next_run, opportunity, "v1", confirmed, at)
    after = repository.alerts(1, 25)
    assert after["total"] == 1
    alert = after["items"][0]
    assert alert["id"] == before["id"]
    assert alert["created_at"] == before["created_at"]
    assert alert["run_id"] == first_run
    assert alert["evidence_level"] == "document_confirmed"
    assert alert["snapshot"]["initial_metadata_alert"]["snapshot"] == provisional.snapshot
    assert repository.alert_for_opportunity(opportunity)["id"] == before["id"]
    assert not repository.alert(next_run, opportunity, "v1", provisional, at)
    assert repository.get_alert(before["id"])["evidence_level"] == "document_confirmed"
    engine.dispose()
