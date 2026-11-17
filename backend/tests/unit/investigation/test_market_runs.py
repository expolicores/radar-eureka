import copy
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.investigation.economic_cycle import extract_rows, reconstruct
from public_procurement.investigation.market_benchmark.schemas import PublicOffer
from public_procurement.investigation.market_benchmark.serpapi_adapter import SerpApiShoppingAdapter
from public_procurement.investigation.market_benchmark.service import (
    MarketReportStore,
    run_benchmark,
)
from public_procurement.investigation.market_runs import (
    ExistingMarketPipeline,
    ManualMarketRunner,
    MarketRunRequest,
)
from public_procurement.investigation.private_market_pipeline import (
    DateMarketPipeline,
    private_market_candidates,
)
from public_procurement.investigation.research_api import router


def product():
    return PublicOffer(
        brand="Samsung",
        model="58U8000H",
        canonical_model="UN58U8000H",
        size="58 pulgadas",
        product_type="televisor",
        public_process_identity="CO1.REQ.11253117",
        public_process_code="MC-070-2026",
        public_entity="Universidad del Atlantico",
        public_product_description="TV Samsung 58U8000H",
        public_unit_price="3767123",
        public_evidence_ref="fixture:878001221:p339",
        public_document="OFERTA ECONOMICA MC-070-2026.pdf",
        public_page_reference="p339/340",
        price_origin="explicit",
        quantity="1",
        supplier="TEAM IT",
        price_tax_basis="excludes_vat",
        document_heading_process_code="MC-028-2026",
    )


def benchmark(p):
    fixture = json.loads(
        (Path(__file__).resolve().parents[2] / "fixtures/serpapi_samsung.json").read_text(
            encoding="utf8"
        )
    )

    class API:
        def search(self, params):
            return copy.deepcopy(
                fixture["shopping" if params["engine"] == "google_shopping" else "product"]
            )

    return run_benchmark(
        p, shopping=SerpApiShoppingAdapter(API()), now=datetime(2026, 11, 5, tzinfo=UTC)
    )


DATES = {"start_date": "2026-10-01", "end_date": "2026-10-31"}


def public_report():
    fragment = {
        "id": "fragment",
        "document_version_id": "version",
        "original_name": "OFERTA ECONOMICA.pdf",
        "text": "Descripcion Cantidad Valor Unitario Valor Total\n"
        "1 Televisor Samsung 58U8000H 58 pulgadas LED 4K Smart TV UNIDAD 1 3.767.123 3.767.123",
        "source_locator": {
            "page_number": 3,
            "input_sha256": "abc",
            "extraction_method": "native_pdf_text",
        },
    }
    process = {
        "id": "CO1.REQ.NEW",
        "reference": "NEW-DISCOVERED",
        "entity": "Entidad nueva",
        "contracts": [],
        "documents": [],
        "products": [],
        "published_at": "2026-10-01",
    }
    cycle = reconstruct(process, extract_rows(fragment), [])
    process["economic_cycle"] = cycle
    return {
        "processes": [process],
        "summary": {},
        "comparisons": [],
        "signals": [],
        "window_start": "2026-10-01",
        "window_before": "2026-11-01",
    }


def client_for(runner):
    app = FastAPI()
    app.state.manual_market_runner = runner
    app.state.research_reports = Mock()
    app.include_router(router)
    return TestClient(app)


def wait_done(runner, identifier):
    until = time.monotonic() + 4
    while time.monotonic() < until:
        run = runner.get(identifier)
        if run.status in {"completed", "completed_with_warnings", "failed"}:
            return run
        time.sleep(0.01)
    pytest.fail("Worker did not finish")


