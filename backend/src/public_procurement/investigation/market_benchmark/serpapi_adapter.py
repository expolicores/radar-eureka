"""Limited structured Shopping → Product → optional Immersive discovery."""

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlsplit

from public_procurement.shared.text import normalize_text

from .aggregation import aggregate
from .matching import match_identity
from .ports import ShoppingDiscoveryResult
from .query_expansion import model_family
from .schemas import ApiEvidence, MarketObservation, ProductIdentity, RejectionReason, SearchResult
from .serpapi_http import ENDPOINT, SerpApiError, SerpApiTransport, public_parameters
from .web_pages import classify_page

STORE_FIELDS = (
    "position",
    "name",
    "source",
    "title",
    "link",
    "product_link",
    "price",
    "extracted_price",
    "currency",
    "shipping",
    "condition",
    "details_and_offers",
    "rating",
    "reviews",
    "merchant_id",
    "discount",
    "coupon",
    "alt_currency",
)
CONTRADICTIONS = {
    "different_model",
    "conflicting_models_in_title",
    "different_size",
    "different_capacity",
    "accessory_or_service",
    "used_or_refurbished",
    "non_comparable_bundle",
}


def shopping_query(product: ProductIdentity) -> str:
    return " ".join(
        v.strip()
        for v in (
            product.brand,
            product.canonical_model or product.model,
            product.product_type,
            product.size,
            product.capacity,
        )
        if v and v.strip()
    )


def store_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        return (
            parsed.scheme == "https"
            and bool(host)
            and not parsed.username
            and not parsed.password
            and parsed.path.strip("/") != ""
            and not re.search(r"(^|\.)google\.[a-z.]+$", host)
            and host != "serpapi.com"
            and not host.endswith(".serpapi.com")
        )
    except ValueError:
        return False


def _price(value: Any) -> Decimal | None:
    if not isinstance(value, (int, float, Decimal)) or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
        return result if result.is_finite() and result > 0 else None
    except InvalidOperation:
        return None


def _co_context(payload: dict[str, Any], inherited: bool = False) -> bool:
    parameters = payload.get("search_parameters")
    if isinstance(parameters, dict) and "gl" in parameters:
        return bool(parameters["gl"] == "co")
    return inherited


def _product_text(details: dict[str, Any]) -> str:
    attributes = details.get("product_attributes")
    extra = (
        " ".join(
            str(a.get("name") or "") + " " + str(a.get("value") or "")
            for a in attributes
            if isinstance(a, dict)
        )
        if isinstance(attributes, list)
        else ""
    )
    return " ".join([str(details.get("title") or ""), str(details.get("brand") or ""), extra])


