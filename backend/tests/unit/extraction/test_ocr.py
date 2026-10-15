from pathlib import Path
from unittest.mock import Mock

import pytest

from public_procurement.extraction.adapters import ocr
from public_procurement.extraction.adapters.pdf import extract_pdf
from public_procurement.extraction.domain.content import ExtractionError, ExtractionLimits
from public_procurement.extraction.ocr_config import OcrPolicy

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "extraction"
TEXT = (
    "JUGO HIT TETRA X 200 ML.\nCHOCORRAMO TRADICIONAL X 65 GR.\n"
    "CANTIDAD 400 PACK\nVALOR UNITARIO: $5.200\nVALOR TOTAL: $2.080.000"
)
ENGINE = {
    "available": True,
    "command": "fake-tesseract",
    "language": "spa",
    "engine_version": "test",
}


def test_scan_fixture_has_no_text_and_renders_real_page(monkeypatch):
    pytest.importorskip("pypdfium2")
    pytest.importorskip("PIL")
    path = FIXTURES / "scanned_refrigerios.pdf"
    assert not extract_pdf(path, ExtractionLimits()).fragments
    recognize = Mock(return_value=(TEXT, 92.5))
    monkeypatch.setattr(ocr, "recognize_image", recognize)
    result = ocr.extract_ocr(path, ExtractionLimits(), OcrPolicy(), [1], ENGINE)
    assert result.diagnostics["coverage_complete"]
    assert result.fragments[0].page_number == 1
    assert result.fragments[0].source_locator["extraction_method"] == "ocr_text"
    assert result.fragments[0].source_locator["ocr_confidence"] == 92.5
    assert recognize.call_args.args[0].mode == "L"


def test_page_failure_continues_and_page_limit_is_explicit(monkeypatch):
    pytest.importorskip("pypdfium2")
    monkeypatch.setattr(
        ocr, "recognize_image", Mock(side_effect=[RuntimeError("timeout"), (TEXT, 90)])
    )
    result = ocr.extract_ocr(
        FIXTURES / "mixed_refrigerios.pdf",
        ExtractionLimits(),
        OcrPolicy(max_ocr_pages=2),
        [1, 2, 3],
        ENGINE,
    )
    assert result.diagnostics["status"] == "ocr_truncated"
    assert not result.diagnostics["coverage_complete"]
    assert result.diagnostics["required_pages"] == [1, 2, 3]
    assert result.diagnostics["processed_pages"] == [1, 2]
    assert result.diagnostics["omitted_pages"] == [3]
    assert result.diagnostics["pages"][0]["status"] == "ocr_failed"
    assert result.fragments[0].page_number == 2


def test_pixel_limit_never_runs_tesseract(monkeypatch):
    pytest.importorskip("pypdfium2")
    recognize = Mock()
    monkeypatch.setattr(ocr, "recognize_image", recognize)
    result = ocr.extract_ocr(
        FIXTURES / "scanned_refrigerios.pdf",
        ExtractionLimits(),
        OcrPolicy(max_pixels=100),
        [1],
        ENGINE,
    )
    assert result.diagnostics["pages"][0]["error_code"] == "ocr_pixel_limit"
    assert not result.diagnostics["coverage_complete"]
    recognize.assert_not_called()


def test_missing_binary_is_controlled(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: None)
    assert not ocr.probe_engine("missing-tesseract", None, OcrPolicy())["available"]


def test_page_count_safety_is_not_bypassed_by_ocr():
    pytest.importorskip("pypdfium2")
    with pytest.raises(ExtractionError, match="páginas"):
        ocr.extract_ocr(
            FIXTURES / "mixed_refrigerios.pdf",
            ExtractionLimits(max_pages=2),
            OcrPolicy(),
            [2],
            ENGINE,
        )
