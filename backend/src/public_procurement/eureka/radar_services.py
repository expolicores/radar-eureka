"""Corridas de Radar: rescaneo desde inicio, fallos aislados y alertas históricas."""

import hashlib
import json
import time
import uuid
from collections.abc import Callable, Iterable
from contextlib import nullcontext
from dataclasses import asdict
from datetime import UTC, date, datetime
from typing import Any

from public_procurement.ingestion.services import SecopProcess

from .domain.radar import RadarProcess, candidate_decision, evaluate_alert
from .ports import RadarPipeline, RadarRepository
from .radar_config import RadarConfig
from .radar_repositories import COUNTERS


def _stage_callback(
    service: "RadarService", item: dict[str, Any], identity: tuple[str, str], dry_run: bool
) -> Callable[[str], None]:
    def stage(name: str) -> None:
        item["stage"] = name
        if service.observer:
            service.observer("stage", {"name": name, "secop_id": identity[1]})
        if not dry_run:
            service.repository.stage(*identity, name, service.clock())

    return stage


def radar_process(record: SecopProcess) -> RadarProcess:
    return RadarProcess(
        record.dataset_id,
        record.id_del_proceso,
        record.id_del_portafolio,
        record.published_on,
        record.department,
        record.municipality,
        record.entity_name,
        record.title,
        record.description,
        record.phase,
        record.status,
        record.category_code,
        record.base_price_cop,
    )


