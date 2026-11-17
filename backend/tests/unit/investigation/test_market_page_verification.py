import json
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import httpx
import pytest

from public_procurement.investigation.market_benchmark.aggregation import aggregate
from public_procurement.investigation.market_benchmark.matching import observe
from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
    MercadoLibreAdapter,
    MercadoLibreError,
)
from public_procurement.investigation.market_benchmark.page_verifier import (
    HttpMarketPageVerifier,
    PageResponse,
    fetch_page,
    public_url,
)
from public_procurement.investigation.market_benchmark.schemas import (
    PageEvidence,
    ProductIdentity,
    SearchResult,
)
from public_procurement.investigation.market_benchmark.service import run_benchmark

NOW = datetime(2026, 11, 4, tzinfo=UTC)
PRODUCT = ProductIdentity(
    brand="Samsung",
    model="58U8000H",
    canonical_model="UN58U8000H",
    product_type="televisor",
    size="58 pulgadas",
)


def candidate(index=0, **changes):
    return observe(
        PRODUCT,
        SearchResult.model_validate(
            {
                "title": "TV Samsung UN58U8000H 58 pulgadas",
                "snippet": "COP $2.000.000",
                "url": f"https://tienda{index}.com.co/product/un58u8000h",
                "query": "fixture",
                "captured_at": NOW,
                "search_provider": "fixture",
                **changes,
            }
        ),
    )


def product_data(**changes):
    return {
        "@type": "Product",
        "name": "TV Samsung UN58U8000H 58 pulgadas",
        "brand": {"name": "Samsung"},
        "model": "UN58U8000H",
        "screenSize": "58 pulgadas",
        "offers": {
            "@type": "Offer",
            "price": "1900000",
            "priceCurrency": "COP",
            "availability": "https://schema.org/InStock",
            "seller": {"name": "Fixture"},
        },
        **changes,
    }


def html(data=None, extra=""):
    return (
        '<html><title>Producto</title><script type="application/ld+json">'
        + json.dumps(product_data() if data is None else data)
        + "</script>"
        + extra
        + "</html>"
    ).encode()


def verifier(body=None, status=200, headers=None):
    fetch = Mock(
        side_effect=lambda url: PageResponse(
            url, status, html() if body is None else body, headers or {"content-type": "text/html"}
        )
    )
    return HttpMarketPageVerifier(fetch), fetch


@pytest.mark.parametrize("model", ["58U8000H", "UN58U8000H"])
def test_exact_or_high_model_and_page_price_accepted(model):
    v, _ = verifier(html(product_data(name=f"TV Samsung {model} 58 pulgadas", model=model)))
    row = v.verify(PRODUCT, candidate())
    assert row.valid_for_benchmark
    assert row.price == Decimal("1900000")  # page overrides snippet's 2,000,000
    assert row.verification_status == "verified"
    assert row.price_evidence_level == "page_verified_price"
    assert isinstance(row.evidence, PageEvidence)
    assert len(row.evidence.content_sha256) == 64
    assert row.evidence.candidate.snippet == "COP $2.000.000"
    assert row.seller_name == "Fixture"


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (product_data(model="UN58TU7000"), "wrong_model"),
        (product_data(model="U8500"), "wrong_model"),
        (product_data(screenSize="55"), "wrong_size"),
        (product_data(name="TV Samsung UN58U8000H 65 pulgadas"), "wrong_size"),
        (product_data(name="Control remoto Samsung UN58U8000H"), "accessory_or_replacement"),
        (product_data(name="Pantalla para Samsung UN58U8000H"), "accessory_or_replacement"),
        (product_data(brand="LG"), "wrong_brand"),
        (product_data(category="Celular"), "wrong_product_type"),
        (product_data(offers={}), "no_price"),
        (product_data(offers={"price": "1900000"}), "currency_unknown"),
        (product_data(offers={"price": "1900000", "priceCurrency": "USD"}), "currency_unknown"),
        (
            product_data(
                offers=[
                    {"price": "1900000", "priceCurrency": "COP"},
                    {"price": "2100000", "priceCurrency": "COP"},
                ]
            ),
            "ambiguous_price",
        ),
        (
            product_data(
                offers={"@type": "AggregateOffer", "lowPrice": "1900000", "highPrice": "2100000"}
            ),
            "ambiguous_price",
        ),
        (
            product_data(
                offers={
                    "price": "1900000",
                    "priceCurrency": "COP",
                    "availability": "https://schema.org/OutOfStock",
                }
            ),
            "unavailable",
        ),
        (
            product_data(
                offers={"price": "1900000", "priceCurrency": "COP", "priceValidUntil": "2020-01-01"}
            ),
            "stale_or_cache_only",
        ),
        (
            product_data(
                offers={
                    "price": "1900000",
                    "priceCurrency": "COP",
                    "itemCondition": "https://schema.org/UsedCondition",
                }
            ),
            "accessory_or_replacement",
        ),
    ],
)
def test_page_rejection_reasons_and_provenance(data, reason):
    v, _ = verifier(html(data))
    row = v.verify(PRODUCT, candidate())
    assert not row.valid_for_benchmark
    assert row.rejection_reason == reason
    assert isinstance(row.evidence, PageEvidence)
    assert row.evidence.extracted_fields["name"] == data["name"]


