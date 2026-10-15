import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli
from public_procurement.ingestion.services import ProcessSyncResult

runner = CliRunner()


def test_unbounded_sync_is_rejected_before_configuration_or_network(monkeypatch) -> None:
    def forbidden():
        raise AssertionError("No debe cargar configuración")

    monkeypatch.setattr(cli, "load_settings", forbidden)
    result = runner.invoke(cli.app, ["sync-processes"])
    assert result.exit_code == 2
    assert "portafolio" in result.output


def test_dry_run_does_not_create_engine_or_require_database_url(monkeypatch) -> None:
    def forbidden(*args):
        raise AssertionError("No debe conectar a la base")

    monkeypatch.setattr(cli, "load_settings", forbidden)
    monkeypatch.setattr(cli, "create_db_engine", forbidden)
    monkeypatch.setattr(cli.SocrataProcessSource, "fetch_processes", lambda self, query: iter([]))
    result = runner.invoke(cli.app, ["sync-processes", "--portfolio", "CO1.BDOS.1", "--dry-run"])
    assert result.exit_code == 0
    assert "sin persistencia" in result.output


def test_existing_beta_commands_remain_registered() -> None:
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "load-seed" in result.output
    assert "recalculate-signals" in result.output
    assert "sync-processes" in result.output


def test_sync_composes_process_service_without_running_beta_ingestion(monkeypatch) -> None:
    engine = Mock()
    sessions = Mock()
    now = datetime(2026, 10, 12, tzinfo=UTC)
    service = Mock()
    service.run.return_value = ProcessSyncResult(uuid.uuid4(), now, now, 2, 1, 1)
    monkeypatch.setattr(cli, "load_settings", Mock())
    monkeypatch.setattr(cli, "configure_logging", Mock())
    monkeypatch.setattr(cli, "create_db_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda configured_engine: sessions)
    monkeypatch.setattr(cli, "build_process_ingestion_service", lambda factory: service)
    beta = Mock(side_effect=AssertionError("No debe ejecutar la ingesta simulada"))
    monkeypatch.setattr(cli, "build_ingestion_service", beta)
    result = runner.invoke(cli.app, ["sync-processes", "--portfolio", "CO1.BDOS.10985405"])
    assert result.exit_code == 0
    assert "1 procesos únicos" in result.output
    assert service.run.call_args.args[1].portfolio_id == "CO1.BDOS.10985405"
    engine.dispose.assert_called_once()
    beta.assert_not_called()
