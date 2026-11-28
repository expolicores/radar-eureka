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
    assert extractor.calls[0] == []  # native pass: no OCR budget
    assert extractor.calls[1] == [1, 2]  # scanned: the index is only known after OCR
    assert extractor.calls[2] == [20, 21]
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

    assert extractor.calls == [[], [1, 2], [3, 4], [5, 6]]
    assert entry["ocr_stop_reason"] == "document_ocr_budget"


def test_explicit_requirement_stops_the_search():
    extractor = FakeExtractor({2: "4. REQUISITOS HABILITANTES ........ 20", 20: REQUIRED})
    entry = governing_entry()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    assert extractor.calls[:2] == [[], [1, 2]]
    assert extractor.calls[2] == [20, 21]
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


# ---------------------------------------------------------------- A: decoupled circuit


def run_with_failing_secop2(tmp_path, monkeypatch, *, include):
    secop2_rows = [row(n, dept) for n, dept in ((1, "Boyacá"), (2, "Bogotá"), (3, "Valle"))]
    secop1_rows = [secop1_discovery_row(91, "Santander", "26-13-11111111")]
    data = [*secop2_rows, *secop1_rows]
    calls = []

    def post(path, payload):
        calls.append((path, payload))
        if path != DOCUMENT_ENDPOINT:
            return {"count": len(data), "data": data}
        identifier = str(payload["idContrato"])
        if identifier == "91":
            path91 = doc_path("INVMC", 1, "26-13-11111111")
            return inventory_body([secop1_row("Invitación", path91)])
        if payload["page"] == 2:
            return {"status": 1, "documentos": []}
        return {
            "status": 1,
            "documentos": {
                "encabezados": ["Item", "Nombre", "Tipo", "Documento"],
                "campos": [
                    table(f"{identifier}1", "Invitación.pdf"),
                    table(f"{identifier}2", "Estudios previos.pdf"),
                ],
            },
        }

    def refuse(*_args, **_kwargs):
        raise en01.AcquisitionError("http_error", "403")

    monkeypatch.setattr(en01, "check_session", Mock())
    monkeypatch.setattr(en01.spike, "download_document", refuse)
    client = SimpleNamespace(
        post=post, profile_id=EXAMPLE_PROFILE, deadline=time.monotonic() + 360, requests=0
    )
    args = SimpleNamespace(discovery_pages=1, documents=10, processes=3, recent_days=30)
    if include:
        args.include_secop1, args.secop1_processes = True, 5
    output = tmp_path / ("on" if include else "off")
    output.mkdir()
    code = en01.run(client, args, None, output, now=CUTOFF)
    return code, output, calls


def test_secop2_download_circuit_does_not_block_secop1_inventory(tmp_path, monkeypatch):
    # Arrange / Act
    code, output, calls = run_with_failing_secop2(tmp_path, monkeypatch, include=True)

    # Assert: the circuit still stops SECOP II and the run, but after SECOP I inventories.
    errors = report(output, "errors.json")
    assert code == 2
    assert {"stage": "budget", "code": "download_circuit_open"} in errors
    assert [p["idContrato"] for path, p in calls if path == DOCUMENT_ENDPOINT][-1] == 91
    assert [i["constancia"] for i in flow.load_queue(output)["items"]] == ["26-13-11111111"]
    metrics = report(output, "metrics.json")
    assert metrics["secop1_inventories"] == 1
    assert metrics["status"] == "partial"


def test_without_secop1_the_circuit_stops_exactly_as_before(tmp_path, monkeypatch):
    code, output, calls = run_with_failing_secop2(tmp_path, monkeypatch, include=False)

    assert code == 2
    assert {"stage": "budget", "code": "download_circuit_open"} in report(output, "errors.json")
    assert all(p["idContrato"] != 91 for path, p in calls if path == DOCUMENT_ENDPOINT)
    assert not (output / flow.QUEUE_FILE).exists()


@pytest.mark.parametrize("code", ["duration_budget", "request_budget", "download_close_unverified"])
def test_other_budget_stops_are_never_deferred(code):
    assert en01.is_download_circuit(en01.BudgetReached(code)) is False
    assert en01.is_download_circuit(en01.BudgetReached("download_circuit_open")) is True


