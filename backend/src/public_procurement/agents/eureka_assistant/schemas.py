"""Small allowlisted payloads; never serialize raw run/provider data to the model."""

from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TOOL_NAME = "get_latest_cdp_run"
TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "name": TOOL_NAME,
    "description": (
        "Obtiene el resumen de la corrida más reciente de Licitaciones.info (CDP) "
        "persistida en Eureka. Solo lectura; no ejecuta corridas."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
    "strict": True,
}


def parameter_tool(name: str, field: str, description: str) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {field: {"type": "string"}},
            "required": [field],
            "additionalProperties": False,
        },
        "strict": True,
    }


TOOL_SCHEMAS = [
    TOOL_SCHEMA,
    {
        "type": "function",
        "name": "get_eureka_commercial_profile",
        "description": "Lee el perfil comercial real y vigente de Eureka: regiones, categorías, "
        "monto preferido y condiciones de complejidad. "
        "Consúltalo primero para priorizar oportunidades para el usuario.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    parameter_tool(
        "get_run_alerts",
        "run_id",
        "Lee hasta 10 alertas creadas en la corrida indicada por UUID. "
        "No incluye alertas previas omitidas por dedupe.",
    ),
    parameter_tool(
        "get_run_review_candidates",
        "run_id",
        "Lee hasta 10 procesos de esa corrida que siguen en Merecen Revisión; "
        "primero las entradas nuevas. Excluye procesos con alerta.",
    ),
    parameter_tool(
        "get_process_detail",
        "identity",
        "Lee metadata y decisión consolidada de una identidad canónica exacta. "
        "No recalcula scoring ni confirma vigencia con el proveedor.",
    ),
    parameter_tool(
        "get_process_evidence",
        "identity",
        "Lee hasta 20 facts y canonicals y 10 documentos persistidos; "
        "distingue evidencia documental de metadata. No descarga ni ejecuta OCR.",
    ),
]


class FoundrySettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    azure_foundry_project_endpoint: str
    eureka_foundry_agent_name: str = "eureka-assistant"
    eureka_foundry_model_deployment: str = "gpt-4.1-mini-eureka"
    eureka_foundry_timeout_seconds: float = Field(default=120, ge=5, le=600)

    @field_validator("azure_foundry_project_endpoint")
    @classmethod
    def project_endpoint(cls, value: str) -> str:
        parts = urlsplit(value)
        if (
            parts.scheme != "https"
            or not parts.hostname
            or parts.username
            or parts.password
            or parts.query
            or parts.fragment
            or "/api/projects/" not in parts.path
        ):
            raise ValueError("Configura el Project endpoint HTTPS de Foundry, sin credenciales.")
        return value.rstrip("/")


class LatestCdpRunSummary(BaseModel):
    has_run: bool
    source: str = "licitaciones_info_cdp"
    run_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    status: str | None = None
    processes_total: int | None = Field(default=None, ge=0)
    recent_processes: int | None = Field(default=None, ge=0)
    open_processes: int | None = Field(default=None, ge=0)
    processed: int | None = Field(default=None, ge=0)
    review_candidates_total: int | None = Field(default=None, ge=0)
    review_new_entries: int | None = Field(default=None, ge=0)
    review_existing_entries: int | None = Field(default=None, ge=0)
    alert_candidates: int | None = Field(default=None, ge=0)
    alerts_created: int | None = Field(default=None, ge=0)
    duplicate_alerts: int | None = Field(default=None, ge=0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SpikeError(RuntimeError):
    """Only safe, application-owned messages may reach the CLI."""


class SpikeResult(BaseModel):
    agent_name: str
    agent_version: str
    conversation_id: str
    tool_results: list[LatestCdpRunSummary | dict[str, Any]]
    answer: str
