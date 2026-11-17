"""Public evidence from THIS date run -> explicit candidates -> existing private pipeline.

No reads of published reports, no re-extraction, no changes to market matching/signals.
"""

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ValidationError

from .market_benchmark.presentation import present_market_reports
from .market_benchmark.schemas import MarketObservation, ProductIdentity, PublicOffer, PublicProduct
from .market_benchmark.service import build_report
from .run_background import _write
from .run_contracts import ResearchRunRequest
from .run_pipeline import ExistingResearchPipeline


class PrivateMarketCandidate(BaseModel):
    candidate_id: str
    process_identity: str
    process_code: str
    product_id: str
    description: str
    brand: str | None = None
    model: str | None = None
    status: Literal["eligible", "ineligible", "pending_review"]
    reasons: list[str] = Field(default_factory=list)
    public_evidence_status: str = "unresolved"
    public_product: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    market_status: str = "not_attempted"
    market_report_id: str | None = None
    reused_market_from: str | None = None


def _id(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:32]


def _date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        date = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return date if date.tzinfo else date.replace(tzinfo=ZoneInfo("America/Bogota"))
    except ValueError:
        return None


def private_market_candidates(report: dict[str, Any]) -> list[PrivateMarketCandidate]:
    candidates: dict[str, PrivateMarketCandidate] = {}
    for process in report.get("processes", []):
        for item in (process.get("economic_cycle") or {}).get("products", []):
            key = _id([process["id"], item["id"]])
            if key in candidates:
                continue
            c = PrivateMarketCandidate(
                candidate_id=key,
                process_identity=process["id"],
                process_code=process.get("reference") or process["id"],
                product_id=item["id"],
                description=item["item_description"],
                brand=item.get("brand"),
                model=item.get("model"),
                status="pending_review",
                warnings=list(dict.fromkeys([*item.get("notes", []), *item.get("conflicts", [])])),
            )
            candidates[key] = c
            fields = item.get("fields", {})
            if not c.brand or not c.model:
                c.status, c.reasons = "ineligible", ["unresolved_product_identity"]
                continue
            if any(fields.get(k, {}).get("status") != "confirmed" for k in ("brand", "model")):
                c.reasons = ["conflicting_or_uncertain_product_identity"]
                continue
            # The cycle has already verified contract/award/accepted-offer linkage.
            price = item.get("purchase_price")
            if price:
                column = price["column"]
                stage = {
                    "contract_unit_price": "contract",
                    "awarded_unit_price": "awarded",
                    "accepted_offer_unit_price": "accepted_offer",
                }.get(column)
            else:
                # Unconfirmed offers are usable ONLY for preliminary market research.
                column, stage = "offer_unit_price", "offer"
                field = fields.get(column, {})
                if field.get("status") != "confirmed" or not field.get("value"):
                    c.reasons = ["no_documented_public_unit_price"]
                    continue
                price = {"value": field["value"], "evidence": field.get("alternatives", [])}
            alternatives = price.get("evidence", [])
            evidence = [ev for a in alternatives for ev in a.get("evidence", [])]
            c.evidence = evidence
            if not stage:
                c.reasons = ["unresolved_public_price_stage"]
                continue
            c.public_evidence_status = {
                "contract": "contract_confirmed",
                "awarded": "awarded_confirmed",
                "accepted_offer": "accepted_offer_confirmed",
                "offer": "documented_unconfirmed_offer",
            }[stage]
            source = next(
                (
                    e
                    for e in evidence
                    if e.get("source_document")
                    and e.get("source_page") is not None
                    and (e.get("input_sha256") or e.get("document_version_id"))
                ),
                None,
            )
            if not source:
                c.reasons = ["missing_document_page_provenance"]
                continue
            date = _date(item.get("purchase_date")) if stage != "offer" else None
            if stage != "offer" and date is None:
                c.reasons = ["missing_verified_purchase_date"]
                continue
            observation_ids = {a.get("observation_id") for a in alternatives}
            observations = [
                o for o in item.get("observations", []) if o.get("id") in observation_ids
            ]
            tax_bases = {o.get("vat_basis", "undetermined") for o in observations}
            tax = next(iter(tax_bases)) if len(tax_bases) == 1 else "undetermined"
            document: dict[str, Any] = next(
                (
                    d
                    for d in process.get("documents", [])
                    if d.get("name") == source["source_document"]
                ),
                {},
            )
            data = dict(
                brand=c.brand,
                model=c.model,
                product_type=item.get("normalized_product"),
                size=str((item.get("specifications") or {}).get("screen_size_inches") or "")
                or None,
                public_process_identity=c.process_identity,
                public_process_code=c.process_code,
                public_entity=process.get("entity") or "",
                public_product_description=c.description,
                public_unit_price=price["value"],
                public_price_stage=stage,
                public_price_date=date,
                public_evidence_ref="cycle:"
                + key
                + ":"
                + str(source.get("input_sha256") or source.get("document_version_id")),
                public_document=source["source_document"],
                public_page_reference=str(source["source_page"]),
                public_document_url=document.get("source_url"),
                quantity=item.get("quantity"),
                price_origin=price.get("origin") or alternatives[0].get("value_origin", "explicit"),
                price_tax_basis={"included": "includes_vat", "excluded": "excludes_vat"}.get(
                    tax, "unknown"
                ),
                evidence_warnings=c.warnings,
                evidence_text=source.get("evidence_text"),
            )
            try:
                product = (PublicOffer if stage == "offer" else PublicProduct).model_validate(data)
            except (ValidationError, IndexError):
                c.reasons = ["incomplete_structured_public_evidence"]
                continue
            c.status, c.reasons = "eligible", ["structured_documented_public_product"]
            c.public_product = product.model_dump(mode="json")
    return list(candidates.values())


