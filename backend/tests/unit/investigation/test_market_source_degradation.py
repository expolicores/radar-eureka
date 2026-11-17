from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from public_procurement.investigation.market_benchmark.aggregation import extract_mco_listing_id
from public_procurement.investigation.market_benchmark.matching import match_identity, observe
from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
    MercadoLibreAdapter,
    MercadoLibreError,
    catalog_rank,
    structured_match,
)
from public_procurement.investigation.market_benchmark.query_expansion import expanded_queries
from public_procurement.investigation.market_benchmark.schemas import (
    ProductIdentity,
    PublicProduct,
    SearchResult,
)
from tests.market_pages import verified_benchmark as run_benchmark

NOW = datetime(2026, 11, 4, tzinfo=UTC)
TV = ProductIdentity(
    brand="Samsung",
    model="58U8000H",
    product_type="televisor",
    size="58 pulgadas",
    expected_domain_id="MCO-TELEVISIONS",
)
CATALOG_FIXTURE = {
    "id": "MCO80188666",
    "site_id": "MCO",
    "status": "active",
    "domain_id": "MCO-TELEVISIONS",
    "name": "Smart Tv Samsung 58 Crystal Uhd U8000h 4k Vision Ai 2026",
}


def test_expansion_uses_generic_context_and_is_bounded():
    queries = expanded_queries(TV)
    assert "Samsung 58 pulgadas 58U8000H" in queries
    assert "Samsung 58 pulgadas U8000H" in queries
    assert len(queries) == len(set(queries)) <= 4
    other = ProductIdentity(
        brand="Example", model="AB1234", product_type="disco", capacity="2 TB", product_family="AB"
    )
    assert "Example disco AB1234" in expanded_queries(other)
    assert "Example 2 TB AB1234" in expanded_queries(other)
    assert all(
        "Samsung" not in query and "televisor" not in query for query in expanded_queries(other)
    )
    assert match_identity(other, "Disco Example AB1234").level == "exact"


def test_real_catalog_reference_is_high_only_with_sufficient_context():
    match = structured_match(TV, CATALOG_FIXTURE)
    assert match.level == "high"
    assert match.reason == "size_model_family_and_domain"
    without_context = ProductIdentity(brand="Samsung", model="58U8000H")
    assert structured_match(without_context, CATALOG_FIXTURE).level not in {"exact", "high"}


def test_domain_ranking_rejects_accessory_even_with_matching_reference():
    accessory = {
        **CATALOG_FIXTURE,
        "name": "Samsung 58U8000H",
        "domain_id": "MCO-TV_REMOTE_CONTROLS",
    }
    good = structured_match(TV, CATALOG_FIXTURE)
    bad = structured_match(TV, accessory)
    assert catalog_rank(TV, CATALOG_FIXTURE, good) > catalog_rank(TV, accessory, bad)
    assert bad.level == "reject"
    assert bad.reason == "different_product_domain"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("name", "Samsung 65 pulgadas U8000H"),
        ("name", "Samsung 58 pulgadas U8200H"),
        ("name", "Samsung 58 pulgadas 58U8000"),
    ],
)
def test_context_never_hides_material_model_or_size_difference(key, value):
    assert structured_match(TV, {**CATALOG_FIXTURE, key: value}).level not in {"exact", "high"}


@pytest.mark.parametrize(
    ("field", "expected", "attribute", "observed"),
    [
        ("capacity", "256 GB", "STORAGE_CAPACITY", "128 GB"),
        ("dimensions", "10x20 cm", "DIMENSIONS", "10x30 cm"),
        ("size", "58 pulgadas", "SCREEN_SIZE", '65"'),
    ],
)
def test_explicit_measurement_conflicts(field, expected, attribute, observed):
    product = ProductIdentity(brand="Example", model="AB1234", **{field: expected})
    row = {"name": "Example AB1234", "attributes": [{"id": attribute, "value_name": observed}]}
    assert structured_match(product, row).level == "reject"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://articulo.mercadolibre.com.co/MCO-123456-tv-_JM", "MCO123456"),
        ("https://www.mercadolibre.com.co/MCO123456-tv", "MCO123456"),
        ("https://www.mercadolibre.com.co/tv/p/MCO80188666", None),
        ("https://www.mercadolibre.com.co/tv/p/MCO80188666?wid=MCO123456", "MCO123456"),
        ("https://evil.example/MCO-123456-tv", None),
        ("https://www.mercadolibre.com.ar/MCO-123456-tv", None),
        ("https://user:password@mercadolibre.com.co/MCO-123456-tv", None),
        ("https://[malformed", None),
    ],
)
def test_listing_id_extraction_not_catalog_id_or_other_domain(url, expected):
    assert extract_mco_listing_id(url) == expected


