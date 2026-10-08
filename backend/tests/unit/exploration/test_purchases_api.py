import uuid
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.exploration.domain.analysis import AnalysisStatus
from public_procurement.exploration.services import PurchaseListView, PurchaseSummaryView
from public_procurement.ingestion.services import (
    PurchaseSearchCriteria,
    PurchaseSort,
    Source,
    ValueRange,
)


class RecordingExplorationService:
    """Doble del servicio: registra los criterios y devuelve una página fija."""

    def __init__(self) -> None:
        self.criteria: list[PurchaseSearchCriteria] = []
        self.has_signal: list[bool | None] = []

    def list_purchases(
        self, criteria: PurchaseSearchCriteria, has_signal: bool | None = None
    ) -> PurchaseListView:
        self.criteria.append(criteria)
        self.has_signal.append(has_signal)
        summary = PurchaseSummaryView(
            id=uuid.UUID("031fd76d-19fa-4853-9eea-457326e6d679"),
            reference="CO1.PCCNTR.0000142",
            source=Source.SECOP_II,
            entity_name="Alcaldía Municipal de San Rafael del Valle",
            entity_department="Valle del Cauca",
            supplier_name="Tecnología Andina Demo S.A.S.",
            object_description="Adquisición de televisores",
            modality="Mínima cuantía",
            total_value_cop=39_600_000,
            signed_on=date(2026, 8, 14),
            analysis_status=AnalysisStatus.PENDING_COMPARISON,
        )
        return PurchaseListView(
            items=(summary,), total=1, page=criteria.page, page_size=criteria.page_size
        )

    def get_purchase(self, purchase_id: uuid.UUID) -> None:
        return None


@pytest.fixture
def service(app: FastAPI) -> RecordingExplorationService:
    double = RecordingExplorationService()
    app.state.exploration_service = double
    return double


def test_list_purchases_uses_default_paging_and_sort_when_no_parameters(
    client: TestClient, service: RecordingExplorationService
) -> None:
    # Arrange / Act
    response = client.get("/api/v1/purchases")
    # Assert
    assert response.status_code == 200
    criteria = service.criteria[0]
    assert (criteria.page, criteria.page_size, criteria.sort) == (1, 25, PurchaseSort.SIGNED_DESC)
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["total_value_cop"] == 39_600_000
    assert body["items"][0]["analysis_status"] == "pending_comparison"


def test_list_purchases_passes_every_filter_to_the_service_when_given(
    client: TestClient, service: RecordingExplorationService
) -> None:
    # Arrange
    params = {
        "q": "san rafael",
        "source": "tvec",
        "modality": "Mínima cuantía",
        "department": "Valle del Cauca",
        "value_range": "between_20m_100m",
        "signed_from": "2026-01-01",
        "signed_to": "2026-06-30",
        "has_signal": "true",
        "sort": "value_desc",
        "page": "2",
        "page_size": "50",
    }
    # Act
    client.get("/api/v1/purchases", params=params)
    # Assert
    criteria = service.criteria[0]
    assert criteria.text == "san rafael"
    assert criteria.source is Source.TVEC
    assert criteria.department == "Valle del Cauca"
    assert criteria.value_range is ValueRange.BETWEEN_20M_100M
    assert (criteria.signed_from, criteria.signed_to) == (date(2026, 1, 1), date(2026, 6, 30))
    assert (criteria.page, criteria.page_size, criteria.sort) == (2, 50, PurchaseSort.VALUE_DESC)
    assert service.has_signal == [True]


@pytest.mark.parametrize(
    ("params", "parameter"),
    [
        ({"page_size": "500"}, "page_size"),
        ({"page": "0"}, "page"),
        ({"source": "secop_iii"}, "source"),
        ({"sort": "random"}, "sort"),
        ({"signed_from": "ayer"}, "signed_from"),
    ],
)
def test_list_purchases_returns_400_problem_details_when_parameter_is_invalid(
    client: TestClient,
    service: RecordingExplorationService,
    params: dict[str, str],
    parameter: str,
) -> None:
    # Arrange / Act
    response = client.get("/api/v1/purchases", params=params)
    # Assert
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Solicitud inválida"
    assert response.json()["detail"] == f"El parámetro «{parameter}» no es válido."
    assert service.criteria == []


def test_get_purchase_returns_404_problem_details_when_purchase_does_not_exist(
    client: TestClient, service: RecordingExplorationService
) -> None:
    # Arrange
    missing = "00000000-0000-0000-0000-000000000000"
    # Act
    response = client.get(f"/api/v1/purchases/{missing}")
    # Assert
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "Compra no encontrada"


def test_get_purchase_returns_400_when_identifier_is_not_a_uuid(
    client: TestClient, service: RecordingExplorationService
) -> None:
    # Arrange / Act
    response = client.get("/api/v1/purchases/no-es-un-uuid")
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "El parámetro «purchase_id» no es válido."