def test_multiple_products_do_not_promote_recommendation_to_main_offer():
    v, _ = verifier(html([product_data(model="UN58TU7000"), product_data()]))
    row = v.verify(PRODUCT, candidate())
    assert not row.valid_for_benchmark
    assert row.rejection_reason == "ambiguous_price"


def test_explicit_centimeters_match_inches_without_model_equivalence_guess():
    v, _ = verifier(html(product_data(screenSize={"value": "147.32", "unitCode": "CMT"})))
    assert v.verify(PRODUCT, candidate()).valid_for_benchmark


def test_meta_only_page_and_conflicting_meta_price():
    meta = '<meta property="og:title" content="TV Samsung UN58U8000H 58 pulgadas">'
    meta += '<meta property="product:price:amount" content="1.900.000">'
    meta += '<meta property="product:price:currency" content="COP">'
    v, _ = verifier(meta.encode())
    assert v.verify(PRODUCT, candidate()).valid_for_benchmark
    v, _ = verifier(html(extra=meta.replace("1.900.000", "2.100.000")))
    assert v.verify(PRODUCT, candidate()).rejection_reason == "ambiguous_price"


@pytest.mark.parametrize("status", [401, 403, 429, 500, 404, 304])
def test_http_error_nonblocking(status):
    v, _ = verifier(status=status)
    row = v.verify(PRODUCT, candidate())
    assert not row.valid_for_benchmark
    assert row.rejection_reason in {"blocked", "verification_failed", "stale_or_cache_only"}


def test_blocked_js_and_cached_pages_never_promote_snippet():
    for body in [
        b"<title>Access denied</title>",
        b"<title>TV Samsung UN58U8000H</title><script>loadApp()</script>",
    ]:
        v, _ = verifier(body)
        row = v.verify(PRODUCT, candidate())
        assert not row.valid_for_benchmark
        assert row.price_evidence_level == "snippet_price"
    v, _ = verifier(headers={"warning": '110 - "Response is stale"'})
    assert v.verify(PRODUCT, candidate()).rejection_reason == "stale_or_cache_only"


def test_generic_page_not_fetched_and_redirect_to_generic_not_accepted():
    v, fetch = verifier()
    assert (
        v.verify(PRODUCT, candidate(url="https://tienda.com.co/")).rejection_reason
        == "generic_page"
    )
    fetch.assert_not_called()
    v = HttpMarketPageVerifier(lambda _: PageResponse("https://tienda.com.co/", 200, html(), {}))
    assert v.verify(PRODUCT, candidate()).rejection_reason == "generic_page"


def test_snippet_only_is_weak_and_cannot_produce_benchmark():
    scout = Mock()
    scout.scout.return_value = [candidate(i) for i in range(3)]
    report = run_benchmark(PRODUCT, scout=scout)
    assert report["benchmark"]["valid_observations_count"] == 0
    assert all(
        o["rejection_reason"] == "stale_or_cache_only" for o in report["benchmark"]["observations"]
    )


def test_aggregation_never_counts_unverified_snippets_even_if_matching_marked_valid():
    result = aggregate(PRODUCT, [candidate(i) for i in range(3)], NOW)
    assert result.valid_observations_count == 0
    assert result.median_price is None


def test_verifier_must_provide_direct_page_provenance_not_just_a_flag():
    fake = candidate()
    fake.price_evidence_level = "page_verified_price"
    fake.verification_status = "verified"
    v, scout = Mock(), Mock()
    v.verify.return_value = fake
    scout.scout.return_value = [candidate()]
    report = run_benchmark(PRODUCT, scout=scout, page_verifier=v)
    assert report["benchmark"]["valid_observations_count"] == 0


def test_existing_urls_verified_before_scout_and_stop_when_diverse():
    search = Mock()
    search.search.return_value = [candidate(i).evidence for i in range(3)]
    scout = Mock()
    v, fetch = verifier()
    report = run_benchmark(PRODUCT, search, scout=scout, page_verifier=v)
    scout.scout.assert_not_called()
    assert fetch.call_count == 3
    assert report["benchmark"]["valid_observations_count"] == 3
    assert report["benchmark"]["median_price"] == "1900000"


