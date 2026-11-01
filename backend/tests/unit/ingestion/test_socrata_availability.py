import io
import json
from datetime import date
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from public_procurement.ingestion.adapters.socrata_availability import diagnose_availability


@pytest.mark.parametrize(
    ("raw", "status", "normalized"),
    [
        ("2026-10-20", "dataset_lag", "2026-10-20"),
        ("2026-10-21", "no_rows_in_window", "2026-10-21"),
        ("2026-10-23T23:00:00", "no_rows_in_window", "2026-10-24T04:00:00+00:00"),
        ("2026-10-21T02:00:00Z", "dataset_lag", "2026-10-21T02:00:00+00:00"),
        (None, "diagnostic_failed", None),
        ("invalid", "diagnostic_failed", None),
    ],
)
def test_aggregate_only_once_and_timezone(raw, status, normalized):
    body = io.BytesIO(json.dumps([{"latest_available_date": raw}]).encode())
    with patch(
        "public_procurement.ingestion.adapters.socrata_availability.urlopen", return_value=body
    ) as request:
        result = diagnose_availability(date(2026, 10, 21), date(2026, 10, 24))
    assert result["status"] == status
    assert result["latest_available_date"] == normalized
    request.assert_called_once()
    query = parse_qs(urlparse(request.call_args.args[0].full_url).query)
    assert query == {
        "$select": ["max(fecha_de_publicacion_del) AS latest_available_date"],
        "$limit": ["1"],
    }
    assert result["query_window_start"] == "2026-10-21"
    assert result["query_window_before"] == "2026-10-24"


def test_failure_no_retry_and_no_sensitive_error():
    with patch(
        "public_procurement.ingestion.adapters.socrata_availability.urlopen",
        side_effect=TimeoutError("secret token"),
    ) as request:
        result = diagnose_availability(date(2026, 10, 21), date(2026, 10, 24))
    request.assert_called_once()
    assert result["status"] == "diagnostic_failed"
    assert "secret" not in json.dumps(result)
    assert result["latest_available_date"] is None
