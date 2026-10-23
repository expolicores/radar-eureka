import hashlib
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from public_procurement.extraction.adapters.documents import RegisteredDocumentSource
from public_procurement.extraction.adapters.format_detection import document_suffix
from public_procurement.extraction.adapters.isolated import IsolatedExtractor
from public_procurement.extraction.domain.content import ExtractionLimits, ExtractionStatus

from .test_readers import pdf_bytes
from .test_services import Source


@pytest.mark.parametrize(
    "name", ["sin extension", "8. Invitacion Publica Guican", "incorrecto.xlsx"]
)
def test_pdf_signature_selects_pdf_identity_and_real_worker_without_filename_extension(name):
    source = Source()
    source.data = pdf_bytes("Texto PDF verificado")
    document = replace(
        source.documents[0],
        original_name=name,
        content_type="application/octet-stream",
        input_sha256=hashlib.sha256(source.data).hexdigest(),
        observed_size=len(source.data),
    )
    reader = IsolatedExtractor(source, ExtractionLimits())
    assert reader.identity(document).name == "pdf-text"
    parsed = reader.extract(document)
    assert parsed.status is ExtractionStatus.COMPLETED
    assert "Texto PDF verificado" in parsed.fragments[0].text
    assert document.original_name == name


@pytest.mark.parametrize(
    ("name", "content_type", "prefix", "suffix"),
    [
        ("nombre", "Application/PDF; charset=binary", b"", ".pdf"),
        (
            "nombre.docx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            b"PK",
            ".xlsx",
        ),
        (
            "nombre",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            b"PK",
            ".docx",
        ),
        (
            "nombre",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            b"%PDF-1.7",
            ".pdf",
        ),
        ("nombre.PDF", None, b"", ".pdf"),
        ("8. Invitacion", None, b"unknown", ""),
        ("nombre.xls", "application/vnd.ms-excel", b"unknown", ""),
    ],
)
def test_only_supported_types_and_extensions_are_allowed(name, content_type, prefix, suffix):
    assert document_suffix(name, content_type, prefix) == suffix


def test_registered_source_preserves_stored_content_type():
    documents = Mock()
    documents.latest_version.return_value = SimpleNamespace(
        id="version",
        original_name="sin extension",
        sha256="hash",
        observed_size=42,
        content_type="application/pdf",
    )
    documents.list_documents.return_value = [SimpleNamespace(id="document")]
    result = RegisteredDocumentSource(documents).for_process("process")[0]
    assert result.content_type == "application/pdf"
    assert result.original_name == "sin extension"
