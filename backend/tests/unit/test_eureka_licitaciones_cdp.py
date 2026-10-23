"""Offline experiment tests: fake browser/transport, no DB or provider requests."""

import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import eureka_licitaciones_cdp as flow  # noqa: E402 -- standalone scripts directory
import licitaciones_cdp_open as opener  # noqa: E402
import licitaciones_cdp_runtime as runtime  # noqa: E402

URL = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=doc-1"
PROCESS = {
    "Link": "https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.42",
    "idContrato": 1,
    "id_fuente_contract": 3,
    "key_config": "secop2",
    "idUltimaFase": "CO1.NTC.EXAMPLE",
    "CodigoProceso": "EXAMPLE",
    "TextoDepartamento": "Boyacá : Tunja",
    "Objeto": "Suministro de refrigerios",
    "FechaPublicacion": "2026-10-19 12:00:00",
    "FechaVencimiento": "2026-10-30 09:00:00",
    "EstadoProceso": "Published",
}


def table(name="INVITACIÓN", url=URL):
    return {
        "status": 1,
        "cantidad": 1,
        "documentos": {
            "encabezados": ["Item", "Nombre", "Tipo", "Documento"],
            "campos": [
                [
                    {"id_documento": 1},
                    1,
                    name,
                    "<img src='/img/extensiones/pdf.svg'>",
                    f"<a href='{url}'>Descargar</a>",
                ]
            ],
        },
    }


def test_existing_cdp_is_reused_without_launch(monkeypatch):
    monkeypatch.setattr(opener, "cdp_active", lambda: True)
    launch = Mock()
    monkeypatch.setattr(opener.subprocess, "Popen", launch)
    assert opener.main() == 0
    launch.assert_not_called()


def test_busy_port_and_missing_edge_do_not_launch(monkeypatch, capsys):
    monkeypatch.setattr(opener, "cdp_active", lambda: False)
    monkeypatch.setattr(opener, "port_in_use", lambda: True)
    assert opener.main() == 1
    monkeypatch.setattr(opener, "port_in_use", lambda: False)
    monkeypatch.setattr(opener, "find_edge", Mock(side_effect=FileNotFoundError("Edge no existe")))
    assert opener.main() == 1
    assert "Edge no existe" in capsys.readouterr().out


def test_opener_uses_dedicated_profile_and_fixed_loopback(monkeypatch, tmp_path):
    active = iter([False, True])
    monkeypatch.setattr(opener, "cdp_active", lambda: next(active))
    monkeypatch.setattr(opener, "port_in_use", lambda: False)
    monkeypatch.setattr(opener, "find_edge", lambda: tmp_path / "msedge.exe")
    monkeypatch.setattr(opener, "PROFILE", tmp_path / "profile")
    launch = Mock()
    monkeypatch.setattr(opener.subprocess, "Popen", launch)
    assert opener.main() == 0
    args = launch.call_args.args[0]
    assert "--remote-debugging-address=127.0.0.1" in args
    assert "--remote-debugging-port=9222" in args
    assert f"--user-data-dir={tmp_path / 'profile'}" in args
    assert args[-1] == "https://licitaciones.info/"


def test_functional_tab_selection_and_ambiguous_or_wrong_host():
    page = SimpleNamespace(url="https://col.licitaciones.info/cliente/contratos#/?letra=MP")
    browser = SimpleNamespace(contexts=[SimpleNamespace(pages=[page])])
    assert runtime.find_page(browser) is page
    browser.contexts[0].pages = [page, page]
    with pytest.raises(runtime.SpikeError, match="manual"):
        runtime.find_page(browser)
    browser.contexts[0].pages = [
        SimpleNamespace(url="https://mcol.licitaciones.info/cliente/contratos")
    ]
    with pytest.raises(runtime.SpikeError):
        runtime.find_page(browser)


@pytest.mark.parametrize("status", [404, 302, None])
def test_bootstrap_failure_stops_without_login_or_secret_logging(status):
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.return_value = {"status": status, "secret": "do-not-log"}
    events = []
    client = runtime.PageClient(page, "1086005", events.append)
    with pytest.raises(runtime.SpikeError, match="manual"):
        client.bootstrap()
    assert "do-not-log" not in str(events)
    assert client.requests == 1


