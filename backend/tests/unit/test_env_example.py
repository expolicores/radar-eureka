from pathlib import Path

from public_procurement.shared.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"
OUT_OF_SCOPE_PREFIXES = ("AI_", "AZURE_", "FOUNDRY_", "ANTHROPIC_", "MAIL", "RESEND_", "S3_", "R2_")


def _declared_variables() -> set[str]:
    lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    return {
        line.split("=", 1)[0].strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    }


def test_env_example_documents_exactly_the_settings_variables_when_compared() -> None:
    # Arrange
    expected = {name.upper() for name in Settings.model_fields}
    # Act
    declared = _declared_variables()
    # Assert
    assert declared == expected == {"DATABASE_URL", "APP_ENV", "LOG_LEVEL"}


def test_env_example_has_no_out_of_scope_variables_when_reviewed() -> None:
    # Arrange / Act
    declared = _declared_variables()
    # Assert
    assert not [name for name in declared if name.startswith(OUT_OF_SCOPE_PREFIXES)]
