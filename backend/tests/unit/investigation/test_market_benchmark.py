from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from public_procurement.investigation.market_benchmark.aggregation import TEMPORAL_LIMITATION
from public_procurement.investigation.market_benchmark.matching import observe
from public_procurement.investigation.market_benchmark.schemas import (
    ProductIdentity,
    PublicProduct,
    SearchResult,
)
from public_procurement.investigation.market_benchmark.service import (
    MarketReportStore,
)
from tests.market_pages import verified_benchmark as run_benchmark

NOW = datetime(2026, 11, 4, tzinfo=UTC)


def product(price="3767123"):
    return PublicProduct(
        public_process_identity="fixture-process",
        public_process_code="FIXTURE",
        public_entity="Test entity",
        public_product_description="TV Samsung 58U8000H",
        brand="Samsung",
        model="58U8000H",
        public_unit_price=price,
        public_price_stage="contract",
        public_price_date=NOW,
        public_evidence_ref="fixture-fact",
        public_document="fixture-contract.pdf",
        public_page_reference="p. 3",
        price_origin="explicit",
    )


def result(
    title="TV Samsung 58U8000H 58 pulgadas",
    snippet="COP $2.000.000 en stock",
    url="https://shop.example/product/58u8000h",
):
    return SearchResult(
        title=title,
        snippet=snippet,
        url=url,
        query="fixture query",
        captured_at=NOW,
        search_provider="mock",
    )


@pytest.mark.parametrize(
    ("title", "level", "valid"),
    [
        ("TV Samsung 58U8000H 58 pulgadas", "exact", True),
        ("TV Samsung UN58U8000HKXZL 58 pulgadas", "high", True),
        ("TV Samsung Smart 58 pulgadas", "partial", False),
        ("TV Samsung 58U9000H", "reject", False),
        ("TV Samsung 58U8000H 65 pulgadas", "reject", False),
        ("TV Samsung 58U8000H usado", "reject", False),
        ("TV Samsung 58U8000H reacondicionado", "reject", False),
        ("Combo TV Samsung 58U8000H barra de sonido", "reject", False),
        ("Control remoto Samsung 58U8000H", "reject", False),
    ],
)
def test_identity(title, level, valid):
    observation = observe(product(), result(title=title))
    assert observation.match_level == level
    assert observation.valid_for_benchmark is valid


@pytest.mark.parametrize(
    "snippet",
    [
        "12 cuotas de $100.000",
        "$2.000.000 o 12 cuotas",
        "$2.000.000 $3.000.000",
        "USD $2000",
        "sin precio",
    ],
)
def test_invalid_prices(snippet):
    observation = observe(product(), result(snippet=snippet))
    assert observation.price is None
    assert not observation.valid_for_benchmark


def test_valid_promotion_unknown_stock():
    observation = observe(product(), result(snippet="Promocion COP $2.000.000"))
    assert observation.promotion_detected
    assert observation.availability == "unknown"
    assert observation.valid_for_benchmark
    assert "availability_not_verified" in observation.notes


def test_unavailable_not_in_benchmark():
    assert not observe(product(), result(snippet="COP $2.000.000 agotado")).valid_for_benchmark


def search_results():
    return [
        result(url=f"https://retailer{i}.example/product/58u8000h", snippet=f"COP ${i}.000.000")
        for i in (1, 2, 3)
    ]


@pytest.mark.parametrize(
    ("price", "difference", "percent"),
    [("3000000", "1000000", "50"), ("1000000", "-1000000", "-50")],
)
def test_benchmark_median_and_signed_comparison(price, difference, percent):
    search = Mock()
    search.search.return_value = search_results()
    report = run_benchmark(product(price), search, NOW)
    assert report["benchmark"]["valid_observations_count"] == 3
    assert report["benchmark"]["retailers_count"] == 3
    assert Decimal(report["benchmark"]["median_price"]) == 2000000
    assert Decimal(report["comparison"]["absolute_difference"]) == Decimal(difference)
    assert Decimal(report["comparison"]["percentage_difference"]) == Decimal(percent)
    assert report["signal"]["type"] == "PUBLIC_VS_PRIVATE_PRICE_DIFFERENCE"
    assert TEMPORAL_LIMITATION in report["comparison"]["limitations"]
    assert report["signal"]["public_evidence"]["public_page_reference"] == "p. 3"
    assert (
        report["benchmark"]["observations"][0]["evidence"]["candidate"]["query"] == "fixture query"
    )
    assert search.search.call_count == report["web_discovery"]["queries_executed"]


def test_less_than_three_and_deduplication():
    search = Mock()
    a = result()
    search.search.return_value = [
        a,
        a,
        result(url="https://shop.example/product/58u8000h?utm_source=search"),
    ]
    report = run_benchmark(product(), search, NOW)
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["comparison"] is None
    assert report["signal"] is None
    assert report["benchmark"]["benchmark_status"] == "insufficient_market_evidence"


