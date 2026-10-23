from dataclasses import replace
from datetime import date

import pytest

from public_procurement.eureka.domain.affinity import match_catalog
from public_procurement.eureka.domain.radar import candidate_decision, evaluate_alert
from public_procurement.eureka.radar_config import load_radar_config
from public_procurement.eureka.radar_services import radar_process
from public_procurement.shared.config import Settings

from .test_details import covarachia_entries, setup_details


@pytest.fixture
def config():
    return load_radar_config(
        Settings(database_url="postgresql://unused", _env_file=None).eureka_radar_config_path
    )


def process():
    from public_procurement.ingestion.services import SecopProcess

    return SecopProcess(
        "CO1.REQ.11172521",
        "CO1.BDOS.golden",
        "REF",
        "San Luis Beltrán",
        "Boyacá",
        "Covarachía",
        "Suministro de refrigerios",
        "Día del colegio",
        "Mínima cuantía",
        "Presentación de oferta",
        "Publicado",
        date(2026, 10, 7),
        date(2026, 10, 7),
        2080000,
        "50192703",
        None,
        offer_deadline_raw="2026-10-13T00:00:00.000",
    )


def details(score=65):
    service, _, _ = setup_details(
        covarachia_entries(), missing=("RUP_REQUIRED", "EXPERIENCE_REQUIRED", "DELIVERY_COUNT")
    )
    return replace(service.get("CO1.REQ.11172521"), score=score)


@pytest.mark.parametrize(
    "text", ["JUGO HIT TETRA X 200Ml", "JUGOS TETRA HIT X 200 Ml", "Hit 200 ml", "Jugo Hit"]
)
def test_alias_normalization_recognizes_hit(config, text):
    assert any(match.concept == "Jugo Hit" for match in match_catalog(text, "", config))


def test_token_matching_not_substring_and_unspsc_is_preliminary(config):
    assert not match_catalog("whitelist", "", config)
    matches = match_catalog("Compra", "50192703", config)
    assert matches
    assert all(match.method == "unspsc" and match.origin == "metadata" for match in matches)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"published_on": date(2026, 10, 6)}, "outside_window"),
        ({"department": "Bogotá"}, "outside_region"),
        ({"title": "Interventoría", "description": ""}, "strong_exclusion"),
        ({"published_on": None}, "publication_unknown"),
    ],
)
def test_initial_filters(config, change, code):
    result = candidate_decision(
        radar_process(replace(process(), **change)),
        date(2026, 10, 7),
        date(2026, 10, 14),
        ("Boyacá", "Casanare"),
        config,
    )
    assert not result.accepted
    assert result.code == code


@pytest.mark.parametrize("raw", [None, "", "-", "   ", "not-a-date", "2026-02-30"])
def test_offer_deadline_is_a_hard_candidate_condition(config, raw):
    record = radar_process(replace(process(), offer_deadline_raw=raw))
    decision = candidate_decision(
        record, date(2026, 10, 5), date(2026, 10, 16), ("Boyacá",), config
    )
    assert not decision.accepted
    assert decision.code == "missing_or_invalid_offer_deadline"
    assert not evaluate_alert(record, decision, details(), config, 30_000_000).create


@pytest.mark.parametrize("state", ["Proceso cancelado", "Adjudicado", "Evaluación", "Cerrado"])
def test_parseable_past_deadline_passes_without_state_or_phase_gate(config, state):
    record = radar_process(
        replace(process(), status=state, phase=state, offer_deadline_raw="2026-10-01T00:00:00.000")
    )
    decision = candidate_decision(
        record, date(2026, 10, 5), date(2026, 10, 16), ("Boyacá",), config
    )
    assert decision.accepted
    assert decision.code == "candidate"


def test_parentheses_in_reference_title_and_description_do_not_disqualify(config):
    record = radar_process(
        replace(
            process(),
            reference="FGN-RCS-IPSE-0042-2026 (Presentación de oferta)",
            title="Suministro de refrigerios (Presentación de oferta)",
            description="Comunidad educativa (actividades culturales)",
        )
    )
    assert candidate_decision(
        record, date(2026, 10, 5), date(2026, 10, 16), ("Boyacá",), config
    ).accepted


