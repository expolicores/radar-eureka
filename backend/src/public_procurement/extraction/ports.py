import uuid
from contextlib import AbstractContextManager
from typing import BinaryIO, Protocol

from .domain.content import DocumentInput, ExtractorIdentity, ParsedContent


class DocumentSource(Protocol):
    def process_id(self, reference: str) -> uuid.UUID: ...

    def for_process(self, reference: str) -> list[DocumentInput]: ...
    def for_document(self, reference: str) -> DocumentInput: ...
    def open_version(
        self, version_id: uuid.UUID, max_bytes: int
    ) -> AbstractContextManager[BinaryIO]: ...


class ContentExtractor(Protocol):
    def identity(self, document: DocumentInput) -> ExtractorIdentity: ...
    def extract(self, document: DocumentInput) -> ParsedContent: ...
