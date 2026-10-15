import pytest

from public_procurement.shared.config import Settings
from public_procurement.shared.testing import settings_for_test_database

DEVELOPMENT = "postgresql+psycopg://user@localhost:55432/public_procurement"
TEST = "postgresql+psycopg://user@localhost:55432/public_procurement_test"


@pytest.mark.parametrize(
    ("test_url", "environment"),
    [
        (None, "local"),
        ("", "local"),
        (DEVELOPMENT, "local"),
        ("postgresql://other@127.0.0.1:55432/public_procurement", "local"),
        ("sqlite:///procurement_test", "local"),
        ("not-a-url", "local"),
        (TEST, "production"),
    ],
)
def test_unsafe_test_destination_is_rejected(test_url, environment) -> None:
    settings = Settings(
        _env_file=None, database_url=DEVELOPMENT, test_database_url=test_url, app_env=environment
    )
    with pytest.raises(ValueError, match=r".+"):
        settings_for_test_database(settings)


def test_same_database_name_is_rejected_even_with_different_host() -> None:
    settings = Settings(
        _env_file=None, database_url=TEST, test_database_url=TEST.replace("localhost", "127.0.0.1")
    )
    with pytest.raises(ValueError, match="nombres distintos"):
        settings_for_test_database(settings)


def test_explicit_test_database_preserves_development_configuration() -> None:
    settings = Settings(_env_file=None, database_url=DEVELOPMENT, test_database_url=TEST)
    selected = settings_for_test_database(settings)
    assert selected.database_url == TEST
    assert settings.database_url == DEVELOPMENT
