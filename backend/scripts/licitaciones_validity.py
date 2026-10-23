"""Offer validity from get-info metadata only; never requests detail/documents."""

from datetime import datetime

from licitaciones_event_time import timed_warning
from licitaciones_freshness import BOGOTA, local_now


def parse_deadline(raw):
    """Naive provider values mean Bogota; normalize explicit offsets to Bogota."""
    if raw is None or raw == "":
        return None, None
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=BOGOTA)
        return value.astimezone(BOGOTA), None
    except (ValueError, TypeError, OverflowError):
        return None, "invalid_deadline_at"


def validity_counts(processes):
    """All validity counters cover recent SECOP II only, before document selection."""
    recent = [
        p
        for p in processes
        if p.get("recent")
        and (str(p.get("id_fuente_contract")) == "3" or p.get("key_config") == "secop2")
    ]
    return {
        "secop_ii_recent": len(recent),
        **{
            f"secop_ii_{status}": sum(p["validity_status"] == status for p in recent)
            for status in ("open", "closed", "unknown")
        },
        "provider_status_deadline_conflicts": sum(
            p["validity_warning"] == "provider_status_deadline_conflict" for p in recent
        ),
    }


def apply_validity(processes, now=None):
    now = now or local_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=BOGOTA)
    annotated, warnings = [], []
    for source in processes:
        evidence = source.get("raw_source_reference", {})
        raw = evidence.get("FechaVencimiento", source.get("deadline_at"))
        provider_status = evidence.get("EstadoProceso", source.get("provider_status"))
        deadline, warning = parse_deadline(raw)
        status = "unknown" if deadline is None else "open" if deadline > now else "closed"
        if status == "closed" and str(provider_status).strip().casefold() in {
            "published",
            "publicado",
            "abierto",
            "open",
        }:
            warning = "provider_status_deadline_conflict"
        process = {
            **source,
            "deadline_at": deadline.isoformat() if deadline else None,
            "deadline_timezone": "America/Bogota",
            "provider_status": provider_status,
            "validity_status": status,
            "validity_warning": warning,
        }
        annotated.append(process)
        # Historical/non-SECOP conflicts stay on their process, without summary noise.
        if (
            warning
            and process.get("recent")
            and (
                str(process.get("id_fuente_contract")) == "3"
                or process.get("key_config") == "secop2"
            )
        ):
            warnings.append(
                timed_warning(
                    {
                        "stage": "validity",
                        "code": warning,
                        "process_reference": process["process_reference"],
                    }
                )
            )
    return annotated, validity_counts(annotated), warnings
