"""Nivel de confianza de una comparación: 100 menos penalizaciones configurables (FR-068)."""

from dataclasses import dataclass
from enum import StrEnum

from .config import PENALTY_LABELS, AnalysisConfig, PenaltyCode


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Penalty:
    code: PenaltyCode
    label: str
    points: int


@dataclass(frozen=True)
class Confidence:
    score: int
    level: ConfidenceLevel
    penalties: tuple[Penalty, ...]


def compute_confidence(codes: list[PenaltyCode], config: AnalysisConfig) -> Confidence:
    penalties = tuple(Penalty(code, PENALTY_LABELS[code], config.penalties[code]) for code in codes)
    score = max(0, 100 - sum(penalty.points for penalty in penalties))
    if score >= config.high_confidence_from:
        level = ConfidenceLevel.HIGH
    elif score >= config.medium_confidence_from:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW
    return Confidence(score=score, level=level, penalties=penalties)
