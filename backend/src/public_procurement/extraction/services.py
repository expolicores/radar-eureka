"""Extracción y búsqueda compartidas: no modifica scoring de Eureka ni tablas documentales."""

import uuid
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.documents.services import build_document_service
from public_procurement.shared.config import Settings

from .adapters.documents import RegisteredDocumentSource
from .adapters.hybrid import LocalOcrFallback, native_quality
from .adapters.isolated import IsolatedExtractor
from .canonical_repositories import SqlCanonicalRepository
from .consolidation import consolidate, digest_inputs
from .domain.canonical import (
    CONSOLIDATION_VERSION,
    REQUIRED_TYPES,
    CanonicalFact,
    CanonicalReadState,
    CanonicalSummary,
)
from .domain.content import (
    REUSABLE_STATUSES,
    DocumentInput,
    EvidenceFragment,
    ExtractionError,
    ExtractionLimits,
    ExtractionResult,
    ExtractionStatus,
    SearchHit,
)
from .domain.structured import RULE_VERSION, StructuredFact
from .domain.text import normalize_extracted_text
from .ocr_config import load_ocr_policy
from .ports import ContentExtractor, DocumentSource
from .repositories import SqlExtractionRepository
from .structured_repositories import SqlStructuredRepository
from .structured_rules import extract_facts

__all__ = [
    "TV_RESEARCH_CANONICAL_VERSION",
    "CanonicalFact",
    "CanonicalReadState",
    "CanonicalSummary",
    "ConsolidationService",
    "ExtractionResult",
    "ExtractionService",
    "SearchHit",
    "StructuredExtractionService",
    "StructuredFact",
    "build_consolidation_service",
    "build_extraction_service",
    "build_structured_service",
    "build_tv_research_structured_service",
    "extraction_metrics",
]

TV_RESEARCH_CANONICAL_VERSION = "canonical-tv-research-v3"


def extraction_metrics(results: list[ExtractionResult]) -> dict[str, int | float]:
    diagnostics = [r.diagnostics for r in results]
    return {
        "documents_processed": len(results),
        "native_pdf_sufficient": sum(d.get("status") == "native_success" for d in diagnostics),
        "documents_requiring_ocr": sum(
            bool(d.get("required_pages")) or str(d.get("status", "")).startswith("ocr_")
            for d in diagnostics
        ),
        "ocr_pages_required": sum(len(d.get("required_pages", [])) for d in diagnostics),
        "ocr_pages_processed": sum(len(d.get("processed_pages", [])) for d in diagnostics),
        "ocr_pages_successful": sum(len(d.get("successful_pages", [])) for d in diagnostics),
        "ocr_pages_failed": sum(
            p.get("status") == "ocr_failed" for d in diagnostics for p in d.get("pages", [])
        ),
        "ocr_pages_omitted": sum(len(d.get("omitted_pages", [])) for d in diagnostics),
        "ocr_unavailable_documents": sum(d.get("status") == "ocr_unavailable" for d in diagnostics),
        "incomplete_documents": sum(d.get("coverage_complete") is False for d in diagnostics),
        "ocr_elapsed_seconds": round(
            sum(float(d.get("elapsed_seconds", 0)) for d in diagnostics), 3
        ),
    }


