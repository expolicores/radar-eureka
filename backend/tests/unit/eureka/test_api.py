import uuid
from unittest.mock import Mock

from public_procurement.eureka.api import get_eureka_queries
from public_procurement.eureka.services import EurekaHttpQueries

from .test_details import covarachia_entries, entry, setup_details


def configure(app, entries=None, state="consolidated"):
    details, stored, canonical = setup_details(
        covarachia_entries() if entries is None else entries,
        status=state,
        missing=("RUP_REQUIRED", "EXPERIENCE_REQUIRED", "DELIVERY_COUNT"),
    )
    details.opportunities.all.return_value = [stored]
    details.opportunities.get_by_id.side_effect = lambda identifier: (
        stored if identifier == stored.id else None
    )
    metadata = Mock()
    metadata.header.return_value = {
        "process_id": stored.process_id,
        "secop_id": "CO1.REQ.11172521",
        "title": "Refrigerios",
        "reference": "012-2026",
        "description": "DESCRIPCIÓN ORIGINAL; línea 1\nlínea 2",
        "source_url": "https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.11026997",
        "entity": "San Luis Beltrán",
        "department": "Boyacá",
        "municipality": "Covarachía",
        "budget": 2080000,
        "published_at": "2026-10-07",
    }
    service = EurekaHttpQueries(details, metadata)
    app.dependency_overrides[get_eureka_queries] = lambda: service
    return stored, canonical, service


def test_http_list_pagination_filters_and_no_full_text(app, client):
    stored, canonical, _ = configure(app)
    response = client.get(
        "/api/eureka/opportunities?priority=high&department=boyaca&category=packaged_food&review_required=false"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["opportunity_id"] == str(stored.id)
    assert data["items"][0]["score"] == 65
    assert data["items"][0]["budget"] == 2080000
    assert data["items"][0]["reference"] == "012-2026"
    assert data["items"][0]["description"] == "DESCRIPCIÓN ORIGINAL; línea 1\nlínea 2"
    assert data["items"][0]["source_url"].endswith("noticeUID=CO1.NTC.11026997")
    assert "evidence_text" not in response.text
    assert client.get("/api/eureka/opportunities?priority=low").json()["total"] == 0
    assert client.get("/api/eureka/opportunities?page=2&page_size=1").json()["items"] == []
    assert client.get("/api/eureka/opportunities?page_size=101").status_code == 400
    canonical.run.assert_not_called()


def test_http_detail_reuses_read_model_and_distinguishes_unknown(app, client):
    stored, canonical, _ = configure(app)
    response = client.get(f"/api/eureka/opportunities/{stored.id}")
    assert response.status_code == 200
    assert response.json()["opportunity"]["reference"] == "012-2026"
    assert response.json()["opportunity"]["description"] == "DESCRIPCIÓN ORIGINAL; línea 1\nlínea 2"
    details = response.json()["details"]
    assert details["score"] == 65
    assert details["priority"] == "high"
    assert details["commercial_profile"]["guarantee_required"] == "not_required"
    assert details["commercial_profile"]["rup_required"] == "unknown"
    assert len(details["commercial"]["products"]) == 2
    assert details["commercial"]["purchase_items"][0]["value"]["quantity"] == 400
    canonical.extract.assert_not_called()
    assert client.get(f"/api/eureka/opportunities/{uuid.uuid4()}").status_code == 404


def test_http_non_enriched_opportunity_remains_available(app, client):
    stored, _, _ = configure(app, entries=[], state="not_extracted")
    data = client.get(f"/api/eureka/opportunities/{stored.id}").json()
    assert data["details"]["enrichment_status"] == "not_extracted"
    assert data["details"]["commercial"]["products"] == []
    assert data["opportunity"]["budget"] == 2080000


def test_detail_exposes_metadata_only_alert_without_reenrichment(app, client):
    stored, canonical, service = configure(app, entries=[], state="not_extracted")
    service.radar = Mock()
    service.radar.alert_for_opportunity.return_value = {
        "evidence_level": "metadata_only",
        "document_status": "unavailable",
    }
    response = client.get(f"/api/eureka/opportunities/{stored.id}")
    assert response.status_code == 200
    assert response.json()["opportunity"]["evidence_level"] == "metadata_only"
    assert response.json()["opportunity"]["document_status"] == "unavailable"
    assert response.json()["opportunity"]["review_required"] is True
    assert response.json()["opportunity"]["score"] == 65
    canonical.run.assert_not_called()


def test_http_conflict_never_selects_metadata_budget_instead(app, client):
    stored, _, _ = configure(
        app, [entry("BUDGET_COP", None, "conflict", [{"value": 123}])], state="conflict"
    )
    data = client.get(f"/api/eureka/opportunities/{stored.id}").json()
    assert data["details"]["review_required"]
    assert data["opportunity"]["budget"] is None
    assert data["details"]["quality"]["conflicts"][0]["candidates"] == [{"value": 123}]


def test_http_evidence_checks_membership_and_preserves_locator(app, client):
    stored, canonical, service = configure(app)
    detail = service.detail(stored.id)
    identifier = detail["details"]["evidence"]["commercial.products"][0]["canonical_fact_id"]
    canonical.evidence.return_value = [
        {
            "structured_fact_id": str(uuid.uuid4()),
            "document_version_id": str(uuid.uuid4()),
            "content_fragment_id": None,
            "evidence_text": "JUGO HIT X 200 ml",
            "source_locator": {
                "sources": [{"original_name": "Estudios.pdf", "locator": {"page_number": 3}}]
            },
            "rule_name": "product",
            "rule_version": "v1",
        }
    ]
    response = client.get(
        f"/api/eureka/opportunities/{stored.id}/evidence?canonical_fact_id={identifier}"
    )
    assert response.status_code == 200
    assert response.json()[0]["source_locator"]["sources"][0]["locator"]["page_number"] == 3
    assert response.json()[0]["confidence"] == "0.8"
    assert (
        client.get(
            f"/api/eureka/opportunities/{stored.id}/evidence?canonical_fact_id={uuid.uuid4()}"
        ).status_code
        == 404
    )
