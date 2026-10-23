"""Candidate-adapter hardening; entirely offline with fake CDP and HTTP."""

import copy
import json
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import eureka_licitaciones_cdp as flow  # noqa: E402
import licitaciones_candidate_contracts as contracts  # noqa: E402
import licitaciones_cdp_runtime as runtime  # noqa: E402

ROW = {
    "idContrato": 42,
    "id_fuente_contract": 3,
    "key_config": "secop2",
    "idUltimaFase": "CO1.NTC.TEST",
    "CodigoProceso": "TEST-2026",
    "TextoDepartamento": "Boyacá : Tunja",
    "Objeto": "Compra de refrigerios",
    "EntidadContratante": "Entidad de prueba",
    "FechaPublicacion": "2026-10-20 13:00:00",
    "FechaVencimiento": "2026-10-30 09:00:00",
    "EstadoProceso": "Published",
    "Valor": "7000000",
    "Link": "https://community.secop.gov.co/Public/Test",
}


@pytest.mark.parametrize("status", [401, 419])
def test_expired_session_has_actionable_message_and_exit_code(status):
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.return_value = {"status": status, "token": "secret-not-to-log"}
    events = []
    client = runtime.PageClient(page, "1086005", events.append)
    with pytest.raises(runtime.CandidateError) as result:
        client.bootstrap()
    assert result.value.code == "session_expired"
    assert result.value.exit_code == 12
    assert "manualmente y vuelve a ejecutar" in str(result.value)
    assert "secret-not-to-log" not in str(events)
    assert client.requests == 1


def test_cdp_unavailable_is_distinct_and_does_not_leak_connection_error():
    playwright = Mock()
    playwright.chromium.connect_over_cdp.side_effect = RuntimeError("secret-internals")
    with pytest.raises(runtime.CandidateError) as result:
        runtime.connect_browser(playwright, "http://127.0.0.1:9222")
    assert result.value.exit_code == 10
    assert result.value.code == "cdp_unavailable"
    assert "secret-internals" not in str(result.value)


def test_open_browser_without_contracts_has_invalid_tab_code():
    browser = Mock(contexts=[Mock(pages=[Mock(url="https://licitaciones.info/")])])
    with pytest.raises(runtime.CandidateError) as result:
        runtime.find_page(browser)
    assert result.value.code == "invalid_tab"
    assert result.value.exit_code == 11


@pytest.mark.parametrize("status", [403, 404])
def test_profile_endpoint_unavailable_has_own_code(status):
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.return_value = {"status": status}
    client = runtime.PageClient(page, "1086005", lambda _: None)
    with pytest.raises(runtime.CandidateError) as result:
        client.post("/cliente/contratos/get-info/MP?perfiles=1086005", {"limit": 1})
    assert result.value.code == "profile_unavailable"
    assert result.value.exit_code == 13


@pytest.mark.parametrize(
    "body",
    [
        {"count": 1337370, "data": [ROW]},
        {"count": 31, "data": [{**ROW, "Objeto": None}]},
        {"count": 31, "data": "html-or-unexpected"},
    ],
)
def test_invalid_generic_get_info_never_falls_back_or_fabricates_rows(body):
    with pytest.raises(runtime.CandidateError) as result:
        runtime.validate_discovery(body, 30)
    assert result.value.code == "invalid_get_info"
    assert result.value.exit_code == 14


def test_process_contract_preserves_identity_metadata_and_raw_reference():
    process = contracts.CandidateProcess.from_source(ROW, "1086005")
    data = process.to_dict()
    assert data["external_source"] == "licitaciones_info"
    assert data["profile_id"] == "1086005"
    assert data["process_reference"] == "licitaciones_info:1086005:42"
    assert data["codigo_proceso"] == "TEST-2026"
    assert data["entity_name"] == ROW["EntidadContratante"]
    assert data["object"] == ROW["Objeto"]
    assert data["department"] == "Boyacá"
    assert data["municipality"] == "Tunja"
    assert data["published_at"] == "2026-10-20T13:00:00"
    assert data["amount"] == "7000000"
    assert data["id_contrato"] == "42"
    assert data["id_fuente_contract"] == "3"
    assert data["id_ultima_fase"] == "CO1.NTC.TEST"
    assert data["key_config"] == "secop2"
    assert data["raw_source_reference"]["Link"] == ROW["Link"]
    missing = contracts.CandidateProcess.from_source(
        {**ROW, "Valor": "-", "TextoDepartamento": "Boyacá"}, "1086005"
    )
    assert missing.amount is None
    assert missing.municipality is None
    assert missing.reference == process.reference


