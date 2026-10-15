import uuid
from dataclasses import replace
from decimal import Decimal

import pytest

from public_procurement.extraction.consolidation import consolidate, normalized_unit
from public_procurement.extraction.domain.structured import make_fact

from .test_structured_rules import fragment

PROCESS = uuid.uuid4()


def fact(
    kind,
    *,
    string=None,
    number=None,
    unit=None,
    normalized=None,
    confidence="0.8",
    group=None,
    subject=None,
    source=None,
    boolean=None,
):
    source = source or fragment("Texto fuente", {"kind": "pdf_page", "page_number": 3})
    return replace(
        make_fact(
            PROCESS,
            (source,),
            kind,
            "test-rule",
            "structured-v1",
            string=string,
            number=Decimal(str(number)) if number is not None else None,
            unit=unit,
            normalized=normalized,
            confidence=confidence,
            group=group,
            subject=subject,
            boolean=boolean,
        ),
        id=uuid.uuid4(),
    )


def product(name, size=200, unit="ml", **kwargs):
    return fact(
        "product",
        string=name,
        normalized={"name": name, "presentation": str(size), "unit": unit},
        **kwargs,
    )


def item(
    quantity=400, price=None, total=None, group="row", description="Refrigerios PACK", **kwargs
):
    return fact(
        "purchase_item",
        string=description,
        group=group,
        normalized={
            "description": description,
            "quantity": str(quantity),
            "unit": "PACK",
            "unit_price_cop": str(price) if price is not None else None,
            "total_cop": str(total) if total is not None else None,
        },
        **kwargs,
    )


def of_type(summary, kind):
    return [value for value in summary.facts if value.canonical_type == kind]


def test_products_trivial_aliases_keep_all_sources_and_corroborate():
    sources = [product("JUGOS TETRA HIT"), product("jugo hit tetra"), product("Jugo Hit")]
    result = of_type(consolidate(PROCESS, sources), "PRODUCT")
    assert len(result) == 1
    assert result[0].canonical_value["value"] == {
        "name": "jugo hit",
        "presentation_value": 200,
        "presentation_unit": "ml",
    }
    assert set(result[0].evidence_ids) == {f.id for f in sources}
    assert result[0].canonical_value["corroborated"]
    assert result[0].confidence == Decimal("0.8")
    assert (
        len(
            of_type(
                consolidate(
                    PROCESS,
                    [
                        product("Ponque Chocorramo tradicional", 65, "gr"),
                        product("Chocorramo tradicional", 65, "g"),
                    ],
                ),
                "PRODUCT",
            )
        )
        == 1
    )


def test_different_products_or_sizes_are_not_fuzzy_merged():
    result = consolidate(PROCESS, [product("Hit", 200), product("Hit", 500), product("Hito", 200)])
    assert len(of_type(result, "PRODUCT")) == 3


def test_confidence_and_structured_source_preference_are_transparent():
    pdf = fact("unspsc", string="50192703")
    docx = fact(
        "unspsc",
        string="50192703",
        confidence="1.0",
        source=fragment(
            "50192703",
            {"kind": "docx_table_cell", "table_number": 1, "row_number": 2, "column_number": 1},
        ),
    )
    result = consolidate(PROCESS, [pdf, docx]).facts[0]
    assert result.confidence == Decimal("1.0")
    assert result.canonical_value["corroborated"]
    assert result.canonical_value["candidates"][0]["preferred_fact_id"] == str(docx.id)
    tied = replace(pdf, confidence=Decimal("1.0"))
    assert consolidate(PROCESS, [tied, docx]).facts[0].canonical_value["candidates"][0][
        "preferred_fact_id"
    ] == str(docx.id)


def test_repeated_same_fragment_is_not_independent_corroboration():
    source = fragment("UNSPSC 50192703")
    result = consolidate(
        PROCESS,
        [
            fact("unspsc", string="50192703", source=source),
            fact("unspsc", string="50192703", source=source),
        ],
    ).facts[0]
    assert not result.canonical_value["corroborated"]


@pytest.mark.parametrize(
    ("kind", "unit"), [("quantity", "PACK"), ("unit_price_cop", "COP"), ("total_cop", "COP")]
)
def test_contradictory_numbers_keep_candidates_and_select_no_value(kind, unit):
    result = consolidate(
        PROCESS, [fact(kind, number=400, unit=unit), fact(kind, number=450, unit=unit)]
    ).facts[0]
    assert result.status == "conflict"
    assert result.canonical_value["value"] is None
    assert len(result.canonical_value["candidates"]) == 2
    assert result.canonical_value["review_required"]
    assert not result.canonical_value["corroborated"]


