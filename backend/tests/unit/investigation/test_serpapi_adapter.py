import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from public_procurement.investigation.market_benchmark.aggregation import aggregate
from public_procurement.investigation.market_benchmark.schemas import ProductIdentity
from public_procurement.investigation.market_benchmark.serpapi_adapter import (
    SerpApiShoppingAdapter,
    normalize_offer,
    shopping_query,
)
from public_procurement.investigation.market_benchmark.serpapi_http import (
    SerpApiError,
    SerpApiHttp,
    SerpApiSettings,
    sanitize,
)
from public_procurement.investigation.market_benchmark.service import run_benchmark

NOW = datetime(2026, 11, 5, tzinfo=UTC)
TARGET = ProductIdentity(
    brand="Samsung",
    model="58U8000H",
    canonical_model="UN58U8000H",
    product_type="televisor",
    size="58 pulgadas",
)


@pytest.fixture
def fixture():
    return json.loads(
        (Path(__file__).resolve().parents[2] / "fixtures/serpapi_samsung.json").read_text(
            encoding="utf8"
        )
    )


class API:
    def __init__(self, fixture):
        self.fixture, self.calls = fixture, []

    def search(self, parameters):
        self.calls.append(parameters.copy())
        return copy.deepcopy(
            self.fixture["shopping" if parameters["engine"] == "google_shopping" else "product"]
        )


def test_real_case_two_high_one_ambiguous_no_signal(fixture):
    api = API(fixture)
    report = run_benchmark(TARGET, shopping=SerpApiShoppingAdapter(api), now=NOW)
    b = report["benchmark"]
    assert b["valid_observations_count"] == 2
    assert b["benchmark_status"] == "insufficient_market_evidence"
    assert report["signal"] is None
    stores = b["observations"]
    assert len(stores) == 3
    assert len(b["duplicates"]) == 3  # optional immersive returned the same offers
    ambiguous = next(o for o in stores if o["retailer"] == "Addi")
    assert not ambiguous["valid_for_benchmark"]
    assert ambiguous["provider_metadata"]["identity_diagnostic"] == "ambiguous"
    assert ambiguous["match_level"] == "partial"
    valid = [o for o in stores if o["valid_for_benchmark"]]
    assert {o["price"] for o in valid} == {"1799900", "3339900"}
    assert all(o["match_level"] == "high" for o in valid)
    assert all(o["currency_inferred"] and o["currency"] == "COP" for o in valid)
    assert all(o["price_evidence_level"] == "shopping_provider_price" for o in valid)
    assert len(report["shopping_discovery"]["shopping_candidates"]) == 1
    assert all(
        "fixture-public-product-token" not in json.dumps(r) for r in api_safe_receipts(report)
    )


def api_safe_receipts(report):
    return [report["shopping_discovery"], report["benchmark"]]


def test_query_uses_context_and_canonical_without_changing_original():
    assert shopping_query(TARGET) == "Samsung UN58U8000H televisor 58 pulgadas"
    assert TARGET.model == "58U8000H"


@pytest.mark.parametrize(
    ("title", "accepted"),
    [
        ("TV Samsung UN58U8000HKXZL 58 pulgadas", True),
        ("TV Samsung 58U8000H 58 pulgadas", True),
        ("TV Samsung U8500H 58 pulgadas", False),
        ("TV Samsung UN58U8000H 55 pulgadas", False),
        ("Control remoto Samsung UN58U8000H", False),
        ("Televisor Samsung 58 pulgadas", False),
    ],
)
def test_existing_matching_applies_per_store(fixture, title, accepted):
    row = {**fixture["product"]["product_results"]["stores"][0], "title": title}
    o = normalize_offer(
        TARGET, row, {"brand": "Samsung"}, "1", "google_product", "query", True, NOW
    )
    assert o.valid_for_benchmark is accepted


@pytest.mark.parametrize(
    ("co", "currency", "formatted", "expected"),
    [
        (True, None, "$ 1.799.900", True),
        (False, None, "$ 1.799.900", False),
        (True, "USD", "$ 1.799.900", False),
        (True, "COP", "US$ 450", False),
        (True, None, "US$ 450", False),
        (False, "COP", "COP $ 1.799.900", True),
    ],
)
def test_controlled_currency_inference(fixture, co, currency, formatted, expected):
    row = {
        **fixture["product"]["product_results"]["stores"][0],
        "currency": currency,
        "price": formatted,
    }
    o = normalize_offer(TARGET, row, {"brand": "Samsung"}, "1", "google_product", "q", co, NOW)
    assert o.valid_for_benchmark is expected
    assert o.currency_inferred is (expected and currency is None)


