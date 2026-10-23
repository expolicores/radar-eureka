"""Decisiones auditables de Radar v1. El score es explicativo, nunca un gate."""

from dataclasses import dataclass
from datetime import date
from typing import Any

from ..radar_config import RadarConfig
from .affinity import match_catalog, normalize, phrase_match
from .details import EurekaOpportunityDetails


@dataclass(frozen=True)
class RadarProcess:
    dataset_id: str
    secop_id: str
    portfolio_id: str | None
    published_on: date | None
    department: str | None
    municipality: str | None
    entity: str | None
    title: str | None
    description: str | None
    phase: str | None
    status: str | None
    unspsc: str | None
    budget: int | None
    offer_deadline: date | None = None
    offer_deadline_raw: Any = None

    @property
    def text(self) -> str:
        return " ".join(value for value in (self.title, self.description) if value)


@dataclass(frozen=True)
class CandidateDecision:
    accepted: bool
    code: str
    matches: list[dict[str, Any]]
    review_notes: list[str]


def candidate_decision(
    process: RadarProcess, start: date, before: date, regions: tuple[str, ...], config: RadarConfig
) -> CandidateDecision:
    if process.published_on is None:
        return CandidateDecision(False, "publication_unknown", [], [])
    if not start <= process.published_on < before:
        return CandidateDecision(False, "outside_window", [], [])
    if normalize(process.department or "", config) not in {
        normalize(region, config) for region in regions
    }:
        return CandidateDecision(False, "outside_region", [], [])
    if process.offer_deadline is None:
        return CandidateDecision(False, "missing_or_invalid_offer_deadline", [], [])
    if any(phrase_match(process.text, term, config) for term in config.strong_exclusions):
        return CandidateDecision(False, "strong_exclusion", [], [])
    matches = [
        match.json()
        for match in match_catalog(
            process.text, process.unspsc or "", config, include_discovery_only=True
        )
    ]
    matches.extend(
        {
            "category": "broad_need",
            "label": "Necesidad de bienes por confirmar",
            "concept": term,
            "matched": term,
            "origin": "metadata",
            "method": "broad_term/normalization",
        }
        for term in config.candidate_terms
        if phrase_match(process.text, term, config)
    )
    notes = [
        "Vigencia por confirmar: fecha de recepción válida; no se verifica vencimiento ni apertura."
    ]
    if not any(
        phrase_match(process.phase or "", phase, config) for phase in config.preferred_phases
    ):
        notes.append("Fase no preferida o desconocida: requiere revisión.")
    return CandidateDecision(
        bool(matches), "candidate" if matches else "no_metadata_match", matches, notes
    )


@dataclass(frozen=True)
class AlertDecision:
    create: bool
    confirmed: bool
    priority: str
    review_required: bool
    reasons: list[dict[str, Any]]
    snapshot: dict[str, Any]


