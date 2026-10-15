"""Procesos SECOP previos o posteriores a adjudicación, distintos de las compras de la beta."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime

SECOP_PROCESS_DATASET = "p6dx-8zbt"


@dataclass(frozen=True)
class SecopProcess:
    id_del_proceso: str
    id_del_portafolio: str | None
    reference: str | None
    entity_name: str | None
    department: str | None
    municipality: str | None
    title: str | None
    description: str | None
    modality: str | None
    phase: str | None
    status: str | None
    published_on: date | None
    last_published_on: date | None
    base_price_cop: int | None
    category_code: str | None
    source_url: str | None
    dataset_id: str = SECOP_PROCESS_DATASET

    def __post_init__(self) -> None:
        if not self.id_del_proceso.strip() or len(self.id_del_proceso) > 128:
            raise ValueError("Identificador de proceso vacío o demasiado largo.")
        if self.dataset_id != SECOP_PROCESS_DATASET:
            raise ValueError("Dataset de procesos no soportado.")
        if self.base_price_cop is not None and self.base_price_cop < 0:
            raise ValueError("El precio base no puede ser negativo.")

    @property
    def identity(self) -> tuple[str, str]:
        return self.dataset_id, self.id_del_proceso


@dataclass(frozen=True)
class ProcessQuery:
    published_from: date | None = None
    published_before: date | None = None
    portfolio_id: str | None = None
    page_size: int = 1000
    max_pages: int = 100
    departments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.portfolio_id and not (self.published_from and self.published_before):
            raise ValueError("Indica un portafolio o un intervalo de publicación completo.")
        if (self.published_from is None) != (self.published_before is None):
            raise ValueError("El intervalo necesita inicio y fin exclusivo.")
        if (
            self.published_from
            and self.published_before
            and self.published_from >= self.published_before
        ):
            raise ValueError("El fin exclusivo debe ser posterior al inicio.")
        if self.portfolio_id is not None and len(self.portfolio_id) > 128:
            raise ValueError("El identificador de portafolio es demasiado largo.")
        if self.portfolio_id is not None and not self.portfolio_id.strip():
            raise ValueError("El portafolio no puede estar vacío.")
        if not 1 <= self.page_size <= 1000 or not 1 <= self.max_pages <= 1000:
            raise ValueError("Tamaño o límite de páginas fuera del rango permitido.")
        if len(self.departments) > 32 or any(
            not value.strip() or len(value) > 128 for value in self.departments
        ):
            raise ValueError("Regiones de consulta inválidas.")


@dataclass(frozen=True)
class ProcessSyncResult:
    id: uuid.UUID
    started_at: datetime
    finished_at: datetime
    read_count: int
    unique_count: int
    changed_count: int


def unique_processes(processes: list[SecopProcess]) -> list[SecopProcess]:
    by_identity: dict[tuple[str, str], SecopProcess] = {}
    for process in processes:
        previous = by_identity.get(process.identity)
        if previous is not None and previous != process:
            raise ValueError("La consulta contiene versiones contradictorias del mismo proceso.")
        by_identity[process.identity] = process
    return list(by_identity.values())
