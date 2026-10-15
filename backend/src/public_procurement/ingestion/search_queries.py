"""Consultas SECOP propias; no accede a otros módulos."""

import uuid
from typing import Any

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session

from public_procurement.shared.search_sql import match

from .process_repositories import SecopProcessRecord as Process


def metadata_text() -> Any:
    fields = (
        Process.title,
        Process.description,
        Process.reference,
        Process.id_del_proceso,
        Process.entity_name,
        Process.department,
        Process.municipality,
        Process.category_code,
    )
    expression: Any = func.coalesce(fields[0], literal_column("''"))
    for field in fields[1:]:
        expression = expression + literal_column("' '") + func.coalesce(field, literal_column("''"))
    return expression


def candidates(session: Session, query: str | None, filters: dict[str, Any]) -> set[uuid.UUID]:
    statement = select(Process.id)
    if filters.get("identifiers") is not None:
        statement = statement.where(Process.id.in_(filters["identifiers"]))
    if query:
        statement = statement.where(match(metadata_text(), query))
    for key in ("department", "municipality"):
        if filters.get(key):
            statement = statement.where(
                func.public.search_normalize_v1(getattr(Process, key)) == filters[key]
            )
    if filters.get("published_from"):
        statement = statement.where(Process.published_on >= filters["published_from"])
    if filters.get("published_to"):
        statement = statement.where(Process.published_on <= filters["published_to"])
    if filters.get("entity_query"):
        statement = statement.where(match(metadata_text(), filters["entity_query"]))
    return set(session.scalars(statement))


def records(
    session: Session, identifiers: list[uuid.UUID], expressions: dict[str, str]
) -> list[dict[str, Any]]:
    fields = (
        "title",
        "description",
        "reference",
        "id_del_proceso",
        "entity_name",
        "department",
        "municipality",
        "category_code",
    )
    flags = [
        (key + "." + field, match(func.coalesce(getattr(Process, field), ""), expression))
        for key, expression in expressions.items()
        for field in fields
    ]
    result = []
    for row in session.execute(
        select(Process, *(value for _, value in flags)).where(Process.id.in_(identifiers))
    ):
        record = row[0]
        data = {column.name: getattr(record, column.name) for column in Process.__table__.columns}
        data["_queries"] = [name for (name, _), found in zip(flags, row[1:], strict=True) if found]
        result.append(data)
    return result
