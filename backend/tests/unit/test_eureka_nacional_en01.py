"""Offline EN-01 smoke and shared-reader checks."""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import eureka_nacional_commercial as commercial  # noqa: E402
import eureka_nacional_en01 as en01  # noqa: E402
import eureka_nacional_experience as rules  # noqa: E402
from licitaciones_cdp_runtime import DOCUMENT_ENDPOINT  # noqa: E402
from licitaciones_freshness import BOGOTA  # noqa: E402
from spike_licitaciones_info import SpikeDocument  # noqa: E402

CUTOFF = datetime(2026, 11, 19, 12, tzinfo=BOGOTA)
REQUIRED = "El proponente deberá acreditar experiencia contractual con dos contratos ejecutados."
WAIVED = "No se exige experiencia contractual al proponente."
SECOP = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId="


def fragment(text, page=1, method="native_pdf_text"):
    return SimpleNamespace(
        text=text, source_locator={"page_number": page, "extraction_method": method}
    )


def evidence_document(text, role="primary", *, complete=True, identifier="1"):
    return {
        "document_id": identifier,
        "name": f"{role}.pdf",
        "url": SECOP + identifier,
        "sha256": "a" * 64,
        "role": role,
        "complete": complete,
        "fragments": [fragment(text)] if text else [],
    }


@pytest.mark.parametrize(
    ("clause", "expected"),
    [
        (REQUIRED, "positive"),
        (WAIVED, "negative"),
        ("La experiencia del proponente no es requisito habilitante.", "negative"),
        ("No se exige el RUP para acreditar la experiencia del oferente.", "ambiguous"),
        ("No se exige experiencia específica del proponente.", "ambiguous"),
        ("No se exige experiencia del proponente para el lote 1.", "ambiguous"),
        ("La experiencia del personal debe ser de cinco años.", None),
        ("Experiencia del proponente según el anexo 3.", "ambiguous"),
        ("Experiencia del proponente evaluada con puntos.", "ambiguous"),
        ("Experiencia mínima del proponente", "ambiguous"),
        ("Los requisitos habilitantes se detallan en el Anexo 4.", "ambiguous"),
        (
            "El proponente deberá acreditar experiencia contractual para obtener puntaje.",
            "ambiguous",
        ),
    ],
)
def test_clause_rules(clause, expected):
    assert rules.clause_rule(clause) == expected


@pytest.mark.parametrize(
    ("documents", "status"),
    [
        ([evidence_document(REQUIRED)], "experience_required"),
        ([evidence_document(WAIVED)], "no_experience_required"),
        (
            [evidence_document(WAIVED + " Los requisitos habilitantes se detallan en el Anexo 4.")],
            "experience_ambiguous",
        ),
        ([evidence_document("Pago contra entrega.")], "not_resolved"),
        ([evidence_document(WAIVED, complete=False)], "not_resolved"),
        (
            [
                evidence_document(WAIVED),
                evidence_document("", "support", complete=False, identifier="2"),
            ],
            "not_resolved",
        ),
        (
            [
                evidence_document(REQUIRED),
                evidence_document("", "amendment", complete=False, identifier="2"),
            ],
            "not_resolved",
        ),
        (
            [evidence_document(WAIVED), evidence_document(REQUIRED, "amendment", identifier="2")],
            "experience_ambiguous",
        ),
    ],
)
def test_coverage_and_conflicts(documents, status):
    assert rules.classify_experience(documents)["status"] == status


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


