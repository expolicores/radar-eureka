import json
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock
from urllib.error import HTTPError

import pytest

from public_procurement.investigation.market_benchmark.aggregation import aggregate
from public_procurement.investigation.market_benchmark.matching import observe
from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
    MercadoLibreAdapter,
    MercadoLibreError,
    MercadoLibreHttp,
    MercadoLibreSettings,
    NoRedirect,
    item_observation,
    status_error,
)
from public_procurement.investigation.market_benchmark.schemas import (
    ProductIdentity,
    PublicOffer,
    SearchResult,
)
from tests.market_pages import verified_mercadolibre_benchmark as run_mercadolibre_benchmark

NOW = datetime(2026, 11, 4, tzinfo=UTC)
PRODUCT = ProductIdentity(brand="Samsung", model="58U8000H")


def item(i=1, seller=1, **overrides):
    return {
        "id": f"MCO{i}",
        "site_id": "MCO",
        "title": "TV Samsung 58U8000H 58 pulgadas",
        "price": 2000000,
        "currency_id": "COP",
        "condition": "new",
        "status": "active",
        "seller_id": seller,
        "permalink": f"https://articulo.mercadolibre.com.co/MCO-{i}-tv",
        "available_quantity": 50,
        "catalog_product_id": "MCO100",
        "official_store_id": 99,
        "attributes": [
            {"id": "BRAND", "value_name": "Samsung"},
            {"id": "MODEL", "value_name": "58U8000H"},
        ],
        "buying_mode": "buy_it_now",
        **overrides,
    }


def catalog(cid="MCO100", **overrides):
    return {
        "id": cid,
        "site_id": "MCO",
        "name": "Samsung 58U8000H",
        "status": "active",
        "attributes": item()["attributes"],
        "domain_id": "MCO-TELEVISIONS",
        **overrides,
    }


class FakeApi:
    def __init__(self, rows=None, products=None, details=None):
        self.rows = rows if rows is not None else [item()]
        self.products = products if products is not None else [catalog()]
        self.details = details or {"MCO100": catalog()}
        self.requests = []

    def get(self, path, params=None):
        self.requests.append({"endpoint": path, "params": params})
        if path == "/products/search":
            return {"results": self.products}
        if path.startswith("/products/"):
            value = self.details[path.split("/")[-1]]
            if isinstance(value, Exception):
                raise value
            return value
        if path.startswith("/items/"):
            iid = path.rsplit("/", 1)[-1]
            return next(r for r in self.rows if r["id"] == iid)
        raise AssertionError(path)


def test_mco_catalog_and_concrete_item_only():
    api = FakeApi()
    result = MercadoLibreAdapter(api).collect(PRODUCT, listing_ids=["MCO1"])
    assert not result.diagnostics["errors"]
    assert result.diagnostics["catalog_product_id"] == "MCO100"
    assert api.requests[0]["params"]["site_id"] == "MCO"
    assert [c["endpoint"] for c in api.requests] == [
        "/products/search",
        "/products/MCO100",
        "/items/MCO1",
    ]
    assert len(result.observations) == 1


def test_missing_auth_does_not_make_http_call(monkeypatch):
    opener = Mock()
    monkeypatch.setattr(
        "public_procurement.investigation.market_benchmark.mercadolibre_adapter.build_opener",
        opener,
    )
    http = MercadoLibreHttp(MercadoLibreSettings(_env_file=None, mercadolibre_access_token=None))
    report = run_mercadolibre_benchmark(PRODUCT, MercadoLibreAdapter(http))
    assert report["status"] == "completed_with_warnings"
    assert report["errors"][0]["code"] == "missing_auth_configuration"
    assert report["mercadolibre"]["request_count"] == 0
    assert report["benchmark"]["valid_observations_count"] == 0
    assert report["signal"] is None
    opener.assert_not_called()


