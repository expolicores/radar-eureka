import hashlib
import os
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select

from public_procurement.extraction.adapters import hybrid, ocr
from public_procurement.extraction.adapters.hybrid import LocalOcrFallback
from public_procurement.extraction.adapters.isolated import IsolatedExtractor
from public_procurement.extraction.canonical_repositories import (
    CanonicalEvidenceRecord,
    CanonicalFactRecord,
)
from public_procurement.extraction.domain.content import (
    ExtractionError,
    ExtractionLimits,
    ExtractionStatus,
)
from public_procurement.extraction.ocr_config import OcrPolicy
from public_procurement.extraction.repositories import (
    ExtractionDiagnosticRecord,
    ExtractionRunRecord,
)
from public_procurement.extraction.services import (
    ConsolidationService,
    ExtractionService,
    StructuredExtractionService,
)
from public_procurement.extraction.structured_repositories import StructuredFactRecord

from .test_ocr import ENGINE, FIXTURES, TEXT
from .test_services import Source


def build(sessions, name="scanned_refrigerios", policy=None):
    source = Source()
    source.data = (FIXTURES / f"{name}.pdf").read_bytes()
    source.documents[0] = replace(
        source.documents[0],
        input_sha256=hashlib.sha256(source.data).hexdigest(),
        observed_size=len(source.data),
    )
    limits = ExtractionLimits()
    fallback = LocalOcrFallback(
        source,
        limits,
        policy or OcrPolicy(),
        os.environ.get("EXTRACTION_TESSERACT_CMD", "tesseract"),
        Path(os.environ["EXTRACTION_TESSDATA_PATH"])
        if os.environ.get("EXTRACTION_TESSDATA_PATH")
        else None,
    )
    return ExtractionService(sessions, source, IsolatedExtractor(source, limits), limits, fallback)


@pytest.fixture
def simulated_engine(monkeypatch, tmp_path):
    pytest.importorskip("pypdfium2")
    monkeypatch.setattr(hybrid, "probe_engine", lambda *args: ENGINE)
    recognize = Mock(return_value=(TEXT, 95))
    monkeypatch.setattr(ocr, "recognize_image", recognize)

    def extract(reader, document):
        snapshot = tmp_path / "snapshot.pdf"
        with reader.documents.open_version(
            document.document_version_id, reader.limits.max_bytes
        ) as source:
            snapshot.write_bytes(source.read())
        return ocr.extract_ocr(snapshot, reader.limits, reader.policy, reader.pages, reader.engine)

    monkeypatch.setattr(hybrid.OcrPageExtractor, "extract", extract)
    return recognize


def test_native_never_calls_engine_probe(sessions, monkeypatch):
    probe = Mock(side_effect=AssertionError("native must not invoke OCR"))
    monkeypatch.setattr(hybrid, "probe_engine", probe)
    result = build(sessions, "native_refrigerios").extract_document("D")
    assert result.status is ExtractionStatus.COMPLETED
    assert result.extractor.name == "pdf-text"
    probe.assert_not_called()


def test_mixed_uses_ocr_only_page_two_and_keeps_native_runs(sessions, simulated_engine):
    service = build(sessions, "mixed_refrigerios")
    result = service.extract_document("D")
    _, fragments = service.content_for_process("P")
    assert [
        (f.source_locator["page_number"], f.source_locator["extraction_method"]) for f in fragments
    ] == [(1, "native_pdf_text"), (2, "ocr_text"), (3, "native_pdf_text")]
    assert result.diagnostics["required_pages"] == [2]
    simulated_engine.assert_called_once()
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(ExtractionRunRecord)) == 2
    second = service.extract_document("D")
    assert second.run_id == result.run_id
    assert second.reused
    simulated_engine.assert_called_once()


