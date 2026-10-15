import uuid
from unittest.mock import Mock

from public_procurement.eureka.api import get_radar_queries
from public_procurement.eureka.services import RadarHttpQueries


def test_empty_lists_validation_and_missing_resources(app, client):
    repository = Mock()
    repository.alerts.return_value = repository.runs.return_value = {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 25,
    }
    repository.get_alert.side_effect = repository.get_run.side_effect = LookupError("No encontrado")
    app.dependency_overrides[get_radar_queries] = lambda: repository
    assert client.get("/api/eureka/alerts").json()["total"] == 0
    assert client.get("/api/eureka/radar-runs").json()["items"] == []
    assert client.get("/api/eureka/alerts?page_size=101").status_code == 400
    assert client.get(f"/api/eureka/alerts/{uuid.uuid4()}").status_code == 404
    assert client.get(f"/api/eureka/radar-runs/{uuid.uuid4()}").status_code == 404


def test_historical_alert_is_served_without_reenrichment(app, client):
    repository = Mock()
    alert = {
        "id": str(uuid.uuid4()),
        "opportunity_id": str(uuid.uuid4()),
        "run_id": str(uuid.uuid4()),
        "alert_type": "new_opportunity",
        "rule_version": "v1",
        "created_at": "2026-10-13T15:00:00Z",
        "priority": "high",
        "review_required": True,
        "reasons": [{"code": "score_reference", "value": 20, "mandatory_gate": False}],
        "snapshot": {"score": 20, "products": [{"name": "jugo hit"}]},
    }
    repository.alerts.return_value = {"items": [alert], "total": 1, "page": 1, "page_size": 25}
    app.dependency_overrides[get_radar_queries] = lambda: repository
    response = client.get("/api/eureka/alerts")
    assert response.status_code == 200
    assert response.json()["items"][0]["snapshot"]["score"] == 20
    repository.alerts.assert_called_once_with(1, 25)


def test_alert_presentation_reuses_ingestion_without_changing_snapshot(app, client):
    repository, metadata = Mock(), Mock()
    identifier = uuid.uuid4()
    snapshot = {"secop_id": "CO1.REQ.11192009", "score": 65, "title": "Título histórico"}
    alert = {
        "id": identifier,
        "opportunity_id": uuid.uuid4(),
        "run_id": uuid.uuid4(),
        "alert_type": "new_opportunity",
        "rule_version": "v1",
        "created_at": "2026-10-15T15:00:00Z",
        "priority": "high",
        "review_required": True,
        "reasons": [],
        "snapshot": snapshot,
    }
    metadata.header.return_value = {
        "secop_id": "CO1.REQ.11192009",
        "reference": "RESO-006-2026",
        "description": "DESCRIPCIÓN; original\nSEGUNDA LÍNEA",
        "source_url": "https://community.secop.gov.co/Public/?noticeUID=original",
    }
    repository.alerts.return_value = {"items": [alert], "total": 1, "page": 1, "page_size": 25}
    repository.get_alert.return_value = alert
    queries = RadarHttpQueries(repository, metadata)
    app.dependency_overrides[get_radar_queries] = lambda: queries
    for url in ("/api/eureka/alerts", f"/api/eureka/alerts/{identifier}"):
        data = client.get(url).json()
        item = data["items"][0] if "items" in data else data
        assert item["snapshot"] == snapshot
        assert item["process"] == metadata.header.return_value
    assert "process" not in alert
    metadata.header.assert_called_with("CO1.REQ.11192009")
    metadata.header.side_effect = ValueError("Metadata ausente")
    assert queries.get_alert(identifier)["process"] is None
    assert queries.get_alert(identifier)["snapshot"] == snapshot
