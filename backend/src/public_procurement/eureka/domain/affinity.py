"""Afinidad comercial determinística; UNSPSC nunca confirma un producto documental."""

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from ..radar_config import RadarConfig


def normalize(value: str, config: RadarConfig) -> str:
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", text)
    tokens = re.findall(r"[a-z0-9]+", text)
    return " ".join(config.token_aliases.get(token, token) for token in tokens)


def phrase_match(text: str, phrase: str, config: RadarConfig) -> bool:
    needle = normalize(phrase, config)
    if not needle:
        return False
    normalized = normalize(text, config)
    for match in re.finditer(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", normalized):
        prefix = normalized[max(0, match.start() - 45) : match.start()]
        if not re.search(r"(?:no(?: se)?(?: (?:requiere|exige|incluye))?|sin)\s+$", prefix):
            return True
    return False


@dataclass(frozen=True)
class CommercialMatch:
    category: str
    label: str
    concept: str
    matched: str
    origin: str
    method: str
    canonical_fact_id: str | None = None

    def json(self) -> dict[str, Any]:
        return asdict(self)


def match_catalog(
    text: str,
    unspsc: str,
    config: RadarConfig,
    origin: str = "metadata",
    canonical_id: str | None = None,
) -> list[CommercialMatch]:
    matches: list[CommercialMatch] = []
    codes = set(re.findall(r"(?<!\d)\d{8}(?!\d)", unspsc))
    for family in sorted(config.families, key=lambda item: -item.priority):
        if any(phrase_match(text, term, config) for term in family.exclusions):
            continue
        concepts: set[str] = set()
        for method, terms in (
            ("term", family.terms),
            ("phrase", family.phrases),
            ("brand", family.brands),
        ):
            for term in terms:
                if phrase_match(text, term, config) and normalize(term, config) not in concepts:
                    concepts.add(normalize(term, config))
                    matches.append(
                        CommercialMatch(
                            family.category,
                            family.label,
                            term,
                            term,
                            origin,
                            method + "/normalization",
                            canonical_id,
                        )
                    )
        for concept, aliases in family.aliases.items():
            for alias in (concept, *aliases):
                if phrase_match(text, alias, config):
                    matches.append(
                        CommercialMatch(
                            family.category,
                            family.label,
                            concept,
                            alias,
                            origin,
                            "alias/normalization",
                            canonical_id,
                        )
                    )
                    break
        for code in sorted(codes.intersection(family.unspsc)):
            matches.append(
                CommercialMatch(
                    family.category, family.label, code, code, origin, "unspsc", canonical_id
                )
            )
    return matches
