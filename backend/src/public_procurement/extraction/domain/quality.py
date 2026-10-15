"""Evaluación determinística por página, sin librerías PDF ni I/O."""

from typing import Any


def assess_text(text: str, min_chars: int, min_ratio: float, max_damaged: float) -> dict[str, Any]:
    visible = [c for c in text if not c.isspace()]
    count = len(visible)
    alphanumeric = sum(c.isalnum() for c in visible)
    damaged = sum(c == "\ufffd" or ord(c) < 32 for c in visible)
    ratio = alphanumeric / count if count else 0.0
    damage_ratio = damaged / count if count else 0.0
    reasons = []
    if alphanumeric < min_chars:
        reasons.append("few_alphanumeric_characters")
    if ratio < min_ratio:
        reasons.append("low_alphanumeric_ratio")
    if damage_ratio > max_damaged:
        reasons.append("damaged_characters")
    return {
        "status": "native_text_empty"
        if not count
        else ("native_text_low_quality" if reasons else "native_text_ok"),
        "alphanumeric_chars": alphanumeric,
        "alphanumeric_ratio": ratio,
        "damaged_ratio": damage_ratio,
        "reasons": reasons,
        "ocr_required": bool(reasons) or not count,
        "thresholds": {
            "min_alphanumeric_chars": min_chars,
            "min_alphanumeric_ratio": min_ratio,
            "max_damaged_ratio": max_damaged,
        },
    }
