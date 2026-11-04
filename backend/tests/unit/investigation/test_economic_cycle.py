from copy import deepcopy
from decimal import Decimal

import pytest

from public_procurement.investigation.economic_cycle import (
    build_cycles,
    classify_stage,
    derive_unit_price,
    extract_rows,
    match_item,
    reconstruct,
    verified_documents,
)


def fragment(name="ESTUDIOS PREVIOS.pdf", text=None, identifier="f"):
    return {
        "id": identifier,
        "document_version_id": "v-" + identifier,
        "original_name": name,
        "text": text
        or (
            "Descripcion Cantidad Valor Unitario Valor Total\n"
            "1 Televisor LG 55 pulgadas LED 4K Smart TV UNIDAD 5 960.861 4.804.305"
        ),
        "source_locator": {
            "page_number": 3,
            "input_sha256": identifier,
            "extraction_method": "native_pdf_text",
        },
    }


def process(**changes):
    return {
        "id": "CO1.REQ.123456",
        "reference": "MC-001-2026",
        "entity": "Entidad A",
        "published_at": "2026-10-15",
        "contracts": [],
        "documents": [],
        "tv_confirmed": True,
        "products": [],
        **changes,
    }


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("ESTUDIOS PREVIOS.pdf", "studies_previous"),
        ("INVITACION.pdf", "invitation"),
        ("ANEXO TECNICO.pdf", "technical_specification"),
        ("OFERTA ECONOMICA.pdf", "economic_offer"),
        ("EVALUACION OFERTA.pdf", "evaluation_report"),
        ("ACEPTACION DE OFERTA.pdf", "award"),
        ("CONTRATO.pdf", "contract"),
        ("OTROSI.pdf", "amendment"),
        ("desconocido.pdf", "unknown"),
    ],
)
def test_stage_classification(name, expected):
    assert classify_stage(name)[0] == expected


def test_reference_phone_example_arithmetic_without_process_hardcoding():
    row = extract_rows(
        fragment(
            text="Descripcion Cantidad Valor Unitario Valor Total\n"
            "1 Celular Xiaomi Redmi 15C UNIDAD 5 960.861 4.804.305"
        )
    )[0]
    assert row["brand"] == "XIAOMI"
    assert row["model"] == "REDMI 15C"
    total, qty = row["fields"]["budget_total"], row["fields"]["quantity"]
    calculated = derive_unit_price(total, qty, single_item_scope=True)
    assert Decimal(calculated["value"]) == Decimal("960861")
    assert calculated["value_origin"] == "calculated"
    assert len(calculated["calculation_inputs"]) == 2
    assert row["fields"]["budget_unit_price"]["value_origin"] == "explicit"
    assert calculated["evidence"][0]["source_page"] == 3


@pytest.mark.parametrize(("single", "conflicts"), [(False, False), (True, True)])
def test_no_division_of_bundle_or_conflict(single, conflicts):
    row = extract_rows(fragment())[0]
    assert (
        derive_unit_price(
            row["fields"]["budget_total"],
            row["fields"]["quantity"],
            single_item_scope=single,
            conflicts=conflicts,
        )
        is None
    )


def test_total_only_row_derives_price_with_two_provenances():
    row = extract_rows(
        fragment(
            text="Descripcion Cantidad Valor Total\n"
            "1 Televisor LG 55 pulgadas LED 4K Smart TV UNIDAD 5 4.804.305"
        )
    )[0]
    result = reconstruct(process(), [row], [])
    item = result["products"][0]
    assert Decimal(item["budget_unit_price"]) == Decimal("960861")
    alternative = item["fields"]["budget_unit_price"]["alternatives"][0]
    assert alternative["value_origin"] == "calculated"
    assert len(alternative["calculation_inputs"]) == 2
    assert item["purchase_price"] is None


def test_stage_evidence_complements_without_promoting_budget():
    budget = extract_rows(fragment())[0]
    offer = extract_rows(fragment("OFERTA ECONOMICA.pdf", identifier="offer"))[0]
    item = reconstruct(process(), [budget, offer], [])["products"][0]
    assert item["budget_unit_price"] == "960861"
    assert item["offer_unit_price"] == "960861"
    assert item["contract_unit_price"] is None
    assert len(item["links"]) == 1
    assert item["purchase_price"] is None
    concepts = {c["canonical_type"] for c in item["canonical_projection"]}
    assert {"PURCHASE_ITEM", "QUANTITY", "UNIT_PRICE_COP", "TOTAL_COP", "BUDGET_COP"} <= concepts