def test_wrong_catalog_not_chosen():
    wrong = catalog(name="Samsung 65U8000H", attributes=[{"id": "MODEL", "value_name": "65U8000H"}])
    api = FakeApi(products=[wrong])
    result = MercadoLibreAdapter(api).collect(PRODUCT)
    assert result.diagnostics["catalog_product_id"] is None
    assert result.diagnostics["catalog_candidates"][0]["match_level"] == "reject"
    assert not any(c["endpoint"] == "/products/MCO100" for c in api.requests)


def test_ambiguous_catalog_not_first_result():
    products = [catalog("MCO100"), catalog("MCO101")]
    result = MercadoLibreAdapter(
        FakeApi(products=products, details={p["id"]: p for p in products})
    ).collect(PRODUCT)
    assert result.diagnostics["catalog_product_id"] is None
    assert result.diagnostics["catalog_selection_reason"] == "ambiguous_or_unvalidated_catalog"


def test_detail_contradiction_not_ignored():
    api = FakeApi(
        details={"MCO100": catalog(attributes=[{"id": "MODEL", "value_name": "65U8000H"}])}
    )
    result = MercadoLibreAdapter(api).collect(PRODUCT)
    assert result.diagnostics["catalog_product_id"] is None


@pytest.mark.parametrize(
    ("overrides", "valid", "reason"),
    [
        ({}, True, "same_brand_and_exact_model"),
        (
            {"title": "TV Samsung UN58U8000HKXZL", "attributes": []},
            True,
            "samsung_regional_prefix_suffix",
        ),
        ({"title": "TV Samsung 65U8000H", "attributes": []}, False, "different_model"),
        ({"title": "TV Samsung U8200H", "attributes": []}, False, "irrelevant_or_generic_result"),
        ({"title": "TV Samsung 58U8000", "attributes": []}, False, "different_model"),
        ({"title": "TV Samsung 58U8000H 55 pulgadas"}, False, "different_size"),
        ({"title": "Control remoto Samsung 58U8000H"}, False, "accessory_or_service"),
        ({"condition": "used"}, False, "condition_not_new_or_unknown"),
        ({"condition": None}, False, "condition_not_new_or_unknown"),
        ({"condition": "refurbished"}, False, "condition_not_new_or_unknown"),
        ({"title": "Samsung 58U8000H Open box"}, False, "used_or_refurbished"),
        ({"status": "paused"}, False, "listing_not_active"),
        ({"status": "closed"}, False, "listing_not_active"),
        ({"available_quantity": 0}, False, "listing_unavailable"),
        ({"currency_id": "USD"}, False, "currency_not_cop"),
        ({"site_id": "MLA"}, False, "different_or_unknown_site"),
        ({"price": None}, False, "invalid_listing_total_price"),
        ({"price": "NaN"}, False, "invalid_listing_total_price"),
        ({"price": True}, False, "invalid_listing_total_price"),
        ({"buying_mode": "auction"}, False, "not_fixed_total_price"),
    ],
)
def test_item_rules(overrides, valid, reason):
    observation = item_observation(PRODUCT, item(**overrides), NOW)
    assert observation is not None
    assert observation.valid_for_benchmark is valid
    assert observation.match_reason == reason


def test_price_is_total_not_installment_shipping_or_quantity():
    row = item(
        price=2000000,
        installments={"quantity": 12, "amount": 166666},
        shipping={"cost": 99999},
        available_quantity=50,
        original_price=2500000,
    )
    o = item_observation(PRODUCT, row, NOW)
    assert o.price == Decimal(2000000)
    assert o.available_quantity_reference == 50
    assert o.availability == "available"
    assert "available_quantity_is_referential_not_exact_stock" in o.notes
    assert o.promotion_detected
    assert o.source_type == "marketplace_api"
    assert o.evidence.response["price"] == 2000000
    assert o.evidence.site_id == "MCO"


