"""Offline EN-01 smoke and shared-reader checks."""

import hashlib
import json
import os
import sys
import time
from collections import Counter
from contextlib import nullcontext
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

from public_procurement.licitaciones_cdp import configuration  # noqa: E402

EXAMPLE_PROFILE = "1234567"
NATIONAL_FILTER_SHA256 = "f4f1d02fd12e1738402c8ef4a261ff1d13a427198f26293b0d024fa8afd0619b"
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
        (REQUIRED, rules.REQ),
        (WAIVED, rules.NEG),
        ("La experiencia del proponente no es requisito habilitante.", rules.NEG),
        ("No se exige el RUP para acreditar la experiencia del oferente.", rules.CONDITIONAL),
        ("No se exige experiencia específica del proponente.", rules.CONDITIONAL),
        ("No se exige experiencia del proponente para el lote 1.", rules.CONDITIONAL),
        ("La experiencia del personal debe ser de cinco años.", rules.OTHER),
        ("Experiencia del proponente según el anexo 3.", rules.CONDITIONAL),
        ("Experiencia del proponente evaluada con puntos.", rules.OTHER),
        ("Experiencia mínima del proponente", rules.CONDITIONAL),
        ("Los requisitos habilitantes se detallan en el Anexo 4.", rules.CONDITIONAL),
        (
            "El proponente deberá acreditar experiencia contractual para obtener puntaje.",
            rules.OTHER,
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

    preflight = Mock()
    monkeypatch.setattr(en01, "check_session", preflight)
    downloaded = []
    fixture = Path(__file__).resolve().parents[1] / "fixtures/extraction/native_refrigerios.pdf"
    pdf = fixture.read_bytes()

    def download(_client, document, storage, _settings, *, diagnostics):
        downloaded.append(document.document_id)
        return storage.store(
            [pdf],
            original_name=document.original_name,
            content_type="application/pdf",
            expected_size=len(pdf),
            max_bytes=en01.DOCUMENT_BYTES,
        )

    def extract(document, _stored, _storage, _settings, *, select_ocr_pages):
        text = WAIVED if document.document_id == "2" else REQUIRED
        return {
            "status": "completed",
            "page_count": 1,
            "elapsed_seconds": 0.01,
            "fragments": [{"source_locator": fragment(text).source_locator}],
        }, [fragment(text)]

    monkeypatch.setattr(en01.spike, "download_document", download)
    monkeypatch.setattr(en01.spike, "run_existing_extractor", extract)
    client = SimpleNamespace(
        post=post, profile_id=EXAMPLE_PROFILE, deadline=time.monotonic() + 360, requests=12
    )
    args = SimpleNamespace(discovery_pages=4, documents=5, processes=5, recent_days=30)
    assert en01.run(client, args, None, tmp_path, now=CUTOFF) == 0
    preflight.assert_called_once_with(client, EXAMPLE_PROFILE, aggregator=True)
    assert all(
        path == f"/cliente/contratos/get-info/MP?perfiles={EXAMPLE_PROFILE}"
        for path, _ in calls
        if path != DOCUMENT_ENDPOINT
    )
    assert all(
        p["profile_id"] == EXAMPLE_PROFILE
        and p["process_reference"].startswith(f"licitaciones_info:{EXAMPLE_PROFILE}:")
        for p in report(tmp_path, "processes.json")["processes"]
    )

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
    assert metrics["limits"]["native_pages_per_pdf"] is None
    assert metrics["ai_calls"] == 0
    assert "11" not in downloaded
    assert "21" not in downloaded
    geography = ",".join(en01.load_national_locations())
    national_calls = [payload for path, payload in calls if path != DOCUMENT_ENDPOINT]
    assert [p["page"] for p in national_calls] == [1, 2]
    assert all(p["query"] == {"ubicacion_filter": geography} for p in national_calls)
    assert national_calls[0] == {
        "query": {"ubicacion_filter": geography},
        "limit": 30,
        "ascending": 0,
        "page": 1,
        "byColumn": 1,
        "orderBy": "FechaPublicacion",
        "columns": en01.spike.COLUMNS,
    }
    assert report(tmp_path, "processes.json")["geography"] == {
        "source": "Licitaciones.info",
        "location_count": 1130,
        "ubicacion_filter_sha256": NATIONAL_FILTER_SHA256,
    }
    results = report(tmp_path, "experience_requirements.json")
    assert results[0]["evidence"][0]["page"] == 1
    assert results[0]["evidence"][0]["method"] == "native_pdf_text"
    assert results[1]["pending_document_ids"] == ["21"]
    assert report(tmp_path, "errors.json") == []


def test_repeated_provider_page_is_partial_and_counted(tmp_path, monkeypatch):
    monkeypatch.setattr(en01, "check_session", Mock())
    client = SimpleNamespace(
        profile_id=EXAMPLE_PROFILE,
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
    client = en01.SmokeClient(Mock(), EXAMPLE_PROFILE, time.monotonic())
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
        extraction_max_pages=12,
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
        profile_id=EXAMPLE_PROFILE,
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
    from pypdf import PdfReader, PdfWriter

    fixtures = Path(__file__).resolve().parents[1] / "fixtures/extraction"
    scanned = PdfReader(fixtures / "scanned_refrigerios.pdf").pages[0]
    native = PdfReader(fixtures / "native_refrigerios.pdf").pages[0]
    path = tmp_path / "long_mixed.pdf"
    writer = PdfWriter()
    writer.add_page(scanned)
    for _ in range(13):
        writer.add_page(native)
    writer.add_page(scanned)
    writer.write(path)
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    stored = storage.store(
        [path.read_bytes()],
        original_name=path.name,
        content_type="application/pdf",
        expected_size=path.stat().st_size,
        max_bytes=en01.DOCUMENT_BYTES,
    )
    settings = en01.settings_for_run(
        tmp_path, os.getenv("EXTRACTION_TESSERACT_CMD", "tesseract"), None, ocr_pages=1
    )
    document = SpikeDocument("Invitación pública.pdf", "pdf", SECOP + "1", "1")
    entry = {"role": "primary"}
    en01.extract_document(document, stored, storage, settings, entry, ocr_pages=1)
    assert entry["total_pages"] == 15
    assert entry["native_pages"] == list(range(2, 15))
    assert entry["ocr_required_pages"] == [1, 15]
    assert entry["ocr_pages"] == entry["ocr_success_pages"] == [1]
    assert entry["pending_pages"] == [15]
    assert not entry["complete"]
    assert entry["fragments"][0].source_locator["extraction_method"] == "ocr_text"


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
    client = SimpleNamespace(
        profile_id=EXAMPLE_PROFILE, post=Mock(return_value={"count": len(data), "data": data})
    )
    discovery = {"pages": [], "duplicates": 0}
    profile = commercial.load_commercial_profile()
    selected = en01.discover(
        client, args, CUTOFF, discovery, profile, en01.load_national_locations()
    )
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


def test_geography_preserves_every_id_in_capture_order():
    ids = en01.load_national_locations()
    assert len(ids) == len(set(ids)) == 1130
    assert hashlib.sha256(",".join(ids).encode("ascii")).hexdigest() == NATIONAL_FILTER_SHA256


@pytest.mark.parametrize("error", ["count", "duplicate", "non_string", "invalid_id", "missing"])
def test_geography_rejects_invalid_capture(tmp_path, error):
    config = json.loads(en01.DEFAULT_GEOGRAPHY.read_text(encoding="utf-8-sig"))
    if error == "count":
        config["location_count"] -= 1
    elif error == "duplicate":
        config["location_ids"][-1] = config["location_ids"][0]
    elif error == "non_string":
        config["location_ids"][0] = int(config["location_ids"][0])
    elif error == "invalid_id":
        config["location_ids"][0] += " "
    else:
        config["location_ids"].pop()

    geography = tmp_path / "geography.json"
    geography.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(en01.spike.SpikeError, match=r"1.130"):
        en01.load_national_locations(geography)


@pytest.mark.parametrize(
    ("override", "env", "expected"),
    [
        (None, None, "2345678"),
        (None, EXAMPLE_PROFILE, EXAMPLE_PROFILE),
        ("3456789", EXAMPLE_PROFILE, "3456789"),
    ],
)
def test_cli_passes_resolved_profile_to_cdp(tmp_path, monkeypatch, override, env, expected):
    monkeypatch.setattr(configuration, "BACKEND", tmp_path)
    (tmp_path / ".env").write_text("LICITACIONES_PROFILE_ID=2345678\n", encoding="utf-8")
    monkeypatch.delenv("LICITACIONES_PROFILE_ID", raising=False)
    if env is not None:
        monkeypatch.setenv("LICITACIONES_PROFILE_ID", env)

    monkeypatch.setitem(
        sys.modules, "playwright.sync_api", SimpleNamespace(sync_playwright=nullcontext)
    )
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path / "runs")
    monkeypatch.setattr(en01, "settings_for_run", Mock())
    monkeypatch.setattr(en01, "connect_browser", Mock())
    monkeypatch.setattr(en01, "find_page", Mock())
    run = Mock(return_value=0)
    monkeypatch.setattr(en01, "run", run)

    assert en01.main(["--profile-id", override] if override is not None else []) == 0
    assert run.call_args.args[0].profile_id == expected


def test_cli_missing_profile_fails_before_starting_cdp(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(configuration, "BACKEND", tmp_path)
    monkeypatch.delenv("LICITACIONES_PROFILE_ID", raising=False)
    connect = Mock()
    monkeypatch.setattr(en01, "connect_browser", connect)

    assert en01.main([]) == 1
    assert "Falta LICITACIONES_PROFILE_ID" in capsys.readouterr().out
    connect.assert_not_called()


@pytest.mark.parametrize(
    ("text", "method", "kind"),
    [
        (
            "15. ACREDITACIÓN DE EXPERIENCIA MÍNIMA:\nEn este caso no se requiere de experiencia.",
            "native_pdf_text",
            rules.NEG,
        ),
        ("EXPERIENCIA: No aplica.", "native_pdf_text", rules.NEG),
        ("EXPERIENCIA:\nNO APLICA.", "native_pdf_text", rules.NEG),
        (
            "3.3 EXPERIENCIA MÍNIMA REQUERIDA:\nNo se requiere\n3.4 PROPUESTA ECONÓMICA",
            "native_pdf_text",
            rules.NEG,
        ),
        ("EXPERIENClA:\nNo se requlere.", "ocr_text", rules.NEG),
        (
            "EXPERIENCIA: El oferente deberá acreditar dos contratos ejecutados.",
            "native_pdf_text",
            rules.REQ,
        ),
        ("No se aceptarán ofertas que no acrediten experiencia.", "native_pdf_text", rules.REQ),
        (
            "Las entidades no están obligadas a establecer experiencia habilitante.",
            "native_pdf_text",
            rules.CONDITIONAL,
        ),
        (
            "Se solicitarán certificados de experiencia cuando sean exigidos.",
            "native_pdf_text",
            rules.CONDITIONAL,
        ),
        (
            "La experiencia del fabricante es obligatoria.",
            "native_pdf_text",
            rules.OTHER,
        ),
        (
            "Las mipymes aporten mínimo el 25 % de la experiencia general acreditada en la oferta.",
            "native_pdf_text",
            rules.OTHER,
        ),
        (
            "No se excluye que no se requiera experiencia del ofertante.",
            "native_pdf_text",
            rules.CONDITIONAL,
        ),
        ("No aplica.", "native_pdf_text", None),
    ],
)
def test_contextual_assertions_keep_page_provenance(text, method, kind):
    doc = evidence_document("")
    doc["fragments"] = [fragment(text, page=11, method=method)]
    result = rules.classify_experience([doc], inventory_complete=False)
    matches = [e for e in result["evidence"] if e["assertion_type"] == kind]
    if kind is None:
        assert result["evidence"] == []
    else:
        assert matches[0]["page"] == 11
        assert matches[0]["method"] == method
    assert result["status"] != "no_experience_required"


@pytest.mark.parametrize(
    ("name", "role"),
    [
        ("3.PROYECTO_PLIEGO_INVITACIÓN.pdf", "excluded"),
        ("02. Cotización previa.pdf", "excluded"),
        ("03. Invitación Pública N.pdf", "primary"),
        ("2. Adenda aplicable.pdf", "amendment"),
        ("2. ANEXO HABILITANTE.pdf", "support"),
    ],
)
def test_numbered_document_titles(name, role):
    assert rules.document_role(name) == role


def test_review_priority_distinguishes_support_and_silence():
    favorable = rules.classify_experience([evidence_document(WAIVED, "support")])
    assert favorable["status"] == "not_resolved"
    assert favorable["review_category"] == "explicit_favorable"
    silence = rules.classify_experience(
        [evidence_document("Las verificaciones se regirán por el reglamento interno.")]
    )
    assert silence["status"] == "not_resolved"
    assert silence["review_category"] == "documentary_silence"
    assert silence["dependencies"][0]["page"] == 1


def test_document_alternative_uses_remaining_attempt_without_selecting_quote(monkeypatch):
    quote = SpikeDocument("01. Cotización.pdf", "pdf", SECOP + "1", "1")
    draft = SpikeDocument("02. Proyecto_Pliego.pdf", "pdf", SECOP + "2", "2")
    rector = SpikeDocument("03. Invitación definitiva.pdf", "pdf", SECOP + "3", "3")
    annex = SpikeDocument("04. Anexo habilitante.pdf", "pdf", SECOP + "4", "4")
    monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[quote, draft, annex, rector]))
    download = Mock(
        side_effect=[
            en01.AcquisitionError("too_large", "fixture"),
            SimpleNamespace(sha256="a" * 64, observed_size=25),
        ]
    )
    monkeypatch.setattr(en01.spike, "download_document", download)
    monkeypatch.setattr(
        en01.spike,
        "run_existing_extractor",
        Mock(
            return_value=(
                {
                    "status": "completed",
                    "page_count": 1,
                    "elapsed_seconds": 0.01,
                    "fragments": [{"source_locator": fragment(WAIVED).source_locator}],
                },
                [fragment(WAIVED)],
            )
        ),
    )
    metrics, documents, errors = Counter(), [], []
    en01.analyze_documents(
        SimpleNamespace(deadline=time.monotonic() + 360),
        {"inventory_keys": {}},
        None,
        None,
        2,
        metrics,
        documents,
        errors,
    )
    assert [call.args[1] for call in download.call_args_list] == [rector, annex]
    assert metrics["documents_attempted"] == 2
    assert documents[2]["selection_reason"] == "alternative_after_limit"
    assert rules.classify_experience(documents)["review_category"] == "explicit_favorable"
    assert errors[0]["code"] == "too_large"


