from pathlib import Path

from public_procurement.shared.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"
OUT_OF_SCOPE_PREFIXES = ("AI_", "AZURE_", "FOUNDRY_", "ANTHROPIC_", "MAIL", "S3_", "R2_")


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
    assert (
        declared
        == expected
        == {
            "DATABASE_URL",
            "TEST_DATABASE_URL",
            "EUREKA_RADAR_START_DATE",
            "EUREKA_RADAR_REGIONS",
            "EUREKA_RADAR_INTERVAL_HOURS",
            "EUREKA_RADAR_MAX_PROCESSES",
            "EUREKA_AUTOMATION_ENABLED",
            "EUREKA_AUTOMATION_ALLOW_REAL_SEND",
            "EUREKA_AUTOMATION_INTERVAL_HOURS",
            "EUREKA_AUTOMATION_TIMEZONE",
            "EUREKA_AUTOMATION_RUN_TIMES",
            "EUREKA_AUTOMATION_LOG_PATH",
            "EUREKA_LOG_RETENTION_DAYS",
            "EUREKA_AUTOMATION_STALE_MINUTES",
            "EUREKA_AUTOMATION_TASK_NAME",
            "EUREKA_PREFERRED_BUDGET_MAX",
            "EUREKA_RADAR_CONFIG_PATH",
            "EUREKA_METADATA_ALERT_EXCLUSIONS_PATH",
            "LOCAL_STORAGE_PATH",
            "APP_ENV",
            "LOG_LEVEL",
            "DOCUMENT_TIMEOUT_SECONDS",
            "DOCUMENT_MAX_BYTES",
            "EXTRACTION_TIMEOUT_SECONDS",
            "EXTRACTION_MAX_BYTES",
            "EXTRACTION_MAX_CHARS",
            "EXTRACTION_MAX_FRAGMENTS",
            "EXTRACTION_MAX_PAGES",
            "EXTRACTION_OCR_ENABLED",
            "EXTRACTION_OCR_CONFIG_PATH",
            "EXTRACTION_TESSERACT_CMD",
            "EXTRACTION_TESSDATA_PATH",
            "EUREKA_NOTIFICATION_ENABLED",
            "EUREKA_NOTIFICATION_MODE",
            "EUREKA_NOTIFICATION_RECIPIENTS",
            "EUREKA_NOTIFICATION_BASE_URL",
            "EUREKA_NOTIFICATION_CAPTURE_PATH",
            "EUREKA_NOTIFICATION_MAX_RETRIES",
            "EUREKA_NOTIFICATION_RETRY_SECONDS",
            "EUREKA_NOTIFICATION_TIMEOUT_SECONDS",
            "EUREKA_NOTIFICATION_PROCESSING_LEASE_SECONDS",
            "EUREKA_NOTIFICATION_IDEMPOTENCY_MARGIN_SECONDS",
            "EUREKA_NOTIFICATION_MAX_MESSAGES",
            "EUREKA_NOTIFICATION_DIGEST_MAX_ALERTS",
            "RESEND_API_KEY",
            "RESEND_FROM_EMAIL",
        }
    )


def test_env_example_has_no_out_of_scope_variables_when_reviewed() -> None:
    # Arrange / Act
    declared = _declared_variables()
    # Assert
    assert not [name for name in declared if name.startswith(OUT_OF_SCOPE_PREFIXES)]


def test_notifications_example_is_disabled_and_has_no_credentials_or_recipients():
    values = dict(
        line.split("=", 1)
        for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    )
    assert values["EUREKA_NOTIFICATION_ENABLED"] == "false"
    assert values["EUREKA_NOTIFICATION_MODE"] == "disabled"
    assert values["EUREKA_NOTIFICATION_RECIPIENTS"] == ""
    assert values["RESEND_API_KEY"] == ""
    assert values["RESEND_FROM_EMAIL"] == ""
