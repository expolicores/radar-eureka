"""Servicios compartidos: inventario y adquisición, sin HTTP dentro de transacciones."""

import uuid
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Any, BinaryIO, Protocol

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.ingestion.services import ProcessReference, build_process_query_service
from public_procurement.shared.config import Settings

from .adapters.local_storage import LocalBinaryStorage
from .adapters.secop import SecopDownloader
from .adapters.socrata import SocrataDocumentSource
from .domain.document import (
    AcquisitionError,
    Document,
    DocumentVersion,
    DownloadSummary,
    SourceDocument,
)
from .ports import BinaryStorage, DocumentDownloader, DocumentInventorySource
from .repositories import SqlDocumentRepository

__all__ = [
    "AcquisitionError",
    "Document",
    "DocumentService",
    "DocumentVersion",
    "DownloadSummary",
    "build_document_service",
]


class ProcessLookup(Protocol):
    def get_process(self, reference: str) -> ProcessReference | None: ...


class DocumentService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        processes: ProcessLookup,
        inventory: DocumentInventorySource,
        downloader: DocumentDownloader,
        storage: BinaryStorage,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.sessions, self.processes = sessions, processes
        self.inventory, self.downloader, self.storage = inventory, downloader, storage
        self.clock = clock

    def _resolve_process(self, reference: str) -> ProcessReference:
        process = self.processes.get_process(reference)
        if process is None:
            raise ValueError("Proceso persistido no encontrado.")
        return process

    def _process(self, reference: str) -> ProcessReference:
        process = self._resolve_process(reference)
        if not process.portfolio_id:
            raise ValueError("El proceso no tiene portafolio publicado.")
        return process

    def list_documents(self, reference: str) -> list[Document]:
        process = self._resolve_process(reference)
        if not process.portfolio_id:
            return []
        with self.sessions() as session:
            return SqlDocumentRepository(session).list_for(process.id, process.portfolio_id or "")

    def versions(self, document_id: uuid.UUID) -> list[DocumentVersion]:
        with self.sessions() as session:
            return SqlDocumentRepository(session).versions(document_id)

    def get_document(self, reference: str) -> Document:
        with self.sessions() as session:
            document = SqlDocumentRepository(session).find_document(reference)
        if document is None:
            raise ValueError("Documento registrado no encontrado.")
        return document

    def process_id(self, reference: str) -> uuid.UUID:
        return self._resolve_process(reference).id

    def latest_version(self, document_id: uuid.UUID) -> DocumentVersion | None:
        with self.sessions() as session:
            return SqlDocumentRepository(session).latest_version(document_id)

    def open_version(
        self, version_id: uuid.UUID, max_bytes: int
    ) -> AbstractContextManager[BinaryIO]:
        with self.sessions() as session:
            version = SqlDocumentRepository(session).get_version(version_id)
        if version is None:
            raise ValueError("Versión documental no encontrada.")
        return self.storage.open_verified(
            version.storage_path, version.sha256, version.observed_size, max_bytes
        )

    def sync(self, reference: str, dry_run: bool = False) -> list[SourceDocument]:
        process = self._process(reference)
        portfolio = process.portfolio_id
        if portfolio is None:
            raise ValueError("Portafolio ausente.")
        received = self.inventory.fetch(portfolio)
        unique: dict[tuple[str, str], SourceDocument] = {}
        for source in received:
            if source.portfolio_id != portfolio:
                raise ValueError("Documento de otro portafolio.")
            key = source.dataset_id, source.id_documento
            if key in unique and unique[key] != source:
                raise ValueError("Inventario documental contradictorio.")
            unique[key] = source
        documents = list(unique.values())
        if not dry_run:
            with self.sessions.begin() as session:
                repository = SqlDocumentRepository(session)
                for document in documents:
                    repository.sync(process.id, document, self.clock())
        return documents

    def download(self, reference: str) -> DownloadSummary:
        process = self._process(reference)
        portfolio = process.portfolio_id
        if portfolio is None:
            raise ValueError("Portafolio ausente.")
        with self.sessions() as session:
            documents = SqlDocumentRepository(session).list_for(process.id, portfolio)
        available = failed = 0
        for document in documents:
            with self.sessions.begin() as session:
                attempt = SqlDocumentRepository(session).start_attempt(document, self.clock())
            binary, error_code, message = None, None, None
            try:
                binary = self.downloader.download(document.source, self.storage)
            except AcquisitionError as error:
                error_code, message = error.code, str(error)
            except OSError:
                error_code, message = (
                    "storage_error",
                    "No fue posible completar el almacenamiento local.",
                )
            with self.sessions.begin() as session:
                succeeded = SqlDocumentRepository(session).finish(
                    document, attempt, self.clock(), binary, error_code, message
                )
            if not succeeded:
                failed += 1
            else:
                available += 1
        return DownloadSummary(available, failed)


def build_document_service(sessions: sessionmaker[Session], settings: Settings) -> DocumentService:
    return DocumentService(
        sessions,
        build_process_query_service(sessions),
        SocrataDocumentSource(),
        SecopDownloader(settings.document_timeout_seconds, settings.document_max_bytes),
        LocalBinaryStorage(settings.local_storage_path),
    )


def document_search_scope(process_ids: list[uuid.UUID] | None = None) -> Any:
    """Read-only SQL scope, owned by documents: current available versions only."""
    from .search_queries import scope

    return scope(process_ids)


def search_processes_for_document_versions(
    session: Session, versions: set[uuid.UUID]
) -> set[uuid.UUID]:
    from .search_queries import process_ids_for_versions

    return process_ids_for_versions(session, versions)
