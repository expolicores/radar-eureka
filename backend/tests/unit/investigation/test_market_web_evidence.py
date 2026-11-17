from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from public_procurement.investigation.market_benchmark.aggregation import aggregate
from public_procurement.investigation.market_benchmark.matching import observe
from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
    MercadoLibreAdapter,
    MercadoLibreError,
)
from public_procurement.investigation.market_benchmark.schemas import ProductIdentity, SearchResult
from public_procurement.investigation.market_benchmark.web_discovery import discover_web
from public_procurement.investigation.market_benchmark.web_pages import classify_page
from tests.market_pages import verified_benchmark as run_benchmark

NOW = datetime(2026, 11, 4, tzinfo=UTC)
PRODUCT = ProductIdentity(
    brand="Samsung",
    model="58U8000H",
    canonical_model="UN58U8000H",
    product_type="televisor",
    size="58 pulgadas",
    expected_domain_id="MCO-TELEVISIONS",
)


def result(
    url="https://www.exito.com/tv-samsung-un58u8000h/p",
    title="TV Samsung UN58U8000H 58 pulgadas",
    snippet="Precio COP $2.000.000 disponible para compra",
):
    return SearchResult(
        title=title,
        snippet=snippet,
        url=url,
        query="fixture",
        captured_at=NOW,
        search_provider="mock",
    )


@pytest.mark.parametrize(
    ("url", "kind"),
    [
        ("https://www.samsung.com/co/", "home_page"),
        ("https://www.falabella.com.co/falabella-co/brand/SAMSUNG", "brand_page"),
        ("https://www.falabella.com.co/category/televisores", "category_page"),
        ("https://www.exito.com/search?q=UN58U8000H", "category_page"),
        ("https://es.wikipedia.org/wiki/Samsung", "editorial"),
        ("https://example.co/blog/samsung-un58u8000h", "editorial"),
        ("https://www.samsung.com/support/manual/un58u8000h", "editorial"),
        ("https://example.co/manual-un58u8000h.pdf", "editorial"),
        ("https://www.exito.com/tv-un58u8000h/p", "product_page"),
        ("https://www.alkosto.com/p/123456", "product_page"),
        ("https://articulo.mercadolibre.com.co/MCO-123456-tv-_JM", "marketplace_listing"),
        ("https://www.mercadolibre.com.co/tv/p/MCO80188666", "product_page"),
        ("https://example.co/unknown", "unknown"),
    ],
)
def test_page_types_and_gating_even_when_title_and_price_look_good(url, kind):
    row = result(url=url)
    assert classify_page(PRODUCT, row).kind == kind
    assert observe(PRODUCT, row).valid_for_benchmark is (
        kind in {"product_page", "marketplace_listing"}
    )


@pytest.mark.parametrize(
    ("title", "level"),
    [
        ("TV Samsung 58U8000H 58 pulgadas", "exact"),
        ("TV Samsung UN58U8000H 58 pulgadas", "high"),
        ("TV Samsung U8000H 58 pulgadas", "high"),
        ("TV Samsung Smart 58 pulgadas", "partial"),
        ("TV Samsung UN58TU7000 58 pulgadas", "reject"),
        ("TV Samsung U8500 58 pulgadas", "reject"),
        ("TV Samsung UN58U8000H 65 pulgadas", "reject"),
        ("Control remoto Samsung UN58U8000H", "reject"),
        ("Pantalla para Samsung UN58U8000H", "reject"),
    ],
)
def test_web_matching_levels_and_conflicts(title, level):
    observation = observe(PRODUCT, result(title=title))
    assert observation.match_level == level
    assert observation.valid_for_benchmark is (level in {"exact", "high"})


def test_observable_price_and_commercial_context_are_required():
    assert not observe(PRODUCT, result(snippet="Ficha del fabricante")).valid_for_benchmark
    assert observe(
        PRODUCT, result(title="TV Samsung UN58U8000H COP $2.000.000", snippet="Comprar")
    ).valid_for_benchmark
    assert not observe(PRODUCT, result(snippet="12 cuotas de $166.666")).valid_for_benchmark


def test_product_pages_rank_above_generals_and_wrong_products():
    search = Mock()
    search.search.return_value = [
        result(url="https://www.exito.com/"),
        result(),
        result(title="TV Samsung UN65U8000H 65 pulgadas"),
    ]
    discovery = discover_web(PRODUCT, search)
    assert discovery.observations[0].valid_for_benchmark
    assert discovery.observations[0].page_type == "product_page"
    assert discovery.diagnostics["queries_executed"] == 1
    assert search.search.call_count == 1


