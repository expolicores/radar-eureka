"""Operational review fit only. Does not change the discovery catalog, score or alerts."""

import json
import re
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .domain.affinity import normalize
from .radar_config import RadarConfig


class ReviewFitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: int
    max_amount_cop: int = Field(gt=0)
    goods_actions: tuple[str, ...]
    nominal_goods_prefixes: tuple[str, ...]
    physical_fulfillment: tuple[str, ...]
    professional_services: tuple[str, ...]


@lru_cache(maxsize=1)
def load_review_fit_config() -> ReviewFitConfig:
    path = Path(__file__).resolve().parents[3] / "config/eureka_review_admission.v1.json"
    return ReviewFitConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))


def review_fit(item: dict[str, Any], catalog: RadarConfig) -> str | None:
    """A keyword, score or extraction warning cannot substitute for a fitting procurement object."""
    policy = load_review_fit_config()
    metadata = item.get("metadata") or {}
    snapshot = (item.get("decision") or {}).get("snapshot") or {}
    amount = metadata.get("amount")
    if amount is None:
        amount = snapshot.get("budget")
    if amount is not None:
        try:
            parsed = Decimal(str(amount))
            if parsed.is_finite() and parsed > policy.max_amount_cop:
                return "review_rejected_budget_limit"
        except InvalidOperation:
            pass  # Unknown amount remains explicit; no invented value.
    text = normalize(str(metadata.get("object") or item.get("title") or ""), catalog)

    def position(phrase: str) -> int | None:
        match = re.search(r"(?<!\w)" + re.escape(normalize(phrase, catalog)) + r"(?!\w)", text)
        return match.start() if match else None

    actions = [p for word in policy.goods_actions if (p := position(word)) is not None]
    first_goods = min(actions, default=len(text) + 1)
    if any(
        (p := position(phrase)) is not None and p < first_goods
        for phrase in policy.professional_services
    ):
        return "review_rejected_irrelevant_service"
    goods = bool(actions) or any(
        re.match(re.escape(normalize(prefix, catalog)) + r"(?!\w)", text)
        for prefix in policy.nominal_goods_prefixes
    )
    physical_service = any(position(phrase) is not None for phrase in policy.physical_fulfillment)
    confirmed_goods = any(
        isinstance(match, dict) and match.get("canonical_fact_id")
        for match in snapshot.get("confirmed_matches") or []
    )
    if not (goods or physical_service or confirmed_goods):
        return "review_rejected_no_goods_intent"
    return None
