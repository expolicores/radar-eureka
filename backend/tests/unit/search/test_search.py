import copy
import uuid
from datetime import date
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from public_procurement.search.api import queries
from public_procurement.search.domain.query import SearchQuery, modality, normalize, rank, tsquery
from public_procurement.search.services import SearchService


def record(name="jugo hit", opportunity=True):
    return {
        "metadata": {
            "id": uuid.uuid4(),
            "id_del_proceso": "CO1.TEST",
            "title": "Refrigerios",
            "description": "",
            "entity_name": "Escuela",
            "department": "Boyacá",
            "municipality": "Covarachía",
            "published_on": date(2026, 10, 7),
            "base_price_cop": 2080000,
            "category_code": "V1.50192703",
            "source_url": None,
        },
        "opportunity": {
            "id": str(uuid.uuid4()),
            "score": 65,
            "priority": "high",
            "categories": ["packaged_food"],
            "has_alert": False,
        }
        if opportunity
        else None,
        "canonical": [
            {
                "id": str(uuid.uuid4()),
                "type": "PRODUCT",
                "status": "confirmed",
                "value": {"name": name},
            }
        ],
        "structured": [],
        "text": [],
    }


def service(rows):
    source = Mock()
    ids = {row["metadata"]["id"] for row in rows}
    source.eligible.side_effect = lambda q, found=None: ids if found is None else ids & found
    source.candidates.return_value = ids
    source.batch.side_effect = lambda identifiers, expression: [
        r for r in rows if r["metadata"]["id"] in identifiers
    ]
    return SearchService(
        source,
        {"aliases": {"televisor": ["tv"]}, "categories": {"packaged_food": "Alimentos"}},
        {"batch_size": 2, "snippet_chars": 320, "max_reasons": 5, "version": "search-v1"},
    )


@pytest.mark.parametrize("q", ["JÚGO HIT", "jugo hit", "jugo-hit"])
def test_a_exact_product_normalization(q):
    result = service([record()]).search(SearchQuery(q=q))["items"][0]
    assert result["match_type"] == "canonical_match"
    assert result["search_rank"] == 5
    assert result["score"] == 65


def test_b_alias():
    result = service([record("tv")]).search(SearchQuery(q="televisor"))["items"][0]
    assert result["match_mode"] == "explicit_alias"
    assert result["search_rank"] == 4


def test_c_current_canonical_suppresses_structured_same_meaning():
    row = record("televisor")
    row["structured"] = [{"fact_type": "product", "string_value": "jugo hit"}]
    assert service([row]).search(SearchQuery(q="jugo hit"))["total"] == 0


def test_d_structured_fallback():
    row = record()
    row["canonical"] = []
    row["structured"] = [
        {
            "fact_type": "product",
            "normalized_value": {"name": "jugo hit"},
            "string_value": "jugo hit",
            "numeric_value": None,
            "source_locator": {"sources": [{"content_fragment_id": "fragment"}]},
        }
    ]
    result = service([row]).search(SearchQuery(q="jugo hit"))["items"][0]
    assert result["match_type"] == "structured_match"


def test_e_metadata_without_eureka_and_no_writes():
    row = record(opportunity=False)
    row["canonical"] = []
    instance = service([row])
    result = instance.search(SearchQuery(q="refrigerios"))["items"][0]
    assert result["match_type"] == "metadata_match"
    assert result["detail_url"] is None
    assert {call[0] for call in instance.source.mock_calls} <= {"eligible", "candidates", "batch"}


@pytest.mark.parametrize("method", ["ocr_text", "native_pdf_text"])
def test_f_g_native_ocr_same_rank_and_provenance(method):
    row = record()
    row["canonical"] = []
    row["text"] = [
        {
            "id": "fragment",
            "text": "JUGO HIT 200 ML",
            "locator": {"page_number": 3, "extraction_method": method},
        }
    ]
    result = service([row]).search(SearchQuery(q="jugo hit"))["items"][0]
    assert result["search_rank"] == 2
    assert result["matches"][0]["locator"]["extraction_method"] == method