def test_date_run_without_prior_public_run_produces_new_candidates_and_benchmark(tmp_path):
    entered, release = threading.Event(), threading.Event()
    calls = []

    def public(window, directory, stage):
        stage("documents_extraction")
        entered.set()
        assert release.wait(4)
        assert window.model_dump(mode="json") == DATES
        return public_report()

    def market(product, directory):
        calls.append(product)
        assert (
            json.loads((directory / "input.json").read_text(encoding="utf8"))["public_price_stage"]
            == "offer"
        )
        return benchmark(product)

    runner = ManualMarketRunner(tmp_path, DateMarketPipeline(public, market))
    client = client_for(runner)
    try:
        response = client.post("/api/v1/investigation/market-runs", json=DATES)
        assert response.status_code == 202
        identifier = response.json()["run_id"]
        assert response.json()["run_type"] == "state_vs_private_market"
        assert entered.wait(2)
        assert (
            client.get(f"/api/v1/investigation/market-runs/{identifier}").json()["stage"]
            == "documents_extraction"
        )
        assert (
            client.post("/api/v1/investigation/market-runs", json=DATES).json()["run_id"]
            == identifier
        )
        assert (
            client.post(
                "/api/v1/investigation/market-runs", json={**DATES, "end_date": "2026-10-30"}
            ).status_code
            == 409
        )
        release.set()
        done = wait_done(runner, identifier)
        assert done.status == "completed_with_warnings"
        assert done.counts["private_market_candidates"] == 1
        assert done.counts["private_market_observations_valid"] == 2
        assert done.counts["comparisons_generated"] == 0
        assert done.counts["signals_generated"] == 0
        result = client.get(f"/api/v1/investigation/private-market?run_id={identifier}").json()[
            "reports"
        ][0]
        assert result["public_product"]["public_process_code"] == "NEW-DISCOVERED"
        assert result["public_evidence_status"] == "documented_unconfirmed_offer"
        assert result["comparison"] is None
        assert result["signal"] is None
        assert "evidence" not in result["benchmark"]["observations"][0]
        public_view = client.get(f"/api/v1/investigation/market-runs/{identifier}/research").json()
        assert "market_reports" not in public_view
        assert public_view["private_market_candidates"][0]["status"] == "eligible"
        assert len(calls) == 1
        assert not (tmp_path / "latest.json").exists()
        assert not MarketReportStore(tmp_path).path.exists()
        assert (
            ManualMarketRunner(tmp_path, Mock()).get(identifier).status == "completed_with_warnings"
        )
    finally:
        release.set()
        runner.close()


@pytest.mark.parametrize(
    "body",
    [
        {"product_id": "a" * 32},
        {**DATES, "model": "made-up"},
        {**DATES, "path": "secret"},
        {**DATES, "source": "new-provider"},
        {"start_date": "2026-01-01", "end_date": "2026-10-31"},
        {"start_date": "2026-11-01", "end_date": "2026-10-31"},
    ],
)
def test_private_request_dates_only_and_60_day_window(tmp_path, body):
    pipeline = Mock()
    client = client_for(ManualMarketRunner(tmp_path, pipeline))
    assert client.post("/api/v1/investigation/market-runs", json=body).status_code == 422
    pipeline.assert_not_called()


def test_unknown_run_does_not_fall_back_to_published_benchmark(tmp_path):
    MarketReportStore(tmp_path).write(benchmark(product()))
    client = client_for(ManualMarketRunner(tmp_path, Mock()))
    assert client.get(f"/api/v1/investigation/private-market?run_id={uuid4()}").status_code == 404
    assert client.get(f"/api/v1/investigation/market-runs/{uuid4()}/research").status_code == 404


def test_failure_keeps_prior_results_and_hides_provider_secrets(tmp_path):
    MarketReportStore(tmp_path).write(benchmark(product()))
    previous = MarketReportStore(tmp_path).path.read_bytes()
    runner = ManualMarketRunner(tmp_path, Mock(side_effect=RuntimeError("TOKEN=secret")))
    done = wait_done(runner, runner.start(MarketRunRequest(**DATES)).run_id)
    assert done.status == "failed"
    assert done.errors == ["pipeline_failed"]
    assert "secret" not in done.model_dump_json()
    assert MarketReportStore(tmp_path).path.read_bytes() == previous


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("identity", "unresolved_product_identity"),
        ("conflict", "conflicting_or_uncertain_product_identity"),
        ("price", "no_documented_public_unit_price"),
        ("provenance", "missing_document_page_provenance"),
        ("budget", "no_documented_public_unit_price"),
    ],
)
def test_ineligible_or_pending_candidates_never_call_market(tmp_path, change, reason):
    report = public_report()
    item = report["processes"][0]["economic_cycle"]["products"][0]
    if change == "identity":
        item["model"] = None
    if change == "conflict":
        item["fields"]["model"]["status"] = "conflicting"
    if change in {"price", "budget"}:
        item["fields"]["offer_unit_price"]["value"] = None
    if change == "provenance":
        item["fields"]["offer_unit_price"]["alternatives"][0]["evidence"][0]["source_page"] = None
    market = Mock()
    result = DateMarketPipeline(lambda *_: report, market)(
        MarketRunRequest(**DATES), tmp_path, lambda _: None
    )
    market.assert_not_called()
    assert reason in result["private_market_candidates"][0]["reasons"]
    assert result["summary"]["private_market_candidates"] == 0
    assert result["market_reports"] == []
    assert "no_eligible_private_market_products" in result["run_warnings"]


