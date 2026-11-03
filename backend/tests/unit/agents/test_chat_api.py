import copy
import json
import uuid
from contextlib import contextmanager
from types import SimpleNamespace as Ns
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.agents.eureka_assistant.api import router
from public_procurement.agents.eureka_assistant.chat import (
    AssistantChat,
    ChatError,
    assistant_for_turn,
    references,
)
from public_procurement.agents.eureka_assistant.foundry_client import FoundryClient
from public_procurement.agents.eureka_assistant.schemas import TOOL_SCHEMAS, SpikeError, SpikeResult
from public_procurement.agents.eureka_assistant.service import EurekaAssistant
from public_procurement.shared.config import Settings

from .test_eureka_assistant import call, client, config, make_tool, response, run

OWNER = uuid.uuid4()
IDENTITY = "secop:CO1.NTC.11147197"


def result(answer="Resumen", results=None):
    return SpikeResult(
        agent_name="eureka-assistant",
        agent_version="11",
        conversation_id="azure-private-id",
        tool_results=results or [],
        answer=answer,
    )


def http(assistant):
    versions = []

    @contextmanager
    def factory(version):
        versions.append(version)
        yield assistant

    service = AssistantChat(factory)
    app = FastAPI()
    app.state.assistant_chat = service
    app.state.current_user_provider = lambda _: OWNER
    app.include_router(router)
    return TestClient(app), service, versions


