import copy
from datetime import UTC, datetime
from types import SimpleNamespace as Ns
from unittest.mock import Mock

import pytest

from public_procurement.agents.eureka_assistant.chat import references
from public_procurement.agents.eureka_assistant.foundry_client import FoundryClient
from public_procurement.agents.eureka_assistant.schemas import TOOL_SCHEMAS, SpikeError
from public_procurement.agents.eureka_assistant.service import EurekaAssistant
from public_procurement.agents.eureka_assistant.web import (
    WEB_POLICY,
    cited_answer,
    search_action,
    temporal_window,
    web_requested,
)

from .test_chat_api import http
from .test_eureka_assistant import call, client, config, make_tool, remote_project, response, run
from .test_read_tools import tools

NOW = datetime(2026, 11, 4, 19, 30, tzinfo=UTC)
QUESTION = "busca en la web procesos de mi interés que hayan salido esta semana"
URL = "https://www.colombiacompra.gov.co/proceso-ejemplo"


def web_response(answer="Hallazgo externo preliminar. No confirmado en Eureka.", *, sources=True):
    action = Ns(
        type="search",
        query="publicaciones oficiales ventana 2026-11-02 2026-11-04",
        sources=[Ns(url=URL)] if sources else [],
    )
    search = Ns(type="web_search_call", status="completed", action=action)
    annotations = (
        [
            Ns(
                type="url_citation",
                url=URL,
                title="Fuente oficial",
                start_index=0,
                end_index=len(answer),
            )
        ]
        if sources
        else []
    )
    message = Ns(
        type="message", content=[Ns(type="output_text", text=answer, annotations=annotations)]
    )
    return response(search, message, answer=answer)


def web_client(*answers):
    remote = client(*answers)
    remote.web_search_available = True
    return remote


def test_internal_question_does_not_enable_or_call_hosted_web_search():
    tool, queries = make_tool(run())
    remote = web_client(response(call()), response(answer="Resumen interno"))
    result = EurekaAssistant(remote, tool).ask("Resumen de la última corrida CDP")
    choice = remote.openai.responses.create.call_args_list[1].kwargs["tool_choice"]
    assert choice["type"] == "allowed_tools"
    assert all(t["type"] == "function" for t in choice["tools"])
    assert len(choice["tools"]) == 6
    assert result.web_searches == []
    assert result.external_references == []
    queries.runs.assert_called_once()


def test_explicit_web_flow_uses_real_profile_first_and_does_not_execute_discovery_or_writes():
    tool, reads = tools()
    tool.profile = Mock(
        return_value={"regions": ["Configuración de prueba"], "preferred_amount_max": 123}
    )
    remote = web_client(response(call(name="get_eureka_commercial_profile")), web_response())
    events = []
    result = EurekaAssistant(remote, tool, lambda k, v: events.append((k, v)), now=lambda: NOW).ask(
        QUESTION
    )
    first, second = remote.openai.responses.create.call_args_list
    assert first.kwargs["tool_choice"] == {
        "type": "function",
        "name": "get_eureka_commercial_profile",
    }
    assert second.kwargs["tool_choice"] == {
        "type": "allowed_tools",
        "mode": "required",
        "tools": [{"type": "web_search"}],
    }
    profile_json = second.kwargs["input"][0]["output"]
    assert "123" in profile_json
    assert tool.profile.call_count == 1
    assert [e[0] for e in events].index("tool_result") < [e[0] for e in events].index(
        "web_search_completed"
    )
    assert result.web_searches[0].queries
    assert result.external_references[0].url == URL
    assert "[1]" in result.answer
    assert result.external_references[0].published_at is None
    assert result.external_references[0].entity is None
    assert references(result.tool_results) == []
    reads.process.assert_not_called()
    reads.run_review.assert_not_called()
    assert "2026-11-02T00:00:00-05:00" in first.kwargs["input"][0]["content"]
    assert "2026-11-04T14:30:00-05:00" in first.kwargs["input"][0]["content"]


@pytest.mark.parametrize(
    ("question", "start", "end"),
    [
        ("esta semana", "2026-11-02T00:00:00-05:00", "2026-11-04T14:30:00-05:00"),
        ("últimos 7 días", "2026-10-28T14:30:00-05:00", "2026-11-04T14:30:00-05:00"),
        ("hoy", "2026-11-04T00:00:00-05:00", "2026-11-04T14:30:00-05:00"),
        ("ayer", "2026-11-03T00:00:00-05:00", "2026-11-04T00:00:00-05:00"),
    ],
)
def test_publication_window_is_concrete_bogota_time_not_run_timestamps(question, start, end):
    window = temporal_window(question, NOW)
    assert window["published_from"] == start
    assert window["published_until"] == end
    assert window["timezone"] == "America/Bogota"


def test_utc_monday_before_bogota_midnight_is_still_previous_week():
    assert (
        temporal_window("esta semana", datetime(2026, 11, 2, 3, tzinfo=UTC))["published_from"]
        == "2026-10-26T00:00:00-05:00"
    )


@pytest.mark.parametrize(
    ("question", "enabled"),
    [
        ("busca en la web", True),
        ("busca procesos nuevos", True),
        ("qué salió esta semana", True),
        ("revisa si hay algo reciente fuera de Eureka", True),
        ("qué salió esta semana en Eureka", False),
        ("resumen de la última corrida CDP", False),
        ("Qué alertas creó Radar hoy", False),
    ],
)
def test_web_request_routing(question, enabled):
    assert web_requested(question) is enabled


