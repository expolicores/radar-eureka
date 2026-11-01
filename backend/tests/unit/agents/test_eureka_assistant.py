import copy
import json
from types import SimpleNamespace as Ns
from unittest.mock import Mock

import pytest

from public_procurement.agents.eureka_assistant.foundry_client import FoundryClient
from public_procurement.agents.eureka_assistant.schemas import (
    TOOL_SCHEMAS,
    FoundrySettings,
    SpikeError,
)
from public_procurement.agents.eureka_assistant.service import EurekaAssistant, validate_call
from public_procurement.agents.eureka_assistant.tools import LatestCdpRunTool, read_only_tool
from public_procurement.shared.config import Settings


def run():
    return {
        "id": "run-1",
        "started_at": "2026-10-29T19:24:38+00:00",
        "finished_at": "2026-10-29T19:31:20+00:00",
        "status": "completed_with_warnings",
        "alerts_created": 2,
        "errors": [],
        "metrics": {
            "processes_total": 143,
            "recent_processes": 19,
            "open_processes": 6,
            "processed": 3,
            "review_candidates_total": 6,
            "review_new_entries": 2,
            "review_existing_entries": 4,
            "alert_candidates": 4,
            "duplicate_alerts_skipped": 2,
            "warnings": [{"code": "ocr_truncated", "headers": {"Authorization": "secret"}}],
            "process_error_details": [{"code": "extraction_failed", "message": "secret"}],
        },
    }


def config():
    return FoundrySettings(
        _env_file=None,
        azure_foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/compras-publicas-eureka",
    )


def make_tool(value=None):
    queries = Mock(spec=["runs"])
    queries.runs.return_value = {"items": [] if value is None else [value]}
    return LatestCdpRunTool(queries), queries


def call(arguments="{}", name="get_latest_cdp_run", call_id="call-1"):
    return Ns(type="function_call", name=name, arguments=arguments, call_id=call_id)


def response(*items, answer="", status="completed"):
    return Ns(output=list(items), output_text=answer, status=status)


def client(*responses):
    project = Mock()
    openai = Mock()
    openai.conversations.create.return_value = Ns(id="conversation-1")
    openai.responses.create.side_effect = list(responses)
    result = FoundryClient(project, openai, config())
    result.prepare_version = Mock(return_value=("eureka-assistant", "2"))
    return result


def test_summary_serializes_compact_allowlisted_counters_without_secrets():
    raw = run()
    before = copy.deepcopy(raw)
    tool, queries = make_tool(raw)
    summary = tool.get_latest_cdp_run()
    data = json.loads(summary.model_dump_json())
    assert data["run_id"] == "run-1"
    assert data["processes_total"] == 143
    assert data["review_candidates_total"] == 6
    assert data["duplicate_alerts"] == 2
    assert data["warnings"] == ["ocr_truncated"]
    assert data["errors"] == ["extraction_failed"]
    assert "secret" not in summary.model_dump_json()
    assert "headers" not in summary.model_dump_json()
    assert raw == before
    queries.runs.assert_called_once_with(page=1, page_size=1)


def test_no_run_is_explicit_and_unknown_metrics_are_not_zero():
    tool, _ = make_tool()
    result = tool.get_latest_cdp_run()
    assert result.has_run is False
    assert result.run_id is None
    assert result.processes_total is None
    raw = run()
    raw["metrics"] = {}
    tool, _ = make_tool(raw)
    assert tool.get_latest_cdp_run().open_processes is None


def test_preflight_and_query_warnings_are_included_without_duplicate_codes():
    raw = run()
    raw["metrics"]["preflight"] = {"warnings": [{"code": "provider_ignores_limit"}]}
    raw["metrics"]["queries"] = [{"warnings": [{"code": "provider_ignores_limit"}]}]
    tool, _ = make_tool(raw)
    assert tool.get_latest_cdp_run().warnings == ["ocr_truncated", "provider_ignores_limit"]


def test_function_call_output_returns_to_same_conversation_and_pinned_version():
    tool, queries = make_tool(run())
    remote = client(response(call()), response(answer="La corrida creó 2 alertas."))
    events = []
    result = EurekaAssistant(remote, tool, lambda k, v: events.append((k, v))).ask("¿Qué salió?")
    assert result.answer == "La corrida creó 2 alertas."
    first, second = remote.openai.responses.create.call_args_list
    assert [item["type"] for item in first.kwargs["input"]] == ["message", "message"]
    assert first.kwargs["tool_choice"]["name"] == "get_latest_cdp_run"
    assert first.kwargs["parallel_tool_calls"] is False
    assert second.kwargs["conversation"] == first.kwargs["conversation"] == "conversation-1"
    assert second.kwargs["extra_body"]["agent_reference"] == {
        "name": "eureka-assistant",
        "version": "2",
        "type": "agent_reference",
    }
    output = second.kwargs["input"][0]
    assert output["type"] == "function_call_output"
    assert output["call_id"] == "call-1"
    assert json.loads(output["output"])["alerts_created"] == 2
    assert [k for k, v in events] == ["agent_version", "tool_requested", "tool_result"]
    queries.runs.assert_called_once()


def test_repeated_calls_reuse_snapshot_without_multiple_db_reads():
    tool, queries = make_tool(run())
    remote = client(response(call()), response(call(call_id="call-2")), response(answer="Resumen"))
    assert EurekaAssistant(remote, tool).ask("Resumen").answer == "Resumen"
    queries.runs.assert_called_once()