def normalize_offer(
    product: ProductIdentity,
    row: dict[str, Any],
    details: dict[str, Any],
    product_id: str | None,
    engine: str,
    query: str,
    market_co: bool,
    captured: datetime,
    search_id: str | None = None,
    *,
    candidate: bool = False,
) -> MarketObservation | None:
    url = row.get("product_link") if candidate else row.get("link")
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return None
    title = str(row.get("title") or "")
    # Parent model/attributes must NEVER supply a missing store reference.
    brand = str(details.get("brand") or "")
    match = match_identity(product, " ".join([title, brand, str(row.get("condition") or "")]))
    context_match = match_identity(product, _product_text(details))
    notes = ["shopping_provider_not_page_or_checkout_verified"]
    price = _price(row.get("extracted_price"))
    formatted = str(row.get("price") or "")
    explicit_currency = row.get("currency")
    inferred = False
    currency = str(explicit_currency).upper() if explicit_currency else None
    foreign_price = bool(re.search(r"USD|US\$|EUR|MXN|ARS|BRL|R\$", formatted, re.I))
    if currency == "COP" and foreign_price:
        currency = None
        notes.append("provider_currency_conflict")
    if currency is None and not foreign_price and re.search(r"\bCOP\b", formatted, re.I):
        currency = "COP"
    if (
        currency is None
        and market_co
        and "$" in formatted
        and not row.get("alt_currency")
        and not foreign_price
    ):
        currency, inferred = "COP", True
        notes.append("currency_inferred_from_serpapi_colombia_context")
    reason = None
    if brand and normalize_text(brand) != normalize_text(product.brand):
        reason = RejectionReason.WRONG_BRAND
    elif context_match.reason in CONTRADICTIONS and not candidate:
        reason = RejectionReason.WRONG_MODEL
    elif match.level not in {"exact", "high"}:
        reason = (
            RejectionReason.WRONG_SIZE
            if match.reason in {"different_size", "different_capacity"}
            else RejectionReason.ACCESSORY_OR_REPLACEMENT
            if match.reason == "accessory_or_service"
            else RejectionReason.WRONG_MODEL
            if match.reason in CONTRADICTIONS
            else None
        )
        if reason is None:
            notes.append("identity_ambiguous_not_monetary")
    elif price is None:
        reason = RejectionReason.NO_PRICE
    elif currency != "COP":
        reason = RejectionReason.CURRENCY_UNKNOWN
    elif not store_url(url) or not row.get("name"):
        reason = RejectionReason.GENERIC_PAGE
    elif re.search(r"cuotas?|mensual|per month", formatted, re.I):
        reason = RejectionReason.AMBIGUOUS_PRICE
    availability = "unknown"
    shipping_details = " ".join(str(v) for v in row.get("details_and_offers", []) or [])
    if re.search(r"out.?of.?stock|agotado|no disponible|sin stock", shipping_details, re.I):
        availability, reason = "unavailable", RejectionReason.UNAVAILABLE
    elif re.search(r"en stock|in stock", shipping_details, re.I):
        availability = "available"
    if candidate:
        notes.append("shopping_candidate_requires_store_details")
    classification = classify_page(
        product,
        SearchResult(
            title=title,
            snippet=formatted,
            url=url,
            query=query,
            captured_at=captured,
            search_provider="serpapi",
        ),
    )
    if classification.kind in {"home_page", "brand_page", "category_page", "editorial"}:
        reason = RejectionReason.GENERIC_PAGE
    response = {
        "store": {k: row[k] for k in STORE_FIELDS if k in row},
        "product": {
            k: details[k]
            for k in ("title", "brand", "product_attributes", "price_range")
            if k in details
        },
        "product_id": product_id,
        "engine": engine,
        "query": query,
        "market_gl_co_confirmed": market_co,
        "search_id": search_id,
    }
    return MarketObservation(
        retailer=str(row.get("name") or row.get("source") or parsed.hostname),
        market_product_title=title,
        brand=match.brand,
        model=match.model,
        price=price,
        currency=currency,
        currency_inferred=inferred,
        url=url,
        captured_at=captured,
        source="serpapi_" + engine,
        source_type="shopping_provider",
        discovery_method="serpapi_google_shopping",
        extraction_method="structured_shopping_provider",
        price_evidence_level="shopping_provider_price",
        verification_status="weak" if candidate else "not_attempted",
        product_id=product_id,
        seller_id=str(row["merchant_id"]) if row.get("merchant_id") else None,
        seller_name=str(row.get("name") or "") or None,
        shipping=row.get("shipping") if isinstance(row.get("shipping"), (str, dict)) else None,
        condition=str(row.get("condition") or "") or None,
        availability=availability,
        provider_metadata={
            "identity_diagnostic": "ambiguous"
            if match.reason not in CONTRADICTIONS and match.level not in {"exact", "high"}
            else match.level,
            **{
                k: row[k]
                for k in ("position", "rating", "reviews", "discount", "coupon")
                if k in row
            },
        },
        page_type=classification.kind
        if candidate
        else "marketplace_listing"
        if "mercadolibre.com.co" in parsed.hostname
        else "product_page",
        web_source_kind="marketplace_web"
        if "mercadolibre.com.co" in parsed.hostname
        else "retailer_web",
        match_level=match.level,
        match_reason=match.reason,
        rejection_reason=reason,
        valid_for_benchmark=not candidate
        and reason is None
        and match.level in {"exact", "high"}
        and price is not None
        and currency == "COP"
        and store_url(url)
        and bool(row.get("name")),
        evidence=ApiEvidence(
            source="serpapi",
            site_id=None,
            endpoint=ENDPOINT,
            captured_at=captured,
            response=response,
        ),
        notes=notes,
        discovered_queries=[query],
    )