class ExtractionService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        documents: DocumentSource,
        extractor: ContentExtractor,
        limits: ExtractionLimits,
        ocr: LocalOcrFallback | None = None,
    ) -> None:
        self.sessions, self.documents, self.extractor, self.limits = (
            sessions,
            documents,
            extractor,
            limits,
        )

        self.ocr = ocr

    def _extract(
        self,
        document: DocumentInput,
        dry_run: bool,
        *,
        no_ocr: bool = False,
        force_ocr: bool = False,
        retry_ocr: bool = False,
    ) -> ExtractionResult:
        if force_ocr and not dry_run:
            raise ValueError("--force-ocr requiere --dry-run: diagnóstico sin sustituir evidencia.")
        if no_ocr and (force_ocr or retry_ocr):
            raise ValueError("--no-ocr es incompatible con force/retry OCR.")
        native = self._perform(document, dry_run, self.extractor)
        if no_ocr or self.ocr is None or native.extractor.name != "pdf-text":
            return native
        if native.run_id and not native.fragments and native.fragment_count:
            with self.sessions() as session:
                native = replace(
                    native, fragments=SqlExtractionRepository(session).fragments(native.run_id)
                )
        hybrid = self.ocr.prepare(native, force_ocr)
        if hybrid is None:
            return replace(
                native,
                diagnostics={
                    **native.diagnostics,
                    "status": "native_success"
                    if native.status is ExtractionStatus.COMPLETED
                    else native.status.value,
                    "coverage_complete": native.status is ExtractionStatus.COMPLETED,
                    "native_quality": native_quality(native, self.ocr.policy),
                    "config_hash": self.ocr.policy.digest,
                },
            )
        if not dry_run:
            with self.sessions() as session:
                repository = SqlExtractionRepository(session)
                if not repository.has_table("extraction_run_diagnostic"):
                    return replace(
                        native,
                        diagnostics={
                            "status": "ocr_migration_required",
                            "coverage_complete": False,
                            "error_code": "ocr_migration_required",
                            "error_message": (
                                "Persistir OCR requiere 0013_ocr_diagnostics; "
                                "no aplicada automáticamente."
                            ),
                        },
                    )
                attempts = repository.ocr_attempts(document, hybrid.prefix)
            if attempts:
                latest = attempts[-1]
                hybrid.attempt = int(latest.extractor.version.rsplit("-a", 1)[1])
                if (
                    retry_ocr
                    and latest.status is not ExtractionStatus.RUNNING
                    and not latest.diagnostics.get("coverage_complete")
                ):
                    hybrid.attempt += 1
                    if hybrid.attempt > self.ocr.policy.max_retry_attempts:
                        return replace(
                            latest,
                            error_code="ocr_retry_exhausted",
                            error_message=(
                                "Límite OCR agotado; revise configuración o versión de política."
                            ),
                            diagnostics={**latest.diagnostics, "retry_exhausted": True},
                        )
        return self._perform(document, dry_run, hybrid)

    def _perform(
        self, document: DocumentInput, dry_run: bool, extractor: ContentExtractor
    ) -> ExtractionResult:
        identity = extractor.identity(document)
        if document.document_version_id is None:
            return ExtractionResult(
                document,
                identity,
                ExtractionStatus.FAILED,
                None,
                error_code="not_downloaded",
                error_message="El documento no tiene una versión descargada.",
            )
        if not dry_run:
            with self.sessions.begin() as session:
                claimed = SqlExtractionRepository(session).claim(
                    document, identity, datetime.now(UTC)
                )
            if claimed.reused:
                if claimed.status is ExtractionStatus.RUNNING:
                    return claimed
                try:
                    with self.documents.open_version(
                        document.document_version_id, self.limits.max_bytes
                    ):
                        pass
                except ExtractionError as error:
                    with self.sessions.begin() as session:
                        return SqlExtractionRepository(session).record_validation_failure(
                            document, identity, datetime.now(UTC), error.code, str(error)
                        )
                return claimed
        parsed = None
        error_code = error_message = None
        try:
            parsed = extractor.extract(document)
        except ExtractionError as error:
            error_code, error_message = error.code, str(error)
        except (OSError, ValueError):
            error_code, error_message = (
                "input_error",
                "No fue posible procesar la entrada documental.",
            )
        if dry_run:
            return ExtractionResult(
                document,
                identity,
                parsed.status if parsed else ExtractionStatus.FAILED,
                None,
                len(parsed.fragments) if parsed else 0,
                parsed.text_length if parsed else 0,
                parsed.pages_without_text if parsed else (),
                parsed.page_count if parsed else 0,
                error_code=error_code,
                error_message=error_message,
                fragments=parsed.fragments if parsed else (),
                format_counts=parsed.format_counts if parsed else {},
                diagnostics=parsed.diagnostics if parsed else {},
            )
        if claimed.run_id is None:
            raise ValueError("Extracción sin identificador de intento.")
        with self.sessions.begin() as session:
            return SqlExtractionRepository(session).finish(
                claimed.run_id, document, parsed, datetime.now(UTC), error_code, error_message
            )

    def extract_process(
        self,
        reference: str,
        dry_run: bool = False,
        *,
        no_ocr: bool = False,
        retry_ocr: bool = False,
    ) -> Iterator[ExtractionResult]:
        for document in self.documents.for_process(reference):
            yield self._extract(document, dry_run, no_ocr=no_ocr, retry_ocr=retry_ocr)

    def extract_document(
        self,
        reference: str,
        dry_run: bool = False,
        *,
        no_ocr: bool = False,
        force_ocr: bool = False,
        retry_ocr: bool = False,
    ) -> ExtractionResult:
        return self._extract(
            self.documents.for_document(reference),
            dry_run,
            no_ocr=no_ocr,
            force_ocr=force_ocr,
            retry_ocr=retry_ocr,
        )

    def coverage_for_process(self, reference: str) -> dict[str, Any]:
        documents = self.documents.for_process(reference)
        latest = {run.document.document_version_id: run for run in self.list_extractions(reference)}
        diagnostics = []
        for document in documents:
            run = latest.get(document.document_version_id)
            if (
                run
                and self.ocr
                and run.extractor.name in {"pdf-text", "pdf-hybrid-local"}
                and "coverage_complete" not in run.diagnostics
            ):
                if run.run_id and run.fragment_count:
                    with self.sessions() as session:
                        run = replace(
                            run, fragments=SqlExtractionRepository(session).fragments(run.run_id)
                        )
                quality = native_quality(run, self.ocr.policy)
                required = [page["page_number"] for page in quality if page["ocr_required"]]
                run = replace(
                    run,
                    diagnostics={
                        **run.diagnostics,
                        "native_quality": quality,
                        "status": "ocr_required" if required else run.status.value,
                        "required_pages": required,
                        "coverage_complete": run.status is ExtractionStatus.COMPLETED
                        and not required,
                        "config_hash": self.ocr.policy.digest,
                    },
                )
            diagnostics.append(
                {
                    "document_id": str(document.document_id),
                    "document_version_id": str(document.document_version_id),
                    "original_name": document.original_name,
                    "coverage_complete": bool(
                        run
                        and run.diagnostics.get(
                            "coverage_complete", run.status is ExtractionStatus.COMPLETED
                        )
                    ),
                    "diagnostics": run.diagnostics if run else {"status": "not_extracted"},
                }
            )
        return {
            "coverage_complete": bool(documents)
            and all(d["coverage_complete"] for d in diagnostics),
            "documents": diagnostics,
        }

    def list_extractions(self, reference: str) -> list[ExtractionResult]:
        """Consulta intentos históricos de las versiones vigentes, sin ejecutar lectores."""
        documents = self.documents.for_process(reference)
        with self.sessions() as session:
            return SqlExtractionRepository(session).list_runs(documents)

    def content_for_process(self, reference: str) -> tuple[uuid.UUID, list[EvidenceFragment]]:
        process_id = self.documents.process_id(reference)
        versions = [
            d.document_version_id
            for d in self.documents.for_process(reference)
            if d.document_version_id is not None
        ]
        with self.sessions() as session:
            return process_id, SqlExtractionRepository(session).evidence(versions)

    def search(self, reference: str, term: str, limit: int = 50) -> list[SearchHit]:
        needle = normalize_extracted_text(term)
        if not needle or len(needle) > 200 or not 1 <= limit <= 100:
            raise ValueError("Término de búsqueda o límite inválido.")
        versions = [
            d.document_version_id
            for d in self.documents.for_process(reference)
            if d.document_version_id is not None
        ]
        with self.sessions() as session:
            return SqlExtractionRepository(session).search(versions, needle, limit)


