"""Offline regression for rector recognition and bounded recovery routing."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pypdf import PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_stream_recovery as recovery

RULES = recovery.en
CAICEDONIA = (
    "Deberá anexar como requisito técnico en su oferta mínimo tres (3) certificaciones de "
    "experiencia sobre contratos ejecutados, cuyo objeto sean similares a la presente convocatoria."
)
REGISTRADURIA = (
    "El proponente deberá presentar con su propuesta máximo dos (2) certificaciones de experiencia "
    "o acta de liquidación, de contratos ejecutados cuyo objeto y/o actividades ejecutadas sean "
    "iguales o de similares a las del objeto a contratar, y cuya sumatoria sea igual o superior "
    "al presupuesto oficial estimado para el contrato a celebrar."
)
PDF_URL = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=21"


def example_document():
    return recovery.SpikeDocument("Invitación pública", "pdf", PDF_URL, "21")


@pytest.mark.parametrize(("clause", "page"), [(CAICEDONIA, 8), (REGISTRADURIA, 11)])
def test_offer_certificates_trigger_priority_while_corroboration_is_pending(clause, page):
    documents = [
        {
            "document_id": "one",
            "name": "Invitación",
            "role": "primary",
            "complete": True,
            "fragments": [
                SimpleNamespace(
                    text=clause,
                    source_locator={"page_number": page, "extraction_method": "native_pdf_text"},
                )
            ],
        },
        {"document_id": "other", "name": "Complemento", "role": "unknown", "complete": False},
    ]
    result = RULES.classify_experience(documents)
    assert result["status"] == "not_resolved"
    assert result["review_category"] == "explicit_requirement"
    assert [e["page"] for e in result["review_evidence"]] == [page]
    assert result["review_evidence"][0]["basis"] == "mandatory_offer_certificates"


def test_registraduria_template_requires_numbered_invitation_and_object():
    template = "FORMATO INVITACIÓN PÚBLICA VERSIÓN 0\n"
    cover = (
        template
        + "Aprobado:08/09/2017\n"
        + "INVITACIÓN PÚBLICA No. 04 DE 2026 - FRR.\n"
        + "1. OBJETO:\nAdquisición de mobiliario"
    )
    assert RULES.document_cover_metadata(cover)[0] == "primary"
    assert RULES.document_cover_metadata(cover.replace("1. OBJETO:", ""))[0] == "support"
    assert RULES.document_cover_metadata(template + "Anexo para diligenciar")[0] == "support"
    assert RULES.document_cover_metadata("ESTUDIOS PREVIOS\n" + cover)[0] == "support"


@pytest.mark.parametrize(
    ("diagnostic", "expected"),
    [
        ({"error": "http_error", "diagnostics": {"http_status": 403, "redirects": []}}, True),
        ({"error": "http_error", "diagnostics": {"http_status": 403, "redirects": [{}]}}, False),
        ({"error": "http_error", "diagnostics": {"http_status": 404}}, False),
        ({"error": "deadline"}, False),
    ],
)
def test_only_access_403_without_redirect_allows_stream(diagnostic, expected):
    assert recovery.fallback_eligible(diagnostic) is expected


@pytest.mark.parametrize("bad_url", [PDF_URL + "&x=1", PDF_URL.replace("=21", "=22")])
def test_archive_target_rejects_ambiguous_or_different_identity(bad_url):
    with pytest.raises(recovery.AcquisitionError, match="alcance"):
        recovery.validate_target(recovery.SpikeDocument("Invitación", "pdf", bad_url, "21"))


def test_direct_success_skips_edge(tmp_path, monkeypatch):
    stored = SimpleNamespace(sha256="verified")
    monkeypatch.setattr(recovery, "direct_pdf", lambda *_: (stored, {}))
    edge = Mock(side_effect=AssertionError("Edge must not start for a direct success"))
    monkeypatch.setattr(recovery, "stream_pdf", edge)
    outcome = recovery.recover_pdf(example_document(), None, tmp_path / "lock", {})
    assert outcome == (stored, "urllib")
    edge.assert_not_called()


@pytest.mark.parametrize("closed", [True, False])
def test_fallback_retains_no_file_when_close_is_uncertain(tmp_path, monkeypatch, closed):
    path = tmp_path / "reference.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(path)
    payload = path.read_bytes()
    trace = {}
    storage = recovery.LocalBinaryStorage(tmp_path / "binaries")
    marker = tmp_path / "lock"
    monkeypatch.setattr(recovery.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        recovery,
        "direct_pdf",
        lambda *_: (None, {"error": "http_error", "diagnostics": {"http_status": 403}}),
    )

    async def edge(_, result):
        assert marker.exists()
        result.update(
            tab_opened=True,
            target_closed=closed,
            io_closed=True,
            navigation_abort_ack=True,
            requests_forwarded=1,
            stream_bytes=len(payload),
        )
        return [payload]

    monkeypatch.setattr(recovery, "stream_pdf", edge)
    stored, route = recovery.recover_pdf(example_document(), storage, marker, trace)
    assert bool(stored) is closed
    assert route == ("edge_cdp_stream" if closed else None)
    assert marker.exists() is not closed
    assert trace["credits"] == 7
    assert trace["edge"]["session_blocked"] is not closed
    assert len(list(storage.root.glob("sha256/*/*"))) == int(closed)


def test_failed_document_is_not_retried_on_resume(tmp_path, monkeypatch):
    storage = recovery.LocalBinaryStorage(tmp_path / "binaries")
    state = recovery.en.DownloadState(tmp_path, storage)
    document = example_document()
    row = {
        "role": "primary",
        "name": document.original_name,
        "extension": "pdf",
        "document_id": document.document_id,
    }
    candidates = {"A": ("ref", document, [row])}
    fake_acquire = Mock(return_value=(None, None))
    monkeypatch.setattr(recovery, "recover_pdf", fake_acquire)
    args = (candidates, ["A"], state, tmp_path / "edge.lock", None)
    assert recovery.run_lot(*args) == 2
    assert recovery.run_lot(*args) == 2
    fake_acquire.assert_called_once()
    case = recovery.manual.read_json(tmp_path / "recovery_results.json")["ref"]
    assert case["status"] == "not_resolved"
    assert case["review_category"] == "insufficient_evidence"


@pytest.mark.parametrize("declared_mib", [11, 17])
def test_rejected_pdf_preserves_declared_length(declared_mib):
    declared = declared_mib * (1024**2)
    trace = {}
    response = {
        "responseStatusCode": 200,
        "responseHeaders": [
            {"name": "Content-Type", "value": "application/pdf"},
            {"name": "Content-Length", "value": str(declared)},
        ],
    }
    with pytest.raises(recovery.lab.RejectionError, match="declared_size_limit"):
        recovery.lab.response_length(response, diagnostics=trace)
    assert trace == {"declared_bytes": declared}


@pytest.mark.parametrize("has_invitation", [False, True])
def test_archived_notice_requires_corroboration(tmp_path, monkeypatch, has_invitation):
    notice = {"role": "primary", "extension": "pdf", "name": "8. AVISO DE INVITACION PUBLICA"}
    invitation = {
        "role": "primary",
        "extension": "pdf",
        "name": "Invitaci\u00f3n p\u00fablica",
        "document_id": "21",
        "url": PDF_URL,
    }
    inventory = [notice, invitation] if has_invitation else [notice]
    monkeypatch.setattr(
        recovery.manual,
        "archived_inventory",
        lambda _: ({"ref": {"codigo_proceso": "archived-case"}}, {"ref": inventory}, {}),
    )
    state = recovery.en.DownloadState(tmp_path, recovery.LocalBinaryStorage(tmp_path / "binaries"))
    candidates, plan = recovery.saved_or_pending(tmp_path, [], state)
    assert bool(candidates) is has_invitation
    expected = "eligible" if has_invitation else "notice_needs_corroboration"
    assert plan == [{"process": "archived-case", "status": expected}]