def test_local_replay_counts_missed_favorable_evidence():
    import eureka_nacional_replay as replay

    doc = evidence_document("")
    case = {
        "documents": [doc],
        "inventory_complete": False,
        "expected_status": "not_resolved",
        "expected_favorable": True,
    }
    assert replay.evaluate([case]) == {
        "matched": 0,
        "discrepancies": 1,
        "false_positive_favorable": 0,
        "false_negative_favorable": 1,
    }


def test_cover_metadata_records_explicit_date_and_role():
    role, version = rules.document_cover_metadata(
        "03. PLIEGO DEFINITIVO\nFecha de publicación: 23/11/2026"
    )
    assert role == "primary"
    assert version == {"version_marker": "definitivo", "labeled_date": "23/11/2026"}


def test_formats_do_not_take_the_invitation_slot(monkeypatch):
    forms = SpikeDocument("01. Formatos INVITACIÓN PÚBLICA.pdf", "pdf", SECOP + "1", "1")
    invitation = SpikeDocument("02. Invitación Pública.pdf", "pdf", SECOP + "2", "2")
    monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[forms, invitation]))
    download = Mock(side_effect=en01.AcquisitionError("too_large", "fixture"))
    monkeypatch.setattr(en01.spike, "download_document", download)
    documents = []
    en01.analyze_documents(
        SimpleNamespace(deadline=time.monotonic() + 360),
        {"inventory_keys": {}},
        None,
        None,
        1,
        Counter(),
        documents,
        [],
    )
    assert [entry["role"] for entry in documents] == ["support", "primary"]
    assert download.call_args.args[1] == invitation