class DateMarketPipeline:
    def __init__(self, public_pipeline: Any = None, market_pipeline: Any = None) -> None:
        from .market_runs import ExistingMarketPipeline

        self.public = (
            public_pipeline
            if public_pipeline is not None
            else ExistingResearchPipeline(public_evidence_only=True)
        )
        self.market = market_pipeline if market_pipeline is not None else ExistingMarketPipeline()

    def __call__(
        self, window: ResearchRunRequest, directory: Path, stage: Callable[[str], None]
    ) -> dict[str, Any]:
        report = self.public(window, directory, stage)
        stage("product_identification")
        candidates = private_market_candidates(report)
        reports = []
        warnings = []
        market_cache: dict[str, tuple[str, dict[str, Any]]] = {}

        # Candidate snapshot survives partial failures; only run-owned inputs are consumed.
        def snapshot() -> None:
            _write(
                directory / "private-market-candidates.json",
                {"candidates": [c.model_dump(mode="json") for c in candidates]},
            )

        snapshot()
        for c in candidates:
            if c.status != "eligible" or c.public_product is None:
                continue
            stage("private_market_discovery")
            target = directory / "products" / c.candidate_id
            _write(target / "input.json", c.public_product)
            product = (
                PublicOffer if c.public_product["public_price_stage"] == "offer" else PublicProduct
            ).model_validate(c.public_product)
            try:
                identity = _id(
                    product.model_dump(mode="json", include=set(ProductIdentity.model_fields))
                )
                if identity in market_cache:
                    previous_id, previous = market_cache[identity]
                    # Same exact identity/attributes in this run: reuse captured observations,
                    # but apply the existing comparison rules to THIS public evidence.
                    receipt = build_report(
                        product,
                        [
                            MarketObservation.model_validate(o)
                            for o in previous["benchmark"]["observations"]
                        ],
                        datetime.fromisoformat(
                            previous["benchmark"]["captured_at"].replace("Z", "+00:00")
                        ),
                        previous.get("query", ""),
                        [],
                        previous.get("errors", []),
                    )
                    c.reused_market_from = previous_id
                else:
                    receipt = self.market(product, target)
                    market_cache[identity] = (c.candidate_id, receipt)
                _write(target / "market_benchmark.json", receipt)
                stage("benchmark")
                view = present_market_reports({"reports": [receipt]})["reports"][0]
                reports.append(receipt)
                c.market_status, c.market_report_id = "processed", view["report_id"]
                if receipt.get("errors") or receipt.get("status") == "completed_with_warnings":
                    warnings.append("private_provider_limitations")
                if receipt["benchmark"]["benchmark_status"] != "ready":
                    warnings.append("insufficient_market_evidence")
            except Exception:
                # Isolated provider failures cannot discard the public evidence or other products.
                c.market_status = "failed"
                c.warnings.append("private_market_product_failed")
                warnings.append("private_market_product_failed")
            snapshot()
        stage("comparison")
        discovery_path = directory / "selection.json"
        discovery = (
            json.loads(discovery_path.read_text(encoding="utf8")) if discovery_path.exists() else {}
        )
        summary = {
            **report.get("summary", {}),
            "processes_discovered": discovery.get(
                "discovered_unique", len(report.get("processes", []))
            ),
            "processes_selected": len(report.get("processes", [])),
            "products_identified": len(candidates),
            "private_market_candidates": sum(c.status == "eligible" for c in candidates),
            "private_market_products_processed": sum(
                c.market_status == "processed" for c in candidates
            ),
            "private_market_products_failed": sum(c.market_status == "failed" for c in candidates),
            "private_market_observations_valid": sum(
                r["benchmark"]["valid_observations_count"] for r in reports
            ),
            "benchmarks_sufficient": sum(
                r["benchmark"]["benchmark_status"] == "ready" for r in reports
            ),
            "benchmarks_insufficient": sum(
                r["benchmark"]["benchmark_status"] != "ready" for r in reports
            ),
            "comparisons_generated": sum(r.get("comparison") is not None for r in reports),
            "comparisons_possible": sum(r.get("comparison") is not None for r in reports),
            "signals_generated": sum(r.get("signal") is not None for r in reports),
        }
        if not any(c.status == "eligible" for c in candidates):
            warnings.append("no_eligible_private_market_products")
        # Do not expose State-vs-State pairs/signals as results of a private run.
        return {
            **report,
            "summary": summary,
            "private_market_candidates": [c.model_dump(mode="json") for c in candidates],
            "market_reports": reports,
            "run_warnings": list(dict.fromkeys(warnings)),
            "comparisons": [],
            "signals": [],
            "comparisons_possible": 0,
            "economic_cycle_comparisons": None,
            "comparison_readiness": None,
            "comparison_policy": "state-vs-private-market-existing-policy",
            "comparability_counts": {},
            "signal_reason": (
                "Las comparaciones y señales privadas se muestran por producto "
                "y conservan la política de evidencia vigente."
            ),
            "signal_status": "signals_supported"
            if summary["signals_generated"]
            else "insufficient_evidence",
        }
