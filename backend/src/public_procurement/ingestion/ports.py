"""Puertos de la ingesta: dependencias externas que implementan los adaptadores."""

from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from .domain.purchase import Source, SourcePurchase


class PublicDataSource(Protocol):
    """Fuente de datos abiertos de compras: SECOP II o TVEC (datos.gov.co), o el seed de la demo."""

    @property
    def source(self) -> Source: ...

    @property
    def cutoff_at(self) -> datetime:
        """Fecha de corte de los datos que entrega la fuente (con zona horaria)."""
        ...

    def fetch_purchases(self) -> Iterable[SourcePurchase]: ...
