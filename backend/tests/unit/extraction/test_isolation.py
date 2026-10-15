import hashlib
import io
import subprocess
import uuid
from dataclasses import replace
from unittest.mock import Mock

import pytest
from docx import Document

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError
from public_procurement.extraction.adapters.isolated import IsolatedExtractor
from public_procurement.extraction.domain.content import (
    DocumentInput,
    ExtractionError,
    ExtractionLimits,
)

from .test_readers import pdf_bytes
from .test_services import Source


def test_registered_input_is_extracted_in_worker_process() -> None:
    source = Source()
    source.data = pdf_bytes()
    source.documents[0] = DocumentInput(
        uuid.uuid4(),
        uuid.uuid4(),
        "test.pdf",
        hashlib.sha256(source.data).hexdigest(),
        len(source.data),
    )
    result = IsolatedExtractor(source, ExtractionLimits()).extract(source.documents[0])
    assert "Hit" in result.fragments[0].text


@pytest.mark.parametrize(
    ("name", "data", "code"),
    [("unknown.bin", b"data", "unsupported_format"), ("bad.pdf", b"bad", "corrupt_file")],
)
def test_worker_reports_unsupported_or_corrupt_without_exposing_content(name, data, code) -> None:
    source = Source()
    source.data = data
    document = DocumentInput(
        uuid.uuid4(), uuid.uuid4(), name, hashlib.sha256(data).hexdigest(), len(data)
    )
    with pytest.raises(ExtractionError) as error:
        IsolatedExtractor(source, ExtractionLimits()).extract(document)
    assert error.value.code == code


def test_worker_timeout_is_reported(monkeypatch) -> None:
    from public_procurement.extraction.adapters import isolated

    source = Source()
    monkeypatch.setattr(
        isolated.subprocess, "run", Mock(side_effect=subprocess.TimeoutExpired("worker", 1))
    )
    with pytest.raises(ExtractionError) as error:
        IsolatedExtractor(source, ExtractionLimits()).extract(source.documents[0])
    assert error.value.code == "timeout"


def test_extractor_identity_changes_with_limits() -> None:
    source = Source()
    first = IsolatedExtractor(source, ExtractionLimits()).identity(source.documents[0])
    second = IsolatedExtractor(source, replace(ExtractionLimits(), max_pages=100)).identity(
        source.documents[0]
    )
    assert first.version != second.version


def test_local_storage_rejects_arbitrary_paths_and_changed_content(tmp_path) -> None:
    storage = LocalBinaryStorage(tmp_path)
    binary = storage.store(
        [pdf_bytes()],
        original_name="test.pdf",
        content_type="application/pdf",
        expected_size=None,
        max_bytes=10000,
    )
    with (
        pytest.raises(AcquisitionError, match="ruta"),
        storage.open_verified("../../outside", binary.sha256, binary.observed_size, 10000),
    ):
        pass
    (tmp_path / binary.storage_path).write_bytes(b"x" * binary.observed_size)
    with (
        pytest.raises(AcquisitionError) as error,
        storage.open_verified(binary.storage_path, binary.sha256, binary.observed_size, 10000),
    ):
        pass
    assert error.value.code == "hash_mismatch"


def test_worker_preserves_unicode_and_format_counts() -> None:
    document = Document()
    document.add_paragraph("Garantía, piñata y entrega")
    data = io.BytesIO()
    document.save(data)
    source = Source()
    source.data = data.getvalue()
    registered = DocumentInput(
        uuid.uuid4(),
        uuid.uuid4(),
        "test.docx",
        hashlib.sha256(source.data).hexdigest(),
        len(source.data),
    )
    result = IsolatedExtractor(source, ExtractionLimits()).extract(registered)
    assert result.fragments[0].text == "Garantía, piñata y entrega"
    assert result.format_counts == {"paragraphs": 1, "tables": 0}
