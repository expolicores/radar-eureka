"""Guarda de regresión: el perfil comercial histórico no vive en código ni como fallback."""

from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
LEGACY_PROFILE = "1086" + "005"


def test_legacy_commercial_profile_is_not_hardcoded_in_product_or_scripts():
    # Arrange
    sources = [*BACKEND.joinpath("src").rglob("*.py"), *BACKEND.joinpath("scripts").glob("*.py")]
    # Act
    offenders = [
        str(path.relative_to(BACKEND))
        for path in sources
        if LEGACY_PROFILE in path.read_text(encoding="utf-8", errors="replace")
    ]
    # Assert
    assert offenders == []
