import uuid
from decimal import Decimal

import pytest

from public_procurement.extraction.domain.content import EvidenceFragment
from public_procurement.extraction.structured_rules import extract_facts
from public_procurement.extraction.structured_tables import parse_cop


def fragment(text, locator=None, ordinal=1, version=None, run=None):
    return EvidenceFragment(
        uuid.uuid4(),
        version or uuid.uuid4(),
        run or uuid.uuid4(),
        "example.pdf",
        ordinal,
        text,
        locator or {"kind": "pdf_page", "page_number": 3},
    )


def facts(text):
    return extract_facts(uuid.uuid4(), [fragment(text)])


def of_type(results, kind):
    return [fact for fact in results if fact.fact_type == kind]


def test_multiple_products_presentations_and_exact_unicode_evidence():
    source = fragment(
        "JUGO HIT X 200 ml + Chocorramo tradicional X 65 g; 1 litro; 1 kg; 20 UNIDADES"
    )
    results = extract_facts(uuid.uuid4(), [source])
    products = of_type(results, "product")
    assert [p.normalized_value for p in products] == [
        {"name": "jugo hit", "presentation": "200", "unit": "ml"},
        {"name": "chocorramo tradicional", "presentation": "65", "unit": "g"},
    ]
    assert {(p.numeric_value, p.unit) for p in of_type(results, "presentation")} >= {
        (Decimal(200), "ml"),
        (Decimal(65), "g"),
        (Decimal(1), "l"),
        (Decimal(1), "kg"),
    }
    for fact in results:
        evidence = fact.source_locator["sources"][0]
        assert fact.content_fragment_id == source.id
        assert (
            evidence["text"]
            == source.text[evidence["fragment_char_start"] : evidence["fragment_char_end"]]
        )
        assert fact.evidence_text == evidence["text"]


@pytest.mark.parametrize("text", ["400 PACK", "20 UNIDADES", "10 CAJAS", "2 PAQUETES"])
def test_quantities_with_explicit_units(text):
    quantity = of_type(facts(text), "quantity")[0]
    assert quantity.numeric_value == Decimal(text.split()[0])
    assert quantity.confidence == Decimal("1.0")


@pytest.mark.parametrize("text", ["5.200", "$ 5.200", "2.080.000", "$ 2\u2019080.000,oo"])
def test_cop_grouping(text):
    assert parse_cop(text) == Decimal(5200 if "5.200" in text else 2080000)


def test_plain_numbers_have_no_financial_or_legal_meaning():
    results = facts(
        "Nit 80013849. Teléfono 5200. Fecha 2026. 2.080.000. RUP. Experiencia. Garantías."
    )
    assert not results
    assert parse_cop("XXXXX") is None
    assert parse_cop("2.08.000") is None


def test_labelled_values_unspsc_and_budget():
    results = facts(
        "UNSPSC: 50192703. Valor unitario: $ 5.200. Valor total: 2.080.000. "
        "Presupuesto oficial estimado: $ 2\u2019080.000,oo"
    )
    assert of_type(results, "unspsc")[0].string_value == "50192703"
    assert of_type(results, "unit_price_cop")[0].numeric_value == Decimal(5200)
    assert of_type(results, "total_cop")[0].numeric_value == Decimal(2080000)
    assert all(f.numeric_value == Decimal(2080000) for f in of_type(results, "official_budget_cop"))


def test_deadlines_distinguish_payment_from_invoice_submission_and_approval():
    results = facts(
        "PLAZO DE EJECUCIÓN: cinco (05) días calendario. "
        "Enviar factura dentro de 5 días hábiles. Revisar dentro de 10 días hábiles. "
        "La entidad deberá pagar la factura dentro de los 30 días calendario "
        "siguientes a su fecha de aprobación."
    )
    assert [f.numeric_value for f in of_type(results, "execution_term")] == [Decimal(5)]
    term = of_type(results, "payment_term")
    assert len(term) == 1
    assert term[0].numeric_value == Decimal(30)
    assert "aprobación" in term[0].normalized_value["trigger"]
    assert not of_type(facts("Plazo de ejecución: cinco (10) días calendario."), "execution_term")


def test_payment_percent_and_no_delivery_count_inference():
    results = facts("Pago único del 100 % del valor total del contrato, contra entrega.")
    assert of_type(results, "payment_method")[0].normalized_value["mode"] == "single_payment"
    assert of_type(results, "payment_percentage")[0].numeric_value == Decimal(100)
    assert not of_type(results, "delivery_count")
    assert (
        of_type(facts("Se realizarán entregas parciales."), "delivery_count")[0].string_value
        == "multiple"
    )


@pytest.mark.parametrize(
    ("text", "kind", "value"),
    [
        ("No se requiere ningún tipo de póliza", "guarantee", "not_required"),
        ("Se requiere garantía", "guarantee", "required"),
        ("No se requiere garantía de cumplimiento", "guarantee", "not_required"),
        ("Garantía de cumplimiento", "guarantee", "required"),
        ("No se exige RUP", "rup", "not_required"),
        ("Se requiere el RUP", "rup", "required"),
        ("Deberá acreditar experiencia contractual", "experience", "required"),
        ("No se requiere experiencia previa", "experience", "not_required"),
    ],
)
def test_explicit_requirements(text, kind, value):
    results = of_type(facts(text), kind)
    assert results
    assert all(result.string_value == value for result in results)