def test_new_chat_and_continuation_keep_private_conversation_and_pinned_version():
    assistant = Mock(spec=EurekaAssistant)
    assistant.ask.return_value = result()
    api, _, versions = http(assistant)
    first = api.post("/api/eureka/assistant/chat", json={"message": "Resumen"})
    assert first.status_code == 200
    public_id = first.json()["conversation_id"]
    assert uuid.UUID(public_id)
    assert public_id != "azure-private-id"
    assert set(first.json()) == {
        "conversation_id",
        "message",
        "process_references",
        "external_references",
        "web_searches",
    }
    second = api.post(
        "/api/eureka/assistant/chat",
        json={"message": "¿Y sus documentos?", "conversation_id": public_id},
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == public_id
    assert versions == [None, "11"]
    assert assistant.ask.call_args_list[0].kwargs == {"conversation_id": None}
    assert assistant.ask.call_args_list[1].kwargs == {"conversation_id": "azure-private-id"}
    assert "azure-private-id" not in second.text
    assert "agent_version" not in second.text


def test_existing_assistant_service_reuses_remote_context_without_creating_new_conversation():
    tool, _ = make_tool(run())
    remote = client(
        response(call()),
        response(answer="Primero"),
        response(call(call_id="c2")),
        response(answer="Segundo"),
    )
    assistant = EurekaAssistant(remote, tool)
    first = assistant.ask("Resumen")
    second = assistant.ask("¿Qué más?", conversation_id=first.conversation_id)
    assert second.conversation_id == first.conversation_id
    remote.openai.conversations.create.assert_called_once()
    assert all(
        c.kwargs["conversation"] == first.conversation_id
        for c in remote.openai.responses.create.call_args_list
    )


def test_http_client_never_creates_agent_versions_or_changes_instructions():
    models = pytest.importorskip("azure.ai.projects.models")
    definition = {
        "kind": "prompt",
        "model": "gpt-4.1-mini-eureka",
        "instructions": "unchanged",
        "tools": copy.deepcopy(TOOL_SCHEMAS),
    }
    stored = Ns(
        name="eureka-assistant", version="11", definition=models.PromptAgentDefinition(definition)
    )
    project = Mock()
    project.agents.get.return_value = Ns(versions=Ns(latest=stored))
    remote = FoundryClient(project, Mock(), config(), reuse_existing_version=True)
    assert remote.prepare_version() == ("eureka-assistant", "11")
    project.agents.create_version.assert_not_called()
    assert stored.definition.as_dict()["instructions"] == "unchanged"


@pytest.mark.parametrize(
    ("failure", "code", "status"),
    [
        (SpikeError("safe", code="tool_failure"), "tool_failure", 502),
        (SpikeError("safe", code="timeout"), "timeout", 504),
        (
            RuntimeError("Authorization private-token endpoint private-host"),
            "foundry_unavailable",
            503,
        ),
        (TimeoutError("sensitive"), "timeout", 504),
        (ChatError("azure_configuration_missing"), "azure_configuration_missing", 503),
    ],
)
def test_failures_are_explicit_safe_and_recoverable(failure, code, status, caplog):
    assistant = Mock(spec=EurekaAssistant)
    assistant.ask.side_effect = failure
    api, _, _ = http(assistant)
    r = api.post("/api/eureka/assistant/chat", json={"message": "Resumen"})
    assert r.status_code == status
    assert r.json()["code"] == code
    assert r.json()["reset_conversation"] is True
    assert "No pude consultar Eureka" in r.json()["message"]
    assert "private-token" not in r.text + caplog.text
    assert "private-host" not in r.text + caplog.text


def test_empty_answer_is_not_reported_as_success():
    assistant = Mock(spec=EurekaAssistant)
    assistant.ask.return_value = result("  ")
    api, _, _ = http(assistant)
    r = api.post("/api/eureka/assistant/chat", json={"message": "Resumen"})
    assert r.status_code == 502
    assert r.json()["code"] == "empty_response"


def test_missing_configuration_fails_lazily_without_contacting_azure(monkeypatch):
    def absent():
        raise ValueError("private config")

    monkeypatch.setattr("public_procurement.agents.eureka_assistant.chat.FoundrySettings", absent)
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://unused@localhost/unused")
    with (
        pytest.raises(ChatError, match="azure_configuration_missing"),
        assistant_for_turn(settings, None),
    ):
        pytest.fail("Must not initialize SDK or tools")


def test_references_only_from_actual_structured_reads_no_text_parsing_or_raw_payloads():
    values = [
        {
            "found": True,
            "items": [
                {
                    "identity": IDENTITY,
                    "process_code": "MC-CMC-003-2026",
                    "headers": {"Authorization": "private"},
                }
            ],
        },
        {
            "found": True,
            "identity": IDENTITY,
            "entity": "Concejo Corrales",
            "municipality": "Corrales",
            "source_url": "https://community.secop.gov.co/Public/Tendering",
        },
        {"found": False, "identity": "secop:CO1.NTC.999"},
        {"identity": "javascript:alert(1)", "source_url": "javascript:alert(1)"},
    ]
    answer = references(values)
    assert len(answer) == 1
    assert answer[0].process_code == "MC-CMC-003-2026"
    assert answer[0].entity == "Concejo Corrales"
    assert "private" not in json.dumps([r.model_dump() for r in answer])
    assert references([]) == []
    assert (
        references([{"identity": IDENTITY, "source_url": "https://user:password@example.com"}])[
            0
        ].source_url
        is None
    )


def test_endpoint_does_not_create_references_from_model_inventions():
    assistant = Mock(spec=EurekaAssistant)
    assistant.ask.return_value = result("Recomiendo MC-INVENTADO-2026")
    api, _, _ = http(assistant)
    assert (
        api.post("/api/eureka/assistant/chat", json={"message": "Resumen"}).json()[
            "process_references"
        ]
        == []
    )


def test_endpoint_executes_only_existing_read_tool_and_rejects_business_writer():
    raw = run()
    before = copy.deepcopy(raw)
    tool, queries = make_tool(raw)
    remote = client(response(call()), response(answer="Resumen"), response(call(name="run_cdp")))
    api, _, _ = http(EurekaAssistant(remote, tool))
    assert api.post("/api/eureka/assistant/chat", json={"message": "Resumen"}).status_code == 200
    failed = api.post("/api/eureka/assistant/chat", json={"message": "Ejecuta Radar"})
    assert failed.status_code == 502
    queries.runs.assert_called_once()
    assert raw == before


def test_conversation_expiry_ownership_and_limits_never_start_remote_work():
    assistant = Mock(spec=EurekaAssistant)
    assistant.ask.return_value = result()
    api, service, _ = http(assistant)
    public_id = uuid.UUID(
        api.post("/api/eureka/assistant/chat", json={"message": "Resumen"}).json()[
            "conversation_id"
        ]
    )
    with pytest.raises(ChatError, match="conversation_expired"):
        service.chat("Otro", public_id, uuid.uuid4())
    service._sessions[public_id].lock.acquire()
    try:
        with pytest.raises(ChatError, match="conversation_busy"):
            service.chat("Otro", public_id, OWNER)
    finally:
        service._sessions[public_id].lock.release()
    service.clock = lambda: service._sessions[public_id].updated + 1801
    with pytest.raises(ChatError, match="conversation_expired"):
        service.chat("Otro", public_id, OWNER)
    assistant.ask.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        {"message": " "},
        {"message": "x" * 4001},
        {"message": "Resumen", "conversation_id": "azure-id"},
        {"message": "Resumen", "endpoint": "private"},
    ],
)
def test_request_rejects_empty_oversized_or_internal_provider_input(payload):
    assistant = Mock(spec=EurekaAssistant)
    api, _, _ = http(assistant)
    assert api.post("/api/eureka/assistant/chat", json=payload).status_code == 422
    assistant.ask.assert_not_called()