def test_complementary_specifications_keep_types_and_document_provenance():
    budget = extract_rows(fragment())[0]
    contract = extract_rows(fragment("CONTRATO.pdf", identifier="contract"))[0]
    budget["specifications"]["smart"] = None
    contract["specifications"]["panel"] = None
    contract["item_description"] += " profesional business"
    item = reconstruct(process(), [budget, contract], [])["products"][0]
    assert item["specifications"]["smart"] is True
    assert item["specifications"]["screen_size_inches"] == 55
    assert item["specifications"]["panel"] == "LED"
    assert item["other_specifications"]["professional_display"] is True
    evidence = item["specification_evidence"]["smart"]
    assert len(evidence) == 1
    assert evidence[0]["evidence"][0]["fragment_id"] == "contract"


def test_quantity_conflict_preserves_both_and_blocks_calculation():
    first = extract_rows(fragment())[0]
    second = deepcopy(first)
    second["id"] = "different"
    second["fields"]["quantity"]["value"] = "6"
    result = reconstruct(process(), [first, second], [])["products"][0]
    assert result["quantity"] is None
    assert result["fields"]["quantity"]["status"] == "conflicting"
    assert len(result["fields"]["quantity"]["alternatives"]) == 2
    assert result["purchase_price"] is None


def test_evaluation_recommendation_is_not_adjudication():
    row = extract_rows(fragment("INFORME EVALUACION.pdf", identifier="evaluation"))[0]
    item = reconstruct(process(), [row], [])["products"][0]
    assert item["evaluated_offer_unit_price"] == "960861"
    assert item["offer_unit_price"] is None
    assert item["awarded_unit_price"] is None
    assert "evaluation_is_not_award" in item["notes"]
    assert item["purchase_price"] is None


def test_signed_contract_explicit_item_can_be_purchase_price():
    f = fragment("CONTRATO.pdf", identifier="contract")
    f["text"] = "MC-001-2026\n" + f["text"]
    p = process(
        contracts=[{"id_contrato": "CO1.PCCNTR.123456", "fecha_de_firma": "2026-10-16"}],
        documents=[
            {
                "name": "CONTRATO.pdf",
                "selected": True,
                "downloaded": True,
                "extraction_status": "completed",
                "coverage_complete": True,
            }
        ],
    )
    cycle = build_cycles({"processes": [p]}, {p["id"]: [f]})
    item = cycle["processes"][0]["products"][0]
    assert item["purchase_price"]["column"] == "contract_unit_price"
    assert cycle["summary"]["verified_purchase_unit_prices"] == 1


def test_document_reference_cannot_be_borrowed_from_another_contract_document():
    p = process(contracts=[{"id_contrato": "CO1.PCCNTR.123456", "fecha_de_firma": "2026-10-16"}])
    correct = fragment("CONTRATO VIGENTE.pdf", "MC-001-2026", "correct")
    unrelated = fragment("CONTRATO ANTERIOR.pdf", "MC-002-2025", "old")
    assert verified_documents(p, [correct, unrelated], "contract") == ["CONTRATO VIGENTE.pdf"]


def test_partial_contract_does_not_become_purchase_price():
    row = extract_rows(fragment("CONTRATO.pdf"), complete=False)[0]
    p = process(verified_contract_documents=["CONTRATO.pdf"])
    item = reconstruct(p, [row], [])["products"][0]
    assert item["contract_unit_price"] == "960861"
    assert item["purchase_price"] is None
    assert item["requires_manual_review"] is True


def test_same_size_only_is_not_enough_for_cross_stage_join():
    row = extract_rows(fragment())[0]
    other = deepcopy(row)
    row["item_number"] = other["item_number"] = None
    other["item_description"] = "TV 55 pulgadas para una sala distinta"
    other["brand"] = None
    other["specifications"] = {
        "screen_size_inches": 55,
        "resolution": None,
        "panel": None,
        "smart": None,
    }
    assert match_item(row, other) is None


def test_contact_phone_and_mount_are_not_products():
    assert not extract_rows(fragment(text="CELULAR: 3101234567\ncontacto@example.com"))
    assert not extract_rows(
        fragment(text="TELEVISOR Y REPRODUCTOR DE VIDEO, SOPORTE DE 19 A 40 PULGADAS")
    )


def test_metadata_global_contract_value_never_allocated_to_tv():
    row = extract_rows(
        fragment(text="Descripcion Cantidad\n1 Televisor LG 55 pulgadas LED 4K Smart TV UNIDAD 5")
    )[0]
    p = process(contracts=[{"valor_del_contrato": "4804305", "fecha_de_firma": "2026-10-16"}])
    cycle = reconstruct(p, [row], [])
    assert cycle["process_global_contracts"][0]["total"] == "4804305"
    assert cycle["products"][0]["contract_unit_price"] is None


