from pathlib import Path

from pypdf import PdfReader

from ..domain.content import ExtractionError, ExtractionLimits, ExtractionStatus, ParsedContent
from .common import FragmentBuilder


def extract_pdf(path: Path, limits: ExtractionLimits) -> ParsedContent:
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ExtractionError("encrypted_file", "PDF protegido: no se intentan contraseñas.")
    count = len(reader.pages)
    if count > limits.max_pages:
        raise ExtractionError("page_limit", "El PDF excede el límite de páginas.")
    builder = FragmentBuilder(limits)
    empty = []
    errors = []
    for number in range(1, count + 1):
        try:
            page = reader.pages[number - 1]
            text = page.extract_text() or ""
        except Exception:
            errors.append(
                {
                    "page_number": number,
                    "status": "native_extraction_failed",
                    "error_code": "native_page_failed",
                }
            )
            text = ""
        text = text.replace("\x00", "\ufffd")
        if not text.strip():
            empty.append(number)
        builder.add(
            text,
            {"kind": "pdf_page", "page_number": number, "extraction_method": "native_pdf_text"},
            page_number=number,
        )
    status = (
        ExtractionStatus.REQUIRES_OCR
        if empty and not builder.fragments
        else ExtractionStatus.PARTIAL_TEXT
        if empty
        else ExtractionStatus.COMPLETED
        if builder.fragments
        else ExtractionStatus.EMPTY_TEXT
    )
    return ParsedContent(
        status,
        tuple(builder.fragments),
        tuple(empty),
        count,
        diagnostics={"native_page_errors": errors} if errors else {},
    )
