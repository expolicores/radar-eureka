from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from public_procurement.eureka.adapters.radar_pipeline import ExistingRadarPipeline

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
