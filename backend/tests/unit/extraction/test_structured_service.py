from dataclasses import replace

import pytest
from sqlalchemy import func, select

from public_procurement.extraction.domain.content import ExtractionLimits
from public_procurement.extraction.services import ExtractionService, StructuredExtractionService
from public_procurement.extraction.structured_repositories import StructuredFactRecord

from .test_services import Reader, Source


class StructuredReader(Reader):
    def extract(self, document):
        parsed = super().extract(document)
        return replace(
            parsed,
            fragments=(
                replace(
                    parsed.fragments[0],
                    text="Jugo Acme X 200 ml. Se exige RUP.",
                ),
            ),
        )


def setup_service(sessions):
    source, reader = Source(), StructuredReader()
    content = ExtractionService(sessions, source, reader, ExtractionLimits())
    content.extract_document("D")
    with sessions.begin() as session:
        StructuredFactRecord.__table__.create(session.connection())
    return StructuredExtractionService(sessions, content), reader


def count_facts(sessions):
    with sessions() as session:
        return session.scalar(select(func.count()).select_from(StructuredFactRecord))


def test_structured_dry_run_reuses_fragments_without_reextracting_or_writing(sessions):
    service, reader = setup_service(sessions)
    results, inserted = service.extract("P", dry_run=True)
    assert inserted == 0
    assert count_facts(sessions) == 0
    assert reader.calls == 1
    assert {fact.fact_type for fact in results} == {"product", "presentation", "rup"}


def test_structured_idempotence_versions_and_current_vs_historical_evidence(sessions):
    service, reader = setup_service(sessions)
    facts, inserted = service.extract("P")
    repeated, second_inserted = service.extract("P")
    assert inserted == len(facts) == 3
    assert second_inserted == 0
    assert [fact.fingerprint for fact in facts] == [fact.fingerprint for fact in repeated]
    assert count_facts(sessions) == 3
    stored = service.list_facts("P")
    assert all(fact.id is not None for fact in stored)
    assert stored[0].source_locator["sources"][0]["content_fragment_id"]
    service.rule_version = "structured-v2"
    _, inserted = service.extract("P")
    assert inserted == 3
    assert count_facts(sessions) == 6
    assert len(service.list_facts("P")) == 3
    assert len(service.list_facts("P", include_history=True)) == 6
    reader.version = "v2"
    service.content.extract_document("D")
    assert service.list_facts("P") == []
    service.extract("P")
    assert len(service.list_facts("P")) == 3
    assert len(service.list_facts("P", include_history=True)) == 9


def test_missing_persisted_fragments_is_explicit_and_does_not_trigger_download(sessions):
    reader = Reader()
    content = ExtractionService(sessions, Source(), reader, ExtractionLimits())
    with pytest.raises(ValueError, match="fragmentos persistidos"):
        StructuredExtractionService(sessions, content).extract("P", dry_run=True)
    assert reader.calls == 0
