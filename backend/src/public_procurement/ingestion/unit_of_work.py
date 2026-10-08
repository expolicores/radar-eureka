"""Unidad de trabajo de la ingesta sobre SQLAlchemy: una transacción por ejecución."""

from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from .repositories import SqlPurchaseRepository


class SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.purchases = SqlPurchaseRepository(self._session)
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
