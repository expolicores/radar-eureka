"""Invoke existing research steps with fixed server-owned argv, without shell execution."""

import importlib.util
import json
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

from .run_contracts import ResearchRunRequest


class ExistingResearchPipeline:
    def __init__(self, scripts: Path | None = None, *, public_evidence_only: bool = False) -> None:
        self.scripts = scripts or Path(__file__).resolve().parents[3] / "scripts"
        self.public_evidence_only = public_evidence_only

    def __call__(
        self, window: ResearchRunRequest, directory: Path, stage: Callable[[str], None]
    ) -> dict[str, Any]:
        before = window.end_date + timedelta(days=1)
        days = (before - window.start_date).days
        steps: tuple[tuple[str, str, list[str]], ...] = (
            ("discovery", "discover", ["--before", str(before), "--days", str(days), "--prepare"]),
            ("documents_extraction", "sample", ["--execute"]),
            ("research_report", "report", []),
            (
                "economic_cycle",
                "cycle",
                ["--public-evidence-only"] if self.public_evidence_only else [],
            ),
        )
        for name, script, arguments in steps:
            stage(name)
            path = self.scripts / f"eureka_investigation_{script}.py"
            spec = importlib.util.spec_from_file_location(f"research_step_{script}", path)
            if spec is None or spec.loader is None:
                raise RuntimeError("Research step unavailable")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # No global sys.argv mutation, no caller-selected scripts/paths, no --publish.
            module.main(["--sample-directory", str(directory), *arguments])
        result: dict[str, Any] = json.loads(
            (directory / "research-cycle-report.json").read_text(encoding="utf8")
        )
        return result