# ---------------------------------------------------------------- B: inventory recovery

SELECTED = ["26-13-11111111", "26-13-22222222", "26-13-33333333"]


def persisted_run(tmp_path):
    source = tmp_path / "en01-orig"
    source.mkdir()
    processes = [
        {
            **secop1_process(),
            "process_reference": f"licitaciones_info:1:{n}",
            "source_identity": f"secop1:{c}",
            "sampled": True,
            "excluded_reason": None,
            "entity_name": f"Entidad {n}",
            "department": "Boyacá",
            "inventory_keys": {"idContrato": n, "id_fuente_contract": 4, "idUltimaFase": None},
        }
        for n, c in enumerate(SELECTED, 1)
    ]
    processes.append(
        {
            **processes[0],
            "process_reference": "licitaciones_info:1:9",
            "source_identity": "secop1:26-13-99999999",
            "sampled": False,
        }
    )
    processes.append(
        {
            **processes[0],
            "process_reference": "licitaciones_info:1:8",
            "source_identity": "secop1:26-13-88888888",
            "excluded_reason": "outside_commercial_profile",
        }
    )
    (source / "processes.json").write_text(json.dumps({"processes": processes}), "utf-8")
    output = tmp_path / "en01-secop1inv_orig"
    output.mkdir()
    return source, output


class BoundedClient:
    """Raises the runner's own budget error once the authorized requests are spent."""

    def __init__(self, limit, responses):
        self.requests, self.request_limit, self.responses, self.calls = 0, limit, responses, []

    def post(self, path, payload):
        if self.requests + 1 > self.request_limit:
            raise en01.BudgetReached("request_budget")
        self.requests += 1
        self.calls.append((path, payload))
        return self.responses(payload)


def inventory_for(payload):
    constancia = SELECTED[int(payload["idContrato"]) - 1]
    return inventory_body(
        [
            secop1_row("Invitación", doc_path("INVMC", 1, constancia)),
            secop1_row("Estudios previos", doc_path("DA", 2, constancia)),
        ]
    )


def test_recovery_uses_persisted_selection_and_one_request_per_constancia(tmp_path):
    # Arrange
    source, output = persisted_run(tmp_path)
    client = BoundedClient(2, inventory_for)

    # Act
    summary = flow.recover_secop1_inventories(
        client, source, output, SELECTED[:2], is_fatal=en01.is_recovery_fatal
    )

    # Assert
    assert [path for path, _ in client.calls] == [DOCUMENT_ENDPOINT, DOCUMENT_ENDPOINT]
    assert [p["idContrato"] for _, p in client.calls] == [1, 2]
    assert all(p["idUltimaFase"] is None for _, p in client.calls)
    assert summary["feed_requests"] == summary["downloads"] == summary["posts"] == 0
    assert summary["request_credits_used"] == 2
    queue = flow.load_queue(output)
    assert [i["constancia"] for i in queue["items"]] == SELECTED[:2]
    assert queue["batch_sha256"] == summary["batch_sha256"]
    assert report(output, "processes.json")["recovered_from"] == "en01-orig"


@pytest.mark.parametrize(
    "constancias",
    [["26-13-99999999"], ["26-13-88888888"], ["26-13-77777777"], [SELECTED[0], SELECTED[0]]],
)
def test_recovery_refuses_constancias_outside_the_persisted_selection(tmp_path, constancias):
    source, output = persisted_run(tmp_path)
    client = BoundedClient(5, inventory_for)

    with pytest.raises(SpikeError, match="seleccion persistida"):
        flow.recover_secop1_inventories(
            client, source, output, constancias, is_fatal=en01.is_recovery_fatal
        )
    assert client.calls == []


def test_process_needing_a_second_page_never_spends_another_process_credit(tmp_path):
    source, output = persisted_run(tmp_path)

    def paged(payload):
        body = inventory_for(payload)
        if payload["idContrato"] == 1:
            body["cantidad"] = 9  # the provider declares more rows than one page
        return body

    client = BoundedClient(2, paged)

    summary = flow.recover_secop1_inventories(
        client, source, output, SELECTED[:2], is_fatal=en01.is_recovery_fatal
    )

    assert client.requests == 2
    assert [p["page"] for _, p in client.calls] == [1, 1]
    assert [p["stop_reason"] for p in summary["processes"]] == [
        "inventory_failed",
        "secop1_queued_for_acquisition",
    ]
    assert report(output, "errors.json")[0]["code"] == "secop1_inventory_page_budget"
    assert [i["constancia"] for i in flow.load_queue(output)["items"]] == [SELECTED[1]]