def build_extraction_service(
    sessions: sessionmaker[Session],
    settings: Settings,
    *,
    document_service: Any = None,
    ocr_page_limit: int | None = None,
) -> ExtractionService:
    limits = ExtractionLimits(
        max_bytes=settings.extraction_max_bytes,
        timeout_seconds=settings.extraction_timeout_seconds,
        max_chars=settings.extraction_max_chars,
        max_fragments=settings.extraction_max_fragments,
        max_pages=settings.extraction_max_pages,
    )
    documents = RegisteredDocumentSource(
        document_service
        if document_service is not None
        else build_document_service(sessions, settings)
    )
    policy = (
        load_ocr_policy(settings.extraction_ocr_config_path)
        if settings.extraction_ocr_enabled
        else None
    )
    if policy is not None and ocr_page_limit is not None:
        policy = policy.model_copy(
            update={"max_ocr_pages": min(policy.max_ocr_pages, ocr_page_limit)}
        )
    ocr = (
        LocalOcrFallback(
            documents,
            limits,
            policy,
            settings.extraction_tesseract_cmd,
            settings.extraction_tessdata_path,
        )
        if policy is not None
        else None
    )
    return ExtractionService(sessions, documents, IsolatedExtractor(documents, limits), limits, ocr)


class StructuredExtractionService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        content: ExtractionService,
        rule_version: str = RULE_VERSION,
        rule_set: Callable[
            [uuid.UUID, list[EvidenceFragment], str], list[StructuredFact]
        ] = extract_facts,
    ) -> None:
        self.sessions, self.content, self.rule_version = sessions, content, rule_version
        self.rule_set = rule_set

    def extract(self, reference: str, dry_run: bool = False) -> tuple[list[StructuredFact], int]:
        process_id, fragments = self.content.content_for_process(reference)
        if not fragments:
            raise ValueError("No hay fragmentos persistidos: ejecute extract-documents primero.")
        facts = self.rule_set(process_id, fragments, self.rule_version)
        inserted = 0
        if not dry_run:
            with self.sessions.begin() as session:
                inserted = SqlStructuredRepository(session).save(facts, datetime.now(UTC))
        return facts, inserted

    def list_facts(self, reference: str, *, include_history: bool = False) -> list[StructuredFact]:
        process_id = self.content.documents.process_id(reference)
        with self.sessions() as session:
            facts = SqlStructuredRepository(session).list_facts(
                process_id,
                None if include_history else self.rule_version,
            )
        if include_history:
            return facts
        _, fragments = self.content.content_for_process(reference)
        current_ids = {str(fragment.id) for fragment in fragments}
        return [
            fact
            for fact in facts
            if all(
                source["content_fragment_id"] in current_ids
                for source in fact.source_locator["sources"]
            )
        ]


