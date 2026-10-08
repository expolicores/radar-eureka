"""Servicios de casos de investigación: única puerta de entrada al módulo.

Arma las instantáneas con `comparison.services` (señales) y `exploration.services` (compras).
Todas las operaciones reciben el dueño: un caso ajeno se trata como inexistente.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.comparison.services import (
    SignalDetail,
    SignalQueryService,
    build_signal_query_service,
)
from public_procurement.exploration.services import (
    ExplorationService,
    PurchaseDetailView,
    build_exploration_service,
)

from .domain.case import (
    CaseDetail,
    CaseItem,
    CaseItemKind,
    CaseNote,
    CaseNotFoundError,
    CaseSummary,
    InvalidCaseDataError,
    InvestigationError,
    ReferenceNotFoundError,
    SaveResult,
    clean_note,
    clean_title,
)
from .repositories import SqlCaseRepository

__all__ = [
    "CaseDetail",
    "CaseItem",
    "CaseItemKind",
    "CaseNotFoundError",
    "CaseSummary",
    "InvalidCaseDataError",
    "InvestigationError",
    "InvestigationService",
    "ReferenceNotFoundError",
    "SaveResult",
    "build_investigation_service",
]


def signal_snapshot(detail: SignalDetail) -> dict[str, Any]:
    signal = detail.signal
    return {
        "code": signal.code,
        "purchase_id": str(signal.purchase_id),
        "purchase_reference": signal.purchase_reference,
        "item_description": signal.item_description,
        "quantity": signal.quantity,
        "entity_name": signal.entity_name,
        "unit_price_cop": signal.unit_price_cop,
        "median_cop": signal.median_cop,
        "deviation_pct": str(signal.deviation_pct),
        "confidence_level": signal.confidence_level.value,
        "config_version_id": detail.config_version_id,
    }


def purchase_snapshot(detail: PurchaseDetailView) -> dict[str, Any]:
    summary = detail.summary
    return {
        "purchase_id": str(summary.id),
        "reference": summary.reference,
        "entity_name": summary.entity_name,
        "supplier_name": summary.supplier_name,
        "total_value_cop": summary.total_value_cop,
        "signed_on": summary.signed_on.isoformat(),
        "analysis_status": summary.analysis_status.value,
    }


class _SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.cases = SqlCaseRepository(self._session)
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


class InvestigationService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        signals: SignalQueryService,
        exploration: ExplorationService,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._session_factory = session_factory
        self._signals = signals
        self._exploration = exploration
        self._clock = clock

    def create_case(self, owner_id: uuid.UUID, title: str) -> CaseDetail:
        with _SqlUnitOfWork(self._session_factory) as unit_of_work:
            case_id = unit_of_work.cases.create(owner_id, clean_title(title), self._clock())
            return unit_of_work.cases.get(owner_id, case_id)

    def list_cases(self, owner_id: uuid.UUID) -> list[CaseSummary]:
        with _SqlUnitOfWork(self._session_factory) as unit_of_work:
            return unit_of_work.cases.list_for(owner_id)

    def get_case(self, owner_id: uuid.UUID, case_id: uuid.UUID) -> CaseDetail:
        with _SqlUnitOfWork(self._session_factory) as unit_of_work:
            return unit_of_work.cases.get(owner_id, case_id)

    def _snapshot(self, kind: CaseItemKind, reference: str) -> dict[str, Any]:
        if kind is CaseItemKind.SIGNAL:
            signal = self._signals.get_signal(reference)
            if signal is None:
                raise ReferenceNotFoundError
            return signal_snapshot(signal)
        try:
            purchase_id = uuid.UUID(reference)
        except ValueError as exc:
            raise ReferenceNotFoundError from exc
        purchase = self._exploration.get_purchase(purchase_id)
        if purchase is None:
            raise ReferenceNotFoundError
        return purchase_snapshot(purchase)

    def save_item(
        self, owner_id: uuid.UUID, case_id: uuid.UUID, kind: CaseItemKind, reference: str
    ) -> tuple[SaveResult, CaseDetail]:
        """Guarda una señal o una compra como instantánea inmutable del momento."""
        with _SqlUnitOfWork(self._session_factory) as unit_of_work:
            unit_of_work.cases.ensure_owned(owner_id, case_id)
            item = CaseItem(kind, reference, self._snapshot(kind, reference), self._clock())
            result = unit_of_work.cases.add_item(owner_id, case_id, item)
            return result, unit_of_work.cases.get(owner_id, case_id)

    def add_note(self, owner_id: uuid.UUID, case_id: uuid.UUID, body: str) -> CaseDetail:
        # El texto de la nota es libre: nunca se escribe en los logs (puede tener datos L3).
        with _SqlUnitOfWork(self._session_factory) as unit_of_work:
            unit_of_work.cases.add_note(
                owner_id, case_id, CaseNote(clean_note(body), self._clock())
            )
            return unit_of_work.cases.get(owner_id, case_id)


def build_investigation_service(session_factory: sessionmaker[Session]) -> InvestigationService:
    return InvestigationService(
        session_factory,
        build_signal_query_service(session_factory),
        build_exploration_service(session_factory),
    )