@pytest.mark.parametrize("score", [0, 20, 59, 65])
def test_confirmed_affinity_can_alert_below_reference_unknown_requirements_do_not_block(
    config, score
):
    record = radar_process(process())
    candidate = candidate_decision(
        record, date(2026, 10, 7), date(2026, 10, 14), ("Boyacá",), config
    )
    result = evaluate_alert(record, candidate, details(score), config, 30_000_000)
    assert result.create
    assert result.confirmed
    assert result.review_required
    assert result.snapshot["score"] == score
    assert result.snapshot["products"][0]["name"] == "jugo hit"
    assert result.snapshot["execution_days"] == 5
    assert result.snapshot["payment_days"] == 30
    assert result.snapshot["guarantee_required"] == "not_required"
    assert any(
        reason["code"] == "score_reference" and reason["mandatory_gate"] is False
        for reason in result.reasons
    )
    assert any(
        reason.get("method") == "unspsc" and reason["origin"] == "metadata"
        for reason in result.reasons
    )
    assert any(
        reason["code"] == "confirmed_commercial_match" and reason["structured_fact_ids"]
        for reason in result.reasons
    )


@pytest.mark.parametrize("budget", [None, 2080000, 30_000_000, 30_000_001, 100_000_000])
def test_budget_is_review_not_exclusion(config, budget):
    record = radar_process(replace(process(), base_price_cop=budget))
    canonical = details()
    canonical.commercial_profile["budget_cop"] = budget
    candidate = candidate_decision(
        record, date(2026, 10, 7), date(2026, 10, 14), ("Boyacá",), config
    )
    result = evaluate_alert(record, candidate, canonical, config, 30_000_000)
    assert result.create
    if budget and budget > 30_000_000:
        assert result.priority == "medium"


def test_metadata_alone_and_conflicting_facts_never_confirm_product(config):
    record = radar_process(process())
    candidate = candidate_decision(
        record, date(2026, 10, 7), date(2026, 10, 14), ("Boyacá",), config
    )
    canonical = details()
    canonical.commercial["products"] = []
    canonical.commercial["purchase_items"] = []
    assert not evaluate_alert(record, candidate, canonical, config, 30_000_000).create
    canonical.commercial["products"] = [{"status": "conflict", "value": {"name": "jugo hit"}}]
    assert not evaluate_alert(record, candidate, canonical, config, 30_000_000).confirmed


def test_strong_exclusion_blocks_even_with_documentary_affinity(config):
    record = radar_process(process())
    candidate = candidate_decision(
        record, date(2026, 10, 7), date(2026, 10, 14), ("Boyacá",), config
    )
    canonical = details()
    canonical.commercial["purchase_items"][0]["value"]["description"] = (
        "software a la medida con refrigerios"
    )
    assert not evaluate_alert(record, candidate, canonical, config, 30_000_000).create


def test_large_reference_threshold_does_not_block_golden_case(config):
    config = config.model_copy(update={"alert_score_threshold": 9999})
    record = radar_process(process())
    candidate = candidate_decision(
        record, date(2026, 10, 7), date(2026, 10, 14), ("Boyacá",), config
    )
    result = evaluate_alert(record, candidate, details(score=65), config, 30_000_000)
    assert result.create
    assert result.snapshot["score"] == 65
    assert any(
        reason["code"] == "unspsc_match" and reason["origin"] == "canonical_fact"
        for reason in result.reasons
    )


def test_broad_metadata_or_matching_and_negated_exclusions(config):
    record = radar_process(
        replace(
            process(),
            title="Suministro de elementos",
            description="sin obra civil",
            category_code=None,
        )
    )
    candidate = candidate_decision(
        record, date(2026, 10, 7), date(2026, 10, 14), ("Boyacá",), config
    )
    assert candidate.accepted
    assert candidate.matches[0]["method"] == "broad_term/normalization"
