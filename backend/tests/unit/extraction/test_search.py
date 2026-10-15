import pytest

from public_procurement.extraction.domain.content import ExtractionLimits
from public_procurement.extraction.services import ExtractionService

from .test_services import Reader, Source


@pytest.mark.parametrize("term", ["CHOCoRRaMo", "Hit", "garantia", "GARANTÍA"])
def test_persisted_search_is_case_and_accent_tolerant_with_exact_evidence(sessions, term) -> None:
    source, reader = Source(), Reader()
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    result = service.extract_document("D")
    hits = service.search("P", term)
    assert len(hits) == 1
    assert hits[0].extraction_run_id == result.run_id
    assert hits[0].text == "Garantía: Chocorramo y Hit"
    assert hits[0].source_locator["page_number"] == 1
    assert hits[0].context[0]["text"] == hits[0].text


def test_search_uses_latest_extractor_without_duplicate_historical_hits(sessions) -> None:
    source, reader = Source(), Reader()
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    service.extract_document("D")
    reader.version = "v2"
    newest = service.extract_document("D")
    hits = service.search("P", "chocorramo")
    assert len(hits) == 1
    assert hits[0].extraction_run_id == newest.run_id


def test_empty_query_and_sql_wildcards_are_safe(sessions) -> None:
    service = ExtractionService(sessions, Source(), Reader(), ExtractionLimits())
    service.extract_document("D")
    with pytest.raises(ValueError, match="inválido"):
        service.search("P", "  ")
    assert service.search("P", "%") == []