def test_pipeline_uses_national_pages_and_real_inventory_parser(tmp_path, monkeypatch):
    calls = []
    data = [
        row(1, "Boyacá"),
        row(2, "Bogotá"),
        row(3, "Valle del Cauca"),
        row(4, "Nariño", "Servicio de aseo"),
        row(5, "Nariño"),
        row(6, "Antioquia"),
    ]

    def post(path, payload):
        calls.append((path, payload))
        if path != DOCUMENT_ENDPOINT:
            page = payload["page"]
            return {"count": 33, "data": data[:4] if page == 1 else [data[1], *data[4:]]}
        if payload["page"] == 2:
            return {"status": 1, "documentos": []}
        identifier = payload["idContrato"]
        name = "Invitación.pdf"
        docs = [table(str(identifier), name)]
        if identifier == 2:
            docs.append(table("21", "Adenda.docx", "docx"))
        if identifier == 1:
            docs.insert(0, table("11", "Acta de liquidación.pdf"))
        return {
            "status": 1,
            "documentos": {
                "encabezados": ["Item", "Nombre", "Tipo", "Documento"],
                "campos": docs,
            },
        }

    monkeypatch.setattr(en01, "check_session", Mock())
    downloaded = []
    fixture = Path(__file__).resolve().parents[1] / "fixtures/extraction/native_refrigerios.pdf"
    pdf = fixture.read_bytes()

    def download(_client, document, storage, _settings):
        downloaded.append(document.document_id)
        return storage.store(
            [pdf],
            original_name=document.original_name,
            content_type="application/pdf",
            expected_size=len(pdf),
            max_bytes=en01.DOCUMENT_BYTES,
        )

    def extract(document, _stored, _storage, _settings):
        text = WAIVED if document.document_id == "2" else REQUIRED
        return {
            "status": "completed",
            "page_count": 1,
            "elapsed_seconds": 0.01,
            "fragments": [{"source_locator": fragment(text).source_locator}],
        }, [fragment(text)]

    monkeypatch.setattr(en01.spike, "download_document", download)
    monkeypatch.setattr(en01.spike, "run_existing_extractor", extract)
    client = SimpleNamespace(post=post, deadline=time.monotonic() + 360, requests=12)
    args = SimpleNamespace(discovery_pages=4, documents=5, processes=5, recent_days=30)
    assert en01.run(client, args, None, tmp_path, now=CUTOFF) == 0

    metrics = report(tmp_path, "metrics.json")
    assert metrics["documents_downloaded"] == 5
    assert metrics["unique_document_hashes"] == 1
    assert metrics["duplicates"] == 1
    assert metrics["supply_candidates"] == 5
    assert metrics["open_commercial_candidates"] == 5
    assert metrics["categories"]["informatica"]["matches_by_method"]["keywords"] == 5
    assert metrics["categories"]["informatica"]["resolution_rate"]["value"] == 0.8
    assert metrics["categories"]["informatica"]["operational_cost"]["downloads"] == 5
    assert (
        len(report(tmp_path, "processes.json")["exclusion_review_sample"]["primary_service"]) == 1
    )
    assert metrics["resolved"] == 4
    assert metrics["classification"]["not_resolved"] == 1
    assert metrics["by_validity"] == {
        "open": {"experience_required": 4, "not_resolved": 1},
        "closed": {},
        "unknown": {},
    }
    assert metrics["limits"]["pages_per_run_upper_bound"] == 60
    assert metrics["ai_calls"] == 0
    assert "11" not in downloaded
    assert "21" not in downloaded
    assert all(payload["query"] == {} for path, payload in calls if path != DOCUMENT_ENDPOINT)
    results = report(tmp_path, "experience_requirements.json")
    assert results[0]["evidence"][0]["page"] == 1
    assert results[0]["evidence"][0]["method"] == "native_pdf_text"
    assert results[1]["pending_document_ids"] == ["21"]
    assert report(tmp_path, "errors.json") == []


def test_repeated_provider_page_is_partial_and_counted(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "check_session", Mock())
    client = SimpleNamespace(
        post=Mock(return_value={"count": 70, "data": [row(1, "Boyacá", "Consultoría")]}),
        deadline=time.monotonic() + 360,
        requests=3,
    )
    args = SimpleNamespace(discovery_pages=4, documents=5, processes=5, recent_days=30)
    assert en01.run(client, args, None, tmp_path, now=CUTOFF) == 2
    discovery = report(tmp_path, "processes.json")
    assert discovery["stop_reason"] == "provider_repeated_page"
    assert discovery["duplicates"] == 1
    assert client.post.call_count == 2
    assert report(tmp_path, "metrics.json")["resolution_rate"]["value"] is None


