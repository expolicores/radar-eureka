"""Conservative identity and price extraction from search evidence only."""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from urllib.parse import urlsplit

from public_procurement.shared.text import normalize_text

from .query_expansion import model_family
from .schemas import MarketObservation, ProductIdentity, SearchResult
from .urls import canonical_url as canonical_url
from .web_pages import classify_page


@dataclass(frozen=True)
class IdentityMatch:
    level: Literal["exact", "high", "partial", "reject"]
    reason: str
    brand: str | None
    model: str | None


def match_identity(product: ProductIdentity, title: str) -> IdentityMatch:
    title = normalize_text(title)
    brand = (
        product.brand
        if re.search(r"\b" + re.escape(normalize_text(product.brand)) + r"\b", title)
        else None
    )
    tokens = re.findall(r"\b[a-z]*\d{2}[a-z]+\d+[a-z0-9]*\b", title)
    wanted = product.model.lower()
    canonical = (product.canonical_model or "").casefold()
    if canonical:
        compatibility = match_identity(
            product.model_copy(update={"canonical_model": None}), product.brand + " " + canonical
        )
        if compatibility.level not in {"exact", "high"} and not re.fullmatch(
            r"[a-z]{0,3}" + re.escape(wanted) + r"[a-z]{0,4}", canonical
        ):
            canonical = ""
    model = (
        wanted if re.search(r"(?<![a-z0-9])" + re.escape(wanted) + r"(?![a-z0-9])", title) else None
    )
    level: Literal["exact", "high", "partial", "reject"] = "partial"
    reason = "model_not_confirmed"
    if brand and model:
        level, reason = "exact", "same_brand_and_exact_model"
    elif (
        brand
        and canonical
        and re.search(r"(?<![a-z0-9])" + re.escape(canonical) + r"(?![a-z0-9])", title)
    ):
        model = canonical
        level, reason = "high", "compatible_canonical_reference"
    elif (
        brand
        and canonical
        and product.size
        and model_family(product)
        and re.search(r"\b" + re.escape(model_family(product) or "") + r"\b", title)
        and (measure := re.match(r"(\d+(?:[.,]\d+)?)", product.size))
        and re.search(r"\b" + re.escape(measure[1]) + r"\b", title)
    ):
        model = wanted
        level, reason = "high", "canonical_family_and_explicit_size"
    elif (
        brand
        and product.brand.lower() == "samsung"
        and any(t in {"un" + wanted + "kxzl", "un" + wanted + "k", "un" + wanted} for t in tokens)
    ):
        model = next(t for t in tokens if t.startswith("un" + wanted))
        level, reason = "high", "samsung_regional_prefix_suffix"
    elif tokens:
        level, reason = "reject", "different_model"
    if model and any(t not in {model, wanted, canonical} for t in tokens):
        level, reason = "reject", "conflicting_models_in_title"
    family = model_family(product)
    family_prefix = re.match(r"[a-z]+", family or "")
    if family_prefix:
        relatives = re.findall(r"\b" + re.escape(family_prefix[0]) + r"\d{3,}[a-z0-9]*\b", title)
        if any(ref not in {family, wanted, canonical, model} for ref in relatives):
            level, reason = "reject", "conflicting_models_in_title" if model else "different_model"
    size = re.match(r"(?:UN)?(\d{2})", product.model)
    if level == "partial" and not (
        brand
        and re.search(r"\b(tv|televisor|television|smart)\b", title)
        and size
        and re.search(r"\b" + size[1] + r"\b", title)
    ):
        level, reason = "reject", "irrelevant_or_generic_result"
    if size and re.search(r"\b(\d{2})\s*(?:pulgadas|pulg|inches|[\"″])", title):
        sizes = re.findall(r"\b(\d{2})\s*(?:pulgadas|pulg|inches|[\"″])", title)
        if any(s != size[1] for s in sizes):
            level, reason = "reject", "different_size"
    if product.capacity:
        capacity = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*([A-Za-z]+)\s*", product.capacity)
        if capacity:
            observed = re.findall(
                r"\b(\d+(?:[.,]\d+)?)\s*" + re.escape(capacity[2]) + r"\b", title, re.I
            )
            if any(
                Decimal(n.replace(",", ".")) != Decimal(capacity[1].replace(",", "."))
                for n in observed
            ):
                level, reason = "reject", "different_capacity"
    for pattern, rejection in (
        (
            r"\b(usado|reacondicionado|reacondicionada|refurbished|renewed|open box)\b",
            "used_or_refurbished",
        ),
        (r"\b(bundle|combo|paquete|barra de sonido|soporte incluido)\b", "non_comparable_bundle"),
        (
            r"\b(control remoto|remote control|repuesto|reparacion|accesorio|"
            r"pantalla de reemplazo|pantalla para|panel para|display para|replacement screen)\b",
            "accessory_or_service",
        ),
    ):
        if re.search(pattern, title):
            level, reason = "reject", rejection
    return IdentityMatch(level, reason, brand, model.upper() if model else None)