def test_candidate_mapping_preserves_offer_and_provenance_and_deduplicates():
    report = public_report()
    p = report["processes"][0]
    p["economic_cycle"]["products"] *= 2
    candidates = private_market_candidates(report)
    assert len(candidates) == 1
    c = candidates[0]
    assert c.public_evidence_status == "documented_unconfirmed_offer"
    assert c.public_product["public_price_stage"] == "offer"
    assert c.public_product["public_price_date"] is None
    assert c.public_product["public_page_reference"] == "3"
    assert c.evidence[0]["input_sha256"] == "abc"


@pytest.mark.parametrize(
    ("column", "expected"),
    [
        ("contract_unit_price", "contract_confirmed"),
        ("awarded_unit_price", "awarded_confirmed"),
        ("accepted_offer_unit_price", "accepted_offer_confirmed"),
    ],
)
def test_verified_cycle_price_stage_is_preserved_not_inferred_from_filename(column, expected):
    report = public_report()
    item = report["processes"][0]["economic_cycle"]["products"][0]
    field = item["fields"]["offer_unit_price"]
    item["purchase_price"] = {
        "column": column,
        "value": field["value"],
        "evidence": field["alternatives"],
        "origin": "explicit",
    }
    item["purchase_date"] = "2026-10-18"
    candidate = private_market_candidates(report)[0]
    assert candidate.status == "eligible"
    assert candidate.public_evidence_status == expected
    assert candidate.public_product["public_price_date"] == "2026-10-18T00:00:00-05:00"
    item["purchase_date"] = None
    candidate = private_market_candidates(report)[0]
    assert candidate.status == "pending_review"
    assert candidate.reasons == ["missing_verified_purchase_date"]


def test_same_identity_reuses_market_observations_but_not_public_evidence(tmp_path):
    report = public_report()
    second = copy.deepcopy(report["processes"][0])
    second["id"], second["reference"] = "CO1.REQ.OTHER", "OTHER"
    report["processes"].append(second)
    market = Mock(side_effect=lambda p, _: benchmark(p))
    result = DateMarketPipeline(lambda *_: report, market)(
        MarketRunRequest(**DATES), tmp_path, lambda _: None
    )
    assert market.call_count == 1
    assert result["summary"]["private_market_products_processed"] == 2
    assert result["private_market_candidates"][1]["reused_market_from"]
    assert (
        result["market_reports"][1]["public_product"]["public_process_identity"] == "CO1.REQ.OTHER"
    )
    assert all(r["signal"] is None for r in result["market_reports"])


def test_isolated_private_failure_completes_and_preserves_public_evidence(tmp_path):
    pipeline = DateMarketPipeline(
        lambda *_: public_report(), Mock(side_effect=TimeoutError("SECRET"))
    )
    runner = ManualMarketRunner(tmp_path, pipeline)
    done = wait_done(runner, runner.start(MarketRunRequest(**DATES)).run_id)
    assert done.status == "completed_with_warnings"
    assert done.counts["private_market_products_failed"] == 1
    result = runner.research_result(done.run_id)
    assert result["processes"][0]["id"] == "CO1.REQ.NEW"
    assert result["private_market_candidates"][0]["market_status"] == "failed"
    assert "SECRET" not in json.dumps(result)


def test_public_evidence_branch_skips_state_comparison(monkeypatch, tmp_path):
    from public_procurement.investigation import economic_cycle

    monkeypatch.setattr(
        economic_cycle,
        "compare_public_purchases",
        Mock(side_effect=AssertionError("not this branch")),
    )
    report = {
        "comparison_policy": "research-60d-v1",
        "window_start": "2026-10-01",
        "window_before": "2026-11-01",
        "processes": [],
    }
    result = economic_cycle.build_cycles(report, {}, compare_state=False)
    assert result["signals"] == []
    assert result["comparisons"] == []


def test_pipeline_invokes_existing_auto_cli_with_only_server_owned_input(tmp_path, monkeypatch):
    import importlib.util

    calls = []

    class Loader:
        def create_module(self, spec):
            return None

        def exec_module(self, module):
            module.main = lambda argv: calls.append(argv)

    original = importlib.util.spec_from_file_location
    monkeypatch.setattr(
        importlib.util,
        "spec_from_file_location",
        lambda name, path: original(name, path, loader=Loader()),
    )
    expected = benchmark(product())
    (tmp_path / "market_benchmark.json").write_text(json.dumps(expected), encoding="utf8")
    assert ExistingMarketPipeline()(product(), tmp_path) == expected
    assert calls == [
        ["--public-product", str(tmp_path / "input.json"), "--output-directory", str(tmp_path)]
    ]