def test_unavailable_conserves_native_and_retry_is_explicit(
    sessions, simulated_engine, monkeypatch
):
    service = build(sessions, "mixed_refrigerios")
    monkeypatch.setattr(
        hybrid, "probe_engine", lambda *args: {"available": False, "error_code": "ocr_unavailable"}
    )
    first = service.extract_document("D")
    assert first.status is ExtractionStatus.PARTIAL_TEXT
    assert first.diagnostics["status"] == "ocr_unavailable"
    assert service.extract_document("D").run_id == first.run_id
    assert len(service.content_for_process("P")[1]) == 2
    retried = service.extract_document("D", retry_ocr=True)
    assert retried.run_id != first.run_id
    assert retried.diagnostics["attempt"] == 1
    monkeypatch.setattr(hybrid, "probe_engine", lambda *args: ENGINE)
    recovered = service.extract_document("D")
    assert recovered.diagnostics["coverage_complete"]
    assert recovered.run_id != retried.run_id


def test_forced_ocr_cannot_overwrite_native_and_poor_output_keeps_both_native_pages(
    sessions, simulated_engine
):
    service = build(sessions, "mixed_refrigerios")
    simulated_engine.return_value = ("@@", 10)
    result = service.extract_document("D")
    assert not result.diagnostics["coverage_complete"]
    assert [f.source_locator["page_number"] for f in service.content_for_process("P")[1]] == [1, 3]
    with pytest.raises(ValueError, match="dry-run"):
        service.extract_document("D", force_ocr=True)
    with sessions() as session:
        count = session.scalar(select(func.count()).select_from(ExtractionRunRecord))
    service.extract_document("D", dry_run=True, force_ocr=True)
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(ExtractionRunRecord)) == count


def test_truncation_survives_persistence_and_reaches_evidence(sessions, simulated_engine):
    service = build(
        sessions, "mixed_refrigerios", OcrPolicy(max_ocr_pages=1, min_alphanumeric_chars=1000)
    )
    # Keep OCR quality sufficient while requiring all native pages by forcing diagnosis separately.
    service.ocr.policy = OcrPolicy(max_ocr_pages=1)
    native = service._perform(service.documents.documents[0], False, service.extractor)
    with sessions() as session:
        from public_procurement.extraction.repositories import SqlExtractionRepository

        native = replace(
            native, fragments=SqlExtractionRepository(session).fragments(native.run_id)
        )
    extractor = service.ocr.prepare(native, force=True)
    result = service._perform(native.document, False, extractor)
    assert result.diagnostics["status"] == "ocr_truncated"
    assert result.status is ExtractionStatus.PARTIAL_TEXT
    assert result.diagnostics["omitted_pages"] == [2, 3]
    assert not service.coverage_for_process("P")["coverage_complete"]
    assert all(
        f.source_locator["document_coverage_complete"] is False
        for f in service.content_for_process("P")[1]
    )


def test_old_schema_keeps_beta_native_and_requires_migration_for_persistent_ocr(
    sessions, simulated_engine
):
    with sessions.begin() as session:
        ExtractionDiagnosticRecord.__table__.drop(session.connection())
    result = build(sessions, "mixed_refrigerios").extract_document("D")
    assert result.extractor.name == "pdf-text"
    assert result.diagnostics["status"] == "ocr_migration_required"
    assert not result.diagnostics["coverage_complete"]
    simulated_engine.assert_not_called()


