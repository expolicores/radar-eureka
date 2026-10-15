"""Contrato de lectura SQL: relación proceso/versión documental vigente."""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .repositories import AcquisitionAttemptRecord as Attempt
from .repositories import DocumentProcessRecord as Relation
from .repositories import DocumentVersionRecord as Version


def process_ids_for_versions(session: Session, versions: set[uuid.UUID]) -> set[uuid.UUID]:
    return (
        set(
            session.scalars(
                select(Relation.process_id)
                .join(Version, Version.document_id == Relation.document_id)
                .where(Version.id.in_(versions))
            )
        )
        if versions
        else set()
    )


def scope(process_ids: list[uuid.UUID] | None = None) -> Any:
    attempts = select(Attempt.document_id).where(
        Attempt.status == "available", Attempt.version_id.is_not(None)
    )
    if process_ids is not None:
        attempts = attempts.join(Relation, Relation.document_id == Attempt.document_id).where(
            Relation.process_id.in_(process_ids)
        )
    latest = (
        select(
            Attempt.document_id,
            Attempt.version_id,
            func.row_number()
            .over(
                partition_by=Attempt.document_id,
                order_by=(Attempt.finished_at.desc(), Attempt.id.desc()),
            )
            .label("rank"),
        )
        .where(Attempt.status == "available", Attempt.version_id.is_not(None))
        .where(Attempt.document_id.in_(attempts))
        .subquery()
    )
    statement = (
        select(Relation.process_id, latest.c.version_id)
        .join(latest, latest.c.document_id == Relation.document_id)
        .where(latest.c.rank == 1)
    )
    if process_ids is not None:
        statement = statement.where(Relation.process_id.in_(process_ids))
    return statement.distinct().subquery()