def observe(product: ProductIdentity, result: SearchResult) -> MarketObservation:
    match = match_identity(product, result.title + " " + result.snippet)
    # Snippets may confirm condition/size, but the product reference must be in the title.
    title_match = match_identity(product, result.title)
    if match.level != "reject":
        match = title_match
    level, reason, brand, model = match.level, match.reason, match.brand, match.model
    text = normalize_text(result.title + " " + result.snippet)
    notes = []
    # A snippet with installments cannot establish an unambiguous comparable total.
    financing = bool(re.search(r"\b(cuotas?|mensual|mensuales|al mes|financiacion)\b", text))
    raw_evidence = result.title + " " + result.snippet
    values = re.findall(
        r"(?:COP\s*\$?|\$)\s*((?:\d{1,3}(?:[.,]\d{3})+|\d{4,9})(?:[.,]00)?)(?!\d)",
        raw_evidence,
        re.IGNORECASE,
    )
    prices = {Decimal(re.sub(r"[.,]00$", "", v).replace(".", "").replace(",", "")) for v in values}
    price = next(iter(prices)) if len(prices) == 1 else None
    if financing:
        price = None
        notes.append("installments_not_total_price")
    if len(prices) > 1:
        notes.append("ambiguous_multiple_prices")
    if price is None or price <= 0:
        price = None
        notes.append("no_unambiguous_total_price")
    if re.search(r"USD|US\$|EUR|MXN", raw_evidence, re.IGNORECASE):
        price = None
        notes.append("currency_not_cop")
    host = urlsplit(str(result.url)).hostname or ""
    colombian_domain = host.endswith((".co", ".com.co")) or host.removeprefix("www.") in {
        "exito.com",
        "alkosto.com",
        "ktronix.com",
        "tiendasjumbo.co",
        "olimpica.com",
    }
    if price is not None and not re.search(r"\bCOP\b", raw_evidence, re.IGNORECASE):
        if colombian_domain:
            notes.append("currency_inferred_from_colombian_retailer")
        else:
            price = None
            notes.append("currency_not_confirmed")
    availability: Literal["available", "unavailable", "unknown"] = "unknown"
    if re.search(r"agotado|sin stock|no disponible", text):
        availability = "unavailable"
    elif re.search(r"en stock|disponible para compra", text):
        availability = "available"
    if availability == "unknown":
        notes.append("availability_not_verified")
    notes.append("search_snippet_not_checkout_verified")
    web_kind: Literal["retailer_web", "marketplace_web", "manufacturer_web", "other_web"] = (
        "other_web"
    )
    if host == "mercadolibre.com.co" or host.endswith(".mercadolibre.com.co"):
        web_kind = "marketplace_web"
    elif normalize_text(product.brand).replace(" ", "") in host.split("."):
        web_kind = "manufacturer_web"
    elif colombian_domain or re.search(r"\b(comprar|carrito|tienda|en stock)\b", text):
        web_kind = "retailer_web"
    page = classify_page(product, result)
    concrete = page.kind in {"product_page", "marketplace_listing"}
    if not concrete:
        notes.append("candidate_page_not_concrete")
    if not page.commercial:
        notes.append("commercial_context_not_observed")
    score = (
        page.score
        + {"exact": 40, "high": 30, "partial": 10, "reject": -70}[level]
        + (10 if price is not None else 0)
        + (5 if availability == "available" else 0)
        + (5 if web_kind in {"retailer_web", "marketplace_web"} else 0)
    )
    return MarketObservation(
        retailer=urlsplit(str(result.url)).hostname or "unknown",
        market_product_title=result.title,
        brand=brand,
        model=model.upper() if model else None,
        price=price,
        url=result.url,
        captured_at=result.captured_at,
        match_level=level,
        match_reason=reason,
        availability=availability,
        promotion_detected=bool(re.search(r"oferta|promocion|descuento", text)),
        notes=notes,
        evidence=result,
        web_source_kind=web_kind,
        page_type=page.kind,
        discovery_score=score,
        discovered_queries=[result.query],
        valid_for_benchmark=level in {"exact", "high"}
        and price is not None
        and availability != "unavailable"
        and concrete
        and page.commercial,
    )
