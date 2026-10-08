import uuid

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from public_procurement.comparison.services import build_comparison_service
from public_procurement.entrypoints.api.app import create_app
from public_procurement.shared.config import Settings
from public_procurement.shared.persistence import create_session_factory

pytestmark = pytest.mark.integration

OTHER_OWNER = uuid.UUID("11111111-2222-3333-4444-555555555555")
SIGNAL = "SG-2026-0142"


@pytest.fixture(scope="module")
def client(seeded_engine: Engine, database_settings: Settings) -> TestClient:
    return TestClient(create_app(database_settings))


@pytest.fixture(scope="module")
def other_client(seeded_engine: Engine, database_settings: Settings) -> TestClient:
    """Mismo backend, otro dueño (simula a un segundo Analista)."""
    app = create_app(database_settings)

    def other_owner(request: Request) -> uuid.UUID:
        return OTHER_OWNER

    app.state.current_user_provider = other_owner
    return TestClient(app)


def _new_case(client: TestClient, title: str = "Televisores en sedes educativas — Valle") -> str:
    response = client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201
    return str(response.json()["id"])


def test_saving_a_signal_stores_its_snapshot_when_signal_exists(client: TestClient) -> None:
    # Arrange
    case_id = _new_case(client)
    # Act
    response = client.post(
        f"/api/v1/cases/{case_id}/items", json={"kind": "signal", "reference": SIGNAL}
    )
    # Assert
    assert response.status_code == 201
    item = response.json()["items"][0]
    assert item["kind"] == "signal"
    snapshot = item["snapshot"]
    assert (snapshot["code"], snapshot["unit_price_cop"]) == (SIGNAL, 4_950_000)
    assert snapshot["config_version_id"] == "analitica-v1"
    assert {"median_cop", "deviation_pct", "confidence_level"} <= set(snapshot)


def test_saving_a_purchase_stores_its_snapshot_when_purchase_exists(client: TestClient) -> None:
    # Arrange
    case_id = _new_case(client)
    purchase_id = client.get(f"/api/v1/signals/{SIGNAL}").json()["signal"]["purchase_id"]
    # Act
    response = client.post(
        f"/api/v1/cases/{case_id}/items", json={"kind": "purchase", "reference": purchase_id}
    )
    # Assert
    snapshot = response.json()["items"][0]["snapshot"]
    assert (snapshot["reference"], snapshot["total_value_cop"]) == (
        "CO1.PCCNTR.0000142",
        39_600_000,
    )


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/cases", {"title": ""}),
        ("/api/v1/cases", {"title": "x" * 121}),
        ("/items", {"kind": "contract", "reference": SIGNAL}),
        ("/notes", {"body": ""}),
        ("/notes", {"body": "a" * 5_001}),
    ],
    ids=["empty_title", "long_title", "unknown_kind", "empty_note", "long_note"],
)
def test_invalid_data_returns_400_and_saves_nothing_when_posted(
    client: TestClient, path: str, payload: dict[str, object]
) -> None:
    # Arrange
    case_id = _new_case(client)
    url = path if path.startswith("/api") else f"/api/v1/cases/{case_id}{path}"
    # Act
    response = client.post(url, json=payload)
    # Assert
    assert response.status_code == 400
    case = client.get(f"/api/v1/cases/{case_id}").json()
    assert (case["item_count"], case["note_count"]) == (0, 0)


def test_saving_the_same_item_twice_returns_422_when_already_saved(client: TestClient) -> None:
    # Arrange
    case_id = _new_case(client)
    payload = {"kind": "signal", "reference": SIGNAL}
    client.post(f"/api/v1/cases/{case_id}/items", json=payload)
    # Act
    response = client.post(f"/api/v1/cases/{case_id}/items", json=payload)
    # Assert
    assert response.status_code == 422
    assert response.json()["detail"] == "Ese elemento ya está guardado en el caso"
    assert client.get(f"/api/v1/cases/{case_id}").json()["item_count"] == 1


def test_other_owner_gets_404_for_reading_writing_or_saving_when_case_is_not_theirs(
    client: TestClient, other_client: TestClient
) -> None:
    # Arrange
    case_id = _new_case(client)
    # Act
    responses = [
        other_client.get(f"/api/v1/cases/{case_id}"),
        other_client.post(f"/api/v1/cases/{case_id}/notes", json={"body": "intento"}),
        other_client.post(
            f"/api/v1/cases/{case_id}/items", json={"kind": "signal", "reference": SIGNAL}
        ),
    ]
    # Assert
    assert [response.status_code for response in responses] == [404, 404, 404]
    assert all(c["id"] != case_id for c in other_client.get("/api/v1/cases").json())


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "signal", "reference": "SG-2099-0001"},
        {"kind": "purchase", "reference": "00000000-0000-0000-0000-000000000000"},
        {"kind": "purchase", "reference": "no-es-un-uuid"},
    ],
    ids=["missing_signal", "missing_purchase", "invalid_purchase_id"],
)
def test_saving_a_missing_reference_returns_404_when_it_does_not_exist(
    client: TestClient, payload: dict[str, str]
) -> None:
    # Arrange
    case_id = _new_case(client)
    # Act
    response = client.post(f"/api/v1/cases/{case_id}/items", json=payload)
    # Assert
    assert response.status_code == 404


def test_snapshot_does_not_change_when_signals_are_recalculated(
    client: TestClient, seeded_engine: Engine
) -> None:
    # Arrange
    case_id = _new_case(client)
    client.post(f"/api/v1/cases/{case_id}/items", json={"kind": "signal", "reference": SIGNAL})
    before = client.get(f"/api/v1/cases/{case_id}").json()["items"][0]
    # Act
    build_comparison_service(create_session_factory(seeded_engine)).recalculate()
    # Assert
    after = client.get(f"/api/v1/cases/{case_id}").json()["items"][0]
    assert after == before


def test_notes_are_listed_in_creation_order_with_dates_when_added(client: TestClient) -> None:
    # Arrange
    case_id = _new_case(client)
    # Act
    client.post(f"/api/v1/cases/{case_id}/notes", json={"body": "Primera nota"})
    client.post(f"/api/v1/cases/{case_id}/notes", json={"body": "Segunda nota"})
    # Assert
    notes = client.get(f"/api/v1/cases/{case_id}").json()["notes"]
    assert [note["body"] for note in notes] == ["Primera nota", "Segunda nota"]
    assert all(note["created_at"] for note in notes)


def test_case_list_is_ordered_by_last_activity_when_a_case_gets_a_note(client: TestClient) -> None:
    # Arrange
    older = _new_case(client, "Caso antiguo")
    _new_case(client, "Caso reciente")
    # Act
    client.post(f"/api/v1/cases/{older}/notes", json={"body": "Retomado"})
    # Assert
    assert client.get("/api/v1/cases").json()[0]["id"] == older
