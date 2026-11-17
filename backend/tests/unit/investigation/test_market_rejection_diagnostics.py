import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

from public_procurement.investigation.market_benchmark.diagnostics import rejected_diagnostic


def rejected(url="https://www.falabella.com.co/category/tv", **overrides):
    return {
        "source_type": "web_search",
        "url": url,
        "page_type": "category_page",
        "match_level": "reject",
        "match_reason": "different_model",
        "price": None,
        "valid_for_benchmark": False,
        "notes": ["commercial_context_not_observed"],
        "evidence": {
            "query": 'site:falabella.com.co "UN58U8000H"',
            "title": "Samsung televisores",
            "snippet": "Catálogo general",
        },
        **overrides,
    }


def test_fields_and_reasons_are_projected_from_stored_decisions_without_mutation():
    report = {"benchmark": {"observations": [rejected()], "duplicates": []}}
    before = json.dumps(report)
    diagnostic = rejected_diagnostic(report)
    row = diagnostic["rejected_candidates"][0]
    assert set(row) == {
        "query",
        "domain",
        "url",
        "title",
        "snippet",
        "page_type",
        "rejection_reason",
        "extracted_mco_id",
        "price_detected",
        "verification_status",
        "price_evidence_level",
        "extraction_method",
    }
    assert row["domain"] == "www.falabella.com.co"
    assert row["snippet"] == "Catálogo general"
    assert "different_model" in row["rejection_reason"]
    assert "candidate_page_not_concrete" in row["rejection_reason"]
    assert row["price_detected"] is None
    assert json.dumps(report) == before


def test_preferred_domains_first_and_listing_id_from_url():
    rows = [
        rejected("https://other.example/page"),
        rejected("https://articulo.mercadolibre.com.co/MCO-123-tv"),
    ]
    d = rejected_diagnostic({"benchmark": {"observations": rows}})
    assert d["rejected_candidates"][0]["extracted_mco_id"] == "MCO123"
    assert d["unique_rejected_urls"] == 2


def test_valid_and_api_rows_excluded_duplicates_explicit():
    duplicate = rejected(
        page_type="product_page",
        match_level="high",
        price="2000000",
        duplicate_of="first",
        notes=[],
    )
    d = rejected_diagnostic(
        {
            "benchmark": {
                "observations": [
                    rejected(valid_for_benchmark=True),
                    rejected(source_type="marketplace_api"),
                ],
                "duplicates": [duplicate],
            }
        }
    )
    assert d["rejected_records"] == 1
    assert d["rejected_candidates"][0]["rejection_reason"] == "duplicate_offer"
    assert d["rejected_candidates"][0]["price_detected"] == "2000000"


def test_offline_cli_never_constructs_provider_or_writes_receipt(tmp_path, monkeypatch, capsys):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"benchmark": {"observations": [rejected()]}}), encoding="utf8")
    before = receipt.read_bytes()
    path = Path(__file__).resolve().parents[3] / "scripts" / "eureka_market_benchmark.py"
    spec = importlib.util.spec_from_file_location("rejection_cli", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    provider = Mock(side_effect=AssertionError("No provider allowed"))
    monkeypatch.setattr(module, "FoundryMarketPriceScout", provider)
    monkeypatch.setattr(module, "Settings", provider)
    monkeypatch.setattr("sys.argv", ["market", "--diagnose-receipt", str(receipt)])
    module.main()
    assert json.loads(capsys.readouterr().out)["rejected_records"] == 1
    provider.assert_not_called()
    assert receipt.read_bytes() == before
    assert list(tmp_path.iterdir()) == [receipt]
