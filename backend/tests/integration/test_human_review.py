import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.review_repositories import (
    ManualProcessReviewRecord,
    ReviewRepository,
)

pytestmark = pytest.mark.integration


def test_small_review_migration_and_atomic_assessment_do_not_write_alerts(migrated_engine):
    inspector = inspect(migrated_engine)
    assert "manual_process_review" in inspector.get_table_names(schema="eureka")
    assert inspector.get_pk_constraint("manual_process_review", schema="eureka")[
        "constrained_columns"
    ] == ["canonical_identity"]
    sessions = sessionmaker(migrated_engine)
    repository = ReviewRepository(sessions)
    user, at = uuid.uuid4(), datetime.now(UTC)
    with migrated_engine.connect() as c:
        alerts_before = c.scalar(text("SELECT count(*) FROM eureka.alert"))
        facts_before = c.scalar(text("SELECT count(*) FROM extraction.structured_fact"))
    repository.enter(["secop:CO1.NTC.123"], at - timedelta(hours=1), "observed")
    repository.enter(["secop:CO1.NTC.123"], at, "observed")
    repository.save("secop:CO1.NTC.123", "medium", "Revisar monto", user, at)
    repository.save("secop:CO1.NTC.123", "discard", "Presupuesto alto", user, at)
    with sessions() as session:
        rows = session.scalars(select(ManualProcessReviewRecord)).all()
        assert len(rows) == 1
        assert rows[0].manual_rating == "discard"
        assert rows[0].manual_note == "Presupuesto alto"
        assert rows[0].reviewed_by == user
        assert rows[0].reviewed_at == at
        assert rows[0].review_first_seen_at == at - timedelta(hours=1)
    with migrated_engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM eureka.alert")) == alerts_before
        assert c.scalar(text("SELECT count(*) FROM extraction.structured_fact")) == facts_before


def test_temporal_migration_keeps_legacy_assessment_without_inventing_entry_date(
    database_engine, database_settings
):
    from alembic import command

    from .conftest import migration_config

    config = migration_config(database_settings)
    command.downgrade(config, "base")
    command.upgrade(config, "0019_manual_process_review")
    with database_engine.begin() as c:
        c.execute(
            text("""INSERT INTO eureka.manual_process_review
            (canonical_identity, manual_rating, manual_note, reviewed_at)
            VALUES ('secop:CO1.NTC.123', 'high', 'Preservar', '2026-10-21T20:00:00Z')""")
        )
    command.upgrade(config, "0020_review_temporal_trace")
    with database_engine.connect() as c:
        row = c.execute(text("SELECT * FROM eureka.manual_process_review")).mappings().one()
        assert row["review_first_seen_at"] is None
        assert row["review_first_seen_origin"] == "legacy_unknown"
        assert row["manual_rating"] == "high"
        assert row["manual_note"] == "Preservar"
        assert row["reviewed_at"] == datetime(2026, 10, 21, 20, tzinfo=UTC)
