from copy import deepcopy

import pytest

from public_procurement.investigation.comparison_readiness import (
    build_readiness,
    documentary_award_winners,
    economic_document_priority,
    technical_scope,
)


def cycle_fixture():
    evidence = {
        "source_document": "CONTRATO.pdf",
        "source_page": 3,
        "fragment_id": "f",
        "document_version_id": "v",
        "input_sha256": "sha",
        "extraction_method": "native_pdf_text",
        "evidence_text": "TV 55 pulgadas, 2 UN",
    }
    item = {
        "id": "A",
        "normalized_product": "televisor",
        "item_description": "Televisor LG 55 pulgadas LED 4K Smart modelo 55ABC",
        "brand": "LG",
        "model": "55ABC",
        "specifications": {
            "screen_size_inches": 55,
            "panel": "LED",
            "resolution": "4k",
            "smart": True,
        },
        "quantity": "2",
        "unit": "UNIDAD",
        "contract_unit_price": "100",
        "awarded_unit_price": None,
        "offer_unit_price": "90",
        "purchase_date": "2026-10-20",
        "purchase_price": {
            "column": "contract_unit_price",
            "value": "100",
            "origin": "explicit",
            "evidence": [{"value": "100", "value_origin": "explicit", "evidence": [evidence]}],
        },
        "observations": [{"id": "obs", "vat_basis": "included", "evidence": [evidence]}],
        "conflicts": [],
        "other_specifications": {},
    }
    processes = [
        {
            "process_identity": "REQ-A",
            "process_code": "MC-A",
            "products": [item],
            "process_global_contracts": [{"supplier": "Proveedor A", "total": "200"}],
            "document_coverage": [{"downloaded": True, "stage": "contract"}],
        },
    ]
    second = deepcopy(processes[0])
    second.update(process_identity="REQ-B", process_code="MC-B")
    second["products"][0]["id"] = "B"
    second["products"][0]["contract_unit_price"] = "102"
    second["products"][0]["purchase_price"]["value"] = "102"
    second["products"][0]["purchase_price"]["evidence"][0]["value"] = "102"
    processes.append(second)
    return {
        "processes": processes,
        "comparisons": [
            {
                "id": "pair",
                "processes": ["REQ-A", "REQ-B"],
                "entities": ["Entidad A", "Entidad B"],
                "observation_ids": ["A", "B"],
                "comparability_level": "exact",
            }
        ],
    }


def run(cycle):
    return build_readiness(cycle, window_start="2026-09-04", window_before="2026-11-03")


def test_frozen_scope_excludes_partial_pairs_and_unrelated_processes():
    cycle = cycle_fixture()
    cycle["comparisons"].append(
        {"comparability_level": "partial", "processes": ["X", "Y"], "observation_ids": ["x", "y"]}
    )
    assert technical_scope(cycle)["process_identities"] == ["REQ-A", "REQ-B"]
    assert len(run(cycle)["pairs"]) == 1


def test_signed_contract_acceptance_award_evaluation_offer_review_order():
    docs = [
        ("OFERTA ECONOMICA.pdf", "economic_offer"),
        ("RESOLUCION ADJUDICACION.pdf", "award"),
        ("CO1_PCCNTR_Firmado.pdf", "contract"),
        ("COMUNICADO ACEPTACION DE OFERTA.pdf", "award"),
        ("INFORME EVALUACION.pdf", "evaluation_report"),
    ]
    ordered = sorted(docs, key=lambda d: economic_document_priority(*d))
    assert [d[1] for d in ordered] == [
        "contract",
        "award",
        "award",
        "evaluation_report",
        "economic_offer",
    ]
    assert ordered[1][0] == "COMUNICADO ACEPTACION DE OFERTA.pdf"


def test_ready_pair_emits_only_public_price_difference_without_threshold():
    result = run(cycle_fixture())
    assert result["pairs"][0]["status"] == "ready"
    assert result["signals"][0]["type"] == "PUBLIC_PRICE_DIFFERENCE"
    assert result["signals"][0]["difference_pct"] == "2.00"
    assert result["signals"][0]["days_between"] == 0
    assert result["summary"]["explicit_unit_prices"] == 2


@pytest.mark.parametrize(
    ("sides", "status"),
    [([0], "missing_price_a"), ([1], "missing_price_b"), ([0, 1], "missing_both_prices")],
)
def test_unaccepted_offers_and_raw_contract_fields_cannot_substitute_purchase(sides, status):
    cycle = cycle_fixture()
    for side in sides:
        cycle["processes"][side]["products"][0]["purchase_price"] = None
    result = run(cycle)
    assert result["pairs"][0]["blocking_status"] == status
    assert result["pairs"][0]["status"] == "human_review_recommended"
    assert not result["signals"]
    for row in result["comparison_readiness"]:
        if row["preferred_purchase_price"] is None:
            assert "proof_of_winning_offer_acceptance" in row["missing_fields"]
            assert row["accepted_offer_unit_price"] is None


