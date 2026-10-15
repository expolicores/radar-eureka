"""Single local cycle; replaceable scheduler, source and file adapters."""

import platform
import time
import uuid
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import suppress
from datetime import UTC, date, datetime, timedelta
from importlib.metadata import version
from typing import Any, cast
from zoneinfo import ZoneInfo

from sqlalchemy import text

from public_procurement.eureka.services import build_radar_queries, build_radar_service
from public_procurement.extraction.services import ocr_runtime_status
from public_procurement.ingestion.services import ProcessQuery, SecopProcess, fetch_secop_processes
from public_procurement.notifications.services import build_notification_dispatcher
from public_procurement.shared.config import Settings

from .adapters.file_logs import CycleLogs
from .adapters.windows_scheduler import scheduler_status
from .domain.cycle import radar_allows_notifications, schedule
from .ports import Observer
from .repositories import CycleRepository, CycleSchemaPendingError

METRICS = (
    "secop_records_fetched",
    "outside_window",
    "outside_region",
    "already_seen",
    "limit_deferred",
    "prefilter_rejected",
    "candidates",
    "documents_processed",
    "documents_available",
    "document_download_failed",
    "document_sync_started",
    "document_sync_failed",
    "document_errors",
    "extraction_native",
    "extraction_reused",
    "extraction_ocr",
    "ocr_required",
    "ocr_unavailable",
    "extraction_failed",
    "consolidated",
    "canonical_reused",
    "enriched",
    "alert_created",
    "no_alert",
    "notification_prepared",
    "notification_sent",
    "notification_captured",
    "notification_failed",
)


