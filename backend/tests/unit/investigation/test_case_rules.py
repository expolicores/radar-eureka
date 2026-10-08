import pytest

from public_procurement.investigation.domain.case import (
    MAX_NOTE_LENGTH,
    MAX_TITLE_LENGTH,
    InvalidCaseDataError,
    clean_note,
    clean_title,
)


def test_clean_title_trims_spaces_when_title_is_valid() -> None:
    # Arrange
    title = "  Televisores en sedes educativas — Valle  "
    # Act
    cleaned = clean_title(title)
    # Assert
    assert cleaned == "Televisores en sedes educativas — Valle"


@pytest.mark.parametrize("title", ["", "   ", "x" * (MAX_TITLE_LENGTH + 1)])
def test_clean_title_rejects_title_when_empty_or_too_long(title: str) -> None:
    # Arrange / Act / Assert
    with pytest.raises(InvalidCaseDataError) as error:
        clean_title(title)
    assert error.value.field == "title"


def test_clean_note_accepts_the_maximum_length_when_exactly_at_the_limit() -> None:
    # Arrange
    body = "a" * MAX_NOTE_LENGTH
    # Act
    cleaned = clean_note(body)
    # Assert
    assert len(cleaned) == MAX_NOTE_LENGTH


@pytest.mark.parametrize("body", ["", "  ", "a" * (MAX_NOTE_LENGTH + 1)])
def test_clean_note_rejects_note_when_empty_or_too_long(body: str) -> None:
    # Arrange / Act / Assert
    with pytest.raises(InvalidCaseDataError) as error:
        clean_note(body)
    assert error.value.field == "body"
