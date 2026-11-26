"""Regressions for bidder experience mandates and OCR bookmark selection."""

import sys
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_en01 as en
import eureka_nacional_experience as rules


def fragment(text, page):
    return SimpleNamespace(
        text=text, source_locator={"page_number": page, "extraction_method": "ocr_text"}
    )


def primary(*fragments, complete=False):
    return {
        "document_id": "P",
        "name": "Invitacion",
        "role": "primary",
        "complete": complete,
        "fragments": fragments,
    }


def test_ocr_passive_mandate_prioritizes_a_partial_primary():
    clause = (
        "13.2 EXPERIENCIA M\u00cdNIMA Z i , |\nLa experiencia del proponente se acreditar\u00e1 "
        "en a (01) contrato debidamente ejecutado y finalizado, cuyo objeto se relacione."
    )
    result = rules.classify_experience([primary(fragment(clause, 9))])
    assert result["status"] == "not_resolved"
    assert result["review_category"] == "explicit_requirement"
    assert result["review_reason"] == "general_bidder_mandate_partial_primary"
    assert {e["page"] for e in result["review_evidence"]} == {9}


def test_ocr_damaged_subject_needs_bidder_checklist_elsewhere_in_same_primary():
    clause = fragment(
        "416.14 EXPERIENCIA\n| El aroma deber\u00e1 aportar su experiencia espec\u00edfica, "
        "verificable, relacionada con el objeto a contratar.",
        27,
    )
    checklist = fragment(
        "15. Experiencia del Proponente, (Anexo 3).\n16. Certificados que acrediten experiencia.",
        5,
    )
    unsupported = rules.classify_experience([primary(clause)])
    assert unsupported["review_category"] == "insufficient_evidence"
    corroborated = rules.classify_experience([primary(checklist, clause)])
    assert corroborated["status"] == "not_resolved"
    assert corroborated["review_category"] == "explicit_requirement"
    assert {e["basis"] for e in corroborated["review_evidence"]} == {
        "ocr_corroborated_bidder_mandate"
    }
    same_page = rules.classify_experience([primary(fragment(checklist.text, 27), clause)])
    assert same_page["review_category"] == "insufficient_evidence"


@pytest.mark.parametrize(
    ("clause", "expected"),
    [
        (
            "El oferente deber\u00e1 aportar su experiencia espec\u00edfica de suministro.",
            rules.REQ,
        ),
        ("El proponente deber\u00e1 acreditar experiencia mediante un contrato.", rules.REQ),
        ("Los licitantes deber\u00e1n demostrar su experiencia contractual.", rules.REQ),
        ("Si se pide, el oferente deber\u00e1 acreditar experiencia.", rules.CONDITIONAL),
        (
            "Solo para Mipymes el proponente deber\u00e1 acreditar su experiencia.",
            rules.CONDITIONAL,
        ),
        (
            "El representante legal deber\u00e1 aportar su experiencia espec\u00edfica.",
            rules.CONDITIONAL,
        ),
        (
            "El fabricante deber\u00e1 acreditar experiencia mediante contratos ejecutados.",
            rules.CONDITIONAL,
        ),
        (
            "Para acreditar la experiencia, el proponente deber\u00e1 presentar certificados de "
            "experiencia del proponente.",
            rules.CONDITIONAL,
        ),
        (
            "Dicha experiencia se acreditar\u00e1 mediante certificaciones "
            "expedidas por un tercero.",
            rules.CONDITIONAL,
        ),
        ("No se exige experiencia contractual.", rules.NEG),
    ],
)
def test_mandate_does_not_override_scope_and_negation(clause, expected):
    assert rules.clause_rule(clause) == expected


def test_pending_amendment_preserves_insufficient_priority():
    mandate = fragment("El oferente deber\u00e1 aportar su experiencia espec\u00edfica.", 6)
    amendment = {
        "document_id": "different",
        "name": "Adenda",
        "role": "amendment",
        "complete": False,
    }
    result = rules.classify_experience([primary(mandate), amendment])
    assert result["status"] == "not_resolved"
    assert result["review_category"] == "insufficient_evidence"


def test_ocr_selector_prioritizes_relevant_bookmark_over_cover_and_ignores_unneeded_pages():
    pytest.importorskip("pypdfium2")
    pdf = PdfWriter()
    for _ in range(7):
        pdf.add_blank_page(width=120, height=120)
    pdf.add_outline_item("Presupuesto", 2)
    pdf.add_outline_item("Requisitos habilitantes", 4)
    pdf.add_outline_item("Experiencia espec\u00edfica", 5)
    output = BytesIO()
    pdf.write(output)
    output.seek(0)
    pages = en.ocr_bookmark_pages(output)
    assert pages == [5, 6]
    native = SimpleNamespace(
        error_code=None,
        diagnostics={"native_pages_visited": 7},
        fragments=[],
        document=SimpleNamespace(original_name="Invitacion.pdf"),
    )
    assert en.select_ocr_pages(native, range(1, 8), 2, bookmarks=pages) == [5, 6]
    assert en.select_ocr_pages(native, [1, 2, 3, 5, 7], 2, bookmarks=pages) == [5, 1]
