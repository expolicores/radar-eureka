"""Snapshot verificado y lector en un proceso local con timeout, sin rutas de usuario."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any

from ..domain.content import (
    DocumentInput,
    ExtractionError,
    ExtractionLimits,
    ExtractionStatus,
    ExtractorIdentity,
    Fragment,
    ParsedContent,
)
from ..domain.text import NORMALIZATION_VERSION
from ..ports import DocumentSource

READERS = {
    ".pdf": ("pdf-text", "pypdf"),
    ".docx": ("docx-text", "python-docx"),
    ".xlsx": ("xlsx-cells", "openpyxl"),
}


class IsolatedExtractor:
    def __init__(self, documents: DocumentSource, limits: ExtractionLimits) -> None:
        self.documents, self.limits = documents, limits

    def identity(self, document: DocumentInput) -> ExtractorIdentity:
        suffix = Path(document.original_name).suffix.lower()
        reader, library = READERS.get(suffix, ("unsupported", None))
        library_version = version(library) if library else "none"
        policy = hashlib.sha256(
            json.dumps(asdict(self.limits), sort_keys=True).encode()
        ).hexdigest()[:12]
        return ExtractorIdentity(reader, f"v1-{library_version}-{NORMALIZATION_VERSION}-{policy}")

    def worker_options(self) -> dict[str, Any]:
        return {}

    def worker_timeout(self) -> float:
        return self.limits.timeout_seconds

    def run_worker(self, request: dict[str, Any]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "public_procurement.extraction.adapters.worker"],
            input=json.dumps(request),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=self.worker_timeout(),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            check=False,
        )

    def extract(self, document: DocumentInput) -> ParsedContent:
        if document.document_version_id is None:
            raise ExtractionError("not_downloaded", "El documento no tiene una versión descargada.")
        suffix = Path(document.original_name).suffix.lower()
        with tempfile.TemporaryDirectory(prefix="extraction-") as temporary:
            snapshot = Path(temporary) / "input"
            with (
                self.documents.open_version(
                    document.document_version_id, self.limits.max_bytes
                ) as source,
                snapshot.open("wb") as target,
            ):
                size = 0
                for chunk in iter(lambda: source.read(65536), b""):
                    size += len(chunk)
                    if size > self.limits.max_bytes:
                        raise ExtractionError(
                            "too_large", "La entrada excede el límite configurado."
                        )
                    target.write(chunk)
            request = dict(
                path=str(snapshot),
                suffix=suffix,
                input_sha256=document.input_sha256,
                limits=asdict(self.limits),
            )
            request.update(self.worker_options())
            try:
                result = self.run_worker(request)
            except subprocess.TimeoutExpired as exc:
                raise ExtractionError(
                    "timeout", "El lector excedió el tiempo configurado."
                ) from exc
            if result.returncode != 0:
                raise ExtractionError(
                    "reader_failed",
                    "El lector terminó sin resultado; revisar corrupción o memoria.",
                )
            try:
                payload = json.loads(result.stdout)
                if "error_code" in payload:
                    raise ExtractionError(payload["error_code"], payload["error_message"])
                return ParsedContent(
                    ExtractionStatus(payload["status"]),
                    tuple(Fragment(**fragment) for fragment in payload["fragments"]),
                    tuple(payload["pages_without_text"]),
                    payload["page_count"],
                    payload["format_counts"],
                    payload.get("diagnostics", {}),
                )
            except (ValueError, KeyError, TypeError) as exc:
                raise ExtractionError(
                    "reader_protocol", "El lector devolvió una respuesta inválida."
                ) from exc
