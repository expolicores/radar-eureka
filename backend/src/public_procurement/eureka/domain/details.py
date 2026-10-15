"""Vista de lectura documental; no altera score ni determina conveniencia de participar."""

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class StoredOpportunity:
    id: uuid.UUID
    process_id: uuid.UUID
    score: int
    priority: str
    categories: tuple[str, ...]
    review_required: bool
    rule_version: str
    review_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalEntry:
    id: uuid.UUID
    canonical_type: str
    value: Any
    confidence: Decimal
    status: str
    corroborated: bool
    evidence_ids: tuple[uuid.UUID, ...]
    candidates: Any
    field_sources: dict[str, Any]
    field_confidence: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalInput:
    status: str
    facts: tuple[CanonicalEntry, ...]
    missing_fields: tuple[str, ...]
    structured_fact_count: int
    extraction_coverage: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EurekaOpportunityDetails:
    process_id: uuid.UUID
    secop_id: str
    opportunity_id: uuid.UUID | None
    category: tuple[str, ...]
    score: int | None
    priority: str | None
    scoring_rule_version: str | None
    review_required: bool
    enrichment_status: str
    commercial: dict[str, Any]
    execution: dict[str, Any]
    payment: dict[str, Any]
    requirements: dict[str, Any]
    quality: dict[str, Any]
    commercial_profile: dict[str, Any]
    evidence: dict[str, Any]