def test_exhausted_request_budget_stops_the_recovery(tmp_path):
    source, output = persisted_run(tmp_path)
    client = BoundedClient(1, inventory_for)

    summary = flow.recover_secop1_inventories(
        client, source, output, SELECTED, is_fatal=en01.is_recovery_fatal
    )

    assert client.requests == 1
    assert summary["stopped_by"] == "request_budget"
    assert [p["stop_reason"] for p in summary["processes"]] == [
        "secop1_queued_for_acquisition",
        "request_budget",
        "not_attempted_after_request_budget",
    ]


def test_isolated_inventory_failure_is_recorded_and_recovery_continues(tmp_path):
    source, output = persisted_run(tmp_path)

    def flaky(payload):
        if payload["idContrato"] == 1:
            return {"status": 0}
        return inventory_for(payload)

    summary = flow.recover_secop1_inventories(
        BoundedClient(2, flaky), source, output, SELECTED[:2], is_fatal=en01.is_recovery_fatal
    )

    assert [p["stop_reason"] for p in summary["processes"]] == [
        "inventory_failed",
        "secop1_queued_for_acquisition",
    ]
    assert len(report(output, "errors.json")) == 1


SIX = [arg for n in range(6) for arg in ("--secop1-constancia", f"26-13-1111111{n}")]


@pytest.mark.parametrize(
    "argv",
    [
        ["--secop1-inventory-from", "en01-abc"],
        ["--secop1-constancia", "26-13-11111111"],
        ["--secop1-inventory-from", "en01-abc", "--secop1-constancia", "26-13-1x"],
        [
            "--secop1-inventory-from",
            "en01-abc",
            "--include-secop1",
            "--secop1-constancia",
            "26-13-11111111",
        ],
        ["--secop1-inventory-from", "en01-abc", *SIX],
    ],
)
def test_recovery_cli_validation(argv):
    with pytest.raises(SystemExit) as exit_info:
        en01.main(argv)

    assert exit_info.value.code == 2


def test_recovery_cli_refuses_existing_queue_and_preventive_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    source, _output = persisted_run(tmp_path)
    source.rename(tmp_path / "en01-abc")
    args = SimpleNamespace(
        secop1_inventory_from="en01-abc",
        secop1_constancia=[SELECTED[0]],
        cdp_url="http://127.0.0.1:9232",
    )
    (tmp_path / en01.streaming.MARKER_NAME).write_text("x", encoding="utf-8")
    assert en01.recover_secop1_main(args, EXAMPLE_PROFILE) == 1
    (tmp_path / en01.streaming.MARKER_NAME).unlink()
    done = tmp_path / "en01-secop1inv_abc"
    done.mkdir()
    (done / flow.QUEUE_FILE).write_text("{}", encoding="utf-8")
    assert en01.recover_secop1_main(args, EXAMPLE_PROFILE) == 1


# ---------------------------------------------------------------- displayed size admission


@pytest.mark.parametrize(
    ("shown", "reason", "known"),
    [
        (round(22.68 * 1024**2), "displayed_size_over_limit", True),
        (en01.DOCUMENT_BYTES + 1, "displayed_size_over_limit", True),
        (en01.DOCUMENT_BYTES, None, True),  # rounded value at the limit: bytes decide
        (round(2.10 * 1024**2), None, True),
        (None, None, False),  # unknown: never invented, admitted and flagged
        (0, None, False),
        ("5 MB", None, False),
    ],
)
def test_acquisition_size_check(shown, reason, known):
    assert flow.acquisition_size_check({"displayed_size_bytes": shown}) == (reason, known)


