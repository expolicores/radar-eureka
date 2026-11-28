"""Offline tests for the paginated SECOP II inventory reader. Synthetic pages; no network."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import licitaciones_cdp_runtime as runtime

SECOP = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId="
HEADERS = ["Item", "Nombre", "Tipo", "Documento"]
KEYS = {"idContrato": 1, "id_fuente_contract": 3, "idUltimaFase": "CO1.NTC.1"}


def row(doc_id, name="Invitación.pdf"):
    return [
        "",
        "",
        name,
        '<img src="/img/extensiones/pdf.svg">',
        f'<a href="{SECOP}{doc_id}">documento</a>',
    ]


def page(*rows):
    return {"status": 1, "documentos": {"encabezados": HEADERS, "campos": list(rows)}}


EMPTY = {"status": 1, "documentos": []}


class Client:
    def __init__(self, pages):
        self.pages, self.calls = list(pages), []

    def post(self, path, payload):
        self.calls.append(payload["page"])
        return self.pages[payload["page"] - 1]


def test_complete_inventory_ends_on_the_documented_empty_page():
    client = Client([page(row("1"), row("2", "Estudio previo.pdf")), EMPTY])

    documents = runtime.fetch_inventory(client, KEYS)

    assert [d.document_id for d in documents] == ["1", "2"]
    assert client.calls == [1, 2]


@pytest.mark.parametrize(
    "second",
    [
        {"status": 1, "documentos": {}},  # empty object, not the documented empty list
        {"status": 1, "documentos": None},
        {"status": 1, "documentos": {"encabezados": [*HEADERS, "Fecha"], "campos": []}},
        {"status": 1, "documentos": {"encabezados": HEADERS, "campos": [["", "x"]]}},
        {"status": 0, "mensaje": "sin datos"},
    ],
)
def test_unknown_second_page_keeps_first_page_and_is_never_read_as_the_end(second):
    # Arrange
    client = Client([page(row("1")), second])

    # Act
    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(client, KEYS)

    # Assert
    error = raised.value
    assert [d.document_id for d in error.documents] == ["1"]
    assert (error.failed_page, error.pages_read, error.reason) == (2, 1, "unreadable_page")
    assert error.shape["body_type"] == "dict"
    assert client.calls == [1, 2]  # no further page is requested


def test_shape_keeps_structure_and_never_content():
    second = {
        "status": 1,
        "documentos": {
            "encabezados": [*HEADERS, "Fecha"],
            "campos": [["7", "", "Nombre secreto.pdf", "<img>", f'<a href="{SECOP}99">x</a>', "1"]],
        },
    }
    client = Client([page(row("1")), second])

    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(client, KEYS)

    shape = raised.value.shape
    assert shape["encabezados"] == [*HEADERS, "Fecha"]
    assert shape["row_widths"] == [6]
    assert shape["cell_types"] == ["str"] * 6
    serialized = json.dumps(raised.value.diagnostic())
    for secret in ("Nombre secreto", "DocumentId", "community.secop"):
        assert secret not in serialized


def test_unknown_first_page_is_incomplete_with_no_documents():
    client = Client([{"status": 1, "documentos": {}}])

    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(client, KEYS)

    assert raised.value.documents == []
    assert raised.value.failed_page == 1


def test_repeated_page_keeps_documents_and_is_incomplete():
    client = Client([page(row("1")), page(row("1"))])

    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(client, KEYS)

    assert raised.value.reason == "repeated_page"
    assert [d.document_id for d in raised.value.documents] == ["1"]


def test_page_ceiling_keeps_documents_and_is_incomplete():
    client = Client([page(row(str(n))) for n in range(1, 11)])

    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(client, KEYS)

    assert raised.value.reason == "page_limit"
    assert len(raised.value.documents) == 10


def test_incomplete_inventory_is_still_a_spike_error_for_existing_callers():
    assert issubclass(runtime.InventoryIncomplete, runtime.SpikeError)


def test_missing_keys_fail_before_any_request():
    client = Client([])

    with pytest.raises(runtime.SpikeError, match="identificadores"):
        runtime.fetch_inventory(client, {**KEYS, "idUltimaFase": None})

    assert client.calls == []


def test_runner_keeps_partial_inventory_and_records_it_as_incomplete(monkeypatch, tmp_path):
    import eureka_nacional_en01 as en01

    from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

    kept = en01.spike.SpikeDocument("Invitación", "pdf", SECOP + "1", "1")

    def fetch(_client, _keys):
        raise runtime.InventoryIncomplete(
            "Contrato de tabla documental desconocido.",
            documents=[kept],
            failed_page=2,
            reason="unreadable_page",
            shape={"documentos_type": "dict"},
        )

    monkeypatch.setattr(en01, "fetch_inventory", fetch)
    metrics, documents, errors = en01.Counter(), [], []

    en01.analyze_documents(
        object(),
        {"process_reference": "p", "inventory_keys": KEYS},
        LocalBinaryStorage(tmp_path),
        None,
        0,
        metrics,
        documents,
        errors,
    )

    assert [d["name"] for d in documents] == ["Invitación"]
    [error] = errors
    assert error["code"] == "inventory_incomplete"
    assert error["failed_page"] == 2
    assert error["documents_kept"] == 1


def empty_table(cantidad=None):
    body = {
        "status": 1,
        "documentos": {
            "encabezados": [],
            "campos": [],
            "vermas": None,
            "before_table": None,
            "agregar_checkbox_seleccion": False,
        },
    }
    if cantidad is not None:
        body["cantidad"] = cantidad
    return body


def test_empty_table_ends_pagination_but_coverage_stays_unproven():
    # Arrange: the form observed in a real inventory after a full first page.
    client = Client([page(row("1"), row("2")), empty_table(cantidad=2)])

    # Act
    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(client, KEYS)

    # Assert
    error = raised.value
    assert error.reason == "empty_table_unverified_total"
    assert [d.document_id for d in error.documents] == ["1", "2"]
    assert error.shape["cantidad"] == 2
    assert error.shape["encabezados"] == []
    assert client.calls == [1, 2]  # pagination ended; no further page requested


def test_empty_table_is_complete_only_once_cantidad_is_validated_and_matches(monkeypatch):
    monkeypatch.setattr(runtime, "CANTIDAD_IS_DOCUMENT_TOTAL", True)

    documents = runtime.fetch_inventory(
        Client([page(row("1"), row("2")), empty_table(cantidad=2)]), KEYS
    )

    assert [d.document_id for d in documents] == ["1", "2"]


@pytest.mark.parametrize("cantidad", [3, None, "2"])
def test_cantidad_mismatch_or_absence_keeps_the_inventory_incomplete(monkeypatch, cantidad):
    monkeypatch.setattr(runtime, "CANTIDAD_IS_DOCUMENT_TOTAL", True)
    body = empty_table()
    if cantidad is not None:
        body["cantidad"] = cantidad

    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(Client([page(row("1"), row("2")), body]), KEYS)

    assert raised.value.reason == "empty_table_unverified_total"


@pytest.mark.parametrize(
    "variant",
    [
        {"status": 0, "documentos": {"encabezados": [], "campos": []}},
        {"status": 1, "documentos": {"encabezados": [], "campos": [["x"]]}},
        {"status": 1, "documentos": {"encabezados": ["Item"], "campos": []}},
        {"status": 1, "documentos": {"campos": []}},
    ],
)
def test_near_empty_tables_are_not_taken_as_the_end(variant):
    with pytest.raises(runtime.InventoryIncomplete) as raised:
        runtime.fetch_inventory(Client([page(row("1")), variant]), KEYS)

    assert raised.value.reason == "unreadable_page"


def test_trail_records_only_row_counts_and_numeric_cantidad():
    first = {**page(row("1"), row("2")), "cantidad": 2}
    trail = []

    with pytest.raises(runtime.InventoryIncomplete):
        runtime.fetch_inventory(Client([first, empty_table(cantidad=2)]), KEYS, trail=trail)

    assert trail == [
        {"page": 1, "rows": 2, "cantidad": 2, "form": "table"},
        {"page": 2, "rows": 0, "cantidad": 2, "form": "empty_table"},
    ]


def test_documented_empty_list_still_completes_and_is_traced():
    trail = []

    documents = runtime.fetch_inventory(Client([page(row("1")), EMPTY]), KEYS, trail=trail)

    assert [d.document_id for d in documents] == ["1"]
    assert trail[-1] == {"page": 2, "rows": 0, "cantidad": None, "form": "empty_list"}