def public_purchase():
    return PublicProduct(
        brand="Samsung",
        model="58U8000H",
        public_process_identity="fixture",
        public_process_code="fixture",
        public_entity="Test",
        public_product_description="Fixture",
        public_unit_price=3000000,
        public_price_stage="contract",
        public_price_date=NOW,
        public_evidence_ref="fixture",
        public_document="fixture.pdf",
        public_page_reference="p.1",
        price_origin="explicit",
    )


def search_result(url, snippet="COP $2.000.000"):
    return SearchResult(
        title="TV Samsung 58U8000H",
        snippet=snippet,
        url=url,
        captured_at=NOW,
        query="fixture",
        search_provider="mock",
    )


@pytest.mark.parametrize(
    "failure",
    [
        MercadoLibreError("token_expired_or_invalid", 401),
        MercadoLibreError("access_forbidden", 403),
        MercadoLibreError("rate_limited", 429),
        MercadoLibreError("provider_http_error", 500),
        MercadoLibreError("timeout"),
        MercadoLibreError("invalid_response"),
    ],
)
def test_web_benchmark_and_eligibility_survive_ml_errors(failure):
    search = Mock()
    search.search.return_value = [
        search_result(f"https://retailer{i}.example/product/58u8000h") for i in range(3)
    ]
    api = Mock()
    api.get.side_effect = failure
    report = run_benchmark(
        public_purchase(), search, NOW, marketplace_adapter=MercadoLibreAdapter(api)
    )
    assert report["benchmark"]["valid_observations_count"] == 3
    assert report["benchmark"]["median_price"] == "2000000"
    assert report["signal"] is not None  # existing signal policy, no ML dependency
    assert report["status"] == "completed_with_warnings"
    assert report["source_degradations"][0]["source"] == "mercadolibre"
    assert search.search.call_count == report["web_discovery"]["queries_executed"]
    api.get.assert_called_once()


@pytest.mark.parametrize("payload", [{"results": []}, {"results": "malformed"}, []])
def test_empty_or_malformed_catalog_not_blocking(payload):
    api = Mock()
    api.get.return_value = payload
    search = Mock()
    search.search.return_value = [search_result("https://retailer.example/product/58u8000h")]
    report = run_benchmark(TV, search, NOW, marketplace_adapter=MercadoLibreAdapter(api))
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["source_degradations"]


def test_failed_item_enrichment_preserves_sufficient_web_evidence():
    api = Mock()
    api.get.side_effect = MercadoLibreError("access_forbidden", 403)
    search = Mock()
    search.search.return_value = [
        search_result("https://articulo.mercadolibre.com.co/MCO-123456-tv")
    ]
    report = run_benchmark(
        TV, search, NOW, marketplace_adapter=MercadoLibreAdapter(api, enable_catalog=False)
    )
    assert api.get.call_args.args[0] == "/items/MCO123456"
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["benchmark"]["observations"][0]["source_type"] == "web_search"


@pytest.mark.parametrize(
    ("url", "kind"),
    [
        ("https://articulo.mercadolibre.com.co/MCO-123456-tv", "marketplace_web"),
        ("https://www.samsung.com/co/tv", "manufacturer_web"),
        ("https://www.exito.com/tv", "retailer_web"),
        ("https://example.org/tv", "other_web"),
    ],
)
def test_web_source_categories(url, kind):
    assert observe(TV, search_result(url)).web_source_kind == kind


