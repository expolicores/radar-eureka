"""Offline tests for the v3 commercial profile: contextual corrections of false positives
without excluding legitimate supplies. Objects modeled on stored notices."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_commercial as commercial

CONFIG = Path(__file__).resolve().parents[2] / "config"
V2 = commercial.load_commercial_profile(CONFIG / "eureka_nacional_commercial.v2.json")
V3 = commercial.load_commercial_profile(CONFIG / "eureka_nacional_commercial.v3.json")


def assess(profile, obj):
    return commercial.assess_commercial(profile, obj, "", [])


def test_default_profile_is_v3_and_earlier_versions_stay_loadable():
    assert commercial.load_commercial_profile().version == "eureka-nacional-commercial-v3"
    assert V2.hard_service_without_supply is False
    assert all(not category.context_terms for category in V2.categories)


@pytest.mark.parametrize(
    "obj",
    [
        "Contratar la adquisición de una motobomba centrífuga portátil para emergencias",
        "Adquirir un generador eléctrico portátil a gasolina",
        "Adquisición de estufas ecoeficientes portátiles para comunidades rurales",
    ],
)
def test_portable_non_computing_equipment_is_not_technology(obj):
    assert assess(V3, obj)["primary_category"] != "informatica"


@pytest.mark.parametrize(
    "obj",
    [
        "Suministro de un equipo de cómputo portátil para el concejo municipal",
        "Adquisición de computadores portátiles para los mejores estudiantes",
        "Compraventa de dos equipos de cómputo portátiles para la institución",
    ],
)
def test_portable_computers_remain_technology(obj):
    result = assess(V3, obj)

    assert result["commercial_exclusion"] is None
    assert result["primary_category"] == "informatica"


def test_portable_radios_go_to_communications():
    result = assess(V3, "Adquisición de radios de comunicación portátil para la escuela")

    assert result["primary_category"] == "comunicaciones"


def test_animal_feed_is_excluded_with_an_explicit_reason():
    result = assess(V3, "Suministro de alimentos para los animales de granja de la institución")

    assert result["commercial_exclusion"] == "category_excluded"
    assert {"category": "alimentacion", "phrase": "animales"} in result["category_exclusions"]


@pytest.mark.parametrize(
    "obj",
    [
        "Suministro de refrigerios para las actividades culturales del municipio",
        "Suministro de alimentación e hidratación para personal de la fuerza pública",
    ],
)
def test_human_food_supplies_stay_in(obj):
    assert assess(V3, obj)["primary_category"] == "alimentacion"


def test_maintenance_with_typos_is_a_primary_service():
    obj = "Contratar por prestación de sevicios el mantenimento de instrumentos musicales"

    assert assess(V3, obj)["commercial_exclusion"] == "primary_service"


def test_a_later_maintenance_mention_does_not_exclude_supplies():
    obj = (
        "Adquisición, suministro y entrega de tuberías y accesorios de fontanería para la "
        "reparación y mantenimiento de las redes de acueducto"
    )

    assert assess(V3, obj)["commercial_exclusion"] is None


def test_food_service_with_a_later_unrelated_mention_stays_reviewable():
    obj = (
        "El contratista se obliga a prestar el servicio de alimentación para los miembros de la "
        "fuerza pública que acompañan el mantenimiento del orden público"
    )

    result = assess(V3, obj)

    assert result["commercial_exclusion"] is None
    assert result["commercial_confidence"] == "mixed_review"


def test_forestry_compensation_is_excluded_but_nursery_tools_are_kept():
    trees = (
        "Suministrar individuos arbóreos de especies nativas, fertilizantes, herramientas "
        "para la compensación forestal"
    )
    tools = (
        "Suministro de herramientas y equipos para la producción de material vegetal en el "
        "vivero municipal"
    )

    assert assess(V3, trees)["commercial_exclusion"] == "category_excluded"
    assert assess(V3, tools)["primary_category"] == "ferreteria"


def test_logistics_without_event_context_is_dropped_explicitly():
    obj = (
        "Fortalecimiento de las capacidades operativas de la fuerza pública mediante apoyo "
        "logístico al aumento de pie de fuerza"
    )

    result = assess(V3, obj)

    assert result["commercial_exclusion"] is not None
    assert {"category": "eventos", "phrase": "sin_contexto"} in result["category_exclusions"]


@pytest.mark.parametrize(
    "obj",
    [
        "Prestación de servicios logísticos para la organización de la semana de la juventud",
        "Prestación de servicios para la organización y apoyo logístico de la final de la copa",
        "Prestación de servicios de apoyo logístico para el desarrollo del taller regional",
    ],
)
def test_logistics_with_event_context_stays_reviewable(obj):
    result = assess(V3, obj)

    assert result["commercial_exclusion"] is None
    assert result["commercial_confidence"] == "mixed_review"


def test_institutional_calendars_are_stationery_and_keep_the_food_match():
    obj = (
        "Compraventa de calendarios institucionales con información de la gestión y de "
        "refrigerios para la jornada de rendición de cuentas"
    )

    result = assess(V3, obj)

    assert result["primary_category"] == "papeleria"
    assert "alimentacion" in {match["category"] for match in result["category_matches"]}
