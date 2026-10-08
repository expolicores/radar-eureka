"""Configuración analítica versionada: ventanas, mínimos, reglas de señal y penalizaciones.

Los valores iniciales son los del PRD (P-01…P-04, FR-055…FR-068). Sirven para PRIORIZAR revisión
humana y se recalibran con evidencia real; cada resultado guarda el `id` de la versión usada.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class PenaltyCode(StrEnum):
    EQUIVALENT_MATCH = "equivalent_match"
    DERIVED_PRICE = "derived_price"
    MARKET_LIMITED = "market_limited"
    MARKET_UNAVAILABLE = "market_unavailable"
    FEW_COMPARABLES = "few_comparables"
    EXTENDED_WINDOW = "extended_window"
    PERCENTAGE_RULE = "percentage_rule"


PENALTY_LABELS: dict[PenaltyCode, str] = {
    PenaltyCode.EQUIVALENT_MATCH: "Emparejamiento por equivalencia (no mismo modelo)",
    PenaltyCode.DERIVED_PRICE: "Precio unitario derivado (no explícito)",
    PenaltyCode.MARKET_LIMITED: "Benchmark 2 con evidencia limitada",
    PenaltyCode.MARKET_UNAVAILABLE: "Benchmark 2 no disponible",
    PenaltyCode.FEW_COMPARABLES: "Menos de 10 compras comparables",
    PenaltyCode.EXTENDED_WINDOW: "Ventana de comparables ampliada a ±12 meses",
    PenaltyCode.PERCENTAGE_RULE: "Muestra pequeña o heterogénea: umbral porcentual",
}


def _default_penalties() -> dict[PenaltyCode, int]:
    return {
        PenaltyCode.EQUIVALENT_MATCH: 20,
        PenaltyCode.DERIVED_PRICE: 10,
        PenaltyCode.MARKET_LIMITED: 10,
        PenaltyCode.MARKET_UNAVAILABLE: 15,
        PenaltyCode.FEW_COMPARABLES: 10,
        PenaltyCode.EXTENDED_WINDOW: 10,
        PenaltyCode.PERCENTAGE_RULE: 10,
    }


@dataclass(frozen=True)
class AnalysisConfig:
    id: str = "analitica-v1"
    # Benchmark 1 — contratación pública
    window_months: int = 6
    extended_window_months: int = 12
    min_comparables: int = 5
    homogeneous_min_comparables: int = 10
    homogeneous_max_iqr_ratio: Decimal = Decimal("0.5")
    outlier_iqr_factor: Decimal = Decimal("1.5")
    same_model_threshold_pct: Decimal = Decimal(30)
    equivalent_threshold_pct: Decimal = Decimal(50)
    low_price_median_ratio: Decimal = Decimal("0.5")
    # Benchmark 2 — mercado
    market_window_days: int = 30
    market_min_observations: int = 3
    market_min_stores: int = 2
    # Confianza
    few_comparables_below: int = 10
    high_confidence_from: int = 75
    medium_confidence_from: int = 50
    penalties: dict[PenaltyCode, int] = field(default_factory=_default_penalties)


DEFAULT_CONFIG = AnalysisConfig()
