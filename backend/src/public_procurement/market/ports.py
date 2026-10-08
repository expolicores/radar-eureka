"""Puertos del mercado: fuentes de observaciones retail (captura permitida, carga manual o seed)."""

from collections.abc import Iterable
from typing import Protocol

from .domain.observation import MarketObservation


class RetailObservationSource(Protocol):
    def fetch_observations(self) -> Iterable[MarketObservation]: ...
