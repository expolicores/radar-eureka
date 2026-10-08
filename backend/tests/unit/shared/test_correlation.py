import uuid

import pytest

from public_procurement.shared.correlation import resolve_identifier

CLIENT_CORRELATION_ID = "3f2b8c1e-7a4d-4e9b-9c11-5d2a6f8e0b47"


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


@pytest.mark.parametrize(
    "valid_value",
    [CLIENT_CORRELATION_ID, "job:42.retry_1", "a", "x" * 128],
)
def test_resolve_identifier_reuses_value_when_header_is_valid(valid_value: str) -> None:
    # Arrange / Act
    resolved = resolve_identifier(valid_value)
    # Assert
    assert resolved == valid_value


@pytest.mark.parametrize(
    "invalid_value",
    [None, "", "x" * 129, "abc\ninjected", "con espacio", "ñandú"],
)
def test_resolve_identifier_generates_uuid_when_header_is_missing_or_invalid(
    invalid_value: str | None,
) -> None:
    # Arrange / Act
    resolved = resolve_identifier(invalid_value)
    # Assert
    assert resolved != invalid_value
    assert _is_uuid(resolved)


def test_resolve_identifier_generates_different_values_when_called_twice_without_header() -> None:
    # Arrange / Act
    first = resolve_identifier(None)
    second = resolve_identifier(None)
    # Assert
    assert first != second
