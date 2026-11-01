"""Review admission only; never changes discovery, matching rules, scoring or alerts."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from .domain.affinity import match_catalog, phrase_match
from .radar_config import RadarConfig, load_radar_config
from .review_fit import review_fit

POLICY_VERSION = 3
DOCUMENT_REASONS = {
    "suspicious_fact",
    "suspicious_facts",
    "ocr_truncated",
    "partial_document_coverage",
    "partial_coverage",
    "missing_documents",
    "metadata_only",
    "extraction_failed",
    "unsupported_format",
    "document_download_failed",
}


@lru_cache(maxsize=1)
def default_config() -> RadarConfig:
    return load_radar_config(Path(__file__).resolve().parents[3] / "config/eureka_radar.v1.json")


def historical_config(snapshot: dict[str, Any] | None) -> RadarConfig:
    if snapshot and "families" in snapshot:
        return RadarConfig.model_validate(
            {k: v for k, v in snapshot.items() if k in RadarConfig.model_fields}
        )
    return default_config()


def human_intervention(rating: dict[str, Any]) -> bool:
    return bool(
        rating.get("manual_rating")
        or rating.get("manual_note")
        or rating.get("reviewed_at")
        or rating.get("reviewed_by")
    )


@lru_cache(maxsize=8192)
def _metadata_evidence(text: str, unspsc: str, config_json: str) -> tuple[bool, bool, bool]:
    """Cache pure matching by exact input and full config, without changing matching behavior."""
    config = RadarConfig.model_validate_json(config_json)
    strong = any(phrase_match(text, term, config) for term in config.strong_exclusions)
    catalog = bool(match_catalog(text, unspsc, config, include_discovery_only=True))
    broad = any(phrase_match(text, term, config) for term in config.candidate_terms)
    return strong, catalog, broad


def documentary_reasons(item: dict[str, Any]) -> list[str]:
    review = item.get("document_review") or {}
    snapshot = (item.get("decision") or {}).get("snapshot") or {}
    reasons = set(item.get("manual_review_reasons") or review.get("manual_review_reasons") or [])
    reasons.update(k for k in DOCUMENT_REASONS if review.get(k) or snapshot.get(k))
    reasons.update(snapshot.get("manual_review_reasons") or [])
    if item.get("coverage_incomplete"):
        reasons.add("partial_document_coverage")
    if item.get("document_status") == "unavailable":
        reasons.add("missing_documents")
    if item.get("error") and item.get("stage") in {
        "documents_sync",
        "documents_download",
        "extraction",
        "extraction_partial",
    }:
        reasons.add(
            "document_download_failed"
            if item["stage"] == "documents_download"
            else "extraction_failed"
        )
    return sorted(reasons & DOCUMENT_REASONS)


def admission(item: dict[str, Any], config: RadarConfig | None = None) -> dict[str, Any]:
    """Require commercial evidence; basic metadata, amount and unknown date are insufficient."""
    config = config or default_config()
    metadata = item.get("metadata") or {}
    decision = item.get("decision") or {}
    snapshot = decision.get("snapshot") or {}
    text = " ".join(
        str(v)
        for v in [metadata.get("object"), item.get("title"), metadata.get("description")]
        if v
    )
    signals: list[str] = []
    score = snapshot.get("score")
    if isinstance(score, (int, float)) and not isinstance(score, bool) and score > 0:
        signals.append("positive_preliminary_score")
    if snapshot.get("confirmed_matches"):
        signals.append("confirmed_commercial_facts")
    facts = (item.get("document_review") or {}).get("facts") or []
    if any(
        isinstance(f, dict)
        and f.get("fact_type")
        in {"product", "products", "purchase_item", "purchase_items", "unspsc", "item"}
        for f in facts
    ):
        signals.append("commercial_document_facts")
    independent = bool(signals)
    reason = item.get("reason")
    # A commercial exclusion needs independent additional evidence, not its own metadata trigger.
    metadata_strong, metadata_match, metadata_broad = _metadata_evidence(
        text, str(metadata.get("unspsc") or ""), config.model_dump_json()
    )
    strong = reason == "strong_exclusion" or metadata_strong
    if not strong:
        matches = item.get("candidate_matches") or snapshot.get("candidate_matches") or []
        if matches:
            signals.append("persisted_commercial_match")
        if metadata.get("matched_searches"):
            signals.append("validated_commercial_search")
        if metadata_match:
            signals.append("metadata_catalog_match")
        if metadata_broad:
            signals.append("metadata_candidate_term")
    if strong and not independent:
        rejected = "review_rejected_strong_exclusion"
    elif not signals and reason == "missing_or_invalid_offer_deadline":
        rejected = "review_rejected_deadline_only"
    elif not signals:
        rejected = "review_rejected_no_commercial_signal"
    else:
        rejected = None
    fit_rejection = review_fit(item, config)
    if fit_rejection:
        rejected = fit_rejection
    return {
        "review_candidate": bool(signals) and rejected is None,
        "review_admission_reasons": list(dict.fromkeys(signals)),
        "review_rejected_reason": rejected,
        "review_policy_version": POLICY_VERSION,
        "review_fit_rejected_reason": fit_rejection,
    }
