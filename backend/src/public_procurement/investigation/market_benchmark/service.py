"""Opt-in private research service with JSON-only persistence."""

import json
import re
from collections import Counter
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path
from typing import Any

from .aggregation import aggregate, compare, extract_mco_listing_id
from .matching import observe
from .mercadolibre_adapter import MercadoLibreResult
from .page_verifier import weak
from .ports import (
    MarketPageVerifier,
    MarketPriceScout,
    ScoutRequest,
    ScoutUnavailableError,
    ShoppingDiscoveryResult,
    ShoppingSearchPort,
    WebSearch,
)
from .schemas import (
    MarketObservation,
    PageEvidence,
    ProductIdentity,
    PublicOffer,
    PublicPriceEvidence,
    PublicProduct,
    RejectionReason,
    SearchResult,
)
from .urls import canonical_url
from .web_discovery import WebDiscoveryResult, discover_web


def _safe_collect(
    adapter: Any, product: ProductIdentity, ids: list[str], discover_catalog: bool | None = None
) -> MercadoLibreResult:
    try:
        batch = adapter.collect(product, listing_ids=ids, discover_catalog=discover_catalog)
        if not isinstance(batch, MercadoLibreResult):
            raise ValueError("Invalid optional source result")
        if not isinstance(batch.diagnostics, dict) or not all(
            isinstance(batch.diagnostics.get(key), list) for key in ("errors", "warnings")
        ):
            raise ValueError("Invalid optional source diagnostics")
        return batch
    except Exception as exc:  # optional source boundary; never print exception text
        batch = MercadoLibreResult()
        batch.diagnostics.update(source_status="degraded", requests=[], request_count=0)
        batch.diagnostics["errors"].append(
            {"code": "marketplace_source_failure", "error_type": type(exc).__name__}
        )
        return batch


def _canonical_context(product: ProductIdentity, batch: MercadoLibreResult) -> ProductIdentity:
    selected = batch.diagnostics.get("catalog_product_id")
    if not selected:
        return product
    details = batch.diagnostics.get("catalog_details", [])
    if not isinstance(details, list):
        return product
    for detail in details:
        if not isinstance(detail, dict):
            continue
        if detail.get("id") == selected and detail.get("match_level") in {"exact", "high"}:
            attributes = detail.get("attributes", [])
            if not isinstance(attributes, list):
                continue
            for attribute in attributes:
                if not isinstance(attribute, dict):
                    continue
                model = attribute.get("value_name")
                if (
                    attribute.get("id") == "MODEL"
                    and isinstance(model, str)
                    and re.fullmatch(r"[A-Za-z0-9-]{4,100}", model.strip())
                ):
                    return product.model_copy(update={"canonical_model": model.strip().upper()})
    return product


