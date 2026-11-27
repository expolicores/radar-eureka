"""Offline tests for SECOP I runner stages 1 and 3. Synthetic constancias and paths only."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_en01 as en01
import eureka_nacional_secop1_flow as flow
from licitaciones_cdp_runtime import DOCUMENT_ENDPOINT
from licitaciones_freshness import BOGOTA
from spike_licitaciones_info import SpikeError

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

# Same synthetic builders as test_eureka_nacional_en01.py.
EXAMPLE_PROFILE = "1234567"
CUTOFF = datetime(2026, 11, 19, 12, tzinfo=BOGOTA)
REQUIRED = "El proponente deberá acreditar experiencia contractual con dos contratos ejecutados."
SECOP = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId="


def fragment(text, page=1, method="native_pdf_text"):
    return SimpleNamespace(
        text=text, source_locator={"page_number": page, "extraction_method": method}
    )


def row(identifier, department, description="Suministro de computadores"):
    return {
        "idContrato": identifier,
        "id_fuente_contract": 3,
        "idUltimaFase": f"CO1.NTC.{identifier}",
        "CodigoProceso": f"SIMULADO-{identifier}",
        "TextoDepartamento": department,
        "Objeto": description,
        "FechaPublicacion": "2026-11-18 13:00:00",
        "FechaVencimiento": "2026-11-20 09:00:00",
        "Link": f"https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.{identifier}",
    }


def table(doc_id, name, extension="pdf"):
    return [
        "",
        "",
        name,
        f'<img src="/img/extensiones/{extension}.svg">',
        f'<a href="{SECOP}{doc_id}">documento</a>',
    ]


def report(path, filename):
    return json.loads((path / filename).read_text(encoding="utf-8"))


CONSTANCIA = "26-13-12345678"
HEADERS = ["Nombre", "Tipo", "Tamaño", "Fecha publicación del documento", "Documento"]


def secop1_cell(path):
    return f"<a onclick='window.openDocumentoSecop1(\"{path}\")'><i></i> Descargar</a>"


def secop1_row(name, path, size="5.39 MB", extension="pdf"):
    return [
        name,
        f"<img src='/img/extensiones/{extension}.svg' class='table_icono_tipo' />",
        f"<span class='text-nowrap'>{size}</span>",
        "26-11-2026 <br> 06:27 pm",
        secop1_cell(path),
    ]


def doc_path(kind, number, constancia=CONSTANCIA):
    return f"/2020/2020Q2/2026/{kind}/111/{constancia}/{kind}_PROCESO_{constancia}_111_{number}.pdf"


def inventory_body(rows, count=None):
    return {
        "status": 1,
        "cantidad": len(rows) if count is None else count,
        "documentos": {"encabezados": HEADERS, "campos": rows},
    }


ENCINO_LIKE = [
    secop1_row("Invitación", doc_path("INVMC", 1)),
    secop1_row("ESTUDIOS PREVIOS", doc_path("DA", 2), "4.55 MB"),
    secop1_row("CDP", doc_path("DA", 3), "151 KB"),
]


def secop1_process(**changes):
    process = {
        "process_reference": "licitaciones_info:1:9",
        "source": "secop1",
        "source_identity": f"secop1:{CONSTANCIA}",
        "phase_explicit_null": True,
        "commercial_priority": 1,
        "inventory_keys": {"idContrato": "9", "id_fuente_contract": "4", "idUltimaFase": None},
    }
    return {**process, **changes}


# ---------------------------------------------------------------- stage 1: inventory


def test_parses_real_secop1_inventory_contract():
    # Arrange / Act
    documents, issues, declared = flow.parse_secop1_page(inventory_body(ENCINO_LIKE), CONSTANCIA)

    # Assert
    assert issues == []
    assert declared == 3
    assert [d["name"] for d in documents] == ["Invitación", "ESTUDIOS PREVIOS", "CDP"]
    first = documents[0]
    assert first["role"] == "primary"
    assert first["relative_path"] == doc_path("INVMC", 1)
    assert first["document_id"].startswith(f"secop1:{CONSTANCIA}:")
    assert first["displayed_size_bytes"] == round(5.39 * 1024**2)
    assert documents[2]["displayed_size_bytes"] == 151 * 1024


@pytest.mark.parametrize(
    ("cell", "code"),
    [
        (secop1_cell(doc_path("DA", 9, "26-13-99999999")), "constancia_mismatch"),
        ("<a onclick='window.open(\"/x/y.pdf\")'>x</a>", "ambiguous_document_control"),
        (
            "<a onclick='window.openDocumentoSecop1(\"/a/b.pdf\")'>a</a><a onclick=''>b</a>",
            "ambiguous_document_control",
        ),
        (secop1_cell("javascript:alert(1)"), "invalid_relative_path"),
    ],
)
def test_invalid_rows_become_issues_not_documents(cell, code):
    bad = secop1_row("PAA", doc_path("DA", 4))
    bad[4] = cell

    documents, issues, _ = flow.parse_secop1_page(
        inventory_body([*ENCINO_LIKE[:1], bad]), CONSTANCIA
    )

    assert len(documents) == 1
    assert issues == [{"row": 2, "code": code}]


@pytest.mark.parametrize(
    "body",
    [
        {"status": 0},
        {"status": 1, "documentos": {"encabezados": ["Item", "Nombre", "Tipo", "Documento"]}},
        {"status": 1, "documentos": {"encabezados": HEADERS, "campos": "x"}},
    ],
)
def test_unknown_inventory_contract_raises(body):
    with pytest.raises(SpikeError):
        flow.parse_secop1_page(body, CONSTANCIA)


def test_null_phase_is_used_only_when_explicit_and_stops_at_declared_count():
    # Arrange
    client = SimpleNamespace(post=Mock(return_value=inventory_body(ENCINO_LIKE)))

    # Act
    documents, issues, _ = flow.fetch_secop1_inventory(client, secop1_process())

    # Assert
    assert len(documents) == 3
    assert issues == []
    client.post.assert_called_once_with(
        DOCUMENT_ENDPOINT,
        {"idContrato": "9", "id_fuente_contract": "4", "idUltimaFase": None, "page": 1},
    )


@pytest.mark.parametrize(
    "process",
    [
        secop1_process(phase_explicit_null=False),
        secop1_process(source_identity="secop1:no-constancia"),
        secop1_process(source="secop2"),
        secop1_process(
            inventory_keys={"idContrato": "", "id_fuente_contract": "4", "idUltimaFase": None}
        ),
    ],
)
def test_unverified_keys_never_request_an_inventory(process):
    client = SimpleNamespace(post=Mock())

    assert flow.inventory_ready(process) is False
    with pytest.raises(SpikeError):
        flow.fetch_secop1_inventory(client, process)
    client.post.assert_not_called()


def test_paginates_without_declared_count_until_empty_page():
    pages = [inventory_body(ENCINO_LIKE[:2], count=None), {"status": 1, "documentos": []}]
    pages[0].pop("cantidad")
    client = SimpleNamespace(post=Mock(side_effect=pages))

    documents, _, _ = flow.fetch_secop1_inventory(client, secop1_process())

    assert len(documents) == 2
    assert client.post.call_count == 2


def test_repeated_inventory_page_is_rejected():
    body = inventory_body(ENCINO_LIKE[:1], count=9)
    client = SimpleNamespace(post=Mock(return_value=body))

    with pytest.raises(SpikeError, match="repetida"):
        flow.fetch_secop1_inventory(client, secop1_process())


def test_queues_only_the_governing_pdf():
    metrics = {"secop1_inventories": 0, "secop1_queued": 0}
    client = SimpleNamespace(post=Mock(return_value=inventory_body(ENCINO_LIKE)))
    documents = []

    stop, item, issues = flow.analyze_secop1_inventory(client, secop1_process(), metrics, documents)

    assert stop == "secop1_queued_for_acquisition"
    assert issues == []
    assert item["name"] == "Invitación"
    assert item["relative_path"] == doc_path("INVMC", 1)
    assert [d["selection"] for d in documents] == ["queued", "document_limit", "document_limit"]
    assert metrics == {"secop1_inventories": 1, "secop1_queued": 1}


def test_no_queue_without_identified_governing_document_or_with_issues():
    support_only = SimpleNamespace(post=Mock(return_value=inventory_body(ENCINO_LIKE[1:])))
    stop, item, _ = flow.analyze_secop1_inventory(
        support_only, secop1_process(), {"secop1_inventories": 0}, []
    )
    assert (stop, item) == ("governing_document_not_identified", None)

    bad = secop1_row("PAA", "/x/y.pdf")
    with_issue = SimpleNamespace(post=Mock(return_value=inventory_body([*ENCINO_LIKE, bad])))
    stop, item, issues = flow.analyze_secop1_inventory(
        with_issue, secop1_process(), {"secop1_inventories": 0}, []
    )
    assert (stop, item) == ("secop1_inventory_issues", None)
    assert issues[0]["code"] == "constancia_mismatch"


def queue_item(number=1, constancia=CONSTANCIA):
    return {
        "process_reference": f"licitaciones_info:1:{number}",
        "constancia": constancia,
        "document_id": f"secop1:{constancia}:{number:064d}",
        "name": "Invitación",
        "extension": "pdf",
        "relative_path": doc_path("INVMC", number, constancia),
    }


def test_queue_is_bound_to_its_digest_and_limits(tmp_path):
    queue = flow.write_queue(tmp_path, [queue_item(1), queue_item(2)], "en01-test")

    assert flow.load_queue(tmp_path)["batch_sha256"] == queue["batch_sha256"]
    assert queue["max_posts"] == 2

    tampered = json.loads((tmp_path / flow.QUEUE_FILE).read_text(encoding="utf-8"))
    tampered["items"][0]["relative_path"] = doc_path("INVMC", 7)
    (tmp_path / flow.QUEUE_FILE).write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(SpikeError, match="alterada"):
        flow.load_queue(tmp_path)


def test_queue_max_posts_never_exceeds_five(tmp_path):
    queue = flow.write_queue(tmp_path, [queue_item(n) for n in range(1, 8)], "en01-test")

    assert queue["max_posts"] == 5


# ---------------------------------------------------------------- stage 1 inside the runner

SECOP1_LINK = "https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia="


def secop1_discovery_row(identifier, department, constancia, *, explicit_null=True):
    data = {
        **row(identifier, department),
        "Link": SECOP1_LINK + constancia,
        "idUltimaFase": None,
    }
    if not explicit_null:
        data.pop("idUltimaFase")
    return data


def run_stage1(tmp_path, monkeypatch, *, include, secop1_rows):
    calls = []
    data = [row(1, "Boyacá"), row(2, "Bogotá"), *secop1_rows]
    constancias = {str(r["idContrato"]): r["Link"].rsplit("=", 1)[1] for r in secop1_rows}

    def post(path, payload):
        calls.append((path, payload))
        if path != DOCUMENT_ENDPOINT:
            return {"count": len(data), "data": data}
        identifier = str(payload["idContrato"])
        if identifier in constancias:
            constancia = constancias[identifier]
            return inventory_body(
                [
                    secop1_row("Invitación", doc_path("INVMC", 1, constancia)),
                    secop1_row("Estudios previos", doc_path("DA", 2, constancia)),
                ]
            )
        if payload["page"] == 2:
            return {"status": 1, "documentos": []}
        return {
            "status": 1,
            "documentos": {
                "encabezados": ["Item", "Nombre", "Tipo", "Documento"],
                "campos": [table(identifier, "Invitación.pdf")],
            },
        }

    monkeypatch.setattr(en01, "check_session", Mock())
    pdf = Path(__file__).resolve().parents[1] / "fixtures/extraction/native_refrigerios.pdf"
    content = pdf.read_bytes()
    downloads = []

    def download(_client, document, storage, _settings, *, diagnostics):
        downloads.append(document.document_id)
        return storage.store(
            [content],
            original_name="x.pdf",
            content_type="application/pdf",
            expected_size=len(content),
            max_bytes=en01.DOCUMENT_BYTES,
        )

    def extract(document, _stored, _storage, _settings, *, select_ocr_pages):
        return {
            "status": "completed",
            "page_count": 1,
            "elapsed_seconds": 0.01,
            "fragments": [{"source_locator": fragment(REQUIRED).source_locator}],
        }, [fragment(REQUIRED)]

    monkeypatch.setattr(en01.spike, "download_document", download)
    monkeypatch.setattr(en01.spike, "run_existing_extractor", extract)
    client = SimpleNamespace(
        post=post, profile_id=EXAMPLE_PROFILE, deadline=time.monotonic() + 360, requests=0
    )
    args = SimpleNamespace(discovery_pages=1, documents=5, processes=5, recent_days=30)
    if include is not None:
        args.include_secop1 = include
        args.secop1_processes = 5 if include else 0
    output = tmp_path / ("on" if include else "off" if include is False else "legacy")
    output.mkdir()
    code = en01.run(client, args, None, output, now=CUTOFF)
    return code, output, calls, downloads


SECOP1_ROWS = [
    secop1_discovery_row(91, "Santander", "26-13-11111111"),
    secop1_discovery_row(92, "Cauca", "26-11-22222222", explicit_null=False),
]


def secop2_view(output):
    results = report(output, "experience_requirements.json")
    return [
        {
            k: r[k]
            for k in ("process_reference", "status", "review_category", "document_stop_reason")
        }
        for r in results
        if r.get("source") != "secop1"
    ]


def test_flag_off_keeps_secop2_identical_and_excludes_secop1(tmp_path, monkeypatch):
    # Arrange / Act
    legacy = run_stage1(tmp_path, monkeypatch, include=None, secop1_rows=SECOP1_ROWS)
    off = run_stage1(tmp_path, monkeypatch, include=False, secop1_rows=SECOP1_ROWS)

    # Assert
    assert legacy[0] == off[0]
    assert legacy[3] == off[3]
    assert secop2_view(legacy[1]) == secop2_view(off[1])
    assert [c for c in legacy[2]] == [c for c in off[2]]
    for output in (legacy[1], off[1]):
        processes = report(output, "processes.json")["processes"]
        secop1 = [p for p in processes if p["source"] == "secop1"]
        assert {p["excluded_reason"] for p in secop1} == {"inventory_unavailable_for_source"}
        assert not (output / flow.QUEUE_FILE).exists()
        assert "by_source" not in report(output, "metrics.json")


def test_flag_on_adds_secop1_inventory_and_queue_without_touching_secop2(tmp_path, monkeypatch):
    off = run_stage1(tmp_path, monkeypatch, include=False, secop1_rows=SECOP1_ROWS)
    on = run_stage1(tmp_path, monkeypatch, include=True, secop1_rows=SECOP1_ROWS)

    # SECOP II: same results, same downloads, same provider requests.
    assert secop2_view(on[1]) == secop2_view(off[1])
    assert on[3] == off[3]
    secop1_calls = [p for path, p in on[2] if path == DOCUMENT_ENDPOINT and p["idContrato"] == 91]
    assert secop1_calls == [
        {"idContrato": 91, "id_fuente_contract": 3, "idUltimaFase": None, "page": 1}
    ]
    assert [c for c in on[2] if c not in off[2]] == [(DOCUMENT_ENDPOINT, secop1_calls[0])]

    processes = {
        p["process_reference"].rsplit(":", 1)[1]: p
        for p in report(on[1], "processes.json")["processes"]
    }
    assert processes["91"]["sampled"] is True
    assert processes["92"]["excluded_reason"] == "secop1_inventory_keys_unverified"

    queue = flow.load_queue(on[1])
    assert [i["constancia"] for i in queue["items"]] == ["26-13-11111111"]
    assert queue["max_posts"] == 1
    secop1_result = next(
        r for r in report(on[1], "experience_requirements.json") if r.get("source") == "secop1"
    )
    assert secop1_result["status"] == "not_resolved"
    assert secop1_result["document_stop_reason"] == "secop1_queued_for_acquisition"
    metrics = report(on[1], "metrics.json")
    assert metrics["limits"]["secop1_downloads_in_stage_1"] == 0
    assert metrics["by_source"]["secop1"]["queued_governing_pdfs"] == 1
    assert metrics["by_source"]["secop1"]["excluded_by_reason"] == {
        "secop1_inventory_keys_unverified": 1
    }
    assert metrics["secop1_inventories"] == 1


def test_secop1_quota_is_a_maximum_not_a_target(tmp_path, monkeypatch):
    rows = [secop1_discovery_row(90 + n, "Santander", f"26-13-1111111{n}") for n in range(1, 4)]

    code, output, _, _ = run_stage1(tmp_path, monkeypatch, include=True, secop1_rows=rows)

    sampled = [
        p
        for p in report(output, "processes.json")["processes"]
        if p["source"] == "secop1" and p["sampled"]
    ]
    assert len(sampled) == 3
    assert code in (0, 2)


# ---------------------------------------------------------------- stage 3: OCR plan


class FakeExtractor:
    """Scanned PDF: every page needs OCR; returns OCR text for planned pages only."""

    def __init__(self, pages, total=36):
        self.pages, self.total, self.calls = pages, total, []

    def __call__(self, document, stored, storage, settings, entry, *, ocr_pages, page_plan):
        plan = list(page_plan)[:ocr_pages]
        self.calls.append(plan)
        fragments = [
            fragment(self.pages.get(p, f"Pagina {p} sin tema"), p, "ocr_text") for p in plan
        ]
        entry.update(
            total_pages=self.total,
            pages_seen=plan,
            ocr_pages=plan,
            ocr_success_pages=plan,
            native_pages=[],
            pending_pages=[p for p in range(1, self.total + 1) if p not in plan],
            status="ocr_success",
            error_code=None,
            extraction_seconds=4.4 * len(plan),
            fragments=fragments,
            cover_metadata={},
            content_complete=False,
            complete=False,
        )


def governing_entry():
    return {
        "document_id": "secop1:x:1",
        "name": "Invitación",
        "extension": "pdf",
        "role": "primary",
        "role_hint": None,
        "role_source": "filename",
        "complete": False,
    }


def test_index_located_pages_are_read_first_and_partial_coverage_stays_unresolved():
    # Arrange: page 2 is an index pointing to page 20 for habilitation requirements.
    extractor = FakeExtractor({2: "4. REQUISITOS HABILITANTES ........ 20"})
    entry = governing_entry()

    # Act
    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    # Assert
    assert extractor.calls[0] == [1, 2]
    assert extractor.calls[1] == [20, 21]
    assert len(entry["ocr_pages"]) == 12
    assert entry["complete"] is False
    assert len(entry["pending_pages"]) == 24
    assert entry["ocr_stop_reason"] == "document_ocr_budget"
    outcome = flow.classify_experience([entry])
    assert outcome["status"] == "not_resolved"


def test_without_located_pages_reading_is_sequential_and_bounded():
    extractor = FakeExtractor({})
    entry = governing_entry()

    flow.extract_with_ocr_plan(
        extractor, None, None, None, None, entry, flow.OcrBudget(), per_document=6
    )

    assert extractor.calls == [[1, 2], [3, 4], [5, 6]]
    assert entry["ocr_stop_reason"] == "document_ocr_budget"


def test_explicit_requirement_stops_the_search():
    extractor = FakeExtractor({2: "4. REQUISITOS HABILITANTES ........ 20", 20: REQUIRED})
    entry = governing_entry()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    assert extractor.calls == [[1, 2], [20, 21]]
    assert entry["ocr_stop_reason"] == "explicit_requirement_found"


def test_run_budget_is_shared_across_documents():
    budget = flow.OcrBudget(pages=5, seconds=60)
    first, second = FakeExtractor({}), FakeExtractor({})

    flow.extract_with_ocr_plan(first, None, None, None, None, governing_entry(), budget)
    entry = governing_entry()
    flow.extract_with_ocr_plan(second, None, None, None, None, entry, budget)

    assert sum(map(len, first.calls)) == 5
    assert second.calls == [[]]
    assert entry["ocr_stop_reason"] == "run_ocr_budget"


def test_full_coverage_of_short_document_is_complete():
    extractor = FakeExtractor({}, total=3)
    entry = governing_entry()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    assert entry["pending_pages"] == []
    assert entry["complete"] is True
    assert entry["ocr_stop_reason"] == "document_complete"


# ---------------------------------------------------------------- stage 3: offline resume


def stage1_run(tmp_path, *, receipt=True, tamper=False):
    run = tmp_path / "en01-test"
    run.mkdir()
    item = queue_item(1)
    flow.write_queue(run, [item], run.name)
    documents = [
        {
            **item,
            "role": "primary",
            "role_hint": None,
            "role_source": "filename",
            "complete": False,
            "status": "queued_for_acquisition",
        }
    ]
    (run / "documents.json").write_text(
        json.dumps([{"process_reference": item["process_reference"], "documents": documents}]),
        encoding="utf-8",
    )
    (run / "processes.json").write_text(
        json.dumps(
            {
                "processes": [
                    {
                        "process_reference": item["process_reference"],
                        "department": "Santander",
                        "commercial_priority": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    if receipt:
        storage = LocalBinaryStorage(run / "binaries")
        stored = storage.store(
            [b"%PDF-1.4\n%%EOF\n"],
            original_name="x.pdf",
            content_type="application/pdf",
            expected_size=15,
            max_bytes=en01.DOCUMENT_BYTES,
        )
        record = {
            "storage_path": stored.storage_path,
            "sha256": stored.sha256,
            "observed_size": stored.observed_size,
            "content_type": "application/pdf",
        }
        if tamper:
            record["sha256"] = "0" * 64
        (run / flow.RECEIPTS_FILE).write_text(
            json.dumps({f"{item['document_id']}:pdf": record}), encoding="utf-8"
        )
    return run


def resume(tmp_path, run, extractor):
    output = tmp_path / "en01-secop1_test"
    output.mkdir()
    runner = SimpleNamespace(
        spike=en01.spike,
        StoredBinary=en01.StoredBinary,
        verify_document_type=en01.verify_document_type,
        DOCUMENT_BYTES=en01.DOCUMENT_BYTES,
        AcquisitionError=en01.AcquisitionError,
        extract_document=extractor,
    )
    before = {p.name: p.read_bytes() for p in run.iterdir() if p.is_file()}
    summary = flow.resume_secop1(run, output, settings=None, budget=flow.OcrBudget(), runner=runner)
    after = {p.name: p.read_bytes() for p in run.iterdir() if p.is_file()}
    assert before == after  # the source run is never modified
    return summary, report(output, "experience_requirements.json")


def test_resume_extracts_from_receipt_and_keeps_partial_unresolved(tmp_path):
    extractor = FakeExtractor({})
    run = stage1_run(tmp_path)

    summary, results = resume(tmp_path, run, extractor)

    assert summary["network_requests"] == 0
    assert summary["secop1_receipts_used"] == 1
    assert summary["secop1_ocr_pages"] == 12
    assert results[0]["status"] == "not_resolved"
    assert results[0]["document_stop_reason"] == "ocr_document_ocr_budget"


def test_resume_without_receipt_never_downloads(tmp_path):
    extractor = FakeExtractor({})
    run = stage1_run(tmp_path, receipt=False)

    summary, results = resume(tmp_path, run, extractor)

    assert extractor.calls == []
    assert summary["secop1_download_pending"] == 1
    assert results[0]["document_stop_reason"] == "download_pending"


def test_resume_rejects_receipt_that_does_not_match_storage(tmp_path):
    extractor = FakeExtractor({})
    run = stage1_run(tmp_path, tamper=True)

    summary, results = resume(tmp_path, run, extractor)

    assert extractor.calls == []
    assert summary["secop1_receipt_rejected"] == 1
    assert results[0]["status"] == "not_resolved"


@pytest.mark.parametrize(
    "argv",
    [
        ["--secop1-processes", "3"],
        ["--include-secop1", "--resume-inventory-from", "en01-abc"],
        ["--include-secop1", "--secop1-processes", "6"],
    ],
)
def test_cli_rejects_invalid_secop1_options(argv):
    with pytest.raises(SystemExit) as exit_info:
        en01.main(argv)

    assert exit_info.value.code == 2


def test_stage3_cli_refuses_to_overwrite_an_existing_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    (tmp_path / "en01-abc").mkdir()
    done = tmp_path / "en01-secop1_abc"
    done.mkdir()
    (done / "metrics.json").write_text("{}", encoding="utf-8")

    assert flow.main(["en01-abc"]) == 1