def test_oversized_governing_pdf_is_kept_in_inventory_but_not_queued():
    # Arrange
    rows = [secop1_row("Invitación", doc_path("INVMC", 1), "22.68 MB"), *ENCINO_LIKE[1:]]
    client = SimpleNamespace(post=Mock(return_value=inventory_body(rows)))
    documents = []

    # Act
    stop, item, issues = flow.analyze_secop1_inventory(
        client, secop1_process(), {"secop1_inventories": 0}, documents
    )

    # Assert
    assert (stop, item, issues) == ("governing_displayed_size_over_limit", None, [])
    assert len(documents) == 3
    assert documents[0]["selection"] == "displayed_size_over_limit"
    assert documents[0]["status"] == "excluded_from_acquisition"
    outcome = flow.classify_experience(documents)
    assert outcome["status"] == "not_resolved"
    assert outcome["review_category"] != "explicit_requirement"


def recovered_run(tmp_path, sizes):
    """Five saved inventories, queued before the size rule existed."""
    run = tmp_path / "en01-secop1inv_test"
    run.mkdir()
    constancias = [f"26-13-1111111{n}" for n in range(len(sizes))]
    processes, inventories, items = [], [], []
    for n, (constancia, size) in enumerate(zip(constancias, sizes, strict=True)):
        reference = f"licitaciones_info:1:{n}"
        documents, _, _ = flow.parse_secop1_page(
            inventory_body(
                [
                    secop1_row("Invitación", doc_path("INVMC", 1, constancia), size),
                    secop1_row("ESTUDIOS PREVIOS", doc_path("DA", 2, constancia), "1 MB"),
                ]
            ),
            constancia,
        )
        governing = documents[0]
        processes.append({"process_reference": reference, "commercial_priority": "A"})
        inventories.append({"process_reference": reference, "documents": documents})
        items.append(
            {
                "process_reference": reference,
                "constancia": constancia,
                "document_id": governing["document_id"],
                "name": governing["name"],
                "extension": "pdf",
                "relative_path": governing["relative_path"],
                "role": "primary",
                "role_hint": None,
                "displayed_size": governing["displayed_size"],
                "displayed_size_bytes": governing["displayed_size_bytes"],
            }
        )
    (run / "processes.json").write_text(json.dumps({"processes": processes}), "utf-8")
    (run / "documents.json").write_text(json.dumps(inventories), "utf-8")
    queue = flow.write_queue(run, items, run.name)
    return run, queue, constancias


SIZES = ["22.68 MB", "2.10 MB", "742 KB", "539 KB", "602 KB"]


def snapshot(run):
    return {
        p.name: p.read_bytes()
        for p in run.iterdir()
        if p.name in {"processes.json", "documents.json"}
    }


def test_rebuild_excludes_only_oversized_and_preserves_everything_else(tmp_path):
    # Arrange
    run, previous, constancias = recovered_run(tmp_path, SIZES)
    before = snapshot(run)

    # Act
    queue, record = flow.rebuild_queue(run)

    # Assert
    assert [i["constancia"] for i in queue["items"]] == constancias[1:]
    assert queue["max_posts"] == 4
    assert queue["run_id"] == previous["run_id"]
    assert [d["decision"] for d in record["decisions"]] == [
        "displayed_size_over_limit",
        "queued",
        "queued",
        "queued",
        "queued",
    ]
    assert record["network_requests"] == 0
    assert record["previous_batch_sha256"] == previous["batch_sha256"]
    assert snapshot(run) == before  # processes and inventories are never modified
    archived = run / f"secop1_queue.superseded-{previous['batch_sha256'][:16]}.json"
    assert json.loads(archived.read_text(encoding="utf-8")) == previous
    assert flow.load_queue(run)["batch_sha256"] == queue["batch_sha256"]