def document_and_process():
    process = contracts.CandidateProcess.from_source(ROW, "1086005")
    document = flow.spike.SpikeDocument(
        "INVITACIÓN",
        "pdf",
        "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=123",
        "123",
    )
    detail = {
        "extraction_mode": "ocr",
        "extraction_status": "ocr_truncated",
        "total_pages": 30,
        "processed_pages": list(range(1, 21)),
        "coverage_ratio": 0.6667,
        "text_length": 100,
        "ocr_truncated": True,
        "coverage_complete": False,
    }
    return process, contracts.document_contract(process, document, flow.spike.normalized, detail)


def test_document_contract_has_received_url_identity_coverage_and_warnings():
    process, document = document_and_process()
    assert document["process_reference"] == process.reference
    assert document["document_reference"].endswith(":document:123")
    assert document["document_name"] == "INVITACIÓN"
    assert document["document_type"] == "invitation"
    assert document["secop_document_id"] == "123"
    assert document["source_url"].endswith("DocumentId=123")
    assert document["extraction_mode"] == "ocr"
    assert document["extraction_status"] == "ocr_truncated"
    assert document["total_pages"] == 30
    assert document["processed_pages"] == list(range(1, 21))
    assert document["coverage_ratio"] == 0.6667
    assert document["text_length"] == 100
    assert document["warnings"] == ["ocr_truncated", "incomplete_coverage"]


def candidate_fact(page=1, **changes):
    process, document = document_and_process()
    raw = {
        "document_version_id": "local-version",
        "fact_type": "presentation",
        "string_value": None,
        "numeric_value": "1509",
        "unit": "g",
        "normalized_value": None,
        "confidence": "0.35",
        "original_confidence": "1.0",
        "suspicious": True,
        "suspicious_reasons": ["numeric_value_outside_review_range"],
        "evidence_text": "1509 gramos",
        "usable_as_complete_evidence": False,
        "source_locator": {
            "sources": [
                {
                    "content_fragment_id": f"fragment-{page}",
                    "locator": {"page_number": page, "extraction_method": "ocr_text"},
                }
            ]
        },
    }
    return {**contracts.fact_contract(process, raw, document), **changes}


def test_fact_contract_preserves_provenance_and_partial_document_status():
    fact = candidate_fact(page=5)
    assert fact["fact_type"] == "presentation"
    assert fact["value"] == "1509"
    assert fact["unit"] == "g"
    assert fact["normalized_value"] is None
    assert fact["confidence"] == "0.35"
    assert fact["suspicious"]
    assert fact["evidence_text"] == "1509 gramos"
    assert fact["page_reference"] == 5
    assert fact["extraction_mode"] == "ocr"
    assert fact["coverage_ratio"] == 0.6667
    assert not fact["document_coverage_complete"]
    assert not fact["usable_as_complete_evidence"]
    assert fact["provenance"]["source_locator"]["sources"][0]["content_fragment_id"] == "fragment-5"


def test_exact_fact_dedup_keeps_all_occurrences_evidence_and_lowest_confidence():
    first, second = candidate_fact(1), candidate_fact(5, confidence="0.8", suspicious=False)
    before = copy.deepcopy([first, second])
    result = contracts.deduplicate_facts([first, second])
    assert len(result) == 1
    fact = result[0]
    assert fact["occurrences"] == 2
    assert fact["suspicious"]
    assert fact["confidence"] == "0.35"
    assert [
        r["source_locator"]["sources"][0]["locator"]["page_number"]
        for r in fact["provenance_records"]
    ] == [1, 5]
    assert [first, second] == before


@pytest.mark.parametrize(
    "change",
    [
        {"document_reference": "different-document"},
        {"process_reference": "different-process"},
        {"value": "150"},
        {"unit": "ml"},
        {"normalized_value": {"value": "different"}},
    ],
)
def test_dedup_never_crosses_document_process_or_value_boundaries(change):
    assert len(contracts.deduplicate_facts([candidate_fact(), candidate_fact(**change)])) == 2


def test_health_probe_checks_enriched_profile_response_without_commercial_discovery():
    client = Mock()
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.return_value = {"count": 100, "data": [ROW]}
    result = runtime.check_session(client, "1086005")
    assert result["profile_available"]
    assert result["enriched_verified"]
    path, payload = client.post.call_args.args
    assert path.endswith("MP?perfiles=1086005")
    assert payload["limit"] == 30
    assert payload["query"] == {}
    assert payload["orderBy"] == "FechaPublicacion"
    client.post.assert_called_once()


