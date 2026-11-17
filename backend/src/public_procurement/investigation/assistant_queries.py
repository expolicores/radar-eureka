"""Read-only projections of persisted date runs. No worker, SQL, provider or acquisition."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from .market_benchmark.presentation import present_market_reports
from .run_contracts import TERMINAL, ResearchRun

BOGOTA = ZoneInfo("America/Bogota")


def safe(value: Any) -> Any:
    """Bounded scalar projections; untrusted text never becomes an instruction."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        value = re.sub(
            r"(?i)(?:api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+",
            "[redacted]",
            value,
        )
        value = re.sub(r"(?:[A-Za-z]:[\\/]|/home/|/Users/|/tmp/)[^\s]+", "[internal_path]", value)
        return value[:600]
    if isinstance(value, list):
        return [safe(v) for v in value[:12]]
    return None  # Never forward arbitrary nested/provider objects.


def pick(data: dict[str, Any], keys: str) -> dict[str, Any]:
    return {key: safe(data[key]) for key in keys.split() if key in data}


def notices(values: list[Any]) -> list[str]:
    return list(
        dict.fromkeys(
            v
            if isinstance(v, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,100}", v)
            else "unclassified_notice"
            for v in values
        )
    )[:30]


class InvestigationRunRepository:
    """Use the existing DTO/receipt format without constructing writing/recovery workers."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def get(self, run_id: str) -> tuple[ResearchRun, Path]:
        identifier = str(UUID(run_id))
        for root, kind in (
            ("runs", "state_vs_state"),
            ("market-date-runs", "state_vs_private_market"),
        ):
            folder = self.directory / root / identifier
            path = folder / "run.json"
            if not path.exists():
                continue
            run = ResearchRun.model_validate_json(path.read_text(encoding="utf8"))
            if (
                str(run.run_id) != identifier
                or run.run_type != kind
                or run.created_at.tzinfo is None
            ):
                raise ValueError("Invalid run metadata")
            return run, folder
        raise FileNotFoundError("Run not found")

    def latest(
        self, run_type: str | None, today: bool, now: datetime
    ) -> tuple[ResearchRun, Path] | None:
        runs = []
        for root in ("runs", "market-date-runs"):
            for path in (self.directory / root).glob("*/run.json"):
                try:
                    run, directory = self.get(path.parent.name)
                except (ValueError, OSError):
                    # A skipped unreadable newest run could falsely select an older result.
                    raise ValueError(
                        "Cannot establish latest run from unreadable metadata"
                    ) from None
                if run_type and run.run_type != run_type:
                    continue
                if (
                    today
                    and run.created_at.astimezone(BOGOTA).date() != now.astimezone(BOGOTA).date()
                ):
                    continue
                runs.append((run, directory))
        return max(runs, key=lambda row: (row[0].created_at, str(row[0].run_id))) if runs else None

    def result(self, folder: Path, identifier: str) -> dict[str, Any] | None:
        path = folder / "result.json"
        if not path.exists():
            return None
        report: dict[str, Any] = json.loads(path.read_text(encoding="utf8"))
        if str(report.get("investigation_run_id")) != identifier:
            raise ValueError("Result belongs to another run")
        return report


class InvestigationAssistantQueries:
    """One request-scoped run snapshot; no silent fallback to published/latest reports."""

    def __init__(self, repository: InvestigationRunRepository) -> None:
        self.repository = repository
        self.run: ResearchRun | None = None
        self.report: dict[str, Any] | None = None
        self.result_available = False

    def select(
        self, run_id: str | None, run_type: str | None, today: bool, now: datetime
    ) -> dict[str, Any]:
        selected = (
            self.repository.get(run_id) if run_id else self.repository.latest(run_type, today, now)
        )
        if selected is None:
            return {"found": False, "run_type_filter": run_type, "today_bogota": today}
        self.run, folder = selected
        # No finalized report is expected during discovery/extraction. Do not borrow an old one.
        self.report = self.repository.result(folder, str(self.run.run_id))
        self.result_available = self.report is not None
        return self.metadata()

    def metadata(self) -> dict[str, Any]:
        if self.run is None:
            return {"found": False}
        data = self.run.model_dump(mode="json", exclude={"result_url"})
        data["warnings"], data["errors"] = notices(self.run.warnings), notices(self.run.errors)
        return {
            **data,
            "found": True,
            "provisional": self.run.status not in TERMINAL,
            "result_available": self.result_available,
        }

    def _envelope(self, items: list[dict[str, Any]], limit: int = 30) -> dict[str, Any]:
        return {
            "run_id": str(self.run.run_id) if self.run else None,
            "result_available": self.result_available,
            "provisional": bool(self.run and self.run.status not in TERMINAL),
            "total": len(items),
            "truncated": len(items) > limit,
            "items": items[:limit],
        }

    def _markets(self) -> list[dict[str, Any]]:
        reports: list[dict[str, Any]] = present_market_reports(
            {"reports": (self.report or {}).get("market_reports", [])}
        )["reports"]
        return reports

    def products(self) -> dict[str, Any]:
        rows = []
        report = self.report or {}
        candidates = {
            (c["process_identity"], c["product_id"]): c
            for c in report.get("private_market_candidates", [])
        }
        for p in report.get("processes", []):
            products = (p.get("economic_cycle") or {}).get("products", []) or p.get("products", [])
            for item in products:
                candidate = candidates.get((p["id"], str(item.get("id") or "")), {})
                # Private runs define identified products via their persisted candidates.
                # Older extraction observations are context, not additional reconstructed items.
                if self.run and self.run.run_type == "state_vs_private_market" and not candidate:
                    continue
                price = item.get("purchase_price") or {}
                stage = {
                    "contract_unit_price": "contract_confirmed",
                    "awarded_unit_price": "awarded_confirmed",
                    "accepted_offer_unit_price": "accepted_offer_confirmed",
                }.get(str(price.get("column") or ""), "unresolved")
                provenance = candidate.get("evidence", []) or [
                    e for o in item.get("observations", []) for e in o.get("evidence", [])
                ]
                rows.append(
                    {
                        "process_identity": safe(p.get("id")),
                        "process_code": safe(p.get("reference")),
                        "entity": safe(p.get("entity")),
                        "product_id": safe(item.get("id") or item.get("observation_id")),
                        "description": safe(
                            item.get("item_description") or item.get("description")
                        ),
                        **pick(item, "brand model quantity unit"),
                        "public_evidence_status": candidate.get("public_evidence_status", stage),
                        "verified_public_unit_price": safe(price.get("value")),
                        "documented_public_unit_price": safe(
                            (candidate.get("public_product") or {}).get("public_unit_price")
                            or item.get("unit_price_cop")
                            or item.get("offer_unit_price")
                        ),
                        "provenance": [
                            pick(
                                e,
                                "source_document source_page input_sha256 document_version_id "
                                "extraction_method",
                            )
                            for e in provenance[:8]
                        ],
                        "provenance_total": len(provenance),
                        "provenance_truncated": len(provenance) > 8,
                        "private_market_eligibility": candidate.get("status", "not_evaluated"),
                        "eligibility_reasons": notices(candidate.get("reasons", [])),
                        "conflicts": notices(item.get("conflicts", [])),
                        "human_review_recommended": bool(
                            item.get("requires_manual_review")
                            or candidate.get("status") == "pending_review"
                        ),
                    }
                )
        return self._envelope(rows)

    def benchmarks(self, *, unbounded: bool = False) -> dict[str, Any]:
        rows = []
        for r in self._markets():
            public = r.get("public_product") or {}
            b = r["benchmark"]
            rows.append(
                {
                    "process_identity": safe(public.get("public_process_identity")),
                    "process_code": safe(public.get("public_process_code")),
                    "product": pick(r["product"], "brand model canonical_model size product_type"),
                    "public_evidence_status": safe(r.get("public_evidence_status")),
                    **pick(
                        b,
                        "benchmark_status valid_observations_count retailers_count "
                        "min_price median_price max_price evidence_sufficiency captured_at",
                    ),
                    "limitations": notices(b.get("limitations", [])),
                    "observations": [
                        pick(
                            o,
                            "retailer market_product_title model price currency match_level "
                            "price_evidence_level verification_status captured_at",
                        )
                        for o in b.get("observations", [])[:8]
                    ],
                }
            )
        return self._envelope(rows, len(rows) if unbounded else 20)

    def comparisons(self) -> dict[str, Any]:
        rows = []
        for c in (self.report or {}).get("comparisons", []):
            if not c.get("comparison_eligible"):
                continue
            rows.append(
                {
                    "kind": "state_vs_state",
                    **pick(
                        c,
                        "id processes entities comparability unit_price_a_cop "
                        "unit_price_b_cop absolute_difference_cop difference_pct "
                        "percentage_reference days_between limitations",
                    ),
                    "evidence": [
                        pick(
                            s,
                            "process_identity entity description unit_price price_stage "
                            "purchased_at",
                        )
                        for s in c.get("sides", [])
                    ],
                }
            )
        for r in self._markets():
            if r.get("comparison"):
                rows.append(
                    {
                        "kind": "state_vs_private_market",
                        "process_identity": safe(
                            (r.get("public_product") or {}).get("public_process_identity")
                        ),
                        "product": pick(r["product"], "brand model"),
                        **pick(
                            r["comparison"],
                            "public_unit_price private_median_price absolute_difference "
                            "percentage_difference public_price_date market_captured_at "
                            "confidence limitations",
                        ),
                    }
                )
        return self._envelope(rows, 20)

    def signals(self, *, unbounded: bool = False) -> dict[str, Any]:
        rows = [
            pick(
                s,
                "id type title processes entities difference_pct "
                "absolute_difference_cop comparability requires_human_review "
                "limitations",
            )
            for s in (self.report or {}).get("signals", [])
        ]
        for r in self._markets():
            if r.get("signal"):
                rows.append(
                    {
                        **pick(r["signal"], "type meaning"),
                        "process_identity": safe(
                            (r.get("public_product") or {}).get("public_process_identity")
                        ),
                        "product": pick(r["product"], "brand model"),
                        "limitations": notices(r["benchmark"].get("limitations", [])),
                        "human_review_recommended": True,
                    }
                )
        return self._envelope(rows, len(rows) if unbounded else 20)

    def reviews(self) -> dict[str, Any]:
        rows: dict[str, dict[str, Any]] = {}

        def add(identity: Any, code: Any, reason: str) -> None:
            if not isinstance(identity, str):
                return
            row = rows.setdefault(
                identity,
                {
                    "process_identity": safe(identity),
                    "process_code": safe(code),
                    "reasons": [],
                    "human_review_recommended": True,
                },
            )
            if reason not in row["reasons"]:
                row["reasons"].append(reason)

        for p in (self.report or {}).get("processes", []):
            for item in (p.get("economic_cycle") or {}).get("products", []):
                if item.get("conflicts"):
                    add(p["id"], p.get("reference"), "documentary_conflict")
                if item.get("requires_manual_review"):
                    add(p["id"], p.get("reference"), "unresolved_public_evidence")
            for d in p.get("documents", []):
                if d.get("selected") and not d.get("downloaded"):
                    add(p["id"], p.get("reference"), "document_download_failed")
                if d.get("downloaded") and d.get("extraction_status") in {
                    "failed",
                    "extraction_failed",
                    "unsupported_format",
                }:
                    add(p["id"], p.get("reference"), "extraction_failed")
                if d.get("coverage_complete") is False:
                    add(p["id"], p.get("reference"), "partial_document_coverage")
        for c in (self.report or {}).get("private_market_candidates", []):
            if c.get("status") == "pending_review":
                for reason in notices(c.get("reasons", [])):
                    add(c.get("process_identity"), c.get("process_code"), reason)
            if c.get("market_status") == "failed":
                add(
                    c.get("process_identity"),
                    c.get("process_code"),
                    "private_market_product_failed",
                )
        for b in self.benchmarks(unbounded=True)["items"]:
            if b.get("benchmark_status") != "ready":
                add(
                    b.get("process_identity"), b.get("process_code"), "insufficient_market_evidence"
                )
        for s in self.signals(unbounded=True)["items"]:
            identities = s.get("processes", []) or [s.get("process_identity")]
            for identity in identities:
                add(identity, None, "existing_investigative_signal")
        return self._envelope(list(rows.values()))

    def dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name != "get_latest_investigation_run" and (
            self.run is None or arguments.get("run_id") != str(self.run.run_id)
        ):
            raise ValueError("Tool outside selected run")
        if name in {"get_latest_investigation_run", "get_investigation_run"}:
            return self.metadata()
        if self.run is None or arguments.get("run_id") != str(self.run.run_id):
            raise ValueError("Tool outside selected run")
        readers = {
            "get_run_products": self.products,
            "get_run_benchmarks": self.benchmarks,
            "get_run_comparisons": self.comparisons,
            "get_run_signals": self.signals,
            "get_run_review_candidates": self.reviews,
        }
        if name not in readers:
            raise ValueError("Unknown read tool")
        return readers[name]()


def build_assistant_queries(directory: Path) -> InvestigationAssistantQueries:
    return InvestigationAssistantQueries(InvestigationRunRepository(directory))
