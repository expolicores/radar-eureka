"""Manual research run contracts; dates are inclusive Bogotá calendar days."""

import re
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal, Self
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_RESEARCH_DAYS = 60  # Existing controlled discovery bound, not a new UI restriction.
TERMINAL = {"completed", "completed_with_warnings", "failed"}


class ResearchRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> object:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Usa fechas calendario con formato YYYY-MM-DD.")
        return value

    @model_validator(mode="after")
    def window(self) -> Self:
        if self.start_date > self.end_date:
            raise ValueError("La fecha inicial debe ser anterior o igual a la fecha final.")
        if (self.end_date - self.start_date).days + 1 > MAX_RESEARCH_DAYS:
            raise ValueError(
                f"El flujo actual admite como máximo {MAX_RESEARCH_DAYS} días inclusivos."
            )
        if self.end_date == date.max:
            raise ValueError("La fecha final no permite construir el límite exclusivo.")
        return self

    def utc_bounds(self) -> tuple[datetime, datetime]:
        bogota = ZoneInfo("America/Bogota")
        return (
            datetime.combine(self.start_date, time.min, bogota).astimezone(UTC),
            datetime.combine(self.end_date + timedelta(days=1), time.min, bogota).astimezone(UTC),
        )


class ResearchRun(BaseModel):
    run_id: UUID
    run_type: Literal["state_vs_state", "state_vs_private_market"] = "state_vs_state"
    status: Literal["queued", "running", "completed", "completed_with_warnings", "failed"]
    start_date: date
    end_date: date
    window_start_at: datetime
    window_before_at: datetime
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stage: str = "queued"
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    result_url: str | None = None