class RadarService:
    def __init__(
        self,
        repository: RadarRepository,
        pipeline: RadarPipeline,
        config: RadarConfig,
        preferred_budget_max: int,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        observer: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        self.repository, self.pipeline, self.config = repository, pipeline, config
        self.preferred_budget_max, self.clock = preferred_budget_max, clock
        self.observer = observer

    def run(
        self,
        source: Iterable[SecopProcess],
        *,
        start: date,
        before: date,
        regions: tuple[str, ...],
        dry_run: bool = False,
        max_processes: int = 100,
        run_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        if start >= before or not regions or max_processes < 1:
            raise ValueError("Ventana, regiones o límite de procesos inválidos.")
        config_snapshot = {
            **self.config.model_dump(mode="json"),
            "preferred_budget_max": self.preferred_budget_max,
            "regions": list(regions),
            "start_date": start.isoformat(),
            "before_date": before.isoformat(),
            "max_processes": max_processes,
            "strategy": "rescan_from_start",
            "score_gate": False,
        }
        run: dict[str, Any] = {
            "id": run_id or uuid.uuid4(),
            "started_at": self.clock(),
            "finished_at": None,
            "status": "running",
            "start_date": start,
            "before_date": before,
            "regions": list(regions),
            "rule_version": self.config.version,
            "config_hash": hashlib.sha256(
                json.dumps(config_snapshot, sort_keys=True).encode()
            ).hexdigest(),
            "errors": [],
            **dict.fromkeys(COUNTERS, 0),
            "items": [],
            "dry_run": dry_run,
        }
        with nullcontext() if dry_run else self.repository.lock():
            if not dry_run:
                self.repository.start(run, config_snapshot)
                if self.observer:
                    self.observer("radar_started", {"id": str(run["id"])})
            processed: set[tuple[str, str]] = set()
            handled = 0
            try:
                for record in source:
                    if self.observer:
                        self.observer("secop_received", {})
                    identity = record.identity
                    if identity in processed:
                        continue
                    processed.add(identity)
                    process = radar_process(record)
                    prefilter_started = time.monotonic()
                    run["processes_seen"] += 1
                    state = self.repository.state(*identity)
                    item: dict[str, Any] = {
                        "dataset_id": process.dataset_id,
                        "secop_id": process.secop_id,
                        "department": process.department,
                        "published_on": process.published_on.isoformat()
                        if process.published_on
                        else None,
                        "title": process.title,
                        "stage": "metadata",
                        "outcome": "skipped",
                    }
                    claimed = False
                    candidate = candidate_decision(process, start, before, regions, self.config)
                    if self.observer:
                        self.observer(
                            "timing",
                            {
                                "name": "prefilter",
                                "ms": (time.monotonic() - prefilter_started) * 1000,
                            },
                        )
                    if candidate.code in (
                        "outside_window",
                        "outside_region",
                        "publication_unknown",
                    ):
                        item["reason"] = candidate.code
                        run["skipped"] += 1
                    elif state and state["status"] == "completed":
                        item["reason"] = "already_seen"
                        run["skipped"] += 1
                    elif state and state["attempts"] >= self.config.max_attempts:
                        item["reason"] = "attempts_exhausted"
                        run["skipped"] += 1
                    else:
                        if handled >= max_processes:
                            run["status"] = "limited"
                            item["reason"] = "limit_deferred"
                            run["skipped"] += 1
                            run["items"].append(item)
                            if not dry_run:
                                self.repository.outcome(run["id"], item, self.clock(), False)
                            break
                        handled += 1
                        item["candidate_matches"] = candidate.matches
                        item["review_notes"] = candidate.review_notes
                        claimed = True
                        if state is None and claimed:
                            run["new_processes"] += 1
                        if claimed and not dry_run:
                            self.repository.claim(run["id"], *identity, self.clock())
                        if not candidate.accepted:
                            item["reason"] = candidate.code
                            run["skipped"] += 1
                        else:
                            run["candidates"] += 1
                            if self.observer:
                                self.observer("candidate", {})

                            stage = _stage_callback(self, item, identity, dry_run)

                            try:
                                stage("preview" if dry_run else "pipeline")
                                details = (
                                    self.pipeline.preview(process.secop_id)
                                    if dry_run
                                    else self.pipeline.enrich(record, stage)
                                )
                                if details is None or details.enrichment_status not in (
                                    "consolidated",
                                    "conflict",
                                ):
                                    item["outcome"], item["reason"] = (
                                        "pending_enrichment",
                                        "pipeline_required",
                                    )
                                    if not dry_run:
                                        raise ValueError(
                                            "No hay consolidación documental disponible."
                                        )
                                else:
                                    item["process_id"] = str(details.process_id)
                                    run["enriched"] += 1
                                    if self.observer:
                                        self.observer("enriched", {})
                                    stage("alert_evaluation")
                                    decision = evaluate_alert(
                                        process,
                                        candidate,
                                        details,
                                        self.config,
                                        self.preferred_budget_max,
                                    )
                                    coverage = details.quality.get("extraction_coverage", {})
                                    if coverage:
                                        item["extraction_coverage"] = coverage
                                        decision.snapshot["extraction_coverage"] = coverage
                                    if coverage.get("coverage_complete") is False:
                                        item["coverage_incomplete"] = True
                                        item["coverage_warning"] = "document_coverage_incomplete"
                                        run["failures"] += 1
                                    # Preserve document provenance in the historical snapshot.
                                    canonical_ids = {
                                        reason["canonical_fact_id"]
                                        for reason in decision.reasons
                                        if reason.get("code") == "confirmed_commercial_match"
                                    }
                                    for canonical_id in sorted(canonical_ids):
                                        decision.reasons.append(
                                            {
                                                "code": "document_evidence",
                                                "origin": "document",
                                                "canonical_fact_id": canonical_id,
                                                "references": self.pipeline.evidence(
                                                    process.secop_id, uuid.UUID(canonical_id)
                                                ),
                                            }
                                        )
                                    item["decision"] = asdict(decision)
                                    item["decision_codes"] = sorted(
                                        {r["code"] for r in decision.reasons if r.get("code")}
                                    )
                                    if not decision.confirmed:
                                        item["decision_codes"].append("no_confirmed_affinity")
                                    item["outcome"] = "alert" if decision.create else "no_alert"
                                    if decision.create:
                                        if dry_run:
                                            item["would_create_alert"] = True
                                        else:
                                            if details.opportunity_id is None:
                                                raise ValueError("Oportunidad no persistida.")
                                            created = self.repository.alert(
                                                run["id"],
                                                details.opportunity_id,
                                                self.config.version,
                                                decision,
                                                self.clock(),
                                            )
                                            run["alerts_created"] += int(created)
                                            if self.observer:
                                                self.observer("alert_created", {"created": created})
                                            item["alert_created"] = created
                                    item["stage"] = "completed"
                            except Exception as error:
                                item["outcome"] = "failed"
                                item["error"] = {
                                    "stage": item["stage"],
                                    "type": type(error).__name__,
                                    "message": str(error)[:500]
                                    if isinstance(error, (ValueError, RuntimeError))
                                    else "Fallo controlado del pipeline; revisar logs de la etapa.",
                                }
                                run["failures"] += 1
                    run["items"].append(item)
                    if self.observer:
                        self.observer(
                            "process_result",
                            {
                                "reason": item.get("reason"),
                                "outcome": item["outcome"],
                                "stage": item["stage"],
                                "secop_id": process.secop_id,
                                "coverage_incomplete": item.get("coverage_incomplete", False),
                                "error_type": item.get("error", {}).get("type"),
                            },
                        )
                    if not dry_run:
                        self.repository.outcome(run["id"], item, self.clock(), claimed)
                        self.repository.finish(run)
            except Exception as error:
                run["status"] = "failed"
                run["errors"].append(
                    {
                        "stage": "source_or_persistence",
                        "type": type(error).__name__,
                        "message": str(error)[:500]
                        if isinstance(error, (ValueError, RuntimeError))
                        else "Corrida incompleta; revisar proveedor o persistencia.",
                    }
                )
                run["failures"] += 1
            finally:
                if run["status"] == "running":
                    run["status"] = "partial" if run["failures"] else "completed"
                run["finished_at"] = self.clock()
                if not dry_run:
                    self.repository.finish(run)
        return run