def test_ocr_only_selects_low_text_pages_near_relevant_sections_or_cover():
    native = SimpleNamespace(
        document=SimpleNamespace(original_name="Invitación pública.pdf"),
        error_code=None,
        diagnostics={"native_pages_visited": 8},
        fragments=[
            SimpleNamespace(page_number=4, text="7. REQUISITOS HABILITANTES"),
            SimpleNamespace(page_number=7, text="Descripción general del contrato"),
        ],
    )
    assert en01.select_ocr_pages(native, [1, 2, 5, 8, 9], 2) == [5, 1]
    assert en01.select_ocr_pages(native, [1, 2, 5], 0) == []


def test_native_pdf_over_twelve_pages_keeps_page_provenance(tmp_path):
    from pypdf import PdfReader, PdfWriter

    from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

    fixture = Path(__file__).resolve().parents[1] / "fixtures/extraction/native_refrigerios.pdf"
    path = tmp_path / "long.pdf"
    writer = PdfWriter()
    page = PdfReader(fixture).pages[0]
    for _ in range(15):
        writer.add_page(page)
    writer.write(path)
    pdf = path.read_bytes()
    storage = LocalBinaryStorage(tmp_path / "binaries")
    stored = storage.store(
        [pdf],
        original_name=path.name,
        content_type="application/pdf",
        expected_size=len(pdf),
        max_bytes=en01.DOCUMENT_BYTES,
    )
    settings = en01.settings_for_run(tmp_path, "unavailable", None, ocr_pages=0)
    document = SpikeDocument("Invitación Pública.pdf", "pdf", SECOP + "1", "1")
    entry = {"role": "primary"}
    en01.extract_document(document, stored, storage, settings, entry, ocr_pages=0)
    assert entry["total_pages"] == 15
    assert entry["native_pages"] == list(range(1, 16))
    assert entry["pending_pages"] == entry["ocr_pages"] == []
    assert entry["complete"]
    assert entry["fragments"][-1].source_locator["page_number"] == 15

    bounded = settings.model_copy(update={"extraction_max_chars": 25})
    en01.extract_document(document, stored, storage, bounded, entry, ocr_pages=0)
    assert entry["native_stop_reason"] == "text_limit"
    assert entry["native_pages"] == [1]
    assert entry["fragments"][0].source_locator["char_end"] == 25
    assert entry["pending_pages"] == list(range(1, 16))
    assert not entry["complete"]


def test_native_checkpoint_recovers_pages_when_worker_times_out(tmp_path, monkeypatch):
    import hashlib
    import json
    import subprocess
    import uuid
    from contextlib import contextmanager

    from public_procurement.extraction.adapters.isolated import IsolatedExtractor
    from public_procurement.extraction.domain.content import DocumentInput, ExtractionLimits

    snapshot = tmp_path / "fixture.pdf"
    data = b"%PDF-1.7"
    snapshot.write_bytes(data)

    @contextmanager
    def open_version(*_args):
        with snapshot.open("rb") as stream:
            yield stream

    def timeout(request):
        checkpoint = Path(request["checkpoint"])
        records = [
            {"page_count": 20},
            {
                "page_number": 1,
                "boundary": None,
                "empty": False,
                "fragments": [
                    {
                        "ordinal": 1,
                        "text": "Texto de la primera página",
                        "page_number": 1,
                        "source_locator": {"page_number": 1},
                    }
                ],
            },
        ]
        checkpoint.write_text(
            "".join(json.dumps(record) + "\n" for record in records) + '{"unfinished":',
            encoding="utf-8",
        )
        raise subprocess.TimeoutExpired("reader", 12)

    source = SimpleNamespace(open_version=open_version)
    extractor = IsolatedExtractor(source, ExtractionLimits(max_pages=None))
    monkeypatch.setattr(extractor, "run_worker", timeout)
    document = DocumentInput(
        uuid.uuid4(),
        uuid.uuid4(),
        "fixture.pdf",
        hashlib.sha256(data).hexdigest(),
        len(data),
    )
    result = extractor.extract(document)
    assert result.page_count == 20
    assert result.fragments[0].page_number == 1
    assert result.diagnostics["native_stop_reason"] == "timeout"
    assert result.diagnostics["native_incomplete_from"] == 2


@pytest.mark.parametrize(
    ("text", "section"),
    [
        (
            "12.3.1. EXPERIENCIA GENERAL\nEl proponente debe acredita r experiencia, "
            "median te la presentación de dos contratos.",
            "EXPERIENCIA GENERAL",
        ),
        (
            "8.6.) EXPERIENCIA:\nEXPERIENCIA GENERAL (Admisible/No Admisible):\n"
            "Acreditar experiencia mediante la presentación de mínimo dos contratos ejecutados.",
            "EXPERIENCIA GENERAL (Admisible/No Admisible)",
        ),
        (
            "2.5.1 EXPERIENCIA ESPECÍFICA DEL PROPONENTE\n"
            "El proponente deberá acreditar experiencia específica con contratos.",
            "EXPERIENCIA ESPECÍFICA DEL PROPONENTE",
        ),
    ],
)
def test_contextual_general_requirements_allow_early_commercial_deprioritization(text, section):
    doc = evidence_document("")
    doc["fragments"] = [fragment(text, page=27)]
    unknown = {
        "document_id": "other",
        "name": "Otro documento",
        "role": "unknown",
        "complete": False,
    }
    result = rules.classify_experience([doc, unknown])
    assert result["status"] == "not_resolved"
    assert result["reason"] == "requirement_requires_corroboration"
    assert result["review_category"] == "explicit_requirement"
    assert result["review_reason"] == "general_bidder_clause_in_complete_primary"
    assert result["review_evidence"][0]["section"] == section
    assert result["review_evidence"][0]["page"] == 27
    assert result["document_coverage"]["pending"] == [
        {"document_id": "other", "document": "Otro documento", "role": "unknown"}
    ]
    unknown["role"] = "amendment"
    pending_amendment = rules.classify_experience([doc, unknown])
    assert pending_amendment["review_category"] == "insufficient_evidence"


def test_mipyme_heading_applies_to_following_page_with_same_document():
    doc = evidence_document("")
    clause = (
        "El proponente deberá acreditar experiencia específica con certificaciones de contratos."
    )
    doc["fragments"] = [
        fragment("5.1.2.2. EXPERIENCIA ESPECÍFICA: " + clause, page=19),
        fragment("5.1.2.3. EXPERIENCIA MIPYME:", page=21),
        fragment("INVITACIÓN PÚBLICA\n" + clause, page=22),
    ]
    result = rules.classify_experience([doc])
    scopes = [
        (e["scope"], e["assertion_type"], e["page"], e["section_page"]) for e in result["evidence"]
    ]
    assert scopes == [("general_bidder", rules.REQ, 19, 19), ("limited", rules.CONDITIONAL, 22, 21)]
    assert result["status"] == "experience_required"
    assert [e["page"] for e in result["review_evidence"]] == [19]


def test_plural_rule_alone_stays_limited():
    doc = evidence_document("")
    doc["fragments"] = [
        fragment(
            "En el caso de los consorcios, la experiencia habilitante será la suma "
            "de la experiencia de los integrantes.",
            page=11,
        )
    ]
    result = rules.classify_experience([doc])
    assert result["status"] == "experience_ambiguous"
    assert result["review_category"] == "limited_or_ambiguous"
    assert result["review_evidence"][0]["scope"] == "limited"


