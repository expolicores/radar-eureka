from datetime import datetime

import pytest

from public_procurement.documents.adapters.socrata import SocrataDocumentSource, map_document


def row(identifier="1", cursor="row-a"):
    return {
        "id_documento": identifier,
        "proceso": "CO1.BDOS.1",
        "nombre_archivo": "name.pdf",
        "fecha_carga": "2026-10-06T00:00:00.000",
        "source_row_id": cursor,
        "url_descarga_documento": {"url": "https://community.secop.gov.co/file"},
    }


def test_official_fields_preserve_identifiers_and_calendar_date() -> None:
    document = map_document(row(), "CO1.BDOS.1")
    assert document.dataset_id == "dmgg-8hin"
    assert document.id_documento == "1"
    assert document.fecha_carga == datetime(2026, 10, 6)  # noqa: DTZ001 — calendar_date del proveedor
    assert document.source_url == "https://community.secop.gov.co/file"


def test_contract_lookup_uses_official_contract_column_and_preserves_process(monkeypatch):
    source, calls = SocrataDocumentSource(), []

    def page(params):
        calls.append(params)
        return [{**row(), "n_mero_de_contrato": "CO1.PCCNTR.123"}]

    monkeypatch.setattr(source, "_page", page)
    documents = source.fetch_by_contract("CO1.PCCNTR.123")
    assert calls[0]["$where"] == "n_mero_de_contrato = 'CO1.PCCNTR.123'"
    assert "n_mero_de_contrato" in calls[0]["$select"]
    assert documents[0].portfolio_id == "CO1.BDOS.1"


def test_wrong_contract_lookup_is_rejected(monkeypatch):
    source = SocrataDocumentSource()
    monkeypatch.setattr(source, "_page", lambda params: [{**row(), "n_mero_de_contrato": "other"}])
    with pytest.raises(ValueError, match="otro contrato"):
        source.fetch_by_contract("CO1.PCCNTR.123")


def test_inventory_paginates_and_deduplicates(monkeypatch) -> None:
    source, calls = SocrataDocumentSource(), []
    # Primera página completa de filas repetidas: un único documento lógico.
    pages = [[row(cursor=f"row-{i:04}") for i in range(1000)], [row("2", "row-1000")]]

    def page(params):
        calls.append(params)
        return pages.pop(0)

    monkeypatch.setattr(source, "_page", page)
    result = source.fetch("CO1.BDOS.1")
    assert len(result) == 2
    assert ":id > 'row-0999'" in calls[1]["$where"]
    assert "$offset" not in calls[1]


def test_wrong_portfolio_or_conflicting_document_is_rejected(monkeypatch) -> None:
    with pytest.raises(ValueError, match="otro portafolio"):
        map_document(row(), "different")
    source = SocrataDocumentSource()
    monkeypatch.setattr(
        source,
        "_page",
        lambda params: [row(), {**row(cursor="row-b"), "nombre_archivo": "changed.pdf"}],
    )
    with pytest.raises(ValueError, match="contradictorias"):
        source.fetch("CO1.BDOS.1")


def test_opaque_cursor_order_is_defined_by_socrata_not_python(monkeypatch) -> None:
    source = SocrataDocumentSource()
    monkeypatch.setattr(source, "_page", lambda params: [row("1", "row-z"), row("2", "row-a")])
    assert len(source.fetch("CO1.BDOS.1")) == 2


def test_repeated_cursor_is_rejected(monkeypatch) -> None:
    source = SocrataDocumentSource()
    monkeypatch.setattr(source, "_page", lambda params: [row("1", "row-a"), row("2", "row-a")])
    with pytest.raises(ValueError, match="Cursor"):
        source.fetch("CO1.BDOS.1")