def run_benchmark(
    product: ProductIdentity,
    search: WebSearch | None = None,
    now: datetime | None = None,
    marketplace_adapter: Any = None,
    listing_ids: list[str] | None = None,
    *,
    scout: MarketPriceScout | None = None,
    shopping: ShoppingSearchPort | None = None,
    page_verifier: MarketPageVerifier | None = None,
    existing_receipt: dict[str, Any] | None = None,
    target_observations: int = 3,
    max_observations: int = 5,
) -> dict[str, Any]:
    # Validate limits even if deterministic evidence already suffices.
    ScoutRequest(product, target_observations, max_observations)
    captured = now or datetime.now(UTC)
    shopping_batch = ShoppingDiscoveryResult(
        diagnostics={"source_status": "not_configured", "warnings": []}
    )
    if shopping is not None:
        try:
            shopping_batch = shopping.discover(
                product, target=target_observations, maximum=max_observations
            )
            if (
                not isinstance(shopping_batch, ShoppingDiscoveryResult)
                or not isinstance(shopping_batch.diagnostics, dict)
                or not isinstance(shopping_batch.errors, list)
                or not all(isinstance(o, MarketObservation) for o in shopping_batch.observations)
            ):
                raise ValueError("invalid_shopping_response")
        except Exception as exc:  # optional provider boundary, no error bodies/credentials
            shopping_batch = ShoppingDiscoveryResult(
                diagnostics={"source_status": "degraded", "warnings": []},
                errors=[{"code": "shopping_source_failed", "error_type": type(exc).__name__}],
            )
    batch = None
    if marketplace_adapter is not None:
        batch = _safe_collect(
            marketplace_adapter,
            product,
            [],
            discover_catalog=False if shopping is not None else None,
        )
        product = _canonical_context(product, batch)
    discovery = discover_web(product, search) if search else WebDiscoveryResult()
    candidates = [c.model_dump(mode="json") for c in discovery.candidates]
    query = f'{product.brand} "{product.canonical_model or product.model}" precio Colombia COP'
    observations = [*shopping_batch.observations, *discovery.observations]
    if existing_receipt is not None:
        identity = existing_receipt.get("product", {})
        if (
            identity.get("model") != product.model
            or identity.get("brand", "").casefold() != product.brand.casefold()
        ):
            raise ValueError("Web receipt belongs to a different product")
        reused = [
            SearchResult.model_validate(c) for c in existing_receipt.get("candidates", [])[:90]
        ]
        observations.extend(observe(product, c) for c in reused)
        candidates.extend(c.model_dump(mode="json") for c in reused)
    seen_items = set(listing_ids or []) | {
        iid for row in observations if (iid := extract_mco_listing_id(str(row.url)))
    }
    if batch is not None:
        _enrich_listings(
            marketplace_adapter,
            product,
            batch,
            list(
                dict.fromkeys(
                    [
                        *(listing_ids or []),
                        *[
                            iid
                            for row in observations
                            if (iid := extract_mco_listing_id(str(row.url)))
                        ],
                    ]
                )
            )[:10],
        )
    errors = [*discovery.errors, *shopping_batch.errors]
    page_diagnostic: dict[str, Any] = {"attempted": 0, "verified": 0, "rejected": 0, "budget": 10}
    verified_urls: dict[str, MarketObservation] = {}

    def verify_candidate(row: MarketObservation) -> MarketObservation:
        iid = extract_mco_listing_id(str(row.url))
        if batch is not None and iid and row.source_type == "shopping_provider":
            rejection = next(
                (
                    o
                    for o in batch.observations
                    if o.listing_id == iid and o.match_level == "reject"
                ),
                None,
            )
            if rejection is not None:
                return row.model_copy(
                    update={
                        "valid_for_benchmark": False,
                        "verification_status": "rejected",
                        "notes": [*row.notes, "api_enrichment_rejected:" + rejection.match_reason],
                    }
                )
        if (
            batch is not None
            and iid
            and any(o.listing_id == iid and o.valid_for_benchmark for o in batch.observations)
        ):
            return weak(row, RejectionReason.STALE_OR_CACHE_ONLY).model_copy(
                update={"notes": [*row.notes, "api_verified_price_available"]}
            )
        if row.source_type == "shopping_provider" and row.valid_for_benchmark:
            return row  # structured provider price is useful without claiming a store-page visit
        if row.page_type not in {"product_page", "marketplace_listing"}:
            return weak(row, RejectionReason.GENERIC_PAGE, "rejected")
        url = canonical_url(str(row.url))
        if url in verified_urls:
            reused_page = verified_urls[url].model_copy(deep=True)
            reused_page.discovered_queries = list(
                dict.fromkeys(
                    [
                        *reused_page.discovered_queries,
                        *row.discovered_queries,
                    ]
                )
            )
            return reused_page
        if page_verifier is None or page_diagnostic["attempted"] >= 10:
            if row.source_type == "shopping_provider":
                return row  # preserve the provider's identity/currency rejection, not a cache claim
            return weak(row, RejectionReason.STALE_OR_CACHE_ONLY)
        page_diagnostic["attempted"] += 1
        try:
            checked = page_verifier.verify(product, row)
            if not isinstance(checked, MarketObservation):
                raise ValueError("invalid_verifier_result")
            # Even an adapter cannot promote snippet evidence to a verified monetary observation.
            checked.valid_for_benchmark = (
                checked.valid_for_benchmark
                and checked.verification_status == "verified"
                and checked.price_evidence_level == "page_verified_price"
                and isinstance(checked.evidence, PageEvidence)
                and checked.evidence.http_status == 200
                and checked.match_level in {"exact", "high"}
                and checked.price is not None
                and checked.price > 0
                and checked.currency == "COP"
            )
            if not checked.valid_for_benchmark and checked.verification_status == "verified":
                checked = weak(row, RejectionReason.VERIFICATION_FAILED, "failed")
        except (OSError, ValueError, TypeError):
            checked = weak(row, RejectionReason.VERIFICATION_FAILED, "failed")
        page_diagnostic["verified" if checked.valid_for_benchmark else "rejected"] += 1
        verified_urls[url] = checked
        return checked

    checked_initial: list[MarketObservation] = []
    for row in observations:
        current = aggregate(
            product, [*checked_initial, *(batch.observations if batch else [])], captured
        )
        done = current.valid_observations_count >= max_observations or (
            current.valid_observations_count >= target_observations
            and current.independent_sources_count >= 2
        )
        if done:
            deferred = weak(row, RejectionReason.STALE_OR_CACHE_ONLY)
            deferred.notes.append("verification_deferred_sufficient_evidence")
            checked_initial.append(deferred)
        else:
            checked_initial.append(verify_candidate(row))
    observations = checked_initial

    def all_observations() -> list[MarketObservation]:
        return [*observations, *(batch.observations if batch else [])]

    def sufficient() -> bool:
        current = aggregate(product, all_observations(), captured)
        return (
            current.valid_observations_count >= target_observations
            and current.independent_sources_count >= 2
        )

    initial = aggregate(product, all_observations(), captured).valid_observations_count
    diagnostic: dict[str, Any] = {
        "activated": not sufficient() and initial < max_observations and scout is not None,
        "status": "not_needed" if sufficient() or initial >= max_observations else "not_configured",
        "initial_valid_observations": initial,
        "target_observations": target_observations,
        "max_observations": max_observations,
        "requested_missing_observations": (
            max(1, target_observations - initial)
            if not sufficient() and initial < max_observations
            else 0
        ),
        "candidates_received": 0,
        "candidate_budget": 10,
        "errors": [],
    }
    if diagnostic["activated"] and scout is not None:
        request = ScoutRequest(
            product=product,
            target_observations=max(1, target_observations - initial),
            max_observations=max_observations - initial,
            excluded_urls=tuple(str(o.url) for o in all_observations() if o.valid_for_benchmark),
        )
        diagnostic["status"] = "insufficient"
        stream = None
        try:
            stream = iter(scout.scout(request))
            for supplied in islice(stream, 10):
                diagnostic["candidates_received"] += 1
                if not isinstance(supplied, MarketObservation) or not isinstance(
                    supplied.evidence, SearchResult
                ):
                    raise ScoutUnavailableError("invalid_scout_observation")
                # Never trust model-provided match/price/validity fields. Recompute from evidence.
                observation = observe(product, supplied.evidence)
                observation.discovery_method = "market_price_scout"
                observation.extraction_method = supplied.extraction_method
                observation.notes = list(dict.fromkeys([*observation.notes, *supplied.notes]))
                candidates.append(supplied.evidence.model_dump(mode="json"))
                iid = extract_mco_listing_id(str(observation.url))
                if batch is not None and iid and iid not in seen_items:
                    seen_items.add(iid)
                    enrichment = _enrich_listings(marketplace_adapter, product, batch, [iid])
                    for row in enrichment.observations:
                        row.discovery_method = "market_price_scout"
                        row.extraction_method = "mercadolibre_api"
                        row.notes.append(f"scout_web_evidence:{observation.url}")
                observations.append(verify_candidate(observation))
                count = aggregate(product, all_observations(), captured).valid_observations_count
                if sufficient() or count >= max_observations:
                    diagnostic["status"] = (
                        "target_reached" if sufficient() else "max_observations_reached"
                    )
                    break
        except (ScoutUnavailableError, OSError, ValueError, TypeError) as exc:
            issue: dict[str, Any] = {
                "code": "market_price_scout_failed",
                "error_type": type(exc).__name__,
            }
            if isinstance(exc, ScoutUnavailableError):
                if exc.error_type:
                    issue["provider_error_type"] = exc.error_type
                if exc.http_status:
                    issue["http_status"] = exc.http_status
            diagnostic["errors"].append(issue)
            errors.append(issue)
            diagnostic["status"] = "degraded"
        finally:
            close = getattr(stream, "close", None)
            if close:
                close()
    captured = now or datetime.now(UTC)
    if batch is not None:
        errors.extend(batch.diagnostics["errors"])
    report = build_report(product, all_observations(), captured, query, candidates, errors)
    degradations = (
        [
            {"source": "mercadolibre", **issue}
            for issue in [*batch.diagnostics["errors"], *batch.diagnostics["warnings"]]
        ]
        if batch
        else []
    )
    report["shopping_discovery"] = shopping_batch.diagnostics
    shopping_issues = [*shopping_batch.errors, *shopping_batch.diagnostics.get("warnings", [])]
    degradations.extend({"source": "shopping_discovery", **issue} for issue in shopping_issues)
    report["benchmark"]["limitations"].extend(
        "shopping:" + issue["code"] for issue in shopping_issues
    )
    if batch is not None:
        report["mercadolibre"] = batch.diagnostics
    degradations.extend(
        {"source": "page_verification", "code": row.rejection_reason.value, "url": str(row.url)}
        for row in verified_urls.values()
        if row.rejection_reason in {RejectionReason.BLOCKED, RejectionReason.VERIFICATION_FAILED}
    )
    report["source_degradations"] = degradations
    report["status"] = "completed_with_warnings" if errors or degradations else "completed"
    if existing_receipt is not None:
        report["benchmark"]["limitations"].append("web_evidence_reused_at_original_capture_time")
    report["market_price_scout"] = diagnostic
    page_diagnostic["rejection_reasons"] = dict(
        Counter(
            row.rejection_reason.value for row in observations if row.rejection_reason is not None
        )
    )
    report["page_verification"] = page_diagnostic
    if initial < target_observations and diagnostic["status"] != "target_reached":
        report["benchmark"]["limitations"].append("scout_" + diagnostic["status"])
    report["web_discovery"] = {
        **discovery.diagnostics,
        "catalog_product_id_used": batch.diagnostics.get("catalog_product_id") if batch else None,
    }
    return report