def run_facts(service, sessions):
    with sessions.begin() as session:
        for table in (StructuredFactRecord, CanonicalFactRecord, CanonicalEvidenceRecord):
            table.__table__.create(session.connection())
    structured = StructuredExtractionService(sessions, service)
    facts, inserted = structured.extract("P")
    assert inserted > 0
    assert any(f.fact_type == "quantity" and str(f.numeric_value) == "400" for f in facts)
    assert any(f.fact_type == "unit_price_cop" and int(f.numeric_value) == 5200 for f in facts)
    assert any(f.fact_type == "total_cop" and int(f.numeric_value) == 2080000 for f in facts)
    products = [f.normalized_value for f in facts if f.fact_type == "product"]
    assert any("hit" in p["name"] and p["presentation"] == "200" for p in products)
    assert any("chocorramo" in p["name"] and p["presentation"] == "65" for p in products)
    assert all(
        source["locator"]["extraction_method"] == "ocr_text"
        for f in facts
        for source in f.source_locator["sources"]
    )
    canonical = ConsolidationService(sessions, structured)
    summary = canonical.run("P")
    assert summary.persisted
    assert {f.canonical_type for f in summary.facts} >= {
        "PRODUCT",
        "PRESENTATION",
        "QUANTITY",
        "UNIT_PRICE_COP",
        "TOTAL_COP",
    }
    values = {
        kind: [f.canonical_value["value"] for f in summary.facts if f.canonical_type == kind]
        for kind in ("PRODUCT", "QUANTITY", "UNIT_PRICE_COP", "TOTAL_COP")
    }
    assert any("hit" in v["name"] and v["presentation_value"] == 200 for v in values["PRODUCT"])
    assert any(
        "chocorramo" in v["name"] and v["presentation_value"] == 65 for v in values["PRODUCT"]
    )
    assert {"value": 400, "unit": "PACK"} in values["QUANTITY"]
    assert {"value": 5200, "unit": "COP"} in values["UNIT_PRICE_COP"]
    assert {"value": 2080000, "unit": "COP"} in values["TOTAL_COP"]
    assert canonical.run("P").inserted == 0
    for fact in summary.facts:
        assert (
            canonical.evidence("P", fact.id)[0].source_locator["sources"][0]["locator"][
                "page_number"
            ]
            == 1
        )
    return summary


def test_scan_reaches_existing_structured_and_canonical_pipeline(sessions, simulated_engine):
    service = build(sessions)
    result = service.extract_document("D")
    assert result.diagnostics["status"] == "ocr_success"
    run_facts(service, sessions)


@pytest.mark.ocr_real
def test_real_tesseract_scanned_acceptance(sessions):
    if os.environ.get("RUN_REAL_OCR") != "1":
        pytest.skip("Aceptación OCR real pendiente: ejecutar con RUN_REAL_OCR=1 y Tesseract local.")
    service = build(sessions)
    result = service.extract_document("D")
    assert result.diagnostics["status"] == "ocr_success", result.diagnostics
    assert result.diagnostics["processed_pages"] == [1]
    assert service.content_for_process("P")[1][0].source_locator["extraction_method"] == "ocr_text"
    run_facts(service, sessions)


def test_native_parser_failure_can_fallback_without_bypassing_integrity(
    sessions, simulated_engine, monkeypatch
):
    service = build(sessions)
    monkeypatch.setattr(
        service.extractor,
        "extract",
        Mock(side_effect=ExtractionError("corrupt_file", "native failed")),
    )
    result = service.extract_document("D")
    assert result.diagnostics["native_error_code"] == "corrupt_file"
    assert result.diagnostics["coverage_complete"]
    service.extractor.identity = Mock(return_value=replace(result.extractor, version="new"))
    monkeypatch.setattr(
        service.extractor, "extract", Mock(side_effect=ExtractionError("hash_mismatch", "bad hash"))
    )
    assert service.extract_document("D").error_code == "hash_mismatch"


def test_native_low_quality_is_kept_alongside_complementary_ocr(
    sessions, simulated_engine, monkeypatch
):
    from public_procurement.extraction.domain.content import Fragment, ParsedContent

    service = build(sessions)
    native = ParsedContent(
        ExtractionStatus.COMPLETED,
        (Fragment(1, "JUGO HIT X 200 ML", {"kind": "pdf_page", "page_number": 1}, page_number=1),),
        page_count=1,
    )
    monkeypatch.setattr(service.extractor, "extract", lambda document: native)
    result = service.extract_document("D")
    fragments = service.content_for_process("P")[1]
    assert result.diagnostics["coverage_complete"]
    assert [f.source_locator["extraction_method"] for f in fragments] == [
        "native_pdf_text",
        "ocr_text",
    ]
    assert fragments[0].text == native.fragments[0].text
    with sessions() as session:
        import uuid

        from public_procurement.extraction.repositories import SqlExtractionRepository

        original = SqlExtractionRepository(session).fragments(
            uuid.UUID(result.diagnostics["native_run_id"])
        )
    assert original[0].text == native.fragments[0].text