@pytest.mark.parametrize("arguments", ["{", "null", "[]", "1", '{"run_id":"other"}'])
def test_invalid_arguments_never_execute_tool(arguments):
    tool, queries = make_tool(run())
    with pytest.raises(SpikeError, match=r"JSON|parámetros"):
        EurekaAssistant(client(response(call(arguments))), tool).ask("Resumen")
    queries.runs.assert_not_called()


def test_unknown_function_is_not_dispatched():
    with pytest.raises(SpikeError, match="no permitida"):
        validate_call("run_cdp", "{}")


@pytest.mark.parametrize("status", ["failed", "incomplete", "expired", "cancelled", "in_progress"])
def test_failed_or_expired_response_has_no_db_effect(status):
    raw = run()
    before = copy.deepcopy(raw)
    tool, queries = make_tool(raw)
    with pytest.raises(SpikeError, match="fallida"):
        EurekaAssistant(client(response(call(), status=status)), tool).ask("Resumen")
    queries.runs.assert_not_called()
    assert raw == before


def test_failure_after_read_keeps_data_and_does_not_expose_provider_error():
    raw = run()
    before = copy.deepcopy(raw)
    tool, queries = make_tool(raw)
    remote = client(response(call()), RuntimeError("Authorization: secret"))
    with pytest.raises(SpikeError, match="Falló Foundry") as error:
        EurekaAssistant(remote, tool).ask("Resumen")
    assert "secret" not in str(error.value)
    assert raw == before
    queries.runs.assert_called_once()


def test_timeout_and_ungrounded_final_fail_closed():
    tool, queries = make_tool(run())
    clock = Mock(side_effect=[0, 121])
    with pytest.raises(SpikeError, match="tiempo"):
        EurekaAssistant(client(), tool, clock=clock).ask("Resumen")
    with pytest.raises(SpikeError, match="sustentada"):
        EurekaAssistant(client(response(answer="Inventado")), tool).ask("Resumen")
    queries.runs.assert_not_called()


def test_network_timeout_is_actionable_and_does_not_retry():
    tool, queries = make_tool(run())
    remote = client(TimeoutError("secret"))
    with pytest.raises(SpikeError, match="timeout") as error:
        EurekaAssistant(remote, tool).ask("Resumen")
    assert "secret" not in str(error.value)
    assert remote.openai.responses.create.call_count == 1
    queries.runs.assert_not_called()


def test_empty_dataset_round_trip_still_returns_tool_output():
    tool, _ = make_tool()
    remote = client(response(call()), response(answer="No hay corrida CDP persistida."))
    result = EurekaAssistant(remote, tool).ask("Última corrida")
    assert result.tool_results[0].has_run is False
    assert result.answer == "No hay corrida CDP persistida."


def remote_project(definition):
    models = pytest.importorskip("azure.ai.projects.models")
    project = Mock()
    project.agents.get.return_value = Ns(
        versions=Ns(latest=Ns(definition=models.PromptAgentDefinition(definition)))
    )
    project.agents.create_version.return_value = Ns(name="eureka-assistant", version="2")
    return project


def test_new_version_preserves_remote_instructions_and_other_settings():
    definition = {
        "kind": "prompt",
        "model": "gpt-4.1-mini-eureka",
        "instructions": "Authoritative remote instructions",
        "tools": [],
        "temperature": 0.2,
    }
    before = copy.deepcopy(definition)
    project = remote_project(definition)
    remote = FoundryClient(project, Mock(), config())
    assert remote.prepare_version() == ("eureka-assistant", "2")
    request = project.agents.create_version.call_args.kwargs
    assert request["agent_name"] == "eureka-assistant"
    stored = request["definition"].as_dict()
    assert stored["instructions"] == definition["instructions"]
    assert stored["temperature"] == 0.2
    assert stored["tools"] == TOOL_SCHEMAS
    assert definition == before
    project.agents.get.assert_called_once_with("eureka-assistant")


def test_pinned_existing_version_does_not_create_an_extra_version():
    project = remote_project(
        {"kind": "prompt", "model": "gpt-4.1-mini-eureka", "tools": TOOL_SCHEMAS}
    )
    version = project.agents.get.return_value.versions.latest
    version.name, version.version = "eureka-assistant", "3"
    project.agents.get_version.return_value = version
    remote = FoundryClient(project, Mock(), config(), agent_version="3")
    assert remote.prepare_version() == ("eureka-assistant", "3")
    project.agents.get_version.assert_called_once_with("eureka-assistant", "3")
    project.agents.create_version.assert_not_called()
    project.agents.get.assert_not_called()


@pytest.mark.parametrize("changes", [{"model": "other"}, {"tools": [{"type": "web_search"}]}])
def test_unexpected_remote_configuration_does_not_create_version(changes):
    project = remote_project({"kind": "prompt", "model": "gpt-4.1-mini-eureka", **changes})
    with pytest.raises(SpikeError):
        FoundryClient(project, Mock(), config()).prepare_version()
    project.agents.create_version.assert_not_called()


def test_database_tool_enforces_postgresql_readonly(monkeypatch):
    import public_procurement.agents.eureka_assistant.tools as tools

    engine = Mock()
    engine.dialect.name = "postgresql"
    monkeypatch.setattr(tools, "create_db_engine", Mock(return_value=engine))
    monkeypatch.setattr(tools, "sessionmaker", Mock())
    monkeypatch.setattr(tools, "LicitacionesQueries", Mock())
    with read_only_tool(Settings(_env_file=None, database_url="postgresql://unused")):
        pass
    engine.execution_options.assert_called_once_with(postgresql_readonly=True)
    engine.dispose.assert_called_once()
