"""Configuración por ambiente, leída de variables de entorno (y de `.env` en local)."""

import re
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import (
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    SecretStr,
    ValidationError,
    field_validator,
)
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
    test_database_url: str | None = None
    eureka_radar_start_date: date | None = None
    eureka_radar_regions: str = "Boyacá,Casanare"
    eureka_radar_interval_hours: PositiveInt = 12
    eureka_radar_max_processes: PositiveInt = 100
    eureka_automation_enabled: bool = False
    eureka_automation_allow_real_send: bool = False
    eureka_automation_interval_hours: PositiveInt = 12
    eureka_automation_timezone: str = "America/Bogota"
    eureka_automation_run_times: str = "07:00,19:00"
    eureka_automation_log_path: Path = Path(__file__).resolve().parents[3] / ".local/logs/eureka"
    eureka_log_retention_days: PositiveInt = 30
    eureka_automation_stale_minutes: PositiveInt = 180
    eureka_automation_task_name: str = "ComprasPublicas-EurekaRadar"
    eureka_preferred_budget_max: PositiveInt = 30_000_000
    eureka_radar_config_path: Path = (
        Path(__file__).resolve().parents[3] / "config" / "eureka_radar.v1.json"
    )
    eureka_metadata_alert_exclusions_path: Path = (
        Path(__file__).resolve().parents[3] / "config/eureka_metadata_alert_exclusions.v1.json"
    )
    local_storage_path: Path = Path(__file__).resolve().parents[3] / ".local" / "documents"
    document_timeout_seconds: PositiveFloat = 120
    document_max_bytes: PositiveInt = 50 * 1024 * 1024
    extraction_timeout_seconds: PositiveFloat = 60
    extraction_max_bytes: PositiveInt = 50 * 1024 * 1024
    extraction_max_chars: PositiveInt = 2_000_000
    extraction_max_fragments: PositiveInt = 10_000
    extraction_max_pages: PositiveInt = 300
    extraction_ocr_enabled: bool = True
    extraction_ocr_config_path: Path = (
        Path(__file__).resolve().parents[3] / "config" / "extraction_ocr.v1.json"
    )
    extraction_tesseract_cmd: str = "tesseract"
    extraction_tessdata_path: Path | None = None
    eureka_notification_enabled: bool = False
    eureka_notification_mode: Literal["disabled", "file", "resend"] = "disabled"
    eureka_notification_recipients: str = ""
    eureka_notification_base_url: str = "http://127.0.0.1:5173"
    eureka_notification_capture_path: Path = (
        Path(__file__).resolve().parents[3] / ".local" / "notifications"
    )
    eureka_notification_max_retries: NonNegativeInt = 3
    eureka_notification_retry_seconds: PositiveInt = 60
    eureka_notification_timeout_seconds: PositiveFloat = 15
    eureka_notification_processing_lease_seconds: PositiveInt = 300
    eureka_notification_idempotency_margin_seconds: NonNegativeInt = 60
    eureka_notification_max_messages: PositiveInt = 100
    eureka_notification_digest_max_alerts: PositiveInt = 100
    resend_api_key: SecretStr = SecretStr("")
    resend_from_email: str = ""
    app_env: AppEnvironment = AppEnvironment.LOCAL
    log_level: LogLevel = LogLevel.INFO

    @field_validator("eureka_automation_run_times")
    @classmethod
    def _automation_times(cls, value: str) -> str:
        times = [t.strip() for t in value.split(",") if t.strip()]
        if any(not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t) for t in times):
            raise ValueError("Usa horas HH:MM separadas por coma.")
        return ",".join(sorted(set(times)))

    @field_validator("eureka_automation_timezone")
    @classmethod
    def _automation_timezone(cls, value: str) -> str:
        ZoneInfo(value)
        return value

    @field_validator("eureka_automation_task_name")
    @classmethod
    def _automation_task_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value):
            raise ValueError("Nombre de tarea inválido.")
        return value

    @field_validator(
        "local_storage_path",
        "eureka_radar_config_path",
        "eureka_metadata_alert_exclusions_path",
        "extraction_ocr_config_path",
        "eureka_notification_capture_path",
        "eureka_automation_log_path",
    )
    @classmethod
    def _resolve_storage_path(cls, value: Path) -> Path:
        if not value.is_absolute():
            value = Path(__file__).resolve().parents[3] / value
        return value.resolve()

    @field_validator("extraction_tessdata_path", mode="before")
    @classmethod
    def _optional_tessdata(cls, value: Any) -> Any:
        return None if value == "" else value

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
