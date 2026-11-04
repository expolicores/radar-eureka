import json
from dataclasses import replace
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.investigation.domain.television import (
    Television,
    comparability,
    compare_pair,
    positive_decimal,
    television_specs,
)
from public_procurement.investigation.research import (
    ResearchReportStore,
    build_report,
    document_stage,
    products_from_canonicals,
    relevant_document,
    specification_evidence,
)
from public_procurement.investigation.research_api import router


def product(**kwargs):
    return Television(process_id="REQ-A", entity="Entity A", description="Televisor", **kwargs)


@pytest.mark.parametrize("raw", [None, "bad", "NaN", "Infinity", 0, -1])
def test_invalid_prices_remain_absent(raw):
    assert positive_decimal(raw) is None


def test_only_explicit_tv_specs_are_normalized():
    spec = television_specs("Televisor Samsung modelo QN55Q60D QLED 55 pulgadas UHD Smart TV")
    assert spec == {
        "screen_size_inches": 55,
        "panel": "QLED",
        "resolution": "4k",
        "smart": True,
        "brand": "SAMSUNG",
        "model": "QN55Q60D",
    }
    assert all(v is None for v in television_specs("Televisor").values())


def test_multiple_sizes_do_not_silently_choose_one():
    assert television_specs("Televisor de 50 pulgadas o 55 pulgadas")["screen_size_inches"] is None


def test_keyword_only_is_not_a_comparable_product():
    assert (
        comparability(product(), replace(product(), process_id="REQ-B", entity="Entity B"))[0]
        == "not_comparable"
    )


def test_same_entity_is_not_cross_entity_evidence():
    assert comparability(product(), replace(product(), process_id="REQ-B"))[0] == "not_comparable"


def test_same_model_and_incompatible_specs_are_distinct():
    a = product(brand="LG", model="55ABC", screen_size_inches=55)
    b = replace(a, process_id="REQ-B", entity="Entity B")
    assert comparability(a, b)[0] == "same_model"
    assert comparability(a, replace(b, screen_size_inches=65))[0] == "not_comparable"


def test_partial_and_highly_comparable_specs():
    a = product(screen_size_inches=55)
    b = replace(a, process_id="REQ-B", entity="Entity B")
    assert comparability(a, b)[0] == "partially_comparable"
    a = replace(a, panel="QLED", resolution="4k", smart=True)
    assert (
        comparability(a, replace(b, panel="QLED", resolution="4k", smart=True))[0]
        == "highly_comparable"
    )


def test_pair_difference_is_not_a_fabricated_signal():
    a = product(brand="LG", model="55ABC", unit_price_cop=Decimal(100))
    b = replace(a, process_id="REQ-B", entity="Entity B", unit_price_cop=Decimal(150))
    pair = compare_pair(a, b)
    assert Decimal(pair["difference_pct"]) == 50
    assert pair["signal"] is False
    assert "tax_basis_unverified" in pair["limitations"]
    assert "purchase_price_not_confirmed" in pair["limitations"]


def source_item(status="confirmed", price="100", total="200"):
    return {
        "process": {"id_del_proceso": "REQ-A", "entidad": "Entity A"},
        "facts": [],
        "canonicals": {
            "facts": [
                {
                    "id": "canonical",
                    "canonical_type": "PURCHASE_ITEM",
                    "status": status,
                    "confidence": "0.8",
                    "evidence_ids": [],
                    "canonical_value": {
                        "value": {
                            "description": "Televisor 55 pulgadas",
                            "quantity": "2",
                            "unit": "UNIDAD",
                            "unit_price_cop": price,
                            "total_cop": total,
                        }
                    },
                }
            ]
        },
    }


def test_global_total_is_never_divided_to_invent_unit_price():
    assert products_from_canonicals(source_item(price=None))[0].unit_price_cop is None


@pytest.mark.parametrize(
    ("item", "warning"),
    [
        (source_item(status="conflict"), "conflicting_canonical"),
        (source_item(total="300"), "quantity_price_total_mismatch"),
    ],
)
def test_conflicts_or_bad_arithmetic_retain_provenance_but_block_price(item, warning):
    p = products_from_canonicals(item)[0]
    assert p.unit_price_cop is None
    assert warning in p.warnings


