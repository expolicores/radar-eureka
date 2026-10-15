import uuid
from dataclasses import replace

import pytest

from public_procurement.eureka.config import CATALOG_V1, DEFAULT_CONFIG
from public_procurement.eureka.domain.discovery import (
    OpportunityState,
    ProcessFacts,
    evaluate_process,
)


def facts(**changes):
    return replace(
        ProcessFacts(
            uuid.uuid4(),
            "CO1.REQ.1",
            None,
            None,
            None,
            "Boyacá",
            None,
            None,
            "Publicado",
            "Presentación de oferta",
        ),
        **changes,
    )


PRIORITY_CODES = tuple(code for category in CATALOG_V1 for code in category.priority_unspsc)
CANDIDATE_CODES = tuple(code for category in CATALOG_V1 for code in category.candidate_unspsc)


@pytest.mark.parametrize("code", PRIORITY_CODES)
def test_priority_unspsc_can_discover_without_words(code) -> None:
    result = evaluate_process(facts(category_code="V1." + code), DEFAULT_CONFIG)
    assert result.active
    assert result.score == 20
    assert result.matched_unspsc == (code,)


@pytest.mark.parametrize("code", CANDIDATE_CODES)
def test_candidate_codes_have_lower_weight(code) -> None:
    result = evaluate_process(facts(category_code=code), DEFAULT_CONFIG)
    assert result.active
    assert result.score == 10


@pytest.mark.parametrize(
    ("changes", "score"),
    [
        ({"title": "Refrigerios"}, 30),
        ({"title": "Adquisición de bienes"}, 15),
        ({"description": "Día del colegio"}, 15),
        ({"entity_name": "Personería"}, 10),
    ],
)
def test_interest_uses_or_not_and(changes, score) -> None:
    result = evaluate_process(facts(**changes), DEFAULT_CONFIG)
    assert result.active
    assert result.score == score


def test_no_match_is_inactive_even_with_attractive_amount() -> None:
    result = evaluate_process(
        facts(title="Objeto sin señales", base_price_cop=4_000_000), DEFAULT_CONFIG
    )
    assert not result.active
    assert result.state is OpportunityState.NO_MATCH
    assert result.score == 0


def test_unicode_and_case_and_multiple_categories_do_not_multiply_group_points() -> None:
    result = evaluate_process(
        facts(
            title="PAPELERÍA, TÓNER, televisores y refrigerios", entity_name="INSTITUCIÓN EDUCATIVA"
        ),
        DEFAULT_CONFIG,
    )
    assert set(result.matched_categories) == {
        "office_supplies",
        "basic_technology",
        "packaged_food",
    }
    assert result.score == 40
    assert len([r for r in result.reasons if r.code == "product"]) == 1


def test_high_amount_is_penalty_and_never_a_hard_exclusion() -> None:
    result = evaluate_process(
        facts(title="Suministro de refrigerios", base_price_cop=20_000_000), DEFAULT_CONFIG
    )
    assert result.active
    assert result.score == 20
    assert result.penalties[0].code == "high_amount"


@pytest.mark.parametrize(
    "text",
    [
        "Construcción de edificio",
        "Consultoría especializada",
        "Interventoría",
        "Servicios profesionales",
        "Prestación de servicios de apoyo a la gestión",
        "Desarrollo de software a medida",
    ],
)
def test_clear_exclusions_override_entity_and_unspsc_interest(text) -> None:
    result = evaluate_process(
        facts(title=text, entity_name="Alcaldía", category_code="50192703"), DEFAULT_CONFIG
    )
    assert not result.active
    assert result.state is OpportunityState.EXCLUDED


def test_mixed_supply_and_services_is_reviewed_instead_of_discarded() -> None:
    result = evaluate_process(
        facts(title="Suministro de televisores con servicios profesionales de instalación"),
        DEFAULT_CONFIG,
    )
    assert result.active
    assert result.penalties[0].code == "mixed_professional_services"


def test_barriers_are_explicit_and_do_not_discard() -> None:
    result = evaluate_process(
        facts(title="Papelería con múltiples entregas, RUP obligatorio y garantías altas"),
        DEFAULT_CONFIG,
    )
    assert result.active
    assert {p.code for p in result.penalties} == {
        "multiple_deliveries",
        "mandatory_rup",
        "high_guarantees",
    }
    assert result.score == 0


def test_negated_barrier_is_not_applied() -> None:
    result = evaluate_process(
        facts(title="Papelería: no se requiere RUP obligatorio"), DEFAULT_CONFIG
    )
    assert not result.penalties


def test_positive_amount_and_logistics_have_separate_reasons() -> None:
    result = evaluate_process(
        facts(title="Papelería, entrega única", base_price_cop=5_000_000), DEFAULT_CONFIG
    )
    assert result.score == 50
    assert {r.code for r in result.reasons} == {"product", "attractive_amount", "simple_logistics"}


@pytest.mark.parametrize("status", ["Vencido", "Cerrado", "Adjudicado", "Cancelado"])
def test_terminal_process_remains_historical_but_not_active(status) -> None:
    result = evaluate_process(facts(title="Refrigerios", status=status), DEFAULT_CONFIG)
    assert result.state is OpportunityState.CLOSED
    assert not result.active


def test_geography_is_extensible_preference_not_a_hard_filter() -> None:
    result = evaluate_process(facts(title="Papelería", department="Antioquia"), DEFAULT_CONFIG)
    assert result.active
    assert result.penalties[0].code == "outside_geography"


def test_prepared_snacks_are_conditional() -> None:
    result = evaluate_process(facts(title="Refrigerios preparados"), DEFAULT_CONFIG)
    assert "prepared_snacks" in result.matched_categories
    assert any("inocuidad" in note for note in result.review_notes)


def test_score_is_arithmetic_sum_of_unique_reasons_and_penalties() -> None:
    result = evaluate_process(
        facts(
            title="Suministro de elementos y refrigerios para el día del colegio",
            category_code="50192703",
            entity_name="Institución Educativa",
            base_price_cop=4_000_000,
        ),
        DEFAULT_CONFIG,
    )
    assert result.score == 85
    assert result.score == sum(r.points for r in result.reasons) - sum(
        p.points for p in result.penalties
    )


def test_negated_terminal_status_does_not_close_radar() -> None:
    result = evaluate_process(facts(title="Papelería", status="No adjudicado"), DEFAULT_CONFIG)
    assert result.active


def test_configuration_rejects_negative_positive_weights() -> None:
    with pytest.raises(ValueError, match="negativos"):
        replace(DEFAULT_CONFIG.weights, product=-10)
