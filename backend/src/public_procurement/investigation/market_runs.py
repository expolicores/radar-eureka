"""Date-driven private investigation runs and read-only legacy product receipts."""

import importlib.util
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from .market_benchmark.presentation import present_market_reports
from .market_benchmark.schemas import PublicOffer, PublicProduct
from .run_background import ManualResearchRunner
from .run_contracts import ResearchRun, ResearchRunRequest

MarketRunRequest = ResearchRunRequest
MarketRun = ResearchRun


class ExistingMarketPipeline:
    def __call__(self, product: PublicOffer | PublicProduct, directory: Path) -> dict[str, Any]:
        script = Path(__file__).resolve().parents[3] / "scripts/eureka_market_benchmark.py"
        spec = importlib.util.spec_from_file_location("manual_market_benchmark", script)
        if spec is None or spec.loader is None:
            raise RuntimeError("Market benchmark unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Same auto composition and 3/5 limits as CLI; no sys.argv mutation or shell.
        module.main(
            [
                "--public-product",
                str(directory / "input.json"),
                "--output-directory",
                str(directory),
            ]
        )
        result: dict[str, Any] = json.loads(
            (directory / "market_benchmark.json").read_text(encoding="utf8")
        )
        return result


class ManualMarketRunner(ManualResearchRunner):
    def __init__(self, directory: Path, pipeline: Any = None) -> None:
        from .private_market_pipeline import DateMarketPipeline

        super().__init__(
            directory,
            pipeline if pipeline is not None else DateMarketPipeline(),
            root_name="market-date-runs",
            run_type="state_vs_private_market",
            publish=False,
        )

    def result(self, identifier: UUID) -> dict[str, Any]:
        try:
            report = super().result(identifier)
        except FileNotFoundError:
            # Historical product runs remain accessible only by their exact UUID.
            path = self.directory / "market-runs" / str(UUID(str(identifier))) / "result.json"
            legacy = json.loads(path.read_text(encoding="utf8"))
            return present_market_reports({"reports": [legacy]})
        return present_market_reports({"reports": report.get("market_reports", [])})

    def research_result(self, identifier: UUID) -> dict[str, Any]:
        result = super().result(identifier)
        # Raw provider receipts stay on disk; the separate market endpoint is allowlisted.
        return {k: v for k, v in result.items() if k != "market_reports"}
