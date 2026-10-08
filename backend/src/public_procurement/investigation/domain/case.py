"""Casos de investigación privados: elementos guardados como instantánea y notas.

Una instantánea conserva la evidencia tal como la vio el Analista: nunca se modifica, aunque la
señal o los benchmarks se recalculen.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

MAX_TITLE_LENGTH = 120
MAX_NOTE_LENGTH = 5_000


class CaseItemKind(StrEnum):
    SIGNAL = "signal"
    PURCHASE = "purchase"


class InvestigationError(Exception):
    """Datos inválidos o recurso inaccesible (la API los traduce a 400/404)."""


class InvalidCaseDataError(InvestigationError):
    def __init__(self, field: str) -> None:
        super().__init__(f"invalid_{field}")
        self.field = field


class CaseNotFoundError(InvestigationError):
    """Inexistente o de otro dueño: no se distinguen (privacidad)."""


class ReferenceNotFoundError(InvestigationError):
    """La señal o la compra que se quiere guardar no existe (o ya no está vigente)."""


class SaveResult(StrEnum):
    """Resultado de guardar un elemento: un duplicado es un estado de negocio, no un error."""

    SAVED = "saved"
    ALREADY_SAVED = "already_saved"


def clean_title(title: str) -> str:
    cleaned = title.strip()
    if not 1 <= len(cleaned) <= MAX_TITLE_LENGTH:
        raise InvalidCaseDataError("title")
    return cleaned


def clean_note(body: str) -> str:
    cleaned = body.strip()
    if not 1 <= len(cleaned) <= MAX_NOTE_LENGTH:
        raise InvalidCaseDataError("body")
    return cleaned


@dataclass(frozen=True)
class CaseItem:
    kind: CaseItemKind
    reference: str
    snapshot: dict[str, Any]
    saved_at: datetime


@dataclass(frozen=True)
class CaseNote:
    body: str
    created_at: datetime


@dataclass(frozen=True)
class CaseSummary:
    id: uuid.UUID
    title: str
    item_count: int
    note_count: int
    created_at: datetime
    last_activity_at: datetime


@dataclass(frozen=True)
class CaseDetail:
    summary: CaseSummary
    items: tuple[CaseItem, ...]
    notes: tuple[CaseNote, ...]
