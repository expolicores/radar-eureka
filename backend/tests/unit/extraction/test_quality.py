import pytest

from public_procurement.extraction.domain.quality import assess_text
from public_procurement.extraction.ocr_config import OcrPolicy


@pytest.mark.parametrize(
    ("text", "status"),
    [
        ("", "native_text_empty"),
        ("ANEXO", "native_text_low_quality"),
        ("@#$%" * 50, "native_text_low_quality"),
        (
            "Texto legible de una página con contenido suficiente para la extracción nativa.",
            "native_text_ok",
        ),
        ("Contenido " * 20 + "\ufffd" * 50, "native_text_low_quality"),
    ],
)
def test_explicit_quality_and_thresholds(text, status):
    result = assess_text(text, 40, 0.5, 0.05)
    assert result["status"] == status
    assert result["ocr_required"] == (status != "native_text_ok")
    assert result["thresholds"]["min_alphanumeric_chars"] == 40


def test_config_changes_identity_and_can_calibrate_without_code():
    first = OcrPolicy()
    second = first.model_copy(update={"min_alphanumeric_chars": 5})
    assert first.digest != second.digest
    assert not assess_text("ANEXO", second.min_alphanumeric_chars, 0.5, 0.05)["ocr_required"]
