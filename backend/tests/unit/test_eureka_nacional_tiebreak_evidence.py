"""Offline tests: experience shares of statutory tie-break criteria are never habilitating
requirements. Clauses modeled on stored invitations; no entity-specific rules."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_experience as rules

TIEBREAK = (
    "deberá presentar certificación expedida por la Agencia para la Reincorporación y la "
    "Normalización – ARN, donde acredite tal condición. Oferta presentada por un proponente "
    "plural (a) esté conformado por al menos una madre cabeza de familia y/o una persona en "
    "proceso de reincorporación o reintegración, y que tenga una participación de por lo "
    "menos el veinticinco por ciento (25%) en el proponente plural; (b) la madre cabeza de "
    "familia, la persona en proceso de reincorporación o reintegración, o la persona jurídica "
    "aporte mínimo el veinticinco por ciento (25%) de la experiencia acreditada en la oferta"
)


@pytest.mark.parametrize(
    "clause",
    [
        TIEBREAK,
        "La oferta presentada por un proponente plural donde la persona en condición de "
        "discapacidad aporte como mínimo el veinticinco por ciento (25%) de la experiencia "
        "acreditada en la oferta.",
        "La MIPYME, cooperativa o asociación mutual aporte mínimo el veinticinco por ciento "
        "(25%) de la experiencia acreditada en la oferta.",
        "Las mujeres víctimas de violencia intrafamiliar deberán aportar el 25% de la "
        "experiencia acreditada en la oferta.",
    ],
)
def test_tiebreak_experience_shares_are_other_criteria(clause):
    assert rules.assertion(clause) == (rules.OTHER, "other_subject_or_criterion")


@pytest.mark.parametrize(
    "clause",
    [
        "El proponente deberá acreditar experiencia contractual con dos contratos ejecutados.",
        "El proponente deberá presentar copia de mínimo uno (1) y máximo tres (3) contratos "
        "ejecutados y liquidados, registrados en el RUP, cuya experiencia sea igual o superior "
        "al 100 % del presupuesto oficial.",
    ],
)
def test_habilitating_requirements_are_still_requirements(clause):
    assert rules.assertion(clause)[0] == rules.REQ


def test_a_protected_subject_without_an_experience_share_keeps_its_reading():
    clause = (
        "La madre cabeza de familia que se presente como proponente deberá acreditar "
        "experiencia en dos contratos ejecutados."
    )

    assert rules.assertion(clause)[0] == rules.REQ


def test_tiebreak_clause_alone_never_concludes_experience_required():
    document = {
        "document_id": "1",
        "name": "Invitación",
        "role": "primary",
        "complete": True,
        "fragments": [type("F", (), {"text": TIEBREAK, "source_locator": {"page_number": 29}})()],
    }

    result = rules.classify_experience([document])

    assert result["status"] != "experience_required"


@pytest.mark.parametrize(
    "clause",
    [
        "Sillas blancas sin brazo. Estructura ergonómica que proporciona una cómoda experiencia "
        "de asiento, adaptándose a la forma del cuerpo.",
        "Su soporte lumbar evita tensiones en la espalda, mientras que los apoyabrazos aseguran "
        "una experiencia de trabajo más cómoda.",
        "Pantalla de alta resolución para una mejor experiencia de usuario.",
    ],
)
def test_product_descriptions_are_not_about_experience(clause):
    assert rules.assertion(clause) is None


def test_a_product_description_never_hides_a_real_requirement():
    clause = (
        "Silla con una cómoda experiencia de asiento. El proponente deberá acreditar "
        "experiencia en dos contratos ejecutados de suministro de mobiliario."
    )

    assert rules.assertion(clause)[0] == rules.REQ
