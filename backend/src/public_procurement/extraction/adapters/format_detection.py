"""Bounded format selection for the three existing readers; no new parsers."""

from pathlib import Path

SUPPORTED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}


def document_suffix(name: str, content_type: str | None, prefix: bytes = b"") -> str:
    # An unambiguous PDF signature takes precedence over a conflicting declaration.
    if prefix.startswith(b"%PDF-"):
        return ".pdf"
    media_type = (content_type or "").partition(";")[0].strip().lower()
    if media_type in SUPPORTED_TYPES:
        return SUPPORTED_TYPES[media_type]
    suffix = Path(name).suffix.lower()
    return suffix if suffix in SUPPORTED_TYPES.values() else ""
