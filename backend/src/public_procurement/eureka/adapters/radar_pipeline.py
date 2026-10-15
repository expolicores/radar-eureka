"""Pipeline Radar sobre puertas públicas existentes; sin SQL ni nuevas reglas de extracción."""

import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from public_procurement.documents.services import DocumentService
from public_procurement.extraction.services import (
    ConsolidationService,
    ExtractionService,
    StructuredExtractionService,
)
from public_procurement.ingestion.services import (
    ProcessIngestionService,
    ProcessQuery,
    ProcessQueryService,
    SecopProcess,
)

from ..domain.details import EurekaOpportunityDetails

if TYPE_CHECKING:
    from ..services import EurekaDetailsService, EurekaService


class ExistingRadarPipeline:
    def __init__(
        self,
        ingestion: ProcessIngestionService,
        processes: ProcessQueryService,
        documents: DocumentService,
        extraction: ExtractionService,
        structured: StructuredExtractionService,
        consolidation: ConsolidationService,
        eureka: "EurekaService",
        details: "EurekaDetailsService",
        observer: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.ingestion, self.processes, self.documents = ingestion, processes, documents
        self.extraction, self.structured, self.consolidation = extraction, structured, consolidation
        self.eureka, self.details = eureka, details
        self.observer = observer

    def enrich(
        self, process: SecopProcess, stage: Callable[[str], None]
    ) -> EurekaOpportunityDetails:
        reference = process.id_del_proceso
        stage("ingestion")
        self.ingestion.persist([process], ProcessQuery(portfolio_id=process.id_del_portafolio))
        stage("discovery")
        # Existing opportunities retain their exact score and scoring version.
        current = self.preview(reference)
        if current is None or current.opportunity_id is None:
            list(self.eureka.evaluate(reference=reference))
        if (
            current is not None
            and current.enrichment_status in ("consolidated", "conflict")
            and current.quality.get("extraction_coverage", {}).get("coverage_complete") is not False
        ):
            stage("canonical_reused")
            return self.details.get(reference)
        stage("documents_sync")
        inventory = self.documents.sync(reference)
        if self.observer:
            self.observer("documents", {"count": len(inventory)})
        if not inventory:
            raise ValueError("No hay inventario documental; el proceso queda reintentable.")
        stage("documents_download")
        documents = self.documents.list_documents(reference)
        if any(self.documents.latest_version(document.id) is None for document in documents):
            download = self.documents.download(reference)
            if self.observer:
                self.observer(
                    "document_download",
                    {"available": download.available, "failed": download.failed},
                )
            if download.failed:
                raise ValueError(f"Adquisición incompleta: {download.failed} documentos fallidos.")
        elif self.observer:
            self.observer(
                "document_download", {"available": len(documents), "failed": 0, "reused": True}
            )
        stage("extraction")
        results = list(self.extraction.extract_process(reference, retry_ocr=True))
        if self.observer:
            for result in results:
                self.observer(
                    "extraction_result",
                    {
                        "ocr": result.diagnostics.get("status"),
                        "required": len(result.diagnostics.get("required_pages", [])),
                        "processed": 0
                        if result.reused
                        else len(result.diagnostics.get("processed_pages", [])),
                        "native": not result.reused
                        and any(
                            f.source_locator.get("extraction_method") != "ocr_text"
                            for f in result.fragments
                        ),
                        "reused": result.reused,
                        "failed": bool(result.error_code),
                        "ocr_seconds": 0
                        if result.reused
                        else result.diagnostics.get("elapsed_seconds", 0),
                    },
                )
        if any(
            result.error_code
            or str(result.status) == "running"
            or result.diagnostics.get("coverage_complete") is False
            for result in results
        ):
            stage("extraction_partial")
            _, fragments = self.extraction.content_for_process(reference)
            if not fragments:
                raise ValueError("Extracción incompleta sin evidencia útil; proceso reintentable.")
        stage("structured")
        self.structured.extract(reference)
        stage("consolidation")
        self.consolidation.run(reference)
        if self.observer:
            self.observer("consolidated", {})
        return self.details.get(reference)

    def preview(self, reference: str) -> EurekaOpportunityDetails | None:
        if self.processes.get_process(reference) is None:
            return None
        return self.details.get(reference)

    def evidence(self, reference: str, canonical_id: uuid.UUID) -> list[dict[str, Any]]:
        return self.details.evidence(reference, canonical_id)
