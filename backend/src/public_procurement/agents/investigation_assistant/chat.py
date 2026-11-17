"""Small owner-scoped ephemeral conversations. Local receipts are read-only."""

import logging
import re
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from public_procurement.investigation.services import build_assistant_queries
from public_procurement.shared.config import Settings

from ..eureka_assistant.schemas import FoundrySettings
from .diagnostics import configuration, emit, failure
from .service import AssistantError, InvestigationAssistant, summary


class Reply(BaseModel):
    conversation_id: UUID
    response: str
    run_references: list[str] = Field(default_factory=list)
    process_references: list[str] = Field(default_factory=list)


class AzureTransport:
    def __init__(self, remote: Any, model: str) -> None:
        self.remote, self.model = remote, model

    def respond(
        self, inputs: list[Any], tools: list[dict[str, Any]], forced: str | None, timeout: float
    ) -> Any:
        # Azure Projects requires explicit message discriminators, including
        # developer instructions, conversation history and grounding reminders.
        # Leave function calls/outputs unchanged and never mutate local history.
        messages = [
            {"type": "message", **item}
            if isinstance(item, dict) and "role" in item and "type" not in item
            else item
            for item in inputs
        ]
        emit("foundry_request", stage="responses.create", forced_tool=forced)
        try:
            return self.remote.responses.create(
                model=self.model,
                input=messages,
                tools=tools,
                parallel_tool_calls=False,
                tool_choice={"type": "function", "name": forced} if forced else "auto",
                timeout=timeout,
                max_output_tokens=2000,
                store=False,
            )
        except Exception as error:
            diagnostic = failure("responses.create", error)
            code, status = (
                ("timeout", 504)
                if isinstance(error, TimeoutError) or type(error).__name__ == "APITimeoutError"
                else ("foundry_request_failed", 503)
            )
            raise AssistantError(code, status, diagnostic=diagnostic) from None


@contextmanager
def foundry_assistant() -> Iterator[InvestigationAssistant]:
    try:
        config = FoundrySettings()
    except Exception as error:
        raise AssistantError(
            "azure_configuration_missing", diagnostic=failure("configuration", error)
        ) from None
    emit("foundry_configuration", **configuration(config))
    for namespace in ("azure", "openai", "httpx", "httpx2", "httpcore", "httpcore2"):
        logging.getLogger(namespace).setLevel(logging.CRITICAL)
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError as error:
        raise AssistantError(
            "foundry_unavailable", diagnostic=failure("sdk_import", error)
        ) from None
    # Same project/model and credential procedure as Eureka, separate prompt and tool set.
    # No remote agent creation/version edit; no hosted web/code/MCP tools are sent.
    try:
        with (
            DefaultAzureCredential(exclude_interactive_browser_credential=True) as credential,
            AIProjectClient(
                endpoint=config.azure_foundry_project_endpoint,
                credential=credential,
                connection_timeout=10,
                read_timeout=config.eureka_foundry_timeout_seconds,
                retry_total=0,
            ) as project,
            project.get_openai_client(
                timeout=config.eureka_foundry_timeout_seconds, max_retries=0
            ) as remote,
        ):
            yield InvestigationAssistant(
                AzureTransport(remote, config.eureka_foundry_model_deployment),
                config.eureka_foundry_timeout_seconds,
            )
    except AssistantError:
        raise
    except Exception as error:
        raise AssistantError(
            "foundry_unavailable", diagnostic=failure("client_setup_or_close", error)
        ) from None


@dataclass
class Session:
    owner: UUID
    updated: float
    history: list[dict[str, Any]] = field(default_factory=list)
    turns: int = 0
    run_id: UUID | None = None
    lock: Any = field(default_factory=threading.Lock)


