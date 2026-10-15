from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli
from public_procurement.operations import services
from public_procurement.shared.config import Settings


def test_cycle_preflight_json_and_no_dispatch(monkeypatch):
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://unused@localhost/unused")
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    service = Mock()
    service.run.return_value = {"kind": "preflight_configuration_dry_run", "secop_queried": False}
    monkeypatch.setattr(services, "build_cycle_service", lambda *args: service)
    result = CliRunner().invoke(cli.app, ["run-eureka-cycle", "--dry-run", "--json"])
    assert result.exit_code == 0
    assert "preflight_configuration_dry_run" in result.stdout
    service.run.assert_called_once_with(dry_run=True, trigger="manual")


def test_cycle_dry_run_failure_is_sanitized_without_files(monkeypatch):
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://unused@localhost/unused")
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    service = Mock()
    service.run.side_effect = ValueError("SECRET")
    monkeypatch.setattr(services, "build_cycle_service", lambda *args: service)
    record = Mock()
    monkeypatch.setattr(services, "record_startup_failure", record)
    result = CliRunner().invoke(cli.app, ["run-eureka-cycle", "--dry-run"])
    assert result.exit_code == 1
    assert "SECRET" not in result.output
    record.assert_not_called()
