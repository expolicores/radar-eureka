import pytest

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
    for variable in ("DATABASE_URL", "APP_ENV", "LOG_LEVEL"):
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
