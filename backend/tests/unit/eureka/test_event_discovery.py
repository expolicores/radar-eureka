"""Regresión offline; no representa una extracción del documento original de Guateque."""

import json
import uuid
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from public_procurement.eureka.domain.affinity import match_catalog
from public_procurement.eureka.domain.radar import candidate_decision, evaluate_alert
from public_procurement.eureka.radar_config import CommercialFamily, load_radar_config
from public_procurement.eureka.radar_services import radar_process
from public_procurement.extraction.structured_rules import extract_facts
from public_procurement.shared.config import Settings

from ..extraction.test_structured_rules import fragment
from .test_affinity import details, process
from .test_radar import run, setup


@pytest.fixture
def config():
    return load_radar_config(
        Settings(database_url="postgresql://unused", _env_file=None).eureka_radar_config_path
    )


@pytest.fixture
def guateque():
    return json.loads(
        (Path(__file__).parents[2] / "fixtures/eureka/mg_mic_057_2026.json").read_text(
            encoding="utf-8"
        )
    )


def record(case, *, title=None):
    # Keep the existing synthetic unit-test identity/dates; they are not source assertions.
    return replace(
        process(),
        reference=case["reference"],
        entity_name=case["entity_name"],
        department=case["department"],
        municipality=case["municipality"],
        title=title if title is not None else case["object"],
        description=None,
        category_code=case["unspsc"],
        base_price_cop=case["budget_cop"],
    )


def candidate(value, config):
    return candidate_decision(
        radar_process(value), date(2026, 10, 7), date(2026, 10, 14), ("Boyacá",), config
    )


def empty_details(*, unavailable=False):
    normal = details()
    return replace(
        normal,
        enrichment_status="documents_unavailable" if unavailable else "consolidated",
        commercial={**normal.commercial, "products": [], "purchase_items": [], "unspsc": []},
        evidence={},
        quality={"document_status": "unavailable"} if unavailable else {},
    )


def test_catalog_adds_only_one_discovery_code_and_keeps_commercial_codes(config):
    contextual = [f for f in config.families if f.discovery_only]
    assert len(contextual) == 1
    assert contextual[0].unspsc == ("80141607",)
    assert len({c for f in config.families for c in f.unspsc}) == 45
    assert len({c for f in config.families if not f.discovery_only for c in f.unspsc}) == 44
    assert not match_catalog("", "80141607", config)


def test_guateque_enters_funnel_by_unspsc_without_broad_terms(config, guateque):
    isolated = config.model_copy(update={"candidate_terms": ()})
    value = record(guateque)
    assert not candidate(
        value,
        isolated.model_copy(
            update={"families": tuple(f for f in isolated.families if not f.discovery_only)}
        ),
    ).accepted
    decision = candidate(value, isolated)
    assert decision.accepted
    assert [(m["method"], m["matched"], m["discovery_only"]) for m in decision.matches] == [
        ("unspsc", "80141607", True)
    ]
    service, repo, pipeline = setup(isolated)
    pipeline.enrich.return_value = empty_details()
    report = run(service, [value])
    pipeline.enrich.assert_called_once()
    assert report["candidates"] == 1
    assert report["alerts_created"] == 0
    assert repo.outcomes[0]["candidate_matches"] == decision.matches


def test_unspsc_only_never_generates_metadata_alert(config, guateque):
    value = record(guateque, title="Gestión de eventos")
    decision = evaluate_alert(
        radar_process(value),
        candidate(value, config),
        empty_details(unavailable=True),
        config,
        30_000_000,
    )
    assert not decision.create
    assert not decision.confirmed
    assert decision.review_required
    assert decision.snapshot["evidence_level"] == "metadata_only"
    assert any(r["code"] == "discovery_only_requires_commercial_evidence" for r in decision.reasons)


def test_existing_metadata_signals_retain_provisional_semantics(config, guateque):
    value = record(guateque, title="Suministro de papelería")
    result = evaluate_alert(
        radar_process(value),
        candidate(value, config),
        empty_details(unavailable=True),
        config,
        30_000_000,
    )
    assert result.create
    assert not result.confirmed
    assert "event_supplies_discovery" not in result.snapshot["category"]


def test_document_affinity_still_uses_existing_commercial_evaluation(config, guateque):
    value = record(guateque, title="Gestión de eventos")
    commercial = details()
    result = evaluate_alert(
        radar_process(value), candidate(value, config), commercial, config, 30_000_000
    )
    assert result.confirmed
    assert result.snapshot["score"] == commercial.score
    assert all(
        m["category"] != "event_supplies_discovery" for m in result.snapshot["confirmed_matches"]
    )


def test_declared_quantity_uses_existing_extraction_with_provenance(guateque):
    # Synthetic layout using ONLY the reported item/quantity. No invented prices.
    # This exercises the existing parser, not extraction of the original PDF.
    assert "500 balones personalizados" in guateque["declared_goods"]
    source = fragment(
        "ITEM DESCRIPCION CANT UNIDAD VALOR UNITARIO VALOR TOTAL "
        "1 Balones personalizados 500 UNIDADES XXXXX XXXXX"
    )
    facts = extract_facts(uuid.uuid4(), [source])
    quantity = next(f for f in facts if f.fact_type == "quantity" and f.numeric_value == 500)
    assert quantity.numeric_value == 500
    assert quantity.content_fragment_id == source.id
    assert "500" in quantity.evidence_text
    item = next(f for f in facts if f.fact_type == "purchase_item")
    assert item.normalized_value["description"] == "Balones personalizados"
    assert item.normalized_value["unit_price_cop"] is None


@pytest.mark.parametrize("code", ["80141600", "80141605", "80141611", "80141626", "80101500"])
def test_neighbors_not_enabled(config, guateque, code):
    assert not candidate(
        replace(record(guateque, title="Gestión de eventos"), category_code=code), config
    ).accepted


def test_discovery_family_cannot_smuggle_commercial_terms():
    with pytest.raises(ValueError, match="solo admite"):
        CommercialFamily(
            category="context",
            label="Context",
            discovery_only=True,
            unspsc=("80141607",),
            terms=("events",),
        )
