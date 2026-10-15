import uuid
from unittest.mock import Mock

from public_procurement.notifications.api import get_queries
from public_procurement.notifications.services import NotificationSchemaPendingError


def test_read_api_validation_and_no_dispatch(app, client):
    query = Mock()
    query.listing.return_value = {"items": [], "total": 0, "page": 1, "page_size": 25, "counts": {}}
    app.dependency_overrides[get_queries] = lambda: query
    assert client.get("/api/eureka/notifications").status_code == 200
    assert client.get("/api/eureka/notifications?status=invalid").status_code in (400, 422)
    assert client.get("/api/eureka/notifications?page_size=101").status_code in (400, 422)
    assert client.get("/api/eureka/notifications?recipient=invalid").status_code == 422
    assert (
        client.get("/api/eureka/notifications?created_from=2026-10-14T00:00:00").status_code == 422
    )
    assert client.post("/api/eureka/notifications").status_code == 405
    query.detail.side_effect = LookupError("No encontrada")
    assert client.get("/api/eureka/notifications/" + str(uuid.uuid4())).status_code == 404


def test_migration_pending_is_controlled(app, client):
    query = Mock()
    query.listing.side_effect = NotificationSchemaPendingError("Migración pendiente")
    app.dependency_overrides[get_queries] = lambda: query
    assert client.get("/api/eureka/notifications").status_code == 503
