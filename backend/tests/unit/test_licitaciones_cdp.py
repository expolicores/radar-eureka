"""Offline tests: no browser, network, credentials or DB."""

import ast
import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[2] / "scripts" / "observe_licitaciones_cdp.py"
SPEC = importlib.util.spec_from_file_location("cdp_observer", SOURCE)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.mark.parametrize("url", ["http://127.0.0.1:9222", "http://localhost:9222", "http://[::1]:9222"])
def test_local_cdp(url):
    assert module.validate_cdp_url(url) == url


@pytest.mark.parametrize("url", ["https://remote.test:9222", "http://127.0.0.1:9222/x", "http://user:secret@localhost:9222", "http://localhost", "http://localhost:9222/?token=secret"])
def test_reject_other_cdp(url):
    with pytest.raises(ValueError):
        module.validate_cdp_url(url)


def test_tab_and_endpoint_matching():
    assert module.is_contracts_tab("https://col.licitaciones.info/cliente/contratos#/?letra=MP")
    assert module.is_contracts_tab("https://mcol.licitaciones.info/cliente/contratos")
    assert module.is_get_info("https://mcol.licitaciones.info/cliente/contratos/get-info/MP", "POST")
    assert not module.is_get_info("https://fake.test/cliente/contratos/get-info/MP", "POST")
    assert not module.is_contracts_tab("https://fake.test/cliente/contratos")
    assert module.is_get_info("https://col.licitaciones.info/cliente/contratos/get-info/MP?perfiles=1086005", "POST")
    assert not module.is_get_info("https://col.licitaciones.info/cliente/contratos/get-conteo/MP", "POST")


def test_public_summary_only_and_generic_warning():
    report = module.summarize({"count": 1337370, "data": [{"CodigoProceso": "REF", "token": "SECRET"}]})
    assert report["generic_count_warning"]
    assert report["first_five"][0]["CodigoProceso"] == "REF"
    assert "SECRET" not in str(report)
    assert report["enriched_fields_present"]["key_config"] == 0
    with pytest.raises(ValueError):
        module.summarize({"unknown": []})


def test_no_browser_launch_navigation_replay_or_state_export():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    assert "connect_over_cdp" in calls
    assert not set(calls) & {"launch", "launch_persistent_context", "new_context", "new_page", "goto", "evaluate", "fetch", "storage_state", "cookies", "add_cookies", "close"}
