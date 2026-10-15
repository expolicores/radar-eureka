"""Política local versionada; rutas operativas separadas de los umbrales."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OcrPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = "ocr-v1"
    min_alphanumeric_chars: int = Field(default=40, ge=1)
    min_alphanumeric_ratio: float = Field(default=0.5, ge=0, le=1)
    max_damaged_ratio: float = Field(default=0.05, ge=0, le=1)
    language: str = Field(default="spa", pattern=r"^[a-zA-Z0-9_]+$")
    fallback_language: str = Field(default="eng", pattern=r"^[a-zA-Z0-9_]+$")
    max_ocr_pages: int = Field(default=20, ge=1)
    dpi: int = Field(default=300, ge=72, le=600)
    max_pixels: int = Field(default=12_000_000, ge=1)
    page_timeout_seconds: float = Field(default=30, gt=0)
    document_timeout_seconds: float = Field(default=180, gt=0)
    memory_bytes: int = Field(default=512 * 1024 * 1024, ge=64 * 1024 * 1024)
    max_retry_attempts: int = Field(default=3, ge=0, le=20)
    preprocessing: Literal["grayscale-autocontrast-v1"] = "grayscale-autocontrast-v1"

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


def load_ocr_policy(path: Path) -> OcrPolicy:
    return OcrPolicy.model_validate(json.loads(path.read_text(encoding="utf-8")))
