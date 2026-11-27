"""Offline tests for the SECOP I pilot classifier adjustments A (bidder sections) and B
(non-governing pending titles). Synthetic text modeled on the observed invitations."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_experience as rules

REQUIREMENT = (
    "El proponente debe acreditar UN (1) contrato y/o certificación, que dentro de su objeto "
    "y/o alcance contemple el SUMINISTRO Y/O COMPRAVENTA DE ELEMENTOS DE FERRETERÍA."
)


def fragment(text, page=14):
    return SimpleNamespace(
        text=text, source_locator={"page_number": page, "extraction_method": "native_pdf_text"}
    )


def invitation(text, *, complete=True):
    return {
        "document_id": "inv",
        "name": "Invitación",
        "role": "primary",
        "complete": complete,
        "fragments": [fragment(text)],
    }


def pending(name, role=None):
    return {
        "document_id": name,
        "name": name,
        "role": role or rules.document_role(name),
        "complete": False,
    }


def requirement_items(result):
    return [e for e in result["evidence"] if e["assertion_type"] == rules.REQ]


# ---------------------------------------------------------------- A: bidder sections


@pytest.mark.parametrize(
    "heading",
    [
        "EXPERIENCIA DEL PROPONENTE",
        "Experiencia del oferente",
        "4.3. EXPERIENCIA DEL PROPONENTE:",
        "EXPERIENCIA DEL OFERENTE.",
    ],
)
def test_bidder_section_gives_general_scope_to_an_obligatory_clause(heading):
    # Arrange: a generic unknown document stays pending, so prudence keeps the status open.
    docs = [invitation(f"{heading}\n{REQUIREMENT}"), pending("Otro documento")]

    # Act
    result = rules.classify_experience(docs)

    # Assert
    items = requirement_items(result)
    assert [i["scope"] for i in items] == ["general_bidder"]
    assert result["status"] == "not_resolved"
    assert result["review_category"] == "explicit_requirement"
    assert result["review_reason"] == "general_bidder_clause_in_complete_primary"


@pytest.mark.parametrize(
    "clause",
    [
        # Conditional or hypothetical.
        "En caso de consorcios o uniones temporales, la experiencia podrá ser acreditada por "
        "uno o varios de sus miembros.",
        # Scored, not habilitating.
        "Se asignarán 20 puntos al proponente que acredite experiencia en dos contratos "
        "adicionales como factor de calificación.",
        # Addressed to third parties.
        "El personal técnico deberá acreditar experiencia mínima de dos años en contratos.",
        # Descriptive only.
        "La experiencia es adecuada cuando se refiere al tipo de actividades previstas en el "
        "objeto del contrato a celebrar.",
        # Not applicable.
        "Para el presente proceso no se exige experiencia al proponente.",
    ],
)
def test_bidder_section_alone_never_creates_a_requirement(clause):
    result = rules.classify_experience([invitation(f"EXPERIENCIA DEL PROPONENTE\n{clause}")])

    assert requirement_items(result) == []
    assert result["status"] != "experience_required"


@pytest.mark.parametrize(
    "section",
    [
        "experiencia del proponente plural",
        "experiencia del proponente mipyme",
        "criterio diferencial para mipymes",
        "experiencia",
        "experiencia del personal",
    ],
)
def test_bidder_section_pattern_is_narrow(section):
    assert rules.BIDDER_SECTION.fullmatch(section) is None


def test_limited_section_keeps_its_limited_reading():
    text = (
        "CRITERIO DIFERENCIAL PARA MIPYMES\nLas Mipymes podrán acreditar la experiencia de que "
        "trata el presente numeral con máximo cinco contratos."
    )

    result = rules.classify_experience([invitation(text)])

    assert requirement_items(result) == []
    assert result["status"] != "experience_required"


# ---------------------------------------------------------------- B: non-governing pending


@pytest.mark.parametrize(
    "title",
    [
        "ANALISIS DEL SECTOR",
        "2 ANALISIS DEL SECTOR",
        "Análisis de sector",
        "ESTUDIOS DEL SECTOR",
        "CDP",
        "3 CERTIFICADO DE DISPONIBIIDAD PRESUPUESTAL".replace("DISPONIBIIDAD", "DISPONIBILIDAD"),
        "PAA",
        "Plan anual de adquisiciones",
        "BPIN",
    ],
)
def test_non_governing_pending_title_does_not_block_an_explicit_requirement(title):
    # Arrange: the Fómeque shape: complete invitation, support and non-governing pending.
    docs = [
        invitation(f"EXPERIENCIA DEL PROPONENTE\n{REQUIREMENT}"),
        pending("ESTUDIO PREVIO"),
        pending(title),
    ]

    # Act
    result = rules.classify_experience(docs)

    # Assert
    assert docs[2]["role"] == "unknown"
    assert result["status"] == "experience_required"
    assert result["reason"] == "explicit_bidder_requirement"
    assert result["document_coverage"]["non_governing_pending"] == [
        {"document_id": title, "document": title}
    ]
    assert title in {p["document"] for p in result["document_coverage"]["pending"]}


@pytest.mark.parametrize(
    ("title", "role"),
    [
        ("Otro documento", None),  # generic unknown: may be governing
        ("Documento técnico", None),
        ("Análisis del sector - Adenda 1", None),  # amendment by title
        ("ANALISIS DEL SECTOR", "amendment"),  # promoted by its cover once read
        ("Invitación definitiva", None),
    ],
)
def test_possibly_governing_pending_documents_still_block(title, role):
    docs = [invitation(f"EXPERIENCIA DEL PROPONENTE\n{REQUIREMENT}"), pending(title, role)]

    result = rules.classify_experience(docs)

    assert result["status"] == "not_resolved"
    assert result["document_coverage"]["non_governing_pending"] == []


def test_favorable_conclusion_still_requires_every_document():
    waiver = "EXPERIENCIA DEL PROPONENTE\nPara el presente proceso no se exige experiencia."
    docs = [invitation(waiver), pending("ANALISIS DEL SECTOR")]

    result = rules.classify_experience(docs)

    assert result["status"] != "no_experience_required"


def test_incomplete_invitation_is_never_unblocked_by_non_governing_titles():
    docs = [
        invitation(f"EXPERIENCIA DEL PROPONENTE\n{REQUIREMENT}", complete=False),
        pending("CDP"),
    ]

    result = rules.classify_experience(docs)

    assert result["status"] == "not_resolved"


def test_without_the_bidder_requirement_non_governing_titles_change_nothing():
    text = "EXPERIENCIA DEL PROPONENTE\nLa experiencia debe ser adecuada y proporcional."
    docs = [invitation(text), pending("ANALISIS DEL SECTOR"), pending("CDP")]

    result = rules.classify_experience(docs)

    assert result["status"] == "not_resolved"
    assert requirement_items(result) == []
