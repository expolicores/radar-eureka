"""Servicios de aplicación de la ingesta: única puerta de entrada al módulo desde otros módulos."""

import logging
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Protocol, Self

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.shared.logging import log_event

from .domain.process import ProcessQuery, ProcessSyncResult, SecopProcess, unique_processes
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
from .ports import ProcessDataSource, PublicDataSource
from .process_repositories import SqlProcessRepository
from .repositories import SqlPurchaseQueries
from .unit_of_work import SqlUnitOfWork

# Tipos que otros módulos pueden usar: esta es la única puerta de entrada al módulo.
__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "IngestionService",
    "ItemClassification",
    "Panel",
    "ProcessIngestionService",
    "ProcessQuery",
    "ProcessSyncResult",
    "Purchase",
    "PurchaseFilterOptions",
    "PurchaseItem",
    "PurchasePage",
    "PurchaseQueryService",
    "PurchaseSearchCriteria",
    "PurchaseSort",
    "Resolution",
    "SecopProcess",
    "Source",
    "StoredPurchase",
    "TvAttributes",
    "UnitPriceStatus",
    "ValueRange",
    "VatBasis",
    "build_ingestion_service",
    "build_process_ingestion_service",
    "build_purchase_query_service",
]

logger = logging.getLogger("public_procurement.ingestion.services")


@dataclass(frozen=True)
class ProcessReference:
    id: uuid.UUID
    id_del_proceso: str
    portfolio_id: str | None


@dataclass(frozen=True)
class StoredSecopProcess:
    id: uuid.UUID
    process: SecopProcess


class ProcessQueryService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_process(self, reference: str) -> ProcessReference | None:
        with self._session_factory() as session:
            result = SqlProcessRepository(session).find(reference)
            return ProcessReference(*result) if result else None

    def iter_processes(
        self,
        reference: str | None = None,
        department: str | None = None,
        page_size: int = 200,
    ) -> Iterator[StoredSecopProcess]:
        if not 1 <= page_size <= 1000:
            raise ValueError("Tamaño de página de procesos inválido.")
        after = None
        while True:
            with self._session_factory() as session:
                records = SqlProcessRepository(session).read_page(
                    reference, department, after, page_size
                )
            for identifier, process in records:
                yield StoredSecopProcess(identifier, process)
            if len(records) < page_size:
                return
            after = records[-1][0]


def build_process_query_service(session_factory: sessionmaker[Session]) -> ProcessQueryService:
    return ProcessQueryService(session_factory)


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


class ProcessIngestionService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock

    def run(self, source: ProcessDataSource, query: ProcessQuery) -> ProcessSyncResult:
        started_at = self._clock()
        # Todo I/O externo finaliza antes de abrir la transacción. Un fallo no deja carga parcial.
        return self.persist(list(source.fetch_processes(query)), query, started_at)

    def persist(
        self, received: list[SecopProcess], query: ProcessQuery, started_at: datetime | None = None
    ) -> ProcessSyncResult:
        """Persiste registros ya adquiridos; permite orquestación sin repetir consultas externas."""
        started_at = started_at or self._clock()
        processes = unique_processes(received)
        with self._session_factory.begin() as session:
            repository = SqlProcessRepository(session)
            changed = repository.save_all(processes, self._clock())
            result = ProcessSyncResult(
                uuid.uuid4(), started_at, self._clock(), len(received), len(processes), changed
            )
            repository.add_run(result, query)
        log_event(
            logger,
            "process_sync_finished",
            read_count=result.read_count,
            unique_count=result.unique_count,
            changed_count=result.changed_count,
        )
        return result


def build_process_ingestion_service(
    session_factory: sessionmaker[Session],
) -> ProcessIngestionService:
    return ProcessIngestionService(session_factory)


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


def search_process_candidates(
    session: Session, query: str | None, filters: dict[str, Any]
) -> set[uuid.UUID]:
    from .search_queries import candidates

    return candidates(session, query, filters)


def search_process_records(
    session: Session, identifiers: list[uuid.UUID], expressions: dict[str, str]
) -> list[dict[str, Any]]:
    from .search_queries import records

    return records(session, identifiers, expressions)


def fetch_secop_processes(query: ProcessQuery) -> Iterator[SecopProcess]:
    """Public remote source; keeps the Socrata adapter owned by ingestion."""
    from .adapters.socrata_processes import SocrataProcessSource

    return iter(SocrataProcessSource().fetch_processes(query))