class SerpApiShoppingAdapter:
    def __init__(self, transport: SerpApiTransport, *, enable_immersive: bool = True) -> None:
        self.transport, self.enable_immersive = transport, enable_immersive

    def discover(
        self, product: ProductIdentity, target: int = 3, maximum: int = 5
    ) -> ShoppingDiscoveryResult:
        if not 1 <= target <= maximum <= 5:
            raise ValueError("Invalid shopping observation limits")
        captured, query = datetime.now(UTC), shopping_query(product)
        result = ShoppingDiscoveryResult(
            diagnostics={
                "requests": [],
                "warnings": [],
                "query": query,
                "selected_product_ids": [],
                "shopping_results_received": 0,
                "retries": 0,
                "request_budget": 6,
                "immersive_pages": 0,
                "shopping_candidates": [],
            }
        )
        d = result.diagnostics

        def issue(code: str, **fields: Any) -> None:
            d["warnings"].append({"code": code, **fields})

        def blocked() -> bool:
            return any(
                e["code"] in {"authentication_failed", "rate_limited", "missing_api_key"}
                for e in result.errors
            )

        def request(parameters: dict[str, str]) -> dict[str, Any] | None:
            if blocked() or len(d["requests"]) >= 6:
                return None
            record: dict[str, Any] = {"parameters": public_parameters(parameters)}
            d["requests"].append(record)
            try:
                payload = self.transport.search(parameters)
                if not isinstance(payload, dict):
                    raise SerpApiError("invalid_payload")
                info = payload.get("search_information")
                record["product_results_state"] = (
                    info.get("product_results_state") if isinstance(info, dict) else None
                )
                if record["product_results_state"]:
                    issue(
                        "partial_provider_response",
                        engine=parameters["engine"],
                        state=record["product_results_state"],
                    )
                if payload.get("error"):
                    issue(
                        "provider_empty_or_error",
                        engine=parameters["engine"],
                        state=record["product_results_state"],
                    )
                return payload
            except SerpApiError as exc:
                record.update(code=exc.code, http_status=exc.http_status)
                result.errors.append({"code": exc.code, "http_status": exc.http_status})
            except Exception as exc:  # external source boundary, no exception body/URL in receipts
                record["code"] = "source_failure"
                result.errors.append({"code": "source_failure", "error_type": type(exc).__name__})
            return None

        def sufficient() -> bool:
            benchmark = aggregate(product, result.observations, captured)
            return benchmark.valid_observations_count >= maximum or (
                benchmark.valid_observations_count >= target
                and benchmark.independent_sources_count >= 2
            )

        def stores(
            payload: dict[str, Any], pid: str, engine: str, market_co: bool
        ) -> dict[str, Any]:
            details = payload.get("product_results")
            if not isinstance(details, dict):
                issue("missing_product_results", product_id=pid)
                return {}
            rows = details.get("stores")
            if not isinstance(rows, list) or not rows:
                issue("product_without_stores", product_id=pid)
                return details
            metadata = payload.get("search_metadata")
            search_id = (
                str(metadata.get("id"))
                if isinstance(metadata, dict) and metadata.get("id")
                else None
            )
            for row in rows[:30]:
                if not isinstance(row, dict):
                    continue
                observation = normalize_offer(
                    product,
                    row,
                    details,
                    pid,
                    engine,
                    query,
                    _co_context(payload, market_co),
                    captured,
                    search_id,
                )
                if observation:
                    result.observations.append(observation)
                if sufficient():
                    break
            return details

        shopping = request(
            {
                "engine": "google_shopping",
                "q": query,
                "gl": "co",
                "hl": "es",
                "location": "Bogota, Bogota, Colombia",
            }
        )
        pending = []
        if shopping is not None:
            rows = shopping.get("shopping_results")
            if not isinstance(rows, list):
                issue("missing_shopping_results")
                rows = []
            elif not rows:
                issue("empty_shopping_results")
            d["shopping_results_received"] = len(rows)
            co = _co_context(shopping)
            plausible = []
            for row in rows[:40]:
                if not isinstance(row, dict):
                    continue
                pid = str(row.get("product_id") or "")
                observed = normalize_offer(
                    product, row, {}, pid, "google_shopping", query, co, captured, candidate=True
                )
                if observed:
                    d["shopping_candidates"].append(observed.model_dump(mode="json"))
                title = str(row.get("title") or "")
                match = match_identity(product, title)
                if not re.fullmatch(r"\d{1,30}", pid) or match.reason in CONTRADICTIONS:
                    continue
                if not re.search(r"\b" + re.escape(product.brand) + r"\b", title, re.I):
                    continue
                family = product.product_family or model_family(product) or product.model
                score = (100 if match.level in {"exact", "high"} else 0) + (
                    30 if family.casefold() in title.casefold() else 0
                )
                plausible.append((score, pid))
            selected = list(
                dict.fromkeys(pid for _, pid in sorted(plausible, key=lambda pair: -pair[0]))
            )[:3]
            d["selected_product_ids"] = selected
            for pid in selected:
                if sufficient() or blocked():
                    break
                payload = request(
                    {
                        "engine": "google_product",
                        "product_id": pid,
                        "offer_view": "true",
                        "gl": "co",
                        "hl": "es",
                    }
                )
                if payload is None:
                    continue
                details = stores(payload, pid, "google_product", co)
                token = details.get("page_token")
                parent = match_identity(product, _product_text(details))
                compatible = parent.reason not in CONTRADICTIONS and (
                    parent.level in {"exact", "high"}
                    or any(
                        o.product_id == pid and o.valid_for_benchmark for o in result.observations
                    )
                )
                if isinstance(token, str) and token and compatible:
                    pending.append((pid, token, _co_context(payload, co)))
                elif not token and not sufficient():
                    issue("page_token_absent", product_id=pid)
            if self.enable_immersive and pending and not sufficient() and not blocked():
                pid, token, product_co = pending[0]
                next_token = None
                for _ in range(2):
                    params = {
                        "engine": "google_immersive_product",
                        "page_token": token,
                        "more_stores": "true",
                        "gl": "co",
                        "hl": "es",
                    }
                    if next_token:
                        params["next_page_token"] = next_token
                    payload = request(params)
                    d["immersive_pages"] += int(payload is not None)
                    if payload is None:
                        break
                    details = stores(payload, pid, "google_immersive_product", product_co)
                    more = details.get("stores_next_page_token")
                    if sufficient() or not isinstance(more, str) or not more or more == next_token:
                        break
                    next_token = more
        benchmark = aggregate(product, result.observations, captured)
        d.update(
            request_attempts=len(d["requests"]),
            request_count=sum(r.get("code") != "missing_api_key" for r in d["requests"]),
            valid_observations=benchmark.valid_observations_count,
            source_status="degraded" if result.errors or d["warnings"] else "available",
            evidence_sufficiency=benchmark.evidence_sufficiency,
        )
        return result
