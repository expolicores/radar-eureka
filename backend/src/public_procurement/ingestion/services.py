"""Servicios de aplicación de la ingesta: única puerta de entrada al módulo desde otros módulos."""

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from types import TracebackType
from typing import Protocol, Self

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.shared.logging import log_event

from .domain.purchase import (
    IngestionRunResult,
    ItemClassification,
    Panel,
    Purchase,
    PurchaseItem,
    Resolution,
    Source,
    TvAttributes,
    UnitPriceStatus,
    VatBasis,
    build_purchase,
)
from .domain.search import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PurchaseFilterOptions,
    PurchasePage,
    PurchaseSearchCriteria,
    PurchaseSort,
    StoredPurchase,
    ValueRange,
)
from .ports import PublicDataSource
from .repositories import SqlPurchaseQueries
from .unit_of_work import SqlUnitOfWork

# Tipos que otros módulos pueden usar: esta es la única puerta de entrada al módulo.
__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "IngestionService",
    "ItemClassification",
    "Panel",
    "Purchase",
    "PurchaseFilterOptions",
    "PurchaseItem",
    "PurchasePage",
    "PurchaseQueryService",
    "PurchaseSearchCriteria",
    "PurchaseSort",
    "Resolution",
    "Source",
    "StoredPurchase",
    "TvAttributes",
    "UnitPriceStatus",
    "ValueRange",
    "VatBasis",
    "build_ingestion_service",
    "build_purchase_query_service",
]

logger = logging.getLogger("public_procurement.ingestion.services")


class PurchaseRepository(Protocol):
    def save_all(self, source: Source, purchases: list[Purchase]) -> tuple[int, int]: ...

    def add_run(self, run: IngestionRunResult) -> None: ...


class UnitOfWork(Protocol):
    """Una transacción: confirma al salir sin error y revierte si hay excepción."""

    @property
    def purchases(self) -> PurchaseRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


class IngestionService:
    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def run(self, source: PublicDataSource) -> IngestionRunResult:
        """Carga las compras de una fuente: idempotente por identidad de origen."""
        started_at = self._clock()
        purchases = [build_purchase(record) for record in source.fetch_purchases()]
        with self._unit_of_work() as unit_of_work:
            new_count, updated_count = unit_of_work.purchases.save_all(source.source, purchases)
            result = IngestionRunResult(
                source=source.source,
                started_at=started_at,
                finished_at=self._clock(),
                cutoff_at=source.cutoff_at,
                read_count=len(purchases),
                new_count=new_count,
                updated_count=updated_count,
            )
            unit_of_work.purchases.add_run(result)
        log_event(
            logger,
            "ingestion_run_finished",
            source=result.source.value,
            read_count=result.read_count,
            new_count=result.new_count,
            updated_count=result.updated_count,
        )
        return result


def build_ingestion_service(session_factory: sessionmaker[Session]) -> IngestionService:
    return IngestionService(lambda: SqlUnitOfWork(session_factory))


class PurchaseQueries(Protocol):
    def search(self, criteria: PurchaseSearchCriteria) -> PurchasePage: ...

    def get(self, purchase_id: uuid.UUID) -> StoredPurchase | None: ...

    def all_purchases(self) -> tuple[StoredPurchase, ...]: ...

    def get_many(self, purchase_ids: list[uuid.UUID]) -> dict[uuid.UUID, StoredPurchase]: ...

    def tv_purchase_counts(self) -> dict[Source, int]: ...

    def filter_options(self) -> PurchaseFilterOptions: ...

    def latest_cutoff(self) -> datetime | None: ...


class PurchaseQueryService:
    """Lectura de compras para otros módulos (exploración, comparación) y futuras herramientas."""

    def __init__(self, queries: PurchaseQueries) -> None:
        self._queries = queries

    def search(self, criteria: PurchaseSearchCriteria) -> PurchasePage:
        return self._queries.search(criteria)

    def get(self, purchase_id: uuid.UUID) -> StoredPurchase | None:
        return self._queries.get(purchase_id)

    def all_purchases(self) -> tuple[StoredPurchase, ...]:
        """Todas las compras con sus ítems (volumen del MVP: ~1.300)."""
        return self._queries.all_purchases()

    def get_many(self, purchase_ids: list[uuid.UUID]) -> dict[uuid.UUID, StoredPurchase]:
        return self._queries.get_many(purchase_ids)

    def tv_purchase_counts(self) -> dict[Source, int]:
        """Compras con al menos un ítem de televisor, por fuente (indicadores)."""
        return self._queries.tv_purchase_counts()

    def filter_options(self) -> PurchaseFilterOptions:
        return self._queries.filter_options()

    def latest_cutoff(self) -> datetime | None:
        """Fecha de corte más reciente de la ingesta («Datos actualizados al…»)."""
        return self._queries.latest_cutoff()


def build_purchase_query_service(session_factory: sessionmaker[Session]) -> PurchaseQueryService:
    return PurchaseQueryService(SqlPurchaseQueries(session_factory))
