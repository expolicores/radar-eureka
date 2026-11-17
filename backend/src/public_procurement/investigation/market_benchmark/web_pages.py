"""Classify search evidence only; never fetch product pages."""

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlsplit

from public_procurement.shared.text import normalize_text

from .schemas import ProductIdentity, SearchResult
from .urls import extract_mco_listing_id


@dataclass(frozen=True)
class PageAssessment:
    kind: str
    score: int
    commercial: bool


def classify_page(product: ProductIdentity, result: SearchResult) -> PageAssessment:
    parsed = urlsplit(str(result.url))
    host = parsed.hostname or ""
    path = normalize_text(unquote(parsed.path)).rstrip("/")
    title = normalize_text(result.title)
    text = normalize_text(result.title + " " + result.snippet)
    commercial = bool(
        re.search(
            r"\b(comprar|compra|precio|carrito|venta|en stock|disponible)\b|\$|\bCOP\b", text, re.I
        )
    )
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return PageAssessment("unknown", -100, False)
    if (
        host == "wikipedia.org"
        or host.endswith(".wikipedia.org")
        or re.search(
            r"/(?:blog|noticias|news|wiki|manuales?|support|soporte|reviews?)(?:/|$)|\.pdf$", path
        )
        or re.search(r"\b(manual|resena|review|guia de usuario)\b", title)
    ):
        return PageAssessment("editorial", -100, False)
    if not path or path in {"/co", "/co/home", "/home", "/colombia"}:
        return PageAssessment("home_page", -80, False)
    if re.search(r"/(?:brand|brands|marca|marcas)(?:/|$)", path):
        return PageAssessment("brand_page", -80, False)
    if re.search(
        r"/(?:category|categories|categoria|categorias|departamento|search|buscar|busca|listado|offer|ofertas)(?:/|$)",
        path,
    ) or set(parse_qs(parsed.query)) & {"q", "query", "search", "searchTerm"}:
        return PageAssessment("category_page", -70, False)
    if path.strip("/") == normalize_text(product.brand):
        return PageAssessment("brand_page", -80, False)
    if extract_mco_listing_id(str(result.url)):
        return PageAssessment("marketplace_listing", 60, commercial)
    slug = re.sub(r"[^a-z0-9]", "", path)
    references = [product.model, product.canonical_model]
    reference_url = any(re.sub(r"[^a-z0-9]", "", r.casefold()) in slug for r in references if r)
    product_path = bool(
        re.search(r"/(?:p|product|products|producto|productos)/[^/]+|/[^/]+/p$", path)
    )
    if reference_url or product_path or re.search(r"/p/MCO\d+$", path, re.I):
        return PageAssessment("product_page", 40 + (20 if reference_url else 0), commercial)
    if product.product_type and path.strip("/") in {
        normalize_text(product.product_type),
        normalize_text(product.product_type) + "s",
    }:
        return PageAssessment("category_page", -70, False)
    return PageAssessment("unknown", 0, commercial)