def test_three_valid_diverse_stop_before_immersive_and_other_product(fixture):
    stores = fixture["product"]["product_results"]["stores"]
    stores[2]["title"] = "TV Samsung UN58U8000H 58 pulgadas"
    fixture["shopping"]["shopping_results"].append(
        {**fixture["shopping"]["shopping_results"][0], "product_id": "222"}
    )
    api = API(fixture)
    report = run_benchmark(TARGET, shopping=SerpApiShoppingAdapter(api))
    assert [r["engine"] for r in api.calls] == ["google_shopping", "google_product"]
    assert report["benchmark"]["valid_observations_count"] == 3
    assert report["benchmark"]["evidence_sufficiency"] == "sufficient_diverse_market_evidence"


def test_product_without_stores_fully_empty_then_next_id(fixture):
    fixture["shopping"]["shopping_results"].append(
        {**fixture["shopping"]["shopping_results"][0], "product_id": "222"}
    )
    api = Mock()
    api.search.side_effect = [
        fixture["shopping"],
        {"error": "No results", "search_information": {"product_results_state": "Fully empty"}},
        fixture["product"],
    ]
    result = SerpApiShoppingAdapter(api, enable_immersive=False).discover(TARGET)
    assert aggregate(TARGET, result.observations, NOW).valid_observations_count == 2
    assert result.diagnostics["requests"][1]["product_results_state"] == "Fully empty"
    assert api.search.call_count == 3


def test_page_token_absent_no_immersive(fixture):
    del fixture["product"]["product_results"]["page_token"]
    api = API(fixture)
    result = SerpApiShoppingAdapter(api).discover(TARGET)
    assert api.calls[-1]["engine"] == "google_product"
    assert len(api.calls) == 2
    assert any(w["code"] == "page_token_absent" for w in result.diagnostics["warnings"])


def test_immersive_hard_limit_one_extra_page_same_base_token(fixture):
    fixture["product"]["product_results"]["stores_next_page_token"] = "continuation"
    api = API(fixture)
    result = SerpApiShoppingAdapter(api).discover(TARGET)
    assert len(api.calls) == 4
    assert result.diagnostics["immersive_pages"] == 2
    assert api.calls[-1]["page_token"] == api.calls[-2]["page_token"]
    assert api.calls[-1]["next_page_token"] == "continuation"


def test_dedupe_tracking_across_product_and_immersive(fixture):
    result = SerpApiShoppingAdapter(API(fixture)).discover(TARGET)
    for o in result.observations[3:]:
        o.url = type(o.url)(
            str(o.url) + "&srsltid=tracking"
            if "?" in str(o.url)
            else str(o.url) + "?srsltid=tracking"
        )
    assert aggregate(TARGET, result.observations, NOW).valid_observations_count == 2


def test_serpapi_429_is_nonblocking_and_scout_fallback_runs(fixture):
    from public_procurement.investigation.market_benchmark.matching import observe
    from public_procurement.investigation.market_benchmark.schemas import SearchResult
    from tests.market_pages import FixturePageVerifier

    api, scout = Mock(), Mock()
    api.search.side_effect = SerpApiError("rate_limited", 429)
    scout.scout.return_value = [
        observe(
            TARGET,
            SearchResult(
                title="TV Samsung UN58U8000H",
                snippet="COP $2.000.000",
                url=f"https://fixture{i}.co/product/un58u8000h",
                query="q",
                captured_at=NOW,
                search_provider="fixture",
            ),
        )
        for i in range(3)
    ]
    report = run_benchmark(
        TARGET,
        shopping=SerpApiShoppingAdapter(api),
        scout=scout,
        page_verifier=FixturePageVerifier(),
    )
    assert scout.scout.call_count == 1
    assert report["benchmark"]["valid_observations_count"] == 3
    assert report["status"] == "completed_with_warnings"
    assert report["errors"][0]["code"] == "rate_limited"
    assert api.search.call_count == 1