def mock_cli(monkeypatch, tmp_path):
    import playwright.sync_api

    manager = Mock()
    manager.__enter__ = Mock(return_value=Mock())
    manager.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(playwright.sync_api, "sync_playwright", lambda: manager)
    browser = Mock()
    monkeypatch.setattr(flow, "connect_browser", lambda *args: browser)
    monkeypatch.setattr(flow, "find_page", lambda *args: Mock())
    monkeypatch.setattr(flow, "LOCAL", tmp_path)
    monkeypatch.setattr(flow, "check_ocr", Mock(side_effect=AssertionError("OCR must not run")))
    monkeypatch.setattr(
        flow.spike, "Settings", Mock(side_effect=AssertionError("settings must not load"))
    )
    return browser


def test_check_session_cli_does_not_load_ids_ocr_write_files_or_close_browser(
    monkeypatch, tmp_path
):
    browser = mock_cli(monkeypatch, tmp_path)
    monkeypatch.setattr(flow, "load_payload", Mock(side_effect=AssertionError("IDs not needed")))
    monkeypatch.setattr(flow, "PageClient", Mock())
    health = Mock(return_value={"profile_available": True, "enriched_verified": True})
    monkeypatch.setattr(flow, "check_session", health)
    monkeypatch.setattr(flow, "run", Mock(side_effect=AssertionError("full run prohibited")))
    assert flow.main(["--check-session"]) == 0
    health.assert_called_once()
    browser.close.assert_not_called()
    assert not list(tmp_path.iterdir())


def test_check_session_cli_returns_session_expired_without_full_run(monkeypatch, tmp_path, capsys):
    mock_cli(monkeypatch, tmp_path)
    monkeypatch.setattr(flow, "PageClient", Mock())
    monkeypatch.setattr(
        flow,
        "check_session",
        Mock(side_effect=runtime.CandidateError("session_expired", runtime.MANUAL_LOGIN)),
    )
    assert flow.main(["--check-session"]) == 12
    assert "manualmente y vuelve a ejecutar" in capsys.readouterr().out
    assert not list(tmp_path.iterdir())


def test_discovery_only_cli_writes_contracts_and_summary_without_documents_or_ocr(
    monkeypatch, tmp_path
):
    mock_cli(monkeypatch, tmp_path)
    payload = flow.spike.build_process_payload("1,2", "refrigerio", 30)
    monkeypatch.setattr(flow, "load_payload", lambda *args: payload)
    client = Mock()
    client.requests = 3
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.side_effect = [{"count": 31, "data": [ROW]}, {"count": 31, "data": [ROW]}]
    monkeypatch.setattr(flow, "PageClient", lambda *args: client)
    monkeypatch.setattr(flow, "fetch_inventory", Mock(side_effect=AssertionError("no inventory")))
    monkeypatch.setattr(
        flow.spike, "LocalBinaryStorage", Mock(side_effect=AssertionError("no binaries"))
    )
    assert flow.main(["--discovery-only"]) == 0
    directory = next(tmp_path.iterdir())
    assert {p.name for p in directory.iterdir()} == {"discovery.json", "run_summary.json"}
    discovery = json.loads((directory / "discovery.json").read_text(encoding="utf-8"))
    assert discovery["processes"][0]["external_source"] == "licitaciones_info"
    summary = json.loads((directory / "run_summary.json").read_text())
    assert summary["mode"] == "discovery_only"
    assert summary["secop_ii_eligible"] == 1
    assert summary["documents_downloaded"] == 0
    assert summary["ocr"] is None


def test_summary_counts_coverage_modes_and_raw_vs_deduplicated_facts():
    extraction = [
        {
            "documents": [
                {"extraction_mode": "native", "ocr_truncated": False, "coverage_complete": True},
                {"extraction_mode": "ocr", "ocr_truncated": True, "coverage_complete": False},
                {"extraction_mode": "mixed", "ocr_truncated": False, "coverage_complete": True},
            ],
            "facts": [candidate_fact()],
            "raw_fact_count": 2,
        }
    ]
    summary = runtime.summarize_run({}, [], extraction, [], [])
    assert summary["full_coverage_documents"] == 2
    assert summary["partial_coverage_documents"] == 1
    assert summary["native_documents"] == 1
    assert summary["ocr_documents"] == 1
    assert summary["mixed_documents"] == 1
    assert summary["suspicious_facts"] == 1
    assert summary["facts_found"] == 1
    assert summary["raw_facts_found"] == 2
    assert summary["facts_deduplicated"] == 1


def test_document_defaults_keep_not_selected_explicit():
    process = contracts.CandidateProcess.from_source(ROW, "1086005")
    value = contracts.CandidateDocument(
        process.reference, "doc", "CDP", "other", "pdf", "123", "https://example.invalid"
    )
    assert asdict(value)["extraction_status"] == "not_selected"


