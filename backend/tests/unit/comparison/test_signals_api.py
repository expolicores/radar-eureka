from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.comparison.services import (
    ConfidenceLevel,
    SignalFilters,
    SignalPage,
    SignalSort,
    SignalSummary,
)

from ...builders import SignalRowBuilder

PROHIBITED_TERMS = ("sobreprecio", "corrupción", "corrupcion", "fraude", "hallazgo fiscal")


class RecordingSignalService:
    def __init__(self) -> None:
        self.calls: list[tuple[SignalFilters, SignalSort, int, int]] = []

    def list_signals(
        self, filters: SignalFilters, sort: SignalSort, page: int, page_size: int
    ) -> SignalPage:
        self.calls.append((filters, sort, page, page_size))
        return SignalPage((SignalRowBuilder().build(),), 1, page, page_size)

    def summary(self) -> SignalSummary:
        return SignalSummary(
            tv_purchases_by_source={"secop_ii": 335, "tvec": 932},
            signals_by_confidence={
                ConfidenceLevel.HIGH: 16,
                ConfidenceLevel.MEDIUM: 26,
                ConfidenceLevel.LOW: 0,
            },
            incomplete_comparisons=40,
            without_source_information=112,
            config_version_id="analitica-v1",
            data_cutoff_at=datetime(2026, 10, 6, 8, 10, tzinfo=UTC),
        )


@pytest.fixture
def service(app: FastAPI) -> RecordingSignalService:
    double = RecordingSignalService()
    app.state.signal_service = double
    return double


def test_list_signals_uses_priority_and_default_page_when_no_parameters(
    client: TestClient, service: RecordingSignalService
) -> None:
    # Arrange / Act
    response = client.get("/api/v1/signals")
    # Assert
    assert response.status_code == 200
    filters, sort, page, page_size = service.calls[0]
    assert (sort, page, page_size) == (SignalSort.PRIORITY, 1, 25)
    assert filters == SignalFilters()
    assert response.json()["items"][0]["code"] == "SG-2026-0142"
    assert response.json()["items"][0]["deviation_pct"] == "73.1"


def test_list_signals_passes_filters_when_given(
    client: TestClient, service: RecordingSignalService
) -> None:
    # Arrange
    params = {
        "q": "san rafael",
        "department": "Valle del Cauca",
        "source": "tvec",
        "confidence": "high",
        "year": "2026",
        "sort": "deviation",
    }
    # Act
    client.get("/api/v1/signals", params=params)
    # Assert
    filters, sort, _, _ = service.calls[0]
    assert filters == SignalFilters(
        text="san rafael",
        department="Valle del Cauca",
        source="tvec",
        confidence=ConfidenceLevel.HIGH,
        year=2026,
    )
    assert sort is SignalSort.DEVIATION


@pytest.mark.parametrize(
    ("params", "parameter"),
    [
        ({"confidence": "certain"}, "confidence"),
        ({"sort": "random"}, "sort"),
        ({"year": "1990"}, "year"),
    ],
)
def test_list_signals_returns_400_when_parameter_is_invalid(
    client: TestClient, service: RecordingSignalService, params: dict[str, str], parameter: str
) -> None:
    # Arrange / Act
    response = client.get("/api/v1/signals", params=params)
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == f"El parámetro «{parameter}» no es válido."


def test_summary_adds_totals_when_requested(
    client: TestClient, service: RecordingSignalService
) -> None:
    # Arrange / Act
    body = client.get("/api/v1/signals/summary").json()
    # Assert
    assert (body["tv_purchases"], body["signals"]) == (1267, 42)
    assert body["signals_by_confidence"] == {"high": 16, "medium": 26, "low": 0}


def test_signal_responses_never_use_accusatory_terms_when_returned(
    client: TestClient, service: RecordingSignalService
) -> None:
    # Arrange / Act
    texts = client.get("/api/v1/signals").text + client.get("/api/v1/signals/summary").text
    # Assert
    assert not [term for term in PROHIBITED_TERMS if term in texts.lower()]
