"""Local publication freshness, with a frozen run clock and no provider requests."""

from datetime import datetime, timedelta, timezone

from licitaciones_event_time import timed_warning

BOGOTA = timezone(timedelta(hours=-5), name="America/Bogota")
DEFAULT_RECENT_DAYS = 7


def local_now():
    return datetime.now(BOGOTA)


def validate_recent_days(value):
    if type(value) is not int or value < 1:
        raise ValueError("recent-days debe ser un entero positivo.")
    return value


def apply_freshness(processes, recent_days=DEFAULT_RECENT_DAYS, now=None):
    """Preserve every process; invalid/future dates are never document candidates.

    Naive provider timestamps and naive injected clocks mean Bogota local time.
    Aware timestamps retain their offset. The boundary is inclusive, without
    rounding age before comparison. stale_processes counts all non-recent rows.
    """
    validate_recent_days(recent_days)
    now = now or local_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=BOGOTA)
    annotated, warnings = [], []
    invalid = 0
    for source in processes:
        process = {**source, "age_days": None, "recent": False}
        codes = []
        try:
            published = datetime.fromisoformat(
                str(source.get("published_at")).replace("Z", "+00:00")
            )
            if published.tzinfo is None:
                published = published.replace(tzinfo=BOGOTA)
            age = (now - published).total_seconds() / 86400
            process["age_days"] = round(age, 6)
            process["recent"] = 0 <= age <= recent_days
            if age < 0:
                codes.append("future_published_at")
        except (ValueError, TypeError, OverflowError):
            invalid += 1
            codes.append("invalid_published_at")
        process["freshness_warnings"] = codes
        warnings.extend(
            timed_warning(
                {
                    "stage": "freshness",
                    "code": code,
                    "process_reference": source["process_reference"],
                }
            )
            for code in codes
        )
        annotated.append(process)

    def is_secop(process):
        return (
            str(process.get("id_fuente_contract")) == "3" or process.get("key_config") == "secop2"
        )

    metrics = {
        "unique_processes_total": len(annotated),
        "unique_processes_recent": sum(p["recent"] for p in annotated),
        "secop_ii_total": sum(is_secop(p) for p in annotated),
        "secop_ii_recent": sum(is_secop(p) and p["recent"] for p in annotated),
        "stale_processes": sum(not p["recent"] for p in annotated),
        "invalid_published_at": invalid,
    }
    return annotated, metrics, warnings
