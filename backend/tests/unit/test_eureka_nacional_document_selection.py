"""Offline tests for governing-document recognition and selection order. Titles are modeled
on stored inventories; no entity- or process-specific rules."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_experience as rules


@pytest.mark.parametrize(
    "name",
    [
        "CONDICIONES GENERALES DE PARTICIPACION_0001",
        "CONDICIONES GENERALES DE PARTICIPACIÓN REPUESTOS PARA MANTENIMIENTO",
        "Condiciones de participación",
        "2. CONDICIONES PARA LA PARTICIPACION",
        "Reglas de participación del proceso",
        "Condiciones generales para la presentación de ofertas",
        "Condiciones de presentación de propuestas",
    ],
)
def test_participation_conditions_are_governing_documents(name):
    assert rules.document_role(name) == "primary"


@pytest.mark.parametrize(
    ("name", "role"),
    [
        # Identifications already validated stay unchanged.
        ("Invitación", "primary"),
        ("IPMC-115-2026 INVITACION PUBLICA", "primary"),
        ("Pliego de condiciones definitivo", "primary"),
        ("ESTUDIOS PREVIOS_0001", "support"),
        ("Adenda No. 1", "amendment"),
        ("Modificación condiciones de participación", "amendment"),
        ("FORMATOS", "support"),
        ("COTIZACIONES_0001", "excluded"),
        # Ambiguous titles do not become governing documents.
        ("Condiciones técnicas mínimas", "unknown"),
        ("Condiciones del contrato de seguro", "unknown"),
        ("CDP_0001", "unknown"),
        ("ESTUDIO DE MERCADO_0001", "unknown"),
        ("AVISO DE LIMITACIÓN A MIPYMES", "unknown"),
    ],
)
def test_validated_roles_are_preserved_and_ambiguous_titles_are_not_promoted(name, role):
    assert rules.document_role(name) == role


def order(names):
    documents = [(name, rules.document_role(name)) for name in names]
    documents.sort(key=lambda d: rules.document_priority(d[0], d[1], rules.document_role_hint(*d)))
    return [name for name, _ in documents]


def test_governing_conditions_lead_and_administrative_support_goes_last():
    # Arrange: the inventory shape observed for a minimum-amount SECOP II process.
    names = [
        "CDP_0001",
        "CONDICIONES GENERALES DE PARTICIPACION_0001",
        "COTIZACIONES_0001",
        "ESTUDIO DE MERCADO_0001",
        "ESTUDIOS PREVIOS_0001",
    ]

    # Act
    ordered = order(names)

    # Assert
    assert ordered == [
        "CONDICIONES GENERALES DE PARTICIPACION_0001",
        "ESTUDIOS PREVIOS_0001",
        "ESTUDIO DE MERCADO_0001",
        "CDP_0001",
        "COTIZACIONES_0001",
    ]


@pytest.mark.parametrize(
    "administrative",
    ["CDP", "SOLICITUD CDP", "SOLICITUD PAA", "1- BANCO DE PROYECTOS", "ANALISIS DEL SECTOR"],
)
def test_administrative_support_never_displaces_an_unidentified_document(administrative):
    assert order([administrative, "Documento del proceso"]) == [
        "Documento del proceso",
        administrative,
    ]


def test_invitation_still_precedes_participation_conditions_marked_final():
    ordered = order(["Condiciones de participación", "Invitación pública definitiva"])

    assert ordered[0] == "Invitación pública definitiva"


def test_ambiguous_title_never_displaces_a_valid_invitation():
    ordered = order(["Condiciones técnicas mínimas", "Invitación", "Estudios previos"])

    assert ordered == ["Invitación", "Estudios previos", "Condiciones técnicas mínimas"]


# ---------------------------------------------------------------- «convocatoria»

from types import SimpleNamespace  # noqa: E402


def fragment(text, page=1):
    return SimpleNamespace(text=text, source_locator={"page_number": page})


@pytest.mark.parametrize(
    "name", ["CONVOCATORIA 20 DE 2026", "Convocatoria pública No. 3", "03 convocatoria"]
)
def test_a_call_is_only_a_governing_hint_by_name(name):
    role = rules.document_role(name)

    assert role == "unknown"
    assert rules.document_role_hint(name, role) == "primary"


@pytest.mark.parametrize(
    ("name", "role"),
    [
        ("03. Aviso convocatoria SASI 023 DE 2026", "unknown"),
        ("AVISO DE CONVOCATORIA PUBLICA- PROCESO AI-SASI-4781-2026", "unknown"),
        ("Estudios previos convocatoria 20", "support"),
        ("Adenda a la convocatoria", "amendment"),
        ("Invitación convocatoria 2026", "primary"),
    ],
)
def test_notices_and_already_recognized_documents_get_no_call_hint(name, role):
    assert rules.document_role(name) == role
    assert rules.document_role_hint(name, rules.document_role(name)) is None


def test_call_is_confirmed_as_governing_when_its_text_sets_participation_conditions():
    entry = {"name": "CONVOCATORIA 20 DE 2026", "role": "unknown", "role_hint": "primary"}
    fragments = [
        fragment("Objeto: suministro de papelería."),
        fragment("DOCUMENTOS DE LA PROPUESTA\nCertificación de la experiencia.", page=6),
    ]

    assert rules.confirm_governing_by_content(entry, fragments) is True
    assert entry["role"] == "primary"
    assert entry["role_hint"] is None
    assert entry["role_source"] == "content_confirmed"
    assert entry["role_evidence"] == {"page": 6, "phrase": "documentos de la propuesta"}


def test_call_without_participation_conditions_stays_a_hint():
    entry = {"name": "CONVOCATORIA", "role": "unknown", "role_hint": "primary"}

    assert rules.confirm_governing_by_content(entry, [fragment("Cronograma y objeto.")]) is False
    assert (entry["role"], entry["role_hint"]) == ("unknown", "primary")


@pytest.mark.parametrize(
    "entry",
    [
        {"name": "CDP", "role": "unknown", "role_hint": None},
        {"name": "Estudio previo", "role": "support", "role_hint": None},
        {"name": "Invitación", "role": "primary", "role_hint": None},
    ],
)
def test_content_never_promotes_documents_without_a_governing_hint(entry):
    before = dict(entry)

    rules.confirm_governing_by_content(entry, [fragment("Requisitos habilitantes del proponente")])

    assert entry == before


def test_call_is_selected_before_studies_but_after_a_recognized_invitation():
    assert order(["CDP 069", "ESTUDIO PREVIO 20 DE 2026", "CONVOCATORIA 20 DE 2026"]) == [
        "CONVOCATORIA 20 DE 2026",
        "ESTUDIO PREVIO 20 DE 2026",
        "CDP 069",
    ]
    assert order(["CONVOCATORIA 20", "Invitación"])[0] == "Invitación"