def test_same_model_incompatible_sizes_remains_manual_review_with_alternatives():
    cycle = cycle_fixture()
    item = cycle["processes"][0]["products"][0]
    item["conflicts"] = ["model_reused_for_incompatible_sizes"]
    result = run(cycle)
    row = result["comparison_readiness"][0]
    assert row["readiness_status"] == "human_review_recommended"
    assert "conflicting_product_reference" in row["human_review_reasons"]
    assert "product_conflict" in row["economic_states"]
    assert row["conflicts"] == item["conflicts"]
    assert result["pairs"][0]["blocking_status"] == "conflict_a"
    assert not result["signals"]


def test_price_conflict_blocks_pair():
    cycle = cycle_fixture()
    cycle["processes"][1]["products"][0]["conflicts"] = ["contract_unit_price"]
    result = run(cycle)
    assert result["pairs"][0]["blocking_status"] == "conflict_b"
    assert "price_conflict" in result["comparison_readiness"][1]["economic_states"]


def test_missing_quantity_not_replaced_by_lot_quantity():
    cycle = cycle_fixture()
    cycle["processes"][0]["products"][0]["quantity"] = None
    result = run(cycle)
    assert result["comparison_readiness"][0]["quantity"] is None
    assert result["comparison_readiness"][0]["economic_readiness_status"] == "missing_quantity"
    assert not result["signals"]


def test_missing_supplier_is_visible_and_not_alone_a_blocker():
    cycle = cycle_fixture()
    cycle["processes"][0]["process_global_contracts"] = []
    result = run(cycle)
    assert result["comparison_readiness"][0]["supplier"] is None
    assert "missing_supplier" in result["comparison_readiness"][0]["economic_states"]
    assert result["pairs"][0]["status"] == "ready"


def test_calculated_unit_requires_both_input_provenances():
    cycle = cycle_fixture()
    price = cycle["processes"][0]["products"][0]["purchase_price"]
    price["origin"] = price["evidence"][0]["value_origin"] = "calculated"
    result = run(cycle)
    assert not result["signals"]
    ev = price["evidence"][0]["evidence"]
    price["evidence"][0]["calculation_inputs"] = [
        {"field": "item_total", "value": "200", "evidence": ev},
        {"field": "quantity", "value": "2", "evidence": ev},
    ]
    assert run(cycle)["summary"]["calculated_unit_prices"] == 1
    assert run(cycle)["signals"]


def test_incomplete_price_provenance_blocks_a_signal():
    cycle = cycle_fixture()
    cycle["processes"][0]["products"][0]["purchase_price"]["evidence"][0]["evidence"][0][
        "input_sha256"
    ] = None
    assert not run(cycle)["signals"]


def test_publication_cannot_fill_purchase_date():
    cycle = cycle_fixture()
    item = cycle["processes"][0]["products"][0]
    item["purchase_date"] = None
    item["published_at"] = "2026-10-20"
    assert "verified_purchase_date" in run(cycle)["comparison_readiness"][0]["missing_fields"]
    assert not run(cycle)["signals"]


def test_readiness_does_not_modify_baseline_or_clean_budget_conflicts():
    cycle = cycle_fixture()
    cycle["processes"][0]["products"][0]["conflicts"] = ["budget_unit_price"]
    original = deepcopy(cycle)
    result = run(cycle)
    assert cycle == original
    assert result["signals"]
    assert result["comparison_readiness"][0]["conflicts"] == ["budget_unit_price"]


def test_technical_mismatch_and_same_entity_cannot_emit_signal():
    cycle = cycle_fixture()
    cycle["processes"][1]["products"][0]["specifications"]["screen_size_inches"] = 70
    assert run(cycle)["pairs"][0]["status"] == "technical_mismatch"
    cycle = cycle_fixture()
    cycle["comparisons"][0]["entities"] = ["Entidad A", "Entidad A"]
    assert run(cycle)["pairs"][0]["status"] == "technical_mismatch"


def test_unavailable_frozen_observation_fails_instead_of_expanding_scope():
    cycle = cycle_fixture()
    cycle["comparisons"][0]["observation_ids"][0] = "MISSING"
    with pytest.raises(ValueError, match="unavailable observation"):
        run(cycle)


def test_explicit_award_supplier_is_process_evidence_and_never_a_unit_price():
    fragment = {
        "id": "f",
        "original_name": "RESOLUCION ADJUDICACION.pdf",
        "document_version_id": "v",
        "text": "ARTÍCULO PRIMERO. Adjudicación. Adjudicar el proceso a "
        "PROVEEDOR EJEMPLO S.A.S., NIT omitido, por $500.000.",
        "source_locator": {
            "page_number": 3,
            "input_sha256": "sha",
            "extraction_method": "native_pdf_text",
        },
    }
    result = documentary_award_winners([fragment])
    assert result[0]["supplier"] == "PROVEEDOR EJEMPLO S.A.S."
    assert result[0]["source_page"] == 3
    assert "price" not in result[0]
    fragment["text"] = "Se evalúa la propuesta de PROVEEDOR EJEMPLO S.A.S., NIT omitido"
    assert not documentary_award_winners([fragment])
