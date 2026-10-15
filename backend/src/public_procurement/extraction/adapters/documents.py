import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import BinaryIO

from public_procurement.documents.services import AcquisitionError, Document, DocumentService

from ..domain.content import DocumentInput, ExtractionError


class RegisteredDocumentSource:
    def __init__(self, documents: DocumentService) -> None:
        self.documents = documents

    def process_id(self, reference: str) -> uuid.UUID:
        return self.documents.process_id(reference)

    def _input(self, document: Document) -> DocumentInput:
        version = self.documents.latest_version(document.id)
        if version is None:
            return DocumentInput(document.id, None, document.source.original_name, "", 0)
        return DocumentInput(
            document.id, version.id, version.original_name, version.sha256, version.observed_size
        )

    def for_process(self, reference: str) -> list[DocumentInput]:
        return [self._input(document) for document in self.documents.list_documents(reference)]

    def for_document(self, reference: str) -> DocumentInput:
        return self._input(self.documents.get_document(reference))

    @contextmanager
    def open_version(self, version_id: uuid.UUID, max_bytes: int) -> Iterator[BinaryIO]:
        try:
            with self.documents.open_version(version_id, max_bytes) as file:
                yield file
        except AcquisitionError as exc:
            raise ExtractionError(exc.code, str(exc)) from exc