def test_rebuild_is_deterministic(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first_run, _, _ = recovered_run(tmp_path / "a", SIZES)
    second_run, _, _ = recovered_run(tmp_path / "b", SIZES)

    first = flow.rebuild_queue(first_run)[0]["batch_sha256"]
    again = flow.rebuild_queue(first_run)[0]["batch_sha256"]
    second = flow.rebuild_queue(second_run)[0]["batch_sha256"]

    assert first == again == second


def test_rebuild_refuses_a_queue_that_no_longer_matches_its_inventory(tmp_path):
    run, _, _ = recovered_run(tmp_path, SIZES)
    inventories = json.loads((run / "documents.json").read_text(encoding="utf-8"))
    inventories[0]["documents"].pop(0)
    (run / "documents.json").write_text(json.dumps(inventories), "utf-8")

    with pytest.raises(SpikeError, match="no coincide"):
        flow.rebuild_queue(run)


def test_rebuilt_queue_feeds_acquisition_plan_and_offline_resume(tmp_path):
    import eureka_nacional_secop1_acquire as acquire

    run, _, constancias = recovered_run(tmp_path, SIZES)
    queue, _ = flow.rebuild_queue(run)

    items, recorded = acquire.plan_batch(queue, run)
    assert [i["constancia"] for i in items] == constancias[1:]
    assert recorded == 0

    storage = LocalBinaryStorage(run / "binaries")
    pdf = b"%PDF-1.4\n%%EOF\n"
    staged = storage.store(
        [pdf],
        original_name="x.pdf",
        content_type="application/pdf",
        expected_size=len(pdf),
        max_bytes=en01.DOCUMENT_BYTES,
    )
    acquire.write_receipt(
        run,
        items[0],
        {
            "storage_path": staged.storage_path,
            "sha256": staged.sha256,
            "received_bytes": staged.observed_size,
        },
    )
    summary, results = resume(tmp_path, run, FakeExtractor({}))

    assert summary["secop1_processes"] == 4
    assert summary["secop1_receipts_used"] == 1
    assert summary["secop1_download_pending"] == 3
    assert constancias[0] not in {r["constancia"] for r in results}
    assert all(r["status"] == "not_resolved" for r in results)


def test_stage3_cli_refuses_rebuild_once_attempts_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    run, _, _ = recovered_run(tmp_path, SIZES)
    (run / "secop1_attempts").mkdir()

    assert flow.main([run.name, "--rebuild-queue"]) == 1
    assert flow.load_queue(run)["max_posts"] == 5


class MixedExtractor:
    """Native pages, scanned pages (OCR yields text), blank pages (OCR yields nothing) and
    pages the extractor refuses to OCR. Mirrors extract_document's entry fields."""

    def __init__(self, total, *, native, scanned=(), blank=(), refused=(), texts=None):
        self.total, self.native, self.scanned = total, set(native), set(scanned)
        self.blank, self.refused = set(blank), set(refused)
        self.texts, self.calls = texts or {}, []

    def __call__(self, document, stored, storage, settings, entry, *, ocr_pages, page_plan):
        plan = list(page_plan)[:ocr_pages]
        self.calls.append(plan)
        processed = [p for p in plan if p not in self.native and p not in self.refused]
        success = [p for p in processed if p in self.scanned]
        fragments = [
            fragment(self.texts.get(p, f"Texto nativo {p}"), p) for p in sorted(self.native)
        ]
        fragments += [fragment(self.texts.get(p, f"OCR {p}"), p, "ocr_text") for p in success]
        seen = sorted(self.native | set(success))
        entry.update(
            total_pages=self.total,
            pages_seen=seen,
            ocr_pages=processed,
            ocr_success_pages=success,
            native_pages=sorted(self.native),
            pending_pages=[p for p in range(1, self.total + 1) if p not in seen],
            status="ocr_success" if success else "native_success",
            error_code=None,
            extraction_seconds=0.1 + 4.4 * len(processed),
            fragments=fragments,
            cover_metadata={},
            content_complete=False,
            complete=False,
        )


def test_taraira_like_document_reads_its_only_scanned_page():
    # Arrange: 75 pages, all native except page 43 (the reported defect).
    extractor = MixedExtractor(75, native=set(range(1, 76)) - {43}, scanned={43})
    entry = governing_entry()
    budget = flow.OcrBudget()

    # Act
    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, budget)

    # Assert
    assert extractor.calls == [[], [43]]
    assert entry["ocr_candidates"] == [43]
    assert entry["ocr_pages"] == [43]
    assert entry["pending_pages"] == []
    assert entry["complete"] is True
    assert entry["ocr_stop_reason"] == "document_complete"
    assert budget.pages_left == flow.RUN_OCR_PAGES - 1


