"""Estado del análisis de una compra, tal como lo ve el Analista en la exploración.

Distingue «la fuente no publica el dato» de «el producto no pudo compararlo».
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class AnalysisStatus(StrEnum):
    WITH_SIGNAL = "with_signal"
    COMPARED_NO_SIGNAL = "compared_no_signal"
    INSUFFICIENT_COMPARABLES = "insufficient_comparables"
    EXCLUDED = "excluded"
    QUALITY_REVIEW = "quality_review"
    NO_UNIT_PRICE = "no_unit_price"
    VAT_INCOMPLETE = "vat_incomplete"
    PENDING_COMPARISON = "pending_comparison"


class ComparisonState(StrEnum):
    """Resultado vigente de la comparación de la compra (lo calcula el módulo de comparación)."""

    SIGNAL = "signal"
    NO_SIGNAL = "no_signal"
    LOW_PRICE_REVIEW = "low_price_review"
    INSUFFICIENT_COMPARABLES = "insufficient_comparables"


@dataclass(frozen=True)
class ItemState:
    """Lo que el estado del análisis necesita saber de un ítem."""

    is_tv: bool
    price_pending_review: bool
    price_missing: bool
    vat_not_comparable: bool


def derive_analysis_status(
    items: Sequence[ItemState], comparison: ComparisonState | None = None
) -> AnalysisStatus:
    """Precedencia: excluido → con señal → revisión de calidad → sin precio → IVA no comparable →
    comparado sin señal → comparables insuficientes → pendiente de comparación."""
    tv_items = [item for item in items if item.is_tv]
    if not tv_items:
        return AnalysisStatus.EXCLUDED
    if comparison is ComparisonState.SIGNAL:
        return AnalysisStatus.WITH_SIGNAL
    if comparison is ComparisonState.LOW_PRICE_REVIEW or any(
        item.price_pending_review for item in tv_items
    ):
        return AnalysisStatus.QUALITY_REVIEW
    if all(item.price_missing for item in tv_items):
        return AnalysisStatus.NO_UNIT_PRICE
    if any(item.vat_not_comparable for item in tv_items):
        return AnalysisStatus.VAT_INCOMPLETE
    if comparison is ComparisonState.NO_SIGNAL:
        return AnalysisStatus.COMPARED_NO_SIGNAL
    if comparison is ComparisonState.INSUFFICIENT_COMPARABLES:
        return AnalysisStatus.INSUFFICIENT_COMPARABLES
    return AnalysisStatus.PENDING_COMPARISON
