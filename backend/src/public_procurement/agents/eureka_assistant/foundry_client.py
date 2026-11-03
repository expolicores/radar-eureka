"""Current Azure AI Projects agent versions + Responses; no legacy Assistants API."""

from copy import deepcopy
from typing import Any

from .schemas import TOOL_NAME, TOOL_SCHEMAS, FoundrySettings, SpikeError


class FoundryClient:
    def __init__(
        self,
        project: Any,
        responses_client: Any,
        config: FoundrySettings,
        *,
        agent_version: str | None = None,
        reuse_existing_version: bool = False,
    ) -> None:
        self.project, self.openai, self.config = project, responses_client, config
        self.agent_version = agent_version
        self.reuse_existing_version = reuse_existing_version
        self.web_search_available = False

    def prepare_version(self) -> tuple[str, str]:
        from azure.ai.projects.models import PromptAgentDefinition

        current = (
            self.project.agents.get_version(
                self.config.eureka_foundry_agent_name, self.agent_version
            )
            if self.agent_version is not None
            else self.project.agents.get(self.config.eureka_foundry_agent_name).versions.latest
        )
        definition = deepcopy(current.definition.as_dict())
        if definition.get("kind") != "prompt":
            raise SpikeError("El agente almacenado no es un Prompt Agent.")
        if definition.get("model") != self.config.eureka_foundry_model_deployment:
            raise SpikeError(
                "El deployment almacenado difiere de la configuración; no se modificó."
            )
        # Fail closed if the remote agent has acquired capabilities outside this spike.
        tools = definition.get("tools") or []
        names = {t["name"] for t in TOOL_SCHEMAS}
        functions = [t for t in tools if t.get("type") == "function"]
        web = [t for t in tools if t.get("type") == "web_search"]
        if (
            len(web) > 1
            or len(functions) + len(web) != len(tools)
            or any(t.get("name") not in names for t in functions)
        ):
            raise SpikeError("El agente tiene otras tools; revisa su definición antes del spike.")
        self.web_search_available = bool(web)
        if self.agent_version is not None or self.reuse_existing_version:
            expected = {t["name"]: t["parameters"] for t in TOOL_SCHEMAS}
            if (
                len(functions) != len(expected)
                or {t["name"]: t.get("parameters") for t in functions} != expected
            ):
                raise SpikeError("La versión indicada no tiene el contrato de tool esperado.")
            return str(current.name), str(current.version)
        definition["tools"] = deepcopy(TOOL_SCHEMAS) + deepcopy(web)
        # All stored instructions and other definition settings remain authoritative.
        version = self.project.agents.create_version(
            agent_name=self.config.eureka_foundry_agent_name,
            definition=PromptAgentDefinition(definition),
        )
        return str(version.name), str(version.version)

    def conversation(self) -> str:
        return str(self.openai.conversations.create().id)

    def respond(
        self,
        conversation: str,
        name: str,
        version: str,
        inputs: Any,
        timeout: float,
        *,
        first: bool,
        first_tool: str = TOOL_NAME,
        web_mode: bool = False,
        force_web: bool = False,
    ) -> Any:
        choice: Any = "auto"
        if first:
            choice = {"type": "function", "name": first_tool}
        elif self.web_search_available:
            allowed = [{"type": "function", "name": t["name"]} for t in TOOL_SCHEMAS]
            if web_mode:
                allowed.append({"type": "web_search"})
            choice = {
                "type": "allowed_tools",
                "mode": "required" if force_web else "auto",
                "tools": [{"type": "web_search"}] if force_web else allowed,
            }
        options = {"include": ["web_search_call.action.sources"]} if web_mode else {}
        return self.openai.responses.create(
            conversation=conversation,
            input=inputs,
            extra_body={
                "agent_reference": {"type": "agent_reference", "name": name, "version": version}
            },
            tool_choice=choice,
            parallel_tool_calls=False,
            timeout=timeout,
            **options,
        )