def test_bootstrap_200_json_and_transport_scope():
    page = Mock(url=runtime.ORIGIN + "/cliente/contratos")
    page.evaluate.return_value = {
        "status": 200,
        "json": True,
        "sameEndpoint": True,
        "configObject": True,
    }
    client = runtime.PageClient(page, "1086005", lambda _: None)
    assert client.bootstrap() == {"get_config_user_status": 200}
    with pytest.raises(runtime.SpikeError, match="alcance"):
        client.post("/wordpress-comunication/login", {})
    page.evaluate.assert_called_once()


def test_discovery_contract_and_scope_filter():
    rows = [
        PROCESS,
        {**PROCESS, "idContrato": 2, "id_fuente_contract": 2, "key_config": "secopI"},
        {**PROCESS, "idContrato": 3, "TextoDepartamento": "Colombia: Todo el pais"},
        {**PROCESS, "idContrato": 4, "Objeto": "Combustibles"},
        PROCESS,
    ]
    runtime.validate_discovery({"count": 31, "data": rows}, 30)
    eligible, excluded = runtime.filter_processes(rows, "refrigerio")
    assert [r["idContrato"] for r in eligible] == [1, 2]
    assert [r["reason"] for r in excluded] == [
        "outside_boyaca",
        "object_mismatch",
        "duplicate",
    ]


@pytest.mark.parametrize(
    "body",
    [
        {"count": 1337370, "data": [PROCESS]},
        {"count": 31, "data": [{**PROCESS, "Objeto": None}]},
        {"count": 31, "data": [{**PROCESS, "FechaPublicacion": "-"}]},
        {"count": 31, "data": "unknown"},
    ],
)
def test_invalid_discovery_is_not_a_functional_session(body):
    with pytest.raises(runtime.SpikeError):
        runtime.validate_discovery(body, 30)


def test_payload_uses_actual_local_ids_and_validated_contract(tmp_path):
    ids = ",".join(str(i) for i in range(1, 124))
    path = tmp_path / "ids.txt"
    path.write_text(ids, encoding="utf-8")
    payload = runtime.load_payload(path, "refrigerio", 30)
    assert payload["query"] == {"Objeto": "refrigerio", "ubicacion_filter": ids}
    assert payload["orderBy"] == "FechaPublicacion"
    assert payload["ascending"] == 0
    assert payload["limit"] == 30
    assert payload["page"] == 1
    path.write_text("1,1", encoding="utf-8")
    with pytest.raises(runtime.SpikeError):
        runtime.load_payload(path, "refrigerio", 30)


def test_actual_document_table_parser_and_priority():
    invitation = runtime.parse_document_page(table())[0]
    studies = runtime.parse_document_page(table("ESTUDIOS PREVIOS", URL + "2"))[0]
    other = runtime.parse_document_page(table("CDP", URL + "3"))[0]
    selected = flow.spike.select_documents([other, studies, invitation], 2)
    assert selected == [invitation, studies]
    assert invitation.source_url == URL
    assert runtime.parse_document_page({"status": 1, "documentos": []}) == []
    with pytest.raises(runtime.SpikeError):
        runtime.parse_document_page({"status": 0, "documentos": []})
    with pytest.raises(Exception, match="HTTPS"):
        runtime.parse_document_page(table(url="https://unsafe.example/file"))


def test_inventory_pages_to_empty_and_repeated_page_rejected():
    client = Mock()
    client.post.side_effect = [table(), {"status": 1, "documentos": []}]
    assert len(runtime.fetch_inventory(client, PROCESS)) == 1
    assert [call.args[1]["page"] for call in client.post.call_args_list] == [1, 2]
    client.post.side_effect = [table(), table()]
    with pytest.raises(runtime.SpikeError, match="repetida"):
        runtime.fetch_inventory(client, PROCESS)


