"""Tesseract local por página; este lector no interpreta hechos comerciales."""

import hashlib
import math
import os
import shutil
import subprocess
import time
from collections import defaultdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from ..domain.content import ExtractionError, ExtractionLimits, ExtractionStatus, ParsedContent
from ..domain.quality import assess_text
from ..ocr_config import OcrPolicy
from .common import FragmentBuilder


def probe_engine(command: str, tessdata: Path | None, policy: OcrPolicy) -> dict[str, Any]:
    libraries = {}
    for name in ("pytesseract", "pypdfium2", "Pillow"):
        try:
            libraries[name] = version(name)
        except PackageNotFoundError:
            return {"available": False, "error_code": "ocr_dependencies_missing", "missing": name}
    executable = shutil.which(command)
    if not executable:
        return {"available": False, "error_code": "ocr_unavailable", "libraries": libraries}
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        result = subprocess.run(  # noqa: S603
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=flags,
            check=True,
        )
        args = [executable]
        if tessdata:
            args.extend(["--tessdata-dir", str(tessdata)])
        langs = subprocess.run(  # noqa: S603
            [*args, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=flags,
            check=True,
        )
        lines = langs.stdout.splitlines()
        installed = {line.strip() for line in lines[1:]}
        language = policy.language if policy.language in installed else policy.fallback_language
        if language not in installed:
            return {
                "available": False,
                "error_code": "ocr_language_missing",
                "languages": sorted(installed),
            }
        # --list-langs reports the effective tessdata directory, including defaults.
        data_dir = tessdata
        if data_dir is None and lines and '"' in lines[0]:
            data_dir = Path(lines[0].split('"')[1])
        model = data_dir / f"{language}.traineddata" if data_dir else None
        fingerprint = None
        if model and model.is_file():
            with model.open("rb") as source:
                fingerprint = hashlib.file_digest(source, "sha256").hexdigest()
        return {
            "available": True,
            "command": executable,
            "engine_version": result.stdout.splitlines()[0],
            "libraries": libraries,
            "language": language,
            "language_fallback": language != policy.language,
            "tessdata": str(data_dir) if data_dir else None,
            "model_sha256": fingerprint,
        }
    except (OSError, subprocess.SubprocessError, IndexError):
        return {"available": False, "error_code": "ocr_probe_failed", "libraries": libraries}


def recognize_image(image: Any, engine: dict[str, Any], timeout: float) -> tuple[str, float | None]:
    import pytesseract  # type: ignore[import-untyped]

    pytesseract.pytesseract.tesseract_cmd = engine["command"]
    config = "--psm 6"
    if engine.get("tessdata"):
        # This function runs in the isolated worker. Windows shlex parsing retains
        # quotes in --tessdata-dir arguments; the environment accepts spaces directly.
        os.environ["TESSDATA_PREFIX"] = engine["tessdata"]
    data = pytesseract.image_to_data(
        image,
        lang=engine["language"],
        config=config,
        output_type=pytesseract.Output.DICT,
        timeout=timeout,
    )
    lines: dict[tuple[int, int, int], list[str]] = defaultdict(list)
    confidences = []
    for index, word in enumerate(data["text"]):
        if not word.strip():
            continue
        key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
        lines[key].append(word)
        confidence = float(data["conf"][index])
        if 0 <= confidence <= 100:
            confidences.append(confidence)
    return "\n".join(" ".join(words) for words in lines.values()), (
        sum(confidences) / len(confidences) if confidences else None
    )


def extract_ocr(
    path: Path,
    limits: ExtractionLimits,
    policy: OcrPolicy,
    requested_pages: list[int] | None,
    engine: dict[str, Any],
) -> ParsedContent:
    import pypdfium2 as pdfium  # type: ignore[import-untyped]
    from PIL import ImageOps

    builder = FragmentBuilder(limits)
    started = time.monotonic()
    pages: list[dict[str, Any]] = []
    processed: list[int] = []
    success: list[int] = []
    omitted: list[int] = []
    document = pdfium.PdfDocument(str(path))
    try:
        count = len(document)
        if count > limits.max_pages:
            raise ExtractionError("page_limit", "El PDF excede el límite de páginas.")
        required = sorted(
            set(requested_pages if requested_pages is not None else range(1, count + 1))
        )
        if any(number < 1 or number > count for number in required):
            raise ExtractionError("ocr_protocol", "Página OCR fuera del documento.")
        for number in required:
            if len(processed) >= policy.max_ocr_pages:
                omitted.append(number)
                pages.append(
                    {"page_number": number, "status": "ocr_omitted", "error_code": "ocr_page_limit"}
                )
                continue
            remaining = policy.document_timeout_seconds - (time.monotonic() - started)
            if remaining <= 0:
                omitted.append(number)
                pages.append(
                    {
                        "page_number": number,
                        "status": "ocr_omitted",
                        "error_code": "ocr_document_timeout",
                    }
                )
                continue
            if not engine.get("available"):
                omitted.append(number)
                pages.append(
                    {
                        "page_number": number,
                        "status": "ocr_unavailable",
                        "error_code": engine.get("error_code"),
                    }
                )
                continue
            processed.append(number)
            page_started = time.monotonic()
            try:
                page = document[number - 1]
                try:
                    width, height = page.get_size()
                    scale = policy.dpi / 72
                    if math.ceil(width * scale) * math.ceil(height * scale) > policy.max_pixels:
                        raise ExtractionError(
                            "ocr_pixel_limit", "Página supera el límite de píxeles."
                        )
                    bitmap = page.render(scale=scale)
                    try:
                        with (
                            bitmap.to_pil() as rendered,
                            ImageOps.grayscale(rendered) as gray,
                            ImageOps.autocontrast(gray) as image,
                        ):
                            text, confidence = recognize_image(
                                image,
                                engine,
                                min(policy.page_timeout_seconds, remaining),
                            )
                    finally:
                        bitmap.close()
                finally:
                    page.close()
                quality = assess_text(
                    text,
                    policy.min_alphanumeric_chars,
                    policy.min_alphanumeric_ratio,
                    policy.max_damaged_ratio,
                )
                if quality["ocr_required"]:
                    pages.append(
                        {
                            "page_number": number,
                            "status": "ocr_failed",
                            "error_code": "ocr_low_quality",
                            "quality": quality,
                            "ocr_confidence": confidence,
                            "raw_text_sample": text[:4096],
                            "raw_text_truncated": len(text) > 4096,
                            "elapsed_seconds": round(time.monotonic() - page_started, 3),
                        }
                    )
                    continue
                builder.add(
                    text,
                    {
                        "kind": "pdf_page",
                        "page_number": number,
                        "extraction_method": "ocr_text",
                        "ocr_engine": "tesseract",
                        "ocr_engine_version": engine.get("engine_version"),
                        "ocr_policy_version": policy.version,
                        "ocr_config_hash": policy.digest,
                        "ocr_language": engine["language"],
                        "ocr_confidence": confidence,
                        "ocr_confidence_scale": "word_mean_0_100_not_semantic",
                    },
                    page_number=number,
                )
                success.append(number)
                pages.append(
                    {"page_number": number, "status": "ocr_success", "ocr_confidence": confidence}
                )
            except (OSError, RuntimeError, ValueError, ExtractionError) as error:
                pages.append(
                    {
                        "page_number": number,
                        "status": "ocr_failed",
                        "error_code": getattr(error, "code", "ocr_page_failed"),
                        "error_message": str(error)[:500],
                    }
                )
            pages[-1]["elapsed_seconds"] = round(time.monotonic() - page_started, 3)
        incomplete = set(required) - set(success)
        status = (
            "ocr_truncated"
            if omitted and engine.get("available")
            else (
                "ocr_unavailable"
                if not engine.get("available")
                else "partial_success"
                if incomplete and success
                else "ocr_failed"
                if incomplete
                else "ocr_success"
            )
        )
        return ParsedContent(
            ExtractionStatus.PARTIAL_TEXT
            if incomplete and builder.fragments
            else ExtractionStatus.REQUIRES_OCR
            if incomplete
            else ExtractionStatus.COMPLETED,
            tuple(builder.fragments),
            tuple(sorted(incomplete)),
            count,
            diagnostics={
                "status": status,
                "coverage_complete": not incomplete,
                "required_pages": required,
                "processed_pages": processed,
                "successful_pages": success,
                "omitted_pages": omitted,
                "pages": pages,
                "engine": engine,
                "policy": policy.model_dump(),
                "config_hash": policy.digest,
                "elapsed_seconds": round(time.monotonic() - started, 3),
            },
        )
    finally:
        document.close()
