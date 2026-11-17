"""Bounded direct-page verification. No JS, retailer API, cookies or link crawling."""

import hashlib
import ipaddress
import json
import re
import socket
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

import httpx

from public_procurement.shared.text import normalize_text

from .matching import match_identity
from .schemas import (
    ApiEvidence,
    MarketObservation,
    PageEvidence,
    ProductIdentity,
    RejectionReason,
    SearchResult,
)
from .urls import canonical_url
from .web_pages import classify_page


@dataclass(frozen=True)
class PageResponse:
    url: str
    status: int
    body: bytes
    headers: dict[str, str]


def public_url(url: str) -> None:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.port not in {None, 443}
    ):
        raise ValueError("unsafe_page_url")
    addresses = socket.getaddrinfo(parts.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("nonpublic_page_url")


def fetch_page(url: str) -> PageResponse:
    deadline = time.monotonic() + 20
    # trust_env=False avoids sending requests through a configured credential-bearing proxy.
    with httpx.Client(
        timeout=10,
        follow_redirects=False,
        trust_env=False,
        headers={
            "User-Agent": "EurekaMarketPriceScout/1.1",
            "Accept": "text/html,application/xhtml+xml",
            "Cache-Control": "no-cache",
        },
    ) as client:
        for _ in range(4):
            if time.monotonic() >= deadline:
                raise ValueError("page_budget_exceeded")
            public_url(url)
            client.cookies.clear()
            with client.stream(
                "GET", url, timeout=max(0.1, min(10, deadline - time.monotonic()))
            ) as response:
                headers = {
                    k.lower(): v
                    for k, v in response.headers.items()
                    if k.lower() in {"content-type", "warning", "location"}
                }
                if response.status_code in {301, 302, 303, 307, 308}:
                    url = urljoin(url, response.headers.get("location", ""))
                    continue
                if response.status_code != 200:
                    return PageResponse(url, response.status_code, b"", headers)
                if "html" not in headers.get("content-type", "").lower():
                    raise ValueError("not_html")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 2_000_000 or time.monotonic() > deadline:
                        raise ValueError("page_budget_exceeded")
                return PageResponse(url, response.status_code, bytes(body), headers)
    raise ValueError("redirect_budget_exceeded")


class ProductHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, list[str]] = {}
        self.json_blocks: list[str] = []
        self.title: list[str] = []
        self._script: list[str] | None = None
        self._title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and (values.get("type") or "").lower() == "application/ld+json":
            self._script = []
        if tag == "title":
            self._title = True
        key = values.get("property") or values.get("name") or values.get("itemprop")
        if key and values.get("content"):
            self.meta.setdefault(key.lower(), []).append(str(values["content"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script is not None:
            self.json_blocks.append("".join(self._script))
            self._script = None
        if tag == "title":
            self._title = False

    def handle_data(self, data: str) -> None:
        if self._script is not None:
            self._script.append(data)
        if self._title:
            self.title.append(data)


def _name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or "")
    return str(value or "")


def _screen_inches(value: Any) -> Decimal | None:
    text = _name(value)
    if isinstance(value, dict):
        text += " " + str(value.get("unitText") or value.get("unitCode") or "")
    number = re.match(r"\s*(\d+(?:[.,]\d+)?)", text)
    if number is None:
        return None
    size = Decimal(number[1].replace(",", "."))
    if re.search(r"\b(cm|cmt|centimetros?)\b", normalize_text(text)):
        return size / Decimal("2.54")
    if re.search(r"\b(mm|mmt|milimetros?)\b", normalize_text(text)):
        return size / Decimal("25.4")
    return size


def _products(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [p for v in value for p in _products(v)]
    if isinstance(value, dict):
        kind = value.get("@type", [])
        if "Product" in (kind if isinstance(kind, list) else [kind]):
            return [value]
        return [p for v in value.values() if isinstance(v, (list, dict)) for p in _products(v)]
    return []


def _price(value: Any) -> Decimal | None:
    text = str(value or "").strip().replace(" ", "")
    if not re.fullmatch(r"\d+(?:[.,]\d+)*", text):
        return None
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?", text):
        if re.search(r"[.,]\d{2}$", text):
            text = re.sub(r"[.,]", "", text[:-3]) + "." + text[-2:]
        else:
            text = re.sub(r"[.,]", "", text)
    else:
        text = text.replace(",", ".")
    try:
        price = Decimal(text)
        return price if price.is_finite() and price > 0 else None
    except InvalidOperation:
        return None


def weak(
    candidate: MarketObservation, reason: RejectionReason, status: str = "weak"
) -> MarketObservation:
    result = candidate.model_copy(
        update={
            "valid_for_benchmark": False,
            "verification_status": status,
            "rejection_reason": reason,
            "price_evidence_level": "snippet_price"
            if isinstance(candidate.evidence, SearchResult)
            else candidate.price_evidence_level,
        }
    )
    if reason in {
        RejectionReason.WRONG_MODEL,
        RejectionReason.WRONG_SIZE,
        RejectionReason.WRONG_PRODUCT_TYPE,
        RejectionReason.WRONG_BRAND,
        RejectionReason.ACCESSORY_OR_REPLACEMENT,
    }:
        result.match_level, result.match_reason = "reject", reason.value
    return result


def _identity_reason(reason: str) -> RejectionReason:
    if "size" in reason or "capacity" in reason:
        return RejectionReason.WRONG_SIZE
    if reason in {"accessory_or_service", "used_or_refurbished", "non_comparable_bundle"}:
        return RejectionReason.ACCESSORY_OR_REPLACEMENT
    if "brand" in reason:
        return RejectionReason.WRONG_BRAND
    return RejectionReason.WRONG_MODEL


class HttpMarketPageVerifier:
    def __init__(self, fetch: Callable[[str], PageResponse] = fetch_page) -> None:
        self.fetch = fetch

    def verify(self, product: ProductIdentity, candidate: MarketObservation) -> MarketObservation:
        if candidate.page_type not in {"product_page", "marketplace_listing"}:
            return weak(candidate, RejectionReason.GENERIC_PAGE, "rejected")
        try:
            page = self.fetch(str(candidate.url))
            return verify_response(product, candidate, page)
        except (httpx.HTTPError, OSError, ValueError, TypeError, RecursionError) as exc:
            result = weak(candidate, RejectionReason.VERIFICATION_FAILED, "failed")
            result.notes.append("page_verification_error_type:" + type(exc).__name__)
            return result


def verify_response(
    product: ProductIdentity, candidate: MarketObservation, page: PageResponse
) -> MarketObservation:
    if not isinstance(candidate.evidence, (SearchResult, ApiEvidence)):
        raise ValueError("page_candidate_requires_search_provenance")
    page_evidence = PageEvidence(
        candidate=candidate.evidence,
        final_url=page.url,
        captured_at=datetime.now(UTC),
        http_status=page.status,
        content_sha256=hashlib.sha256(page.body).hexdigest(),
        extracted_fields={},
        evidence_text="",
        extraction_sources=[],
    )
    candidate = candidate.model_copy(
        update={
            "evidence": page_evidence,
            "extraction_method": "direct_page_http",
            "source": "direct_page",
        }
    )
    if page.status in {401, 403, 429}:
        return weak(candidate, RejectionReason.BLOCKED, "blocked")
    if page.status == 304 or "110" in page.headers.get("warning", ""):
        return weak(candidate, RejectionReason.STALE_OR_CACHE_ONLY)
    if page.status != 200:
        return weak(candidate, RejectionReason.VERIFICATION_FAILED, "failed")
    parser = ProductHTML()
    parser.feed(page.body.decode("utf8", errors="replace"))
    title = " ".join(parser.title).strip()
    if re.search(r"captcha|access denied|acceso denegado|just a moment|robot check", title, re.I):
        return weak(candidate, RejectionReason.BLOCKED, "blocked")
    structured = []
    for block in parser.json_blocks[:30]:
        try:
            structured.extend(_products(json.loads(block)))
        except (ValueError, RecursionError):
            continue
    # A recommendation cannot provide the price of the page's actual product.
    linked = [
        p
        for p in structured
        if isinstance(p.get("url"), str)
        and canonical_url(urljoin(page.url, p["url"])) == canonical_url(page.url)
    ]
    if linked:
        structured = linked
    elif len(structured) > 1:
        return weak(candidate, RejectionReason.AMBIGUOUS_PRICE, "rejected")
    compatible = [
        p
        for p in structured
        if match_identity(
            product,
            " ".join(
                [
                    _name(p.get("brand")),
                    _name(p.get("name")),
                    _name(p.get("model")),
                    _name(p.get("mpn")),
                ]
            ),
        ).level
        in {"exact", "high"}
    ]
    selected = compatible if compatible else structured[:1]
    if len(selected) > 1:
        return weak(candidate, RejectionReason.AMBIGUOUS_PRICE, "rejected")
    data = selected[0] if selected else {}
    meta = parser.meta

    def meta_one(*keys: str) -> str:
        return next((v for k in keys for v in meta.get(k, [])), "")

    name = _name(data.get("name")) or meta_one("og:title", "twitter:title") or title
    brand = _name(data.get("brand")) or meta_one("product:brand", "brand")
    model = _name(data.get("model")) or _name(data.get("mpn")) or meta_one("product:model", "model")
    size = _name(data.get("screenSize")) or _name(data.get("size"))
    category = _name(data.get("category"))
    attributes = " ".join(
        _name(a.get("name")) + " " + _name(a.get("value"))
        for a in data.get("additionalProperty", [])
        if isinstance(a, dict)
    )
    identity_text = " ".join([name, brand, model, size, category, attributes])
    page_evidence.extracted_fields = {
        "name": name,
        "brand": brand,
        "model": model,
        "size": size,
        "category": category,
        "offers": data.get("offers", []),
    }
    page_evidence.evidence_text = identity_text[:5000]
    page_evidence.extraction_sources = ["json_ld_product_offer"] if data else ["product_meta"]
    match = match_identity(product, identity_text)
    candidate = candidate.model_copy(
        update={
            "market_product_title": name,
            "brand": brand or match.brand,
            "model": model or match.model,
            "match_level": match.level,
            "match_reason": match.reason,
            "price": None,
            "currency": None,
            "captured_at": page_evidence.captured_at,
            "url": page_evidence.final_url,
            "extraction_method": "direct_page_structured",
        }
    )
    if brand and normalize_text(brand) != normalize_text(product.brand):
        return weak(candidate, RejectionReason.WRONG_BRAND, "rejected")
    if model and match_identity(product, product.brand + " " + model).level not in {
        "exact",
        "high",
    }:
        return weak(candidate, RejectionReason.WRONG_MODEL, "rejected")
    expected_size = _screen_inches(product.size)
    actual_size = _screen_inches(data.get("screenSize") or data.get("size"))
    if expected_size is not None and actual_size is not None and expected_size != actual_size:
        return weak(candidate, RejectionReason.WRONG_SIZE, "rejected")
    if (
        product.product_type
        and re.search(r"televisor|television|\btv\b", normalize_text(product.product_type))
        and re.search(r"celular|smartphone|telefono|monitor|tablet", normalize_text(identity_text))
    ):
        return weak(candidate, RejectionReason.WRONG_PRODUCT_TYPE, "rejected")
    if match.level not in {"exact", "high"}:
        result = weak(candidate, _identity_reason(match.reason), "rejected")
        result.match_level, result.match_reason = match.level, match.reason
        return result
    captured = datetime.now(UTC)
    offers = data.get("offers", [])
    offers = offers if isinstance(offers, list) else [offers]
    if any(isinstance(o, dict) and o.get("@type") == "AggregateOffer" for o in offers):
        return weak(candidate, RejectionReason.AMBIGUOUS_PRICE, "rejected")
    prices, currencies = set(), set()
    availability, condition, seller, expiry = [], [], [], []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        spec = offer.get("priceSpecification") or {}
        value = _price(
            offer.get("price") or (spec.get("price") if isinstance(spec, dict) else None)
        )
        if value is not None:
            prices.add(value)
        currency = offer.get("priceCurrency") or (
            spec.get("priceCurrency") if isinstance(spec, dict) else None
        )
        if currency:
            currencies.add(str(currency).upper())
        availability.append(_name(offer.get("availability")))
        condition.append(_name(offer.get("itemCondition") or data.get("itemCondition")))
        seller.append(_name(offer.get("seller")))
        if offer.get("priceValidUntil"):
            expiry.append(str(offer["priceValidUntil"]))
    for key in ("product:price:amount", "og:price:amount", "price"):
        prices.update(p for v in meta.get(key, []) if (p := _price(v)) is not None)
    for key in ("product:price:currency", "og:price:currency", "pricecurrency"):
        currencies.update(v.upper().strip() for v in meta.get(key, []))
    availability.extend(meta.get("product:availability", []))
    page_evidence.extracted_fields.update(
        {
            "observed_prices": sorted(str(p) for p in prices),
            "observed_currencies": sorted(currencies),
        }
    )
    candidate.price = next(iter(prices)) if len(prices) == 1 else None
    candidate.currency = next(iter(currencies)) if len(currencies) == 1 else None
    reason = None
    if not prices:
        reason = RejectionReason.NO_PRICE
    elif len(prices) != 1:
        reason = RejectionReason.AMBIGUOUS_PRICE
    elif currencies != {"COP"}:
        reason = RejectionReason.CURRENCY_UNKNOWN
    elif any(
        re.search(
            r"out.?of.?stock|sold.?out|discontinued|agotado|unavailable|sin stock|no disponible",
            v,
            re.I,
        )
        for v in availability
    ):
        reason = RejectionReason.UNAVAILABLE
    elif any(re.search(r"used|refurbished|usado|reacondicionado", v, re.I) for v in condition):
        reason = RejectionReason.ACCESSORY_OR_REPLACEMENT
    for expiry_value in expiry:
        try:
            expires = datetime.fromisoformat(expiry_value)
            if len(expiry_value) == 10:
                expires = expires.replace(hour=23, minute=59, second=59)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=ZoneInfo("America/Bogota"))
            if expires <= captured:
                reason = RejectionReason.STALE_OR_CACHE_ONLY
        except ValueError:
            reason = RejectionReason.VERIFICATION_FAILED
    final = SearchResult(
        title=name,
        snippet=identity_text,
        url=page.url,
        query="direct_page",
        captured_at=captured,
        search_provider="direct_page",
    )
    assessment = classify_page(product, final)
    if assessment.kind not in {"product_page", "marketplace_listing"}:
        reason = RejectionReason.GENERIC_PAGE
    if reason is not None:
        return weak(candidate, reason, "rejected")
    page_evidence.extracted_fields.update(
        {
            "price": str(next(iter(prices))),
            "currency": "COP",
            "availability": availability,
            "condition": condition,
            "seller": seller,
        }
    )
    return candidate.model_copy(
        update={
            "retailer": urlsplit(page.url).hostname or "unknown",
            "source": "direct_page",
            "url": final.url,
            "market_product_title": name,
            "brand": brand or match.brand,
            "model": model or match.model,
            "match_level": match.level,
            "match_reason": match.reason,
            "price": next(iter(prices)),
            "currency": "COP",
            "captured_at": captured,
            "availability": "available"
            if any("instock" in v.lower() for v in availability)
            else "unknown",
            "condition": next((v for v in condition if v), None),
            "seller_name": next((v for v in seller if v), None),
            "evidence": page_evidence,
            "page_type": assessment.kind,
            "verification_status": "verified",
            "price_evidence_level": "page_verified_price",
            "extraction_method": "direct_page_structured",
            "valid_for_benchmark": True,
            "rejection_reason": None,
            "notes": ["direct_page_not_checkout_verified"],
        }
    )
