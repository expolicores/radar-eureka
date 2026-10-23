import uuid
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from public_procurement.eureka.adapters.radar_pipeline import ExistingRadarPipeline
from public_procurement.extraction.domain.content import (
    DocumentInput,
    ExtractionResult,
    ExtractionStatus,
    ExtractorIdentity,
)

from .test_affinity import details, process


def build():
    services = [Mock() for _ in range(8)]
    pipeline = ExistingRadarPipeline(*services)
    _ingestion, processes, documents, extraction, _structured, _consolidation, eureka, detail = (
        services
    )
    processes.get_process.return_value = SimpleNamespace(id="process")
    detail.get.side_effect = [
        replace(details(), enrichment_status="not_extracted", opportunity_id=None),
        details(),
    ]
    documents.sync.return_value = [Mock()]
    documents.list_documents.return_value = [SimpleNamespace(id="document")]
    documents.latest_version.return_value = None
    documents.download.return_value = SimpleNamespace(failed=0)
    extraction.extract_process.return_value = [
        SimpleNamespace(error_code=None, status="completed", diagnostics={})
    ]
    eureka.evaluate.return_value = []
    return pipeline, services


def test_existing_pipeline_composes_public_services_in_order():
    pipeline, services = build()
    stages = []
    result = pipeline.enrich(process(), stages.append)
    assert result.score == 65
    assert stages == [
        "ingestion",
        "discovery",
        "documents_sync",
        "documents_download",
        "extraction",
        "structured",
        "consolidation",
    ]
    services[0].persist.assert_called_once()
    services[6].evaluate.assert_called_once()
    services[4].extract.assert_called_once()
    services[5].run.assert_called_once()


def test_download_failure_prevents_extraction_and_remains_retryable():
    pipeline, services = build()
    services[2].download.return_value.failed = 1
    with pytest.raises(ValueError, match="Adquisición incompleta"):
        pipeline.enrich(process(), lambda stage: None)
    services[3].extract_process.assert_not_called()
    services[5].run.assert_not_called()


def test_empty_inventory_returns_metadata_only_without_extracting_or_rescoring():
    pipeline, services = build()
    services[2].sync.return_value = []
    existing = replace(details(), enrichment_status="not_extracted", quality={})
    services[7].get.side_effect = [existing, existing]
    result = pipeline.enrich(process(), lambda stage: None)
    assert result.opportunity_id == existing.opportunity_id
    assert result.score == existing.score
    assert result.quality["evidence_level"] == "metadata_only"
    assert result.quality["document_status"] == "unavailable"
    assert result.enrichment_status == "documents_unavailable"
    services[2].sync.assert_called_once()
    services[2].download.assert_not_called()
    services[3].extract_process.assert_not_called()
    services[6].evaluate.assert_not_called()


def test_inventory_transport_error_is_not_converted_into_metadata_only():
    pipeline, services = build()
    services[2].sync.side_effect = RuntimeError("Socrata unavailable")
    with pytest.raises(RuntimeError, match="Socrata unavailable"):
        pipeline.enrich(process(), lambda stage: None)


def test_existing_canonical_state_reuses_score_without_discovery_or_download():
    pipeline, services = build()
    services[7].get.side_effect = None
    services[7].get.return_value = details()
    assert pipeline.enrich(process(), lambda stage: None).score == 65
    services[6].evaluate.assert_not_called()
    services[2].download.assert_not_called()


def test_incomplete_extraction_continues_with_usable_evidence_and_records_stage():
    pipeline, services = build()
    services[3].extract_process.return_value = [
        SimpleNamespace(
            error_code="ocr_unavailable",
            status="partial_text",
            diagnostics={
                "status": "ocr_truncated",
                "coverage_complete": False,
            },
        ),
    ]
    services[3].content_for_process.return_value = ("P", [Mock()])
    stages = []
    assert pipeline.enrich(process(), stages.append).score == 65
    assert "extraction_partial" in stages
    services[4].extract.assert_called_once()
    services[5].run.assert_called_once()


def test_incomplete_extraction_without_any_evidence_remains_retryable():
    pipeline, services = build()
    services[3].extract_process.return_value = [
        SimpleNamespace(
            error_code=None,
            status="requires_ocr",
            diagnostics={
                "status": "ocr_unavailable",
                "coverage_complete": False,
            },
        ),
    ]
    services[3].content_for_process.return_value = ("P", [])
    with pytest.raises(ValueError, match="sin evidencia útil"):
        pipeline.enrich(process(), lambda stage: None)
    services[4].extract.assert_not_called()


@pytest.mark.parametrize(
    ("status", "length", "error", "expected"),
    [
        (ExtractionStatus.COMPLETED, 30, None, True),
        (ExtractionStatus.PARTIAL_TEXT, 30, None, True),
        (ExtractionStatus.FAILED, 0, "unsupported_format", False),
        (ExtractionStatus.REQUIRES_OCR, 0, None, False),
        (ExtractionStatus.COMPLETED, 0, None, False),
    ],
)
def test_result_observation_distinguishes_usable_text_from_failed_or_empty(
    status, length, error, expected
):
    pipeline, services = build()
    observer = Mock()
    pipeline.observer = observer
    services[2].download.return_value = SimpleNamespace(available=1, failed=0)
    result = ExtractionResult(
        DocumentInput(uuid.uuid4(), uuid.uuid4(), "name", "hash", 5),
        ExtractorIdentity("pdf-text", "v1"),
        status,
        None,
        fragment_count=int(length > 0),
        text_length=length,
        error_code=error,
    )
    services[3].extract_process.return_value = [result]
    services[3].content_for_process.return_value = ("P", [Mock()])
    pipeline.enrich(process(), lambda stage: None)
    payload = next(
        call.args[1] for call in observer.call_args_list if call.args[0] == "extraction_result"
    )
    assert payload["succeeded"] is expected
    assert payload["error_code"] == error
    assert payload["text_length"] == length