def test_idempotent_projection_and_whitespace_invariant_matching():
    row = extract_rows(fragment())[0]
    other = deepcopy(row)
    other["item_description"] = other["item_description"].replace(" ", "\n ")
    assert match_item(row, other)
    assert reconstruct(process(), [row, row], []) == reconstruct(process(), [row], [])


def test_explicit_offer_acceptance_needs_reference_supplier_and_quantity():
    offer = extract_rows(fragment("OFERTA ECONOMICA.pdf", identifier="offer"))[0]
    offer.update(explicit_offer_reference="ABC-123", bidder="Proveedor A")
    acceptance = extract_rows(fragment("ACEPTACION DE OFERTA.pdf", identifier="award"))[0]
    acceptance.update(
        explicit_offer_reference="ABC-123", bidder="Proveedor A", acceptance_explicit=True
    )
    acceptance["fields"].pop("awarded_unit_price")
    acceptance["fields"].pop("awarded_total")
    p = process(verified_award_documents=["ACEPTACION DE OFERTA.pdf"])
    item = reconstruct(p, [offer, acceptance], [])["products"][0]
    assert item["purchase_price"]["column"] == "accepted_offer_unit_price"
    assert item["purchase_price"]["evidence"][0]["acceptance_evidence"]
    acceptance["bidder"] = "Otro proveedor"
    item = reconstruct(p, [offer, acceptance], [])["products"][0]
    assert item["purchase_price"] is None


def test_contract_price_has_priority_and_both_stage_values_are_preserved():
    contract = extract_rows(fragment("CONTRATO.pdf", identifier="contract"))[0]
    award = extract_rows(fragment("ACEPTACION DE OFERTA.pdf", identifier="award"))[0]
    p = process(
        verified_contract_documents=["CONTRATO.pdf"],
        verified_award_documents=["ACEPTACION DE OFERTA.pdf"],
    )
    item = reconstruct(p, [award, contract], [])["products"][0]
    assert item["purchase_price"]["column"] == "contract_unit_price"
    assert item["awarded_unit_price"] == item["contract_unit_price"] == "960861"


def test_unsupported_evaluation_reference_to_past_contract_not_current_product():
    f = fragment("EVALUACION.pdf")
    f["text"] = "Certificado de experiencia contractual\n" + f["text"]
    assert extract_rows(f) == []


def test_no_merge_of_conflicting_model_without_proven_item_position():
    first = extract_rows(fragment())[0]
    other = deepcopy(first)
    first.update(item_number=None, model="ABC-123")
    other.update(item_number=None, model="XYZ-987")
    assert match_item(first, other) is None


def test_shared_item_position_preserves_model_conflict():
    first = extract_rows(fragment())[0]
    other = deepcopy(first)
    first["model"] = "ABC-123"
    other.update(id="other", model="XYZ-987")
    item = reconstruct(process(), [first, other], [])["products"][0]
    assert item["model"] is None
    assert "model" in item["conflicts"]


def test_offer_prices_from_different_suppliers_remain_alternatives():
    first = extract_rows(fragment("OFERTA ECONOMICA.pdf"))[0]
    other = deepcopy(first)
    first["bidder"] = "Proveedor A"
    other.update(id="other", bidder="Proveedor B", offer_reference="other")
    other["fields"]["offer_unit_price"]["value"] = "1000000"
    other["fields"]["offer_total"]["value"] = "5000000"
    item = reconstruct(process(), [first, other], [])["products"][0]
    assert item["offer_unit_price"] is None
    assert item["fields"]["offer_unit_price"]["status"] == "uncertain"
    assert len(item["fields"]["offer_unit_price"]["alternatives"]) == 2
    assert item["purchase_price"] is None


def test_secop_estimated_and_actual_columns_are_not_confused():
    row = extract_rows(
        fragment(
            "CONTRATO.pdf",
            text=(
                "Descripcion Cantidad Unidad Precio unitario estimado "
                "Precio unitario Precio total estimado\n"
                "1\n52161505\nTELEVISOR 75 PULGADAS PROFESIONAL TIPO BUSINESS\n3,00\nUN\n"
                "8.500.000,00\n5.850.000,00\n25.500.000,00\n17.550.000,00\n"
                "2\n45111701\nCONSOLA DE SONIDO\n3,00\nUN\n7.000.000,00\n6.500.000,00"
            ),
        )
    )[0]
    assert row["fields"]["contract_unit_price"]["value"] == "5850000"
    assert row["fields"]["contract_total"]["value"] == "17550000"
    assert row["fields"]["budget_unit_price"]["value"] == "8500000"
    assert row["fields"]["budget_total"]["value"] == "25500000"
    assert row["fields"]["quantity"]["value"] == "3"