def test_h_budget_and_unspsc_structured_filters():
    instance = service([record()])
    assert (
        instance.search(SearchQuery(budget_min=2000000, budget_max=3000000, unspsc="50192703"))[
            "total"
        ]
        == 1
    )
    assert instance.search(SearchQuery(budget_max=100))["total"] == 0
    assert instance.search(SearchQuery(unspsc="11111111"))["total"] == 0


def test_i_brand_is_explicit_text_never_inferred():
    instance = service([record("impresora laser")])
    assert instance.search(SearchQuery(brand="epson"))["total"] == 0
    assert service([record("impresora epson")]).search(SearchQuery(brand="epson"))["total"] == 1


def test_j_k_filters_only_pagination_dedup_and_score_does_not_rank():
    rows = [record("tv"), record("jugo hit")]
    rows[0]["opportunity"]["score"] = 100
    instance = service(rows)
    assert instance.search(SearchQuery(page=100))["items"] == []
    assert instance.search(SearchQuery(page_size=1))["total"] == 2
    result = instance.search(SearchQuery(q="jugo hit"))
    assert result["items"][0]["score"] == 65
    assert len({r["process_id"] for r in result["items"]}) == result["total"]


def test_l_full_text_requires_database_match_flag():
    row = record("bien")
    row["text"] = [
        {"id": "f", "text": "suministro de televisores", "locator": {}, "_queries": ["q"]}
    ]
    result = service([row]).search(SearchQuery(q="television"))["items"][0]
    assert result["match_mode"] == "full_text"
    row["text"][0]["_queries"] = []
    assert service([row]).search(SearchQuery(q="television"))["total"] == 0


def test_m_n_validation_no_nlp_or_injected_tsquery():
    assert tsquery([normalize("x'); DROP TABLE t --")]) == "(x:* & drop:* & table:* & t:*)"
    for values in (
        {"budget_min": 2, "budget_max": 1},
        {"page": 0},
        {"page_size": 101},
        {"unspsc": "bad"},
        {"q": "!!!"},
        {"published_from": "2026-10-14", "published_to": "2026-10-07"},
    ):
        with pytest.raises(ValidationError):
            SearchQuery(**values)
    assert modality("pantalla", "televisor", {}) is None
    assert rank("canonical_match", "token_prefix", "PRODUCT") == 1


def test_read_model_does_not_mutate_input():
    row = record()
    before = copy.deepcopy(row)
    service([row]).search(SearchQuery(q="jugo hit"))
    assert row == before


def test_canonical_product_ranks_before_native_text_regardless_of_score():
    canonical = record()
    canonical["opportunity"]["score"] = 1
    text = record()
    text["canonical"] = []
    text["opportunity"]["score"] = 100
    text["text"] = [{"id": "fragment", "text": "jugo hit", "locator": {}}]
    results = service([text, canonical]).search(SearchQuery(q="jugo hit"))["items"]
    assert [r["match_type"] for r in results] == ["canonical_match", "extracted_text_match"]
    assert [r["score"] for r in results] == [1, 100]


def test_structured_budget_precedes_metadata_when_canonical_missing():
    row = record()
    row["metadata"]["base_price_cop"] = 9000000
    row["structured"] = [{"fact_type": "official_budget_cop", "numeric_value": 2080000}]
    result = service([row]).search(SearchQuery(budget_min=2000000, budget_max=3000000))
    assert result["items"][0]["budget_origin"] == "structured_match"


def test_complete_unordered_tokens_are_not_downgraded_to_prefix():
    assert modality("hit jugo", "jugo hit", {}) == "full_text"
    assert modality("jugo hit", "jugo hi", {}) == "token_prefix"


def test_api_validation_pagination_and_evidence_ownership(app, client):
    instance = Mock()
    instance.search.return_value = {
        "items": [],
        "total": 0,
        "page": 2,
        "page_size": 20,
        "duration_ms": 1,
        "ranking_version": "search-v1",
    }
    instance.evidence.return_value = []
    app.dependency_overrides[queries] = lambda: instance
    assert client.get("/api/search?page=2").status_code == 200
    assert client.get("/api/search?page_size=101").status_code in (400, 422)
    path = f"/api/search/processes/{uuid.uuid4()}/evidence"
    assert client.get(path).status_code == 422
    assert client.get(path, params={"fragment_id": str(uuid.uuid4())}).status_code == 404
