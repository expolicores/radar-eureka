from copy import deepcopy

from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.investigation.market_benchmark.presentation import present_market_reports
from public_procurement.investigation.market_benchmark.service import MarketReportStore
from public_procurement.investigation.research import ResearchReportStore
from public_procurement.investigation.research_api import router


def receipt():
    return {
        "product": {"brand": "Samsung", "model": "58U8000H"},
        "public_product": {
            "public_process_code": "MC-070-2026",
            "public_price_stage": "offer",
            "public_evidence_ref": "document:p339",
            "public_unit_price": "3767123",
            "document_heading_process_code": "MC-028-2026",
            "evidence_warnings": ["document_process_reference_mismatch"],
            "raw": {"api_key": "DO-NOT-EXPOSE"},
        },
        "public_evidence_status": "documented_unconfirmed_offer",
        "comparison": None,
        "signal": None,
        "benchmark": {
            "benchmark_status": "insufficient_market_evidence",
            "median_price": "2569900",
            "valid_observations_count": 2,
            "observations": [
                {
                    "retailer": "store",
                    "valid_for_benchmark": False,
                    "match_level": "partial",
                    "price": "2270000",
                    "url": "https://shop.co/item?api_key=DO-NOT-EXPOSE&id=1",
                    "evidence": {"api_key": "DO-NOT-EXPOSE"},
                    "provider_metadata": {"raw": "DO-NOT-EXPOSE"},
                }
            ],
        },
        "shopping_discovery": {
            "source_status": "degraded",
            "requests": [{"secret": "DO-NOT-EXPOSE"}],
            "request_count": 5,
        },
        "errors": [{"code": "rate_limited", "http_status": 429, "raw": "DO-NOT-EXPOSE"}],
    }


def test_presentation_preserves_decisions_prices_conflict_without_raw_or_recalculating():
    raw = receipt()
    original = deepcopy(raw)
    view = present_market_reports({"reports": [raw]})["reports"][0]
    assert raw == original
    assert view["comparison"] is None
    assert view["signal"] is None
    assert view["benchmark"]["median_price"] == "2569900"
    assert view["benchmark"]["observations"][0]["valid_for_benchmark"] is False
    assert view["public_product"]["document_heading_process_code"] == "MC-028-2026"
    assert view["benchmark"]["observations"][0]["url"] == "https://shop.co/item?id=1"
    assert "DO-NOT-EXPOSE" not in str(view)
    assert (
        view["report_id"] == present_market_reports({"reports": [raw]})["reports"][0]["report_id"]
    )
    another_capture = deepcopy(raw)
    another_capture["benchmark"]["captured_at"] = "2026-11-06T01:00:00Z"
    assert (
        view["report_id"]
        != present_market_reports({"reports": [another_capture]})["reports"][0]["report_id"]
    )


def test_existing_endpoint_returns_only_read_projection_without_altering_receipt(tmp_path):
    store = MarketReportStore(tmp_path)
    store.write(receipt())
    before = store.path.read_bytes()
    app = FastAPI()
    app.state.research_reports = ResearchReportStore(tmp_path)
    app.include_router(router)
    response = TestClient(app).get("/api/v1/investigation/private-market")
    assert response.status_code == 200
    assert "DO-NOT-EXPOSE" not in response.text
    assert response.json()["reports"][0]["public_evidence_status"] == "documented_unconfirmed_offer"
    assert store.path.read_bytes() == before


def test_invalid_receipt_returns_safe_error(tmp_path):
    store = MarketReportStore(tmp_path)
    store.path.write_text("invalid-json", encoding="utf8")
    app = FastAPI()
    app.state.research_reports = ResearchReportStore(tmp_path)
    app.include_router(router)
    response = TestClient(app).get("/api/v1/investigation/private-market")
    assert response.status_code == 503
    assert "traceback" not in response.text.lower()