def test_budget_stops_before_cdp_or_download():
    client = en01.SmokeClient(Mock(), time.monotonic())
    with pytest.raises(en01.BudgetReached, match="duration_budget"):
        client.reserve()
    client.deadline = time.monotonic() + 360
    client.requests = 55
    with pytest.raises(en01.BudgetReached, match="request_budget"):
        client.reserve(6)


def test_shared_native_extractor_reads_existing_fixture_without_db(tmp_path):
    fixture = Path(__file__).resolve().parents[1] / "fixtures/extraction/native_refrigerios.pdf"
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    stored = storage.store(
        [fixture.read_bytes()],
        original_name=fixture.name,
        content_type="application/pdf",
        expected_size=fixture.stat().st_size,
        max_bytes=en01.DOCUMENT_BYTES,
    )
    settings = en01.spike.Settings(
        _env_file=None,
        database_url="disabled://no-db",
        extraction_ocr_enabled=False,
        extraction_max_pages=en01.PAGES_PER_DOCUMENT,
    )
    document = SpikeDocument(fixture.name, "pdf", SECOP + "1", "1")
    detail, fragments = en01.spike.run_existing_extractor(document, stored, storage, settings)
    assert detail["status"] == "completed"
    assert fragments
    assert fragments[0].source_locator["extraction_method"] == "native_pdf_text"
    assert fragments[0].source_locator["page_number"] == 1


def test_discovery_preserves_completed_pages_on_provider_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "check_session", Mock())
    failure = en01.CandidateError("session_expired", "private response details")
    client = SimpleNamespace(
        post=Mock(side_effect=[{"count": 80, "data": [row(1, "Bogotá")]}, failure]),
        deadline=time.monotonic() + 360,
        requests=4,
    )
    args = SimpleNamespace(discovery_pages=4, documents=5, processes=5, recent_days=30)
    assert en01.run(client, args, None, tmp_path, now=CUTOFF) == failure.exit_code
    assert report(tmp_path, "metrics.json")["unique_processes"] == 1
    errors = report(tmp_path, "errors.json")
    assert errors == [{"stage": "cdp", "code": "session_expired", "criterion": None}]


@pytest.mark.ocr_real
@pytest.mark.skipif(os.getenv("RUN_REAL_OCR") != "1", reason="requires local Tesseract spa")
def test_shared_ocr_extractor_uses_en01_policy(tmp_path):
    fixture = Path(__file__).resolve().parents[1] / "fixtures/extraction/scanned_refrigerios.pdf"
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    stored = storage.store(
        [fixture.read_bytes()],
        original_name=fixture.name,
        content_type="application/pdf",
        expected_size=fixture.stat().st_size,
        max_bytes=en01.DOCUMENT_BYTES,
    )
    settings = en01.settings_for_run(
        tmp_path, os.getenv("EXTRACTION_TESSERACT_CMD", "tesseract"), None
    )
    document = SpikeDocument(fixture.name, "pdf", SECOP + "1", "1")
    detail, fragments = en01.spike.run_existing_extractor(document, stored, storage, settings)
    assert detail["status"] == "completed"
    assert detail["ocr_pages"] == [1]
    assert fragments[0].source_locator["extraction_method"] == "ocr_text"


