"""Configuración validada de Radar, independiente del scoring de discovery."""

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CommercialFamily(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    category: str
    label: str
    terms: tuple[str, ...] = ()
    phrases: tuple[str, ...] = ()
    brands: tuple[str, ...] = ()
    aliases: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    unspsc: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    priority: int = Field(default=1, ge=1)


class RadarConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: str = Field(min_length=1, max_length=64)
    families: tuple[CommercialFamily, ...]
    terminal_terms: tuple[str, ...]
    preferred_phases: tuple[str, ...]
    strong_exclusions: tuple[str, ...]
    review_terms: tuple[str, ...]
    token_aliases: dict[str, str]
    candidate_terms: tuple[str, ...] = ()
    alert_score_threshold: int = Field(default=60, ge=0)
    max_attempts: int = Field(default=3, ge=1, le=10)
    page_size: int = Field(default=200, ge=1, le=1000)
    max_pages: int = Field(default=100, ge=1, le=1000)
    manageable_execution_days: int = Field(default=30, ge=1)
    manageable_payment_days: int = Field(default=60, ge=1)

    @model_validator(mode="after")
    def unique_families(self) -> "RadarConfig":
        if not self.families or len({item.category for item in self.families}) != len(
            self.families
        ):
            raise ValueError("El catálogo necesita familias únicas.")
        return self

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


def load_radar_config(path: Path) -> RadarConfig:
    return RadarConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))
