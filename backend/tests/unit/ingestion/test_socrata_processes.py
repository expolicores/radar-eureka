import io
import json
from datetime import date, datetime
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

from public_procurement.ingestion.adapters import socrata_processes as adapter
from public_procurement.ingestion.domain.process import ProcessQuery


def row(cursor="row-a", identifier="CO1.REQ.11172521"):
    return {
        "source_row_id": cursor,
        "id_del_proceso": identifier,
        "id_del_portafolio": "CO1.BDOS.10985405",
        "precio_base": "1000000.00",
        "fecha_de_publicacion_del": "2026-10-07T00:00:00.000",
        "urlproceso": {
            "url": "https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index"
        },
    }


def test_mapper_preserves_process_and_portfolio_without_sensitive_fields() -> None:
    mapped = adapter.map_process({**row(), "nit_del_proveedor_adjudicado": "do-not-store"})
    assert mapped.id_del_proceso == "CO1.REQ.11172521"
    assert mapped.id_del_portafolio == "CO1.BDOS.10985405"
    assert mapped.base_price_cop == 1_000_000
    assert mapped.published_on == date(2026, 10, 7)
    assert "do-not-store" not in repr(mapped)


@pytest.mark.parametrize("value", ["1.5", "NaN", "-1", "invalid", "9223372036854775808"])
def test_mapper_rejects_invalid_cop_prices(value) -> None:
    with pytest.raises(ValueError, match=r".+"):
        adapter.map_process({**row(), "precio_base": value})


def test_mapper_does_not_invent_missing_price_or_portfolio() -> None:
    mapped = adapter.map_process({"id_del_proceso": "CO1.REQ.1"})
    assert mapped.base_price_cop is None
    assert mapped.id_del_portafolio is None


def test_cursor_pagination_escapes_filters_and_has_no_offset(monkeypatch) -> None:
    requests = []
    pages = [[row("row-a"), row("row-b", "CO1.REQ.2")], [row("row-c", "CO1.REQ.3")]]

    def get(request, timeout):
        requests.append(parse_qs(urlparse(request.full_url).query))
        assert timeout == 45
        return io.BytesIO(json.dumps(pages.pop(0)).encode())

    monkeypatch.setattr(adapter, "urlopen", get)
    query = ProcessQuery(portfolio_id="CO1.BDOS.'123", page_size=2)
    results = list(adapter.SocrataProcessSource().fetch_processes(query))
    assert len(results) == 3
    assert requests[0]["$where"] == ["id_del_portafolio = 'CO1.BDOS.''123'"]
    assert ":id > 'row-b'" in requests[1]["$where"][0]
    assert all("$offset" not in request for request in requests)
    assert requests[0]["$order"] == [":id ASC"]


def test_publication_interval_is_inclusive_exclusive(monkeypatch) -> None:
    requests = []

    def get(request, timeout):
        requests.append(parse_qs(urlparse(request.full_url).query))
        return io.BytesIO(b"[]")

    monkeypatch.setattr(adapter, "urlopen", get)
    query = ProcessQuery(published_from=date(2026, 10, 1), published_before=date(2026, 10, 8))
    assert list(adapter.SocrataProcessSource().fetch_processes(query)) == []
    assert "fecha_de_publicacion_del >= '2026-10-01'" in requests[0]["$where"][0]
    assert "fecha_de_publicacion_del < '2026-10-08'" in requests[0]["$where"][0]


def test_requested_calendar_window_contains_no_intraday_boundaries(monkeypatch) -> None:
    source = adapter.SocrataProcessSource()
    requests = []
    monkeypatch.setattr(source, "_page", lambda params: requests.append(params) or [])
    assert (
        list(
            source.fetch_processes(
                ProcessQuery(published_from=date(2026, 10, 13), published_before=date(2026, 10, 15))
            )
        )
        == []
    )
    assert requests[0]["$where"] == (
        "fecha_de_publicacion_del >= '2026-10-13' AND fecha_de_publicacion_del < '2026-10-15'"
    )


@pytest.mark.parametrize("field", ["published_from", "published_before"])
@pytest.mark.parametrize("hour", [0, 12])
def test_query_explicitly_rejects_datetime_boundaries(field, hour):
    boundaries = {"published_from": date(2026, 10, 13), "published_before": date(2026, 10, 15)}
    boundaries[field] = datetime(2026, 10, 14, hour)  # noqa: DTZ001 -- límite rechazado, sin zona
    with pytest.raises(ValueError, match="YYYY-MM-DD sin hora"):
        ProcessQuery(**boundaries)


@pytest.mark.parametrize(
    "pages",
    [
        [[row("row-a")], [row("row-a")]],
        [[{**row(), "source_row_id": None}]],
    ],
)
def test_missing_or_nonadvancing_cursor_is_rejected(monkeypatch, pages) -> None:
    monkeypatch.setattr(
        adapter, "urlopen", lambda *a, **kw: io.BytesIO(json.dumps(pages.pop(0)).encode())
    )
    with pytest.raises(ValueError, match="Cursor"):
        list(
            adapter.SocrataProcessSource().fetch_processes(
                ProcessQuery(portfolio_id="P", page_size=1)
            )
        )


def test_max_pages_never_silently_truncates_results(monkeypatch) -> None:
    monkeypatch.setattr(
        adapter, "urlopen", lambda *a, **kw: io.BytesIO(json.dumps([row()]).encode())
    )
    with pytest.raises(ValueError, match="max-pages"):
        list(
            adapter.SocrataProcessSource().fetch_processes(
                ProcessQuery(portfolio_id="P", page_size=1, max_pages=1)
            )
        )


@pytest.mark.parametrize("cursor", [None, "", "row-a"])
def test_partial_page_finishes_without_requiring_next_cursor(monkeypatch, cursor) -> None:
    pages = [[row(cursor), row(cursor, "CO1.REQ.2")]]

    def page(params):
        assert params["$limit"] == "200"
        return pages.pop(0)

    source = adapter.SocrataProcessSource()
    monkeypatch.setattr(source, "_page", page)
    assert len(list(source.fetch_processes(ProcessQuery(portfolio_id="P", page_size=200)))) == 2
    assert pages == []


def test_partial_page_without_selected_cursor_is_final(monkeypatch) -> None:
    record = row()
    del record["source_row_id"]
    source = adapter.SocrataProcessSource()
    monkeypatch.setattr(source, "_page", lambda params: [record])
    assert len(list(source.fetch_processes(ProcessQuery(portfolio_id="P")))) == 1


def test_opaque_cursor_order_is_delegated_to_socrata(monkeypatch) -> None:
    requests = []
    pages = [
        [row("row-x2f7_7edi.3zdt"), row("row-djky.tfcm~tdzt", "CO1.REQ.2")],
        [row("row-8jet-k82b_y8pc", "CO1.REQ.3"), row("row-4kd6_i7jc.djyk", "CO1.REQ.4")],
        [],
    ]

    def page(params):
        requests.append(params)
        return pages.pop(0)

    source = adapter.SocrataProcessSource()
    monkeypatch.setattr(source, "_page", page)
    assert len(list(source.fetch_processes(ProcessQuery(portfolio_id="P", page_size=2)))) == 4
    assert ":id > 'row-djky.tfcm~tdzt'" in requests[1]["$where"]
    assert ":id > 'row-4kd6_i7jc.djyk'" in requests[2]["$where"]
    assert all(params["$order"] == ":id ASC" for params in requests)
    assert all(":id AS source_row_id" in params["$select"] for params in requests)


@pytest.mark.parametrize(
    "pages",
    [
        [[row("a"), row("a")]],
        [[row("a"), row("b")], [row("c"), row("a")]],
        [[row("a"), row("b")], [row("a"), row("c")]],
        [[row("a"), {"id_del_proceso": "CO1.REQ.2"}]],
    ],
)
def test_full_pages_reject_missing_repeated_or_cycling_cursors(monkeypatch, pages) -> None:
    source = adapter.SocrataProcessSource()
    monkeypatch.setattr(source, "_page", lambda params: pages.pop(0))
    with pytest.raises(ValueError, match="Cursor"):
        list(source.fetch_processes(ProcessQuery(portfolio_id="P", page_size=2)))


def test_transient_http_error_is_retried(monkeypatch) -> None:
    attempts, waits = [], []

    def get(request, timeout):
        attempts.append(request)
        if len(attempts) < 3:
            raise HTTPError(adapter.ENDPOINT, 429, "limited", {}, None)
        return io.BytesIO(b"[]")

    monkeypatch.setattr(adapter, "urlopen", get)
    monkeypatch.setattr(adapter.time, "sleep", waits.append)
    assert (
        list(adapter.SocrataProcessSource().fetch_processes(ProcessQuery(portfolio_id="P"))) == []
    )
    assert waits == [2, 4]


def test_nontransient_error_is_not_retried(monkeypatch) -> None:
    def get(request, timeout):
        raise HTTPError(adapter.ENDPOINT, 400, "invalid query", {}, None)

    monkeypatch.setattr(adapter, "urlopen", get)
    with pytest.raises(RuntimeError, match="HTTP 400"):
        list(adapter.SocrataProcessSource().fetch_processes(ProcessQuery(portfolio_id="P")))


def test_department_filter_is_case_normalized_and_escapes_literals(monkeypatch):
    requests = []

    def get(request, timeout):
        requests.append(parse_qs(urlparse(request.full_url).query))
        return io.BytesIO(b"[]")

    monkeypatch.setattr(adapter, "urlopen", get)
    list(
        adapter.SocrataProcessSource().fetch_processes(
            ProcessQuery(portfolio_id="portfolio", departments=("CASANARE", "O'Hara"))
        )
    )
    assert "lower(departamento_entidad) IN ('casanare','o''hara')" in requests[0]["$where"][0]
