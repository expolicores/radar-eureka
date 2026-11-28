"""Offline tests for the v2 commercial profile: synonyms, food and events categories and
reviewable mixed objects, without accepting unrelated services. Objects modeled on stored
notices; no entity-specific rules."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_commercial as commercial

CONFIG = Path(__file__).resolve().parents[2] / "config"
V1 = commercial.load_commercial_profile(CONFIG / "eureka_nacional_commercial.v1.json")
V2 = commercial.load_commercial_profile(CONFIG / "eureka_nacional_commercial.v2.json")


def assess(profile, obj):
    return commercial.assess_commercial(profile, obj, "", [])


def test_default_profile_is_v2_and_v1_is_preserved():
    assert commercial.load_commercial_profile().version == "eureka-nacional-commercial-v2"
    assert V1.version == "eureka-nacional-commercial-v1"
    assert V1.mixed_review is False


@pytest.mark.parametrize(
    ("obj", "category"),
    [
        (
            "Adquisición de equipos tecnológicos para el fortalecimiento institucional",
            "informatica",
        ),
        ("Suministro de dotación (calzado y vestido de labor) para la auxiliar", "uniformes_epp"),
        ("Suministro de elementos de oficina para la personería municipal", "papeleria"),
        ("Suministro de consumibles de impresión y cartuchos de tóner", "papeleria"),
        ("Suministro de elementos didácticos para la escuela de artes", "educacion"),
        ("Adquisición de paquetes alimentarios para hogares víctimas", "alimentacion"),
        ("Suministro de refrigerios para las actividades culturales", "alimentacion"),
    ],
)
def test_synonyms_and_new_categories_recover_clear_goods(obj, category):
    result = assess(V2, obj)

    assert result["commercial_exclusion"] is None
    assert result["primary_category"] == category
    assert result["commercial_confidence"] == "goods"
    assert result["category_matches"][0]["object_terms"]  # traceable expression


@pytest.mark.parametrize(
    "obj",
    [
        "Suministro de alimentación, refrigerios y servicio de hospedaje para las festividades",
        "Prestación de servicios de apoyo logístico para organizar eventos institucionales",
        "Suministro de bienes y servicios logísticos para la organización de actividades",
    ],
)
def test_mixed_objects_stay_reviewable_and_never_confirmed(obj):
    result = assess(V2, obj)

    assert result["commercial_exclusion"] is None
    assert result["commercial_confidence"] == "mixed_review"


@pytest.mark.parametrize(
    "obj",
    [
        "Prestación de servicios de consultoría para eventos institucionales",
        "Prestación de servicios profesionales de apoyo a la gestión",
        "Prestación de servicios de capacitación a asociaciones de mineros",
        "Prestación de servicios de vigilancia para eventos institucionales",
        "Prestación de servicios de transporte terrestre de pasajeros para eventos",
        "Interventoría a la construcción de la tarima de eventos",
    ],
)
def test_unrelated_services_are_never_accepted(obj):
    result = assess(V2, obj)

    assert result["commercial_exclusion"] is not None
    assert result["commercial_confidence"] is None


@pytest.mark.parametrize(
    "obj",
    [
        "Adquisición de gallinas ponedoras y alimento tipo concentrado",
        "Suministro de alimentos para animales del zoológico",
        "Compra de ganado en pie para proyectos productivos",
    ],
)
def test_animal_feed_and_livestock_stay_out(obj):
    assert assess(V2, obj)["commercial_exclusion"] is not None


def test_v1_behavior_is_unchanged_for_mixed_and_food_objects():
    mixed = "Prestación de servicios de apoyo logístico para la organización de eventos"
    food = "Suministro de refrigerios para las actividades culturales"

    assert assess(V1, mixed)["commercial_exclusion"] == "primary_service"
    assert assess(V1, food)["commercial_exclusion"] is not None


def test_mixed_candidates_rank_after_clear_goods():
    base = {"validity_status": "open", "preferred_modality": True, "commercial_priority": "B"}

    clear = commercial.selection_rank({**base, "commercial_confidence": "goods"})
    mixed = commercial.selection_rank({**base, "commercial_confidence": "mixed_review"})

    assert clear < mixed


@pytest.mark.parametrize(
    "obj",
    [
        "Servicio de mantenimiento preventivo y correctivo de hardware de equipos de cómputo",
        "Prestación del servicio en mantenimiento de equipos tecnológicos: cámaras y computadores",
    ],
)
def test_equipment_maintenance_services_are_not_recovered(obj):
    assert assess(V2, obj)["commercial_exclusion"] is not None


@pytest.mark.parametrize(
    "obj",
    [
        "Apoyo logístico para la realización del evento deportivo departamental",
        "Organización y ejecución de actividades deportivas de integración",
        "Suministro de incentivos y apoyo logístico al desarrollo de actividades",
    ],
)
def test_event_objects_without_clear_supply_are_reviewable(obj):
    result = assess(V2, obj)

    assert result["commercial_exclusion"] is None
    assert result["commercial_confidence"] == "mixed_review"


def test_operational_adjectives_do_not_make_goods_mixed():
    obj = "Adquisición de equipos tecnológicos para fortalecer la capacidad técnica y operativa"

    assert assess(V2, obj)["commercial_confidence"] == "goods"
