"""Offline tests for the documentary dependency detector. Synthetic clauses modeled on the
patterns observed in stored invitations; no entity-specific rules."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_experience as rules

DEPENDENCY = ("NORMATIVA_CONDICIONAL", "document_dependency")


@pytest.mark.parametrize(
    "clause",
    [
        # Contracting regime or selection governed by an internal regulation.
        "Régimen especial según reglamento interno del consejo directivo.",
        "El proceso derivado de este análisis se rige por lo determinado en el manual de "
        "contratación institucional y el reglamento interno.",
        "La institución dará inicio al proceso de selección conforme al reglamento interno.",
        "La contratación se adelanta según el reglamento interno de contratación de la entidad.",
        "Los requisitos que deberá cumplir el oferente se establecen en el reglamento interno.",
        # Requirements or experience referred to other documents (unchanged behavior).
        "La experiencia deberá acreditarse mediante los documentos establecidos en el "
        "numeral 2.5 de la invitación pública.",
        "Los requisitos habilitantes se detallan en el documento de estudios previos.",
        "Requisitos jurídicos habilitantes: carta de presentación de la propuesta, según anexo 1.",
    ],
)
def test_governing_references_remain_dependencies(clause):
    assert rules.assertion(clause) == DEPENDENCY


@pytest.mark.parametrize(
    "clause",
    [
        # Administrative mentions: spending authority, functions, delegation, supervision.
        "Que el artículo 35, numeral 20, del reglamento interno del concejo establece que el "
        "presidente de la corporación actuará como ordenador del gasto.",
        "Conforme al reglamento interno, las funciones del secretario incluyen el archivo.",
        "La supervisión del contrato se ejercerá según el reglamento interno de la corporación.",
        "Por delegación prevista en el reglamento interno, el tesorero expedirá el registro.",
    ],
)
def test_administrative_internal_regulation_mentions_are_not_dependencies(clause):
    assert rules.assertion(clause) is None


def test_internal_regulation_mention_about_experience_is_still_a_dependency():
    clause = "La experiencia exigida se acreditará según el reglamento interno."

    assert rules.assertion(clause) == DEPENDENCY


def fragment(text, page=1):
    return SimpleNamespace(
        text=text, source_locator={"page_number": page, "extraction_method": "native_pdf_text"}
    )


def document(text, role="primary", identifier="1"):
    return {
        "document_id": identifier,
        "name": f"{role}.pdf",
        "role": role,
        "complete": True,
        "fragments": [fragment(text)],
    }


def test_administrative_mention_no_longer_blocks_or_conditions_the_result():
    # Arrange: complete invitation silent on experience, study with an administrative mention.
    invitation = document("REQUISITOS HABILITANTES\nCarta de presentación de la oferta.")
    study = document(
        "Que el reglamento interno del concejo establece que el presidente actuará como "
        "ordenador del gasto.",
        role="support",
        identifier="2",
    )

    # Act
    result = rules.classify_experience([invitation, study])

    # Assert: silence stays silence; it never becomes an explicit absence.
    assert result["dependencies"] == []
    assert result["status"] == "not_resolved"
    assert result["reason"] == "no_decisive_clause"
    assert result["review_category"] == "documentary_silence"


def test_spurious_dependency_no_longer_turns_an_explicit_waiver_ambiguous():
    invitation = document("No se exige experiencia contractual al proponente.")
    study = document(
        "Que el reglamento interno establece que el presidente es el ordenador del gasto.",
        role="support",
        identifier="2",
    )

    result = rules.classify_experience([invitation, study])

    assert result["status"] != "experience_ambiguous"
    assert result["dependencies"] == []
