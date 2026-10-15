"""Solo lectura a través de extraction.services, sin tablas ni repositorios ajenos."""

import uuid
from typing import Any

from public_procurement.extraction.services import ConsolidationService

from ..domain.details import CanonicalEntry, CanonicalInput


class ExtractionCanonicalSource:
    def __init__(self, canonical: ConsolidationService) -> None:
        self.canonical = canonical

    def read(self, reference: str) -> CanonicalInput:
        result = self.canonical.read_state(reference)
        summary = result.summary
        return CanonicalInput(
            result.status,
            tuple(
                CanonicalEntry(
                    fact.id,
                    fact.canonical_type,
                    fact.canonical_value.get("value"),
                    fact.confidence,
                    fact.status,
                    fact.canonical_value.get("corroborated", False),
                    fact.evidence_ids,
                    fact.canonical_value.get(
                        "candidates", fact.canonical_value.get("field_candidates", [])
                    ),
                    fact.canonical_value.get("field_sources", {}),
                    fact.canonical_value.get("field_confidence", {}),
                )
                for fact in summary.facts
            ),
            summary.missing_fields,
            summary.input_count,
            self.canonical.structured.content.coverage_for_process(reference)
            if result.status != "not_extracted"
            else {},
        )

    def evidence(self, reference: str, canonical_id: uuid.UUID) -> list[dict[str, Any]]:
        return [
            {
                "structured_fact_id": str(fact.id),
                "document_version_id": str(fact.document_version_id),
                "content_fragment_id": str(fact.content_fragment_id)
                if fact.content_fragment_id
                else None,
                "evidence_text": fact.evidence_text,
                "source_locator": fact.source_locator,
                "rule_name": fact.rule_name,
                "rule_version": fact.rule_version,
            }
            for fact in self.canonical.evidence(reference, canonical_id)
        ]
