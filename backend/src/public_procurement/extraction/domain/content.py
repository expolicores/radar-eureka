import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExtractionStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_TEXT = "partial_text"
    REQUIRES_OCR = "requires_ocr"
    EMPTY_TEXT = "empty_text"
    FAILED = "failed"


REUSABLE_STATUSES = ("completed", "partial_text", "requires_ocr", "empty_text")
CLAIM_STATUSES = (*REUSABLE_STATUSES, "running")


class ExtractionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ExtractionLimits:
    max_bytes: int = 50 * 1024 * 1024
    timeout_seconds: float = 60
    max_chars: int = 2_000_000
    max_fragments: int = 10_000
    max_pages: int = 300
    fragment_chars: int = 20_000
    max_archive_bytes: int = 100 * 1024 * 1024
    max_archive_entries: int = 5000
    max_cells: int = 100_000


@dataclass(frozen=True)
class DocumentInput:
    document_id: uuid.UUID
    document_version_id: uuid.UUID | None
    original_name: str
    input_sha256: str
    observed_size: int


@dataclass(frozen=True)
class ExtractorIdentity:
    name: str
    version: str


@dataclass(frozen=True)
class Fragment:
    ordinal: int
    text: str
    source_locator: dict[str, Any]
    page_number: int | None = None
    paragraph_number: int | None = None
    table_number: int | None = None
    row_number: int | None = None
    column_number: int | None = None
    sheet_name: str | None = None
    cell_range: str | None = None


@dataclass(frozen=True)
class ParsedContent:
    status: ExtractionStatus
    fragments: tuple[Fragment, ...]
    pages_without_text: tuple[int, ...] = ()
    page_count: int = 0
    format_counts: dict[str, int] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def text_length(self) -> int:
        return sum(len(fragment.text) for fragment in self.fragments)


@dataclass(frozen=True)
class ExtractionResult:
    document: DocumentInput
    extractor: ExtractorIdentity
    status: ExtractionStatus
    run_id: uuid.UUID | None
    fragment_count: int = 0
    text_length: int = 0
    pages_without_text: tuple[int, ...] = ()
    page_count: int = 0
    reused: bool = False
    error_code: str | None = None
    error_message: str | None = None
    fragments: tuple[Fragment, ...] = field(default=(), repr=False)
    format_counts: dict[str, int] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchHit:
    document_version_id: uuid.UUID
    original_name: str
    input_sha256: str
    extraction_run_id: uuid.UUID
    fragment_id: uuid.UUID
    text: str
    source_locator: dict[str, Any]
    context: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class EvidenceFragment:
    id: uuid.UUID
    document_version_id: uuid.UUID
    extraction_run_id: uuid.UUID
    original_name: str
    ordinal: int
    text: str
    source_locator: dict[str, Any]