def test_decimal_formatting_does_not_create_quantity_conflict():
    first = extract_rows(fragment())[0]
    second = extract_rows(
        fragment(identifier="second", text=fragment()["text"].replace("UNIDAD 5", "5,00 UN"))
    )[0]
    item = reconstruct(process(), [first, second], [])["products"][0]
    assert item["quantity"] == "5"
    assert "quantity" not in item["conflicts"]


def test_continued_quantity_table_retains_header_provenance():
    f = fragment(
        "CONTRATO.pdf", "5 Televisor 58 pulgadas 4K Smart TV\n1\nNotas adicionales: sin precio"
    )
    header = {"source_page": 4, "evidence_text": "Descripción Unidad Cantidad"}
    row = extract_rows(f, quantity_header=header)[0]
    assert row["fields"]["quantity"]["value"] == "1"
    assert row["fields"]["quantity"]["evidence"][0]["quantity_header_evidence"] == header


def test_missing_quantity_does_not_produce_inferred_row_from_narrative():
    assert (
        extract_rows(fragment(text="Televisor 55 pulgadas 4K Smart TV disponible para uso")) == []
    )


def test_budget_conflict_kept_while_explicit_later_contract_price_is_retained():
    first = extract_rows(fragment())[0]
    second = deepcopy(first)
    second["id"] = "another-budget"
    second["fields"]["budget_total"]["value"] = "5000000"
    second["fields"]["budget_unit_price"]["value"] = "1000000"
    contract = extract_rows(fragment("CONTRATO.pdf", identifier="contract"))[0]
    p = process(verified_contract_documents=["CONTRATO.pdf"])
    item = reconstruct(p, [first, second, contract], [])["products"][0]
    assert item["budget_unit_price"] is None
    assert item["contract_unit_price"] == "960861"
    assert item["purchase_price"]["column"] == "contract_unit_price"
    assert item["requires_manual_review"] is True
    assert "budget_unit_price" in item["conflicts"]


def test_different_award_and_contract_values_are_not_silently_resolved():
    award = extract_rows(fragment("ACEPTACION DE OFERTA.pdf", identifier="award"))[0]
    contract = extract_rows(fragment("CONTRATO.pdf", identifier="contract"))[0]
    contract["fields"]["contract_total"]["value"] = "5000000"
    contract["fields"]["contract_unit_price"]["value"] = "1000000"
    p = process(
        verified_contract_documents=["CONTRATO.pdf"],
        verified_award_documents=["ACEPTACION DE OFERTA.pdf"],
    )
    item = reconstruct(p, [award, contract], [])["products"][0]
    assert "award_contract_unit_price_disagreement" in item["conflicts"]
    assert item["purchase_price"] is None


def test_cross_page_quantity_and_total_keep_both_provenances():
    qty = extract_rows(
        fragment(
            "CONTRATO.pdf",
            text=("Descripcion Cantidad\n1 Televisor LG 55 pulgadas LED 4K Smart TV UNIDAD 5"),
            identifier="qty",
        )
    )[0]
    total = extract_rows(
        fragment(
            "CONTRATO.pdf",
            text=("Descripcion Valor Total\n1 Televisor LG 55 pulgadas LED 4K Smart TV 4.804.305"),
            identifier="total",
        )
    )[0]
    p = process(verified_contract_documents=["CONTRATO.pdf"])
    item = reconstruct(p, [qty, total], [])["products"][0]
    assert Decimal(item["contract_unit_price"]) == Decimal("960861")
    a = item["fields"]["contract_unit_price"]["alternatives"][0]
    assert a["value_origin"] == "calculated"
    assert {e["fragment_id"] for e in a["evidence"]} == {"qty", "total"}


def test_requested_quantity_cannot_be_assumed_to_be_final_contract_quantity():
    qty = extract_rows(fragment())[0]
    total = extract_rows(
        fragment(
            "CONTRATO.pdf",
            text=("Descripcion Valor Total\n1 Televisor LG 55 pulgadas LED 4K Smart TV 4.804.305"),
            identifier="total",
        )
    )[0]
    item = reconstruct(process(), [qty, total], [])["products"][0]
    assert item["contract_total"] == "4804305"
    assert item["contract_unit_price"] is None


