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
