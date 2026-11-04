from dataclasses import replace

import pytest

from public_procurement.documents.services import SourceDocument
from public_procurement.investigation.document_recovery import recover_inventory
from public_procurement.investigation.human_review import recommend_human_review


def doc(identifier="1"):
    return SourceDocument(
        identifier,
        "CO1.BDOS.1",
        "OFERTA ECONOMICA.pdf",
        None,
        "https://community.secop.gov.co/file",
    )


class Inventory:
    def __init__(self):
        self.calls = []
        self.contract_docs = [doc(), doc("2")]

    def fetch(self, key):
        self.calls.append(("process", key))
        return [doc()]

    def fetch_by_contract(self, key):
        self.calls.append(("contract", key))
        return self.contract_docs


def recover(source, **kwargs):
    return recover_inventory(
        source,
        portfolio_id="CO1.BDOS.1",
        contracts=[{"proceso_de_compra": "CO1.BDOS.1", "id_contrato": "CO1.PCCNTR.123"}],
        **kwargs,
    )


def test_contract_fallback_combines_and_deduplicates_all_origin_keys():
    source = Inventory()
    result = recover(source)
    assert source.calls == [("process", "CO1.BDOS.1"), ("contract", "CO1.PCCNTR.123")]
    assert result["merged_count"] == 2
    assert result["additional_document_ids"] == ["2"]
    origins = result["discovery_provenance"]["1"]
    assert {o["kind"] for o in origins} == {"process_identifier", "contract_identifier"}
    assert {o["provider_field"] for o in origins} == {"proceso", "n_mero_de_contrato"}


def test_same_name_different_official_document_ids_are_not_collapsed():
    result = recover(Inventory())
    assert len(result["documents"]) == 2


def test_contract_raw_process_key_is_preserved_separately_from_association():
    source = Inventory()
    source.contract_docs = [replace(doc("2"), portfolio_id="CO1.REQ.42")]
    result = recover(source, cached_documents=[doc()])
    assert source.calls == [("contract", "CO1.PCCNTR.123")]
    assert all(d["portfolio_id"] == "CO1.BDOS.1" for d in result["documents"])
    origin = result["discovery_provenance"]["2"][0]
    assert origin["provider_process_identifier"] == "CO1.REQ.42"
    assert origin["associated_portfolio_id"] == "CO1.BDOS.1"


def test_unverified_contract_relationship_is_not_queried():
    source = Inventory()
    result = recover_inventory(
        source,
        portfolio_id="CO1.BDOS.1",
        contracts=[{"proceso_de_compra": "wrong", "id_contrato": "CO1.PCCNTR.123"}],
    )
    assert source.calls == [("process", "CO1.BDOS.1")]
    assert result["merged_count"] == 1


def test_conflicting_metadata_does_not_replace_existing_evidence():
    source = Inventory()
    source.contract_docs = [replace(doc(), original_name="DIFFERENT.pdf")]
    result = recover(source)
    assert result["documents"][0]["original_name"] == "OFERTA ECONOMICA.pdf"
    assert result["warnings"][0]["reason"] == "unresolved_document_relationship"


@pytest.mark.parametrize(("potential", "discarded"), [(False, False), (True, True)])
def test_discardable_or_uninteresting_process_is_not_a_human_review_case(potential, discarded):
    result = recommend_human_review(
        potential=potential,
        discarded=discarded,
        ready=False,
        reasons=["missing_itemized_contract_price"],
    )
    assert not result["human_review_recommended"]
    assert result["human_review_reasons"] == []


def test_partial_interesting_process_is_a_recommendation_not_a_signal_or_error():
    result = recommend_human_review(
        potential=True,
        ready=False,
        reasons=["missing_itemized_contract_price", "missing_itemized_contract_price"],
    )
    assert result["review_status"] == "human_review_recommended"
    assert result["human_review_reasons"] == ["missing_itemized_contract_price"]
    assert "signal" not in result
    assert "error" not in result