def test_ocr_joined_name_of_next_item_does_not_pollute_tv_price_row():
    f = fragment(
        "COTIZACION.pdf",
        text=(
            "Televisor Samsung 50 pulgadas Smart TV 4K UHD | 5 | 2.071.000 10.355.000\n"
            "Kitrobotica con control IQ 1 2.456.300 2.456.300"
        ),
    )
    row = extract_rows(f)[0]
    assert row["fields"]["quantity"]["value"] == "5"
    assert row["fields"]["offer_unit_price"]["value"] == "2071000"
    assert row["fields"]["offer_total"]["value"] == "10355000"


def test_two_incompatible_brands_in_row_preserve_both_alternatives():
    f = fragment(
        "COTIZACION.pdf",
        text=(
            "Descripcion Cantidad Valor Unitario Valor Total\n"
            "1 Televisor LG Samsung 55 pulgadas Smart TV UNIDAD 5 960.861 4.804.305"
        ),
    )
    row = extract_rows(f)[0]
    item = reconstruct(process(), [row], [])["products"][0]
    assert item["brand"] is None
    assert item["fields"]["brand"]["status"] == "conflicting"
    assert {a["value"] for a in item["fields"]["brand"]["alternatives"]} == {"LG", "SAMSUNG"}
    assert item["requires_manual_review"] is True


def test_unspsc_prefix_and_ocr_product_typo_preserve_distinct_item_rows():
    f = fragment(
        "CONTRATO.pdf",
        text=(
            "ITEM UNSPSC DESCRIPCION CANTIDAD UNIDAD VALOR UNITARIO VALOR TOTAL\n"
            "2 52161505 TELEVISOR 70 PULGADAS 50XY9999ZZ 4K QLED SMART TV "
            "1 UNIDAD 2.553.400 2.553.400\n"
            "3 52161505 TELEVISORE 55 PULGADAS 55XY9999ZZ 4K SMART TV "
            "4 UNIDAD 2.412.750 9.651.000\n"
            "4 45111616 VIDEOPROYECTOR 1 UNIDAD 2.468.600 2.468.600"
        ),
    )
    rows = extract_rows(f)
    assert len(rows) == 2
    assert rows[1]["fields"]["contract_unit_price"]["value"] == "2412750"
    assert rows[1]["model"] == "55XY9999ZZ"


def test_quotation_embedded_in_contract_is_not_a_contractual_price():
    f = fragment(
        "CONTRATO.pdf",
        text=(
            "ASUNTO: COTIZACION 255\n"
            "Descripcion Cantidad Valor Unitario Valor Total\n"
            "1 Televisor LG 55 pulgadas LED 4K Smart TV UNIDAD 5 960.861 4.804.305"
        ),
    )
    row = extract_rows(f)[0]
    assert row["source_stage"] == "economic_offer"
    assert "contract_unit_price" not in row["fields"]
    assert row["fields"]["offer_unit_price"]["value"] == "960861"


def test_selected_offer_filename_alone_is_not_proof_of_adjudication():
    assert classify_stage("OFERTA SELECCIONADA MC-001.pdf")[0] == "economic_offer"


def test_same_model_reference_for_two_sizes_is_preserved_as_critical_conflict():
    one = extract_rows(
        fragment(
            "CONTRATO.pdf",
            text=(
                "Descripcion Cantidad Valor Unitario Valor Total\n"
                "1 Televisor LG 55 pulgadas modelo 55XY9999ZZ LED 4K Smart TV "
                "UNIDAD 5 960.861 4.804.305"
            ),
        )
    )[0]
    two = deepcopy(one)
    two.update(id="other", item_number="2")
    two["specifications"]["screen_size_inches"] = 70
    items = reconstruct(process(verified_contract_documents=["CONTRATO.pdf"]), [one, two], [])[
        "products"
    ]
    assert len(items) == 2
    assert all("model_reused_for_incompatible_sizes" in i["conflicts"] for i in items)
    assert all(i["purchase_price"] is None for i in items)


def test_reference_not_borrowed_from_different_version_with_same_filename():
    p = process(contracts=[{"id_contrato": "CO1.PCCNTR.123456", "fecha_de_firma": "2026-10-16"}])
    current = fragment("CONTRATO.pdf", "MC-001-2026", "current")
    unrelated = fragment("CONTRATO.pdf", "MC-002-2025", "unrelated")
    assert verified_documents(p, [current, unrelated], "contract", return_versions=True) == [
        "v-current"
    ]
