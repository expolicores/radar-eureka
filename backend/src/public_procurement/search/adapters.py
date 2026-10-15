import uuid
from typing import Any

from sqlalchemy.orm import Session

from public_procurement.eureka.services import search_opportunities
from public_procurement.extraction.services import (
    search_extraction_candidates,
    search_extraction_evidence,
    search_extraction_snapshots,
)
from public_procurement.ingestion.services import search_process_candidates, search_process_records

from .domain.query import SearchQuery, normalize, tsquery


class PersistedSearchSource:
    def __init__(self, session: Session) -> None:
        self.session = session

    def eligible(
        self, query: SearchQuery, identifiers: set[uuid.UUID] | None = None
    ) -> set[uuid.UUID]:
        return search_process_candidates(
            self.session,
            None,
            {
                "identifiers": identifiers,
                "department": normalize(query.department),
                "municipality": normalize(query.municipality),
                "published_from": query.published_from,
                "published_to": query.published_to,
                "entity_query": tsquery([normalize(query.entity)])
                if normalize(query.entity)
                else None,
            },
        )

    def candidates(self, expression: str, query: SearchQuery) -> set[uuid.UUID]:
        return search_process_candidates(
            self.session, expression, {}
        ) | search_extraction_candidates(self.session, expression)

    def batch(
        self, identifiers: list[uuid.UUID], expression: dict[str, str] | None
    ) -> list[dict[str, Any]]:
        metadata = search_process_records(self.session, identifiers, expression or {})
        content = search_extraction_snapshots(self.session, identifiers, expression)
        opportunities = search_opportunities(self.session, identifiers)
        return [
            {"metadata": m, **content[m["id"]], "opportunity": opportunities.get(m["id"])}
            for m in metadata
        ]

    def evidence(
        self, process_id: uuid.UUID, canonical_id: uuid.UUID | None, fragment_id: uuid.UUID | None
    ) -> list[dict[str, Any]]:
        return search_extraction_evidence(self.session, process_id, canonical_id, fragment_id)
