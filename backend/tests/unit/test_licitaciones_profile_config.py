"""Offline commercial profile resolution; never logs in or requests the provider."""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from public_procurement.licitaciones_cdp import configuration
from public_procurement.licitaciones_cdp.adapters import LicitacionesInfoSource
from public_procurement.shared.config import Settings

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import eureka_licitaciones_cdp as flow
import licitaciones_cdp_runtime as runtime
import licitaciones_search_plan as plans
from licitaciones_sources import process_identity

from .test_licitaciones_candidate import mock_cli


def test_profile_from_existing_settings_and_environment(monkeypatch):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", "730001")
    settings = Settings(database_url="disabled://no-db", _env_file=None)
    assert settings.licitaciones_profile_id == "730001"
    assert configuration.resolve_profile_id(settings=settings) == "730001"


def test_profile_from_local_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv("LICITACIONES_PROFILE_ID", raising=False)
    (tmp_path / ".env").write_text("LICITACIONES_PROFILE_ID=730002\n", encoding="utf8")
    monkeypatch.setattr(configuration, "BACKEND", tmp_path)
    assert configuration.resolve_profile_id() == "730002"


@pytest.mark.parametrize("value", [None, "", " "])
def test_missing_profile_has_no_historical_fallback(value, monkeypatch):
    monkeypatch.delenv("LICITACIONES_PROFILE_ID", raising=False)
    settings = Settings(database_url="disabled://no-db", _env_file=None)
    settings = settings.model_copy(update={"licitaciones_profile_id": value})
    with pytest.raises(
        configuration.ProfileConfigurationError, match="Falta LICITACIONES_PROFILE_ID"
    ):
        configuration.resolve_profile_id(settings=settings)


@pytest.mark.parametrize("value", ["0", "-1", "abc", "1&perfiles=2", chr(0xFF11)])
def test_invalid_profile_is_rejected_without_echoing_value(value):
    with pytest.raises(configuration.ProfileConfigurationError, match="numerico positivo") as exc:
        configuration.resolve_profile_id(value)
    assert value not in str(exc.value)


def test_explicit_override_does_not_load_settings(monkeypatch):
    monkeypatch.setattr(configuration, "Settings", Mock(side_effect=AssertionError("not needed")))
    assert configuration.resolve_profile_id(" 730003 ") == "730003"


def test_cli_profile_override_and_safe_smoke_output(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", "730001")
    mock_cli(monkeypatch, tmp_path)
    client = Mock()
    monkeypatch.setattr(flow, "PageClient", client)
    health = Mock(
        return_value={
            "profile_available": True,
            "get_config_user_status": 200,
            "get_info_status": 200,
        }
    )
    monkeypatch.setattr(flow, "check_session", health)
    assert flow.main(["--check-session", "--profile-id", "730003"]) == 0
    assert client.call_args.args[1] == "730003"
    assert health.call_args.args[1] == "730003"
    result = json.loads(capsys.readouterr().out.strip())
    assert result["configured_profile_id"] == "730003"
    assert result["cdp_reachable"]
    assert result["session_authenticated"]
    assert result["profile_available"]
    assert result["status"] == "healthy"
    assert not list(tmp_path.iterdir())


def test_cli_uses_configured_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", "730004")
    mock_cli(monkeypatch, tmp_path)
    client = Mock()
    monkeypatch.setattr(flow, "PageClient", client)
    monkeypatch.setattr(flow, "check_session", Mock(return_value={"profile_available": True}))
    assert flow.main(["--check-session"]) == 0
    assert client.call_args.args[1] == "730004"


def test_missing_cli_configuration_stops_before_cdp(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("LICITACIONES_PROFILE_ID", raising=False)
    monkeypatch.setattr(configuration, "BACKEND", tmp_path)
    connection = Mock(side_effect=AssertionError("CDP must not be reached"))
    monkeypatch.setattr(flow, "connect_browser", connection)
    assert flow.main(["--check-session"]) == 2
    connection.assert_not_called()
    assert "Falta LICITACIONES_PROFILE_ID" in capsys.readouterr().out


@pytest.mark.parametrize("status", [200, 403, 404])
def test_configured_profile_available_or_unavailable(status):
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.return_value = {"status": status, "json": True, "sameEndpoint": True, "data": {}}
    client = runtime.PageClient(page, "730005", Mock())
    endpoint = "/cliente/contratos/get-info/MP?perfiles=730005"
    if status == 200:
        assert client.post(endpoint, {"query": {}}) == {}
    else:
        with pytest.raises(runtime.CandidateError) as exc:
            client.post(endpoint, {"query": {}})
        assert exc.value.code == "profile_unavailable"
    assert page.evaluate.call_args.args[1]["path"] == endpoint


def test_search_plan_uses_runtime_profile_and_rejects_second_source(monkeypatch, tmp_path):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", "730006")
    raw = json.loads(plans.DEFAULT_PLAN.read_text(encoding="utf8"))
    assert "profile_id" not in raw
    ids = tmp_path / "ids.txt"
    ids.write_text(",".join(str(i) for i in range(123)), encoding="utf8")
    raw["regions"]["boyaca"]["ids_file"] = str(ids)
    raw["unspsc"]["catalog_file"] = str(
        plans.DEFAULT_PLAN.parent.parent / "config/eureka_radar.v1.json"
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(raw), encoding="utf8")
    assert plans.load_plan(plan_path)["profile_id"] == "730006"
    assert plans.load_plan(plan_path, profile_id="730007")["profile_id"] == "730007"
    raw["profile_id"] = "730008"
    plan_path.write_text(json.dumps(raw), encoding="utf8")
    with pytest.raises(runtime.SpikeError, match="Plan invalido"):
        plans.load_plan(plan_path)


def test_adapter_receives_configured_profile_and_injection(monkeypatch):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", "730009")
    assert LicitacionesInfoSource(Mock()).profile_id == "730009"
    assert LicitacionesInfoSource(Mock(), profile_id="730010").profile_id == "730010"


def test_identity_does_not_invent_profile_or_rewrite_persisted_namespace(monkeypatch):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", "730011")
    process = {"id_contrato": "77", "key_config": "external"}
    assert process_identity(process) is None
    assert process_identity({**process, "profile_id": "730012"}) == "licitaciones_info:730012:77"
    assert (
        process_identity(
            {
                **process,
                "process_reference": "licitaciones_info:730013:77",
            }
        )
        == "licitaciones_info:730013:77"
    )
