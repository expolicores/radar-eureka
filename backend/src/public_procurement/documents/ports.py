from collections.abc import Iterable
from contextlib import AbstractContextManager
from typing import BinaryIO, Protocol

from .domain.document import SourceDocument, StoredBinary


class DocumentInventorySource(Protocol):
    def fetch(self, portfolio_id: str) -> list[SourceDocument]: ...


class BinaryStorage(Protocol):
    def open_verified(
        self,
        storage_path: str,
        sha256: str,
        observed_size: int,
        max_bytes: int,
    ) -> AbstractContextManager[BinaryIO]: ...

    def store(
        self,
        chunks: Iterable[bytes],
        *,
        original_name: str,
        content_type: str,
        expected_size: int | None,
        max_bytes: int,
    ) -> StoredBinary: ...


class DocumentDownloader(Protocol):
    def download(self, source: SourceDocument, storage: BinaryStorage) -> StoredBinary: ...
