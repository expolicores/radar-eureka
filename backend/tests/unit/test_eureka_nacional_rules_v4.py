"""Offline regression tests for the contextual-v4 general rules: plural negations, the scope
of a negation around a bidder mandate, contracts the bidder must attach, and statutory
tie-break shares. Sentences are modeled on stored invitations but carry no entity-,
municipality- or process-specific rule."""

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_experience as rules
import eureka_nacional_findings as findings


def fragment(text, page=1):
    return SimpleNamespace(
        text=text, source_locator={"page_number": page, "extraction_method": "native_pdf_text"}
    )


def document(text, role="primary", identifier="1", complete=True):
    return {
        "document_id": identifier,
        "name": f"{role}.pdf",
        "role": role,
        "complete": complete,
        "pages_seen": [1] if complete else [],
        "total_pages": 1 if complete else None,
        "fragments": [fragment(text)] if complete else [],
    }


# ---------------------------------------------------------------- explicit negations


@pytest.mark.parametrize(
    "clause",
    [
        "No se exigen experiencia, capacidad financiera ni Registro Único de Proponentes.",
        "No se requieren experiencia ni indicadores financieros para este proceso.",
        "No se exige experiencia al proponente.",
    ],
)
def test_singular_and_plural_negations_are_waivers(clause):
    assert rules.assertion(clause) == (rules.NEG, "explicit_waiver")


def test_plural_waiver_followed_by_a_document_list_is_still_a_waiver():
    clause = (
        "No se exigen experiencia, capacidad financiera ni Registro Único de Proponentes. "
        "4.1 Persona natural: (a) copia de la cédula de ciudadanía; (b) certificado de "
        "matrícula mercantil con fecha de expedición no mayor a treinta (30) días"
    )

    assert rules.assertion(clause) == (rules.NEG, "explicit_waiver")


@pytest.mark.parametrize(
    "clause",
    [
        "No se exige experiencia mínima adicional a la señalada en el numeral anterior.",
        "No se exigen experiencia específica distinta de la general.",
    ],
)
def test_partial_negations_are_never_waivers(clause):
    assert rules.assertion(clause)[0] != rules.NEG


def test_short_plural_answer_under_an_experience_heading_is_scoped():
    page = "EXPERIENCIA DEL PROPONENTE: No se exigen."

    [item] = [
        e for e in rules.document_assertions(document(page)) if e["assertion_type"] == rules.NEG
    ]

    assert item["basis"] == "heading_scoped_waiver"


# ---------------------------------------------------------------- mandates


@pytest.mark.parametrize(
    "clause",
    [
        "El proponente deberá acreditar experiencia mínima en un contrato cuyo valor no sea "
        "inferior al 50% del presupuesto oficial.",
        "Documentos que acreditan la experiencia mínima (Anexo 5) El proponente deberá "
        "acreditar una experiencia mínima de dos (2) años, aportando máximo dos (2) "
        "certificaciones. • Validez: No se aceptarán copias de contratos.",
    ],
)
def test_a_negation_after_the_mandate_does_not_cancel_it(clause):
    assert rules.assertion(clause) == (rules.REQ, "bidder_experience_mandate")


def test_a_negation_before_the_mandate_still_cancels_it():
    clause = "No es obligatorio que el proponente deba acreditar experiencia en contratos."

    assert rules.assertion(clause)[0] != rules.REQ


@pytest.mark.parametrize(
    "clause",
    [
        "El proponente deberá anexar copia de dos (2) contratos ejecutados con entidades "
        "públicas para acreditar su experiencia.",
        "Para acreditar la experiencia, el oferente deberá allegar certificaciones de "
        "contratos ejecutados cuyo objeto sea similar.",
    ],
)
def test_attaching_executed_contracts_is_a_requirement(clause):
    assert rules.assertion(clause) == (rules.REQ, "bidder_contract_submission")