def test_same_retailer_model_price_dedupe_preserves_provenance():
    search = Mock()
    search.search.return_value = [
        result(),
        result(url="https://www.exito.com/product/UN58U8000H?utm_source=x"),
    ]
    discovery = discover_web(PRODUCT, search)
    from tests.market_pages import FixturePageVerifier

    benchmark = aggregate(
        PRODUCT, [FixturePageVerifier().verify(PRODUCT, o) for o in discovery.observations], NOW
    )
    assert benchmark.valid_observations_count == 1
    assert len(benchmark.duplicates) == 1
    assert len(benchmark.observations[0].discovered_queries) == 1
    assert all(o.duplicate_of for o in benchmark.duplicates)


def test_empty_search_is_insufficient_not_exception():
    search = Mock()
    search.search.return_value = []
    report = run_benchmark(PRODUCT, search)
    assert report["benchmark"]["benchmark_status"] == "insufficient_market_evidence"
    assert report["web_discovery"]["source_status"] == "empty"


def test_canonical_catalog_context_is_used_before_web_without_guessing_prices():
    product = PRODUCT.model_copy(update={"canonical_model": None})
    api = Mock()
    api.requests = []
    detail = {
        "id": "MCO80188666",
        "name": "Samsung UN58U8000H 58 pulgadas",
        "status": "active",
        "domain_id": "MCO-TELEVISIONS",
        "attributes": [
            {"id": "BRAND", "value_name": "Samsung"},
            {"id": "MODEL", "value_name": "UN58U8000H"},
        ],
    }
    api.get.side_effect = lambda path, params=None: (
        {"results": [detail]} if path == "/products/search" else detail
    )
    search = Mock()
    search.search.return_value = []
    report = run_benchmark(product, search, marketplace_adapter=MercadoLibreAdapter(api))
    assert '"UN58U8000H"' in search.search.call_args_list[0].args[0]
    assert report["web_discovery"]["catalog_product_id_used"] == "MCO80188666"
    assert report["product"]["model"] == "58U8000H"
    assert report["benchmark"]["valid_observations_count"] == 0


def test_web_listing_is_enriched_once_and_api_is_preferred():
    api = Mock()
    api.requests = []
    api.get.return_value = {
        "id": "MCO123456",
        "site_id": "MCO",
        "title": "Samsung 58U8000H",
        "price": 1900000,
        "currency_id": "COP",
        "condition": "new",
        "status": "active",
        "seller_id": 1,
        "permalink": "https://articulo.mercadolibre.com.co/MCO-123456-tv",
        "available_quantity": 1,
    }
    search = Mock()
    search.search.return_value = [result(url="https://articulo.mercadolibre.com.co/MCO-123456-tv")]
    report = run_benchmark(
        PRODUCT,
        search,
        marketplace_adapter=MercadoLibreAdapter(api, enable_catalog=False),
    )
    api.get.assert_called_once_with("/items/MCO123456")
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["benchmark"]["observations"][0]["source_type"] == "marketplace_api"
    assert report["benchmark"]["median_price"] == "1900000"


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_failed_enrichment_keeps_valid_web_price(status):
    api = Mock()
    api.requests = []
    api.get.side_effect = MercadoLibreError("http_failure", status)
    search = Mock()
    search.search.return_value = [result(url="https://articulo.mercadolibre.com.co/MCO-123456-tv")]
    report = run_benchmark(
        PRODUCT,
        search,
        marketplace_adapter=MercadoLibreAdapter(api, enable_catalog=False),
    )
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["benchmark"]["median_price"] == "2000000"
    assert report["source_degradations"]


def test_optional_web_error_has_no_retry_and_does_not_abort():
    search = Mock()
    search.search.side_effect = TimeoutError("private details must not appear")
    report = run_benchmark(PRODUCT, search)
    assert report["web_discovery"]["queries_planned"] == 1
    assert report["web_discovery"]["queries_executed"] == 1
    assert report["benchmark"]["valid_observations_count"] == 0
    assert "private details" not in str(report)


def test_malformed_canonical_attributes_do_not_block_web():
    from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
        MercadoLibreResult,
    )

    batch = MercadoLibreResult()
    batch.diagnostics.update(
        catalog_product_id="MCO80188666",
        catalog_details=[
            {
                "id": "MCO80188666",
                "match_level": "high",
                "attributes": [None, 1, {"id": "MODEL", "value_name": []}],
            }
        ],
    )
    adapter = Mock()
    adapter.collect.return_value = batch
    search = Mock()
    search.search.return_value = [result()]
    report = run_benchmark(
        PRODUCT.model_copy(update={"canonical_model": None}),
        search,
        marketplace_adapter=adapter,
    )
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["web_discovery"]["canonical_model_used"] is None
