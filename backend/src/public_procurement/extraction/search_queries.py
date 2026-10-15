"""Búsqueda y snapshots actuales: lecturas privadas del módulo extraction."""

import uuid
from collections import defaultdict
from dataclasses import asdict
from typing import Any

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session

from public_procurement.documents.services import (
    document_search_scope,
    search_processes_for_document_versions,
)
from public_procurement.shared.search_sql import match, values_text

from .canonical_repositories import CanonicalEvidenceRecord, CanonicalFactRecord
from .consolidation import digest_inputs
from .domain.canonical import CONSOLIDATION_VERSION
from .domain.content import REUSABLE_STATUSES
from .domain.structured import RULE_VERSION
from .repositories import ContentFragmentRecord as Fragment
from .repositories import ExtractionRunRecord as Run
from .structured_repositories import StructuredFactRecord as Structured
from .structured_repositories import as_fact


def active_fragments(process_ids: list[uuid.UUID] | None = None) -> Any:
    documents = document_search_scope(process_ids)
    ranked = (
        select(
            Run.id,
            Run.document_version_id,
            func.row_number()
            .over(
                partition_by=Run.document_version_id,
                order_by=(Run.finished_at.desc(), Run.id.desc()),
            )
            .label("rank"),
        )
        .where(Run.status.in_(REUSABLE_STATUSES), Run.fragment_count > 0)
        .where(Run.document_version_id.in_(select(documents.c.version_id)))
        .subquery()
    )
    return (
        select(
            documents.c.process_id,
            Fragment.id.label("fragment_id"),
            Fragment.extraction_run_id,
            ranked.c.document_version_id,
        )
        .join(ranked, ranked.c.document_version_id == documents.c.version_id)
        .join(Fragment, Fragment.extraction_run_id == ranked.c.id)
        .where(ranked.c.rank == 1)
        .subquery()
    )


def candidates(session: Session, query: str) -> set[uuid.UUID]:
    canonical_ids = select(CanonicalFactRecord.process_id).where(
        CanonicalFactRecord.rule_version == CONSOLIDATION_VERSION,
        match(
            values_text(CanonicalFactRecord.canonical_value.op("->")(literal_column("'value'"))),
            query,
        ),
    )
    structured_ids = select(Structured.process_id).where(
        Structured.rule_version == RULE_VERSION,
        match(
            func.coalesce(Structured.string_value, literal_column("''"))
            + literal_column("' '")
            + values_text(Structured.normalized_value),
            query,
        ),
    )
    text_versions = (
        select(Run.document_version_id)
        .join(Fragment, Fragment.extraction_run_id == Run.id)
        .where(match(Fragment.normalized_text, query))
    )
    # Broad candidates can include history; snapshots performs the authoritative
    # current-version/digest check before anything becomes a search result.
    text_ids = search_processes_for_document_versions(session, set(session.scalars(text_versions)))
    return set(session.scalars(canonical_ids.union(structured_ids))) | text_ids


def snapshots(
    session: Session, process_ids: list[uuid.UUID], query: dict[str, str] | None
) -> dict[uuid.UUID, dict[str, Any]]:
    active = active_fragments(process_ids)
    expressions = query or {}
    rows = session.execute(select(active)).all()
    active_ids: dict[uuid.UUID, set[str]] = defaultdict(set)
    for row in rows:
        active_ids[row.process_id].add(str(row.fragment_id))
    current_structured: dict[uuid.UUID, list[Any]] = defaultdict(list)
    structured_flags = [
        (
            key,
            match(
                func.coalesce(Structured.string_value, "")
                + " "
                + values_text(Structured.normalized_value),
                expression,
            ),
        )
        for key, expression in expressions.items()
    ]
    structured_queries = {}
    for row in session.execute(
        select(Structured, *(value for _, value in structured_flags)).where(
            Structured.process_id.in_(process_ids), Structured.rule_version == RULE_VERSION
        )
    ):
        record = row[0]
        structured_queries[record.id] = [
            key for (key, _), found in zip(structured_flags, row[1:], strict=True) if found
        ]
        fact = as_fact(record)
        sources = fact.source_locator.get("sources", [])
        if sources and all(
            source.get("content_fragment_id") in active_ids[fact.process_id] for source in sources
        ):
            current_structured[fact.process_id].append(fact)
    digests = {pid: digest_inputs(current_structured[pid]) for pid in process_ids}
    canonical: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    canonical_flags = [
        (key, match(values_text(CanonicalFactRecord.canonical_value["value"]), expression))
        for key, expression in expressions.items()
    ]
    for row in session.execute(
        select(CanonicalFactRecord, *(value for _, value in canonical_flags)).where(
            CanonicalFactRecord.process_id.in_(process_ids),
            CanonicalFactRecord.rule_version == CONSOLIDATION_VERSION,
        )
    ):
        record = row[0]
        if record.input_digest == digests[record.process_id]:
            canonical[record.process_id].append(
                {
                    "id": str(record.id),
                    "type": record.canonical_type,
                    "value": record.canonical_value.get("value"),
                    "status": record.status,
                    "_queries": [
                        key
                        for (key, _), found in zip(canonical_flags, row[1:], strict=True)
                        if found
                    ],
                }
            )
    texts: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    if query:
        text_flags = [
            (key, match(Fragment.normalized_text, expression))
            for key, expression in expressions.items()
        ]
        statement = (
            select(active.c.process_id, Fragment, *(value for _, value in text_flags))
            .join(Fragment, Fragment.id == active.c.fragment_id)
            .where(match(Fragment.normalized_text, " | ".join(expressions.values())))
            .order_by(Fragment.ordinal)
        )
        for row in session.execute(statement):
            pid, fragment = row[:2]
            texts[pid].append(
                {
                    "id": str(fragment.id),
                    "text": fragment.text,
                    "locator": fragment.source_locator,
                    "_queries": [
                        key for (key, _), found in zip(text_flags, row[2:], strict=True) if found
                    ],
                }
            )
    return {
        pid: {
            "canonical": canonical[pid],
            "structured": [
                {**asdict(f), "_queries": structured_queries[f.id]} for f in current_structured[pid]
            ],
            "text": texts[pid],
        }
        for pid in process_ids
    }


def evidence(
    session: Session,
    process_id: uuid.UUID,
    canonical_id: uuid.UUID | None,
    fragment_id: uuid.UUID | None,
) -> list[dict[str, Any]]:
    data = snapshots(session, [process_id], None)[process_id]
    if canonical_id:
        if not any(c["id"] == str(canonical_id) for c in data["canonical"]):
            return []
        ids = set(
            session.scalars(
                select(CanonicalEvidenceRecord.structured_fact_id).where(
                    CanonicalEvidenceRecord.canonical_fact_id == canonical_id
                )
            )
        )
        return [
            {"evidence_text": fact["evidence_text"], "source_locator": fact["source_locator"]}
            for fact in data["structured"]
            if fact["id"] in ids
        ]
    if fragment_id:
        active = active_fragments([process_id])
        fragment = session.scalar(
            select(Fragment)
            .join(active, active.c.fragment_id == Fragment.id)
            .where(Fragment.id == fragment_id)
        )
        if fragment:
            return [
                {
                    "evidence_text": fragment.text,
                    "source_locator": {
                        "sources": [
                            {
                                "text": fragment.text,
                                "locator": fragment.source_locator,
                                "content_fragment_id": str(fragment.id),
                            }
                        ]
                    },
                }
            ]
    return []