def test_scout_continues_for_diversity_then_stops_and_dedupes_pages():
    rows = [
        candidate(url=f"https://articulo.mercadolibre.com.co/MCO-{i}-tv")
        for i in range(123456, 123459)
    ]
    rows += [candidate(url=str(rows[0].url) + "?utm_source=duplicate"), candidate(4), candidate(5)]
    scout = Mock()
    scout.scout.return_value = rows
    v, fetch = verifier()
    report = run_benchmark(PRODUCT, scout=scout, page_verifier=v)
    assert report["market_price_scout"]["candidates_received"] == 5
    assert fetch.call_count == 4
    assert report["benchmark"]["valid_observations_count"] == 4
    assert report["benchmark"]["evidence_sufficiency"] == "sufficient_diverse_market_evidence"


def test_marketplace_max_five_stops_and_remains_concentrated():
    scout = Mock()
    scout.scout.return_value = [
        candidate(url=f"https://articulo.mercadolibre.com.co/MCO-{i}-tv")
        for i in range(123456, 123464)
    ]
    v, fetch = verifier()
    report = run_benchmark(PRODUCT, scout=scout, page_verifier=v)
    assert fetch.call_count == 5
    assert report["benchmark"]["valid_observations_count"] == 5
    assert report["benchmark"]["evidence_sufficiency"] == "marketplace_concentrated_evidence"


def api_item():
    return {
        "id": "MCO123456",
        "site_id": "MCO",
        "title": "TV Samsung UN58U8000H 58 pulgadas",
        "price": 1800000,
        "currency_id": "COP",
        "condition": "new",
        "status": "active",
        "seller_id": 1,
        "available_quantity": 1,
        "permalink": "https://articulo.mercadolibre.com.co/MCO-123456-tv",
    }


@pytest.mark.parametrize("api_fails", [False, True])
def test_api_preferred_without_page_request_or_page_fallback(api_fails):
    api = Mock()
    api.requests = []
    if api_fails:
        api.get.side_effect = MercadoLibreError("access_forbidden", 403)
    else:
        api.get.return_value = api_item()
    scout = Mock()
    scout.scout.return_value = [candidate(url=api_item()["permalink"])]
    v, fetch = verifier()
    report = run_benchmark(
        PRODUCT,
        scout=scout,
        page_verifier=v,
        marketplace_adapter=MercadoLibreAdapter(api, enable_catalog=False),
    )
    assert fetch.call_count == int(api_fails)
    assert report["benchmark"]["median_price"] == ("1900000" if api_fails else "1800000")
    row = next(o for o in report["benchmark"]["observations"] if o["valid_for_benchmark"])
    assert row["price_evidence_level"] == (
        "page_verified_price" if api_fails else "api_verified_price"
    )


def test_verified_page_preferred_over_snippet_when_deduplicating():
    snippet = candidate()
    v, _ = verifier()
    page = v.verify(PRODUCT, snippet)
    benchmark = aggregate(PRODUCT, [snippet, page], NOW)
    assert benchmark.median_price == Decimal("1900000")
    assert benchmark.duplicates[0].price_evidence_level == "snippet_price"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/p/x",
        "https://user:secret@example.com/p/x",
        "https://127.0.0.1/p/x",
        "https://example.com:8080/p/x",
    ],
)
def test_private_or_credential_url_not_requested(monkeypatch, url):
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 443))])
    with pytest.raises(ValueError, match=r"unsafe_page_url|nonpublic_page_url"):
        public_url(url)


def test_http_redirect_budget_and_private_redirect_and_body_cap(monkeypatch):
    original = httpx.Client
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda host, *a, **k: [
            (2, 1, 6, "", ("127.0.0.1" if host == "127.0.0.1" else "93.184.216.34", 443))
        ],
    )
    requests = []

    def handler(request):
        requests.append(request)
        assert "authorization" not in request.headers
        assert "cookie" not in request.headers
        return httpx.Response(302, headers={"location": "https://127.0.0.1/product/x"})

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )
    with pytest.raises(ValueError, match="nonpublic_page_url"):
        fetch_page("https://example.com/product/x")
    assert len(requests) == 1
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: original(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, headers={"content-type": "text/html"}, content=b"x" * 2_000_001
                )
            ),
            **kwargs,
        ),
    )
    with pytest.raises(ValueError, match="page_budget_exceeded"):
        fetch_page("https://example.com/product/x")
