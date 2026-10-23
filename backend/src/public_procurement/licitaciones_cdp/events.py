"""Temporal provenance only. Historical events never borrow run/publication timestamps."""

from datetime import UTC, datetime
from typing import Any

from public_procurement.ingestion.services import canonical_process_identity

MESSAGES = {
    "metadata_only": "Sin documentos disponibles; evaluación basada en metadata.",
    "unknown_source": "Origen por verificar; se conserva la metadata útil.",
    "commercially_not_eligible": "No cumple la decisión comercial actual de Eureka.",
    "stale": "Fuera de la ventana reciente configurada.",
    "validity_closed": "Fecha límite vencida.",
    "validity_unknown": (
        "Fecha límite ausente o no verificable; no pasa a documentos automáticamente."
    ),
    "limit_deferred": "Diferido por el límite de procesamiento configurado.",
    "incomplete_row": "Información mínima insuficiente para procesar.",
    "provider_status_deadline_conflict": "El estado del proveedor contradice el deadline vencido.",
    "invalid_deadline_at": "La fecha límite no es válida.",
    "invalid_published_at": "La fecha de publicación no es válida.",
    "future_published_at": "La fecha de publicación está en el futuro.",
    "provider_ignores_limit": "El proveedor devolvió más filas que el límite solicitado.",
    "transient_retry": "Fallo transitorio; se aplica el único reintento configurado.",
    "unenriched_row_skipped": "Fila sin los campos enriquecidos requeridos.",
    "outside_local_scope": "Fila fuera del alcance local configurado.",
    "session_expired": "Sesión expirada. Inicia sesión manualmente y vuelve a ejecutar.",
    "cdp_unavailable": "Edge CDP no está disponible.",
    "unsupported_format": "Formato documental no compatible.",
    "extraction_failed": "Falló la extracción documental.",
    "document_download_failed": "Falló la descarga documental.",
    "partial_coverage": "Cobertura documental parcial.",
    "ocr_truncated": "OCR limitado a 20 páginas.",
    "suspicious_fact": "Hay hechos documentales que requieren revisión humana.",
    "missing_documents": "Faltan documentos requeridos.",
}
DISCARD_CODES = {
    "outside_local_scope",
    "stale",
    "closed",
    "validity_closed",
    "validity_unknown",
    "commercially_not_eligible",
    "limit_deferred",
    "deferred_by_limit",
    "metadata_object_exclusion",
    "incomplete_row",
    "unenriched_row_skipped",
    "missing_canonical_identity",
}
ERROR_CODES = {
    "extraction_failed",
    "document_download_failed",
    "network_error",
    "invalid_response",
    "process_error",
    "source_error",
}


def event_type(code: str) -> str:
    return "discard" if code in DISCARD_CODES else "error" if code in ERROR_CODES else "warning"


def notice(
    value: Any, run_id: str, at: datetime | None = None, process: dict[str, Any] | None = None
) -> dict[str, Any]:
    event = dict(value) if isinstance(value, dict) else {"code": str(value)}
    code = str(event.get("code") or "unknown_event")
    event.update(code=code, run_id=run_id)
    event.setdefault("event_type", event_type(code))
    event.setdefault("message", MESSAGES.get(code, f"Incidencia registrada: {code}."))
    event.setdefault("generated_at", at.astimezone(UTC).isoformat() if at else None)
    event["timestamp_status"] = "recorded" if event["generated_at"] else "not_recorded"
    event.setdefault("process_identity", None)
    if process:
        metadata = process.get("metadata", process)
        reference = (
            metadata.get("source_identity")
            or metadata.get("id_ultima_fase")
            or metadata.get("process_reference")
        )
        event["process_identity"] = process.get("canonical_identity") or (
            canonical_process_identity(
                str(reference), metadata.get("raw_source_reference", {}).get("Link")
            )
            if reference
            else None
        )
        event.setdefault("codigo_proceso", metadata.get("codigo_proceso"))
        event.setdefault("stage", process.get("stage", "metadata"))
        event.setdefault("source", metadata.get("provider_source", "unknown"))
    return event


def annotate_run(run: dict[str, Any], at: datetime | None = None) -> dict[str, Any]:
    """New events get generation time; legacy read projection exposes explicitly unknown time."""
    identifier = str(run["id"])
    items = run.get("items", [])
    by_reference = {}
    for item in items:
        m = item.get("metadata", {})
        for ref in (item.get("secop_id"), m.get("process_reference"), m.get("id_ultima_fase")):
            if ref:
                by_reference[ref] = item

    def events(values: list[Any], item: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return [
            notice(
                v,
                identifier,
                at,
                item
                or by_reference.get(v.get("process_reference") if isinstance(v, dict) else None),
            )
            for v in values
        ]

    run["errors"] = events(run.get("errors", []))
    for error in run["errors"]:
        error["event_type"] = "error"
    metrics = run.setdefault("metrics", {})
    for key in ("warnings", "process_warning_details", "process_error_details"):
        metrics[key] = events(metrics.get(key, []))
    preflight = metrics.get("preflight", {})
    if "warnings" in preflight:
        preflight["warnings"] = events(preflight["warnings"])
    for query in metrics.get("queries", []):
        query["warnings"] = events(query.get("warnings", []))
        if query.get("error_code"):
            query["error"] = notice(
                query.get("error") or {"code": query["error_code"]}, identifier, at
            )
            query["error"]["event_type"] = "error"
    for item in items:
        for key in ("warnings", "errors"):
            if key in item:
                item[key] = events(item[key], item)
                if key == "errors":
                    for error in item[key]:
                        error["event_type"] = "error"
        if item.get("error"):
            item["error"] = notice(
                {"code": item.get("reason", "process_error"), **item["error"]}, identifier, at, item
            )
        reason = item.get("reason")
        if reason in DISCARD_CODES and not item.get("discard_event"):
            item["discard_event"] = notice({"code": reason}, identifier, at, item)
    groups: dict[str, list[dict[str, Any]]] = {"discard": [], "warning": [], "error": []}
    values = [
        *run["errors"],
        *metrics.get("warnings", []),
        *metrics.get("process_warning_details", []),
        *metrics.get("process_error_details", []),
        *preflight.get("warnings", []),
    ]
    for query in metrics.get("queries", []):
        values.extend(query.get("warnings", []))
        if query.get("error"):
            values.append(query["error"])
    for item in items:
        values.extend(item.get("warnings", []))
        values.extend(item.get("errors", []))
        if item.get("discard_event"):
            values.append(item["discard_event"])
    seen = set()
    for value in values:
        event_key = tuple(
            str(value.get(k))
            for k in (
                "code",
                "process_identity",
                "process_reference",
                "generated_at",
                "search_id",
                "document_version_id",
            )
        )
        if event_key not in seen:
            seen.add(event_key)
            category = value.get("event_type", event_type(value["code"]))
            groups[category if category in groups else event_type(value["code"])].append(value)
    metrics["event_groups"] = groups
    return run
