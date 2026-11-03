"""Temporary conversation orchestration. Opaque IDs; no SQL or business writes."""

import logging
import re
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from public_procurement.shared.config import Settings
from public_procurement.shared.logging import log_event

from .foundry_client import FoundryClient
from .schemas import ExternalReference, FoundrySettings, SpikeError, SpikeResult, WebSearchAction
from .service import EurekaAssistant
from .tools import read_only_tool

logger = logging.getLogger(__name__)
IDENTITY = re.compile(
    r"(?:secop:CO1\.(?:NTC|REQ)\.\d+|secop1:\d+-\d+-\d+|licitaciones_info:\d+:\d+)"
)


class ProcessReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: str
    process_code: str | None = None
    entity: str | None = None
    municipality: str | None = None
    department: str | None = None
    source_url: str | None = None


class ChatReply(BaseModel):
    conversation_id: uuid.UUID
    message: str
    process_references: list[ProcessReference] = Field(default_factory=list)
    external_references: list[ExternalReference] = Field(default_factory=list)
    web_searches: list[WebSearchAction] = Field(default_factory=list)


class ChatError(RuntimeError):
    def __init__(self, code: str, status: int = 503, *, reset: bool = True) -> None:
        super().__init__(code)
        self.code, self.status, self.reset = code, status, reset


@dataclass
class Conversation:
    owner: uuid.UUID
    remote_id: str | None = None
    agent_version: str | None = None
    updated: float = 0
    turns: int = 0
    lock: Any = field(default_factory=Lock)


def references(results: list[Any]) -> list[ProcessReference]:
    """Only actual structured tool results, never model text or a fresh DB query."""
    found: dict[str, ProcessReference] = {}

    def add(value: dict[str, Any]) -> None:
        identity = value.get("identity") or value.get("process_identity")
        if not isinstance(identity, str) or not IDENTITY.fullmatch(identity):
            return
        if value.get("found") is False:
            return
        location = value.get("location") or {}
        location = location if isinstance(location, dict) else {}

        def compact(v: Any) -> str | None:
            return v[:500] if isinstance(v, str) and v.strip() else None

        url = compact(value.get("source_url"))
        if url:
            try:
                parsed = urlsplit(url)
                if (
                    parsed.scheme not in ("https", "http")
                    or not parsed.hostname
                    or parsed.username
                    or parsed.password
                ):
                    url = None
            except ValueError:
                url = None
        new = ProcessReference(
            identity=identity,
            process_code=compact(value.get("process_code")),
            entity=compact(value.get("entity")),
            municipality=compact(value.get("municipality") or location.get("municipality")),
            department=compact(value.get("department") or location.get("department")),
            source_url=url,
        )
        previous = found.get(identity)
        if previous:
            new = ProcessReference.model_validate(
                {k: v or getattr(previous, k) for k, v in new.model_dump().items()}
            )
        found[identity] = new

    for result in results:
        if not isinstance(result, dict) or result.get("found") is False:
            continue
        add(result)
        metadata = result.get("metadata")
        if isinstance(metadata, dict):
            add(metadata)
        for item in result.get("items", []):
            if isinstance(item, dict):
                add(item)
    return list(found.values())[:20]


@contextmanager
def assistant_for_turn(settings: Settings, version: str | None) -> Iterator[EurekaAssistant]:
    """Lazy SDK/configuration: the rest of Eureka works without Foundry installed."""
    try:
        config = FoundrySettings()
    except Exception:
        raise ChatError("azure_configuration_missing") from None
    # These namespaces may otherwise log endpoints/headers/credential diagnostics.
    for namespace in ("azure", "openai", "httpx", "httpx2", "httpcore", "httpcore2"):
        logging.getLogger(namespace).setLevel(logging.CRITICAL)
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        raise ChatError("foundry_unavailable") from None
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
        read_only_tool(settings) as tool,
    ):

        def emit(event: str, value: Any) -> None:
            # Log operation types, never prompt, answer, tool output, endpoint or Azure IDs.
            if event == "tool_requested":
                log_event(logger, "assistant_tool_requested", tool=value["name"])
            elif event == "web_search_completed":
                log_event(
                    logger,
                    "assistant_web_search_completed",
                    queries=len(value["queries"]),
                    sources=len(value["sources"]),
                    warning_codes=value.get("warnings", []),
                )
            elif event == "web_research_pending":
                log_event(logger, "assistant_web_research_pending", codes=value["codes"])

        yield EurekaAssistant(
            FoundryClient(
                project, remote, config, agent_version=version, reuse_existing_version=True
            ),
            tool,
            emit,
        )