def test_expired_session_during_inventory_stops_before_other_processes(monkeypatch, tmp_path):
    client = Mock()
    client.requests = 4
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.side_effect = [
        {"count": 31, "data": [ROW]},
        {"count": 31, "data": [ROW, {**ROW, "idContrato": 43}]},
    ]
    monkeypatch.setattr(flow, "PageClient", lambda *args: client)
    monkeypatch.setattr(flow, "load_payload", lambda *args: {})
    inventory = Mock(side_effect=runtime.CandidateError("session_expired", runtime.MANUAL_LOGIN))
    monkeypatch.setattr(flow, "fetch_inventory", inventory)
    args = SimpleNamespace(
        profile_id="1086005",
        term="refrigerio",
        max_processes=30,
        max_document_processes=3,
        max_documents=2,
        location_ids_file=tmp_path,
    )
    assert flow.run(Mock(), args, Mock(), tmp_path, {}) == 12
    inventory.assert_called_once()
    summary = json.loads((tmp_path / "run_summary.json").read_text())
    assert summary["status"] == "failed"
    assert summary["errors"][0]["code"] == "session_expired"
    assert summary["documents_downloaded"] == 0


def test_empty_health_response_is_not_claimed_as_healthy():
    client = Mock()
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.return_value = {"count": 0, "data": []}
    with pytest.raises(runtime.CandidateError) as error:
        runtime.check_session(client, "1086005")
    assert error.value.code == "invalid_response"


def test_preflight_diagnostic_preserves_oversized_page_warning_without_secret_logging():
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.side_effect = [
        {"status": 200, "json": True, "sameEndpoint": True, "configObject": True},
        {
            "status": 200,
            "json": True,
            "sameEndpoint": True,
            "headers": {"Authorization": "secret-not-to-log"},
            "data": {"count": 31, "data": [ROW] * 31},
        },
    ]
    events = []
    client = runtime.PageClient(page, "1086005", events.append)
    health = runtime.check_session(client, "1086005")
    assert health["warnings"][0]["code"] == "provider_ignores_limit"
    diagnostic = client.last_get_info_diagnostic
    assert diagnostic["count"] == 31
    assert diagnostic["rows_received"] == 31
    assert diagnostic["limit_requested"] == 30
    assert diagnostic["page_requested"] == 1
    assert diagnostic["payload"]["query"] == {}
    assert diagnostic["id_fuente_contract"]["present"] == 31
    assert diagnostic["key_config"]["non_empty"] == 31
    assert diagnostic["first_three_codigo_proceso"] == ["TEST-2026"] * 3
    assert diagnostic["invalid_criterion"] is None
    assert diagnostic["enriched_ratio"] == 1
    assert "secret-not-to-log" not in json.dumps(events)


def test_session_requested_one_received_thirty_warns_but_remains_healthy():
    quality = runtime.validate_session_response({"count": 31, "data": [ROW] * 30}, 1)
    assert quality["enriched_rows"] == 30
    warning = quality["warnings"][0]
    assert {k: v for k, v in warning.items() if k != "generated_at"} == {
        "code": "provider_ignores_limit",
        "requested_limit": 1,
        "rows_received": 30,
    }
    assert warning["generated_at"]


@pytest.mark.parametrize("enriched_count", [27, 24])
def test_session_accepts_reasonable_enrichment_ratio(enriched_count):
    rows = [ROW] * enriched_count + [{**ROW, "id_fuente_contract": None, "key_config": None}] * (
        30 - enriched_count
    )
    client = Mock()
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.return_value = {"count": 30, "data": rows}
    health = runtime.check_session(client, "1086005")
    assert health["enriched_verified"]
    assert health["enriched_ratio"] == enriched_count / 30
    assert health["min_enriched_ratio"] == 0.8


def test_session_rejects_insufficient_enrichment_even_when_count_is_not_generic():
    rows = [ROW] * 23 + [{**ROW, "id_fuente_contract": None, "key_config": None}] * 7
    with pytest.raises(runtime.CandidateError) as error:
        runtime.validate_session_response({"count": 30, "data": rows}, 30)
    assert error.value.code == "insufficient_enriched_rows"
    assert error.value.quality["enriched_rows"] == 23


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"count": 1337370, "data": [ROW]}, "generic_dataset"),
        ({"count": 0, "data": []}, "invalid_response"),
        ("<html>not JSON</html>", "invalid_response"),
        ({"count": 1, "data": [{"CodigoProceso": "TEST"}]}, "invalid_response"),
    ],
)
def test_session_error_categories(body, code):
    with pytest.raises(runtime.CandidateError) as error:
        runtime.validate_session_response(body, 30)
    assert error.value.code == code