def test_experience_form_records_missing_primary_without_treating_form_as_requirement():
    form = evidence_document("Anexo 6\nFormato experiencia del proponente", role="support")
    rector = {
        "document_id": "rector",
        "name": "Invitación pública",
        "role": "primary",
        "complete": False,
    }
    result = rules.classify_experience([form, rector])
    assert result["status"] == "not_resolved"
    assert result["review_category"] == "insufficient_evidence"
    assert result["document_coverage"]["pending"][0]["document_id"] == "rector"


def test_waiver_and_silence_keep_distinct_commercial_and_formal_results():
    support = {"document_id": "annex", "name": "Anexo", "role": "support", "complete": False}
    waiver = evidence_document("EXPERIENCIA: No aplica.")
    result = rules.classify_experience([waiver, support])
    assert result["status"] == "not_resolved"
    assert result["review_category"] == "explicit_favorable"
    assert result["review_evidence"][0]["assertion_type"] == rules.NEG
    silence = rules.classify_experience([evidence_document("Presentar el anexo técnico.")])
    assert silence["status"] == "not_resolved"
    assert silence["review_category"] == "documentary_silence"
    assert silence["review_evidence"] == []


def test_conflicting_waiver_blocks_early_commercial_deprioritization():
    doc = evidence_document("")
    doc["fragments"] = [
        fragment(
            "2.5.1 EXPERIENCIA ESPECÍFICA DEL PROPONENTE\n"
            "El proponente deberá acreditar experiencia con contratos.",
            page=3,
        ),
        fragment(WAIVED, page=6),
    ]
    result = rules.classify_experience([doc])
    assert result["status"] == "experience_ambiguous"
    assert result["review_category"] == "limited_or_ambiguous"
    assert {e["assertion_type"] for e in result["review_evidence"]} == {rules.NEG, rules.REQ}


def test_exploratory_credit_guard_is_opt_in():
    page = Mock()
    deadline = time.monotonic() + 360
    regular = en01.SmokeClient(page, EXAMPLE_PROFILE, deadline)
    regular.requests = 60
    with pytest.raises(en01.BudgetReached, match="request_budget"):
        regular.reserve()
    exploratory = en01.SmokeClient(
        page, EXAMPLE_PROFILE, deadline, request_limit=en01.EXPLORATORY_REQUEST_CREDITS
    )
    exploratory.requests = 194
    exploratory.reserve(6)
    assert exploratory.requests == 200
    with pytest.raises(en01.BudgetReached, match="request_budget"):
        exploratory.reserve()


def test_exploratory_cli_uses_bounded_preset_without_cdp(monkeypatch, tmp_path):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", EXAMPLE_PROFILE)
    monkeypatch.setitem(
        sys.modules, "playwright.sync_api", SimpleNamespace(sync_playwright=nullcontext)
    )
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path / "runs")
    monkeypatch.setattr(en01, "settings_for_run", Mock())
    monkeypatch.setattr(en01, "connect_browser", Mock())
    monkeypatch.setattr(en01, "find_page", Mock())
    run = Mock(return_value=0)
    monkeypatch.setattr(en01, "run", run)
    assert en01.main(["--exploratory"]) == 0
    client, args, *_ = run.call_args.args
    assert (args.processes, args.discovery_pages, args.documents) == (15, 8, 24)
    assert client.request_limit == 200
    assert 710 < client.deadline - time.monotonic() <= 720
    with pytest.raises(SystemExit):
        en01.main(["--exploratory", "--processes", "16"])
    assert run.call_count == 1


def test_exploratory_progression_records_requirement_waiver_and_silence(monkeypatch, tmp_path):
    def doc(name, identifier):
        return SpikeDocument(name, "pdf", SECOP + identifier, identifier)

    histories = {
        1: [
            doc("Invitación.pdf", "1"),
            doc("Anexo habilitante.pdf", "11"),
            doc("Estudio de mercado.pdf", "12"),
        ],
        2: [
            doc("Invitación.pdf", "2"),
            doc("Formato de experiencia.pdf", "23"),
            doc("Anexo habilitante.pdf", "22"),
        ],
        3: [doc("Invitación.pdf", "3"), doc("Anexo habilitante.pdf", "31")],
    }
    texts = {
        "1": "2.1 EXPERIENCIA GENERAL\n" + REQUIRED,
        "2": WAIVED,
        "22": WAIVED,
        "3": "El suministro se entrega en la bodega municipal.",
    }
    downloaded = []

    def download(_client, document, _storage, _settings, *, diagnostics):
        downloaded.append(document.document_id)
        return SimpleNamespace(sha256=document.document_id.zfill(64), observed_size=25)

    def extract(document, *args, **kwargs):
        return {"status": "completed", "page_count": 1, "elapsed_seconds": 0.02}, [
            fragment(texts[document.document_id])
        ]

    rows = [row(1, "Boyacá"), row(2, "Bogotá"), row(3, "Nariño")]
    monkeypatch.setattr(en01, "check_session", Mock())
    monkeypatch.setattr(
        en01, "fetch_inventory", lambda _client, keys: histories[keys["idContrato"]]
    )
    monkeypatch.setattr(en01.spike, "download_document", download)
    monkeypatch.setattr(en01.spike, "run_existing_extractor", extract)
    client = SimpleNamespace(
        profile_id=EXAMPLE_PROFILE,
        deadline=time.monotonic() + 720,
        requests=2,
        post=Mock(return_value={"count": len(rows), "data": rows}),
    )
    args = SimpleNamespace(
        processes=3, documents=6, discovery_pages=8, recent_days=30, ocr_pages=2, exploratory=True
    )
    assert en01.run(client, args, None, tmp_path, now=CUTOFF) == 0
    assert downloaded == ["1", "2", "22", "3"]
    results = report(tmp_path, "experience_requirements.json")
    assert [r["document_stop_reason"] for r in results] == [
        "applicable_requirement_in_governing_pdf",
        "no_pertinent_corroborating_pdf",
        "silence_secondary_review",
    ]
    assert [r["review_category"] for r in results] == [
        "explicit_requirement",
        "explicit_favorable",
        "documentary_silence",
    ]
    assert results[0]["status"] == results[1]["status"] == "not_resolved"
    assert results[0]["review_evidence"][0]["page"] == 1
    assert report(tmp_path, "deprioritized_review_sample.json") == [results[0]]
    metrics = report(tmp_path, "metrics.json")
    assert metrics["governing_downloads"] == 3
    assert metrics["processes_with_explicit_absence"] == 1
    assert metrics["processes_with_explicit_requirement"] == 1
    assert metrics["corroboration_attempts"] == 1
    assert metrics["documentary_silence"] == 1


def test_leticia_imperatives_survive_page_header_without_inventing_a_waiver():
    doc = evidence_document("")
    doc["fragments"] = [
        fragment(
            "www.contraloria.gov.co\n"
            "Aportar como experiencia general dos (2) contratos de compraventa celebrado con\n"
            "entidades públicas o privadas durante la última vigencia fiscal "
            "y cuyo valor sea igual\n"
            "o superior al presupuesto oficial.\n"
            "Experiencia especifica\n"
            "Aportar como experiencia especifica un (1) contrato de suministro de papelería,\n"
            "útiles de oficina, tóner y tintas cuyo valor sea igual "
            "o superior a cinco (5) veces el\n"
            "valor del presupuesto oficial.",
            page=14,
        )
    ]
    result = rules.classify_experience([doc], inventory_complete=False)
    assert result["status"] == "not_resolved"
    assert [e["section"].lower() for e in result["evidence"]] == [
        "experiencia general",
        "experiencia especifica",
    ]
    assert all(
        e["scope"] == "general_bidder" and e["assertion_type"] == rules.REQ and e["page"] == 14
        for e in result["evidence"]
    )