def build_structured_service(
    sessions: sessionmaker[Session],
    settings: Settings,
) -> StructuredExtractionService:
    return StructuredExtractionService(sessions, build_extraction_service(sessions, settings))


def build_tv_research_structured_service(
    sessions: sessionmaker[Session], settings: Settings, *, content: ExtractionService | None = None
) -> StructuredExtractionService:
    """Explicit research rule set, keeping Radar's default structured-v1 unchanged."""
    from .research_tv_rules import RESEARCH_TV_RULE_VERSION, extract_tv_research_facts

    return StructuredExtractionService(
        sessions,
        content if content is not None else build_extraction_service(sessions, settings),
        RESEARCH_TV_RULE_VERSION,
        extract_tv_research_facts,
    )


class ConsolidationService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        structured: StructuredExtractionService,
        rule_version: str = CONSOLIDATION_VERSION,
    ) -> None:
        self.sessions, self.structured, self.rule_version = sessions, structured, rule_version

    def run(self, reference: str, dry_run: bool = False) -> CanonicalSummary:
        from dataclasses import replace

        process_id = self.structured.content.documents.process_id(reference)
        sources = self.structured.list_facts(reference)
        if not sources:
            raise ValueError(
                "No hay hechos estructurados vigentes; ejecute extract-structured primero."
            )
        summary = consolidate(process_id, sources, self.rule_version)
        if dry_run:
            return summary
        with self.sessions.begin() as session:
            inserted = SqlCanonicalRepository(session).save(summary.facts, datetime.now(UTC))
        return replace(summary, inserted=inserted, persisted=True)

    def show(self, reference: str) -> CanonicalSummary:
        process_id = self.structured.content.documents.process_id(reference)
        sources = self.structured.list_facts(reference)
        digest = digest_inputs(sources)
        with self.sessions() as session:
            facts = SqlCanonicalRepository(session).list_facts(
                process_id, self.rule_version, digest
            )
        return CanonicalSummary(
            facts,
            len(sources),
            tuple(
                kind for kind in REQUIRED_TYPES if not any(f.canonical_type == kind for f in facts)
            ),
            persisted=bool(facts),
        )

    def evidence(self, reference: str, canonical_id: uuid.UUID) -> list[StructuredFact]:
        process_id = self.structured.content.documents.process_id(reference)
        with self.sessions() as session:
            return SqlCanonicalRepository(session).evidence(process_id, canonical_id)

    def history(self, reference: str) -> tuple[CanonicalFact, ...]:
        process_id = self.structured.content.documents.process_id(reference)
        with self.sessions() as session:
            return SqlCanonicalRepository(session).list_facts(process_id)

    def read_state(self, reference: str) -> CanonicalReadState:
        """Lectura progresiva compatible con fases anteriores; nunca ejecuta escritores."""
        content = self.structured.content
        content.documents.process_id(reference)
        empty = CanonicalSummary((), 0, REQUIRED_TYPES)
        with content.sessions() as session:
            repository = SqlExtractionRepository(session)
            tables = {
                name: repository.has_table(name)
                for name in (
                    "extraction_run",
                    "content_fragment",
                    "structured_fact",
                    "canonical_fact",
                    "canonical_fact_evidence",
                )
            }
        if not tables["extraction_run"] or not tables["content_fragment"]:
            return CanonicalReadState("not_extracted", empty)
        runs = content.list_extractions(reference)
        if not any(run.status.value in REUSABLE_STATUSES for run in runs):
            return CanonicalReadState("not_extracted", empty)
        if not tables["structured_fact"]:
            return CanonicalReadState("extracted", empty)
        sources = self.structured.list_facts(reference)
        if not sources:
            return CanonicalReadState("extracted", empty)
        partial = CanonicalSummary((), len(sources), REQUIRED_TYPES)
        if not tables["canonical_fact"] or not tables["canonical_fact_evidence"]:
            return CanonicalReadState("structured", partial)
        summary = self.show(reference)
        if not summary.persisted:
            return CanonicalReadState("structured", partial)
        return CanonicalReadState("conflict" if summary.conflicts else "consolidated", summary)


