"""Single local research worker with JSON receipts and OS-held exclusion/restart recovery."""

import json
import logging
import os
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO
from uuid import UUID, uuid4

from public_procurement.shared.logging import log_event

from .research import ResearchReportStore
from .run_contracts import TERMINAL, ResearchRun, ResearchRunRequest
from .run_pipeline import ExistingResearchPipeline

logger = logging.getLogger(__name__)


class ResearchBusyError(RuntimeError):
    pass


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4()}.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf8")
    temporary.replace(path)


def _lease(path: Path) -> BinaryIO:
    file = path.open("a+b")
    try:
        if file.seek(0, 2) == 0:
            file.write(b"0")
            file.flush()
        file.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            # Unix-only attributes are absent from Windows type stubs.
            unix_lock: Any = fcntl
            unix_lock.flock(file, unix_lock.LOCK_EX | unix_lock.LOCK_NB)
    except OSError:
        file.close()
        raise ResearchBusyError("Ya existe una corrida investigativa activa.") from None
    return file


class ManualResearchRunner:
    def __init__(
        self,
        directory: Path,
        pipeline: Any = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        *,
        root_name: str = "runs",
        run_type: Any = "state_vs_state",
        publish: bool = True,
    ) -> None:
        self.directory = directory
        self.root = directory / root_name
        self.run_type = run_type
        self.publish = publish
        self.root.mkdir(parents=True, exist_ok=True)
        self.pipeline = pipeline if pipeline is not None else ExistingResearchPipeline()
        self.clock = clock
        self.guard = threading.RLock()
        self.closing = False
        self.owned: UUID | None = None
        try:
            with _lease(self.root / "worker.lock"):
                self._recover()
        except ResearchBusyError:
            pass  # Another live backend owns the shared directory; never interrupt its run.

    def _path(self, run_id: UUID) -> Path:
        return self.root / str(UUID(str(run_id)))

    def get(self, run_id: UUID) -> ResearchRun:
        with self.guard:
            path = self._path(run_id) / "run.json"
            if not path.exists():
                raise FileNotFoundError("Corrida no encontrada.")
            return ResearchRun.model_validate_json(path.read_text(encoding="utf8"))

    def _save(self, run: ResearchRun) -> None:
        _write(self._path(run.run_id) / "run.json", run.model_dump(mode="json"))
        log_event(
            logger,
            "investigation_run",
            run_id=str(run.run_id),
            status=run.status,
            stage=run.stage,
            warnings_count=len(run.warnings),
            errors_count=len(run.errors),
        )

    def active(self) -> ResearchRun | None:
        path = self.root / "active.json"
        if not path.exists():
            return None
        run = self.get(UUID(json.loads(path.read_text(encoding="utf8"))["run_id"]))
        return run if run.status not in TERMINAL else None

    def _recover(self) -> None:
        for path in self.root.glob("*/run.json"):
            run = ResearchRun.model_validate_json(path.read_text(encoding="utf8"))
            if run.status not in TERMINAL:
                run.status, run.stage = "failed", "interrupted"
                run.finished_at = self.clock()
                run.errors.append("backend_restarted")
                self._save(run)

    def start(self, window: ResearchRunRequest) -> ResearchRun:
        with self.guard:
            if self.closing:
                raise ResearchBusyError("El backend se está reiniciando.")
            try:
                lease = _lease(self.root / "worker.lock")
            except ResearchBusyError:
                active = self.active()
                if active and (active.start_date, active.end_date) == (
                    window.start_date,
                    window.end_date,
                ):
                    return active  # A repeated POST does not create a second active run.
                raise
            try:
                self._recover()
                start, before = window.utc_bounds()
                run = ResearchRun(
                    run_id=uuid4(),
                    run_type=self.run_type,
                    status="queued",
                    start_date=window.start_date,
                    end_date=window.end_date,
                    window_start_at=start,
                    window_before_at=before,
                    created_at=self.clock(),
                )
                self._save(run)
                _write(self.root / "active.json", {"run_id": str(run.run_id)})
                self.owned = run.run_id
                thread = threading.Thread(
                    target=self._execute,
                    args=(run.run_id, window, lease),
                    daemon=True,
                    name=f"research-{run.run_id}",
                )
                try:
                    thread.start()
                except Exception:
                    run.status, run.finished_at = "failed", self.clock()
                    run.errors.append("worker_start_failed")
                    self._save(run)
                    self.owned = None
                    raise RuntimeError("Research worker unavailable") from None
                return run
            except BaseException:
                lease.close()
                raise

    def _execute(self, identifier: UUID, window: ResearchRunRequest, lease: BinaryIO) -> None:
        try:
            with self.guard:
                run = self.get(identifier)
                run.status, run.started_at = "running", self.clock()
                self._save(run)

            def stage(name: str) -> None:
                with self.guard:
                    if self.closing:
                        raise RuntimeError("Backend shutting down")
                    run = self.get(identifier)
                    run.stage = name
                    self._save(run)

            report = self.pipeline(window, self._path(identifier), stage)
            with self.guard:
                if self.closing:
                    return
                counts = {k: v for k, v in report.get("summary", {}).items() if type(v) is int}
                counts.setdefault("processes_found", len(report.get("processes", [])))
                counts.setdefault("signals_generated", len(report.get("signals", [])))
                warnings = [
                    key
                    for key in (
                        "documents_failed",
                        "extraction_failed",
                        "partial_coverage_documents",
                    )
                    if counts.get(key, 0) > 0
                ]
                if any(p.get("warnings") or p.get("errors") for p in report.get("processes", [])):
                    warnings.append("process_warnings_or_errors")
                inventory_errors = self._path(identifier) / "inventory-errors.json"
                if inventory_errors.exists() and json.loads(
                    inventory_errors.read_text(encoding="utf8")
                ):
                    warnings.append("inventory_errors")
                report = {
                    **report,
                    "investigation_run_id": str(identifier),
                    "run_type": self.run_type,
                }
                _write(self._path(identifier) / "result.json", report)
                if self.publish:
                    ResearchReportStore(self.directory).write(report)
                run = self.get(identifier)
                run.status = "completed_with_warnings" if warnings else "completed"
                run.stage, run.finished_at = "finished", self.clock()
                run.warnings = list(dict.fromkeys([*warnings, *report.get("run_warnings", [])]))
                run.status = "completed_with_warnings" if run.warnings else "completed"
                run.counts = counts
                run.result_url = (
                    f"/explorar?private_run={identifier}&market_run={identifier}"
                    if self.run_type == "state_vs_private_market"
                    else f"/explorar?run={identifier}"
                )
                self._save(run)
        except Exception:
            # No provider exception body, API key, headers, or filesystem paths in run responses.
            with self.guard:
                run = self.get(identifier)
                if run.status not in TERMINAL:
                    run.status, run.finished_at = "failed", self.clock()
                    run.errors.append("pipeline_failed")
                    self._save(run)
        finally:
            with self.guard:
                self.owned = None
            lease.close()

    def result(self, identifier: UUID) -> dict[str, Any]:
        self.get(identifier)
        path = self._path(identifier) / "result.json"
        if not path.exists():
            raise FileNotFoundError("El resultado aún no está disponible.")
        result: dict[str, Any] = json.loads(path.read_text(encoding="utf8"))
        return result

    def close(self) -> None:
        with self.guard:
            self.closing = True
            run = self.get(self.owned) if self.owned else None
            if run is not None and run.status not in TERMINAL:
                run.status, run.finished_at = "failed", self.clock()
                run.errors.append("backend_restarted")
                self._save(run)
