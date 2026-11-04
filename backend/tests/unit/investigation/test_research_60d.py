from dataclasses import replace
from decimal import Decimal

from public_procurement.investigation.domain.television import Television
from public_procurement.investigation.research_comparison import compare_public_purchases


def purchase(**changes):
    return Television(
        **{
            "process_id": "REQ-A",
            "entity": "Entidad A",
            "description": "Televisor LG 55 pulgadas LED 4K Smart modelo 55ABC",
            "screen_size_inches": 55,
            "panel": "LED",
            "resolution": "4k",
            "smart": True,
            "brand": "LG",
            "model": "55ABC",
            "quantity": Decimal(2),
            "unit": "UNIDAD",
            "unit_price_cop": Decimal(100),
            "price_stage": "contract",
            "price_reliable": True,
            "evidence": [{"document": "CONTRATO.pdf", "page": 3}],
            "observation_id": "A",
            "purchased_at": "2026-09-10",
            "purchase_date_source": "socrata_fecha_de_firma",
            "vat_basis": "included",
            **changes,
        }
    )


def compare(first, second):
    return compare_public_purchases(
        [first, second], window_start="2026-09-04", window_before="2026-11-03"
    )


def test_moderate_difference_has_no_anomaly_threshold():
    first = purchase()
    second = purchase(
        process_id="REQ-B",
        entity="Entidad B",
        unit_price_cop=Decimal(102),
        observation_id="B",
        purchased_at="2026-10-30",
    )
    result = compare(first, second)
    signal = result["signals"][0]
    assert signal["type"] == "PUBLIC_PRICE_DIFFERENCE"
    assert Decimal(signal["difference_pct"]) == 2
    assert signal["threshold_pct"] is None
    assert signal["days_between"] == 50
    assert signal["comparability_level"] == "exact"
    assert signal["sides"][0]["evidence"]


def test_high_comparability_can_emit_investigative_signal():
    first = purchase(model=None)
    second = replace(
        first,
        process_id="REQ-B",
        entity="Entidad B",
        observation_id="B",
        unit_price_cop=Decimal(110),
    )
    assert compare(first, second)["signals"][0]["comparability_level"] == "high"


def test_partial_has_no_monetary_signal():
    first = purchase(model=None, panel=None)
    second = replace(
        first,
        process_id="REQ-B",
        entity="Entidad B",
        observation_id="B",
        unit_price_cop=Decimal(200),
    )
    assert not compare(first, second)["signals"]


def test_missing_purchase_date_does_not_borrow_publication_date():
    first = purchase(purchased_at=None, published_at="2026-10-20")
    second = purchase(process_id="REQ-B", entity="Entidad B", observation_id="B")
    pair = compare(first, second)["comparisons"][0]
    assert pair["days_between"] is None
    assert not pair["comparison_eligible"]
    assert "purchase_date_unknown_publication_not_substituted" in pair["limitations"]


def test_purchase_outside_declared_window_cannot_emit_signal():
    first = purchase(purchased_at="2026-08-15")
    second = purchase(process_id="REQ-B", entity="Entidad B", observation_id="B")
    assert not compare(first, second)["signals"]


def test_unaccepted_offer_never_becomes_purchase_price():
    first = purchase(price_stage="offer")
    second = purchase(process_id="REQ-B", entity="Entidad B", observation_id="B")
    assert not compare(first, second)["signals"]


def test_percentage_uses_lower_price_even_if_side_a_is_higher():
    first = purchase(unit_price_cop=Decimal(150))
    second = purchase(
        process_id="REQ-B", entity="Entidad B", observation_id="B", unit_price_cop=Decimal(100)
    )
    pair = compare(first, second)["comparisons"][0]
    assert Decimal(pair["absolute_difference_cop"]) == 50
    assert Decimal(pair["difference_pct"]) == 50


def test_known_different_tax_bases_block_comparison():
    first = purchase(vat_basis="excluded")
    second = purchase(
        process_id="REQ-B", entity="Entidad B", observation_id="B", vat_basis="included"
    )
    assert not compare(first, second)["signals"]


def test_critical_conflict_blocks_signal():
    first = purchase(warnings=["conflicting_canonical"])
    second = purchase(process_id="REQ-B", entity="Entidad B", observation_id="B")
    assert not compare(first, second)["signals"]


def test_professional_display_is_not_equated_with_consumer_tv():
    first = purchase(description="Televisor 55 pulgadas profesional tipo business")
    second = purchase(process_id="REQ-B", entity="Entidad B", observation_id="B")
    pair = compare(first, second)["comparisons"][0]
    assert pair["comparability_level"] == "not_comparable"
    assert "different_product_class" in pair["limitations"]


def test_noncritical_budget_variance_is_visible_without_deleting_contract_price():
    first = purchase(warnings=["noncritical_budget_conflict_preserved"])
    second = purchase(process_id="REQ-B", entity="Entidad B", observation_id="B")
    signal = compare(first, second)["signals"][0]
    assert "noncritical_budget_conflict_preserved" in signal["limitations"]


def test_exact_explicit_reference_does_not_invent_a_brand():
    first = purchase(brand=None, model="55XY9999ZZ", panel=None)
    second = purchase(
        process_id="REQ-B",
        entity="Entidad B",
        observation_id="B",
        brand="LG",
        model="55XY9999ZZ",
        panel=None,
    )
    signal = compare(first, second)["signals"][0]
    assert signal["comparability_level"] == "exact"
    assert signal["sides"][0]["characteristics"]["brand"] is None


def test_same_reference_does_not_override_incompatible_known_size():
    first = purchase(brand=None, model="55XY9999ZZ")
    second = purchase(
        process_id="REQ-B",
        entity="Entidad B",
        observation_id="B",
        brand=None,
        model="55XY9999ZZ",
        screen_size_inches=70,
    )
    assert not compare(first, second)["signals"]