def evaluate_alert(
    process: RadarProcess,
    candidate: CandidateDecision,
    details: EurekaOpportunityDetails,
    config: RadarConfig,
    preferred_budget_max: int,
) -> AlertDecision:
    reasons: list[dict[str, Any]] = [
        {"code": "region_match", "value": process.department, "origin": "metadata"},
        {"code": "new_process", "value": True, "origin": "radar_state"},
    ]
    reasons.extend({"code": "candidate_match", **match} for match in candidate.matches)
    commercial = details.commercial
    confirmed_matches: list[dict[str, Any]] = []
    products: list[dict[str, Any]] = []
    for key in ("products", "purchase_items"):
        for fact in commercial.get(key, []):
            if fact.get("status") != "confirmed" or not isinstance(fact.get("value"), dict):
                continue
            value = fact["value"]
            text = str(value.get("name" if key == "products" else "description", ""))
            matches = match_catalog(text, "", config, "canonical_fact", fact["canonical_fact_id"])
            # The canonical fact must retain actual document evidence, not merely a label.
            refs = [
                ref
                for ref in details.evidence.get("commercial." + key, [])
                if ref.get("canonical_fact_id") == fact["canonical_fact_id"]
                and ref.get("structured_fact_ids")
            ]
            if matches and refs:
                confirmed_matches.extend(
                    {
                        "code": "confirmed_commercial_match",
                        **match.json(),
                        "structured_fact_ids": refs[0]["structured_fact_ids"],
                        "confidence": fact.get("confidence"),
                    }
                    for match in matches
                )
                if key == "products":
                    products.append(value)
    reasons.extend(confirmed_matches)
    for fact in commercial.get("unspsc", []):
        if fact.get("status") == "confirmed" and isinstance(fact.get("value"), dict):
            reasons.extend(
                {"code": "unspsc_match", **match.json()}
                for match in match_catalog(
                    "",
                    str(fact["value"].get("code", "")),
                    config,
                    "canonical_fact",
                    fact["canonical_fact_id"],
                )
            )
    profile = details.commercial_profile
    budget = profile.get("budget_cop")
    if commercial.get("budget_cop") is None:
        budget = process.budget
    review = details.review_required or bool(candidate.review_notes)
    for note in candidate.review_notes:
        reasons.append({"code": "review", "value": note})
    reasons.append(
        {
            "code": "budget",
            "value": budget,
            "preferred_max": preferred_budget_max,
            "origin": "canonical_fact" if commercial.get("budget_cop") else "metadata",
        }
    )
    over_budget = budget is not None and int(budget) > preferred_budget_max
    if budget is None or over_budget:
        review = True
        reasons.append(
            {"code": "budget_review", "value": "above_preferred" if over_budget else "unknown"}
        )
    for field in (
        "execution_days",
        "payment_days",
        "guarantee_required",
        "rup_required",
        "experience_required",
    ):
        reasons.append(
            {"code": field, "value": profile.get(field, "unknown"), "origin": "canonical_fact"}
        )
    for field, limit in (
        ("execution_days", config.manageable_execution_days),
        ("payment_days", config.manageable_payment_days),
    ):
        value = profile.get(field)
        if value is not None and int(value) > limit:
            review = True
            reasons.append({"code": "conditions_review", "field": field, "value": value})
    if (
        profile.get("guarantee_required") != "not_required"
        or profile.get("rup_required") != "not_required"
        or profile.get("experience_required") != "not_required"
    ):
        review = True
    text = (
        process.text
        + " "
        + " ".join(
            str(fact.get("value", ""))
            for fact in commercial.get("purchase_items", [])
            if fact.get("status") == "confirmed"
        )
    )
    blocked = any(phrase_match(text, term, config) for term in config.strong_exclusions)
    for term in config.review_terms:
        if phrase_match(text, term, config):
            review = True
            reasons.append({"code": "participation_review", "value": term})
    if blocked:
        reasons.append({"code": "strong_exclusion", "value": True})
    reasons.append(
        {
            "code": "score_reference",
            "value": details.score,
            "threshold": config.alert_score_threshold,
            "mandatory_gate": False,
        }
    )
    categories = list(dict.fromkeys(match["category"] for match in confirmed_matches))
    priority = details.priority or "medium"
    if over_budget:
        priority = {"high": "medium", "medium": "low", "low": "low"}.get(priority, "medium")
    snapshot = {
        "secop_id": process.secop_id,
        "title": process.title,
        "entity": process.entity,
        "department": process.department,
        "municipality": process.municipality,
        "budget": budget,
        "category": categories,
        "products": products,
        "score": details.score,
        "scoring_rule_version": details.scoring_rule_version,
        "execution_days": profile.get("execution_days"),
        "payment_days": profile.get("payment_days"),
        "guarantee_required": profile.get("guarantee_required", "unknown"),
        "candidate_matches": candidate.matches,
        "confirmed_matches": confirmed_matches,
    }
    confirmed = bool(confirmed_matches)
    unavailable = details.quality.get("document_status") == "unavailable"
    commercial_metadata_matches = [
        match for match in candidate.matches if not match.get("discovery_only")
    ]
    provisional = unavailable and not confirmed and bool(commercial_metadata_matches)
    snapshot["evidence_level"] = (
        "metadata_only" if unavailable and not confirmed else "document_confirmed"
    )
    snapshot["document_status"] = "unavailable" if unavailable else "available"
    if provisional:
        snapshot["category"] = list(
            dict.fromkeys(match["category"] for match in commercial_metadata_matches)
        )
    if unavailable and not confirmed and not commercial_metadata_matches:
        reasons.append({"code": "discovery_only_requires_commercial_evidence", "value": True})
    if unavailable:
        reasons.append(
            {
                "code": "documents_unavailable",
                "origin": "metadata",
                "value": "Inventario documental vacío; revisión manual y reintento pendientes.",
            }
        )
    return AlertDecision(
        candidate.accepted and (confirmed or provisional) and not blocked,
        confirmed,
        priority,
        review or unavailable,
        reasons,
        snapshot,
    )
