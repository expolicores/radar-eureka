from sqlalchemy import func, select

from public_procurement.extraction.canonical_repositories import (
    CanonicalEvidenceRecord,
    CanonicalFactRecord,
)
from public_procurement.extraction.services import ConsolidationService

from .test_structured_service import setup_service


def canonical_setup(sessions, create_tables=True):
    structured, reader = setup_service(sessions)
    structured.extract("P")
    if create_tables:
        with sessions.begin() as session:
            CanonicalFactRecord.__table__.create(session.connection())
            CanonicalEvidenceRecord.__table__.create(session.connection())
    return ConsolidationService(sessions, structured), reader


def count(sessions, model):
    with sessions() as session:
        return session.scalar(select(func.count()).select_from(model))


def test_dry_run_needs_no_canonical_tables_and_does_not_rerun_extraction(sessions):
    service, reader = canonical_setup(sessions, create_tables=False)
    summary = service.run("P", dry_run=True)
    assert summary.input_count == 3
    assert len(summary.facts) == 3
    assert summary.inserted == 0
    assert not summary.persisted
    assert reader.calls == 1


def test_persistence_reuses_ids_links_and_preserves_original_evidence(sessions):
    service, _ = canonical_setup(sessions)
    first = service.run("P")
    repeated = service.run("P")
    assert first.inserted == 3
    assert repeated.inserted == 0
    assert [f.id for f in first.facts] == [f.id for f in repeated.facts]
    stored = service.show("P")
    assert [f.id for f in stored.facts] == [f.id for f in first.facts]
    assert count(sessions, CanonicalFactRecord) == 3
    assert count(sessions, CanonicalEvidenceRecord) == 3
    for fact in stored.facts:
        evidence = service.evidence("P", fact.id)
        assert {source.id for source in evidence} == set(fact.evidence_ids)
        assert evidence[0].source_locator["sources"][0]["text"]


def test_changed_inputs_and_rules_keep_snapshots_but_never_show_stale_results(sessions):
    service, reader = canonical_setup(sessions)
    first = service.run("P")
    service.rule_version = "canonical-v2"
    assert not service.show("P").persisted
    changed = service.run("P")
    assert changed.inserted == 3
    assert count(sessions, CanonicalFactRecord) == 6
    reader.version = "reader-v2"
    service.structured.content.extract_document("D")
    service.structured.extract("P")
    assert not service.show("P").persisted
    newest = service.run("P")
    assert newest.inserted == 3
    assert count(sessions, CanonicalFactRecord) == 9
    assert len(service.history("P")) == 9
    assert service.evidence("P", first.facts[0].id)
    assert [fact.id for fact in service.show("P").facts] == [fact.id for fact in newest.facts]


def test_evidence_lookup_does_not_cross_processes(sessions):
    import uuid

    service, _ = canonical_setup(sessions)
    first = service.run("P")
    service.structured.content.documents.process_identifier = uuid.uuid4()
    assert service.evidence("Other", first.facts[0].id) == []


def test_derived_read_status_progresses_without_creating_missing_tables(sessions):
    from public_procurement.extraction.domain.content import ExtractionLimits
    from public_procurement.extraction.services import (
        ExtractionService,
        StructuredExtractionService,
    )
    from public_procurement.extraction.structured_repositories import StructuredFactRecord

    from .test_services import Source
    from .test_structured_service import StructuredReader

    content = ExtractionService(sessions, Source(), StructuredReader(), ExtractionLimits())
    structured = StructuredExtractionService(sessions, content)
    service = ConsolidationService(sessions, structured)
    assert service.read_state("P").status == "not_extracted"
    content.extract_document("D")
    assert service.read_state("P").status == "extracted"
    with sessions.begin() as session:
        StructuredFactRecord.__table__.create(session.connection())
    structured.extract("P")
    assert service.read_state("P").status == "structured"
    with sessions.begin() as session:
        CanonicalFactRecord.__table__.create(session.connection())
        CanonicalEvidenceRecord.__table__.create(session.connection())
    service.run("P")
    assert service.read_state("P").status == "consolidated"
    assert service.read_state("P").summary.input_count == 3


def test_read_status_does_not_show_stale_canonical_snapshot(sessions):
    service, reader = canonical_setup(sessions)
    service.run("P")
    assert service.read_state("P").status == "consolidated"
    reader.version = "new-reader"
    service.structured.content.extract_document("D")
    assert service.read_state("P").status == "extracted"
    service.structured.extract("P")
    assert service.read_state("P").status == "structured"


def test_read_status_marks_persisted_conflicts(sessions):
    service, _ = canonical_setup(sessions)
    summary = service.run("P")
    with sessions.begin() as session:
        record = session.get(CanonicalFactRecord, summary.facts[0].id)
        record.status = "conflict"
        record.canonical_value = {
            "value": None,
            "candidates": [],
            "review_required": True,
            "corroborated": False,
        }
    assert service.read_state("P").status == "conflict"


def test_read_status_before_extraction_schema_exists():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from public_procurement.extraction.domain.content import ExtractionLimits
    from public_procurement.extraction.services import (
        ExtractionService,
        StructuredExtractionService,
    )

    from .test_services import Reader, Source

    engine = create_engine("sqlite://")
    try:
        sessions = sessionmaker(engine)
        content = ExtractionService(sessions, Source(), Reader(), ExtractionLimits())
        service = ConsolidationService(sessions, StructuredExtractionService(sessions, content))
        assert service.read_state("P").status == "not_extracted"
    finally:
        engine.dispose()
