"""Adaptador seed del puerto `PublicDataSource`: datos ficticios para la demo, sin red.

Lo reemplaza el adaptador de Socrata (datos.gov.co) sin cambios en el dominio ni en el servicio.
"""

from collections.abc import Iterable
from datetime import datetime

from ..domain.purchase import Source, SourcePurchase
from .seed_data import SEED_CUTOFF_AT, generate_seed_purchases


class SeedPublicDataSource:
    def __init__(self, source: Source) -> None:
        self._source = source

    @property
    def source(self) -> Source:
        return self._source

    @property
    def cutoff_at(self) -> datetime:
        return SEED_CUTOFF_AT

    def fetch_purchases(self) -> Iterable[SourcePurchase]:
        return [
            purchase for purchase in generate_seed_purchases() if purchase.source is self._source
        ]
