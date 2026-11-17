import json
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from public_procurement.investigation.market_benchmark.foundry_scout import (
    FoundryMarketPriceScout,
    normalize_response,
)
from public_procurement.investigation.market_benchmark.matching import observe
from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
    MercadoLibreAdapter,
    MercadoLibreError,
)
from public_procurement.investigation.market_benchmark.ports import (
    ScoutRequest,
    ScoutUnavailableError,
)
from public_procurement.investigation.market_benchmark.schemas import ProductIdentity, SearchResult
from tests.market_pages import verified_benchmark as run_benchmark

NOW = datetime(2026, 11, 4, tzinfo=UTC)
TV = ProductIdentity(
    brand="Samsung", model="58U8000H", canonical_model="UN58U8000H", size="58 pulgadas"
)


def evidence(index=0, **changes):
    return SearchResult.model_validate(
        {
            "title": "TV Samsung UN58U8000H 58 pulgadas",
            "snippet": "Precio COP $2.000.000 disponible para compra",
            "url": f"https://tienda{index}.com.co/product/un58u8000h",
            "query": "fixture",
            "captured_at": NOW,
            "search_provider": "fixture",
            **changes,
        }
    )


class Scout:
    def __init__(self, rows):
        self.rows, self.requests, self.consumed = rows, [], 0
        self.closed = False

    def scout(self, request):
        self.requests.append(request)
        try:
            for row in self.rows:
                self.consumed += 1
                yield observe(request.product, row)
        finally:
            self.closed = True


@pytest.mark.parametrize("existing", [0, 1, 2, 3])
def test_activation_missing_only_preserves_existing_and_stops(existing):
    search = Mock()
    search.search.return_value = [evidence(i) for i in range(existing)]
    scout = Scout([evidence(i) for i in range(existing, 8)])
    report = run_benchmark(TV, search, NOW, scout=scout)
    assert report["benchmark"]["valid_observations_count"] == 3
    assert len(scout.requests) == (existing < 3)
    if existing < 3:
        assert scout.requests[0].target_observations == 3 - existing
        assert scout.requests[0].max_observations == 5 - existing
        assert len(scout.requests[0].excluded_urls) == existing
        assert scout.consumed == 3 - existing
        assert scout.closed
    for i in range(existing):
        assert any(
            str(o["url"]) == str(evidence(i).url) for o in report["benchmark"]["observations"]
        )


def test_dedupe_does_not_satisfy_target_and_candidate_budget_is_bounded():
    scout = Scout([evidence()] * 50)
    report = run_benchmark(TV, now=NOW, scout=scout)
    assert scout.consumed == 10
    assert scout.closed
    assert report["benchmark"]["valid_observations_count"] == 1
    assert len(report["benchmark"]["duplicates"]) == 9
    assert report["benchmark"]["benchmark_status"] == "insufficient_market_evidence"


def test_cross_source_dedupe_and_provenance():
    search = Mock()
    search.search.return_value = [evidence()]
    scout = Scout([evidence(), evidence(1), evidence(2)])
    report = run_benchmark(TV, search, NOW, scout=scout)
    assert report["benchmark"]["valid_observations_count"] == 3
    assert len(report["benchmark"]["duplicates"]) == 1
    assert report["benchmark"]["evidence_sufficiency"] == "sufficient_diverse_market_evidence"
    assert (
        sum(
            o["discovery_method"] == "market_price_scout"
            for o in report["benchmark"]["observations"]
        )
        >= 2
    )


@pytest.mark.parametrize(
    ("title", "accepted"),
    [
        ("TV Samsung 58U8000H 58 pulgadas", True),
        ("TV Samsung UN58U8000H 58 pulgadas", True),
        ("Samsung televisor 58 pulgadas", False),
        ("Samsung UN65U8000H 65 pulgadas", False),
        ("Control remoto Samsung UN58U8000H", False),
    ],
)
def test_scout_matching_not_relaxed(title, accepted):
    report = run_benchmark(TV, now=NOW, scout=Scout([evidence(title=title)]))
    assert report["benchmark"]["valid_observations_count"] == int(accepted)


def test_does_not_trust_scout_price_or_match_flag():
    fake = observe(TV, evidence(title="TV otra marca ABC9999", snippet="sin precio"))
    fake.valid_for_benchmark = True
    fake.match_level = "exact"
    fake.price = 123
    scout = Mock()
    scout.scout.return_value = [fake]
    report = run_benchmark(TV, scout=scout)
    assert report["benchmark"]["valid_observations_count"] == 0


@pytest.mark.parametrize(
    "error", [TimeoutError("secret"), ScoutUnavailableError("secret"), ValueError("secret")]
)
def test_provider_failure_is_nonblocking_and_sanitized(error):
    scout = Mock()
    scout.scout.side_effect = error
    search = Mock()
    search.search.return_value = [evidence()]
    report = run_benchmark(TV, search, NOW, scout=scout)
    assert report["status"] == "completed_with_warnings"
    assert report["benchmark"]["valid_observations_count"] == 1
    assert "secret" not in json.dumps(report)
    assert report["market_price_scout"]["status"] == "degraded"