def test_guarantee_policy_and_product_obligations_remain_separate():
    results = facts(
        "No se requiere póliza, pero se debe anexar documentación, "
        "anexando certificado de garantía y reemplazar los productos que salgan defectuosos."
    )
    guarantee = of_type(results, "guarantee")
    assert len(guarantee) == 1
    assert guarantee[0].source_locator["subject"] == "policy"
    assert len(of_type(results, "operational_observation")) == 2
    assert not of_type(facts("Si se requiere garantía, se notificará."), "guarantee")


def table_fragments(xlsx=False):
    version, run = uuid.uuid4(), uuid.uuid4()
    rows = [
        ["ITEM", "DESCRIPCIÓN", "CANTIDAD", "UNIDAD DE MEDIDA", "VALOR UNITARIO", "VALOR TOTAL"],
        ["1", "Jugo Acme X 250 ml + Galleta Beta X 65 g", "20", "CAJAS", "$ 5.200", "104.000"],
    ]
    return [
        fragment(
            value,
            {"kind": "xlsx_cell", "sheet_name": "Oferta", "cell_range": f"{chr(64 + column)}{row}"}
            if xlsx
            else {
                "kind": "docx_table_cell",
                "table_number": 1,
                "row_number": row,
                "column_number": column,
            },
            (row - 1) * 6 + column,
            version,
            run,
        )
        for row, values in enumerate(rows, 1)
        for column, value in enumerate(values, 1)
    ]


@pytest.mark.parametrize("xlsx", [False, True])
def test_table_headers_reconstruct_items_and_link_multiple_products(xlsx):
    sources = table_fragments(xlsx)
    results = extract_facts(uuid.uuid4(), sources)
    item = of_type(results, "purchase_item")[0]
    assert item.normalized_value["quantity"] == "20"
    assert item.normalized_value["unit"] == "CAJA"
    assert item.normalized_value["unit_price_cop"] == "5200"
    assert item.normalized_value["total_cop"] == "104000"
    assert item.content_fragment_id is None
    assert len(item.source_locator["sources"]) == 12
    assert len(of_type(results, "product")) == 2
    assert all(
        p.source_locator["group_key"] == item.source_locator["group_key"]
        for p in of_type(results, "product")
    )


def test_pdf_table_header_required_and_placeholder_prices_not_invented():
    text = "ITEM DESCRIPCION DEL BIEN O SERVICIO CANT UNIDAD DE MEDIDA VALOR UNITARIO VALOR TOTAL "
    row = "1 Refrigerios PACK (Jugo Acme X 200 ml) 400 PACK 5.200 2.080.000 TOTAL 2.080.000"
    item = of_type(facts(text + row), "purchase_item")[0]
    assert item.normalized_value["unit_price_cop"] == "5200"
    assert item.normalized_value["total_cop"] == "2080000"
    assert not of_type(facts(row), "purchase_item")
    blank = of_type(facts(text + row.replace("5.200 2.080.000", "XXXXX XXXXXX")), "purchase_item")[
        0
    ]
    assert blank.normalized_value["unit_price_cop"] is None
    assert blank.normalized_value["total_cop"] is None


def test_same_row_numbers_in_different_documents_cannot_combine():
    sources = table_fragments()
    sources[8] = fragment("20", sources[8].source_locator, sources[8].ordinal)
    assert not of_type(extract_facts(uuid.uuid4(), sources), "purchase_item")


def test_case_accents_and_decomposed_original_are_preserved():
    original = "PLAZO DE EJECUCIO\u0301N: 10 di\u0301as hábiles"
    term = of_type(facts(original), "execution_term")[0]
    assert term.evidence_text == original
    assert term.unit == "días hábiles"


def test_malformed_price_and_guarantee_percentage_are_not_payment_facts():
    results = facts("Valor unitario: 2.08.000. Garantía por 100 % del valor del contrato.")
    assert not of_type(results, "unit_price_cop")
    assert not of_type(results, "payment_percentage")


def test_duplicate_rule_paths_do_not_duplicate_the_same_budget_evidence():
    assert len(of_type(facts("Presupuesto oficial: $ 2.080.000"), "official_budget_cop")) == 1


def test_adjacent_heading_and_paragraph_keep_both_sources_and_lower_confidence():
    version, run = uuid.uuid4(), uuid.uuid4()
    heading = fragment(
        "Plazo de ejecución:", {"kind": "docx_paragraph", "paragraph_number": 1}, 1, version, run
    )
    value = fragment(
        "10 días hábiles", {"kind": "docx_paragraph", "paragraph_number": 2}, 2, version, run
    )
    result = of_type(extract_facts(uuid.uuid4(), [heading, value]), "execution_term")[0]
    assert result.numeric_value == Decimal(10)
    assert result.confidence == Decimal("0.6")
    assert result.content_fragment_id is None
    assert [source["content_fragment_id"] for source in result.source_locator["sources"]] == [
        str(heading.id),
        str(value.id),
    ]


def test_payment_context_does_not_turn_invoice_submission_into_payment_deadline():
    assert not of_type(
        facts("Trámite de pago: enviar la factura dentro de 5 días hábiles."), "payment_term"
    )


def test_negation_does_not_leak_between_requirements_and_counts_are_not_sizes():
    results = facts("No se exige RUP. Se requiere garantía. 20 UNIDADES")
    assert of_type(results, "rup")[0].string_value == "not_required"
    assert of_type(results, "guarantee")[0].string_value == "required"
    assert not of_type(results, "presentation")