@pytest.mark.parametrize(
    ("obj", "description", "unspsc", "category", "reason", "method"),
    [
        (
            "Adquisición de bienes",
            "",
            ["43211503"],
            "informatica",
            "matched_commercial_goods",
            "unspsc",
        ),
        (
            "Adquisición de bienes",
            "Computadores portátiles",
            [],
            "informatica",
            "matched_commercial_goods",
            "keywords",
        ),
        (
            "Suministro de tabletas e impresoras",
            "",
            ["43212105"],
            "informatica",
            "matched_commercial_goods",
            "both",
        ),
        (
            "Suministro de bienes",
            "",
            ["43000000", "43210000", "43219999"],
            None,
            "outside_commercial_profile",
            None,
        ),
        (
            "Suministro e instalación de cámaras de seguridad",
            "",
            ["46171610"],
            "videovigilancia",
            "matched_commercial_goods",
            "both",
        ),
        (
            "Adquisición de detergente para el servicio de aseo",
            "",
            ["47131800"],
            "aseo",
            "matched_commercial_goods",
            "both",
        ),
        (
            "Prestación del servicio de aseo con suministro de detergente",
            "",
            ["47131800"],
            None,
            "primary_service",
            None,
        ),
        (
            "Suministro de materiales de ferretería para obra civil",
            "",
            ["27111700"],
            "ferreteria",
            "matched_commercial_goods",
            "both",
        ),
        (
            "Construcción de obras civiles y suministro de materiales de ferretería",
            "",
            ["27111700"],
            None,
            "obra_civil",
            None,
        ),
        ("Compra de camioneta y repuestos", "", ["25172500"], None, "vehiculos_completos", None),
        (
            "Suministro de llantas para camionetas",
            "",
            ["25172500"],
            "repuestos",
            "matched_commercial_goods",
            "both",
        ),
        (
            "Adquisición de bienes",
            "",
            ["25132100"],
            None,
            "outside_commercial_profile",
            None,
        ),
        (
            "Adquisición de drones comerciales",
            "",
            ["25132100"],
            "drones",
            "matched_commercial_goods",
            "both",
        ),
        (
            "Adquisición de bienes",
            "",
            ["25132103"],
            "drones",
            "matched_commercial_goods",
            "unspsc",
        ),
        (
            "Adquisición de drones",
            "",
            ["25132102", "25132103"],
            None,
            "excluded_product_code",
            None,
        ),
    ],
)
def test_commercial_profile(obj, description, unspsc, category, reason, method):
    result = commercial.assess_commercial(
        commercial.load_commercial_profile(), obj, description, unspsc
    )
    assert result["primary_category"] == category
    assert result["commercial_reason"] == reason
    if category:
        assert (
            next(m["method"] for m in result["category_matches"] if m["category"] == category)
            == method
        )


def test_normalizes_only_eight_digit_unspsc_tokens():
    assert commercial.parse_unspsc([43211503, "43212105-impresora; 43211503", "432115"]) == [
        "43211503",
        "43212105",
    ]
    assert commercial.parse_unspsc({"code": "43211503"}) == []


def test_prefers_open_minimum_quantities_and_keeps_category_overlap():
    def candidate(identifier, municipality, modality=None, end="2026-11-20 09:00:00", status=None):
        return {
            **row(identifier, municipality, "Compra de computadores e impresoras y papelería"),
            "modalidad": modality,
            "FechaVencimiento": end,
            "EstadoProceso": status,
            "UNSPSC": ["43211503", "14111507"],
        }

    data = [
        candidate(1, "Bogotá", "Mínima cuantía", status="Adjudicado"),
        candidate(2, "Boyacá", "Selección abreviada"),
        candidate(3, "Valle", "Mínima cuantía"),
    ]
    args = SimpleNamespace(discovery_pages=1, processes=2, recent_days=30)
    client = SimpleNamespace(post=Mock(return_value={"count": len(data), "data": data}))
    discovery = {"pages": [], "duplicates": 0}
    profile = commercial.load_commercial_profile()
    selected = en01.discover(client, args, CUTOFF, discovery, profile)
    assert [item["id_contrato"] for item in selected] == ["3", "2"]
    assert discovery["processes"][0]["validity_status"] == "closed"
    assert discovery["processes"][0]["validity_warning"] == "terminal_provider_status"
    assert discovery["provider_fields"] == {
        "unspsc_shapes": {"list": 3},
        "unspsc_rows_parsed": 3,
        "description_rows": 0,
        "modality_rows": 3,
    }
    stats = commercial.commercial_metrics(discovery["processes"], [], profile)
    assert stats["multi_category_processes_deduplicated"] == 3
    assert stats["categories"]["papeleria"]["matches_by_method"]["both"] == 3
    assert sum(stats["candidates_by_commercial_family"].values()) == 3
