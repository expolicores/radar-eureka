import io
from datetime import date
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from public_procurement.ingestion.adapters.socrata_processes import map_process
from public_procurement.ingestion.domain.process import parse_offer_deadline


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "-",
        " \t\n",
        "invalid",
        "2026-02-30",
        "2026-10-13garbage",
        "2026-10-13T25:00:00",
        0,
        True,
        {},
        ["2026-10-13"],
    ],
)
def test_invalid_deadline_is_rejected_without_aborting_adapter(raw):
    assert parse_offer_deadline(raw) is None
    record = map_process({"id_del_proceso": "P", "fecha_de_recepcion_de": raw})
    assert record.offer_deadline_raw == raw
    assert record.offer_deadline is None


@pytest.mark.parametrize(
    "raw",
    [
        "2026-10-13",
        "2026-10-13T00:00:00.000",
        "2026-10-13T12:34:56Z",
        "2026-10-13T12:34:56-05:00",
        " 2026-10-13T00:00:00.000 ",
        "2026-10-13 12:34:56",
    ],
)
def test_iso_deadline_is_parseable_without_comparing_with_today(raw):
    record = map_process({"id_del_proceso": "P", "fecha_de_recepcion_de": raw})
    assert record.offer_deadline_raw == raw
    assert record.offer_deadline == date(2026, 10, 13)


def test_missing_field_is_preserved_as_unknown():
    assert map_process({"id_del_proceso": "P"}).offer_deadline_raw is None


def test_deadline_migration_is_nullable_additive_without_backfill_and_reversible_offline():
    output = io.StringIO()
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"), output_buffer=output)
    config.attributes["database_url"] = "postgresql+psycopg://offline@localhost:55432/offline_test"
    command.upgrade(config, "0016_eureka_operations:0017_offer_deadline", sql=True)
    sql = output.getvalue()
    assert "ALTER TABLE ingestion.secop_process ADD COLUMN offer_deadline_raw JSONB" in sql
    assert "NOT NULL" not in sql
    assert "CREATE TABLE" not in sql
    assert "UPDATE ingestion" not in sql
    assert "DELETE FROM" not in sql
    output.seek(0)
    output.truncate()
    command.downgrade(config, "0017_offer_deadline:0016_eureka_operations", sql=True)
    assert "ALTER TABLE ingestion.secop_process DROP COLUMN offer_deadline_raw" in output.getvalue()