def test_la_capilla_indirect_requirement_under_explicit_experience_section():
    doc = evidence_document("")
    doc["fragments"] = [
        fragment(
            "11.2.1 EXPERIENCIA ESPECÍFICA\n"
            "de un contratista idóneo que ejecute el contrato con las mejores calidades, "
            "garantizando experiencia,\n"
            "suficiencia técnica administrativa y operacional, la entidad a determinado "
            "exigir al proponente la\n"
            "acreditación de experiencia especifica así: a través de DOS (2) contratos "
            "o certificaciones de suministro\n"
            "o compraventa, cuyo objeto describa el suministro de bienes relacionado ",
            page=10,
        )
    ]
    result = rules.classify_experience([doc], inventory_complete=False)
    assert result["status"] == "not_resolved"
    assert result["evidence"][0]["page"] == 10
    assert result["evidence"][0]["assertion_type"] == rules.REQ
    assert result["evidence"][0]["scope"] == "general_bidder"


def test_san_francisco_table_requires_experience_only_within_each_company_size():
    table = (
        "TAMAÑO ACREDITACIÓN DE EXPERIENCIA\n"
        "Micro, Pequeñas y\nMedianas\nEmpresas\n"
        "El proponente debe anexar con su propuesta dos (2) certificaciones o copias de\n"
        "contratos con su respectiva acta de liquidación de contratos celebrados, ejecutados.\n"
        "Grandes empresas El proponente debe anexar con su propuesta MAXIMO UNA (1) "
        "certificación o copia\n"
        "de contratos con su respectiva acta de liquidación de contrato celebrado, ejecutado."
    )
    continuation = (
        "NOTA 3: En caso de Consorcio o Unión temporal, para efectos de la verificación "
        "de la Experiencia del Proponente, se procederá a sumar los valores de los contratos."
    )
    doc = evidence_document("")
    doc["fragments"] = [fragment(table, page=34), fragment(continuation, page=35)]
    result = rules.classify_experience([doc])
    table_evidence = [e for e in result["evidence"] if e["assertion_type"] == rules.REQ]
    assert [(e["scope"], e["page"]) for e in table_evidence] == [("limited", 34)] * 2
    assert result["status"] == "experience_ambiguous"
    assert result["review_category"] == "limited_or_ambiguous"
    assert all(e in result["review_evidence"] for e in table_evidence)
    doc["fragments"] = [fragment(table.split("\n", 1)[1], page=34)]
    no_heading = rules.classify_experience([doc])
    assert not any(e["assertion_type"] in {rules.REQ, rules.NEG} for e in no_heading["evidence"])


def test_analyzed_history_uses_only_result_rows_and_deduplicates_notices(tmp_path):
    for run_name, profile in (("en01-first_run", "2222222"), ("en01-second", "3333333")):
        root = tmp_path / run_name
        root.mkdir()
        ref = f"licitaciones_info:{profile}:10"
        rows = [
            {"process_reference": ref, "source": "secop2", "source_identity": "CO1.NTC.12345"},
            {
                "process_reference": "selected-only",
                "source": "secop2",
                "source_identity": "CO1.NTC.99999",
                "sampled": True,
            },
        ]
        en01.write_json(root / "processes.json", {"processes": rows})
        en01.write_json(root / "experience_requirements.json", [{"process_reference": ref}])
    assert en01.load_analyzed_secop_ids(tmp_path, ["en01-first_run", "en01-second"]) == {
        "CO1.NTC.12345"
    }


@pytest.mark.parametrize("bad_notice", ["CO1.REQ.12345", None, "licitaciones_info:2222222:10"])
def test_incomparable_history_fails_before_browser(tmp_path, monkeypatch, bad_notice, capsys):
    root = tmp_path / "en01-old"
    root.mkdir()
    en01.write_json(
        root / "processes.json",
        {
            "processes": [
                {"process_reference": "row", "source": "secop2", "source_identity": bad_notice}
            ]
        },
    )
    en01.write_json(root / "experience_requirements.json", [{"process_reference": "row"}])
    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    connect = Mock()
    monkeypatch.setattr(en01, "connect_browser", connect)
    assert en01.main(["--exploratory", "--exclude-analyzed-from", root.name]) == 1
    assert "referencia comparable SECOP II" in capsys.readouterr().out
    connect.assert_not_called()


def test_notice_exclusion_precedes_inventory_and_ignores_aggregator_profile(monkeypatch, tmp_path):
    known = row(91, "Boyacá")
    known.update(
        Link="https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.12345",
        idUltimaFase="CO1.NTC.12345",
    )
    uncertain = row(92, "Bogotá")
    uncertain.update(
        Link="https://community.secop.gov.co/Public/?noticeUID=CO1.REQ.12345",
        idUltimaFase="CO1.REQ.12345",
    )
    valid = row(93, "Nariño")
    monkeypatch.setattr(en01, "check_session", Mock())
    inventory = Mock(return_value=[])
    monkeypatch.setattr(en01, "fetch_inventory", inventory)
    client = SimpleNamespace(
        profile_id=EXAMPLE_PROFILE,
        deadline=time.monotonic() + 720,
        requests=2,
        post=Mock(return_value={"count": 3, "data": [known, uncertain, valid]}),
    )
    args = SimpleNamespace(
        processes=1,
        documents=1,
        discovery_pages=8,
        recent_days=30,
        exploratory=True,
        excluded_secop_ids=frozenset({"CO1.NTC.12345"}),
    )
    assert en01.run(client, args, None, tmp_path, now=CUTOFF) == 0
    assert [call.args[1]["idContrato"] for call in inventory.call_args_list] == [93]
    metrics = report(tmp_path, "metrics.json")
    assert metrics["eligible_before_history"] == 3
    assert metrics["inventory_eligible"] == metrics["sampled"] == 1
    assert metrics["excluded_by_reason"] == {
        "previously_analyzed_secop": 1,
        "secop_notice_identity_unverified": 1,
    }


def test_betulia_recovers_contract_minimum_inside_numbered_heading():
    text = (
        "14 Compromiso Anticorrupción 14 Compromiso Anticorrupción\n"
        "5.5 EXPERIENCIA MINIMA REQUERIDA PARA PARTICIPAR (Mínimo dos (2) contratos cuyo objeto\n"
        "sea igual o similar al presente contrato y cada uno por una cuantía igual o superior al "
        "100% del valor del\n"
        "presupuesto oficial expresado en SMMLV)\n"
        "CONTENIDO MINIMO DE LA\n"
        "CERTIFICACION PARA QUE SEA\n"
        "VALIDA:"
    )
    doc = evidence_document("")
    doc["fragments"] = [fragment(text, page=12)]
    pending = evidence_document("", role="unknown", complete=False, identifier="2")
    decision = rules.classify_experience([doc, pending])
    assert decision["status"] == "not_resolved"
    assert decision["review_category"] == "explicit_requirement"
    (evidence,) = decision["review_evidence"]
    assert evidence["basis"] == "minimum_experience_in_heading"
    assert (evidence["scope"], evidence["page"], evidence["section_page"]) == (
        "general_bidder",
        12,
        12,
    )
    assert "100%" in evidence["excerpt"]
    assert "Compromiso Anticorrupción" not in evidence["excerpt"]
    assert "CONTENIDO MINIMO" not in evidence["excerpt"]


@pytest.mark.parametrize(
    "clause",
    [
        "5.5 EXPERIENCIA MINIMA REQUERIDA PARA PARTICIPAR (No aplica experiencia)",
        "5.5 EXPERIENCIA MINIMA REQUERIDA PARA PARTICIPAR "
        "(Podrá acreditar como mínimo dos (2) contratos cuyo objeto sea similar)",
        "EXPERIENCIA MINIMA REQUERIDA PARA PARTICIPAR "
        "(Mínimo dos contratos cuyo objeto sea similar)",
    ],
)
def test_minimum_heading_rule_does_not_infer_a_waiver_or_obligation_without_its_cues(clause):
    decision = rules.classify_experience([evidence_document(clause)])
    assert decision["status"] == "not_resolved"
    assert not any(e["assertion_type"] in {rules.NEG, rules.REQ} for e in decision["evidence"])