def test_native_pages_never_consume_ocr_budget_and_blank_pages_stay_pending():
    extractor = MixedExtractor(10, native={1, 2, 3, 5, 6, 8, 9, 10}, scanned={4}, blank={7})
    entry = governing_entry()
    budget = flow.OcrBudget()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, budget)

    assert extractor.calls == [[], [4, 7]]
    assert entry["ocr_pages"] == [4, 7]
    assert entry["ocr_success_pages"] == [4]
    assert entry["pending_pages"] == [7]
    assert entry["complete"] is False
    assert entry["ocr_stop_reason"] == "pages_exhausted"
    assert budget.pages_left == flow.RUN_OCR_PAGES - 2
    assert flow.classify_experience([entry])["status"] == "not_resolved"


def test_relevance_rules_prioritize_located_scanned_pages():
    texts = {2: "4. REQUISITOS HABILITANTES ........ 9"}
    extractor = MixedExtractor(
        12, native=set(range(1, 13)) - {5, 9, 12}, scanned={5, 9, 12}, texts=texts
    )
    entry = governing_entry()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    assert extractor.calls[1][0] == 9
    assert sorted(entry["ocr_pages"]) == [5, 9, 12]


def test_planned_page_the_extractor_refuses_does_not_stall_or_repeat():
    extractor = MixedExtractor(6, native={1, 2, 3}, scanned={5, 6}, refused={4})
    entry = governing_entry()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    assert extractor.calls == [[], [4, 5], [6]]
    assert entry["ocr_unprocessed_planned"] == [4]
    assert entry["pending_pages"] == [4]
    assert entry["ocr_stop_reason"] == "pages_exhausted"


def test_native_explicit_requirement_needs_no_ocr():
    extractor = MixedExtractor(5, native={1, 2, 3, 4}, scanned={5}, texts={3: REQUIRED})
    entry = governing_entry()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    assert extractor.calls == [[]]
    assert entry["ocr_stop_reason"] == "explicit_requirement_found"
    assert entry["pending_pages"] == [5]


def test_fully_native_document_is_complete_after_one_pass():
    extractor = MixedExtractor(4, native={1, 2, 3, 4})
    entry = governing_entry()

    flow.extract_with_ocr_plan(extractor, None, None, None, None, entry, flow.OcrBudget())

    assert extractor.calls == [[]]
    assert entry["complete"] is True
    assert entry["ocr_candidates"] == []


def test_resume_can_be_limited_to_one_queued_constancia(tmp_path):
    run, _, constancias = recovered_run(tmp_path, ["2.10 MB", "742 KB"])
    output = tmp_path / "en01-secop1_only"
    output.mkdir()
    runner = SimpleNamespace(
        spike=en01.spike,
        StoredBinary=en01.StoredBinary,
        verify_document_type=en01.verify_document_type,
        DOCUMENT_BYTES=en01.DOCUMENT_BYTES,
        AcquisitionError=en01.AcquisitionError,
        extract_document=FakeExtractor({}),
    )

    summary = flow.resume_secop1(
        run, output, settings=None, budget=flow.OcrBudget(), runner=runner, only=[constancias[0]]
    )

    results = report(output, "experience_requirements.json")
    assert [r["constancia"] for r in results] == [constancias[0]]
    assert summary["only_constancias"] == [constancias[0]]
    with pytest.raises(SpikeError, match="fuera de la cola"):
        flow.resume_secop1(
            run,
            output,
            settings=None,
            budget=flow.OcrBudget(),
            runner=runner,
            only=["26-13-99999999"],
        )


# ---------------------------------------------------------------- recovery batch hash


def recovery_args(**extra):
    return SimpleNamespace(
        secop1_inventory_from="en01-orig",
        secop1_constancia=SELECTED[:2],
        cdp_url="http://127.0.0.1:9232",
        **extra,
    )


def test_recovery_plan_only_prints_a_stable_hash_without_connecting(tmp_path, monkeypatch, capsys):
    # Arrange
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    persisted_run(tmp_path)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)  # any import would fail

    # Act
    code = en01.recover_secop1_main(recovery_args(secop1_plan_only=True), EXAMPLE_PROFILE)

    # Assert
    plan = json.loads(capsys.readouterr().out)
    assert code == 0
    assert plan["request_credit_limit"] == 2
    assert plan["constancias"] == sorted(SELECTED[:2])
    digest, _ = en01.secop1_recovery_digest(tmp_path / "en01-orig", list(reversed(SELECTED[:2])))
    assert plan["batch_sha256"] == digest
    assert not (tmp_path / "en01-secop1inv_orig" / flow.QUEUE_FILE).exists()


