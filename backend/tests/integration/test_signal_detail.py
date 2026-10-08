import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from public_procurement.comparison.services import (
    SignalQueryService,
    build_signal_query_service,
)
from public_procurement.entrypoints.api.app import create_app
from public_procurement.shared.config import Settings
from public_procurement.shared.persistence import create_session_factory

pytestmark = pytest.mark.integration

PROHIBITED_TERMS = ("sobreprecio", "corrupción", "corrupcion", "fraude", "hallazgo fiscal")


@pytest.fixture(scope="module")
def service(seeded_engine: Engine) -> SignalQueryService:
    return build_signal_query_service(create_session_factory(seeded_engine))


@pytest.fixture(scope="module")
def client(seeded_engine: Engine, database_settings: Settings) -> TestClient:
    return TestClient(create_app(database_settings))


def test_signal_detail_reproduces_the_current_comparison_when_code_exists(
    service: SignalQueryService,
) -> None:
    # Arrange / Act
    detail = service.get_signal("SG-2026-0142")
    # Assert
    assert detail is not None
    signal = detail.signal
    assert (signal.purchase_reference, signal.quantity) == ("CO1.PCCNTR.0000142", 8)
    assert detail.q1_cop <= signal.median_cop <= detail.q3_cop < detail.threshold_cop
    assert detail.threshold_cop < signal.unit_price_cop
    assert detail.comparables
    assert all(c.unit_price_cop > 0 and c.reference for c in detail.comparables)
    assert all(o.method == "simulated" for o in detail.market_observations)
    assert 100 - sum(p.points for p in detail.penalties) == signal.confidence_score
    assert detail.config_version_id == "analitica-v1"


def test_signal_detail_is_none_when_code_does_not_exist(service: SignalQueryService) -> None:
    # Arrange / Act
    detail = service.get_signal("SG-2099-0001")
    # Assert
    assert detail is None


def test_signal_endpoint_returns_404_problem_details_when_code_does_not_exist(
    client: TestClient,
) -> None:
    # Arrange / Act
    response = client.get("/api/v1/signals/SG-2099-0001")
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Señal no encontrada"


def test_purchase_detail_includes_current_result_per_item_when_purchase_has_a_signal(
    client: TestClient,
) -> None:
    # Arrange
    purchase_id = client.get("/api/v1/signals/SG-2026-0142").json()["signal"]["purchase_id"]
    # Act
    items = client.get(f"/api/v1/purchases/{purchase_id}").json()["items"]
    # Assert
    tv, accessory = items
    assert (tv["comparison_outcome"], tv["signal_code"]) == ("signal", "SG-2026-0142")
    assert (accessory["comparison_outcome"], accessory["signal_code"]) == (None, None)


def test_detail_responses_never_use_accusatory_terms_when_returned(client: TestClient) -> None:
    # Arrange
    detail = client.get("/api/v1/signals/SG-2026-0142")
    purchase_id = detail.json()["signal"]["purchase_id"]
    # Act
    text = (detail.text + client.get(f"/api/v1/purchases/{purchase_id}").text).lower()
    # Assert
    assert not [term for term in PROHIBITED_TERMS if term in text]