def test_same_retailer_model_and_price_count_once():
    search = Mock()
    search.search.return_value = [
        result(url=f"https://shop.example/product/58u8000h/offer{i}") for i in range(3)
    ]
    report = run_benchmark(product(), search, NOW)
    assert report["benchmark"]["valid_observations_count"] == 1
    assert report["benchmark"]["retailers_count"] == 1
    assert "limited_retailer_diversity" in report["benchmark"]["limitations"]


def test_no_public_evidence_no_signal():
    search = Mock()
    search.search.return_value = search_results()
    report = run_benchmark(ProductIdentity(brand="Samsung", model="58U8000H"), search, NOW)
    assert report["benchmark"]["benchmark_status"] == "ready"
    assert report["comparison"] is None
    assert report["signal"] is None
    assert report["public_evidence_status"] == "missing_public_evidence"


def test_json_only_write_does_not_change_public_report(tmp_path):
    public = tmp_path / "latest.json"
    public.write_text("original", encoding="utf8")
    search = Mock()
    search.search.return_value = []
    report = run_benchmark(product(), search, NOW)
    store = MarketReportStore(tmp_path)
    store.write(report)
    assert store.read()["reports"][0] == report
    assert public.read_text(encoding="utf8") == "original"
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "latest.json",
        "private-market-latest.json",
    ]


def test_budget_not_purchase_price():
    data = product().model_dump()
    data["public_price_stage"] = "budget"
    with pytest.raises(ValidationError):
        PublicProduct.model_validate(data)


def test_generic_model_rejected():
    with pytest.raises(ValidationError):
        ProductIdentity(brand="Samsung", model="58")


def test_unconfirmed_offer_keeps_evidence_without_purchase_signal():
    from public_procurement.investigation.market_benchmark.schemas import PublicOffer

    data = product().model_dump()
    data.update(
        public_price_stage="offer",
        public_price_date=None,
        price_tax_basis="excludes_vat",
        document_heading_process_code="OTHER-PROCESS",
        public_process_code="MC-070-2026",
        public_page_reference="PDF p. 339 de 340",
        quantity="1",
        item_total="3767123",
        supplier="TEAM IT S.A.S.",
        evidence_text="TV SAMSUNG 58U8000H $3.767.123",
    )
    offer = PublicOffer.model_validate(data)
    search = Mock()
    search.search.return_value = search_results()
    report = run_benchmark(offer, search, NOW)
    assert report["benchmark"]["benchmark_status"] == "ready"
    assert report["public_evidence_status"] == "documented_unconfirmed_offer"
    assert report["public_product"]["public_price_date"] is None
    assert report["public_product"]["public_page_reference"] == "PDF p. 339 de 340"
    assert report["public_product"]["supplier"] == "TEAM IT S.A.S."
    assert "document_process_reference_mismatch" in report["public_product"]["evidence_warnings"]
    assert report["preliminary_comparison"]["status"] == "preliminary_not_confirmed_purchase"
    assert report["preliminary_comparison"]["absolute_difference"] is None
    assert report["comparison"] is None
    assert report["signal"] is None


def test_document_conflict_blocks_even_purchase_label():
    data = product().model_dump()
    data["document_heading_process_code"] = "DIFFERENT-PROCESS"
    search = Mock()
    search.search.return_value = search_results()
    report = run_benchmark(PublicProduct.model_validate(data), search, NOW)
    assert report["comparison"] is None
    assert report["signal"] is None


def test_api_read_only_projection(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from public_procurement.investigation.research import ResearchReportStore
    from public_procurement.investigation.research_api import router

    app = FastAPI()
    app.state.research_reports = ResearchReportStore(tmp_path)
    app.include_router(router)
    response = TestClient(app).get("/api/v1/investigation/private-market")
    assert response.status_code == 200
    assert response.json()["reports"] == []
    assert list(tmp_path.iterdir()) == []


def test_ambiguous_currency_not_assumed_cop():
    assert not observe(product(), result(snippet="$2.000.000")).valid_for_benchmark


def test_multiple_models_not_silently_selected():
    assert observe(product(), result(title="Samsung 58U8000H o 65U8000H")).match_level == "reject"


def test_failed_search_is_recorded_without_signal():
    search = Mock()
    search.search.side_effect = TimeoutError("ignored provider diagnostics")
    report = run_benchmark(product(), search, NOW)
    assert report["errors"] == [{"code": "market_search_failed", "error_type": "TimeoutError"}]
    assert report["signal"] is None
    assert report["benchmark"]["benchmark_status"] == "insufficient_market_evidence"