def test_ocr_truncated_and_mixed_coverage_do_not_claim_complete():
    detail = {
        "page_count": 30,
        "status": "partial_text",
        "diagnostics": {
            "status": "ocr_truncated",
            "coverage_complete": False,
            "required_pages": list(range(1, 31)),
            "processed_pages": list(range(1, 21)),
            "successful_pages": list(range(1, 21)),
            "omitted_pages": list(range(21, 31)),
        },
    }
    result = runtime.coverage(detail)
    assert result["extraction_status"] == "ocr_truncated"
    assert len(result["processed_pages"]) == 20
    assert result["total_pages"] == 30
    assert result["coverage_ratio"] == 0.6667
    assert not result["coverage_complete"]
    mixed = runtime.coverage(
        {
            "page_count": 3,
            "status": "completed",
            "diagnostics": {
                "coverage_complete": True,
                "successful_pages": [2],
                "processed_pages": [2],
                "native_quality": [
                    {"page_number": 1, "status": "native_text_ok"},
                    {"page_number": 3, "status": "native_text_ok"},
                ],
            },
        }
    )
    assert mixed["processed_pages"] == [1, 2, 3]
    assert mixed["coverage_ratio"] == 1


def fact(**changes):
    return {
        "fact_type": "presentation",
        "numeric_value": "1509",
        "unit": "g",
        "confidence": "0.8",
        "document_version_id": "v1",
        "evidence_text": "1509 gramos",
        "source_locator": {
            "sources": [{"locator": {"page_number": 5, "extraction_method": "ocr_text"}}]
        },
        **changes,
    }


def test_suspicious_numeric_fact_retains_value_evidence_and_provenance():
    policy = json.loads(runtime.POLICY_PATH.read_text())
    original = fact()
    result = runtime.annotate_facts([original], {"v1"}, policy)[0]
    assert result["suspicious"]
    assert float(result["confidence"]) < float(original["confidence"])
    assert result["numeric_value"] == "1509"
    assert result["evidence_text"] == original["evidence_text"]
    assert result["source_locator"] == original["source_locator"]
    assert not result["usable_as_complete_evidence"]
    assert not result["document_coverage_complete"]
    assert original["confidence"] == "0.8"
    valid = runtime.annotate_facts([fact(numeric_value="150")], {"v1"}, policy)[0]
    assert not valid["suspicious"]
    assert not valid["usable_as_complete_evidence"]


def test_product_requires_evidence_and_quantities_have_review_ranges():
    policy = json.loads(runtime.POLICY_PATH.read_text())
    values = [
        fact(fact_type="product", string_value="Jugo Hit", evidence_text="Compra de sillas"),
        fact(fact_type="quantity", numeric_value="-2"),
    ]
    assert all(f["suspicious"] for f in runtime.annotate_facts(values, set(), policy))
    assert runtime.annotate_facts([fact(unit="unknown")], set(), policy)[0]["suspicious"]


def test_run_summary_counts_downloads_modes_truncation_and_facts():
    summary = runtime.summarize_run(
        {"processes": [PROCESS], "eligible": [PROCESS], "count": 31},
        [{"downloads": [{}, {}]}],
        [
            {
                "documents": [
                    {"extraction_mode": "ocr", "ocr_truncated": True},
                    {"extraction_mode": "native", "ocr_truncated": False},
                ],
                "facts": [{"suspicious": True}, {"suspicious": False}],
            }
        ],
        [],
        [{"code": "ocr_truncated"}],
    )
    assert summary["documents_downloaded"] == 2
    assert summary["ocr_truncated"] == 1
    assert summary["extraction_modes"] == {"native": 1, "ocr": 1, "mixed": 0}
    assert summary["facts_found"] == 2
    assert summary["suspicious_facts"] == 1