def _merge_batches(batch: MercadoLibreResult, extra: MercadoLibreResult) -> None:
    batch.observations.extend(extra.observations)
    for key in ("errors", "warnings", "requests", "listing_candidates"):
        batch.diagnostics[key] = [*batch.diagnostics.get(key, []), *extra.diagnostics.get(key, [])]
    batch.diagnostics["request_count"] = len(batch.diagnostics.get("requests", []))
    batch.diagnostics["source_status"] = (
        "degraded" if batch.diagnostics["errors"] or batch.diagnostics["warnings"] else "available"
    )


def build_report(
    product: ProductIdentity,
    observations: list[MarketObservation],
    captured: datetime,
    query: str,
    candidates: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    benchmark = aggregate(product, observations, captured)
    comparison = compare(product, benchmark) if isinstance(product, PublicProduct) else None
    signal = None
    if comparison and isinstance(product, PublicProduct) and not product.evidence_warnings:
        signal = {
            "type": "PUBLIC_VS_PRIVATE_PRICE_DIFFERENCE",
            "meaning": "Existe una diferencia cuantificada entre el precio público documentado "
            "y el benchmark privado actual.",
            "comparison": comparison.model_dump(mode="json"),
            "public_evidence": product.model_dump(mode="json"),
        }
    preliminary = None
    if isinstance(product, PublicOffer):
        preliminary = {
            "status": "preliminary_not_confirmed_purchase",
            "public_offer": product.model_dump(mode="json"),
            "private_median_price": str(benchmark.median_price)
            if benchmark.median_price is not None
            else None,
            "absolute_difference": None,
            "percentage_difference": None,
            "limitations": [
                "offer_acceptance_not_confirmed",
                "tax_basis_not_aligned_no_price_difference_calculated",
                *product.evidence_warnings,
                *benchmark.limitations,
            ],
        }
    if isinstance(product, PublicPriceEvidence) and product.evidence_warnings:
        comparison = None
    return {
        "schema_version": "private-market-benchmark-v0.1",
        "errors": errors,
        "query": query,
        "product": product.model_dump(mode="json"),
        "public_product": product.model_dump(mode="json")
        if isinstance(product, PublicPriceEvidence)
        else None,
        "public_evidence_status": "documented_unconfirmed_offer"
        if isinstance(product, PublicOffer)
        else "provided"
        if isinstance(product, PublicProduct)
        else "missing_public_evidence",
        "candidates": candidates,
        "benchmark": benchmark.model_dump(mode="json"),
        "comparison": comparison.model_dump(mode="json") if comparison else None,
        "signal": signal,
        "preliminary_comparison": preliminary,
    }


def _enrich_listings(
    adapter: Any, product: ProductIdentity, batch: MercadoLibreResult, ids: list[str]
) -> MercadoLibreResult:
    blocked = any(
        e.get("http_status") in {401, 403, 429} or e.get("code") == "missing_auth_configuration"
        for e in batch.diagnostics["errors"]
    )
    extra = MercadoLibreResult()
    if ids and not blocked:
        extra = _safe_collect(adapter, product, ids, discover_catalog=False)
        _merge_batches(batch, extra)
    return extra


def run_mercadolibre_benchmark(
    product: ProductIdentity,
    adapter: Any,
    web_receipt: dict[str, Any] | None = None,
    listing_ids: list[str] | None = None,
    *,
    page_verifier: MarketPageVerifier | None = None,
) -> dict[str, Any]:
    return run_benchmark(
        product,
        marketplace_adapter=adapter,
        existing_receipt=web_receipt,
        listing_ids=listing_ids,
        page_verifier=page_verifier,
    )


class MarketReportStore:
    def __init__(self, directory: Path) -> None:
        self.path = directory / "private-market-latest.json"

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": "private-market-benchmark-v0.1", "reports": []}
        data: dict[str, Any] = json.loads(self.path.read_text(encoding="utf8"))
        if data.get("schema_version") != "private-market-benchmark-v0.1":
            raise ValueError("Invalid private-market report")
        return data

    def write(self, report: dict[str, Any]) -> None:
        # Public reports, raw evidence, DB and Estado-vs-Estado are never modified.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"schema_version": "private-market-benchmark-v0.1", "reports": [report]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf8",
        )
        temporary.replace(self.path)
