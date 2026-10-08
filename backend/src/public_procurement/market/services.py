"""Servicios del mercado: única puerta de entrada al módulo desde otros módulos."""

import logging
import uuid
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.shared.logging import log_event

from .domain.observation import (
    AcquisitionMethod,
    MarketObservation,
    MarketVatBasis,
    Store,
    StoredObservation,
)
from .ports import RetailObservationSource
from .repositories import SqlObservationQueries, SqlObservationRepository

__all__ = [
    "AcquisitionMethod",
    "MarketIngestionService",
    "MarketObservation",
    "MarketQueryService",
    "MarketVatBasis",
    "Store",
    "StoredObservation",
    "build_market_ingestion_service",
    "build_market_query_service",
]

logger = logging.getLogger("public_procurement.market.services")


class _SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.observations = SqlObservationRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        finally:
            self._session.close()


class MarketIngestionService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def load(self, source: RetailObservationSource) -> int:
        """Registra las observaciones nuevas (histórico inmutable); devuelve cuántas."""
        observations = list(source.fetch_observations())
        with _SqlUnitOfWork(self._session_factory) as unit_of_work:
            new_count = unit_of_work.observations.add_new(observations)
        log_event(
            logger, "market_observations_loaded", read_count=len(observations), new_count=new_count
        )
        return new_count


class MarketQueryService:
    """Lectura de observaciones para la comparación (Benchmark 2) y el detalle de señales."""

    def __init__(self, queries: SqlObservationQueries) -> None:
        self._queries = queries

    def all_observations(self) -> tuple[StoredObservation, ...]:
        return self._queries.all_observations()

    def get_many(self, ids: list[uuid.UUID]) -> tuple[StoredObservation, ...]:
        return self._queries.get_many(ids)


def build_market_ingestion_service(
    session_factory: sessionmaker[Session],
) -> MarketIngestionService:
    return MarketIngestionService(session_factory)


def build_market_query_service(session_factory: sessionmaker[Session]) -> MarketQueryService:
    return MarketQueryService(SqlObservationQueries(session_factory))
