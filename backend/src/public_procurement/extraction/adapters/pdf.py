import json
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

from pypdf import PdfReader

from ..domain.content import (
    ExtractionError,
    ExtractionLimits,
    ExtractionStatus,
    Fragment,
    ParsedContent,
)
from .common import FragmentBuilder


def extract_pdf(
    path: Path,
    limits: ExtractionLimits,
    checkpoint: Callable[[dict], None] | None = None,
) -> ParsedContent:
    started = time.monotonic()
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ExtractionError("encrypted_file", "PDF protegido: no se intentan contraseñas.")
    count = len(reader.pages)
    if limits.max_pages is not None and count > limits.max_pages:
        raise ExtractionError("page_limit", "El PDF excede el límite de páginas.")
    builder = FragmentBuilder(limits)
    empty = []
    errors = []
    boundary = None
    visited = 0
    if checkpoint:
        checkpoint({"page_count": count})
    for number in range(1, count + 1):
        if checkpoint and time.monotonic() - started >= limits.timeout_seconds * 0.85:
            boundary = "native_time_limit"
            break
        try:
            page = reader.pages[number - 1]
            text = page.extract_text() or ""
        except Exception as error:
            if checkpoint and isinstance(error, MemoryError):
                boundary = "memory_limit"
                break
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
        start = len(builder.fragments)
        locator = {
            "kind": "pdf_page",
            "page_number": number,
            "extraction_method": "native_pdf_text",
        }
        if checkpoint and len(text) > limits.max_chars - builder.chars:
            text = text[: limits.max_chars - builder.chars]
            boundary = "text_limit"
        try:
            builder.add(text, locator, page_number=number)
        except (ExtractionError, MemoryError) as error:
            if not checkpoint:
                raise
            boundary = getattr(error, "code", "memory_limit")
        visited = number
        if checkpoint:
            checkpoint(
                {
                    "page_number": number,
                    "fragments": [asdict(f) for f in builder.fragments[start:]],
                    "empty": bool(empty and empty[-1] == number),
                    "error": errors[-1] if errors and errors[-1]["page_number"] == number else None,
                    "boundary": boundary,
                }
            )
        if boundary:
            break
    diagnostics = {"native_page_errors": errors} if errors else {}
    if checkpoint:
        diagnostics.update(
            native_pages_visited=visited,
            native_stop_reason=boundary,
            native_incomplete_from=number if boundary else None,
            native_cpu_seconds=round(time.process_time(), 6),
        )
    status = (
        ExtractionStatus.PARTIAL_TEXT
        if boundary and builder.fragments
        else ExtractionStatus.REQUIRES_OCR
        if boundary or (empty and not builder.fragments)
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
        diagnostics=diagnostics,
    )


def recover_pdf_checkpoint(path: Path, reason: str) -> ParsedContent | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as stream:
        header = stream.readline()
        if not header.endswith("\n"):
            return None
        count = json.loads(header)["page_count"]
        fragments = []
        visited = 0
        empty = []
        errors = []
        incomplete_from = None
        for line in stream:
            if not line.endswith("\n"):
                break
            page = json.loads(line)
            visited = page["page_number"]
            fragments.extend(Fragment(**f) for f in page["fragments"])
            if page["empty"]:
                empty.append(visited)
            if page.get("error"):
                errors.append(page["error"])
            if page["boundary"]:
                incomplete_from = visited
    return ParsedContent(
        ExtractionStatus.PARTIAL_TEXT if fragments else ExtractionStatus.REQUIRES_OCR,
        tuple(fragments),
        tuple(empty),
        count,
        diagnostics={
            "native_pages_visited": visited,
            "native_stop_reason": reason,
            "native_page_errors": errors,
            "native_incomplete_from": incomplete_from or min(visited + 1, count),
        },
    )