@pytest.mark.parametrize(
    ("cover", "role", "complete"),
    [
        ("INVITACIÓN PÚBLICA\nObjeto del proceso", "primary", True),
        ("FORMATOS DE INVITACIÓN\nNombre del proponente", "support", True),
        ("Objeto del proceso", "unknown", False),
        ("PROYECTO DE PLIEGO DE CONDICIONES", "excluded", True),
        ("SOLICITUD DE INFORMACIÓN A\nPROVEEDORES", "excluded", True),
    ],
)
def test_truncated_title_beats_support_but_needs_cover(monkeypatch, cover, role, complete):
    candidate = SpikeDocument("04-INVITACIO 025-2026", "pdf", SECOP + "1", "1")
    study = SpikeDocument("Estudios previos", "pdf", SECOP + "2", "2")
    monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[study, candidate]))
    download = Mock(return_value=SimpleNamespace(sha256="a" * 64, observed_size=25))
    monkeypatch.setattr(en01.spike, "download_document", download)
    monkeypatch.setattr(
        en01.spike,
        "run_existing_extractor",
        Mock(
            return_value=(
                {"status": "completed", "page_count": 1, "elapsed_seconds": 0.01},
                [fragment(cover)],
            )
        ),
    )
    inv = []
    en01.analyze_documents(
        SimpleNamespace(deadline=time.monotonic() + 360),
        {"inventory_keys": {}},
        None,
        None,
        1,
        Counter(),
        inv,
        [],
    )
    assert download.call_args.args[1] == candidate
    assert inv[1]["role"] == role
    assert inv[1]["complete"] == complete
    assert inv[1]["content_complete"]


def test_shared_docx_reader_preserves_paragraph_and_table_without_pages(tmp_path, monkeypatch):
    from docx import Document

    path = tmp_path / "invitation.docx"
    docx = Document()
    docx.add_paragraph("INVITACIÓN PÚBLICA")
    docx.add_paragraph(REQUIRED)
    docx.add_table(rows=1, cols=1).cell(0, 0).text = REQUIRED
    docx.save(path)
    pdf_alternative = SpikeDocument("Estudios previos.pdf", "pdf", SECOP + "2", "2")
    rector = SpikeDocument("Invitación Pública", "docx", SECOP + "1", "1")
    settings = en01.settings_for_run(tmp_path, "not-available", None)
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    payload = path.read_bytes()
    stored = storage.store(
        [payload],
        original_name=path.name,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        expected_size=len(payload),
        max_bytes=en01.DOCUMENT_BYTES,
    )
    monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[pdf_alternative, rector]))
    download = Mock(return_value=stored)
    monkeypatch.setattr(en01.spike, "download_document", download)
    inv = []
    en01.analyze_documents(
        SimpleNamespace(deadline=time.monotonic() + 360),
        {"inventory_keys": {}},
        storage,
        settings,
        1,
        Counter(),
        inv,
        [],
    )
    assert download.call_args.args[1] == rector
    entry = inv[1]
    assert entry["complete"]
    assert entry["coverage_unit"] == "docx_fragment"
    assert entry["docx_fragments"] == 3
    assert entry["total_pages"] == 0
    assert entry["ocr_pages"] == []
    evidence = rules.classify_experience(inv)["evidence"]
    assert [(e["method"], e["page"]) for e in evidence] == [("native_docx_text", None)] * 2
    assert evidence[0]["locator"]["paragraph_number"] == 2
    assert evidence[1]["locator"]["column_number"] == 1


def test_ocr_prioritizes_index_destination_before_neighbours_and_keeps_scan_bounded():
    native = SimpleNamespace(
        document=SimpleNamespace(original_name="Invitación pública.pdf"),
        error_code=None,
        diagnostics={"native_pages_visited": 12},
        fragments=[
            SimpleNamespace(
                page_number=2,
                text="1.2. EXPERIENCIA ......................... 8",
            ),
            SimpleNamespace(
                page_number=4,
                text="Para requisitos habilitantes véase página 19.",
            ),
        ],
    )
    assert en01.select_ocr_pages(native, [1, 2, 5, 8, 19], 2) == [8, 2]
    native.fragments = []
    assert en01.select_ocr_pages(native, list(range(1, 13)), 2) == [1, 2]
    native.document.original_name = "Estudios previos.pdf"
    assert en01.select_ocr_pages(native, list(range(1, 13)), 2) == []


@pytest.mark.parametrize(("known", "expected_pages"), [(1, 8), (2, 9), (20, 10)])
def test_extra_feed_pages_only_cover_shortfall_after_exclusion(known, expected_pages):
    def response(_, payload):
        i = payload["page"]
        return {"count": 310, "data": [row(2 * i - 1, "Boyacá"), row(2 * i, "Nariño")]}

    client = SimpleNamespace(profile_id=EXAMPLE_PROFILE, post=Mock(side_effect=response))
    args = SimpleNamespace(
        processes=15,
        discovery_pages=8,
        recent_days=30,
        exploratory=True,
        conditional_extra_feed_pages=2,
        excluded_secop_ids=frozenset(f"CO1.NTC.{i}" for i in range(1, known + 1)),
    )
    discovery = {"pages": [], "duplicates": 0}
    selected = en01.discover(
        client,
        args,
        CUTOFF,
        discovery,
        commercial.load_commercial_profile(),
        en01.load_national_locations(),
    )
    assert client.post.call_count == expected_pages
    assert len(selected) == (0 if known == 20 else 15)
    assert all(p["source_identity"] not in args.excluded_secop_ids for p in selected)


@pytest.mark.parametrize(
    ("text", "page", "scope", "dependency"),
    [
        (
            "1.7.2. CONDICIONES DE EXPERIENCIA:\n"
            "Para acreditar la EXPERIENCIA, el proponente debe aportar máximo dos (2) "
            "contratos ejecutados y terminados cuyo objeto sea igual o similar.",
            7,
            "general_bidder",
            False,
        ),
        (
            "7.2.2. EXPERIENCIA DEL PROPONENTE - FORMULARIO No. 4\n"
            "El proponente deberá acreditar la experiencia requerida en este proceso de "
            "selección con el lleno de los requisitos que se encuentran a continuación.",
            12,
            "general_bidder",
            False,
        ),
        (
            "B. Experiencia.\nCertificar experiencia en máximo tres (3) certificaciones "
            "de contratos ejecutados y terminados dentro de los últimos dos años.",
            7,
            "general_bidder",
            False,
        ),
        (
            "Experiencia requerida\nEl proponente deberá aportar evidencias de experiencia "
            "acorde a la necesidad expuesta como se indicó en los documentos solicitados "
            "en la tabla anterior.",
            5,
            "unspecified",
            True,
        ),
    ],
)
def test_latest_silences_are_requirements_with_their_original_scope(text, page, scope, dependency):
    doc = evidence_document("")
    doc["fragments"] = [fragment(text, page=page)]
    decision = rules.classify_experience([doc], inventory_complete=False)
    (evidence,) = decision["evidence"]
    assert (evidence["assertion_type"], evidence["page"], evidence["scope"]) == (
        rules.REQ,
        page,
        scope,
    )
    assert bool(decision["dependencies"]) is dependency
    assert decision["status"] == ("experience_ambiguous" if dependency else "not_resolved")


def test_concatenated_invitation_gets_hint_and_fragmented_cover_validates_title():
    name = "InvitacionPublica_"
    assert rules.document_role(name) == "unknown"
    assert rules.document_role_hint(name, "unknown") == "primary"
    role, _ = rules.document_cover_metadata(
        "INSTITU CIO N EDUC ATIVA\nINVITA CI O N P UBLI CA PROC E S O CONT RA C TU A L"
    )
    assert role == "primary"
    assert rules.document_cover_metadata("ESTU DIO S PREV IOS PROC ESO CONTRAC TU AL")[0] == (
        "support"
    )


def test_docx_amendment_reuses_the_eligible_office_path():
    assert en01.supports_document({"extension": "docx", "role": "amendment"})
    assert not en01.supports_document({"extension": "docx", "role": "support"})


