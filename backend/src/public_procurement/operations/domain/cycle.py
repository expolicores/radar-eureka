from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo


def manual_operations_window(now: datetime) -> tuple[date, date]:
    """Desde anteayer hasta mañana exclusivo, incluyendo hoy en Bogotá."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("La ventana manual requiere una hora con zona explícita.")
    local = now.astimezone(ZoneInfo("America/Bogota"))
    today = local.date()
    return today - timedelta(days=2), today + timedelta(days=1)


def schedule(now: datetime, timezone: str, run_times: str, interval: int) -> datetime:
    local = now.astimezone(ZoneInfo(timezone))
    times = [time.fromisoformat(t.strip()) for t in run_times.split(",") if t.strip()]
    if not times:
        # Stable anchor, rather than a moving now+interval prediction on each GET.
        anchor = datetime(1970, 1, 1, tzinfo=local.tzinfo)
        elapsed = (local - anchor).total_seconds()
        return anchor + timedelta(hours=(int(elapsed // (interval * 3600)) + 1) * interval)
    if any(t.tzinfo is not None for t in times):
        raise ValueError("Las horas deben ser locales HH:MM, sin offset.")
    return min(
        dt
        for day in (0, 1)
        for t in times
        if (dt := datetime.combine(local.date() + timedelta(days=day), t, local.tzinfo)) > local
    )


def radar_allows_notifications(result: dict[str, Any]) -> bool:
    return result["status"] in ("completed", "partial") and not result.get("errors")