def test_http_200_non_json_get_info_is_invalid_response_not_expired_session():
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.return_value = {"status": 200, "json": False, "sameEndpoint": True}
    client = runtime.PageClient(page, "1086005", lambda _: None)
    with pytest.raises(runtime.CandidateError) as error:
        client.post("/cliente/contratos/get-info/MP?perfiles=1086005", {"query": {}, "limit": 30})
    assert error.value.code == "invalid_response"


def external_row():
    return {
        **ROW,
        "Link": "https://fao.taleo.net/careersection/jobdetail.ftl",
        "idUltimaFase": None,
        "CodigoProceso": None,
        "id_fuente_contract": None,
        "key_config": None,
    }


@pytest.mark.parametrize(
    ("secop_total", "enriched", "external", "ratio"),
    [(19, 19, 11, 1), (25, 24, 5, 0.96), (30, 24, 0, 0.8)],
)
def test_preflight_uses_independent_secop_denominator(secop_total, enriched, external, ratio):
    rows = (
        [ROW] * enriched
        + [{**ROW, "key_config": None}] * (secop_total - enriched)
        + [external_row()] * external
    )
    result = runtime.validate_session_response({"count": 31, "data": rows}, 30)
    assert result["preflight_status"] == "healthy"
    assert result["rows_total"] == 30
    assert result["secop_candidates"] == secop_total
    assert result["external_candidates"] == external
    assert result["unknown_source_rows"] == 0
    assert result["secop_enriched"] == enriched
    assert result["secop_unenriched"] == secop_total - enriched
    assert result["secop_enriched_ratio"] == ratio
    assert result["min_enriched_ratio"] == 0.8


@pytest.mark.parametrize(
    "missing", ["CodigoProceso", "FechaPublicacion", "id_fuente_contract", "key_config"]
)
@pytest.mark.parametrize("remove_key", [False, True])
def test_malformed_secop_stays_in_denominator(missing, remove_key):
    row = {**ROW, missing: None}
    if remove_key:
        del row[missing]
    assert runtime.classify_preflight_source(row) == "secop_candidate"
    with pytest.raises(runtime.CandidateError) as error:
        runtime.validate_session_response({"count": 30, "data": [ROW] * 23 + [row] * 7}, 30)
    assert error.value.code == "insufficient_enriched_rows"
    assert error.value.quality["secop_candidates"] == 30
    assert error.value.quality["secop_unenriched"] == 7
    assert error.value.quality["secop_enriched_ratio"] == 23 / 30
    assert error.value.quality["preflight_status"] == "unhealthy_response"


@pytest.mark.parametrize("external", [False, True])
def test_no_identifiable_secop_is_inconclusive_not_expired(external):
    row = external_row()
    if not external:
        row["Link"] = None
    with pytest.raises(runtime.CandidateError) as error:
        runtime.validate_session_response({"count": 31, "data": [row] * 30}, 30)
    assert error.value.code == "insufficient_secop_sample"
    assert error.value.exit_code == 19
    assert error.value.quality["preflight_status"] == "inconclusive"
    assert error.value.quality["secop_enriched_ratio"] is None
    assert error.value.quality["external_candidates"] == (30 if external else 0)
    assert error.value.quality["unknown_source_rows"] == (0 if external else 30)
    assert "Inicia" not in str(error.value)


@pytest.mark.parametrize(
    ("link", "phase", "expected"),
    [
        ("https://community.secop.gov.co/Public/", None, "secop_candidate"),
        ("https://www.contratos.gov.co/consultas/", None, "secop_candidate"),
        (None, "CO1.NTC.123", "secop_candidate"),
        (None, "CO1.REQ.123", "secop_candidate"),
        (None, "CO1.NTC.TEST", "unknown_source"),
        ("https://community.secop.gov.co.evil.test/", None, "external_candidate"),
        ("https://example.test/?noticeUID=CO1.NTC.123", None, "external_candidate"),
        ("https://community.secop.gov.co@evil.test/", None, "unknown_source"),
        ("https://[invalid", None, "unknown_source"),
        (None, None, "unknown_source"),
    ],
)
def test_source_classification_does_not_depend_on_enrichment(link, phase, expected):
    row = {**external_row(), "Link": link, "idUltimaFase": phase}
    assert runtime.classify_preflight_source(row) == expected
    row.update(id_fuente_contract=3, key_config="secop2", EsSecop=True)
    assert runtime.classify_preflight_source(row) == expected