def test_opt_in_governing_pdf_cap_reads_an_oversize_local_fixture(tmp_path):
    from pypdf import PdfReader, PdfWriter

    fixture = Path(__file__).resolve().parents[1] / "fixtures/extraction/native_refrigerios.pdf"
    writer = PdfWriter()
    writer.add_page(PdfReader(fixture).pages[0])
    writer.add_attachment("anexo.bin", b"X" * (11 * en01.MIB))
    path = tmp_path / "governing.pdf"
    writer.write(path)
    payload = path.read_bytes()
    settings = en01.settings_for_run(tmp_path, "not-available", None)
    cap = 16 * en01.MIB
    assert en01.DOCUMENT_BYTES < len(payload) < cap
    entry = {"extension": "pdf", "role": "primary"}
    assert en01.document_settings(settings, entry, en01.DOCUMENT_BYTES) is settings
    assert en01.document_settings(settings, {"extension": "pdf", "role": "support"}, cap) is (
        settings
    )
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    with pytest.raises(en01.AcquisitionError) as rejected:
        storage.store(
            [payload],
            original_name=path.name,
            content_type="application/pdf",
            expected_size=len(payload),
            max_bytes=settings.document_max_bytes,
        )
    assert rejected.value.code == "too_large"
    scoped = en01.document_settings(settings, entry, cap)
    stored = storage.store(
        [payload],
        original_name=path.name,
        content_type="application/pdf",
        expected_size=len(payload),
        max_bytes=scoped.document_max_bytes,
    )
    document = SpikeDocument("Invitación pública", "pdf", SECOP + "1", "1")
    en01.extract_document(document, stored, storage, scoped, entry, ocr_pages=0)
    assert scoped.extraction_max_bytes == cap
    assert scoped.extraction_timeout_seconds == settings.extraction_timeout_seconds
    assert entry["complete"]
    assert entry["pages_seen"] == [1]
    assert entry["ocr_pages"] == []


def test_download_failure_keeps_safe_diagnostics_in_inventory_and_errors(monkeypatch):
    rector = SpikeDocument("Invitación Pública.pdf", "pdf", SECOP + "1", "1")
    monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[rector]))
    recorded = {
        "stage": "response_headers",
        "http_status": 503,
        "exception_type": "HTTPError",
        "content_type": "text/html",
        "rejection_reason": "http_error",
        "redirects": [],
    }

    def download(*args, diagnostics):
        diagnostics.update(recorded)
        raise en01.AcquisitionError("http_error", "private response")

    monkeypatch.setattr(en01.spike, "download_document", download)
    inv, errors = [], []
    en01.analyze_documents(
        SimpleNamespace(deadline=time.monotonic() + 360),
        {"inventory_keys": {}},
        None,
        None,
        1,
        Counter(),
        inv,
        errors,
    )
    assert inv[0]["download_diagnostics"] == recorded
    assert errors[0]["download_diagnostics"] == recorded
    assert "private response" not in json.dumps(errors)


def test_archived_probe_is_bounded_and_skips_discovery(monkeypatch, tmp_path):
    import eureka_nacional_download_probe as probe

    run = tmp_path / "en01-history"
    run.mkdir()
    en01.write_json(
        run / "processes.json",
        {"processes": [{"codigo_proceso": "SIMULADO", "process_reference": "proc"}]},
    )
    entry = {
        "role": "primary",
        "extension": "pdf",
        "selection": "selected",
        "status": "download_failed",
        "url": SECOP + "1",
        "name": "Invitación",
        "document_id": "1",
    }
    en01.write_json(run / "documents.json", [{"process_reference": "proc", "documents": [entry]}])
    document = probe.archived_document(run, "SIMULADO")
    assert document.original_name == "Invitación.pdf"
    output = tmp_path / "probe"
    output.mkdir()
    downloader = Mock()
    downloader.download.side_effect = [
        en01.AcquisitionError("http_error", "private"),
        SimpleNamespace(observed_size=250, sha256="a" * 64),
    ]
    factory = Mock(return_value=downloader)
    monkeypatch.setattr(probe, "SecopDownloader", factory)
    monkeypatch.setattr(probe.time, "sleep", Mock())
    result = probe.probe(document, output, 2)
    factory.assert_called_once_with(12, en01.DOCUMENT_BYTES)
    assert downloader.download.call_count == 2
    assert result == [{"rejection_reason": "http_error"}, {"bytes": 250}]
    assert result == report(output, "download_probe.json")
    entry["url"] += "&token=private"
    en01.write_json(run / "documents.json", [{"process_reference": "proc", "documents": [entry]}])
    with pytest.raises(ValueError, match="enlace archivado"):
        probe.archived_document(run, "SIMULADO")


def test_verified_document_receipt_survives_restart(tmp_path):
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    doc = SpikeDocument("Invitación", "pdf", SECOP + "1", "1")
    pdf = b"%PDF-1.4\ncontenido\n%%EOF"
    stored = storage.store(
        [pdf],
        original_name="file.pdf",
        content_type="application/pdf",
        expected_size=len(pdf),
        max_bytes=1000,
    )
    en01.DownloadState(tmp_path, storage).remember(doc, stored)
    state = en01.DownloadState(tmp_path, storage)
    assert state.cached(doc, 1000) == stored
    (storage.root / stored.storage_path).write_bytes(b"misma ruta, contenido alterado")
    assert state.cached(doc, 1000) is None


def test_resume_keeps_saved_selection_and_never_probes_feed(tmp_path, monkeypatch):
    selected = SimpleNamespace(
        profile_id=EXAMPLE_PROFILE, requests=0, deadline=time.monotonic() + 360
    )
    sample = row(1, "Boyacá")
    n = en01.discover(
        SimpleNamespace(
            profile_id=EXAMPLE_PROFILE, post=Mock(return_value={"count": 1, "data": [sample]})
        ),
        SimpleNamespace(processes=1, recent_days=30, discovery_pages=4),
        CUTOFF,
        {"pages": [], "duplicates": 0},
        commercial.load_commercial_profile(),
        en01.load_national_locations(),
    )
    check = Mock(side_effect=AssertionError("feed preflight"))
    discover = Mock(side_effect=AssertionError("feed"))
    inventory = Mock(return_value=[])
    monkeypatch.setattr(en01, "check_session", check)
    monkeypatch.setattr(en01, "discover", discover)
    monkeypatch.setattr(en01, "fetch_inventory", inventory)
    args = SimpleNamespace(
        processes=1,
        documents=5,
        recent_days=30,
        discovery_pages=8,
        resume_snapshot=n,
        resume_inventory_from="en01-source",
        exploratory=True,
    )
    assert en01.run(selected, args, None, tmp_path, now=CUTOFF) == 0
    assert report(tmp_path, "metrics.json")["discovered_rows"] == 0
    assert inventory.call_count == 1
    check.assert_not_called()
    discover.assert_not_called()


@pytest.mark.parametrize("edge_fails", [False, True])
def test_edge_fallback_uses_second_budget_slot_only_after_403(tmp_path, monkeypatch, edge_fails):
    import eureka_nacional_cdp_stream as edge

    doc = SpikeDocument("Invitación", "pdf", SECOP + "1", "1")
    monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[doc]))

    def direct(*args, diagnostics):
        diagnostics["http_status"] = 403
        raise en01.AcquisitionError("http_error", "rechazado")

    def browser(*args, cdp_url, parent_page):
        assert parent_page is client.page
        assert cdp_url.endswith(":9232")
        args[-1]["target_closed"] = True
        if edge_fails:
            raise en01.AcquisitionError("unexpected_response", "rechazado")
        return SimpleNamespace(sha256="a" * 64, observed_size=44)

    monkeypatch.setattr(en01.spike, "download_document", direct)
    monkeypatch.setattr(edge, "download_stream_pdf", Mock(side_effect=browser))
    monkeypatch.setattr(
        en01.spike,
        "run_existing_extractor",
        Mock(
            return_value=(
                {"status": "completed", "page_count": 1, "elapsed_seconds": 0.01},
                [fragment(REQUIRED)],
            )
        ),
    )
    client = SimpleNamespace(deadline=time.monotonic() + 360, page=Mock(), reserve=Mock())
    settings = en01.settings_for_run(tmp_path, "tesseract", None)
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    state = en01.DownloadState(tmp_path, storage, edge_enabled=True)
    inv, errors, metrics = [], [], Counter()
    en01.analyze_documents(
        client,
        {"inventory_keys": {}},
        storage,
        settings,
        2,
        metrics,
        inv,
        errors,
        download_state=state,
    )
    client.reserve.assert_called_once_with(1)
    assert metrics["documents_attempted"] == 2
    assert metrics["edge_downloaded"] == (not edge_fails)
    assert bool(errors) == edge_fails
    assert errors[0]["code"] == "unexpected_response" if edge_fails else inv[0]["complete"]


