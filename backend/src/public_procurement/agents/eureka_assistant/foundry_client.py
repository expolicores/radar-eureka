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
    ) -> None:
        self.project, self.openai, self.config = project, responses_client, config
        self.agent_version = agent_version

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
        if any(t.get("type") != "function" or t.get("name") not in names for t in tools):
            raise SpikeError("El agente tiene otras tools; revisa su definición antes del spike.")
        if self.agent_version is not None:
            expected = {t["name"]: t["parameters"] for t in TOOL_SCHEMAS}
            if (
                len(tools) != len(expected)
                or {t["name"]: t.get("parameters") for t in tools} != expected
            ):
                raise SpikeError("La versión indicada no tiene el contrato de tool esperado.")
            return str(current.name), str(current.version)
        definition["tools"] = deepcopy(TOOL_SCHEMAS)
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
    ) -> Any:
        return self.openai.responses.create(
            conversation=conversation,
            input=inputs,
            extra_body={
                "agent_reference": {"type": "agent_reference", "name": name, "version": version}
            },
            tool_choice={"type": "function", "name": first_tool} if first else "auto",
            parallel_tool_calls=False,
            timeout=timeout,
        )