def test_budget_contract_award_have_different_stages():
    assert document_stage("ESTUDIO PREVIO.pdf") == "specifications"
    assert document_stage("COMUNICADO DE ACEPTACION.pdf") == "award"
    assert document_stage("CONTRATO FIRMADO.pdf") == "contract"
    assert not relevant_document("CEDULA DE CIUDADANIA.pdf")
    assert not relevant_document("CERTIFICACION BANCARIA.pdf")


def test_specification_excerpt_preserves_page_fragment_and_hash():
    f = {
        "id": "fragment",
        "document_version_id": "version",
        "original_name": "estudio.pdf",
        "text": "Televisor 55 pulgadas QLED UHD. CONTRATISTA: private person",
        "source_locator": {"page_number": 3, "input_sha256": "hash"},
    }
    result = specification_evidence([f])[0]
    assert result["source_locator"]["page_number"] == 3
    assert result["source_locator"]["input_sha256"] == "hash"
    assert result["fragment_id"] == "fragment"
    assert "private person" not in result["description"]
    assert result["unit_price_cop"] is None


def sample():
    return {
        "source": "socrata_secop",
        "started_at": "2026-11-03T12:00:00Z",
        "finished_at": "2026-11-03T12:01:00Z",
        "window_start": "2026-10-17",
        "window_before": "2026-10-24",
        "processes": [
            {
                "process": {
                    "id_del_proceso": "REQ-A",
                    "id_del_portafolio": "BDOS-A",
                    "entidad": "Entity A",
                }
            }
        ],
    }


def test_contract_link_uses_exact_published_portfolio_not_inferred_req_ntc():
    s = sample()
    report = build_report(
        s,
        [
            {"proceso_de_compra": "BDOS-A", "id_contrato": "CONTRACT-A"},
            {"proceso_de_compra": "REQ-A", "id_contrato": "WRONG"},
        ],
        {},
    )
    assert [c["id_contrato"] for c in report["processes"][0]["contracts"]] == ["CONTRACT-A"]
    assert report["signals"] == []
    assert report["processes"][0]["lifecycle_missing"]


def test_demo_or_partial_sample_is_rejected():
    s = sample()
    s["source"] = "demo"
    with pytest.raises(ValueError, match="muestra Socrata finalizada"):
        build_report(s, [], {})
    s["source"] = "socrata_secop"
    s["finished_at"] = None
    with pytest.raises(ValueError, match="muestra Socrata finalizada"):
        build_report(s, [], {})


def test_conflicting_canonical_is_not_exposed_as_a_confirmed_value():
    s = sample()
    s["processes"][0].update({"canonicals": source_item(status="conflict")["canonicals"]})
    report = build_report(s, [], {})
    canonical = report["processes"][0]["canonical_summaries"][0]
    assert canonical["value"] is None
    assert canonical["status"] == "conflict"


def test_report_store_missing_never_falls_back_to_demo_and_publication_is_atomic(tmp_path):
    store = ResearchReportStore(tmp_path)
    assert store.read()["signal_status"] == "not_run"
    store.write(build_report(sample(), [], {}))
    assert store.read()["processes"][0]["id"] == "REQ-A"
    assert not list(tmp_path.glob("*.tmp"))
    store.path.write_text(json.dumps({"source": "demo"}), encoding="utf-8")
    with pytest.raises(ValueError, match="Informe investigativo inválido"):
        store.read()


def test_report_endpoint_is_read_only_and_reports_invalid_file(tmp_path):
    app = FastAPI()
    app.include_router(router)
    app.state.research_reports = ResearchReportStore(tmp_path)
    client = TestClient(app)
    assert client.get("/api/v1/investigation/research").json()["processes"] == []
    assert not list(tmp_path.iterdir())
    app.state.research_reports.path.write_text("invalid", encoding="utf-8")
    assert client.get("/api/v1/investigation/research").status_code == 503
