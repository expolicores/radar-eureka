"""Estadísticos de una distribución de precios, en `Decimal` (nunca `float` para dinero)."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

ONE_DECIMAL = Decimal("0.1")


def quantile(sorted_values: Sequence[Decimal], q: Decimal) -> Decimal:
    """Cuantil con interpolación lineal en la posición `(n − 1) · q`."""
    if not sorted_values:
        raise ValueError("empty_distribution")
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    fraction = position - lower
    if lower + 1 >= len(sorted_values):
        return sorted_values[lower]
    return sorted_values[lower] + fraction * (sorted_values[lower + 1] - sorted_values[lower])


@dataclass(frozen=True)
class Distribution:
    count: int
    q1: Decimal
    median: Decimal
    q3: Decimal

    @property
    def iqr(self) -> Decimal:
        return self.q3 - self.q1

    @classmethod
    def of(cls, prices_cop: Sequence[int]) -> "Distribution":
        values = sorted(Decimal(price) for price in prices_cop)
        return cls(
            count=len(values),
            q1=quantile(values, Decimal("0.25")),
            median=quantile(values, Decimal("0.5")),
            q3=quantile(values, Decimal("0.75")),
        )


def to_cop(value: Decimal) -> int:
    """Redondea un intermedio a COP entero."""
    return int(value.to_integral_value(ROUND_HALF_UP))


def deviation_pct(price_cop: int, reference: Decimal) -> Decimal:
    """Desviación porcentual del precio frente a la referencia, con un decimal."""
    if reference <= 0:
        raise ValueError("reference_must_be_positive")
    return ((Decimal(price_cop) - reference) / reference * 100).quantize(ONE_DECIMAL, ROUND_HALF_UP)
