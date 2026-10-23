"""Opt-in single retry for transient acquisition failures, never authentication."""

import time
from collections.abc import Callable

from ..domain.document import AcquisitionError, SourceDocument, StoredBinary
from ..ports import BinaryStorage, DocumentDownloader


class RetryOnceDownloader:
    def __init__(
        self, delegate: DocumentDownloader, wait: Callable[[float], None] = time.sleep
    ) -> None:
        self.delegate, self.wait = delegate, wait

    def download(self, source: SourceDocument, storage: BinaryStorage) -> StoredBinary:
        try:
            return self.delegate.download(source, storage)
        except AcquisitionError as error:
            if error.code not in {"network_error", "timeout"}:
                raise
        self.wait(4)
        return self.delegate.download(source, storage)
