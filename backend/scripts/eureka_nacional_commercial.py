"""Commercial EN-01 profile matching and category funnel metrics."""

import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from spike_licitaciones_info import ROOT, normalized

DEFAULT_PROFILE = ROOT / "config" / "eureka_nacional_commercial.v3.json"
CODE = re.compile(r"(?<![\w.])\d{8}(?![\w.])")
METHODS = ("unspsc", "keywords", "both")
SERVICE_WORD = re.compile(r"\b(?:servicios?|logistic[oa]s?)\b")
SUPPLY_WORD = re.compile(
    r"\b(?:adquisicion|adquirir|suministro|suministrar|compra|compraventa|dotacion|"
    r"entrega|entregar|venta)\b"
)


class Exclusion(BaseModel):
    id: str
    pattern: str


class Category(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    priority: Literal["A", "B"]
    segments: list[str]
    families: dict[str, str]
    classes: dict[str, str]
    products: dict[str, str]
    context_classes: dict[str, str]
    keywords: list[str]
    synonyms: list[str]
    exclusions: list[str]
    rationale: str
    # v3: a category whose terms are generic (e.g. «apoyo logístico») only applies when the
    # object also names one of these contexts; otherwise the match is dropped explicitly.
    context_terms: list[str] = []

    @model_validator(mode="after")
    def validate_code_levels(self):
        if any(
            not re.fullmatch(r"\d{8}", code) or code[-2:] != "00" or code[4:6] == "00"
            for code in self.classes.keys() | self.context_classes.keys()
        ) or any(not re.fullmatch(r"\d{8}", code) or code[-2:] == "00" for code in self.products):
            raise ValueError("Las categorías requieren clases y productos UNSPSC válidos")
        codes = self.classes.keys() | self.products.keys() | self.context_classes.keys()
        if set(self.families) != {code[:4] + "0000" for code in codes} or set(self.segments) != {
            code[:2] for code in codes
        }:
            raise ValueError("Las familias y segmentos deben corresponder a los códigos declarados")
        if not codes and not (self.keywords or self.synonyms):
            raise ValueError("La categoría debe tener códigos o palabras clave")
        return self


class CommercialProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    geography: Literal["nacional"]
    catalog: dict[str, str]
    candidate_segments: list[str]
    preferred_modalities: list[str]
    terminal_states: list[str]
    supply_pattern: str
    service_pattern: str
    exclusions: list[Exclusion]
    excluded_products: dict[str, str]
    categories: list[Category] = Field(min_length=1)
    # v2: objects mixing a commercial category with service wording stay as reviewable
    # candidates, unless the service matches `hard_service_pattern`. v1 keeps both off.
    mixed_review: bool = False
    hard_service_pattern: str = ""
    # v3: an unrelated service with no explicit supply verb is a primary service even when
    # its wording escapes `service_pattern` (typos such as «mantenimento»).
    hard_service_without_supply: bool = False

    @model_validator(mode="after")
    def validate_rules(self):
        if not self.catalog.get("version"):
            raise ValueError("Se requiere la version del catalogo oficial")
        if len({category.id for category in self.categories}) != len(self.categories):
            raise ValueError("Los identificadores de categoría deben ser únicos")
        for pattern in (
            self.supply_pattern,
            self.service_pattern,
            self.hard_service_pattern,
            *(r.pattern for r in self.exclusions),
        ):
            re.compile(pattern)
        return self

    @property
    def fingerprint(self):
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


def load_commercial_profile(path=DEFAULT_PROFILE):
    return CommercialProfile.model_validate_json(Path(path).read_bytes())


def plain(value):
    return " ".join(re.findall(r"[a-z0-9]+", normalized(value or "")))


def parse_unspsc(value):
    """Read observed scalar/list metadata without guessing remote request encoding."""
    fields = value if isinstance(value, list) else [value]
    return sorted(
        {
            code
            for field in fields
            if isinstance(field, str | int)
            for code in CODE.findall(str(field))
        }
    )


def phrase_match(text, phrase):
    tokens = plain(phrase).split()
    if not tokens:
        return None
    parts = [re.escape(word) + (r"(?:s|es)?" if len(word) >= 4 else "") for word in tokens]
    return re.search(r"\b" + " ".join(parts) + r"\b", text)


def assess_commercial(profile, obj, description, codes):
    obj, description = plain(obj), plain(description)
    scope = obj or description
    supply = re.search(profile.supply_pattern, scope)
    service = re.search(profile.service_pattern, scope)
    matches, category_exclusions = [], []
    first_product_at = None
    for category in profile.categories:
        object_hits = {
            term: match.start()
            for term in [*category.keywords, *category.synonyms]
            if (match := phrase_match(obj, term))
        }
        object_terms = list(object_hits)
        if object_hits:
            earliest = min(object_hits.values())
            first_product_at = (
                earliest if first_product_at is None else min(first_product_at, earliest)
            )
        description_terms = [
            term
            for term in [*category.keywords, *category.synonyms]
            if phrase_match(description, term)
        ]
        terms = list(dict.fromkeys([*object_terms, *description_terms]))
        unspsc = [
            code
            for code in codes
            if code in category.products
            or code[:6] + "00" in category.classes
            or (terms and code in category.context_classes)
        ]
        if not unspsc and not terms:
            continue
        if category.context_terms and not any(
            phrase_match(obj, term) or phrase_match(description, term)
            for term in category.context_terms
        ):
            category_exclusions.append({"category": category.id, "phrase": "sin_contexto"})
            continue
        excluded = next((term for term in category.exclusions if phrase_match(obj, term)), None)
        # A documented physical item ahead of an accessory service remains in scope.
        accessory = (
            supply and service and any(pos < service.start() for pos in object_hits.values())
        )
        if excluded and not accessory:
            category_exclusions.append({"category": category.id, "phrase": excluded})
            continue
        matches.append(
            {
                "category": category.id,
                "priority": category.priority,
                "families": sorted({code[:4] + "0000" for code in unspsc}),
                "unspsc": unspsc,
                "object_terms": object_terms,
                "description_terms": description_terms,
                "method": "both" if unspsc and terms else "unspsc" if unspsc else "keywords",
            }
        )

    explicit_exclusion = next(
        (rule.id for rule in profile.exclusions if re.search(rule.pattern, scope)), None
    )
    excluded_codes = sorted(set(codes) & profile.excluded_products.keys())
    reason = explicit_exclusion
    if excluded_codes:
        reason = reason or "excluded_product_code"
    if (
        not reason
        and service
        and (
            not supply
            or service.start() <= supply.end() + 2
            or (first_product_at is not None and service.start() < first_product_at)
        )
    ):
        reason = "primary_service"
    hard = re.search(profile.hard_service_pattern, scope) if profile.hard_service_pattern else None
    if (
        not reason
        and profile.hard_service_without_supply
        and not SUPPLY_WORD.search(scope)
        and hard
        # Only when the unrelated service is the object itself, ahead of any product term.
        and (first_product_at is None or hard.start() < first_product_at)
    ):
        reason = "primary_service"
    confidence = "goods"
    if (
        reason == "primary_service"
        and profile.mixed_review
        and matches
        and not (
            hard
            # v3 only blocks an unrelated service that is the object itself (ahead of any
            # product term); v2 blocks any mention.
            and (
                not profile.hard_service_without_supply
                or first_product_at is None
                or hard.start() < first_product_at
            )
        )
    ):
        # A relevant category is present: keep it reviewable, never as a confirmed supply.
        reason, confidence = None, "mixed_review"
    elif (
        profile.mixed_review
        and not reason
        and matches
        and (not supply or SERVICE_WORD.search(scope))
    ):
        # No explicit supply, or goods plus a service component (hosting, logistics):
        # reviewable, never a confirmed supply.
        confidence = "mixed_review"
    if not reason and not matches:
        reason = "category_excluded" if category_exclusions else "outside_commercial_profile"
    if (
        not reason
        and confidence != "mixed_review"
        and not supply
        and (first_product_at is None or first_product_at > 12)
    ):
        reason = "goods_object_not_clear"

    if reason:
        primary = None
    else:
        primary = min(
            matches,
            key=lambda item: (
                item["priority"],
                ("both", "keywords", "unspsc").index(item["method"]),
            ),
        )
    return {
        "category_matches": matches,
        "primary_category": primary["category"] if primary else None,
        "commercial_priority": primary["priority"] if primary else None,
        "commercial_reason": reason or "matched_commercial_goods",
        "commercial_exclusion": reason,
        "category_exclusions": category_exclusions,
        "excluded_product_codes": excluded_codes,
        "description_available": bool(description),
        "accessory_service_signal": bool(service and not reason),
        "commercial_confidence": None if reason else confidence,
    }


def selection_rank(process):
    status = {"open": 0, "unknown": 1, "closed": 2}[process["validity_status"]]
    return (
        status,
        not process["preferred_modality"],
        process["commercial_priority"],
        process.get("commercial_confidence") == "mixed_review",
    )


def commercial_metrics(processes, results, profile):
    categories = {
        category.id: {
            "priority": category.priority,
            "discovered": 0,
            "matches_by_method": dict.fromkeys(METHODS, 0),
            "candidates": 0,
            "open_candidates": 0,
            "sampled": 0,
            "analyzed": 0,
            "resolved": 0,
            "no_experience_required": 0,
            "operational_cost": {
                "elapsed_seconds": 0.0,
                "request_credits": 0,
                "downloads": 0,
                "ocr_pages_reported": 0,
                "monetary_cost": None,
            },
        }
        for category in profile.categories
    }
    overlap = 0
    unspsc_families, commercial_families, methods = Counter(), Counter(), Counter()
    for process in processes:
        matches = process["category_matches"]
        overlap += len(matches) > 1
        for match in matches:
            group = categories[match["category"]]
            group["discovered"] += 1
            group["matches_by_method"][match["method"]] += 1
        primary = process["primary_category"]
        if primary and process["excluded_reason"] is None:
            group = categories[primary]
            group["candidates"] += 1
            group["open_candidates"] += process["validity_status"] == "open"
            group["sampled"] += process["sampled"]
            match = next(item for item in matches if item["category"] == primary)
            commercial_families[primary] += 1
            methods[match["method"]] += 1
            unspsc_families.update(match["families"])

    for result in results:
        group = categories[result["commercial_category"]]
        group["analyzed"] += 1
        group["resolved"] += result["status"] in {"experience_required", "no_experience_required"}
        group["no_experience_required"] += result["status"] == "no_experience_required"
        for key, value in result["operational_cost"].items():
            group["operational_cost"][key] += value
    for group in categories.values():
        group["resolution_rate"] = fraction(group["resolved"], group["analyzed"])
        group["no_experience_rate"] = fraction(group["no_experience_required"], group["resolved"])
        group["operational_cost"]["elapsed_seconds"] = round(
            group["operational_cost"]["elapsed_seconds"], 3
        )
    return {
        "categories": categories,
        "candidates_by_commercial_family": dict(commercial_families),
        "candidates_by_unspsc_family": dict(unspsc_families),
        "candidate_matches_by_method": {method: methods[method] for method in METHODS},
        "multi_category_processes_deduplicated": overlap,
        "open_commercial_candidates": sum(g["open_candidates"] for g in categories.values()),
    }


def fraction(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }
