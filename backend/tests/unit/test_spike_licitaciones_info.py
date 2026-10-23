"""Contratos sintéticos; no representan respuestas reales aún no autorizadas."""

import importlib.util
import json
import sys
import uuid
from dataclasses import asdict
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError
from public_procurement.extraction.domain.content import EvidenceFragment
from public_procurement.shared.config import Settings

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "spike_licitaciones_info.py"
auth_spec = importlib.util.spec_from_file_location(
    "licitaciones_auth", SCRIPT.with_name("licitaciones_auth.py")
)
auth = importlib.util.module_from_spec(auth_spec)
sys.modules[auth_spec.name] = auth
auth_spec.loader.exec_module(auth)
spec = importlib.util.spec_from_file_location("spike_licitaciones_info", SCRIPT)
spike = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = spike
spec.loader.exec_module(spike)

URL = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=test-id"
PROCESS = {
    "idContrato": 123,
    "id_fuente_contract": 3,
    "idUltimaFase": "CO1.NTC.TEST",
    "CodigoProceso": "TEST-001",
    "TextoDepartamento": "Boyacá",
    "Objeto": "Refrigerios",
    "FechaPublicacion": "2026-10-19",
    "NumeroDocumentos": 4,
}
DOCUMENT = {"nombre": "INVITACIÓN.pdf", "tipo": "pdf", "url": URL, "id_documento": 999}


def config(**overrides):
    return {
        "LICITACIONES_BASE_URL": "https://example.licitaciones.info",
        "LICITACIONES_COOKIE": "synthetic-session",
        "LICITACIONES_X_CSRF_TOKEN": "",
        "LICITACIONES_X_XSRF_TOKEN": "",
        "LICITACIONES_BOYACA_LOCATION_IDS": "1,2,3",
        "LICITACIONES_PROFILE_ID": "1086005",
        **overrides,
    }


@pytest.mark.parametrize(
    "wrapper",
    [lambda rows: rows, lambda rows: {"data": rows}, lambda rows: {"data": {"data": rows}}],
)
def test_get_info_parsing_secop2_and_metadata(wrapper):
    second = {**PROCESS, "idContrato": 124, "id_fuente_contract": 1, "key_config": "secop2"}
    parsed = spike.parse_process_rows(
        wrapper([PROCESS, second, {**PROCESS, "id_fuente_contract": 2}])
    )
    assert len(parsed) == 2
    assert parsed[0]["Objeto"] == "Refrigerios"
    assert parsed[0]["FechaPublicacion"] == "2026-10-19"


@pytest.mark.parametrize(
    "payload",
    [
        {"unexpected": []},
        {"error": "secret", "data": []},
        [{"Objeto": "missing identifier"}],
        [None],
    ],
)
def test_unknown_or_invalid_process_contract_fails_explicitly(payload):
    with pytest.raises(spike.SpikeError):
        spike.parse_process_rows(payload)


def test_payload_filters_and_discovery_dedup_no_additional_queries():
    client = Mock()
    client.post.return_value = {
        "data": [PROCESS, PROCESS, {**PROCESS, "TextoDepartamento": "Tolima"}]
    }
    processes, received = spike.fetch_processes(client, config(), "refrigerio", 30)
    assert received == 3
    assert len(processes) == 1
    client.post.assert_called_once()
    path, payload = client.post.call_args.args
    assert path.endswith("?perfiles=1086005")
    assert payload["query"] == {"Objeto": "refrigerio", "ubicacion_filter": "1,2,3"}
    assert payload["orderBy"] == "FechaPublicacion"
    assert payload["ascending"] == 0
    assert payload["limit"] == 30
    assert payload["page"] == 1


@pytest.mark.parametrize(("limit", "locations"), [(31, "1"), (0, "1"), (30, ""), (30, "inventado")])
def test_bounds_and_missing_location_ids(limit, locations):
    with pytest.raises(spike.SpikeError):
        spike.build_process_payload(locations, "refrigerio", limit)


@pytest.mark.parametrize(
    "wrapper", [lambda rows: rows, lambda rows: {"documentos": rows}, lambda rows: {"data": rows}]
)
def test_document_parser_preserves_public_url_and_archive_id(wrapper):
    document = spike.parse_document_rows(wrapper([DOCUMENT]))[0]
    assert document.document_id == "test-id"  # no confundir con el id interno 999
    assert document.source_url == URL
    assert document.original_name == "INVITACIÓN.pdf"
    assert document.extension == "pdf"


@pytest.mark.parametrize(
    "url",
    [
        "http://community.secop.gov.co/file",
        "https://evil.invalid/file",
        "https://community.secop.gov.co@evil.invalid/file",
    ],
)
def test_document_url_rejects_other_hosts_and_http(url):
    with pytest.raises(AcquisitionError):
        spike.parse_document_rows([{**DOCUMENT, "url": url}])


def test_documents_paginate_until_empty_and_dedup():
    client = Mock()
    client.post.side_effect = [
        {"data": [DOCUMENT]},
        {
            "data": [
                {**DOCUMENT, "url": URL + "2"},
                DOCUMENT,
            ]
        },
        {"data": []},
    ]
    assert len(spike.fetch_documents(client, PROCESS)) == 2
    assert [call.args[1]["page"] for call in client.post.call_args_list] == [1, 2, 3]
    assert client.post.call_args.args[1]["idUltimaFase"] == "CO1.NTC.TEST"


def test_repeated_document_page_is_not_silently_accepted():
    client = Mock()
    client.post.return_value = [DOCUMENT]
    with pytest.raises(spike.SpikeError, match="repetida"):
        spike.fetch_documents(client, PROCESS)


def test_document_selection_prioritizes_names_and_supported_formats():
    docs = [
        spike.SpikeDocument(name, ext, URL, name)
        for name, ext in (
            ("CDP.pdf", "pdf"),
            ("Estudios previos.docx", "docx"),
            ("INVITACIÓN.pdf", "pdf"),
            ("Anexo técnico.exe", "exe"),
        )
    ]
    assert [doc.original_name for doc in spike.select_documents(docs, 2)] == [
        "INVITACIÓN.pdf",
        "Estudios previos.docx",
    ]


@pytest.mark.parametrize("status", [302, 401, 403, 419, 429])
def test_auth_and_rate_limit_halt_without_leaking_secrets(status):
    transport = Mock(
        return_value=httpx.Response(status, headers={"Location": "https://evil.invalid"})
    )
    client = spike.Client(config(), transport=httpx.MockTransport(transport), sleep=lambda _: None)
    try:
        with pytest.raises(spike.SpikeError) as error:
            client.post("/test", {})
        assert "synthetic-session" not in str(error.value)
        with pytest.raises(spike.SpikeError):
            client.post("/test", {})
        assert transport.call_count == 1
    finally:
        client.http.close()


def test_request_budget_and_throttle():
    sleep = Mock()
    client = spike.Client(config(), sleep=sleep)
    try:
        client.reserve()
        client.reserve(6)
        assert client.requests == 7
        sleep.assert_called_once()
        client.requests = 60
        with pytest.raises(spike.SpikeError, match="60 requests"):
            client.reserve()
    finally:
        client.http.close()


def test_missing_auth_never_makes_network_request():
    with pytest.raises(spike.SpikeError, match="LICITACIONES_COOKIE"):
        spike.Client(config(LICITACIONES_COOKIE=""))


def test_existing_native_extractor_with_local_storage_and_forbidden_db(tmp_path):
    data = (SCRIPT.parents[1] / "tests/fixtures/extraction/native_refrigerios.pdf").read_bytes()
    storage = LocalBinaryStorage(tmp_path)
    stored = storage.store(
        [data],
        original_name="invitacion.pdf",
        content_type="application/pdf",
        expected_size=len(data),
        max_bytes=1024 * 1024,
    )
    settings = Settings(
        _env_file=None, database_url="disabled://no-db", extraction_ocr_enabled=False
    )
    document = spike.SpikeDocument("invitacion.pdf", "pdf", URL, "test-id")
    result, evidence = spike.run_existing_extractor(document, stored, storage, settings)
    assert result["status"] == "completed"
    assert result["extraction_mode"] == "native"
    assert result["text_length"] > 40
    assert evidence
    assert evidence[0].source_locator["extraction_method"] == "native_pdf_text"
    signals = spike.summarize_result(uuid.uuid4(), evidence)
    assert signals["structured_facts"] == []  # El fixture nativo contiene texto genérico.
    assert "synthetic-session" not in json.dumps(result, default=str)
    with pytest.raises(AssertionError, match="base de datos"):
        spike.deny_database()


def test_signal_groups_use_existing_structured_rule_types():
    fragment = EvidenceFragment(
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
        "test.pdf",
        0,
        "Se requiere experiencia. No se requiere RUP. Garantía de cumplimiento. "
        "Pago único. Plazo de ejecución: 10 días calendario.",
        {"page_number": 1, "extraction_method": "native_pdf_text"},
    )
    signals = spike.summarize_result(uuid.uuid4(), [fragment])
    for group in (
        "experience_requirements",
        "payment_terms",
        "execution_terms",
        "guarantees",
        "other_restrictions",
    ):
        assert signals[group], group
    assert all(fact["source_locator"]["sources"] for fact in signals["structured_facts"])
    assert asdict(fragment)["text"].startswith("Se requiere")


@pytest.mark.parametrize("fixture", ["scanned_refrigerios", "mixed_refrigerios"])
def test_existing_ocr_fallback_preserves_provenance_and_signals(tmp_path, monkeypatch, fixture):
    pytest.importorskip("pypdfium2")
    from public_procurement.extraction.adapters import hybrid, ocr

    text = (
        "JUGO HIT TETRA X 200 ML.\nCHOCORRAMO TRADICIONAL X 65 GR.\n"
        "CANTIDAD 400 PACK\nVALOR UNITARIO: $5.200\nVALOR TOTAL: $2.080.000"
    )
    engine = {
        "available": True,
        "command": "simulated",
        "language": "spa",
        "engine_version": "test",
    }
    monkeypatch.setattr(hybrid, "probe_engine", lambda *args: engine)
    monkeypatch.setattr(ocr, "recognize_image", Mock(return_value=(text, 95)))

    def recover(reader, document):
        snapshot = tmp_path / "ocr-input.pdf"
        with reader.documents.open_version(
            document.document_version_id, reader.limits.max_bytes
        ) as src:
            snapshot.write_bytes(src.read())
        return ocr.extract_ocr(snapshot, reader.limits, reader.policy, reader.pages, reader.engine)

    monkeypatch.setattr(hybrid.OcrPageExtractor, "extract", recover)
    data = (SCRIPT.parents[1] / f"tests/fixtures/extraction/{fixture}.pdf").read_bytes()
    storage = LocalBinaryStorage(tmp_path / "isolated-binaries")
    stored = storage.store(
        [data],
        original_name="invitacion.pdf",
        content_type="application/pdf",
        expected_size=len(data),
        max_bytes=1024 * 1024,
    )
    settings = Settings(
        _env_file=None, database_url="disabled://no-db", extraction_ocr_enabled=True
    )
    result, evidence = spike.run_existing_extractor(
        spike.SpikeDocument("invitacion.pdf", "pdf", URL, "test-id"),
        stored,
        storage,
        settings,
    )
    assert result["diagnostics"]["coverage_complete"] is True
    assert result["ocr_pages"] == ([1] if fixture == "scanned_refrigerios" else [2])
    assert result["extraction_mode"] == ("ocr" if fixture == "scanned_refrigerios" else "mixed")
    assert any(fragment.source_locator["extraction_method"] == "ocr_text" for fragment in evidence)
    if fixture == "mixed_refrigerios":
        assert [fragment.source_locator["page_number"] for fragment in evidence] == [1, 2, 3]
    signals = spike.summarize_result(uuid.uuid4(), evidence)
    assert signals["products_found"]
    assert signals["commercial_terms_found"]


def test_main_reads_local_ids_without_querying_real_source_or_db(tmp_path, monkeypatch):
    ids = tmp_path / "ids.txt"
    ids.write_text("40060001,40060002\n", encoding="utf-8")
    monkeypatch.setattr(
        spike, "load_session", lambda _: config(LICITACIONES_BOYACA_LOCATION_IDS="")
    )
    client = Mock()
    client.requests = 0
    factory = Mock(return_value=client)
    monkeypatch.setattr(spike, "Client", factory)
    monkeypatch.setattr(spike, "SPIKE_ROOT", tmp_path / "runs")
    monkeypatch.setattr(spike, "fetch_processes", Mock(return_value=([], 0)))
    assert spike.main(["--location-ids-file", str(ids)]) == 0
    assert factory.call_args.args[0]["LICITACIONES_BOYACA_LOCATION_IDS"] == "40060001,40060002"
    report = json.loads(
        next((tmp_path / "runs").glob("*/results.json")).read_text(encoding="utf-8")
    )
    assert report["processes"] == []
    assert "synthetic-session" not in json.dumps(report)


@pytest.mark.parametrize(
    "location",
    [
        "/login?token=VERY_SECRET#VERY_SECRET",
        "/auth/VERY_SECRET",
        "https://user:VERY_SECRET@other.invalid/login",
    ],
)
def test_redirect_diagnostic_redacts_secrets(location):
    assert "VERY_SECRET" not in auth.safe_location(location)


def test_redirect_location_keeps_known_public_target():
    assert (
        auth.safe_location("/cliente/contratos")
        == "https://col.licitaciones.info/cliente/contratos"
    )


def test_browser_header_capture_never_stores_cookie_or_password():
    headers = auth.capture_headers(
        {
            "Cookie": "secret",
            "X-XSRF-TOKEN": "local-secret",
            "password": "password-secret",
            "Origin": "unsafe",
        }
    )
    assert "cookie" not in headers
    assert "password" not in headers
    assert headers["origin"] == auth.ORIGIN
    report = auth.compare_headers({"Cookie": "secret", "X-Requested-With": "XMLHttpRequest"}, {})
    assert "secret" not in json.dumps(report)
    assert report[0] == {"header": "Cookie", "browser_200": True, "script": False}


def test_context_request_shares_cookie_jar_and_never_follows_redirects():
    context = Mock()
    response = context.request.post.return_value
    response.status = 302
    response.headers = {"location": "/login?token=secret"}
    report = auth.validate_context(
        context, {"accept": "application/json"}, {"Cookie": "secret"}, {"limit": 30}
    )
    assert report["accepted"] is False
    assert "secret" not in json.dumps(report)
    assert context.request.post.call_args.kwargs["max_redirects"] == 0
    assert context.request.post.call_args.kwargs["max_retries"] == 0
    response.dispose.assert_called_once()


def test_context_validation_requires_200_json():
    response = Mock(status=200, headers={"content-type": "application/json"})
    response.json.return_value = {"data": []}
    assert auth.validation_report(response, {}, {})["accepted"] is True
    response.headers = {"content-type": "text/html"}
    assert auth.validation_report(response, {}, {})["accepted"] is False


def test_storage_must_stay_under_ignored_spike_directory(tmp_path):
    with pytest.raises(ValueError, match="directorio local"):
        auth.local_path(tmp_path / "storage_state.json")


def test_auth_check_stops_before_any_documents_or_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(spike, "load_session", lambda _: config())
    client = Mock()
    monkeypatch.setattr(spike, "Client", Mock(return_value=client))
    fetch = Mock(side_effect=AssertionError("must not run discovery parser or documents"))
    monkeypatch.setattr(spike, "fetch_processes", fetch)
    assert spike.main(["--auth-check-only"]) == 0
    client.post.assert_called_once()
    fetch.assert_not_called()


def test_spike_playwright_session_does_not_require_manual_cookie(monkeypatch):
    session = Mock()
    factory = Mock(return_value=session)
    monkeypatch.setattr(auth, "BrowserSession", factory)
    configured = config(LICITACIONES_BASE_URL=auth.ORIGIN, LICITACIONES_COOKIE="")
    state = auth.LOCAL / "storage_state.json"
    client = spike.Client(configured, storage_state=state)
    assert client.http is session
    assert client.requests == 0
    factory.assert_called_once_with(state, auth.LOCAL / "request_headers.json")


def test_browser_session_rejects_foreign_endpoints_before_request():
    session = auth.BrowserSession.__new__(auth.BrowserSession)
    session.context = Mock()
    with pytest.raises(ValueError, match="alcance"):
        session.post("https://evil.invalid/", json={})
    session.context.request.post.assert_not_called()


@pytest.mark.parametrize(
    ("route", "status"),
    [
        ("get-info/MP", 200),
        ("get-conteo/MP", 200),
        ("get-filtro", 200),
        ("missing", 404),
    ],
)
def test_browser_trace_only_records_safe_endpoint_metadata(route, status):
    event = auth.http_event(
        auth.ORIGIN + "/cliente/contratos/" + route + "?token=secret", "POST", status
    )
    assert event["status"] == status
    assert "secret" not in json.dumps(event)
    assert set(event) == {"endpoint", "method", "status", "location"}
    assert auth.http_event("https://other.invalid/login", "GET", 403) is None
    assert auth.http_event(auth.ORIGIN + "/asset", "GET", 200) is None


def test_new_session_snapshot_preserves_existing_state_and_headers(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "LOCAL", tmp_path)
    monkeypatch.setattr(
        auth, "write_local", lambda path, data: path.write_text(json.dumps(data), encoding="utf-8")
    )
    original = tmp_path / "storage_state.json"
    original.write_bytes(b'{"cookies":[],"origins":[]}')
    header_file = tmp_path / "request_headers.json"
    header_file.write_bytes(b'{"accept":"original"}')
    before = original.read_bytes(), header_file.read_bytes()
    context = Mock()
    context.storage_state.return_value = {"cookies": [], "origins": []}
    paths = auth.save_authenticated_snapshot(context, {"accept": "new"}, {}, "unique")
    assert (original.read_bytes(), header_file.read_bytes()) == before
    assert Path(paths["state"]).name == "storage_state.candidate-unique.json"
    assert Path(paths["state"]).exists()


@pytest.fixture
def login_helper():
    spec = importlib.util.spec_from_file_location(
        "login_licitaciones_info", SCRIPT.with_name("login_licitaciones_info.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("captured", [False, True])
def test_visible_helper_keeps_browser_open_after_success_or_navigation_error(
    tmp_path,
    monkeypatch,
    login_helper,
    captured,
):
    helper = login_helper
    monkeypatch.setattr(helper, "LOCAL", tmp_path)
    monkeypatch.setattr(helper, "local_path", lambda path: path)
    clock = iter([0, 0, 99999, 99999])
    monkeypatch.setattr(helper.time, "monotonic", lambda: next(clock))
    context, browser, page = Mock(), Mock(), Mock()
    context.pages = [page]
    context.new_page.return_value = page
    page.is_closed.return_value = False
    listeners = {}
    context.on.side_effect = lambda event, callback: listeners.update({event: callback})
    if captured:
        response = Mock(url=auth.ORIGIN + auth.ENDPOINT, status=200)
        response.request.method = "POST"
        response.request.all_headers.return_value = {"accept": "application/json"}
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"data": []}
        page.goto.side_effect = lambda *args, **kwargs: listeners["response"](response)
        monkeypatch.setattr(helper, "validate_context", Mock(return_value={"accepted": True}))
        monkeypatch.setattr(helper, "save_authenticated_snapshot", Mock(return_value={}))
        monkeypatch.setattr(helper, "write_local", Mock())
    else:
        page.goto.side_effect = TimeoutError("sensitive text must not appear")
    assert helper.run_visible(None, context, browser, {}, 120, "test") == (0 if captured else 1)
    page.wait_for_timeout.assert_called_once_with(500)
    browser.close.assert_not_called()
    text = (tmp_path / "browser-network-test.jsonl").read_text(encoding="utf-8")
    assert "sensitive text" not in text
    assert '"reason": "timeout"' in text
