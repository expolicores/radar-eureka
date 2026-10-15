import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

CONSOLIDATION_VERSION = "canonical-v1"
REQUIRED_TYPES = (
    "PRODUCT",
    "PRESENTATION",
    "PURCHASE_ITEM",
    "QUANTITY",
    "UNIT_PRICE_COP",
    "TOTAL_COP",
    "BUDGET_COP",
    "UNSPSC",
    "EXECUTION_TERM",
    "DELIVERY_LOCATION",
    "PAYMENT_METHOD",
    "PAYMENT_TERM",
    "GUARANTEE_REQUIRED",
    "RUP_REQUIRED",
    "DELIVERY_COUNT",
    "EXPERIENCE_REQUIRED",
)


@dataclass(frozen=True)
class CanonicalFact:
    id: uuid.UUID
    process_id: uuid.UUID
    canonical_type: str
    canonical_key: str
    canonical_value: dict[str, Any]
    confidence: Decimal
    status: str
    rule_version: str
    input_digest: str
    evidence_ids: tuple[uuid.UUID, ...]


@dataclass(frozen=True)
class CanonicalSummary:
    facts: tuple[CanonicalFact, ...]
    input_count: int
    missing_types: tuple[str, ...]
    inserted: int = 0
    persisted: bool = False

    @property
    def conflicts(self) -> tuple[CanonicalFact, ...]:
        return tuple(fact for fact in self.facts if fact.status == "conflict")

    @property
    def missing_fields(self) -> tuple[str, ...]:
        absent = list(self.missing_types)
        for fact in self.facts:
            if fact.canonical_type == "PURCHASE_ITEM":
                value = fact.canonical_value["value"]
                absent.extend(
                    f"PURCHASE_ITEM:{fact.canonical_key}:{field}"
                    for field in (
                        "description",
                        "quantity",
                        "unit",
                        "unit_price_cop",
                        "total_cop",
                    )
                    if field not in value
                )
        return tuple(absent)


@dataclass(frozen=True)
class CanonicalReadState:
    status: str
    summary: CanonicalSummary