def preflight(settings: Settings, sessions: Any, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    local = now.astimezone(ZoneInfo(settings.eureka_automation_timezone))
    start = settings.eureka_radar_start_date
    if start is None or start > local.date():
        raise ValueError("Configura EUREKA_RADAR_START_DATE, sin fecha futura.")
    next_run = schedule(
        now,
        settings.eureka_automation_timezone,
        settings.eureka_automation_run_times,
        settings.eureka_automation_interval_hours,
    )
    with sessions() as session:
        session.execute(text("SET TRANSACTION READ ONLY"))
        session.execute(text("SELECT 1"))
        ready = (
            session.scalar(text("SELECT to_regclass('operations.automation_cycle')")) is not None
        )
    return {
        "kind": "preflight_configuration_dry_run",
        "secop_queried": False,
        "db_connected": True,
        "schema_ready": ready,
        "ocr": ocr_runtime_status(settings),
        "window": {
            "from": start.isoformat(),
            "before": (local.date() + timedelta(days=1)).isoformat(),
            "before_exclusive": True,
            "timezone": settings.eureka_automation_timezone,
            "note": "Límite calendario exclusivo; no predice resultados SECOP.",
        },
        "next_theoretical": next_run.isoformat(),
        "stages": ["radar", "evaluate_global_coverage", "notifications", "metrics_logs"],
        "notification_mode": settings.eureka_notification_mode,
        "max_processes": settings.eureka_radar_max_processes,
    }


class AutomationCycleService:
    def __init__(
        self,
        repository: Any,
        radar: Callable[..., dict[str, Any]],
        notify: Callable[[], dict[str, Any]],
        logs: Any,
        settings: Settings,
        preflight_check: Callable[[], dict[str, Any]],
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        reconcile_radar: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.repository, self.radar, self.notify = repository, radar, notify
        self.logs, self.settings, self.preflight_check, self.clock = (
            logs,
            settings,
            preflight_check,
            clock,
        )
        self.reconcile_radar = reconcile_radar

    def run(
        self,
        *,
        dry_run: bool = False,
        trigger: str = "manual",
        cycle_id: uuid.UUID | None = None,
        on_started: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        config = self.preflight_check()
        if dry_run:
            return config
        if trigger == "scheduled" and not self.settings.eureka_automation_enabled:
            return {"status": "skipped", "reason": "automation_disabled"}
        self.repository.ready()
        now = self.clock().isoformat()
        cycle: dict[str, Any] = {
            "schema_version": 1,
            "id": str(cycle_id or uuid.uuid4()),
            "started_at": now,
            "finished_at": None,
            "heartbeat_at": now,
            "status": "running",
            "trigger": trigger,
            "host": platform.node(),
            "app_version": version("public-procurement"),
            "radar_run_id": str(uuid.uuid4()),
            "radar_linked": False,
            "notification_summary": {},
            "metrics": dict.fromkeys(METRICS, 0),
            "reasons": {},
            "errors": [],
            "events": [],
            "durations_ms": dict.fromkeys(
                (
                    "ingestion",
                    "prefilter",
                    "documents",
                    "extraction",
                    "ocr",
                    "consolidation",
                    "eureka",
                    "notifications",
                ),
                0,
            ),
            "duration_ms": None,
            "processes_seen": 0,
            "failures": 0,
            "config_snapshot": config,
            "stage": "starting",
            "source_summary": {
                "records_received": 0,
                "query_completed": False,
                "zero_records_confirmed": False,
                "remote_filters_applied": True,
            },
        }
        stem = f"eureka-cycle-{datetime.fromisoformat(now).strftime('%Y%m%d-%H%M%S')}-{cycle['id']}"
        cycle["log_files"] = {"log": stem + ".log", "summary": stem + ".json"}
        started = time.monotonic()
        last_stage: tuple[str, float] | None = None

        def checkpoint() -> None:
            cycle["heartbeat_at"] = self.clock().isoformat()
            self.repository.save(cycle)
            try:
                self.logs.write(cycle)
            except (OSError, ValueError):
                if not any(e["code"] == "log_write_failed" for e in cycle["errors"]):
                    cycle["errors"].append({"code": "log_write_failed", "stage": "logs"})
                    self.repository.save(cycle)

        def observe(event: str, data: dict[str, Any]) -> None:
            nonlocal last_stage
            verify()
            metrics = cycle["metrics"]
            if event == "radar_started":
                cycle["radar_linked"] = True
                cycle["stage"] = "secop"
            elif event == "secop_received":
                metrics["secop_records_fetched"] += 1
                cycle["source_summary"]["records_received"] = metrics["secop_records_fetched"]
            elif event in ("candidate", "enriched", "alert_created"):
                target = {
                    "candidate": "candidates",
                    "enriched": "enriched",
                    "alert_created": "alert_created",
                }[event]
                metrics[target] += int(data.get("created", True))
            elif event == "timing":
                cycle["durations_ms"][data["name"]] = (
                    cycle["durations_ms"].get(data["name"], 0) + data["ms"]
                )
            elif event == "stage":
                cycle["stage"] = data["name"]
                moment = time.monotonic()
                if last_stage:
                    name, since = last_stage
                    cycle["durations_ms"][name] = (
                        cycle["durations_ms"].get(name, 0) + (moment - since) * 1000
                    )
                last_stage = data["name"], moment
                if data["name"] == "documents_sync":
                    metrics["document_sync_started"] += 1
                if data["name"] == "canonical_reused":
                    metrics["canonical_reused"] += 1
            elif event == "documents":
                metrics["documents_processed"] += data["count"]
            elif event == "document_download":
                metrics["documents_available"] += data["available"]
                metrics["document_download_failed"] += data["failed"]
            elif event == "consolidated":
                metrics["consolidated"] += 1
            elif event == "extraction_result":
                metrics["extraction_reused"] += int(data.get("reused", False))
                metrics["extraction_native"] += int(data["native"])
                metrics["extraction_ocr"] += data["processed"]
                metrics["ocr_required"] += data["required"]
                metrics["ocr_unavailable"] += int(data["ocr"] == "ocr_unavailable")
                metrics["extraction_failed"] += int(data["failed"])
                cycle["durations_ms"]["ocr"] = (
                    cycle["durations_ms"].get("ocr", 0) + data["ocr_seconds"] * 1000
                )
            elif event == "process_result":
                cycle["processes_seen"] += 1
                metrics["no_alert"] += int(data["outcome"] == "no_alert")
                cycle["failures"] += int(
                    data["outcome"] == "failed" or data.get("coverage_incomplete", False)
                )
                if data.get("outcome") == "failed" or data.get("coverage_incomplete"):
                    cycle["errors"].append(
                        {
                            "code": "process_failed"
                            if data["outcome"] == "failed"
                            else "document_coverage_incomplete",
                            "stage": data["stage"],
                            "secop_id": data.get("secop_id"),
                            "type": data.get("error_type"),
                        }
                    )
                if last_stage:
                    name, since = last_stage
                    cycle["durations_ms"][name] = (
                        cycle["durations_ms"].get(name, 0) + (time.monotonic() - since) * 1000
                    )
                    last_stage = None
                reason = data.get("reason")
                if reason:
                    cycle["reasons"][reason] = cycle["reasons"].get(reason, 0) + 1
                    if reason in ("outside_window", "outside_region", "already_seen"):
                        metrics[reason] += 1
                    elif reason in (
                        "no_metadata_match",
                        "terminal_phase",
                        "strong_exclusion",
                        "publication_unknown",
                    ):
                        metrics["prefilter_rejected"] += 1
                if data["outcome"] == "failed" and data["stage"].startswith("documents"):
                    metrics["document_errors"] += 1
                    metrics["document_sync_failed"] += int(data["stage"] == "documents_sync")
            cycle["events"].append({"at": self.clock().isoformat(), "event": event, **data})
            checkpoint()

        with self.repository.lock() as verify:
            if verify is None:
                cycle.update(
                    status="skipped", reason="already_running", finished_at=self.clock().isoformat()
                )
                cycle["events"].append({"event": "already_running"})
                cycle["duration_ms"] = round((time.monotonic() - started) * 1000)
                checkpoint()
                if on_started:
                    on_started(cycle)
                return cycle
            # Owning the global lock proves previous coordinators are no longer active.
            for old in self.repository.running():
                if self.reconcile_radar:
                    self.reconcile_radar(old)
                old.update(status="failed", finished_at=self.clock().isoformat())
                old["duration_ms"] = max(
                    0,
                    round(
                        (self.clock() - datetime.fromisoformat(old["started_at"])).total_seconds()
                        * 1000
                    ),
                )
                old["events"].append(
                    {"event": "coordinator_interrupted", "at": self.clock().isoformat()}
                )
                old["errors"].append(
                    {
                        "code": "coordinator_interrupted",
                        "stage": "recovery",
                        "stale_diagnostic": (
                            self.clock() - datetime.fromisoformat(old["heartbeat_at"])
                        ).total_seconds()
                        > self.settings.eureka_automation_stale_minutes * 60,
                    }
                )
                self.repository.save(old)
                with suppress(OSError, ValueError):
                    self.logs.write(old)
            cycle["events"].append(
                {"event": "cycle_started", "at": now, "window": config["window"]}
            )
            checkpoint()
            try:
                if on_started:
                    on_started(cycle)
                verify()
                stage_start = time.monotonic()
                result = self.radar(uuid.UUID(cycle["radar_run_id"]), observe)
                cycle["durations_ms"]["radar"] = (time.monotonic() - stage_start) * 1000
                cycle["radar_status"] = result["status"]
                for target, names in (
                    ("documents", ("documents_sync", "documents_download")),
                    ("eureka", ("discovery", "alert_evaluation")),
                ):
                    cycle["durations_ms"][target] = sum(
                        cycle["durations_ms"].get(name, 0) for name in names
                    )
                metrics = cycle["metrics"]
                for key, source in (
                    ("candidates", "candidates"),
                    ("enriched", "enriched"),
                    ("alert_created", "alerts_created"),
                ):
                    metrics[key] = result[source]
                reasons = Counter(
                    item.get("reason") for item in result.get("items", []) if item.get("reason")
                )
                cycle["reasons"] = dict(reasons)
                cycle["decision_reasons"] = dict(
                    Counter(
                        code
                        for item in result.get("items", [])
                        for code in item.get("decision_codes", [])
                    )
                )
                for reason in (
                    "outside_window",
                    "outside_region",
                    "already_seen",
                    "limit_deferred",
                ):
                    metrics[reason] = reasons[reason]
                metrics["prefilter_rejected"] = sum(
                    v
                    for k, v in reasons.items()
                    if k
                    in (
                        "phase_not_allowed",
                        "no_commercial_signal",
                        "strong_exclusion",
                        "publication_unknown",
                        "no_metadata_match",
                        "terminal_phase",
                    )
                )
                metrics["no_alert"] = sum(
                    i["outcome"] == "no_alert" for i in result.get("items", [])
                )
                cycle["processes_seen"] = result["processes_seen"]
                cycle["failures"] = result["failures"]
                cycle["coverage_complete"] = radar_allows_notifications(result)
                cycle["source_summary"].update(
                    query_completed=cycle["coverage_complete"],
                    zero_records_confirmed=cycle["coverage_complete"]
                    and cycle["metrics"]["secop_records_fetched"] == 0,
                )
                for error in result.get("errors", []):
                    cycle["errors"].append(
                        {
                            "code": "radar_global_failure",
                            "stage": error.get("stage", "radar"),
                            "type": error.get("type"),
                        }
                    )
                checkpoint()
                if not cycle["coverage_complete"]:
                    limited = result["status"] == "limited" and not result.get("errors")
                    # 0016 admite completed_with_warnings; radar_status conserva el límite.
                    cycle["status"] = "completed_with_warnings" if limited else "failed"
                    if not limited:
                        cycle["failures"] = max(1, cycle["failures"])
                    cycle["errors"].append(
                        {
                            "code": "radar_limited" if limited else "radar_incomplete",
                            "stage": "radar",
                            "status": result["status"],
                            "severity": "warning" if limited else "error",
                        }
                    )
                    cycle["notification_summary"] = {"skipped": True, "reason": "radar_incomplete"}
                else:
                    verify()
                    cycle["stage"] = "notifications"
                    notify_start = time.monotonic()
                    cycle["events"].append(
                        {"event": "notifications_started", "at": self.clock().isoformat()}
                    )
                    checkpoint()
                    try:
                        summary = self.notify()
                    except Exception as error:
                        summary = {"failed": 1, "error_type": type(error).__name__}
                        cycle["errors"].append(
                            {
                                "code": "notification_dispatch_failed",
                                "stage": "notifications",
                                "type": type(error).__name__,
                            }
                        )
                    cycle["durations_ms"]["notifications"] = (
                        time.monotonic() - notify_start
                    ) * 1000
                    cycle["notification_summary"] = summary
                    cycle["failures"] += summary.get("failed", 0) + summary.get("retryable", 0)
                    cycle["events"].append(
                        {
                            "event": "notifications_result",
                            "at": self.clock().isoformat(),
                            "summary": {
                                key: summary.get(key)
                                for key in (
                                    "disabled",
                                    "prepared",
                                    "sent",
                                    "captured",
                                    "failed",
                                    "retryable",
                                    "recovered",
                                )
                            },
                        }
                    )
                    for target, source in (
                        ("notification_prepared", "prepared"),
                        ("notification_sent", "sent"),
                        ("notification_captured", "captured"),
                        ("notification_failed", "failed"),
                    ):
                        metrics[target] = summary.get(source, 0)
                    warnings = (
                        result["failures"]
                        or summary.get("failed")
                        or summary.get("retryable")
                        or cycle["errors"]
                    )
                    cycle["status"] = "completed_with_warnings" if warnings else "completed"
            except Exception as error:
                cycle["status"] = "failed"
                cycle["failures"] += 1
                cycle["errors"].append(
                    {
                        "code": "cycle_stage_failed",
                        "stage": cycle["stage"],
                        "type": type(error).__name__,
                    }
                )
            finally:
                cycle["finished_at"] = self.clock().isoformat()
                cycle["duration_ms"] = round((time.monotonic() - started) * 1000)
                cycle["events"].append(
                    {
                        "event": "cycle_finished",
                        "at": cycle["finished_at"],
                        "status": cycle["status"],
                        "metrics": dict(cycle["metrics"]),
                        "reasons": dict(cycle["reasons"]),
                        "duration_ms": cycle["duration_ms"],
                        "durations_ms": dict(cycle["durations_ms"]),
                        "errors": list(cycle["errors"]),
                        "notification_state": "disabled"
                        if cycle["notification_summary"].get("disabled")
                        else cycle["notification_summary"].get("reason", "evaluated"),
                    }
                )
                checkpoint()
                if cycle["errors"] and cycle["status"] == "completed":
                    cycle["status"] = "completed_with_warnings"
                    checkpoint()
                try:
                    self.logs.cleanup({c["id"] for c in self.repository.running()})
                except OSError:
                    cycle["errors"].append({"code": "log_retention_failed"})
                    if cycle["status"] == "completed":
                        cycle["status"] = "completed_with_warnings"
                    checkpoint()
        return cycle


def record_startup_failure(settings: Settings, error_type: str, trigger: str) -> None:
    """Best-effort local diagnostic when DB/config preflight prevents creating a DB cycle."""
    now = datetime.now(UTC).isoformat()
    diagnostic = {
        "id": str(uuid.uuid4()),
        "started_at": now,
        "finished_at": now,
        "status": "failed",
        "persisted": False,
        "trigger": trigger,
        "events": [{"event": "preflight_failed", "type": error_type}],
        "errors": [{"code": "preflight_failed", "type": error_type}],
    }
    with suppress(OSError, ValueError):
        CycleLogs(settings.eureka_automation_log_path, settings.eureka_log_retention_days).write(
            diagnostic
        )


def build_cycle_service(sessions: Any, settings: Settings) -> AutomationCycleService:
    def reconcile_radar(cycle: dict[str, Any]) -> None:
        try:
            run = build_radar_queries(sessions).get_run(uuid.UUID(cycle["radar_run_id"]))
        except LookupError:
            return
        cycle["radar_linked"] = True
        cycle["radar_status_at_recovery"] = run["status"]

    def radar(run_id: uuid.UUID, observer: Observer) -> dict[str, Any]:
        service = build_radar_service(sessions, settings, observer=observer)
        today = datetime.now(ZoneInfo(settings.eureka_automation_timezone)).date()
        query = ProcessQuery(
            published_from=settings.eureka_radar_start_date,
            published_before=today + timedelta(days=1),
            departments=tuple(
                r.strip() for r in settings.eureka_radar_regions.split(",") if r.strip()
            ),
            page_size=service.config.page_size,
            max_pages=service.config.max_pages,
        )

        def source() -> Iterator[SecopProcess]:
            remote = iter(fetch_secop_processes(query))
            while True:
                started = time.monotonic()
                try:
                    record = next(remote)
                except StopIteration:
                    return
                finally:
                    observer(
                        "timing", {"name": "ingestion", "ms": (time.monotonic() - started) * 1000}
                    )
                yield record

        return service.run(
            source(),
            start=cast(date, query.published_from),
            before=cast(date, query.published_before),
            regions=query.departments,
            max_processes=settings.eureka_radar_max_processes,
            run_id=run_id,
        )

    def notify() -> dict[str, Any]:
        dispatcher = build_notification_dispatcher(sessions, settings)
        return dispatcher.run(
            [r.strip() for r in settings.eureka_notification_recipients.split(",") if r.strip()],
            retry=True,
            allow_real_send=settings.eureka_automation_allow_real_send,
        )

    return AutomationCycleService(
        CycleRepository(sessions),
        radar,
        notify,
        CycleLogs(settings.eureka_automation_log_path, settings.eureka_log_retention_days),
        settings,
        lambda: preflight(settings, sessions),
        reconcile_radar=reconcile_radar,
    )


class OperationsQueries:
    def __init__(self, sessions: Any, settings: Settings) -> None:
        self.sessions, self.settings = sessions, settings
        self.repository = CycleRepository(sessions)

    def status(self) -> dict[str, Any]:
        today = datetime.now(ZoneInfo(self.settings.eureka_automation_timezone)).date()
        result: dict[str, Any] = {
            "execution_config": {
                "start_date": self.settings.eureka_radar_start_date,
                "before_date": today + timedelta(days=1),
                "before_exclusive": True,
                "timezone": self.settings.eureka_automation_timezone,
                "regions": [
                    r.strip() for r in self.settings.eureka_radar_regions.split(",") if r.strip()
                ],
                "max_processes": self.settings.eureka_radar_max_processes,
            },
            "db_connected": False,
            "schema_ready": False,
            "latest": None,
            "latest_success": None,
            "latest_alert": None,
            "automation_enabled": self.settings.eureka_automation_enabled,
            "notification_mode": self.settings.eureka_notification_mode,
            "notification_enabled": self.settings.eureka_notification_enabled,
            "scheduler": scheduler_status(self.settings.eureka_automation_task_name),
            "next_theoretical": schedule(
                datetime.now(UTC),
                self.settings.eureka_automation_timezone,
                self.settings.eureka_automation_run_times,
                self.settings.eureka_automation_interval_hours,
            ).isoformat(),
        }
        try:
            with self.sessions() as session:
                session.execute(text("SELECT 1"))
            result["db_connected"] = True
            self.repository.ready()
            result["schema_ready"] = True
            result["latest"] = next(iter(self.repository.listing(1)), None)
            result["latest_success"] = self.repository.latest_success()
            result["active_cycle"] = self.repository.active()
            alerts = build_radar_queries(self.sessions).alerts(1, 1)["items"]
            result["latest_alert"] = alerts[0]["created_at"] if alerts else None
        except CycleSchemaPendingError:
            result["diagnostic"] = "migration_0016_pending"
        except Exception:
            result["diagnostic"] = "database_query_failed"
        try:
            result["ocr"] = ocr_runtime_status(self.settings)
        except Exception:
            result["ocr"] = {"available": False, "error_code": "ocr_probe_failed"}
        return result