def test_two_serpapi_prices_are_preserved_when_fallback_fails(fixture):
    scout = Mock()
    scout.scout.side_effect = TimeoutError("private details")
    report = run_benchmark(TARGET, shopping=SerpApiShoppingAdapter(API(fixture)), scout=scout)
    assert report["benchmark"]["valid_observations_count"] == 2
    assert "private details" not in json.dumps(report)
    assert scout.scout.call_args.args[0].target_observations == 1


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "authentication_failed"),
        (403, "authentication_failed"),
        (429, "rate_limited"),
        (503, "provider_http_error"),
    ],
)
def test_http_errors_sanitized_no_retry(monkeypatch, status, code):
    original, requests = httpx.Client, []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": "fixture-secret"})

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )
    http = SerpApiHttp(SerpApiSettings(_env_file=None, serpapi_api_key="fixture-secret"))
    with pytest.raises(SerpApiError, match=code) as error:
        http.search({"engine": "google_shopping", "q": "fixture"})
    assert "fixture-secret" not in str(error.value)
    assert len(requests) == 1


def test_missing_key_degrades_without_network(monkeypatch):
    client = Mock(side_effect=AssertionError("No network allowed"))
    monkeypatch.setattr(httpx, "Client", client)
    result = SerpApiShoppingAdapter(SerpApiHttp(SerpApiSettings(_env_file=None))).discover(TARGET)
    assert result.errors[0]["code"] == "missing_api_key"
    assert result.diagnostics["request_count"] == 0
    client.assert_not_called()


def test_redaction_nested_and_encoded():
    value = {
        "api_key": "secret /",
        "nested": ["https://x.co/?api_key=secret+%2F"],
        "text": "secret /",
    }
    assert "secret" not in json.dumps(sanitize(value, "secret /"))


def test_invalid_port_response_does_not_abort():
    shopping = Mock()
    shopping.discover.return_value = {"unexpected": "sensitive-provider-body"}
    report = run_benchmark(TARGET, shopping=shopping)
    assert report["errors"][0]["code"] == "shopping_source_failed"
    assert "sensitive-provider-body" not in json.dumps(report)


@pytest.mark.parametrize("fails", [False, True])
def test_mco_enrichment_preferred_or_structured_price_preserved(fixture, fails):
    from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
        MercadoLibreAdapter,
        MercadoLibreError,
    )

    fixture["product"]["product_results"]["stores"][0]["link"] = (
        "https://articulo.mercadolibre.com.co/MCO-123456-tv"
    )
    api = Mock()
    api.requests = []
    native = {
        "id": "MCO123456",
        "site_id": "MCO",
        "title": "TV Samsung UN58U8000H 58 pulgadas",
        "price": 1750000,
        "currency_id": "COP",
        "status": "active",
        "condition": "new",
        "seller_id": 99,
        "available_quantity": 1,
        "permalink": "https://articulo.mercadolibre.com.co/MCO-123456-tv",
    }
    api.get.side_effect = MercadoLibreError("access_forbidden", 403) if fails else None
    api.get.return_value = native
    report = run_benchmark(
        TARGET,
        shopping=SerpApiShoppingAdapter(API(fixture)),
        marketplace_adapter=MercadoLibreAdapter(api),
    )
    api.get.assert_called_once_with("/items/MCO123456")  # no unnecessary catalog searches
    assert report["benchmark"]["valid_observations_count"] == 2
    prices = {o["price"] for o in report["benchmark"]["observations"] if o["valid_for_benchmark"]}
    assert ("1799900" if fails else "1750000") in prices


def test_page_verification_can_upgrade_provider_without_claiming_it_already_visited(fixture):
    from tests.market_pages import FixturePageVerifier

    result = SerpApiShoppingAdapter(API(fixture), enable_immersive=False).discover(TARGET)
    provider = next(o for o in result.observations if o.valid_for_benchmark)
    assert provider.verification_status == "not_attempted"
    page = FixturePageVerifier().verify(TARGET, provider)
    assert page.price_evidence_level == "page_verified_price"
    b = aggregate(TARGET, [provider, page], NOW)
    assert b.observations[0].price_evidence_level == "page_verified_price"


