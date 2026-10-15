from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli
from public_procurement.eureka.config import DEFAULT_CONFIG
from public_procurement.eureka.domain.discovery import evaluate_process

from ..eureka.test_discovery import facts


def test_cli_dry_run_outputs_score_categories_signals_and_reasons(monkeypatch) -> None:
    engine, service = Mock(), Mock()
    result = evaluate_process(
        facts(title="Refrigerios", entity_name="Institución Educativa"), DEFAULT_CONFIG
    )
    service.evaluate.return_value = iter([result])
    monkeypatch.setattr(cli, "load_settings", Mock())
    monkeypatch.setattr(cli, "create_db_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda configured_engine: Mock())
    monkeypatch.setattr(cli, "build_eureka_service", lambda sessions: service)
    response = CliRunner().invoke(
        cli.app, ["evaluate-eureka", "--process", "CO1.REQ.1", "--dry-run"]
    )
    assert response.exit_code == 0
    assert "score 40" in response.output
    assert "Alimentos empacados" in response.output
    assert "+30: Producto específico" in response.output
    assert "sin persistencia" in response.output
    service.evaluate.assert_called_once_with("CO1.REQ.1", None, dry_run=True)
    engine.dispose.assert_called_once()


def test_cli_rejects_missing_or_ambiguous_scope_before_connecting(monkeypatch) -> None:
    forbidden = Mock(side_effect=AssertionError("No debe conectar"))
    monkeypatch.setattr(cli, "load_settings", forbidden)
    assert CliRunner().invoke(cli.app, ["evaluate-eureka"]).exit_code == 2
    assert (
        CliRunner()
        .invoke(cli.app, ["evaluate-eureka", "--process", "P", "--department", "Boyacá"])
        .exit_code
        == 2
    )
    forbidden.assert_not_called()