@pytest.mark.parametrize(
    "clause",
    [
        # optional or limited, never a general requirement
        "El proponente podrá anexar copia de contratos para acreditar experiencia adicional.",
        "Para los consorcios, el proponente deberá anexar los contratos de experiencia de "
        "cada integrante.",
        # the contractor's personnel, not the bidder
        "El contratista deberá anexar los contratos del personal con experiencia.",
    ],
)
def test_optional_limited_or_other_actor_contracts_are_not_general_requirements(clause):
    assert rules.assertion(clause) != (rules.REQ, "bidder_contract_submission")


def test_recognized_requirements_keep_their_earlier_basis():
    clause = (
        "El proponente debe anexar con su propuesta mínimo dos (2) certificaciones de "
        "experiencia sobre contratos ejecutados cuyo objeto sea el suministro de papelería."
    )

    assert rules.assertion(clause) == (rules.REQ, "mandatory_offer_certificates")


# ---------------------------------------------------------------- tie-break shares


@pytest.mark.parametrize(
    "clause",
    [
        "El integrante del proponente plural de que trata el anterior numeral debe aportar "
        "mínimo el veinticinco por ciento (25%) de la experiencia acreditada en la oferta.",
        "el integrante o los integrantes que tengan una participación de por lo menos el "
        "veinticinco por ciento (25 %) en el consorcio y aporten mínimo el veinticinco por "
        "ciento (25 %) de la experiencia general habilitante",
    ],
)
def test_statutory_tie_break_shares_are_another_criterion(clause):
    assert rules.assertion(clause) == (rules.OTHER, "other_subject_or_criterion")


def test_tie_break_share_inside_a_plural_bidder_section_is_not_a_restriction():
    page = (
        "10. PROPONENTES PLURALES Y EXPERIENCIA\n"
        "El integrante del proponente plural de que trata el anterior numeral debe aportar "
        "mínimo el veinticinco por ciento (25%) de la experiencia acreditada en la oferta."
    )

    result = rules.classify_experience([document(page)])

    assert result["reason"] != "limited_applicability"


def test_other_plural_shares_are_not_tie_breaks():
    clause = (
        "Para los proponentes plurales, uno de los integrantes del proponente debe aportar como "
        "mínimo el cuarenta por ciento (40%) de la experiencia."
    )

    assert rules.assertion(clause) != (rules.OTHER, "other_subject_or_criterion")


# ---------------------------------------------------------------- process level


def test_waiver_in_a_complete_primary_with_a_pending_study_is_priority_review():
    # Arrange
    invitation = document(
        "3. REQUISITOS HABILITANTES\nNo se exigen experiencia, capacidad financiera ni "
        "Registro Único de Proponentes."
    )
    pending_study = document("", "support", "2", complete=False)
    documents = [invitation, pending_study]

    # Act
    classification = rules.classify_experience(copy.deepcopy(documents))
    finding = findings.assess_finding(classification, documents)

    # Assert: formal status unchanged, shown as a favorable candidate with a warning.
    assert classification["status"] == "not_resolved"
    assert classification["review_category"] == "explicit_favorable"
    assert classification["classification_method"] == "en01-contextual-v4"
    assert finding["category"] == "priority_review"
    assert finding["basis"] == "explicit_waiver_pending_corroboration"
    assert "documentos_no_verificados_por_el_sistema" in finding["warnings"]
    assert finding["formal_status_unchanged"] is True


def test_human_review_is_attached_without_changing_the_category():
    invitation = document("No se exigen experiencia ni Registro Único de Proponentes.")
    review = {
        "identifiers": ["CO1.NTC.0001"],
        "observation": "no_experience_requirement_found",
        "system_verified": False,
    }
    classification = rules.classify_experience([invitation])

    with_review = findings.assess_finding(
        classification, [invitation], identifiers=["CO1.NTC.0001"], human_reviews=[review]
    )
    without = findings.assess_finding(classification, [invitation])

    assert with_review["category"] == without["category"]
    assert with_review["human_review"] == [review]
    assert with_review["human_review_changes_category"] is False
