"""Provider-independent boundaries for cheap discovery and bounded price scouting."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol

from .schemas import MarketObservation, ProductIdentity, SearchResult


class WebSearch(Protocol):
    def search(self, query: str) -> list[SearchResult]: ...


@dataclass
class ShoppingDiscoveryResult:
    observations: list[MarketObservation] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)


class ShoppingSearchPort(Protocol):
    def discover(
        self, product: ProductIdentity, target: int = 3, maximum: int = 5
    ) -> ShoppingDiscoveryResult: ...


@dataclass(frozen=True)
class ScoutRequest:
    product: ProductIdentity
    target_observations: int = 3
    max_observations: int = 5
    country: str = "Colombia"
    currency: str = "COP"
    excluded_urls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 1 <= self.target_observations <= self.max_observations <= 5:
            raise ValueError("Scout supports 1 <= target <= maximum <= 5")


class ScoutUnavailableError(Exception):
    """Sanitized optional-provider failure; never includes request bodies or credentials."""

    def __init__(self, code: str, *, error_type: str | None = None, http_status: int | None = None):
        super().__init__(code)
        self.error_type, self.http_status = error_type, http_status


class MarketPriceScout(Protocol):
    # Lazy iteration lets the service stop before requesting more offers from a browser.
    def scout(self, request: ScoutRequest) -> Iterable[MarketObservation]: ...


class MarketPageVerifier(Protocol):
    def verify(
        self, product: ProductIdentity, candidate: MarketObservation
    ) -> MarketObservation: ...