def test_seller_and_listing_duplicates_preserved_as_evidence():
    observations = [
        item_observation(PRODUCT, r, NOW)
        for r in [item(1, 1), item(1, 1), item(2, 1, price=2100000), item(3, 2)]
    ]
    benchmark = aggregate(PRODUCT, observations, NOW)
    assert benchmark.valid_observations_count == 2
    assert benchmark.distinct_sellers_count == 2
    assert benchmark.retailers_count == 1
    assert len(benchmark.duplicates) == 2
    assert all(o.duplicate_of and not o.valid_for_benchmark for o in benchmark.duplicates)


def web_observation(url="https://retailer.example/product/58u8000h"):
    return observe(
        PRODUCT,
        SearchResult(
            title="TV Samsung 58U8000H",
            snippet="COP $2.000.000",
            url=url,
            captured_at=NOW,
            query="Samsung 58U8000H",
            search_provider="mock",
        ),
    )


def test_web_and_api_same_listing_count_once():
    api = item_observation(PRODUCT, item(123, 1), NOW)
    web = web_observation("https://articulo.mercadolibre.com.co/MCO-123-tv?utm_source=search")
    benchmark = aggregate(PRODUCT, [web, api], NOW)
    assert benchmark.valid_observations_count == 1
    assert benchmark.observations[0].source_type == "marketplace_api"
    assert len(benchmark.duplicates) == 1


def test_marketplace_concentration_is_not_diversity():
    observations = [item_observation(PRODUCT, item(i, i), NOW) for i in (1, 2, 3)]
    b = aggregate(PRODUCT, observations, NOW)
    assert b.valid_observations_count == 3
    assert b.retailers_count == b.independent_sources_count == 1
    assert b.distinct_sellers_count == 3
    assert b.evidence_sufficiency == "marketplace_concentrated_evidence"
    assert b.median_price == 2000000


def test_diverse_evidence_and_insufficient():
    rows = [item_observation(PRODUCT, item(i, i), NOW) for i in (1, 2)]
    assert aggregate(PRODUCT, rows, NOW).evidence_sufficiency == "insufficient_market_evidence"
    from tests.market_pages import FixturePageVerifier

    page = FixturePageVerifier().verify(PRODUCT, web_observation())
    b = aggregate(PRODUCT, [*rows, page], NOW)
    assert b.evidence_sufficiency == "sufficient_diverse_market_evidence"
    assert b.independent_sources_count == 2


@pytest.mark.parametrize(
    ("status", "code"),
    [(401, "token_expired_or_invalid"), (403, "access_forbidden"), (429, "rate_limited")],
)
def test_errors_abort_without_retries_or_leaking_token(monkeypatch, caplog, status, code):
    opener = Mock()
    secret = "secret-access-token-not-for-output"
    opener.open.side_effect = HTTPError(
        "https://api.mercadolibre.com/products/search", status, secret, None, None
    )
    monkeypatch.setattr(
        "public_procurement.investigation.market_benchmark.mercadolibre_adapter.build_opener",
        Mock(return_value=opener),
    )
    config = MercadoLibreSettings(_env_file=None, mercadolibre_access_token=secret)
    report = run_mercadolibre_benchmark(PRODUCT, MercadoLibreAdapter(MercadoLibreHttp(config)))
    assert report["errors"] == [{"code": code, "http_status": status, "stage": "catalog"}]
    assert secret not in json.dumps(report) + str(config) + caplog.text
    opener.open.assert_called_once()


def test_timeout_no_retry(monkeypatch):
    opener = Mock()
    opener.open.side_effect = TimeoutError()
    monkeypatch.setattr(
        "public_procurement.investigation.market_benchmark.mercadolibre_adapter.build_opener",
        Mock(return_value=opener),
    )
    fake_token = "fixture-token"
    config = MercadoLibreSettings(_env_file=None, mercadolibre_access_token=fake_token)
    r = MercadoLibreAdapter(MercadoLibreHttp(config)).collect(PRODUCT)
    assert r.diagnostics["errors"][0]["code"] == "timeout"
    opener.open.assert_called_once()


