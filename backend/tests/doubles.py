"""Dobles para pruebas: motor de base de datos sin PostgreSQL y captura de logs."""

import logging
from datetime import datetime
from types import TracebackType
from typing import Any, Self

from sqlalchemy.exc import OperationalError

from public_procurement.ingestion.domain.purchase import (
    IngestionRunResult,
    Purchase,
    Source,
    SourcePurchase,
)

SECRET_IN_DRIVER_MESSAGE = "password=clave_incorrecta"


class _Connection:
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def execute(self, statement: Any) -> None:
        return None


class AvailableDatabaseEngine:
    def connect(self) -> _Connection:
        return _Connection()


class UnavailableDatabaseEngine:
    def connect(self) -> _Connection:
        raise OperationalError(
            "SELECT 1", {}, Exception(f"connection refused ({SECRET_IN_DRIVER_MESSAGE})")
        )


class ListLogHandler(logging.Handler):
    """Guarda cada línea ya formateada; se formatea al emitir, con el contexto de la solicitud."""

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


class InMemoryPurchaseRepository:
    """Repositorio en memoria con la misma semántica de identidad que el de SQL."""

    def __init__(self) -> None:
        self.purchases: dict[tuple[Source, str], Purchase] = {}
        self.runs: list[IngestionRunResult] = []

    def save_all(self, source: Source, purchases: list[Purchase]) -> tuple[int, int]:
        new_count = updated_count = 0
        for purchase in purchases:
            key = (source, purchase.source_record_id)
            previous = self.purchases.get(key)
            if previous is None:
                new_count += 1
            elif previous != purchase:
                updated_count += 1
            self.purchases[key] = purchase
        return new_count, updated_count

    def add_run(self, run: IngestionRunResult) -> None:
        self.runs.append(run)


class InMemoryUnitOfWork:
    def __init__(self, repository: InMemoryPurchaseRepository) -> None:
        self.purchases = repository

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class ListPublicDataSource:
    def __init__(
        self, source: Source, purchases: list[SourcePurchase], cutoff_at: datetime
    ) -> None:
        self._source = source
        self._purchases = purchases
        self._cutoff_at = cutoff_at

    @property
    def source(self) -> Source:
        return self._source

    @property
    def cutoff_at(self) -> datetime:
        return self._cutoff_at

    def fetch_purchases(self) -> list[SourcePurchase]:
        return list(self._purchases)
