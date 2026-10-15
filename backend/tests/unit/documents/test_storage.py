import io
import zipfile

import pytest

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError

PDF = b"%PDF-1.4\ncomplete test document\n%%EOF\n"


def store(storage, chunks, expected_size=None, max_bytes=1000, name="test.pdf"):
    return storage.store(
        chunks,
        original_name=name,
        content_type="application/pdf",
        expected_size=expected_size,
        max_bytes=max_bytes,
    )


def test_same_content_reuses_hash_path_and_ignores_original_path(tmp_path) -> None:
    storage = LocalBinaryStorage(tmp_path)
    first = store(storage, [PDF], len(PDF), name="../../outside.pdf")
    second = store(storage, [PDF[:10], PDF[10:]], len(PDF))
    assert first == second
    assert (tmp_path / first.storage_path).read_bytes() == PDF
    assert len(list((tmp_path / "sha256").rglob("*"))) == 2
    assert list((tmp_path / ".tmp").iterdir()) == []


def test_interrupted_download_keeps_previous_binary_and_removes_temporary(tmp_path) -> None:
    storage = LocalBinaryStorage(tmp_path)
    previous = store(storage, [PDF])

    def interrupted():
        yield b"%PDF-1.4\npartial"
        raise ConnectionError("interrupted")

    with pytest.raises(ConnectionError):
        store(storage, interrupted())
    assert (tmp_path / previous.storage_path).read_bytes() == PDF
    assert list((tmp_path / ".tmp").iterdir()) == []


@pytest.mark.parametrize(
    ("data", "expected", "limit", "code"),
    [
        (PDF, len(PDF) + 1, 1000, "size_mismatch"),
        (PDF, None, 4, "too_large"),
        (b"", None, 1000, "empty_file"),
        (b"<html>login</html>", None, 1000, "invalid_content"),
        (b"%PDF-1.4 partial", None, 1000, "invalid_content"),
        (b"PK\x03\x04truncated", None, 1000, "invalid_content"),
    ],
)
def test_invalid_download_never_becomes_visible(tmp_path, data, expected, limit, code) -> None:
    with pytest.raises(AcquisitionError) as error:
        store(LocalBinaryStorage(tmp_path), [data], expected, limit)
    assert error.value.code == code
    assert not (tmp_path / "sha256").exists()
    assert list((tmp_path / ".tmp").iterdir()) == []


def test_zip_container_is_validated_without_extracting_files(tmp_path) -> None:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("[Content_Types].xml", "types")
        archive.writestr("word/document.xml", "content")
    result = store(LocalBinaryStorage(tmp_path), [data.getvalue()], name="file.docx")
    assert (tmp_path / result.storage_path).is_file()
    assert not (tmp_path / "word").exists()
