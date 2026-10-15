import uuid
from typing import Any, Protocol

from .domain.query import SearchQuery


class SearchSource(Protocol):
    def eligible(
        self, query: SearchQuery, identifiers: set[uuid.UUID] | None = None
    ) -> set[uuid.UUID]: ...
    def candidates(self, expression: str, query: SearchQuery) -> set[uuid.UUID]: ...
    def batch(
        self, identifiers: list[uuid.UUID], expression: dict[str, str] | None
    ) -> list[dict[str, Any]]: ...
    def evidence(
        self, process_id: uuid.UUID, canonical_id: uuid.UUID | None, fragment_id: uuid.UUID | None
    ) -> list[dict[str, Any]]: ...