def test_run_bootstrap_failure_writes_all_outputs_without_documents(monkeypatch, tmp_path):
    client = Mock()
    client.requests = 1
    client.bootstrap.side_effect = runtime.SpikeError("manual login")
    monkeypatch.setattr(flow, "PageClient", lambda *args: client)
    monkeypatch.setattr(flow, "load_payload", lambda *args: {})
    args = SimpleNamespace(
        profile_id="1086005",
        term="refrigerio",
        max_processes=30,
        max_document_processes=3,
        max_documents=2,
        location_ids_file=tmp_path,
    )
    assert flow.run(Mock(), args, Mock(), tmp_path, {}) == 1
    client.post.assert_not_called()
    for name in ("discovery", "documents", "extraction", "run_summary"):
        assert (tmp_path / (name + ".json")).exists()
    assert json.loads((tmp_path / "run_summary.json").read_text())["status"] == "failed"


@pytest.mark.parametrize("fail_first", [False, True])
def test_bounded_flow_reuses_extractor_and_writes_partial_fact_annotations(
    monkeypatch, tmp_path, fail_first
):
    client = Mock()
    client.requests = 10
    client.bootstrap.return_value = {"get_config_user_status": 200}
    client.post.return_value = {
        "count": 4,
        "data": [{**PROCESS, "idContrato": n} for n in range(1, 5)],
    }
    client.post.side_effect = [{"count": 4, "data": [PROCESS]}, client.post.return_value]
    monkeypatch.setattr(flow, "PageClient", lambda *args: client)
    monkeypatch.setattr(flow, "load_payload", lambda *args: {})
    inventory = [
        runtime.parse_document_page(table("INVITACIÓN", URL + str(n)))[0] for n in range(3)
    ]
    monkeypatch.setattr(flow, "fetch_inventory", lambda *args: inventory)
    download = Mock(return_value=flow.spike.LocalBinaryStorage)
    # StoredBinary is the shared downloader's actual value type; no filesystem download.
    from public_procurement.documents.domain.document import StoredBinary

    download.return_value = StoredBinary("a" * 64, "sha256/aa/hash", 100, "application/pdf")
    if fail_first:
        download.side_effect = [
            runtime.SpikeError("download interrupted"),
            *[download.return_value] * 5,
        ]
    monkeypatch.setattr(flow.spike, "download_document", download)
    extract = Mock(
        return_value=(
            {
                "name": "INVITACIÓN.pdf",
                "status": "partial_text",
                "extraction_mode": "ocr",
                "text_length": 100,
                "page_count": 30,
                "diagnostics": {
                    "status": "ocr_truncated",
                    "processed_pages": list(range(1, 21)),
                    "omitted_pages": list(range(21, 31)),
                    "coverage_complete": False,
                },
            },
            [SimpleNamespace(document_version_id="v1")],
        )
    )
    monkeypatch.setattr(flow.spike, "run_existing_extractor", extract)
    monkeypatch.setattr(
        flow.spike, "summarize_result", lambda *args: {"structured_facts": [fact()]}
    )
    args = SimpleNamespace(
        profile_id="1086005",
        term="refrigerio",
        max_processes=30,
        max_document_processes=3,
        max_documents=2,
        location_ids_file=tmp_path,
    )
    assert flow.run(Mock(), args, Mock(), tmp_path, {"language": "spa"}) == (2 if fail_first else 0)
    assert download.call_count == 6
    assert extract.call_count == (5 if fail_first else 6)
    summary = json.loads((tmp_path / "run_summary.json").read_text())
    assert summary["processes_found"] == 4
    assert summary["processes_analyzed"] == 3
    assert summary["ocr_truncated"] == (5 if fail_first else 6)
    assert len(summary["errors"]) == int(fail_first)
    assert summary["suspicious_facts"] == 3
    assert summary["status"] == "completed_with_warnings"
    first = json.loads((tmp_path / "extraction.json").read_text())[0]
    assert first["facts"][0]["value"] == "1509"
    assert not first["facts"][0]["usable_as_complete_evidence"]


def test_no_browser_recreation_state_export_or_product_entrypoint():
    for file in ("eureka_licitaciones_cdp.py", "licitaciones_cdp_runtime.py"):
        tree = ast.parse((SCRIPTS / file).read_text(encoding="utf-8"))
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert not calls & {
            "launch",
            "new_context",
            "new_page",
            "goto",
            "storage_state",
            "cookies",
            "add_cookies",
            "close",
        }
