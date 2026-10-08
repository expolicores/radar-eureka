"""Resultado de una compra a partir de los resultados de sus ítems de televisor."""

from collections.abc import Iterable

from .evaluation import Outcome

# Lo más relevante para el Analista primero.
_PRECEDENCE = (
    Outcome.SIGNAL,
    Outcome.LOW_PRICE_REVIEW,
    Outcome.NO_SIGNAL,
    Outcome.INSUFFICIENT_COMPARABLES,
    Outcome.QUALITY_REVIEW,
    Outcome.VAT_INCOMPLETE,
    Outcome.NO_UNIT_PRICE,
)


def purchase_outcome(outcomes: Iterable[Outcome]) -> Outcome | None:
    present = set(outcomes)
    return next((outcome for outcome in _PRECEDENCE if outcome in present), None)
