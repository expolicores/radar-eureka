import uuid
from dataclasses import replace
from unittest.mock import Mock

from public_procurement.eureka.adapters.extraction import ExtractionCanonicalSource
from public_procurement.eureka.adapters.ingestion import IngestionProcessSource
from public_procurement.extraction.consolidation import consolidate
from public_procurement.extraction.services import CanonicalReadState
from public_procurement.ingestion.services import StoredSecopProcess

from ..extraction.test_consolidation import PROCESS, product
from .test_affinity import process


def test_ingestion_header_preserves_reference_description_and_original_url():
    metadata = replace(
        process(),
        reference="RESO-006-2026",
        description="TEXTO; original\nlínea 2",
        source_url="https://community.secop.gov.co/Public/?noticeUID=original",
    )
    service = Mock()
    service.iter_processes.return_value = iter([StoredSecopProcess(uuid.uuid4(), metadata)])
    header = IngestionProcessSource(service).header(metadata.id_del_proceso)
    assert header["reference"] == metadata.reference
    assert header["description"] == metadata.description
    assert header["source_url"] == metadata.source_url
    assert header["secop_id"] == metadata.id_del_proceso
    service.iter_processes.assert_called_once_with(reference=metadata.id_del_proceso)


def test_adapter_reads_public_extraction_service_and_does_not_invoke_writers():
    service = Mock()
    summary = consolidate(PROCESS, [product("Hit")])
    service.read_state.return_value = CanonicalReadState("consolidated", summary)
    adapter = ExtractionCanonicalSource(service)
    result = adapter.read("P")
    assert result.facts[0].id == summary.facts[0].id
    assert result.status == "consolidated"
    service.read_state.assert_called_once_with("P")
    service.run.assert_not_called()
    service.show.assert_not_called()


def test_adapter_evidence_retains_version_locator_and_rule():
    service = Mock()
    source = product("Hit")
    service.evidence.return_value = [source]
    adapter = ExtractionCanonicalSource(service)
    result = adapter.evidence("P", source.id)
    assert result[0]["document_version_id"] == str(source.document_version_id)
    assert result[0]["source_locator"] == source.source_locator
    assert result[0]["evidence_text"] == source.evidence_text
