"""One read-only tool, backed by the existing CDP query facade."""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol

from sqlalchemy.orm import sessionmaker

from public_procurement.licitaciones_cdp.services import LicitacionesQueries
from public_procurement.shared.config import Settings
from public_procurement.shared.database import create_db_engine

from .schemas import LatestCdpRunSummary


class CdpQueries(Protocol):
    def runs(self, page: int = 1, page_size: int = 25) -> dict[str, Any]: ...


def codes(*groups: list[Any]) -> list[str]:
    """Only notice codes, never headers, exception messages or raw provider payloads."""
    result = []
    for group in groups:
        for item in group:
            code = item.get("code") if isinstance(item, dict) else item
            safe = (
                code
                if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", code)
                else "unclassified_notice"
            )
            if safe not in result:
                result.append(safe)
    return result[:30] + (["additional_notices_omitted"] if len(result) > 30 else [])


def summarize(run: dict[str, Any]) -> LatestCdpRunSummary:
    metrics = run.get("metrics") or {}
    fields = {
        k: metrics.get(k)
        for k in (
            "processes_total",
            "recent_processes",
            "open_processes",
            "processed",
            "review_candidates_total",
            "review_new_entries",
            "review_existing_entries",
            "alert_candidates",
        )
    }
    return LatestCdpRunSummary(
        has_run=True,
        run_id=str(run["id"]),
        started_at=run["started_at"],
        finished_at=run.get("finished_at"),
        status=run["status"],
        **fields,
        alerts_created=run.get("alerts_created"),
        duplicate_alerts=metrics.get("duplicate_alerts_skipped"),
        warnings=codes(
            metrics.get("warnings", []),
            metrics.get("process_warning_details", []),
            (metrics.get("preflight") or {}).get("warnings", []),
            *(query.get("warnings", []) for query in (metrics.get("queries") or [])),
        ),
        errors=codes(run.get("errors", []), metrics.get("process_error_details", [])),
    )


class LatestCdpRunTool:
    def __init__(self, queries: CdpQueries) -> None:
        self.queries = queries

    def get_latest_cdp_run(self) -> LatestCdpRunSummary:
        runs = self.queries.runs(page=1, page_size=1)["items"]
        return summarize(runs[0]) if runs else LatestCdpRunSummary(has_run=False)

    def dispatch(self, name: str, arguments: dict[str, Any]) -> Any:
        if name != "get_latest_cdp_run" or arguments:
            raise ValueError("Tool no permitida")
        return self.get_latest_cdp_run()


@contextmanager
def read_only_tool(settings: Settings) -> Iterator[LatestCdpRunTool]:
    engine = create_db_engine(settings)
    try:
        if engine.dialect.name != "postgresql":
            raise ValueError("El spike requiere PostgreSQL con transacciones de solo lectura.")
        # SQLAlchemy/psycopg sets READ ONLY for every transaction, including future
        # changes to a query facade. No SQL queries or writer services in this adapter.
        readonly = engine.execution_options(postgresql_readonly=True)
        from public_procurement.eureka.services import (
            build_assistant_read_queries,
            get_eureka_commercial_profile,
        )

        from .read_tools import EurekaReadTools

        sessions = sessionmaker(readonly, autoflush=False)
        yield EurekaReadTools(
            LicitacionesQueries(sessions),
            build_assistant_read_queries(sessions, settings),
            profile=lambda: get_eureka_commercial_profile(settings),
        )
    finally:
        engine.dispose()
