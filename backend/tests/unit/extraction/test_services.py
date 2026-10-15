import hashlib
import io
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from public_procurement.extraction.domain.content import (
    DocumentInput,
    ExtractionError,
    ExtractionLimits,
    ExtractionStatus,
    ExtractorIdentity,
    Fragment,
    ParsedContent,
)
from public_procurement.extraction.repositories import (
    ContentFragmentRecord,
    ExtractionRunRecord,
    SqlExtractionRepository,
)
from public_procurement.extraction.services import ExtractionService


class Source:
    def __init__(self):
        self.process_identifier = uuid.uuid4()
        self.data = b"registered bytes"
        self.documents = [
            DocumentInput(
                uuid.uuid4(),
                uuid.uuid4(),
                "test.pdf",
                hashlib.sha256(self.data).hexdigest(),
                len(self.data),
            )
        ]

    def for_process(self, reference):
        return self.documents

    def process_id(self, reference):
        return self.process_identifier

    def for_document(self, reference):
        return self.documents[0]

    @contextmanager
    def open_version(self, version_id, max_bytes):
        yield io.BytesIO(self.data)


class Reader:
    def __init__(self):
        self.version = "v1"
        self.calls = 0
        self.failures = 0

    def identity(self, document):
        return ExtractorIdentity("test-reader", self.version)

    def extract(self, document):
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise ExtractionError("corrupt_file", "Archivo corrupto")
        return ParsedContent(
            ExtractionStatus.COMPLETED,
            (
                Fragment(
                    1,
                    "Garantía: Chocorramo y Hit",
                    {"kind": "pdf_page", "page_number": 1},
                    page_number=1,
                ),
            ),
        )


def count(sessions, model):
    with sessions() as session:
        return session.scalar(select(func.count()).select_from(model))


def test_idempotence_and_new_extractor_version_keep_history(sessions) -> None:
    source, reader = Source(), Reader()
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    first = next(service.extract_process("P"))
    repeated = next(service.extract_process("P"))
    assert repeated.reused
    assert repeated.run_id == first.run_id
    assert reader.calls == 1
    reader.version = "v2"
    changed = service.extract_document("D")
    assert changed.run_id != first.run_id
    assert count(sessions, ExtractionRunRecord) == 2
    assert count(sessions, ContentFragmentRecord) == 2
    with sessions() as session:
        fragment = session.scalar(
            select(ContentFragmentRecord).where(
                ContentFragmentRecord.extraction_run_id == first.run_id
            )
        )
        assert fragment.source_locator["document_version_id"] == str(
            source.documents[0].document_version_id
        )
        assert fragment.source_locator["original_name"] == "test.pdf"
        assert fragment.normalized_text == "garantia: chocorramo y hit"
        assert fragment.text == "Garantía: Chocorramo y Hit"


def test_failed_attempt_is_preserved_and_retry_creates_new_run(sessions) -> None:
    source, reader = Source(), Reader()
    reader.failures = 1
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    failed = service.extract_document("D")
    retried = service.extract_document("D")
    assert failed.status is ExtractionStatus.FAILED
    assert failed.run_id != retried.run_id
    assert retried.status is ExtractionStatus.COMPLETED
    with sessions() as session:
        assert session.get(ExtractionRunRecord, failed.run_id).error_code == "corrupt_file"


def test_failure_does_not_stop_batch_and_dry_run_has_no_writes(sessions) -> None:
    source, reader = Source(), Reader()
    source.documents.append(DocumentInput(uuid.uuid4(), uuid.uuid4(), "second.pdf", "a" * 64, 10))
    reader.failures = 1
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    results = list(service.extract_process("P", dry_run=True))
    assert [r.status for r in results] == [ExtractionStatus.FAILED, ExtractionStatus.COMPLETED]
    assert count(sessions, ExtractionRunRecord) == 0
    reader.failures = 1
    results = list(service.extract_process("P"))
    assert [r.status for r in results] == [ExtractionStatus.FAILED, ExtractionStatus.COMPLETED]
    assert count(sessions, ExtractionRunRecord) == 2


def test_new_document_version_gets_new_extraction(sessions) -> None:
    source, reader = Source(), Reader()
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    first = service.extract_document("D")
    old = source.documents[0]
    source.documents[0] = DocumentInput(
        old.document_id, uuid.uuid4(), old.original_name, "b" * 64, 11
    )
    second = service.extract_document("D")
    assert second.run_id != first.run_id
    assert count(sessions, ExtractionRunRecord) == 2


def test_running_claim_prevents_second_reader_and_finalized_run_is_immutable(sessions) -> None:
    source, reader = Source(), Reader()
    document = source.documents[0]
    with sessions.begin() as session:
        first = SqlExtractionRepository(session).claim(
            document, reader.identity(document), datetime.now(UTC)
        )
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    pending = service.extract_document("D")
    assert pending.status is ExtractionStatus.RUNNING
    assert pending.run_id == first.run_id
    assert reader.calls == 0
    with sessions.begin() as session:
        SqlExtractionRepository(session).finish(
            first.run_id, document, reader.extract(document), datetime.now(UTC)
        )
    with sessions.begin() as session, pytest.raises(ValueError, match="finalizada"):
        SqlExtractionRepository(session).finish(first.run_id, document, None, datetime.now(UTC))


def test_reused_result_validates_file_and_keeps_original_evidence(sessions) -> None:
    source, reader = Source(), Reader()
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    first = service.extract_document("D")

    @contextmanager
    def invalid_file(version_id, max_bytes):
        raise ExtractionError("hash_mismatch", "Archivo modificado")
        yield  # pragma: no cover - context manager contract

    source.open_version = invalid_file
    failed = service.extract_document("D")
    assert failed.error_code == "hash_mismatch"
    assert failed.run_id != first.run_id
    assert count(sessions, ExtractionRunRecord) == 2
    assert count(sessions, ContentFragmentRecord) == 1
    with sessions() as session:
        assert session.get(ExtractionRunRecord, first.run_id).status == "completed"


def test_listing_extractions_is_readonly_and_returns_history_for_current_versions(sessions) -> None:
    source, reader = Source(), Reader()
    service = ExtractionService(sessions, source, reader, ExtractionLimits())
    assert service.list_extractions("P") == []
    reader.failures = 1
    failed = service.extract_document("D")
    completed = service.extract_document("D")
    results = service.list_extractions("P")
    assert [r.run_id for r in results] == [failed.run_id, completed.run_id]
    assert reader.calls == 2
    assert count(sessions, ExtractionRunRecord) == 2
