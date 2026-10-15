import uuid
from datetime import UTC, date, datetime

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
