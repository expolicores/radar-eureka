from dataclasses import replace
from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli
from public_procurement.extraction.consolidation import consolidate

from ..extraction.test_consolidation import PROCESS, product


def setup_cli(monkeypatch):
    engine, service = Mock(), Mock()
    monkeypatch.setattr(cli, "load_settings", Mock())
    monkeypatch.setattr(cli, "create_db_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda configured: Mock())
    monkeypatch.setattr(cli, "build_consolidation_service", lambda sessions, settings: service)
    return engine, service


def test_consolidate_cli_dry_run_reports_compact_summary(monkeypatch):
    engine, service = setup_cli(monkeypatch)
    service.run.return_value = consolidate(PROCESS, [product("Hit"), product("Hit")])
    result = CliRunner().invoke(cli.app, ["consolidate-facts", "--process", "P", "--dry-run"])
    assert result.exit_code == 0
    assert "2 hechos de entrada" in result.output
    assert "1 canónicos" in result.output
    assert "RUP_REQUIRED" in result.output
    service.run.assert_called_once_with("P", dry_run=True)
    engine.dispose.assert_called_once()


def test_show_cli_optional_original_evidence(monkeypatch):
    engine, service = setup_cli(monkeypatch)
    source = product("Hit")
    service.show.return_value = replace(consolidate(PROCESS, [source]), persisted=True)
    service.evidence.return_value = [source]
    result = CliRunner().invoke(cli.app, ["show-canonical", "--process", "P", "--with-evidence"])
    assert result.exit_code == 0
    assert source.evidence_text in result.output
    assert "content_fragment_id" in result.output
    engine.dispose.assert_called_once()


def test_no_current_snapshot_is_explained_without_reconsolidating(monkeypatch):
    _, service = setup_cli(monkeypatch)
    service.show.return_value = replace(consolidate(PROCESS, [product("Hit")]), facts=())
    result = CliRunner().invoke(cli.app, ["show-canonical", "--process", "P"])
    assert result.exit_code == 0
    assert "No hay consolidación vigente" in result.output
    service.run.assert_not_called()
