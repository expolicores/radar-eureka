"""One aggregate request, no retries, discovery, mapping or process persistence."""

import json
from datetime import UTC, date, datetime
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ..domain.process import SECOP_PROCESS_DATASET
from .socrata_processes import ENDPOINT, PUBLICATION_FIELD

BOGOTA = ZoneInfo("America/Bogota")
SELECT = f"max({PUBLICATION_FIELD}) AS latest_available_date"


def diagnose_availability(start: date, before: date) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "performed": True,
        "endpoint": ENDPOINT,
        "dataset": SECOP_PROCESS_DATASET,
        "temporal_field": PUBLICATION_FIELD,
        "availability_basis": "global_max_publication_date",
        "query_window_start": start.isoformat(),
        "query_window_before": before.isoformat(),
        "query_window_timezone": "America/Bogota",
        "latest_available_date": None,
        "latest_available_local_date": None,
        "status": "diagnostic_failed",
        "request_attempts": 1,
        "soql_select": SELECT,
    }
    request = Request(  # noqa: S310 -- fixed public HTTPS origin, no caller-supplied URL
        ENDPOINT + "?" + urlencode({"$select": SELECT, "$limit": "1"}),
        headers={"Accept": "application/json", "User-Agent": "PublicProcurement/0.1"},
    )
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310
            body = json.load(response)
        if not isinstance(body, list) or len(body) != 1 or not isinstance(body[0], dict):
            raise ValueError("invalid_aggregate_response")
        raw = body[0].get("latest_available_date")
        if not isinstance(raw, str) or not raw.strip():
            diagnostic["error"] = {"code": "latest_date_unavailable"}
            return diagnostic
        if len(raw) == 10:
            latest_day = date.fromisoformat(raw)
            diagnostic["latest_available_date"] = latest_day.isoformat()
            diagnostic["date_precision"] = "day"
        else:
            latest = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if latest.tzinfo is None:
                # Floating timestamp has no inherent zone. Explicit publisher-zone assumption.
                latest = latest.replace(tzinfo=BOGOTA)
                diagnostic["naive_timestamp_timezone_assumption"] = "America/Bogota"
            latest_day = latest.astimezone(BOGOTA).date()
            diagnostic["latest_available_date"] = latest.astimezone(UTC).isoformat()
            diagnostic["date_precision"] = "timestamp"
        diagnostic.update(
            latest_available_local_date=latest_day.isoformat(),
            latest_before_window_start=latest_day < start,
            status="dataset_lag" if latest_day < start else "no_rows_in_window",
        )
    except Exception as error:
        # Do not log response bodies, request headers, credentials or arbitrary exception messages.
        diagnostic["error"] = {"code": "availability_query_failed", "type": type(error).__name__}
        if isinstance(error, HTTPError):
            diagnostic["error"]["http_status"] = error.code
    return diagnostic
