import json
from datetime import date
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli
from public_procurement.shared.config import Settings


def configure(monkeypatch):
    engine, service, source = Mock(), Mock(), Mock()
    settings = Settings(
        database_url="postgresql://unused",
        eureka_radar_start_date=date(2026, 10, 13),
        _env_file=None,
    )
    service.config.page_size = 200
    service.config.max_pages = 100
    service.run.return_value = {
        "id": "run",
        "status": "completed",
        "processes_seen": 0,
        "candidates": 0,
        "enriched": 0,
        "alerts_created": 0,
        "failures": 0,
        "items": [],
    }
    source.fetch_processes.return_value = []
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "create_db_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda engine: Mock())
    monkeypatch.setattr(cli, "build_radar_service", lambda sessions, settings: service)
    monkeypatch.setattr(cli, "SocrataProcessSource", lambda: source)
    return service, source


def test_cli_uses_configured_start_regions_and_dry_run(monkeypatch):
    service, source = configure(monkeypatch)
    result = CliRunner().invoke(
        cli.app, ["run-eureka-radar", "--before-date", "2026-10-14", "--dry-run", "--json"]
    )
    assert result.exit_code == 0
    assert json.loads(result.output)["alerts_created"] == 0
    query = source.fetch_processes.call_args.args[0]
    assert query.published_from == date(2026, 10, 13)
    assert query.departments == ("Boyacá", "Casanare")
    assert service.run.call_args.kwargs["dry_run"] is True


def test_cli_overrides_and_invalid_window(monkeypatch):
    service, source = configure(monkeypatch)
    result = CliRunner().invoke(
        cli.app,
        [
            "run-eureka-radar",
            "--from-date",
            "2026-10-07",
            "--before-date",
            "2026-10-14",
            "--department",
            "Casanare",
            "--max-processes",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert source.fetch_processes.call_args.args[0].departments == ("Casanare",)
    assert service.run.call_args.kwargs["max_processes"] == 2
    assert CliRunner().invoke(cli.app, ["run-eureka-radar", "--from-date", "bad"]).exit_code == 2


def test_cli_partial_failure_nonzero_exit(monkeypatch):
    service, _ = configure(monkeypatch)
    service.run.return_value["failures"] = 1
    service.run.return_value["status"] = "partial"
    assert (
        CliRunner().invoke(cli.app, ["run-eureka-radar", "--before-date", "2026-10-14"]).exit_code
        == 1
    )


@pytest.mark.parametrize("option", ["--from-date", "--before-date"])
@pytest.mark.parametrize("value", ["2026-10-14T12:00:00", "2026-10-14T00:00:00"])
def test_cli_rejects_hours_before_consulting_source(monkeypatch, option, value):
    service, source = configure(monkeypatch)
    result = CliRunner().invoke(cli.app, ["run-eureka-radar", option, value])
    assert result.exit_code == 2
    source.fetch_processes.assert_not_called()
    service.run.assert_not_called()


def test_cli_accepts_exact_requested_calendar_window(monkeypatch):
    service, source = configure(monkeypatch)
    result = CliRunner().invoke(
        cli.app,
        [
            "run-eureka-radar",
            "--from-date",
            "2026-10-13",
            "--before-date",
            "2026-10-15",
            "--max-processes",
            "2500",
        ],
    )
    assert result.exit_code == 0
    query = source.fetch_processes.call_args.args[0]
    assert query.published_from == date(2026, 10, 13)
    assert query.published_before == date(2026, 10, 15)
    assert service.run.call_args.kwargs["start"] == date(2026, 10, 13)
    assert service.run.call_args.kwargs["before"] == date(2026, 10, 15)