def test_catalog_is_never_a_listing_or_automatic_price_observation():
    api = Mock()
    api.get.side_effect = lambda path, params=None: (
        {"results": [CATALOG_FIXTURE]} if path == "/products/search" else CATALOG_FIXTURE
    )
    result = MercadoLibreAdapter(api).collect(TV)
    assert result.diagnostics["catalog_product_id"] == "MCO80188666"
    assert result.observations == []
    assert all(
        call.args[0] in {"/products/search", "/products/MCO80188666"}
        for call in api.get.call_args_list
    )


def test_unexpected_optional_source_error_is_sanitized_and_nonblocking():
    adapter = Mock()
    adapter.collect.side_effect = RuntimeError("secret must not appear")
    search = Mock()
    search.search.return_value = [search_result("https://retailer.example/product/58u8000h")]
    report = run_benchmark(TV, search, NOW, marketplace_adapter=adapter)
    assert report["benchmark"]["valid_observations_count"] == 1
    assert "secret must not appear" not in str(report)


def test_forbidden_site_search_cannot_be_requested():
    from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
        MercadoLibreHttp,
        MercadoLibreSettings,
    )

    fake_token = "fixture"
    config = MercadoLibreSettings(_env_file=None, mercadolibre_access_token=fake_token)
    http = MercadoLibreHttp(config)
    with pytest.raises(MercadoLibreError, match="endpoint_not_allowed"):
        http.get("/sites/MCO/search", {"q": "fixture"})
    assert http.requests == []


@pytest.mark.parametrize(
    "payload",
    [
        {"bad": "shape"},
        {
            "id": "MCO123456",
            "title": "TV Samsung 58U8000H",
            "price": 2000000,
            "permalink": "https://articulo.mercadolibre.com.co/MCO-123456-tv",
        },
    ],
)
def test_malformed_item_preserves_web_observation(payload):
    api = Mock()
    api.get.return_value = payload
    search = Mock()
    search.search.return_value = [
        search_result("https://articulo.mercadolibre.com.co/MCO-123456-tv")
    ]
    report = run_benchmark(
        TV, search, NOW, marketplace_adapter=MercadoLibreAdapter(api, enable_catalog=False)
    )
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["source_degradations"][0]["code"] == "invalid_item_response"


def test_cli_combined_returns_normally_after_source_degradation(tmp_path, monkeypatch, capsys):
    import importlib.util
    import json
    import sys
    from pathlib import Path

    from public_procurement.investigation.market_benchmark import mercadolibre_adapter as ml

    path = Path(__file__).resolve().parents[3] / "scripts" / "eureka_market_benchmark.py"
    spec = importlib.util.spec_from_file_location("market_cli_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    search = Mock()
    search.search.return_value = [
        search_result("https://articulo.mercadolibre.com.co/MCO-123456-tv")
    ]
    scout = Mock()
    from public_procurement.investigation.market_benchmark.matching import observe

    scout.scout.return_value = [observe(TV, search.search.return_value[0])]
    monkeypatch.setattr(module, "FoundryMarketPriceScout", lambda: scout)
    from tests.market_pages import FixturePageVerifier

    monkeypatch.setattr(module, "HttpMarketPageVerifier", FixturePageVerifier)
    monkeypatch.setattr(ml, "MercadoLibreSettings", Mock())
    http = Mock()
    http.requests = []
    http.get.side_effect = MercadoLibreError("access_forbidden", 403)
    monkeypatch.setattr(ml, "MercadoLibreHttp", lambda _: http)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "market",
            "--brand",
            "Samsung",
            "--model",
            "58U8000H",
            "--source",
            "auto",
            "--output-directory",
            str(tmp_path),
        ],
    )
    from public_procurement.investigation.market_benchmark.ports import ShoppingDiscoveryResult

    shopping = Mock()
    shopping.discover.return_value = ShoppingDiscoveryResult(diagnostics={"warnings": []})
    monkeypatch.setattr(module, "SerpApiShoppingAdapter", lambda _: shopping)
    module.main()  # no SystemExit due to optional-source error
    report = json.loads((tmp_path / "market_benchmark.json").read_text(encoding="utf8"))
    assert report["status"] == "completed_with_warnings"
    assert report["benchmark"]["valid_observations_count"] == 1
    assert "access_forbidden" in capsys.readouterr().out
