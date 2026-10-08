"""Configuración por ambiente, leída de variables de entorno (y de `.env` en local)."""

from enum import StrEnum
from typing import Any

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REQUIRED_VARIABLES = ("DATABASE_URL",)


class AppEnvironment(StrEnum):
    LOCAL = "local"
    CI = "ci"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class MissingConfigurationError(RuntimeError):
    def __init__(self, variable: str) -> None:
        super().__init__(f"Falta la variable de entorno obligatoria: {variable}.")
        self.variable = variable


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    database_url: str
    app_env: AppEnvironment = AppEnvironment.LOCAL
    log_level: LogLevel = LogLevel.INFO

    @field_validator("database_url")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("blank")
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: Any) -> Any:
        return value.upper() if isinstance(value, str) else value


def load_settings(**overrides: Any) -> Settings:
    """Carga la configuración; falla con un mensaje en español si falta una variable obligatoria."""
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        for error in exc.errors():
            location = str(error["loc"][0]).upper() if error["loc"] else ""
            if location in REQUIRED_VARIABLES:
                raise MissingConfigurationError(location) from None
        raise
