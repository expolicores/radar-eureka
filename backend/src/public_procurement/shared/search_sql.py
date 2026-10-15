"""Expresiones de lectura idénticas a los índices de Fase 4.3."""

from typing import Any

from sqlalchemy import func, literal_column


def vector(expression: Any) -> Any:
    return func.to_tsvector(
        literal_column("'spanish'::regconfig"), func.public.search_normalize_v1(expression)
    )


def values_text(expression: Any) -> Any:
    return func.public.search_values_v1(expression)


def match(expression: Any, query: str) -> Any:
    return vector(expression).op("@@")(
        func.to_tsquery(literal_column("'spanish'::regconfig"), query)
    )
