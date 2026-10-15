import json
from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli

from ..eureka.test_details import covarachia_entries, setup_details


def setup_cli(monkeypatch):
    engine = Mock()
    service, _, _ = setup_details(
        covarachia_entries(), missing=("RUP_REQUIRED", "EXPERIENCE_REQUIRED", "DELIVERY_COUNT")
    )
    monkeypatch.setattr(cli, "load_settings", Mock())
    monkeypatch.setattr(cli, "create_db_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda configured: Mock())
    monkeypatch.setattr(cli, "build_eureka_details_service", lambda sessions, settings: service)
    return engine, service


def test_details_cli_legible_output_score_and_missing_requirements(monkeypatch):
    engine, _ = setup_cli(monkeypatch)
    result = CliRunner().invoke(cli.app, ["show-eureka-details", "--process", "CO1.REQ.11172521"])
    assert result.exit_code == 0
    assert "Score: 65" in result.output
    assert "Prioridad: alta" in result.output
    assert "Enrichment: consolidated" in result.output
    assert "chocorramo" in result.output
    assert "5200" in result.output
    assert "rup_required: unknown" in result.output
    assert "Evidence: available" in result.output
    engine.dispose.assert_called_once()


def test_details_cli_json_has_ids_and_unknown_separate_from_not_required(monkeypatch):
    _, _service = setup_cli(monkeypatch)
    result = CliRunner().invoke(cli.app, ["show-eureka-details", "--process", "P", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["score"] == 65
    assert payload["commercial_profile"]["guarantee_required"] == "not_required"
    assert payload["commercial_profile"]["rup_required"] == "unknown"
    assert payload["requirements"]["rup_required"] is None
    assert payload["evidence"]["commercial.products"][0]["canonical_fact_id"]
    assert "evidence_text" not in result.output


def test_details_cli_expands_evidence_only_when_requested(monkeypatch):
    _, service = setup_cli(monkeypatch)
    service.canonical.evidence.return_value = [
        {"evidence_text": "Texto original", "source_locator": {"page_number": 3}}
    ]
    result = CliRunner().invoke(
        cli.app, ["show-eureka-details", "--process", "P", "--json", "--with-evidence"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["evidence_details"]
    assert "Texto original" in result.output
