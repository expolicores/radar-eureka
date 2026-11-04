import uuid
from decimal import Decimal

import pytest

from public_procurement.extraction.domain.content import EvidenceFragment
from public_procurement.extraction.research_tv_rules import (
    RESEARCH_TV_RULE_VERSION,
    extract_tv_research_facts,
)
from public_procurement.extraction.structured_rules import extract_facts


def fragment(text):
    return EvidenceFragment(
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
        "Propuesta Economica.pdf",
        1,
        text,
        {"kind": "pdf_page", "page_number": 1, "input_sha256": "sample-hash"},
    )


def test_opt_in_tv_row_retains_quantity_price_total_and_exact_evidence():
    f = fragment(
        "DESCRIPCION CANT VALOR TOTAL VALOR TOTAL\n"
        "TELEVISOR 65 PULGADAS LED UHD4K SMART TV + BASE GIRATORIA\n"
        "1 3.970.000 3.970.000\n"
    )
    facts = extract_tv_research_facts(uuid.uuid4(), [f], RESEARCH_TV_RULE_VERSION)
    items = [x for x in facts if x.fact_type == "purchase_item"]
    assert len(items) == 1
    assert items[0].normalized_value["unit_price_cop"] == "3970000"
    assert items[0].normalized_value["quantity"] == "1"
    assert items[0].confidence == Decimal("0.6")
    assert items[0].rule_name == "tv_row_price_requires_review"
    assert items[0].source_locator["sources"][0]["locator"]["page_number"] == 1
    assert items[0].source_locator["sources"][0]["content_fragment_id"] == str(f.id)
    assert "DESCRIPCION" not in items[0].evidence_text
    # Radar's existing default rule set is unchanged and doesn't accept this layout.
    assert not any(x.fact_type == "purchase_item" for x in extract_facts(uuid.uuid4(), [f]))


@pytest.mark.parametrize(
    "row",
    [
        "TELEVISOR 65 pulgadas 2 3.970.000 3.970.000",
        "SOPORTE PARA TELEVISOR 65 pulgadas 1 100.000 100.000",
        "TELEVISOR 65 pulgadas presupuesto 29.000.000",
    ],
)
def test_ambiguous_or_inconsistent_rows_do_not_become_research_items(row):
    f = fragment("DESCRIPCION CANT VALOR TOTAL VALOR TOTAL\n" + row)
    facts = extract_tv_research_facts(uuid.uuid4(), [f], RESEARCH_TV_RULE_VERSION)
    assert not any(x.fact_type == "purchase_item" for x in facts)


def test_without_table_header_there_is_no_price_row():
    f = fragment("TELEVISOR 65 pulgadas 1 3.970.000 3.970.000")
    assert not any(
        x.fact_type == "purchase_item"
        for x in extract_tv_research_facts(uuid.uuid4(), [f], RESEARCH_TV_RULE_VERSION)
    )


def test_explicit_abbreviated_unit_column_is_not_treated_as_ambiguous():
    f = fragment(
        "ITEM DESCRIPCION PRODUCTO/SERVICIO CANT VALOR UNIT VALOR TOTAL\n"
        "4 TELEVISOR SMART TV 55” 2 2.610.000 5.220.000"
    )
    facts = extract_tv_research_facts(uuid.uuid4(), [f], RESEARCH_TV_RULE_VERSION)
    item = next(x for x in facts if x.fact_type == "purchase_item")
    assert item.rule_name == "tv_row_price_explicit"
    assert item.normalized_value["quantity"] == "2"
    assert item.normalized_value["unit_price_cop"] == "2610000"


def test_estimated_price_columns_do_not_become_confirmed_unit_prices():
    f = fragment(
        "DESCRIPCION CANT PRECIO UNITARIO ESTIMADO PRECIO TOTAL\n"
        "TELEVISOR 55 pulgadas 2 100.000 200.000"
    )
    facts = extract_tv_research_facts(uuid.uuid4(), [f], RESEARCH_TV_RULE_VERSION)
    items = [
        x for x in facts if x.fact_type == "purchase_item" and x.rule_name.startswith("tv_row")
    ]
    assert all(x.rule_name == "tv_row_price_requires_review" for x in items)