def test_retry_limit_and_new_configuration_identity(sessions, simulated_engine):
    service = build(sessions, policy=OcrPolicy(max_retry_attempts=1))
    simulated_engine.return_value = ("garbage", 0)
    first = service.extract_document("D")
    second = service.extract_document("D", retry_ocr=True)
    assert second.run_id != first.run_id
    exhausted = service.extract_document("D", retry_ocr=True)
    assert exhausted.error_code == "ocr_retry_exhausted"
    assert exhausted.diagnostics["retry_exhausted"]
    service.ocr.policy = OcrPolicy(max_retry_attempts=1, dpi=200)
    changed = service.extract_document("D")
    assert changed.run_id not in (first.run_id, second.run_id)
    assert changed.diagnostics["attempt"] == 0


def test_ocr_failure_does_not_stop_other_documents(sessions, simulated_engine):
    import uuid

    service = build(sessions)
    service.documents.documents.append(
        replace(
            service.documents.documents[0],
            document_id=uuid.uuid4(),
            document_version_id=uuid.uuid4(),
            original_name="second.pdf",
        )
    )
    simulated_engine.side_effect = [RuntimeError("timeout"), (TEXT, 90)]
    results = list(service.extract_process("P"))
    assert not results[0].diagnostics["coverage_complete"]
    assert results[1].diagnostics["coverage_complete"]
    assert service.content_for_process("P")[1]


def test_exhausted_retry_does_not_abort_remaining_documents(sessions, simulated_engine):
    import uuid

    service = build(sessions, policy=OcrPolicy(max_retry_attempts=0))
    service.documents.documents.append(
        replace(
            service.documents.documents[0],
            document_id=uuid.uuid4(),
            document_version_id=uuid.uuid4(),
            original_name="second.pdf",
        )
    )
    simulated_engine.side_effect = [RuntimeError("timeout"), (TEXT, 90)]
    list(service.extract_process("P"))
    results = list(service.extract_process("P", retry_ocr=True))
    assert len(results) == 2
    assert results[0].error_code == "ocr_retry_exhausted"
    assert results[1].diagnostics["coverage_complete"]
    assert simulated_engine.call_count == 2


def test_radar_composes_real_extraction_structured_and_canonical_services(
    sessions, simulated_engine
):
    from public_procurement.eureka.adapters.radar_pipeline import ExistingRadarPipeline

    from ..eureka.test_affinity import details, process

    service = build(sessions)
    with sessions.begin() as session:
        for model in (StructuredFactRecord, CanonicalFactRecord, CanonicalEvidenceRecord):
            model.__table__.create(session.connection())
    structured = StructuredExtractionService(sessions, service)
    canonical = ConsolidationService(sessions, structured)
    ingestion, processes, documents, discovery, detail = (Mock() for _ in range(5))
    detail.get.side_effect = [replace(details(), enrichment_status="not_extracted"), details()]
    documents.sync.return_value = [Mock()]
    documents.list_documents.return_value = [Mock(id="D")]
    documents.latest_version.return_value = Mock()
    pipeline = ExistingRadarPipeline(
        ingestion, processes, documents, service, structured, canonical, discovery, detail
    )
    stages = []
    result = pipeline.enrich(process(), stages.append)
    assert result.score == 65
    assert stages[-2:] == ["structured", "consolidation"]
    assert canonical.show("P").persisted
    assert any(
        f.source_locator["extraction_method"] == "ocr_text"
        for f in service.content_for_process("P")[1]
    )
    discovery.evaluate.assert_not_called()
