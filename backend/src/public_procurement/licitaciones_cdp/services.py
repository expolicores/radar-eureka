"""Manual source operation; all commercial decisions belong to Eureka services."""

import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.eureka.services import (
    build_radar_queries,
    build_source_pipeline,
    evaluate_source_alert,
    load_radar_config,
    source_review_eligible,
)
from public_procurement.ingestion.services import SecopProcess, canonical_process_identity
from public_procurement.shared.config import Settings

from .adapters import LicitacionesInfoSource, provider_identity, provider_metadata
from .events import annotate_run, notice
from .review import REASON_FLAGS, REVIEW_FLAGS, combine_document_reviews, review_reasons

SOURCE = "licitaciones_info_cdp"
SESSION_HELP = (
    "Sesión de Licitaciones.info no disponible. Abre el Edge CDP, inicia sesión, "
    "selecciona Vila Frontier y deja abierta la vista Contratos desktop. Luego vuelve a ejecutar."
)


def safe_json(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def source_record(process: dict[str, Any]) -> SecopProcess:
    notice = provider_identity(process)
    if notice is None:
        raise ValueError("Identidad estable del proveedor ausente")
    published = datetime.fromisoformat(process["published_at"]).date()
    amount = Decimal(process["amount"]) if process.get("amount") is not None else None
    return SecopProcess(
        notice,
        notice,
        process["codigo_proceso"],
        process.get("entity_name"),
        process.get("department"),
        process.get("municipality"),
        process["object"],
        process["object"],
        None,
        None,
        process.get("provider_status"),
        published,
        published,
        int(amount) if amount is not None and amount.is_finite() and amount >= 0 else None,
        None,
        process.get("raw_source_reference", {}).get("Link"),
        offer_deadline_raw=process.get("deadline_at"),
    )


class LicitacionesInfoRunService:
    def __init__(
        self,
        repository: Any,
        settings: Settings,
        source_factory: Callable[..., Any] = LicitacionesInfoSource,
        pipeline_factory: Callable[..., Any] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.repository, self.settings = repository, settings
        self.source_factory, self.pipeline_factory, self.clock = (
            source_factory,
            pipeline_factory,
            clock,
        )

    def run(
        self,
        identifier: uuid.UUID | None = None,
        on_started: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        at = self.clock()
        config = load_radar_config(self.settings.eureka_radar_config_path)
        run: dict[str, Any] = {
            "id": identifier or uuid.uuid4(),
            "started_at": at,
            "finished_at": None,
            "source": SOURCE,
            "status": "running",
            "start_date": (at - timedelta(days=7)).date(),
            "before_date": (at + timedelta(days=1)).date(),
            "regions": ["Boyacá", "Casanare"],
            "rule_version": config.version,
            "config_hash": hashlib.sha256(SOURCE.encode()).hexdigest(),
            "errors": [],
            "metrics": {},
            "items": [],
            **dict.fromkeys(
                (
                    "processes_seen",
                    "new_processes",
                    "candidates",
                    "enriched",
                    "alerts_created",
                    "skipped",
                    "failures",
                ),
                0,
            ),
        }
        metrics = run["metrics"]
        metrics.update(
            dict.fromkeys(
                (
                    "received",
                    "unique",
                    "recent",
                    "SECOP_II",
                    "open",
                    "documents",
                    "extracted",
                    "extraction_attempted",
                    "extraction_succeeded",
                    "extraction_failed",
                    "process_warnings",
                    "process_errors",
                    "canonicalized",
                    "commercially_eligible",
                    "scored",
                    "alert_candidates",
                    "alerts_created",
                    "duplicate_alerts_skipped",
                    "manual_review",
                ),
                0,
            )
        )
        metrics.update(
            extraction_metrics_version=2, process_warning_details=[], process_error_details=[]
        )
        current_item: dict[str, Any] | None = None

        def persist() -> None:
            annotate_run(run, self.clock())
            self.repository.finish(run)

        def mark_manual(item: dict[str, Any], flag: str) -> None:
            item.setdefault("document_review", {})[flag] = True
            item["manual_review_reasons"] = review_reasons(item["document_review"])
            if not item.get("requires_manual_document_review"):
                item["requires_manual_document_review"] = True
                metrics["manual_review"] += 1

        def issue(
            item: dict[str, Any], code: str, *, error: bool = False, document: str | None = None
        ) -> None:
            key = "errors" if error else "warnings"
            counter = "process_errors" if error else "process_warnings"
            entries = item.setdefault(key, [])
            detail = {
                "code": code,
                "stage": item["stage"],
                "process_reference": item["secop_id"],
                "codigo_proceso": item["metadata"]["codigo_proceso"],
            }
            if document is not None:
                detail["document_version_id"] = document
            if any(all(entry.get(k) == v for k, v in detail.items()) for entry in entries):
                return
            detail = notice(detail, str(run["id"]), self.clock(), item)
            metrics[counter] += int(not entries)
            entries.append(detail)
            metrics["process_error_details" if error else "process_warning_details"].append(detail)
            if error:
                run["errors"].append(detail)

        def event(name: str, data: dict[str, Any]) -> None:
            if name == "discovery_progress":
                metrics["stage"] = "preflight" if data.get("stage") == "preflight" else "discovery"
                if data.get("stage") == "preflight" and data.get("preflight_status"):
                    metrics["preflight"] = data
                    annotate_run(run, self.clock())
            elif name in {"inventory", "documents_selected"}:
                key = "documents" if name == "inventory" else "documents_selected"
                metrics[key] = metrics.get(key, 0) + data.get("count", 0)
            elif name == "extraction_result":
                succeeded = bool(data.get("succeeded"))
                metrics["extraction_attempted"] += 1
                metrics["extraction_succeeded"] += int(succeeded)
                metrics["extraction_failed"] += int(not succeeded)
                metrics["extracted"] = metrics["extraction_succeeded"]
                if current_item is not None:
                    if not succeeded:
                        mark_manual(current_item, "extraction_failed")
                        issue(
                            current_item,
                            data.get("error_code") or "extraction_failed",
                            error=True,
                            document=data.get("document_version_id"),
                        )
                    if (
                        data.get("coverage_complete") is False
                        or data.get("ocr") == "ocr_truncated"
                        or data.get("status") == "partial_text"
                    ):
                        mark_manual(current_item, "partial_document_coverage")
                        issue(
                            current_item,
                            "ocr_truncated"
                            if data.get("ocr") == "ocr_truncated"
                            else "partial_coverage",
                            document=data.get("document_version_id"),
                        )
            elif name == "document_download" and data.get("failed") and current_item is not None:
                mark_manual(current_item, "document_download_failed")
                issue(current_item, "document_download_failed", error=True)
            if current_item is not None:
                self.repository.outcome(run["id"], safe_json(current_item), self.clock(), False)
            persist()

        with self.repository.lock():
            self.repository.start(
                run,
                {
                    "source": SOURCE,
                    "profile_id": "1086005",
                    "recent_days": 7,
                    "max_queries": 6,
                    "pause_seconds": 4,
                    "max_document_processes": 3,
                    "max_documents": 2,
                    "manual_only": True,
                },
            )
            if on_started:
                on_started(run)
            try:
                with self.source_factory(event) as source:
                    discovery, summary = source.discover()
                    discovery["processes"] = [provider_metadata(p) for p in discovery["processes"]]
                    for key in (
                        "unique_processes_total",
                        "unique_processes_recent",
                        "secop_ii_total",
                        "secop_ii_recent",
                        "secop_ii_open",
                        "secop_ii_closed",
                        "secop_ii_unknown",
                        "provider_status_deadline_conflicts",
                    ):
                        metrics[key] = summary[key]
                    metrics.update(
                        received=summary["total_rows_received"],
                        unique=summary["unique_processes_total"],
                        recent=summary["unique_processes_recent"],
                        SECOP_II=summary["secop_ii_recent"],
                        open=sum(
                            p.get("recent") and p.get("validity_status") == "open"
                            for p in discovery["processes"]
                        ),
                        warnings=summary.get("warnings", []),
                        queries=summary.get("queries", []),
                        failed_queries=summary.get("failed_queries", 0),
                    )
                    if self.pipeline_factory is None:
                        raise RuntimeError("Pipeline Eureka compartido no configurado")
                    pipeline = self.pipeline_factory(source, event)
                    selected = 0
                    # Persist every discovered result before any slow document operation.
                    for process in discovery["processes"]:
                        item = {
                            "dataset_id": "licitaciones",
                            "secop_id": process["process_reference"],
                            "metadata": process,
                            "stage": "metadata",
                            "outcome": "skipped",
                            "source": SOURCE,
                            "alert_created": False,
                        }
                        run["items"].append(item)
                        self.repository.outcome(run["id"], safe_json(item), self.clock(), False)
                    run["processes_seen"] = len(run["items"])
                    persist()
                    for item in run["items"]:
                        current_item = item
                        process = item["metadata"]
                        try:
                            if not process["recent"]:
                                item["reason"] = "stale"
                            elif process.get("department", "").casefold() not in {
                                "boyacá",
                                "boyaca",
                                "casanare",
                            }:
                                item["reason"] = "outside_local_scope"
                            elif process["validity_status"] != "open":
                                item["reason"] = "validity_" + process["validity_status"]
                            elif not all(
                                process.get(k)
                                for k in ("object", "entity_name", "department", "published_at")
                            ):
                                item["reason"] = "incomplete_row"
                            elif provider_identity(process) is None:
                                item["reason"] = "missing_canonical_identity"
                            else:
                                record = source_record(process)
                                canonical = canonical_process_identity(
                                    record.id_del_proceso, record.source_url
                                )
                                item["canonical_identity"] = canonical
                                previous = self.repository.alert_for_canonical(canonical)
                                if previous:
                                    metrics["alert_candidates"] += 1
                                    metrics["duplicate_alerts_skipped"] += 1
                                    item.update(
                                        reason="duplicate_canonical",
                                        alert_id=str(previous["id"]),
                                        stage="completed",
                                        outcome="duplicate",
                                    )
                                elif selected >= 3:
                                    item["reason"] = "limit_deferred"
                                else:
                                    selected += 1
                                    run["candidates"] += 1
                                    if not process["document_capable"]:
                                        issue(item, "metadata_only")
                                    if process["provider_source"] == "unknown":
                                        issue(item, "unknown_source")

                                    def stage(name: str, item: dict[str, Any] = item) -> None:
                                        item["stage"] = name
                                        metrics["stage"] = name
                                        self.repository.outcome(
                                            run["id"], safe_json(item), self.clock(), False
                                        )
                                        persist()

                                    details = pipeline.enrich(record, stage)
                                    flags = {
                                        **item.get("document_review", {}),
                                        **source.review(pipeline, record.id_del_proceso),
                                    }
                                    for flag, value in item.get("document_review", {}).items():
                                        if isinstance(value, bool) and value:
                                            flags[flag] = True
                                    # Document quality flags never introduce another score gate.
                                    flags["missing_documents"] = (
                                        flags.get("missing_documents", False)
                                        or details.quality.get("document_status") == "unavailable"
                                    )
                                    flags = combine_document_reviews(
                                        flags,
                                        self.repository.document_review_history(
                                            SOURCE, process["process_reference"], run["id"]
                                        ),
                                        current_run_id=str(run["id"]),
                                    )
                                    manual = bool(flags["manual_review_reasons"])
                                    item["document_review"] = flags
                                    item["manual_review_reasons"] = flags["manual_review_reasons"]
                                    item["manual_review_provenance"] = flags[
                                        "manual_review_provenance"
                                    ]
                                    if manual and not item.get("requires_manual_document_review"):
                                        item["requires_manual_document_review"] = True
                                        metrics["manual_review"] += 1
                                    item.setdefault("requires_manual_document_review", False)
                                    for flag in REVIEW_FLAGS:
                                        if flags.get(flag):
                                            mark_manual(item, flag)
                                            issue(item, flag)
                                    for reason in flags["manual_review_reasons"]:
                                        if reason not in REASON_FLAGS:
                                            issue(item, reason)
                                    run["enriched"] += 1
                                    metrics["canonicalized"] += int(
                                        details.enrichment_status in ("consolidated", "conflict")
                                    )
                                    metrics["scored"] += int(details.score is not None)
                                    decision = evaluate_source_alert(record, details, self.settings)
                                    decision = replace(
                                        decision, review_required=decision.review_required or manual
                                    )
                                    decision.snapshot.update(
                                        source=SOURCE,
                                        canonical_identity=canonical,
                                        requires_manual_document_review=manual,
                                        manual_review_reasons=flags["manual_review_reasons"],
                                        manual_review_provenance=flags["manual_review_provenance"],
                                        **{
                                            k: bool(flags.get(k))
                                            for k in (
                                                "missing_documents",
                                                "partial_document_coverage",
                                                "suspicious_fact",
                                                "extraction_failed",
                                                "document_download_failed",
                                            )
                                        },
                                    )
                                    item["decision"] = safe_json(asdict(decision))
                                    item["process_id"] = str(details.process_id)
                                    item.update(stage="completed", outcome="no_alert")
                                    if not decision.create:
                                        item["reason"] = "commercially_not_eligible"
                                    metrics["commercially_eligible"] += int(decision.create)
                                    if decision.create:
                                        metrics["alert_candidates"] += 1
                                        created = self.repository.alert(
                                            run["id"],
                                            details.opportunity_id,
                                            config.version,
                                            decision,
                                            self.clock(),
                                        )
                                        item.update(
                                            alert_created=created,
                                            outcome="alert" if created else "duplicate",
                                        )
                                        if not created:
                                            item["reason"] = "duplicate_canonical"
                                        metrics["alerts_created"] += int(created)
                                        metrics["duplicate_alerts_skipped"] += int(not created)
                                        run["alerts_created"] += int(created)
                        except Exception as error:
                            fallback = (
                                "document_download_failed"
                                if item["stage"] == "documents_download"
                                else "extraction_failed"
                                if item["stage"] in {"extraction", "extraction_partial"}
                                else "process_error"
                            )
                            code = getattr(error, "code", fallback)
                            if code in {"session_expired", "profile_unavailable", "invalid_tab"}:
                                raise
                            run["failures"] += 1
                            if code in {"unsupported_format", "extraction_failed"} or item[
                                "stage"
                            ] in {
                                "documents_sync",
                                "documents_download",
                                "extraction",
                                "extraction_partial",
                            }:
                                mark_manual(
                                    item,
                                    "document_download_failed"
                                    if item["stage"] == "documents_download"
                                    else "missing_documents"
                                    if item["stage"] == "documents_sync"
                                    else "extraction_failed",
                                )
                            issue(item, code, error=True)
                            item.update(
                                outcome="failed",
                                reason=code,
                                error=notice(
                                    {"code": code, "type": type(error).__name__},
                                    str(run["id"]),
                                    self.clock(),
                                    item,
                                ),
                            )
                        finally:
                            item["review_candidate"] = bool(
                                process.get("recent")
                                and process.get("validity_status") == "open"
                                and item.get("reason")
                                not in {
                                    "outside_local_scope",
                                    "incomplete_row",
                                    "missing_canonical_identity",
                                }
                                and source_review_eligible(item)
                            )
                            run["skipped"] += int(item["outcome"] == "skipped")
                            self.repository.outcome(run["id"], safe_json(item), self.clock(), False)
                            persist()
                    run["status"] = (
                        "completed_with_warnings"
                        if run["failures"]
                        or metrics.get("warnings")
                        or metrics["manual_review"]
                        or metrics["failed_queries"]
                        or metrics["process_errors"]
                        or metrics["process_warnings"]
                        else "completed"
                    )
            except Exception as error:
                code = getattr(error, "code", "source_error")
                preflight = getattr(error, "preflight", None)
                if preflight:
                    metrics["preflight"] = preflight
                run["status"] = (
                    "session_unavailable"
                    if code
                    in {
                        "session_expired",
                        "cdp_unavailable",
                        "invalid_tab",
                        "profile_unavailable",
                        "preflight_failed",
                    }
                    else "failed"
                )
                run["errors"].append(
                    notice(
                        {"code": code, "type": type(error).__name__}, str(run["id"]), self.clock()
                    )
                )
                if run["status"] == "session_unavailable":
                    metrics["instruction"] = SESSION_HELP
            finally:
                run["finished_at"] = self.clock()
                items = run["items"]
                recent_items = [i for i in items if i["metadata"].get("recent")]
                metrics.update(
                    processes_total=len(items),
                    recent_processes=len(recent_items),
                    open_processes=sum(
                        i["metadata"].get("validity_status") == "open" for i in recent_items
                    ),
                    closed_processes=sum(
                        i["metadata"].get("validity_status") == "closed" for i in recent_items
                    ),
                    unknown_validity_processes=sum(
                        i["metadata"].get("validity_status") == "unknown" for i in recent_items
                    ),
                    document_capable=sum(
                        i["metadata"].get("document_capable", False)
                        for i in recent_items
                        if i["metadata"].get("validity_status") == "open"
                    ),
                    metadata_only=sum(
                        i.get("decision", {}).get("snapshot", {}).get("document_status")
                        == "unavailable"
                        for i in items
                    ),
                    processed=sum(
                        i.get("outcome") in {"alert", "no_alert", "failed"} for i in items
                    ),
                    review_candidates=sum(bool(i.get("review_candidate")) for i in items),
                )
                metrics["by_source"] = {}
                for item in items:
                    kind = item["metadata"].get("provider_source", "unknown")
                    counts = metrics["by_source"].setdefault(
                        kind,
                        {
                            "processes_total": 0,
                            "recent_processes": 0,
                            "open_processes": 0,
                            "processed": 0,
                            "alerts_created": 0,
                            "review_candidates": 0,
                        },
                    )
                    counts["processes_total"] += 1
                    counts["recent_processes"] += int(bool(item["metadata"].get("recent")))
                    counts["open_processes"] += int(
                        bool(item["metadata"].get("recent"))
                        and item["metadata"].get("validity_status") == "open"
                    )
                    counts["processed"] += int(
                        item.get("outcome") in {"alert", "no_alert", "failed"}
                    )
                    counts["alerts_created"] += int(bool(item.get("alert_created")))
                    counts["review_candidates"] += int(bool(item.get("review_candidate")))
                metrics["duration_seconds"] = (run["finished_at"] - at).total_seconds()
                persist()
        return run


def build_run_service(
    sessions: sessionmaker[Session], settings: Settings
) -> LicitacionesInfoRunService:
    # Reuse the same repository lock as Radar: manual sources cannot overlap.
    bounded = settings.model_copy(
        update={
            "document_timeout_seconds": min(settings.document_timeout_seconds, 60),
            "document_max_bytes": min(settings.document_max_bytes, 20 * 1024 * 1024),
        }
    )
    return LicitacionesInfoRunService(
        build_radar_queries(sessions),
        bounded,
        pipeline_factory=lambda inventory, observer: build_source_pipeline(
            sessions, bounded, inventory, observer
        ),
    )


class LicitacionesQueries:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.repository = build_radar_queries(sessions)

    def runs(self, page: int = 1, page_size: int = 25) -> dict[str, Any]:
        result = self.repository.runs(page, page_size, SOURCE)
        result["items"] = [annotate_run(run) for run in result["items"]]
        return result

    def get_run(self, identifier: uuid.UUID) -> dict[str, Any]:
        run = self.repository.get_run(identifier)
        if run["source"] != SOURCE:
            raise LookupError("Corrida Licitaciones.info no encontrada")
        return annotate_run(run)