def test_partial_and_complete_items_merge_with_field_provenance_and_confidence():
    partial = item(confidence="1.0", group="table-row")
    complete = item(price=5200, total=2080000, group="pdf-row")
    result = of_type(consolidate(PROCESS, [partial, complete]), "PURCHASE_ITEM")[0]
    assert result.status == "confirmed"
    assert result.canonical_value["value"]["quantity"] == 400
    assert result.canonical_value["value"]["unit_price_cop"] == 5200
    assert result.canonical_value["field_sources"]["unit_price_cop"] == [str(complete.id)]
    assert result.canonical_value["field_confidence"]["unit_price_cop"] == "0.8"
    assert result.confidence == Decimal("1.0")


def test_item_conflict_is_visible_in_each_disputed_field():
    summary = consolidate(PROCESS, [item(400, 5200), item(450, 5300, group="other")])
    result = of_type(summary, "PURCHASE_ITEM")[0]
    assert result.status == "conflict"
    assert result.canonical_value["value"]["quantity"] is None
    assert result.canonical_value["value"]["unit_price_cop"] is None
    assert len(result.canonical_value["field_candidates"]["quantity"]) == 2
    assert len(summary.conflicts) == 1


def test_different_item_descriptions_are_not_merged_to_fill_missing_prices():
    result = consolidate(
        PROCESS, [item(description="Refrigerios A"), item(price=5200, description="Refrigerios B")]
    )
    items = of_type(result, "PURCHASE_ITEM")
    assert len(items) == 2
    incomplete = next(
        i for i in items if i.canonical_value["value"]["description"] == "refrigerios a"
    )
    assert "unit_price_cop" not in incomplete.canonical_value["value"]
    assert any("unit_price_cop" in key for key in result.missing_fields)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("mL", "ml"), ("gr", "g"), ("UNIDADES", "unidad"), ("PACK", "PACK"), ("PAQUETE", "PAQUETE")],
)
def test_unit_normalization_does_not_equate_pack_and_paquete(value, expected):
    assert normalized_unit(value) == expected


def test_money_decimal_scale_is_normalized_and_budget_does_not_merge_with_item_total():
    summary = consolidate(
        PROCESS,
        [
            fact("total_cop", number="2080000.000000", unit="COP"),
            fact("total_cop", number="2080000", unit="COP"),
            fact("official_budget_cop", number="2080000", unit="COP"),
        ],
    )
    assert len(summary.facts) == 2
    assert of_type(summary, "TOTAL_COP")[0].canonical_value["value"]["value"] == 2080000


def test_day_kinds_and_boolean_unknown_are_not_silently_equated():
    summary = consolidate(
        PROCESS,
        [
            fact("payment_term", number=30, unit="días calendario"),
            fact("payment_term", number=30, unit="días hábiles"),
            fact("rup", boolean=None, subject="rup"),
            fact("rup", boolean=False, subject="rup"),
        ],
    )
    assert len(summary.conflicts) == 2
    states = [
        c["value"]["state"]
        for c in of_type(summary, "RUP_REQUIRED")[0].canonical_value["candidates"]
    ]
    assert sorted(states) == ["not_required", "unknown"]


def test_idempotence_is_order_independent_and_versions_have_distinct_snapshots():
    inputs = [product("Hit"), product("Hit")]
    first = consolidate(PROCESS, inputs)
    assert first == consolidate(PROCESS, list(reversed(inputs)))
    assert first.facts[0].id != consolidate(PROCESS, inputs, "canonical-v2").facts[0].id
    assert first.facts[0].id != consolidate(PROCESS, [*inputs, product("Other")]).facts[0].id


def test_absent_requirements_stay_absent_and_policy_does_not_cancel_product_guarantee():
    summary = consolidate(
        PROCESS,
        [
            fact("guarantee", boolean=False, subject="policy"),
            fact("guarantee", boolean=True, subject="performance_guarantee"),
        ],
    )
    assert not summary.conflicts
    assert len(of_type(summary, "GUARANTEE_REQUIRED")) == 2
    assert "RUP_REQUIRED" in summary.missing_fields
    assert "EXPERIENCE_REQUIRED" in summary.missing_fields


def test_nonpersisted_or_foreign_facts_are_rejected():
    source = product("Hit")
    with pytest.raises(ValueError, match="persistidos"):
        consolidate(PROCESS, [replace(source, id=None)])
    with pytest.raises(ValueError, match="proceso"):
        consolidate(uuid.uuid4(), [source])
