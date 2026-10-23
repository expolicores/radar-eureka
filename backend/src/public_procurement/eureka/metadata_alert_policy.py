"""Object exclusions only at Socrata's provisional metadata alert boundary."""

import json
import unicodedata
from dataclasses import replace
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr, field_validator

from .domain.radar import AlertDecision

DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[3] / "config/eureka_metadata_alert_exclusions.v1.json"
)


def normalize_object(value: str) -> str:
    text = "".join(
        c for c in unicodedata.normalize("NFD", value.casefold()) if not unicodedata.combining(c)
    )
    return " ".join(text.split())


class MetadataAlertExclusions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal[1]
    enabled: StrictBool
    terms: list[StrictStr]

    @field_validator("version", mode="before")
    @classmethod
    def integer_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("La versión debe ser el entero 1")
        return value

    @field_validator("terms")
    @classmethod
    def nonempty_terms(cls, values: list[str]) -> list[str]:
        if any(not normalize_object(value) for value in values):
            raise ValueError("Los términos no pueden estar vacíos")
        return values

    def match(self, object_text: str) -> str | None:
        if not self.enabled:
            return None
        text = normalize_object(object_text)
        # Most specific substring first; configured order breaks ties, with no fuzzy matching.
        terms = sorted(enumerate(self.terms), key=lambda t: (-len(normalize_object(t[1])), t[0]))
        return next(
            (normalize_object(term) for _, term in terms if normalize_object(term) in text), None
        )


def load_metadata_alert_exclusions(path: Path) -> MetadataAlertExclusions:
    return MetadataAlertExclusions.model_validate(json.loads(path.read_text(encoding="utf-8")))


def provisional_metadata_candidate(decision: AlertDecision, source: str) -> bool:
    return (
        source == "socrata"
        and decision.create
        and not decision.confirmed
        and decision.snapshot.get("evidence_level") == "metadata_only"
        and decision.snapshot.get("document_status") == "unavailable"
    )


def apply_metadata_alert_exclusions(
    decision: AlertDecision,
    *,
    source: str,
    object_text: str,
    policy: MetadataAlertExclusions | None,
) -> AlertDecision:
    if not provisional_metadata_candidate(decision, source):
        return decision
    term = policy.match(object_text) if policy is not None else None
    if policy is not None and term is None:
        return decision
    code = "metadata_object_exclusion" if term else "metadata_exclusion_policy_invalid"
    reason = {
        "code": code,
        "object": object_text,
        "matched_term": term,
        "policy_version": policy.version if policy else None,
    }
    snapshot = {
        **decision.snapshot,
        "metadata_exclusion_reason": code,
        "metadata_exclusion_object": object_text,
        "metadata_exclusion_policy_version": policy.version if policy else None,
    }
    if term:
        snapshot["metadata_exclusion_term"] = term
    return replace(decision, create=False, reasons=[*decision.reasons, reason], snapshot=snapshot)