def test_recovery_refuses_a_batch_that_differs_from_the_approved_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    persisted_run(tmp_path)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)

    args = recovery_args(secop1_expect_sha256="0" * 64)

    assert en01.recover_secop1_main(args, EXAMPLE_PROFILE) == 1
    assert not (tmp_path / "en01-secop1inv_orig" / flow.QUEUE_FILE).exists()


def test_recovery_hash_changes_when_the_source_selection_changes(tmp_path):
    source, _output = persisted_run(tmp_path)
    before, _ = en01.secop1_recovery_digest(source, SELECTED[:2])
    data = json.loads((source / "processes.json").read_text(encoding="utf-8"))
    data["processes"][2]["object"] = "Otro objeto"
    (source / "processes.json").write_text(json.dumps(data), encoding="utf-8")

    after, _ = en01.secop1_recovery_digest(source, SELECTED[:2])

    assert before != after


def test_recovery_plan_refuses_constancias_outside_the_selection(tmp_path):
    source, _output = persisted_run(tmp_path)

    with pytest.raises(SpikeError, match="seleccion persistida"):
        en01.secop1_recovery_digest(source, ["26-13-99999999"])


@pytest.mark.parametrize(
    "argv",
    [
        ["--secop1-plan-only"],
        ["--secop1-expect-sha256", "a" * 64],
        [
            "--secop1-inventory-from",
            "en01-abc",
            "--secop1-constancia",
            "26-13-11111111",
            "--secop1-expect-sha256",
            "no-es-hash",
        ],
    ],
)
def test_recovery_hash_cli_validation(argv):
    with pytest.raises(SystemExit) as exit_info:
        en01.main(argv)

    assert exit_info.value.code == 2


# ---------------------------------------------------------------- recovery from the candidate queue

PENDING = "26-13-99999999"  # stored, eligible, not selected by quota
EXCLUDED = "26-13-88888888"  # stored, commercially excluded


def write_candidate_queue(source, entries, run=None):
    queue = {"run": run or source.name, "network_requests": 0, "queue": entries}
    (source / "candidate_queue.json").write_text(json.dumps(queue), "utf-8")


def queue_entry(constancia, reference, **changes):
    entry = {
        "source": "secop1",
        "source_identity": f"secop1:{constancia}",
        "process_reference": reference,
        "validity_status": "open",
        "inventory": "none",
    }
    return {**entry, **changes}


def queued_run(tmp_path):
    source, output = persisted_run(tmp_path)
    write_candidate_queue(source, [queue_entry(PENDING, "licitaciones_info:1:9")])
    return source, output


def test_queue_mode_admits_a_stored_eligible_constancia_outside_the_selection(tmp_path):
    # Arrange
    source, _output = queued_run(tmp_path)

    # Act
    _digest, core = en01.secop1_recovery_digest(source, [PENDING], from_queue=True, root=tmp_path)

    # Assert
    assert core["selection"] == "candidate_queue"
    assert core["constancias"] == [PENDING]
    assert core["request_credit_limit"] == 1
    with pytest.raises(SpikeError, match="seleccion persistida"):
        en01.secop1_recovery_digest(source, [PENDING])  # the original mode is unchanged


def test_queue_hash_is_bound_to_the_queue_contents(tmp_path):
    source, _output = queued_run(tmp_path)
    before, _ = en01.secop1_recovery_digest(source, [PENDING], from_queue=True, root=tmp_path)
    write_candidate_queue(
        source, [queue_entry(PENDING, "licitaciones_info:1:9", validity_status="unknown")]
    )

    after, _ = en01.secop1_recovery_digest(source, [PENDING], from_queue=True, root=tmp_path)

    assert before != after


