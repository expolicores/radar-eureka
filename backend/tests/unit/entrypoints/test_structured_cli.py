from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli

from ..extraction.test_structured_rules import facts


def setup_cli(monkeypatch):
    engine, service = Mock(), Mock()
    monkeypatch.setattr(cli, "load_settings", Mock())
    monkeypatch.setattr(cli, "create_db_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda configured: Mock())
    monkeypatch.setattr(cli, "build_structured_service", lambda sessions, settings: service)
    return engine, service


def test_extract_structured_cli_dry_run_and_evidence(monkeypatch):
    engine, service = setup_cli(monkeypatch)
    service.extract.return_value = (facts("Jugo Acme X 200 ml"), 0)
    result = CliRunner().invoke(cli.app, ["extract-structured", "--process", "P", "--dry-run"])
    assert result.exit_code == 0
    assert "PRODUCT" in result.output
    assert "Evidencia: Jugo Acme X 200 ml" in result.output
    assert "confianza" in result.output
    service.extract.assert_called_once_with("P", dry_run=True)
    engine.dispose.assert_called_once()


def test_show_structured_cli_history(monkeypatch):
    engine, service = setup_cli(monkeypatch)
    service.list_facts.return_value = facts("No se requiere póliza")
    result = CliRunner().invoke(cli.app, ["show-structured", "--process", "P", "--history"])
    assert result.exit_code == 0
    assert "not_required" in result.output
    service.list_facts.assert_called_once_with("P", include_history=True)
    engine.dispose.assert_called_once()


def test_missing_fragments_cli_fails_clearly(monkeypatch):
    engine, service = setup_cli(monkeypatch)
    service.extract.side_effect = ValueError("No hay fragmentos persistidos")
    result = CliRunner().invoke(cli.app, ["extract-structured", "--process", "P"])
    assert result.exit_code == 1
    assert "No hay fragmentos persistidos" in result.output
    engine.dispose.assert_called_once()