def test_marketplace_prices_stay_concentrated(fixture):
    for i, store in enumerate(fixture["product"]["product_results"]["stores"]):
        store.update(
            title="TV Samsung UN58U8000HKXZL 58 pulgadas",
            link=f"https://articulo.mercadolibre.com.co/MCO-{123456 + i}-tv",
        )
    result = SerpApiShoppingAdapter(API(fixture)).discover(TARGET)
    b = aggregate(TARGET, result.observations, NOW)
    assert b.valid_observations_count == 3
    assert b.evidence_sufficiency == "marketplace_concentrated_evidence"


@pytest.mark.parametrize(
    "failure",
    [
        SerpApiError("timeout"),
        SerpApiError("invalid_payload"),
        SerpApiError("provider_http_error", 500),
    ],
)
def test_provider_failures_remain_insufficient_not_crashes(failure):
    api = Mock()
    api.search.side_effect = failure
    report = run_benchmark(TARGET, shopping=SerpApiShoppingAdapter(api))
    assert report["benchmark"]["benchmark_status"] == "insufficient_market_evidence"
    assert report["status"] == "completed_with_warnings"
    assert api.search.call_count == 1


def test_partial_product_has_warning_but_keeps_offers(fixture):
    fixture["product"]["search_information"] = {"product_results_state": "Partial product details"}
    result = SerpApiShoppingAdapter(API(fixture), enable_immersive=False).discover(TARGET)
    assert aggregate(TARGET, result.observations, NOW).valid_observations_count == 2
    assert result.diagnostics["source_status"] == "degraded"


def test_immersive_does_not_restore_cop_after_explicit_market_conflict(fixture):
    foreign = copy.deepcopy(fixture["product"])
    foreign["search_parameters"]["gl"] = "us"
    immersive = copy.deepcopy(foreign)
    immersive["search_parameters"] = {"engine": "google_immersive_product"}
    api = Mock()
    api.search.side_effect = [fixture["shopping"], foreign, immersive]
    result = SerpApiShoppingAdapter(api).discover(TARGET)
    assert aggregate(TARGET, result.observations, NOW).valid_observations_count == 0
    assert not any(o.currency_inferred for o in result.observations)


@pytest.mark.parametrize("body", [b"not json", b"[]"])
def test_malformed_http_payload_sanitized(monkeypatch, body):
    original = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, content=body)),
            **kwargs,
        ),
    )
    http = SerpApiHttp(SerpApiSettings(_env_file=None, serpapi_api_key="fixture-secret"))
    with pytest.raises(SerpApiError, match="invalid_payload"):
        http.search({"engine": "google_shopping", "q": "fixture"})


def test_runtime_transport_timeout_never_exposes_request_url(monkeypatch):
    original = httpx.Client

    def handler(request):
        raise httpx.ReadTimeout("fixture-secret in request URL")

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )
    http = SerpApiHttp(SerpApiSettings(_env_file=None, serpapi_api_key="fixture-secret"))
    with pytest.raises(SerpApiError, match="timeout") as error:
        http.search({"engine": "google_shopping", "q": "fixture"})
    assert "fixture-secret" not in str(error.value)


def test_native_api_identity_rejection_is_not_hidden_by_provider_price(fixture):
    from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
        MercadoLibreAdapter,
    )

    fixture["product"]["product_results"]["stores"][0]["link"] = (
        "https://articulo.mercadolibre.com.co/MCO-123456-tv"
    )
    api = Mock()
    api.requests = []
    api.get.return_value = {
        "id": "MCO123456",
        "site_id": "MCO",
        "title": "TV Samsung UN58U8000F 58 pulgadas",
        "price": 1750000,
        "currency_id": "COP",
        "status": "active",
        "condition": "new",
        "seller_id": 99,
        "available_quantity": 1,
        "permalink": "https://articulo.mercadolibre.com.co/MCO-123456-tv",
    }
    report = run_benchmark(
        TARGET,
        shopping=SerpApiShoppingAdapter(API(fixture)),
        marketplace_adapter=MercadoLibreAdapter(api),
    )
    assert report["benchmark"]["valid_observations_count"] == 1
    assert any(
        "api_enrichment_rejected" in note
        for row in [*report["benchmark"]["observations"], *report["benchmark"]["duplicates"]]
        for note in row["notes"]
    )