@pytest.mark.parametrize(
    ("entries", "constancias", "reason"),
    [
        ([queue_entry(PENDING, "licitaciones_info:1:9")], [EXCLUDED], "fuera_de_la_cola"),
        # the queue claims an identity that the stored notice does not have
        ([queue_entry(EXCLUDED, "licitaciones_info:1:9")], [EXCLUDED], "fuera_de_la_cola"),
        ([queue_entry(PENDING, "licitaciones_info:1:404")], [PENDING], "fuera_de_la_cola"),
        (
            [queue_entry(PENDING, "licitaciones_info:1:9", validity_status="closed")],
            [PENDING],
            "cerrado",
        ),
        ([queue_entry(PENDING, "licitaciones_info:1:9")], [PENDING, PENDING], "duplicadas"),
    ],
)
def test_queue_mode_refuses_unverifiable_constancias(tmp_path, entries, constancias, reason):
    source, _output = persisted_run(tmp_path)
    write_candidate_queue(source, entries)

    with pytest.raises(SpikeError, match=reason):
        en01.secop1_recovery_digest(source, constancias, from_queue=True, root=tmp_path)


def test_queue_mode_refuses_constancias_already_inventoried_in_any_run(tmp_path):
    # Arrange: an earlier recovery already holds the inventory of the pending notice.
    source, _output = queued_run(tmp_path)
    stored = json.loads((source / "processes.json").read_text(encoding="utf-8"))["processes"]
    pending = next(p for p in stored if p["source_identity"] == f"secop1:{PENDING}")
    earlier = tmp_path / "en01-secop1inv_orig_q1"
    earlier.mkdir()
    (earlier / "processes.json").write_text(json.dumps({"processes": [pending]}), "utf-8")
    (earlier / "documents.json").write_text(
        json.dumps([{"process_reference": pending["process_reference"], "documents": [{}]}]),
        "utf-8",
    )

    # Act / Assert
    with pytest.raises(SpikeError, match="ya_inventariado"):
        en01.secop1_recovery_digest(source, [PENDING], from_queue=True, root=tmp_path)


def test_queue_for_another_run_is_refused(tmp_path):
    source, _output = persisted_run(tmp_path)
    write_candidate_queue(source, [queue_entry(PENDING, "licitaciones_info:1:9")], "en01-otra")

    with pytest.raises(SpikeError, match="no corresponde"):
        en01.secop1_recovery_digest(source, [PENDING], from_queue=True, root=tmp_path)


def test_queue_recovery_inventories_only_the_admitted_constancia(tmp_path):
    # Arrange
    source, output = queued_run(tmp_path)

    def responses(payload):
        assert payload["idContrato"] == 1  # the pending notice reuses the first keys
        return inventory_body([secop1_row("Invitación", doc_path("INVMC", 1, PENDING))])

    client = BoundedClient(1, responses)

    # Act
    summary = flow.recover_secop1_inventories(
        client, source, output, [PENDING], is_fatal=en01.is_recovery_fatal, eligible={PENDING}
    )

    # Assert
    assert client.requests == 1
    assert summary["feed_requests"] == summary["downloads"] == summary["posts"] == 0
    assert [p["constancia"] for p in summary["processes"]] == [PENDING]
    with pytest.raises(SpikeError, match="seleccion persistida"):
        flow.recover_secop1_inventories(
            BoundedClient(1, responses),
            source,
            output,
            [EXCLUDED],
            is_fatal=en01.is_recovery_fatal,
            eligible={PENDING},
        )


def test_queue_lots_get_their_own_output_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    first = en01.secop1_recovery_output("en01-orig", True)
    first.mkdir()
    (first / flow.QUEUE_FILE).write_text("{}", encoding="utf-8")

    assert first.name == "en01-secop1inv_orig_q1"
    assert en01.secop1_recovery_output("en01-orig", True).name == "en01-secop1inv_orig_q2"
    assert en01.secop1_recovery_output("en01-orig", False).name == "en01-secop1inv_orig"


@pytest.mark.parametrize(
    "argv",
    [
        ["--secop1-from-queue"],
        [
            "--secop1-inventory-from",
            "en01-abc",
            "--secop1-constancia",
            "26-13-11111111",
            "--secop1-from-queue",
        ],
    ],
)
def test_queue_recovery_cli_requires_source_and_approved_hash(argv):
    with pytest.raises(SystemExit) as exit_info:
        en01.main(argv)

    assert exit_info.value.code == 2
