"""Composición de evidencia nativa inmutable y OCR complementario."""

import hashlib
import json
import os
import signal
import subprocess
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from ..domain.content import (
    DocumentInput,
    ExtractionError,
    ExtractionLimits,
    ExtractionResult,
    ExtractionStatus,
    ExtractorIdentity,
    ParsedContent,
)
from ..domain.quality import assess_text
from ..ocr_config import OcrPolicy
from ..ports import DocumentSource
from .isolated import IsolatedExtractor
from .ocr import probe_engine


def native_quality(native: ExtractionResult, policy: OcrPolicy) -> list[dict[str, Any]]:
    count = native.page_count or max((f.page_number or 0 for f in native.fragments), default=0)
    return [
        {
            "page_number": number,
            **assess_text(
                "\n".join(f.text for f in native.fragments if f.page_number == number),
                policy.min_alphanumeric_chars,
                policy.min_alphanumeric_ratio,
                policy.max_damaged_ratio,
            ),
        }
        for number in range(1, count + 1)
    ]


class OcrPageExtractor(IsolatedExtractor):
    def __init__(
        self,
        documents: DocumentSource,
        limits: ExtractionLimits,
        policy: OcrPolicy,
        engine: dict[str, Any],
        pages: list[int] | None,
    ) -> None:
        super().__init__(documents, limits)
        self.policy, self.engine, self.pages = policy, engine, pages

    def worker_options(self) -> dict[str, Any]:
        return {
            "mode": "ocr",
            "ocr_policy": self.policy.model_dump(),
            "engine": self.engine,
            "pages": self.pages,
        }

    def worker_timeout(self) -> float:
        return self.policy.document_timeout_seconds + 10

    def run_worker(self, request: dict[str, Any]) -> subprocess.CompletedProcess[str]:
        import sys

        with subprocess.Popen(
            [sys.executable, "-X", "utf8", "-m", "public_procurement.extraction.adapters.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        ) as worker:
            try:
                stdout, stderr = worker.communicate(
                    json.dumps(request), timeout=self.worker_timeout()
                )
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    os.killpg(worker.pid, signal.SIGKILL)  # type: ignore[attr-defined]
                else:
                    # Windows worker owns a Job Object with KILL_ON_JOB_CLOSE.
                    worker.kill()
                worker.communicate()
                raise
            return subprocess.CompletedProcess(worker.args, worker.returncode, stdout, stderr)


class HybridExtractor:
    def __init__(
        self,
        documents: DocumentSource,
        limits: ExtractionLimits,
        policy: OcrPolicy,
        native: ExtractionResult,
        engine: dict[str, Any],
        pages: list[int] | None,
        attempt: int = 0,
    ) -> None:
        self.documents, self.limits, self.policy = documents, limits, policy
        self.native, self.engine, self.pages, self.attempt = native, engine, pages, attempt
        self.reader = OcrPageExtractor(documents, limits, policy, engine, pages)

    @property
    def prefix(self) -> str:
        snapshot = {
            "policy": self.policy.model_dump(),
            "engine": self.engine,
            "native_identity": asdict(self.native.extractor),
            "limits": asdict(self.limits),
        }
        digest = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        return f"v1-{digest}-a"

    def identity(self, document: DocumentInput) -> ExtractorIdentity:
        return ExtractorIdentity("pdf-hybrid-local", f"{self.prefix}{self.attempt}")

    def extract(self, document: DocumentInput) -> ParsedContent:
        required = self.pages or []
        if self.engine.get("available"):
            try:
                recovered = self.reader.extract(document)
            except ExtractionError as error:
                recovered = ParsedContent(
                    ExtractionStatus.REQUIRES_OCR,
                    (),
                    diagnostics={
                        "status": "ocr_failed",
                        "coverage_complete": False,
                        "error_code": error.code,
                        "error_message": str(error),
                        "required_pages": required,
                        "processed_pages": [],
                        "omitted_pages": required,
                        "successful_pages": [],
                        "pages": [],
                    },
                )
        else:
            recovered = ParsedContent(
                ExtractionStatus.REQUIRES_OCR,
                (),
                diagnostics={
                    "status": "ocr_unavailable",
                    "coverage_complete": False,
                    "error_code": self.engine.get("error_code"),
                    "required_pages": required,
                    "processed_pages": [],
                    "omitted_pages": required,
                    "successful_pages": [],
                    "pages": [
                        {
                            "page_number": p,
                            "status": "ocr_unavailable",
                            "error_code": self.engine.get("error_code"),
                        }
                        for p in required
                    ],
                },
            )
        fragments = [
            replace(
                f,
                source_locator={
                    **f.source_locator,
                    "extraction_method": "native_pdf_text",
                    "native_extraction_run_id": str(self.native.run_id)
                    if self.native.run_id
                    else None,
                    "native_ordinal": f.ordinal,
                    "native_extractor_name": self.native.extractor.name,
                    "native_extractor_version": self.native.extractor.version,
                },
            )
            for f in self.native.fragments
        ]
        chars = sum(len(f.text) for f in fragments)
        omitted: list[int] = []
        for fragment in recovered.fragments:
            if (
                chars + len(fragment.text) > self.limits.max_chars
                or len(fragments) >= self.limits.max_fragments
            ):
                if fragment.page_number is not None:
                    omitted.append(fragment.page_number)
                continue
            fragments.append(fragment)
            chars += len(fragment.text)
        diagnostic = {
            **recovered.diagnostics,
            "native_run_id": str(self.native.run_id) if self.native.run_id else None,
            "native_status": self.native.status.value,
            "native_error_code": self.native.error_code,
            "native_quality": native_quality(self.native, self.policy),
            "policy": self.policy.model_dump(),
            "config_hash": self.policy.digest,
            "engine": self.engine,
            "attempt": self.attempt,
            "required_pages_known": self.pages is not None or recovered.page_count > 0,
        }
        if omitted:
            diagnostic.update(
                status="ocr_truncated",
                coverage_complete=False,
                merge_omitted_pages=sorted(set(omitted)),
                merge_error="content_limit",
            )
        complete = bool(diagnostic.get("coverage_complete"))
        unresolved = sorted(
            set(diagnostic.get("required_pages", required))
            - set(diagnostic.get("successful_pages", []))
            | set(omitted)
        )
        fragments.sort(
            key=lambda f: (
                f.page_number or 0,
                f.source_locator.get("extraction_method") == "ocr_text",
                f.ordinal,
            )
        )
        for index, fragment in enumerate(fragments):
            fragments[index] = replace(
                fragment,
                ordinal=index + 1,
                source_locator={
                    **fragment.source_locator,
                    "document_coverage_complete": complete,
                    "document_acquisition_status": diagnostic["status"],
                    "document_ocr_required_pages": diagnostic.get("required_pages", required),
                    "document_ocr_omitted_pages": diagnostic.get("omitted_pages", []) + omitted,
                },
            )
        return ParsedContent(
            ExtractionStatus.COMPLETED
            if complete
            else ExtractionStatus.PARTIAL_TEXT
            if fragments
            else ExtractionStatus.REQUIRES_OCR,
            tuple(fragments),
            tuple(unresolved),
            recovered.page_count or self.native.page_count,
            self.native.format_counts,
            diagnostic,
        )


class LocalOcrFallback:
    def __init__(
        self,
        documents: DocumentSource,
        limits: ExtractionLimits,
        policy: OcrPolicy,
        command: str,
        tessdata: Path | None,
    ) -> None:
        self.documents, self.limits, self.policy = documents, limits, policy
        self.command, self.tessdata = command, tessdata

    def prepare(self, native: ExtractionResult, force: bool = False) -> HybridExtractor | None:
        if native.status is ExtractionStatus.RUNNING:
            return None
        if native.error_code and native.error_code not in (
            "corrupt_file",
            "reader_failed",
            "invalid_text",
            "input_error",
            "timeout",
        ):
            return None
        quality = native_quality(native, self.policy)
        pages = [p["page_number"] for p in quality if force or p["ocr_required"]]
        if not pages and not native.error_code:
            return None
        engine = probe_engine(self.command, self.tessdata, self.policy)
        return HybridExtractor(
            self.documents,
            self.limits,
            self.policy,
            native,
            engine,
            None if native.error_code else pages,
        )