class InvestigationChat:
    def __init__(
        self,
        settings: Settings,
        factory: Callable[..., Any] = foundry_assistant,
        now: Callable[[], datetime] = lambda: datetime.now(ZoneInfo("America/Bogota")),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.directory = settings.local_storage_path.parent / "investigation"
        self.factory, self.now, self.clock = factory, now, clock
        self.sessions: dict[UUID, Session] = {}
        self.guard = threading.Lock()

    def clear(self) -> None:
        with self.guard:
            self.sessions.clear()

    def query(self, message: str, run_id: UUID | None = None) -> Any:
        ids = re.findall(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", message)
        if len(set(ids)) > 1 or (ids and run_id and UUID(ids[0]) != run_id):
            raise AssistantError("ambiguous_run_selection", 422)
        identifier = str(run_id) if run_id else ids[0] if ids else None
        selection = r"(?:corrida|la de|[úu]ltima)\s+(?:investigativa\s+)?(?:de\s+)?"
        private = re.search(selection + r"(?:estado\s+vs\s+)?mercado\s+privado", message, re.I)
        public = re.search(selection + r"estado\s+vs\.?\s+estado", message, re.I)
        if private and public:
            raise AssistantError("ambiguous_run_selection", 422)
        kind = "state_vs_private_market" if private else "state_vs_state" if public else None
        queries = build_assistant_queries(self.directory)
        with suppress(FileNotFoundError):
            queries.select(identifier, kind, bool(re.search(r"\bhoy\b", message, re.I)), self.now())
        return queries

    def chat(
        self, message: str, conversation_id: UUID | None, run_id: UUID | None, owner: UUID
    ) -> Reply:
        if not message.strip() or len(message) > 4000:
            raise AssistantError("invalid_message", 422)
        key, now = conversation_id or uuid4(), self.clock()
        with self.guard:
            for old, session in list(self.sessions.items()):
                if not session.lock.locked() and now - session.updated > 1800:
                    del self.sessions[old]
            state = self.sessions.get(key)
            if conversation_id and (state is None or state.owner != owner):
                raise AssistantError("conversation_expired", 404)
            if state is None:
                if len(self.sessions) >= 50:
                    raise AssistantError("assistant_busy", 429)
                state = Session(owner, now)
                self.sessions[key] = state
            if not state.lock.acquire(blocking=False):
                raise AssistantError("conversation_busy", 409)
        try:
            if state.turns >= 10:
                raise AssistantError("conversation_limit", 409)
            if run_id is None and re.search(r"\b(?:esta|esa)\s+corrida\b", message, re.I):
                run_id = state.run_id
            queries = self.query(message, run_id)
            selected = UUID(queries.metadata()["run_id"]) if queries.run else None
            history = state.history if selected == state.run_id else []
            if (
                queries.run is None
                or queries.metadata().get("provisional")
                or not queries.result_available
            ):
                result = {
                    "response": summary(queries.metadata(), {}),
                    "run_references": [str(selected)] if selected else [],
                    "process_references": [],
                }
            else:
                with self.factory() as assistant:
                    result = assistant.ask(message, queries, history, explicit=run_id is not None)
                for call in result.get("tool_calls", []):
                    emit(
                        "investigation_tool_completed",
                        name=call["name"],
                        run_id=str(selected),
                        total=call["output"].get("total"),
                    )
            state.run_id = selected
            state.history = [
                *state.history,
                {"role": "user", "content": message},
                {"role": "assistant", "content": result["response"]},
            ][-8:]
            state.updated, state.turns = self.clock(), state.turns + 1
            return Reply(
                conversation_id=key, **{k: v for k, v in result.items() if k != "tool_calls"}
            )
        except Exception as error:
            with self.guard:
                self.sessions.pop(key, None)
            if isinstance(error, AssistantError):
                raise
            if isinstance(error, TimeoutError) or type(error).__name__ in {
                "APITimeoutError",
                "ServiceResponseTimeoutError",
            }:
                raise AssistantError("timeout", 504) from None
            raise AssistantError("investigation_read_unavailable") from None
        finally:
            state.lock.release()