class AssistantChat:
    """One in-flight turn per conversation. Bounded ephemeral map per API worker."""

    def __init__(
        self,
        factory: Callable[[str | None], AbstractContextManager[EurekaAssistant]],
        *,
        ttl_seconds: float = 1800,
        max_conversations: int = 50,
        max_turns: int = 20,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.factory, self.ttl, self.capacity = factory, ttl_seconds, max_conversations
        self.max_turns, self.clock = max_turns, clock
        self._sessions: dict[uuid.UUID, Conversation] = {}
        self._guard = Lock()

    def clear(self) -> None:
        with self._guard:
            self._sessions.clear()

    def chat(self, message: str, conversation_id: uuid.UUID | None, owner: uuid.UUID) -> ChatReply:
        if not message.strip() or len(message) > 4000:
            raise ChatError("invalid_message", 422, reset=False)
        key = conversation_id or uuid.uuid4()
        now = self.clock()
        with self._guard:
            for old, session in list(self._sessions.items()):
                if not session.lock.locked() and now - session.updated >= self.ttl:
                    del self._sessions[old]
            state = self._sessions.get(key)
            if conversation_id and (state is None or state.owner != owner):
                raise ChatError("conversation_expired", 404)
            if state is None:
                if len(self._sessions) >= self.capacity:
                    raise ChatError("assistant_busy", 429, reset=False)
                state = Conversation(owner=owner, updated=now)
                self._sessions[key] = state
            if not state.lock.acquire(blocking=False):
                raise ChatError("conversation_busy", 409, reset=False)
        try:
            if state.turns >= self.max_turns:
                raise ChatError("conversation_limit", 409)
            with self.factory(state.agent_version) as assistant:
                result: SpikeResult = assistant.ask(message, conversation_id=state.remote_id)
            if not result.answer.strip():
                raise ChatError("empty_response", 502)
            state.remote_id, state.agent_version = result.conversation_id, result.agent_version
            state.turns += 1
            state.updated = self.clock()
            reply = ChatReply(
                conversation_id=key,
                message=result.answer,
                process_references=references(result.tool_results),
                external_references=result.external_references,
                web_searches=result.web_searches,
            )
            log_event(
                logger, "assistant_turn_completed", process_references=len(reply.process_references)
            )
            return reply
        except Exception as error:
            # An interrupted provider conversation may contain unresolved tool calls.
            # Invalidate that mapping instead of silently replaying a partial turn.
            with self._guard:
                self._sessions.pop(key, None)
            if isinstance(error, ChatError):
                safe = error
            elif isinstance(error, SpikeError):
                safe = ChatError(error.code, 504 if error.code == "timeout" else 502)
            elif isinstance(error, TimeoutError) or type(error).__name__ in {
                "APITimeoutError",
                "ServiceRequestTimeoutError",
                "ServiceResponseTimeoutError",
            }:
                safe = ChatError("timeout", 504)
            else:
                safe = ChatError("foundry_unavailable")
            log_event(
                logger,
                "assistant_turn_failed",
                logging.WARNING,
                code=safe.code,
                error_type=type(error).__name__,
            )
            raise safe from None
        finally:
            state.lock.release()


def build_assistant_chat(settings: Settings) -> AssistantChat:
    return AssistantChat(lambda version: assistant_for_turn(settings, version))
