from dataclasses import replace
from decimal import Decimal

import pytest

from public_procurement.investigation.domain.television import (
    Television,
    compare_pair,
    television_specs,
)
from public_procurement.investigation.research import (
    build_report,
    research_observations,
    tv_in_official_scope,
)
from public_procurement.investigation.research_comparison import compare_observations


def bought(**changes):
    p = Television(
        process_id="REQ-A",
        entity="Entidad A",
        description="Televisor LG 55 pulgadas",
        screen_size_inches=55,
        resolution="4k",
        panel="LED",
        smart=True,
        brand="LG",
        model="55ABC",
        quantity=Decimal(2),
        unit="UNIDAD",
        unit_price_cop=Decimal(100),
        total_cop=Decimal(200),
        price_stage="contract",
        price_reliable=True,
        vat_basis="included",
        observation_id="obs-A",
        published_at="2026-10-10",
        evidence=[{"fact_id": "fact-A", "text": "fila con precio"}],
    )
    return replace(p, **changes)


def test_two_purchases_can_be_compared_without_the_old_five_comparable_barrier():
    a = bought()
    b = bought(
        process_id="REQ-B",
        entity="Entidad B",
        observation_id="obs-B",
        unit_price_cop=Decimal(150),
        total_cop=Decimal(300),
    )
    result = compare_observations([a, b])
    assert result["comparisons_possible"] == 1
    pair = result["comparisons"][0]
    assert pair["absolute_difference_cop"] == "50"
    assert Decimal(pair["difference_pct"]) == 50
    assert len(result["signals"]) == 1
    assert result["signals"][0]["requires_human_review"] is True


@pytest.mark.parametrize(
    "change",
    [
        {"quantity": None},
        {"price_stage": "offer"},
        {"price_reliable": False},
        {"unit_price_cop": Decimal(0)},
        {"warnings": ["unsigned_or_unverified_contract"]},
        {"warnings": ["partial_document_coverage"]},
        {"currency": "USD"},
    ],
)
def test_missing_or_unreliable_fields_do_not_get_a_numeric_purchase_difference(change):
    pair = compare_pair(
        bought(), bought(process_id="REQ-B", entity="Entidad B", **change), research_v2=True
    )
    assert pair["difference_pct"] is None
    assert pair["comparison_eligible"] is False


def test_unknown_tax_preserves_raw_comparison_but_not_a_signal():
    a = bought(vat_basis="undetermined")
    b = bought(
        process_id="REQ-B",
        entity="Entidad B",
        observation_id="obs-B",
        vat_basis="undetermined",
        unit_price_cop=Decimal(180),
    )
    result = compare_observations([a, b])
    assert result["comparisons_possible"] == 1
    assert result["signals"] == []


def test_conflicting_canonical_not_silently_promoted_to_a_signal():
    a = bought(warnings=["cross_document_canonical_conflict_preserved"])
    b = bought(
        process_id="REQ-B", entity="Entidad B", observation_id="obs-B", unit_price_cop=Decimal(180)
    )
    result = compare_observations([a, b])
    assert result["signals"] == []


def test_smart_no_hd_and_miniled_are_explicit_not_guessed():
    assert television_specs("Televisor 32” HD no Smart TV")["smart"] is False
    assert television_specs("Televisor 32” HD no Smart TV")["resolution"] == "hd"
    assert television_specs("Televisor 75” Mini LED 4K")["panel"] == "MINI LED"
    assert television_specs("Televisor 55” Full HD 4K")["resolution"] is None


def test_interactive_screen_is_not_treated_as_a_standard_equivalent():
    a = bought(other_specifications={"interactive_touchscreen": True})
    b = bought(process_id="REQ-B", entity="Entidad B")
    assert compare_pair(a, b, research_v2=True)["comparability"] == "partially_comparable"


def test_research_summary_keeps_sample_size_separate_from_discovery():
    sample = {
        "source": "socrata_secop",
        "started_at": "2026-11-03T12:00:00Z",
        "finished_at": "2026-11-03T12:01:00Z",
        "window_start": "2026-10-04",
        "window_before": "2026-11-03",
        "research_policy": "research-pair-v2",
        "selection": {"discovered_unique": 6329, "mature_metadata": 2175},
        "processes": [
            {"process": {"id_del_proceso": "REQ-A", "id_del_portafolio": "BDOS-A", "entidad": "A"}}
        ],
    }
    report = build_report(sample, [], {})
    assert report["summary"]["processes_found"] == 6329
    assert report["summary"]["document_candidates"] == 1
    assert report["summary"]["processes_with_documented_tv"] == 0
    assert report["analysis_config"]["min_purchases_for_pair"] == 2


def test_duplicate_content_is_not_independent_product_evidence():
    row = {
        "id_del_proceso": "REQ-A",
        "entidad": "Entidad A",
        "fecha_de_publicacion_del": "2026-10-20",
    }

    def fact(identifier, version):
        return {
            "id": identifier,
            "document_version_id": version,
            "fact_type": "purchase_item",
            "rule_name": "tv_row_price_explicit",
            "confidence": "0.8",
            "evidence_text": "TV fila cantidad y precio",
            "normalized_value": {
                "description": "Televisor LG 55 pulgadas modelo 55ABC LED 4K Smart TV",
                "quantity": "2",
                "unit_price_cop": "100",
                "total_cop": "200",
            },
            "source_locator": {
                "sources": [
                    {
                        "original_name": "CONTRATO.pdf",
                        "locator": {"input_sha256": "same-hash", "page_number": 2},
                    }
                ]
            },
        }

    item = {"process": row, "facts": [fact("fact1", "version1"), fact("fact2", "version2")]}
    result = research_observations(
        item, [{"fecha_de_firma": "2026-10-21", "proveedor_adjudicado": "Proveedor"}], []
    )
    assert len(result) == 1
    assert result[0].price_reliable is True


def test_service_mentions_do_not_become_tv_purchase_confirmation():
    item = {
        "process": {
            "id_del_proceso": "REQ-A",
            "entidad": "A",
            "nombre_del_procedimiento": "Mantenimiento de equipos",
        }
    }
    fragments = [
        {
            "id": "f",
            "document_version_id": "v",
            "original_name": "ESTUDIO PREVIO.pdf",
            "text": "Televisor 55 pulgadas Smart TV para mantenimiento",
            "source_locator": {"input_sha256": "hash", "page_number": 1},
        }
    ]
    products = research_observations(item, [], fragments)
    assert len(products) == 1
    assert "service_not_purchase" in products[0].warnings
    assert products[0].price_reliable is False


@pytest.mark.parametrize(
    ("metadata", "name", "content", "expected"),
    [
        ("Dotación institucional", "ESPECIFICACIONES.pdf", "Televisor Smart TV", True),
        ("Televisores", "CONTRATO.pdf", "Servicios de actividad pedagogica", False),
        ("Mantenimiento", "CONTRATO.pdf", "Mantenimiento de televisores", False),
        ("Dotación", "EXPERIENCIA CONTRATO.pdf", "Compra de televisores", False),
        ("Dotación", "COTIZACION.pdf", "Televisor Smart TV", False),
        ("Televisores", "ESTUDIOS PREVIOS.pdf", "Computadores portátiles", False),
    ],
)
def test_documentary_tv_confirmation_requires_official_current_scope(
    metadata, name, content, expected
):
    assert (
        tv_in_official_scope(
            {"nombre_del_procedimiento": metadata},
            [{"original_name": name, "text": content}],
        )
        is expected
    )