@pytest.mark.parametrize(("target", "maximum"), [(0, 5), (4, 3), (3, 6)])
def test_invalid_limits_do_not_start_provider(target, maximum):
    with pytest.raises(ValueError, match="Scout supports"):
        run_benchmark(TV, target_observations=target, max_observations=maximum)


def test_explicit_maximum_and_stop_target():
    scout = Scout([evidence(i) for i in range(10)])
    report = run_benchmark(TV, scout=scout, target_observations=5)
    assert scout.consumed == report["benchmark"]["valid_observations_count"] == 5


def ml_item(i):
    return {
        "id": f"MCO{i}",
        "site_id": "MCO",
        "title": "TV Samsung UN58U8000H 58 pulgadas",
        "price": 1900000,
        "currency_id": "COP",
        "status": "active",
        "condition": "new",
        "seller_id": i,
        "available_quantity": 1,
        "permalink": f"https://articulo.mercadolibre.com.co/MCO-{i}-tv",
    }


def test_marketplace_enrichment_preferred_and_concentration_preserved():
    api = Mock()
    api.requests = []
    api.get.side_effect = lambda path, params=None: ml_item(int(path.rsplit("MCO", 1)[1]))
    scout = Scout([evidence(i, url=ml_item(i)["permalink"]) for i in range(123456, 123459)])
    report = run_benchmark(
        TV, scout=scout, marketplace_adapter=MercadoLibreAdapter(api, enable_catalog=False)
    )
    benchmark = report["benchmark"]
    assert api.get.call_count == 3
    assert benchmark["valid_observations_count"] == 3
    assert benchmark["median_price"] == "1900000"
    assert benchmark["evidence_sufficiency"] == "marketplace_concentrated_evidence"
    assert benchmark["distinct_sellers_count"] == 3
    assert all(o["source_type"] == "marketplace_api" for o in benchmark["observations"])
    assert all(o["discovery_method"] == "market_price_scout" for o in benchmark["observations"])


@pytest.mark.parametrize(
    "failure",
    [
        MercadoLibreError("token_expired_or_invalid", 401),
        MercadoLibreError("access_forbidden", 403),
        MercadoLibreError("rate_limited", 429),
        MercadoLibreError("provider_http_error", 503),
        TimeoutError("secret"),
        ValueError("invalid payload"),
    ],
)
def test_failed_ml_enrichment_preserves_web(failure):
    api = Mock()
    api.requests = []
    api.get.side_effect = failure
    report = run_benchmark(
        TV,
        scout=Scout([evidence(url=ml_item(123456)["permalink"])]),
        marketplace_adapter=MercadoLibreAdapter(api, enable_catalog=False),
    )
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["benchmark"]["median_price"] == "2000000"
    assert report["status"] == "completed_with_warnings"


def response(offers, sources):
    result = Mock()
    result.id = "resp-fixture"
    result.output_text = json.dumps({"offers": offers})
    result.model_dump.return_value = {
        "output": [
            {
                "type": "web_search_call",
                "action": {
                    "sources": [{"type": "url", "url": url} for url in sources],
                },
            }
        ]
    }
    return result


def test_normalize_grounded_response_and_provenance():
    row = evidence()
    r = response(
        [{"title": row.title, "url": str(row.url), "evidence_text": row.snippet}], [str(row.url)]
    )
    observations = list(normalize_response(r, ScoutRequest(TV)))
    assert len(observations) == 1
    assert not observations[0].valid_for_benchmark
    assert observations[0].verification_status == "weak"
    assert observations[0].evidence.provider_reference == "resp-fixture"
    assert observations[0].extraction_method == "grounded_web_quote"


def test_invented_uncited_url_and_over_limit_results_excluded():
    rows = [evidence(i) for i in range(10)]
    r = response(
        [{"title": row.title, "url": str(row.url), "evidence_text": row.snippet} for row in rows],
        [str(row.url) for row in rows[1:]],
    )
    observations = list(normalize_response(r, ScoutRequest(TV, 1, 2)))
    assert len(observations) == 1
    assert str(observations[0].url) == str(rows[1].url)


def test_dedicated_adapter_no_agent_version_no_public_evidence_one_bounded_call():
    client = Mock()
    client.responses.create.return_value = response([], [])
    assert list(FoundryMarketPriceScout(client, "fixture-model").scout(ScoutRequest(TV))) == []
    client.responses.create.assert_called_once()
    options = client.responses.create.call_args.kwargs
    assert options["model"] == "fixture-model"
    assert options["max_tool_calls"] == 3
    assert options["parallel_tool_calls"] is False
    assert options["store"] is False
    assert "agent_reference" not in options
    client.agents.create_version.assert_not_called()


def test_sdk_error_does_not_leak_secrets():
    client = Mock()
    client.responses.create.side_effect = RuntimeError("private headers")
    with pytest.raises(ScoutUnavailableError, match="RuntimeError"):
        list(FoundryMarketPriceScout(client).scout(ScoutRequest(TV)))


def test_invalid_scout_json_is_provider_failure():
    r = response([], [])
    r.output_text = "not json"
    with pytest.raises(ScoutUnavailableError):
        list(normalize_response(r, ScoutRequest(TV)))