def test_empty_search_is_not_global_absence_and_does_not_invent_missing_fields():
    tool, _ = tools()
    remote = web_client(
        response(call(name="get_eureka_commercial_profile")),
        web_response("No existen procesos", sources=False),
    )
    result = EurekaAssistant(remote, tool).ask(QUESTION)
    assert "No existen procesos" not in result.answer
    assert "no es exhaustiva" in result.answer
    assert "aún no indexados" in result.answer
    assert result.external_references == []


def test_citations_never_create_references_from_free_text_or_unsafe_urls():
    raw = web_response("https://inventado.example/proceso", sources=False)
    answer, refs = cited_answer(raw, [])
    assert refs == []
    assert "inventado.example" not in answer
    raw = web_response()
    raw.output[1].content[0].annotations[0].url = "javascript:alert(1)"
    assert cited_answer(raw, [])[1] == []


def test_six_function_contracts_and_remote_instructions_remain_intact_with_web():
    definition = {
        "kind": "prompt",
        "model": "gpt-4.1-mini-eureka",
        "instructions": "Unchanged instructions",
        "tools": [*copy.deepcopy(TOOL_SCHEMAS), {"type": "web_search"}],
    }
    project = remote_project(definition)
    stored = project.agents.get.return_value.versions.latest
    stored.name, stored.version = "eureka-assistant", "12"
    remote = FoundryClient(project, Mock(), config(), reuse_existing_version=True)
    assert remote.prepare_version() == ("eureka-assistant", "12")
    assert remote.web_search_available
    project.agents.create_version.assert_not_called()
    assert stored.definition.as_dict()["instructions"] == "Unchanged instructions"
    assert stored.definition.as_dict()["tools"][:6] == TOOL_SCHEMAS


def test_unexpected_hosted_search_for_internal_question_fails_closed():
    tool, _ = make_tool(run())
    with pytest.raises(SpikeError, match="fuera del flujo"):
        EurekaAssistant(web_client(web_response()), tool).ask("Resumen de la corrida CDP")


def test_web_without_profile_cannot_run_even_if_provider_ignores_tool_choice():
    tool, _ = tools()
    with pytest.raises(SpikeError, match="fuera del flujo"):
        EurekaAssistant(web_client(web_response()), tool).ask(QUESTION)


def test_external_references_reach_http_separate_from_process_references():
    tool, _ = tools()
    remote = web_client(response(call(name="get_eureka_commercial_profile")), web_response())
    api, _, _ = http(EurekaAssistant(remote, tool))
    reply = api.post("/api/eureka/assistant/chat", json={"message": QUESTION})
    assert reply.status_code == 200
    data = reply.json()
    assert data["process_references"] == []
    assert data["external_references"][0]["url"] == URL
    assert data["web_searches"][0]["action"] == "search"
    assert "agent_version" not in data
    assert "Monto preferido" not in WEB_POLICY
    assert "Boyacá" not in WEB_POLICY


def test_external_information_can_use_web_when_needed_without_forcing_every_question():
    tool, _ = tools()
    remote = web_client(response(call(name="get_eureka_commercial_profile")), web_response())
    result = EurekaAssistant(remote, tool).ask("¿Cuál es la tasa de cambio actual?")
    choice = remote.openai.responses.create.call_args_list[1].kwargs["tool_choice"]
    assert choice["mode"] == "auto"
    assert {"type": "web_search"} in choice["tools"]
    assert result.external_references


def test_inverted_date_range_is_explicitly_flagged():
    action = search_action(
        Ns(action=Ns(type="search", query="publicación 2026-11-02..2026-11-01", sources=[]))
    )
    assert action.warnings == ["invalid_search_date_range"]


def test_bad_range_triggers_bounded_research_continuation_with_exact_dates():
    tool, _ = tools()
    bad = web_response()
    bad.output[0].action.query = "publicación 2026-11-02..2026-11-01"
    remote = web_client(response(call(name="get_eureka_commercial_profile")), bad, web_response())
    events = []
    result = EurekaAssistant(remote, tool, lambda k, v: events.append((k, v)), now=lambda: NOW).ask(
        QUESTION
    )
    assert len(result.web_searches) == 2
    third = remote.openai.responses.create.call_args_list[2].kwargs
    assert third["tool_choice"]["mode"] == "required"
    assert "2026-11-04T14:30:00-05:00" in str(third["input"])
    assert any(k == "web_research_pending" for k, _ in events)


def test_persistent_bad_range_does_not_claim_fresh_opportunities_or_retry_forever():
    tool, _ = tools()
    bad = web_response("Encontré procesos de esta semana.")
    bad.output[0].action.query = "fecha 2026-11-02..2026-11-01"
    remote = web_client(
        response(call(name="get_eureka_commercial_profile")), bad, copy.deepcopy(bad)
    )
    result = EurekaAssistant(remote, tool, now=lambda: NOW).ask(QUESTION)
    assert "no pude confirmar oportunidades concretas" in result.answer
    assert "no es exhaustiva" in result.answer
    assert "Encontré procesos de esta semana." not in result.answer
    assert len(remote.openai.responses.create.call_args_list) == 3


def test_portals_only_answer_does_not_stop_to_ask_permission():
    tool, _ = tools()
    premature = web_response("Encontré portales. ¿Quieres que profundice?", sources=False)
    premature.output[0].action.sources = [Ns(url=URL)]
    remote = web_client(
        response(call(name="get_eureka_commercial_profile")), premature, copy.deepcopy(premature)
    )
    result = EurekaAssistant(remote, tool).ask(QUESTION)
    assert "¿Quieres que profundice?" not in result.answer
    assert "solo devolvió fuentes generales" in result.answer
    assert len(result.web_searches) == 2