def test_not_found_catalog_is_explicit_and_not_selected():
    result = MercadoLibreAdapter(FakeApi(details={"MCO100": status_error(404)})).collect(PRODUCT)
    assert result.diagnostics["catalog_product_id"] is None
    assert result.diagnostics["errors"][0]["code"] == "catalog_product_not_found"


def test_redirect_never_forwards_credentials():
    with pytest.raises(MercadoLibreError, match="unexpected_redirect"):
        NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://example.com")


def test_documented_offer_never_generates_final_signal():
    offer = PublicOffer(
        brand="Samsung",
        model="58U8000H",
        public_process_identity="CO1.REQ.11253117",
        public_process_code="MC-070-2026",
        public_entity="Universidad del Atlantico",
        public_product_description="TV Samsung 58U8000H",
        public_unit_price="3767123",
        public_evidence_ref="document:878001221",
        public_document="OFERTA ECONOMICA MC-070-2026.pdf",
        public_page_reference="PDF p.339",
        price_origin="explicit",
        price_tax_basis="excludes_vat",
        document_heading_process_code="MC-028-2026",
    )
    rows = [item(i, i) for i in (1, 2, 3)]
    report = run_mercadolibre_benchmark(
        offer, MercadoLibreAdapter(FakeApi(rows=rows)), listing_ids=[r["id"] for r in rows]
    )
    assert report["benchmark"]["median_price"] == "2000000"
    assert report["comparison"] is None
    assert report["signal"] is None
    assert report["preliminary_comparison"]["status"] == "preliminary_not_confirmed_purchase"


def test_item_404_keeps_listing_error_visible():
    class MissingApi(FakeApi):
        def get(self, path, params=None):
            if path == "/items/MCO1":
                raise status_error(404)
            return super().get(path, params)

    result = MercadoLibreAdapter(MissingApi()).collect(PRODUCT, listing_ids=["MCO1"])
    assert result.observations == []
    assert result.diagnostics["errors"][0]["code"] == "listing_not_found"


def test_catalog_empty_is_not_fabricated():
    result = MercadoLibreAdapter(FakeApi(products=[], rows=[])).collect(PRODUCT)
    assert result.diagnostics["catalog_product_id"] is None
    assert result.diagnostics["catalog_selection_reason"] == "no_matching_catalog_product"
    assert result.observations == []


def test_concentrated_benchmark_cannot_become_strong_purchase_comparison():
    from public_procurement.investigation.market_benchmark.schemas import PublicProduct

    purchase = PublicProduct(
        brand="Samsung",
        model="58U8000H",
        public_process_identity="fixture",
        public_process_code="fixture",
        public_entity="Test",
        public_product_description="Test TV",
        public_unit_price=3000000,
        public_price_stage="contract",
        public_price_date=NOW,
        public_evidence_ref="fixture",
        public_document="fixture.pdf",
        public_page_reference="p.1",
        price_origin="explicit",
    )
    report = run_mercadolibre_benchmark(
        purchase,
        MercadoLibreAdapter(FakeApi(rows=[item(i, i) for i in (1, 2, 3)])),
        listing_ids=["MCO1", "MCO2", "MCO3"],
    )
    assert report["benchmark"]["benchmark_status"] == "ready"
    assert report["benchmark"]["evidence_sufficiency"] == "marketplace_concentrated_evidence"
    assert report["signal"] is None
    assert report["comparison"] is None


def test_requests_cannot_send_tokens_in_query():
    fake_token = "fixture"
    http = MercadoLibreHttp(
        MercadoLibreSettings(_env_file=None, mercadolibre_access_token=fake_token)
    )
    with pytest.raises(MercadoLibreError, match="query_parameter_not_allowed"):
        http.get("/products/search", {"access_token": fake_token})
    assert not http.requests
