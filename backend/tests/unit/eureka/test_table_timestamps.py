"""Insertion and review-entry times are independent of provider and assessment dates."""

import copy
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.radar_repositories import (
    COUNTERS,
    RadarRunProcessRecord,
    RadarRunRecord,
    SqlRadarRepository,
)

from .test_human_review import NOW, observation, service


def test_run_rows_order_by_first_insertion_and_preserve_unknown_legacy_time():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        RadarRunRecord.__table__.create(connection)
        RadarRunProcessRecord.__table__.create(connection)
    sessions = sessionmaker(engine)
    repo = SqlRadarRepository(sessions)
    at = datetime(2026, 10, 23, 1, 19, 20, tzinfo=UTC)  # Bogota 22/10 20:19:20
    run_id = uuid.uuid4()
    repo.start(
        {
            "id": run_id,
            "source": "licitaciones_info_cdp",
            "started_at": at,
            "status": "running",
            "start_date": at.date(),
            "before_date": (at + timedelta(days=1)).date(),
            "regions": ["Boyaca"],
            "rule_version": "test",
            "config_hash": "test",
            "errors": [],
            **dict.fromkeys(COUNTERS, 0),
        },
        {},
    )
    legacy = {
        "dataset_id": "licitaciones",
        "secop_id": "legacy",
        "outcome": "skipped",
        "published_at": "2099-01-01",
        "deadline_at": "2099-12-31",
    }
    with sessions.begin() as session:
        session.add(
            RadarRunProcessRecord(
                id=uuid.uuid4(),
                run_id=run_id,
                dataset_id="licitaciones",
                secop_id="legacy",
                result=legacy,
            )
        )
    for code, seconds in (("B", 0), ("A", 20)):
        item = {"dataset_id": "licitaciones", "secop_id": code, "outcome": "skipped"}
        repo.outcome(run_id, item, at + timedelta(seconds=seconds), False)
    first = repo.get_run(run_id)["items"]
    assert [r["secop_id"] for r in first] == ["A", "B", "legacy"]
    assert first[0]["recorded_at"] == (at + timedelta(seconds=20)).isoformat()
    updated = {**first[0], "recorded_at": "2099-01-01T00:00:00+00:00"}
    repo.outcome(run_id, updated, at + timedelta(hours=1), False)
    repo.outcome(run_id, legacy, at + timedelta(hours=1), False)
    assert repo.get_run(run_id)["items"][0]["recorded_at"] == first[0]["recorded_at"]
    assert repo.get_run(run_id)["items"][-1].get("recorded_at") is None
    engine.dispose()


def test_review_first_seen_desc_nulls_last_ignores_provider_dates_and_human_review():
    observations = [observation(n) for n in (1, 2, 3)]
    observations[2]["result"]["metadata"].update(
        published_at="2026-10-21T10:00:00", deadline_at="2099-12-31"
    )
    svc, repo, _ = service(observations)
    repo.data["ratings"] = {
        "secop:CO1.NTC.3": {"review_first_seen_at": None},
        "secop:CO1.NTC.1": {
            "review_first_seen_at": NOW,
            "review_first_seen_origin": "observed",
            "reviewed_at": NOW + timedelta(days=1),
        },
        "secop:CO1.NTC.2": {
            "review_first_seen_at": NOW + timedelta(seconds=20),
            "review_first_seen_origin": "observed",
            "reviewed_at": None,
        },
    }
    before = copy.deepcopy(repo.data["ratings"])
    assert [r["codigo_proceso"] for r in svc.list({})["items"]] == ["CM-2", "CM-1", "CM-3"]
    repo.data["ratings"]["secop:CO1.NTC.1"]["reviewed_at"] = NOW + timedelta(days=90)
    repo.data["observations"].append(observation(1))
    assert [r["codigo_proceso"] for r in svc.list({})["items"]] == ["CM-2", "CM-1", "CM-3"]
    assert (
        repo.data["ratings"]["secop:CO1.NTC.1"]["review_first_seen_at"]
        == before["secop:CO1.NTC.1"]["review_first_seen_at"]
    )
    assert svc.list({})["items"][-1]["review_first_seen_at"] is None


def test_reading_old_review_rows_does_not_create_first_entry_timestamp():
    svc, repo, _ = service([observation()])
    row = svc.list({})["items"][0]
    assert row["review_first_seen_at"] is None
    assert row["review_first_seen_origin"] == "legacy_unknown"
    assert repo.data["ratings"]["secop:CO1.NTC.1"]["review_first_seen_at"] is None
