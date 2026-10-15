import re
import unicodedata
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


class SearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    q: str = Field(default="", max_length=200)
    product: str = Field(default="", max_length=200)
    brand: str = Field(default="", max_length=200)
    unspsc: str = Field(default="", pattern=r"^(\d{8})?$")
    entity: str = Field(default="", max_length=200)
    department: str = Field(default="", max_length=128)
    municipality: str = Field(default="", max_length=128)
    category: str = Field(default="", max_length=128)
    priority: str = Field(default="", pattern=r"^(high|medium|low)?$")
    budget_min: int | None = Field(default=None, ge=0, le=10**18)
    budget_max: int | None = Field(default=None, ge=0, le=10**18)
    published_from: date | None = None
    published_to: date | None = None
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def ordered_ranges(self) -> "SearchQuery":
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_min > self.budget_max
        ):
            raise ValueError("Presupuesto mínimo superior al máximo.")
        if self.published_from and self.published_to and self.published_from > self.published_to:
            raise ValueError("Fecha inicial posterior a la final.")
        for field in ("q", "product", "brand"):
            if getattr(self, field).strip() and not normalize(getattr(self, field)):
                raise ValueError("La búsqueda debe contener letras o números.")
        return self


def variants(value: str, aliases: dict[str, list[str]]) -> list[str]:
    normalized = normalize(value)
    result = [normalized]
    for name, forms in aliases.items():
        family = [normalize(name), *(normalize(form) for form in forms)]
        if normalized in family:
            result.extend(family)
    return list(dict.fromkeys(v for v in result if v))


def tsquery(values: list[str]) -> str:
    # Only normalized alphanumeric tokens reach this grammar, never user operators.
    return " | ".join(
        "(" + " & ".join(token + ":*" for token in value.split()) + ")" for value in values
    )


def modality(text: str, value: str, aliases: dict[str, list[str]]) -> str | None:
    normalized = normalize(text)
    options = variants(value, aliases)
    if not options:
        return None
    if normalized == options[0]:
        return "exact_normalized"
    if normalized in options[1:]:
        return "explicit_alias"
    if f" {options[0]} " in f" {normalized} ":
        return "phrase"
    for option in options[1:]:
        if f" {option} " in f" {normalized} ":
            return "explicit_alias"
    words = normalized.split()
    for index, option in enumerate(options):
        if all(token in words for token in option.split()):
            return "full_text" if index == 0 else "explicit_alias"
    if any(
        all(any(word.startswith(token) for word in words) for token in option.split())
        for option in options
    ):
        return "token_prefix"
    return None


def searchable_value(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(searchable_value(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(searchable_value(v) for v in value)
    return str(value) if value is not None else ""


def rank(origin: str, mode: str, kind: str) -> int:
    if mode == "token_prefix":
        return 1
    if (
        origin == "canonical_match"
        and kind in ("PRODUCT", "PURCHASE_ITEM")
        and mode == "exact_normalized"
    ):
        return 5
    if mode == "explicit_alias" or origin in ("canonical_match", "structured_match"):
        return 4
    if origin == "metadata_match" and mode == "exact_normalized":
        return 3
    return 1 if mode == "token_prefix" else 2