def build_consolidation_service(
    sessions: sessionmaker[Session],
    settings: Settings,
) -> ConsolidationService:
    return ConsolidationService(sessions, build_structured_service(sessions, settings))


def search_extraction_candidates(session: Session, query: str) -> set[uuid.UUID]:
    from .search_queries import candidates

    return candidates(session, query)


def search_extraction_snapshots(
    session: Session, process_ids: list[uuid.UUID], query: dict[str, str] | None
) -> dict[uuid.UUID, dict[str, Any]]:
    from .search_queries import snapshots

    return snapshots(session, process_ids, query)


def search_extraction_evidence(
    session: Session,
    process_id: uuid.UUID,
    canonical_id: uuid.UUID | None,
    fragment_id: uuid.UUID | None,
) -> list[dict[str, Any]]:
    from .search_queries import evidence

    return evidence(session, process_id, canonical_id, fragment_id)


def ocr_runtime_status(settings: Settings) -> dict[str, Any]:
    """Read-only engine probe exposed through the extraction boundary."""
    from .adapters.ocr import probe_engine
    from .ocr_config import load_ocr_policy

    if not settings.extraction_ocr_enabled:
        return {"available": False, "status": "disabled"}
    result = probe_engine(
        settings.extraction_tesseract_cmd,
        settings.extraction_tessdata_path,
        load_ocr_policy(settings.extraction_ocr_config_path),
    )
    return {
        key: result.get(key) for key in ("available", "engine_version", "language", "error_code")
    }
