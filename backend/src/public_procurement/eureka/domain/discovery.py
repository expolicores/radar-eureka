"""Scoring comercial heurístico y explicable. Nunca determina elegibilidad contractual."""

import re
import uuid
from dataclasses import dataclass
from enum import StrEnum

from public_procurement.shared.text import normalize_text

from ..config import DiscoveryConfig


class OpportunityState(StrEnum):
    CANDIDATE = "candidate"
    REVIEW = "review"
    EXCLUDED = "excluded"
    CLOSED = "closed"
    NO_MATCH = "no_match"


class PriorityBand(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ProcessFacts:
    process_id: uuid.UUID
    secop_id: str
    title: str | None
    description: str | None
    entity_name: str | None
    department: str | None
    base_price_cop: int | None
    category_code: str | None
    status: str | None
    phase: str | None


@dataclass(frozen=True)
class Reason:
    code: str
    label: str
    points: int
    signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class OpportunityEvaluation:
    process_id: uuid.UUID
    secop_id: str
    score: int
    priority_band: PriorityBand
    active: bool
    state: OpportunityState
    matched_categories: tuple[str, ...]
    matched_unspsc: tuple[str, ...]
    matched_terms: tuple[str, ...]
    matched_context: tuple[str, ...]
    reasons: tuple[Reason, ...]
    penalties: tuple[Reason, ...]
    review_notes: tuple[str, ...]
    rule_version: str


def _canonical(text: str) -> str:
    return " ".join(re.findall(r"\w+", normalize_text(text)))


def _matches(text: str, terms: tuple[str, ...], ignore_negated: bool = False) -> tuple[str, ...]:
    normalized = _canonical(text)
    found: dict[str, str] = {}
    for term in terms:
        needle = _canonical(term)
        if not needle:
            continue
        for match in re.finditer(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", normalized):
            prefix = normalized[max(0, match.start() - 45) : match.start()]
            if ignore_negated and re.search(
                r"(?:no(?: se)?(?: (?:requiere|exige|incluye))?|sin)\s+$", prefix
            ):
                continue
            found.setdefault(needle, term)
            break
    return tuple(found.values())


def evaluate_process(facts: ProcessFacts, config: DiscoveryConfig) -> OpportunityEvaluation:
    text = " ".join(value for value in (facts.title, facts.description) if value)
    terminal = _matches(
        " ".join(v for v in (facts.status, facts.phase) if v),
        config.terminal_terms,
        ignore_negated=True,
    )
    codes = set(re.findall(r"(?<!\d)\d{8}(?!\d)", facts.category_code or ""))
    categories: list[str] = []
    priority_codes: set[str] = set()
    candidate_codes: set[str] = set()
    product_terms: list[str] = []
    notes: list[str] = []
    for category in config.catalog:
        priority = codes.intersection(category.priority_unspsc)
        candidate = codes.intersection(category.candidate_unspsc)
        terms = _matches(text, category.product_terms)
        if priority or candidate or terms:
            categories.append(category.code)
            priority_codes.update(priority)
            candidate_codes.update(candidate)
            product_terms.extend(terms)
            if category.conditional:
                notes.append(
                    "Refrigerios preparados: confirmar preparación, inocuidad "
                    "y capacidad de entrega."
                )
    products = tuple(dict.fromkeys(product_terms))
    broad = _matches(text, config.broad_terms)
    needs = _matches(text, config.need_terms)
    entities = _matches(facts.entity_name or "", config.entity_terms)
    interest = bool(products or priority_codes or candidate_codes or broad or needs or entities)
    reasons: list[Reason] = []
    penalties: list[Reason] = []
    weights, profile = config.weights, config.execution
    if products:
        reasons.append(Reason("product", "Producto específico", weights.product, products))
    if priority_codes:
        reasons.append(
            Reason(
                "priority_unspsc",
                "UNSPSC prioritario",
                weights.priority_unspsc,
                tuple(sorted(priority_codes)),
            )
        )
    elif candidate_codes:
        reasons.append(
            Reason(
                "candidate_unspsc",
                "UNSPSC candidato de expansión",
                weights.candidate_unspsc,
                tuple(sorted(candidate_codes)),
            )
        )
    if broad or needs:
        reasons.append(
            Reason(
                "broad_need", "Objeto o necesidad institucional", weights.broad_need, broad + needs
            )
        )
    if entities:
        reasons.append(Reason("entity", "Contexto de entidad relevante", weights.entity, entities))
    if interest:
        amount = facts.base_price_cop
        if (
            amount is not None
            and profile.attractive_min_cop <= amount <= profile.attractive_max_cop
        ):
            reasons.append(
                Reason("attractive_amount", "Cuantía en zona atractiva", weights.attractive_amount)
            )
        if amount is not None and amount >= profile.high_amount_from_cop:
            penalties.append(
                Reason(
                    "high_amount",
                    "Cuantía alta: revisar financiación y condiciones",
                    profile.high_amount_penalty,
                )
            )
        simple = _matches(text, profile.simple_logistics, ignore_negated=True)
        if simple:
            reasons.append(
                Reason(
                    "simple_logistics",
                    "Indicio de logística simple",
                    weights.simple_logistics,
                    simple,
                )
            )
        for barrier in profile.barriers:
            matches = _matches(text, barrier.terms, ignore_negated=True)
            if matches:
                penalties.append(Reason(barrier.code, barrier.label, barrier.points, matches))
        geography = _canonical(facts.department or "")
        if geography and geography not in {_canonical(d) for d in config.departments}:
            penalties.append(
                Reason(
                    "outside_geography",
                    "Fuera de la geografía inicial; revisar logística",
                    profile.outside_geography_penalty,
                    (facts.department or "",),
                )
            )
        # La metadata actual no contiene fecha de cierre: nunca inventar vigencia por antigüedad.
        if not terminal:
            notes.append(
                "Vigencia por confirmar: no hay fecha de cierre de ofertas "
                "en la metadata persistida."
            )
    exclusions = []
    for exclusion in config.exclusions:
        matches = _matches(text, exclusion.terms, ignore_negated=True)
        if matches:
            clear_goods = bool(products or broad)
            dominant_service = any(
                _canonical(text).startswith(_canonical(term)) for term in exclusion.terms
            )
            if clear_goods and not dominant_service:
                penalties.append(
                    Reason(
                        "mixed_" + exclusion.code,
                        "Alcance mixto: " + exclusion.label,
                        exclusion.points,
                        matches,
                    )
                )
            else:
                exclusions.append(exclusion.label)
    score = max(0, sum(r.points for r in reasons) - sum(p.points for p in penalties))
    band = (
        PriorityBand.HIGH
        if score >= config.high_priority_from
        else PriorityBand.MEDIUM
        if score >= config.medium_priority_from
        else PriorityBand.LOW
    )
    if terminal:
        state = OpportunityState.CLOSED
        notes.append("Estado o fase terminal: " + ", ".join(terminal))
    elif exclusions:
        state = OpportunityState.EXCLUDED
        notes.extend(exclusions)
    elif not interest:
        state = OpportunityState.NO_MATCH
    elif penalties or notes:
        state = OpportunityState.REVIEW
    else:
        state = OpportunityState.CANDIDATE
    return OpportunityEvaluation(
        facts.process_id,
        facts.secop_id,
        score,
        band,
        state in (OpportunityState.CANDIDATE, OpportunityState.REVIEW),
        state,
        tuple(categories),
        tuple(sorted(priority_codes | candidate_codes)),
        products + broad + needs,
        entities + ((facts.department,) if facts.department else ()),
        tuple(reasons),
        tuple(penalties),
        tuple(notes),
        config.version,
    )