def test_download_circuit_requires_repeated_failures_across_processes(tmp_path):
    state = en01.DownloadState(tmp_path, en01.spike.LocalBinaryStorage(tmp_path / "binaries"))
    assert not state.record_failure("one")
    assert not state.record_failure("one")
    assert not state.record_failure("one")
    assert state.record_failure("two")


@pytest.mark.parametrize(
    ("enabled", "status", "allowance"), [(False, 403, 2), (True, 429, 2), (True, 403, 1)]
)
def test_edge_cannot_spend_an_unapproved_fallback_slot(
    tmp_path, monkeypatch, enabled, status, allowance
):
    import eureka_nacional_cdp_stream as edge

    doc = SpikeDocument("Invitación", "pdf", SECOP + "1", "1")
    monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[doc]))

    def direct(*args, diagnostics):
        diagnostics["http_status"] = status
        raise en01.AcquisitionError("http_error", "rechazado")

    monkeypatch.setattr(en01.spike, "download_document", direct)
    fallback = Mock()
    monkeypatch.setattr(edge, "download_stream_pdf", fallback)
    settings = en01.settings_for_run(tmp_path, "tesseract", None)
    storage = en01.spike.LocalBinaryStorage(tmp_path / "binaries")
    state = en01.DownloadState(tmp_path, storage, edge_enabled=enabled)
    metrics, errors = Counter(), []
    en01.analyze_documents(
        SimpleNamespace(deadline=time.monotonic() + 360),
        {"inventory_keys": {}},
        storage,
        settings,
        allowance,
        metrics,
        [],
        errors,
        download_state=state,
    )
    assert metrics["documents_attempted"] == 1
    assert errors[0]["code"] == "http_error"
    fallback.assert_not_called()


def test_resume_snapshot_includes_unreached_selected_processes(tmp_path):
    rows = [
        {
            "process_reference": name,
            "sampled": sampled,
            "source": source,
            "inventory_keys": {"idContrato": name, "id_fuente_contract": "3", "idUltimaFase": name},
        }
        for name, sampled, source in [
            ("unreached", True, "secop2"),
            ("resolved", True, "secop2"),
            ("pending", True, "secop2"),
            ("not_sampled", False, "secop2"),
            ("unsupported", True, "secop1"),
        ]
    ]
    en01.write_json(tmp_path / "processes.json", {"processes": rows})
    en01.write_json(
        tmp_path / "experience_requirements.json",
        [
            {"process_reference": "pending", "status": "not_resolved"},
            {"process_reference": "resolved", "status": "experience_required"},
        ],
    )
    result = en01.load_resume_snapshot(tmp_path)
    assert [item["process_reference"] for item in result] == ["pending", "unreached"]


@pytest.mark.parametrize(
    ("extension", "title", "redirects"),
    [
        ("pdf", "Invitacion", [{"http_status": 302}]),
        ("pdf", "Aviso de invitacion publica", []),
        ("pdf", "Estudios previos", []),
        ("docx", "Invitacion", []),
    ],
)
def test_national_stream_rejects_ineligible_paths(extension, title, redirects):
    document = SpikeDocument(title, extension, SECOP + "1", "1")
    err = en01.AcquisitionError("http_error", "rechazado")
    diag = {"http_status": 403, "redirects": redirects}
    assert not en01.can_stream_fallback(document, rules.document_role(title), err, diag)


def test_national_stream_reuses_verified_pdf_and_stops_when_close_is_uncertain(
    tmp_path,
    monkeypatch,
):
    output = tmp_path / "run"
    output.mkdir()
    document = SpikeDocument("Invitacion", "pdf", SECOP + "1", "1")
    pdf = b"%PDF-1.4\\ncontenido\\n%%EOF".replace(b"\\n", b"\n")
    inventory = Mock(return_value=[document])
    monkeypatch.setattr(en01, "fetch_inventory", inventory)

    def direct(*args, diagnostics):
        diagnostics.update(http_status=403, redirects=[])
        raise en01.AcquisitionError("http_error", "rechazado")

    closed = True
    startup_failed = True

    def browser(target, staging, diagnostic, *, cdp_url):
        assert target == document
        assert cdp_url.endswith(":9232")
        if startup_failed:
            diagnostic.update(worker_closed=True, tab_opened=False, stage="cdp_connect")
            raise en01.AcquisitionError("protocol_error", "timeout")
        diagnostic.update(
            stream_bytes=len(pdf),
            worker_closed=True,
            requests_forwarded=1,
            tab_opened=True,
            io_closed=closed,
            navigation_abort_ack=closed,
            target_closed=closed,
        )
        return staging.store(
            [pdf],
            original_name="document.pdf",
            content_type="application/pdf",
            expected_size=len(pdf),
            max_bytes=en01.streaming.DOCUMENT_BYTES,
        )

    monkeypatch.setattr(en01.streaming, "invoke_worker", browser)
    attempt = Mock(side_effect=direct)
    monkeypatch.setattr(en01.spike, "download_document", attempt)
    monkeypatch.setattr(
        en01.spike,
        "run_existing_extractor",
        Mock(
            return_value=(
                {"status": "completed", "page_count": 1, "elapsed_seconds": 0.01},
                [fragment(REQUIRED)],
            )
        ),
    )
    settings = en01.settings_for_run(output, "tesseract", None)
    storage = en01.spike.LocalBinaryStorage(output / "binaries")
    state = en01.DownloadState(output, storage, edge_enabled=True)
    client = SimpleNamespace(deadline=time.monotonic() + 360, reserve=Mock())

    def analyze(metrics, entries, reference="second"):
        return en01.analyze_documents(
            client,
            {"inventory_keys": {}, "process_reference": reference},
            storage,
            settings,
            2,
            metrics,
            entries,
            [],
            download_state=state,
            ocr_pages=0,
        )

    failed_document = document
    failed_metrics, failed_entries = Counter(), []
    analyze(failed_metrics, failed_entries, reference="first")
    assert failed_metrics["documents_attempted"] == 2
    assert failed_entries[0]["status"] == "download_failed"
    assert failed_entries[0]["download_diagnostics"]["edge"]["stage"] == "cdp_connect"
    assert state.failed_processes == ["first"]
    assert not state.stream_marker.exists()

    startup_failed = False
    document = SpikeDocument("Invitacion", "pdf", SECOP + "3", "3")
    inventory.return_value = [document]
    metrics, entries = Counter(), []
    analyze(metrics, entries)
    assert not state.failed_processes
    assert state.cached(failed_document, en01.DOCUMENT_BYTES) is None
    assert metrics["documents_attempted"] == 2
    assert entries[0]["download_diagnostics"]["mechanism"] == "edge_cdp_stream"
    reused = Counter()
    analyze(reused, [])
    assert reused["documents_reused"] == 1
    assert attempt.call_count == 2

    other = SpikeDocument("Invitacion", "pdf", SECOP + "2", "2")
    inventory.return_value = [other]
    document = other
    closed = False
    with pytest.raises(en01.BudgetReached, match="download_close_unverified"):
        analyze(Counter(), [])
    assert state.stream_marker.exists()
    assert state.cached(other, en01.DOCUMENT_BYTES) is None
    inventory.reset_mock()
    with pytest.raises(en01.BudgetReached, match="download_close_unverified"):
        analyze(Counter(), [])
    inventory.assert_not_called()
