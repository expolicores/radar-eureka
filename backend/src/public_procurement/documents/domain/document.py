import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

DOCUMENT_DATASET = "dmgg-8hin"


class AcquisitionStatus(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    FAILED = "failed"


class AcquisitionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SourceDocument:
    id_documento: str
    portfolio_id: str
    original_name: str
    fecha_carga: datetime | None
    source_url: str | None
    dataset_id: str = DOCUMENT_DATASET

    def __post_init__(self) -> None:
        if not self.id_documento or len(self.id_documento) > 128:
            raise ValueError("Identificador documental inválido.")
        if not self.portfolio_id or len(self.portfolio_id) > 128:
            raise ValueError("Portafolio documental inválido.")
        if self.dataset_id != DOCUMENT_DATASET:
            raise ValueError("Dataset documental no soportado.")


@dataclass(frozen=True)
class StoredBinary:
    sha256: str
    storage_path: str
    observed_size: int
    content_type: str


@dataclass(frozen=True)
class Document:
    id: uuid.UUID
    source: SourceDocument
    status: AcquisitionStatus


@dataclass(frozen=True)
class DocumentVersion:
    id: uuid.UUID
    document_id: uuid.UUID
    sha256: str
    storage_path: str
    observed_size: int
    content_type: str
    original_name: str
    fecha_carga: datetime | None
    source_url: str | None
    downloaded_at: datetime


@dataclass(frozen=True)
class DownloadSummary:
    available: int
    failed: int
