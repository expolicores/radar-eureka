import pytest
from pydantic import ValidationError

from public_procurement.shared.config import (
    AppEnvironment,
    LogLevel,
    MissingConfigurationError,
    load_settings,
)

from ...builders import LOCAL_DATABASE_URL

MISSING_DATABASE_URL_MESSAGE = "Falta la variable de entorno obligatoria: DATABASE_URL."


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in (
        "EXTRACTION_TIMEOUT_SECONDS",
        "EXTRACTION_MAX_BYTES",
        "EXTRACTION_MAX_CHARS",
        "EXTRACTION_MAX_FRAGMENTS",
        "EXTRACTION_MAX_PAGES",
        "DOCUMENT_TIMEOUT_SECONDS",
        "DOCUMENT_MAX_BYTES",
        "DATABASE_URL",
        "TEST_DATABASE_URL",
        "LOCAL_STORAGE_PATH",
        "APP_ENV",
        "LOG_LEVEL",
    ):
        monkeypatch.delenv(variable, raising=False)


def test_load_settings_fails_with_spanish_message_when_database_url_is_missing() -> None:
    # Arrange: sin DATABASE_URL en el entorno ni archivo .env
    # Act
    with pytest.raises(MissingConfigurationError) as error:
        load_settings(_env_file=None)
    # Assert
    assert str(error.value) == MISSING_DATABASE_URL_MESSAGE


@pytest.mark.parametrize("blank_value", ["", "   "])
def test_load_settings_fails_with_spanish_message_when_database_url_is_blank(
    monkeypatch: pytest.MonkeyPatch, blank_value: str
) -> None:
    # Arrange
    monkeypatch.setenv("DATABASE_URL", blank_value)
    # Act
    with pytest.raises(MissingConfigurationError) as error:
        load_settings(_env_file=None)
    # Assert
    assert str(error.value) == MISSING_DATABASE_URL_MESSAGE


def test_load_settings_applies_defaults_when_only_database_url_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("DATABASE_URL", LOCAL_DATABASE_URL)
    # Act
    settings = load_settings(_env_file=None)
    # Assert
    assert settings.database_url == LOCAL_DATABASE_URL
    assert settings.app_env is AppEnvironment.LOCAL
    assert settings.log_level is LogLevel.INFO


def test_load_settings_reads_optional_variables_when_they_are_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("DATABASE_URL", LOCAL_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "ci")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    # Act
    settings = load_settings(_env_file=None)
    # Assert
    assert settings.app_env is AppEnvironment.CI
    assert settings.log_level is LogLevel.DEBUG


def test_storage_path_is_resolved_from_backend_without_creating_directory(tmp_path) -> None:
    settings = load_settings(
        _env_file=None, database_url=LOCAL_DATABASE_URL, local_storage_path=tmp_path / "not-created"
    )
    assert settings.local_storage_path == tmp_path / "not-created"
    assert not settings.local_storage_path.exists()


def test_relative_storage_path_does_not_depend_on_working_directory(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    settings = load_settings(
        _env_file=None, database_url=LOCAL_DATABASE_URL, local_storage_path=".local/documents"
    )
    assert settings.local_storage_path.name == "documents"
    assert settings.local_storage_path.parent.parent.name == "backend"


@pytest.mark.parametrize(
    "field",
    [
        "document_timeout_seconds",
        "document_max_bytes",
        "extraction_timeout_seconds",
        "extraction_max_bytes",
        "extraction_max_chars",
        "extraction_max_fragments",
        "extraction_max_pages",
        "eureka_radar_interval_hours",
        "eureka_preferred_budget_max",
    ],
)
@pytest.mark.parametrize("value", [0, -1])
def test_document_limits_must_be_positive(field, value) -> None:
    with pytest.raises(ValidationError):
        load_settings(_env_file=None, database_url=LOCAL_DATABASE_URL, **{field: value})


def test_radar_start_and_config_path_are_explicit_and_portable(monkeypatch, tmp_path):
    from datetime import date

    monkeypatch.chdir(tmp_path)
    settings = load_settings(
        _env_file=None,
        database_url=LOCAL_DATABASE_URL,
        eureka_radar_start_date="2026-10-13",
        eureka_radar_config_path="config/eureka_radar.v1.json",
    )
    assert settings.eureka_radar_start_date == date(2026, 10, 13)
    assert settings.eureka_radar_config_path.is_file()
    assert (
        load_settings(_env_file=None, database_url=LOCAL_DATABASE_URL).eureka_radar_start_date
        is None
    )


def test_ocr_configuration_is_local_and_tessdata_can_be_omitted(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    settings = load_settings(
        _env_file=None,
        database_url=LOCAL_DATABASE_URL,
        extraction_ocr_config_path="config/extraction_ocr.v1.json",
        extraction_tessdata_path="",
    )
    assert settings.extraction_ocr_config_path.is_file()
    assert settings.extraction_tessdata_path is None
    assert settings.extraction_tesseract_cmd == "tesseract"


def test_notification_defaults_are_disabled_portable_and_hide_api_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    settings = load_settings(
        _env_file=None, database_url=LOCAL_DATABASE_URL, resend_api_key="test-secret-not-real"
    )
    assert not settings.eureka_notification_enabled
    assert settings.eureka_notification_mode == "disabled"
    assert settings.eureka_notification_recipients == ""
    assert settings.eureka_notification_capture_path.is_absolute()
    assert "test-secret-not-real" not in repr(settings)
