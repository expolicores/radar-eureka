from datetime import UTC, datetime
from pathlib import Path

import pytest

from public_procurement.operations.domain.cycle import manual_operations_window, schedule


@pytest.mark.parametrize(
    ("utc", "expected"),
    [
        ("2026-10-14T11:59:00+00:00", "2026-10-14T07:00:00-05:00"),
        ("2026-10-14T12:00:00+00:00", "2026-10-14T19:00:00-05:00"),
        ("2026-10-15T00:01:00+00:00", "2026-10-15T07:00:00-05:00"),
    ],
)
def test_bogota_times(utc, expected):
    assert (
        schedule(datetime.fromisoformat(utc), "America/Bogota", "07:00,19:00", 12).isoformat()
        == expected
    )


@pytest.mark.parametrize(
    ("now", "start", "before"),
    [
        ("2026-10-19T22:25:00+00:00", "2026-10-17", "2026-10-20"),
        ("2026-10-20T07:00:00+00:00", "2026-10-18", "2026-10-21"),
        ("2026-10-16T18:59:59+00:00", "2026-10-14", "2026-10-17"),
        ("2026-10-16T19:00:00+00:00", "2026-10-14", "2026-10-17"),
        ("2026-10-17T03:00:00+00:00", "2026-10-14", "2026-10-17"),
        ("2026-10-17T05:00:00+00:00", "2026-10-15", "2026-10-18"),
        ("2026-03-01T19:00:00+00:00", "2026-02-27", "2026-03-02"),
        ("2024-03-01T19:00:00+00:00", "2024-02-28", "2024-03-02"),
        ("2026-12-31T22:00:00+00:00", "2026-12-29", "2027-01-01"),
    ],
)
def test_manual_window_includes_today_in_bogota_without_intraday_bounds(now, start, before):
    window = manual_operations_window(datetime.fromisoformat(now))
    assert tuple(value.isoformat() for value in window) == (start, before)
    assert all(type(value).__name__ == "date" for value in window)


def test_interval_and_invalid_hours():
    assert schedule(datetime(2026, 10, 14, 12, tzinfo=UTC), "America/Bogota", "", 12).hour == 12
    with pytest.raises(ValueError, match="hour must be"):
        schedule(datetime.now(UTC), "America/Bogota", "25:00", 12)


def test_task_policy_and_no_embedded_registration():
    root = Path(__file__).resolve().parents[3]
    script = (root / "scripts/register_eureka_task.ps1").read_text(encoding="utf-8")
    for text in (
        "SupportsShouldProcess",
        "StartWhenAvailable",
        "IgnoreNew",
        "WakeToRun = $false",
        "ShouldProcess",
        "LogonType Interactive",
    ):
        assert text in script
    launcher = (root / "scripts/run_eureka_cycle.ps1").read_text(encoding="utf-8")
    assert "Register-ScheduledTask" not in launcher
