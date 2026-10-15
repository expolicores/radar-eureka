import uuid
from dataclasses import asdict, replace
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.encoders import jsonable_encoder

from public_procurement.eureka.domain.details import (
    CanonicalEntry,
    CanonicalInput,
    StoredOpportunity,
)
from public_procurement.eureka.services import EurekaDetailsService

from .test_discovery import facts


def entry(kind, value, status="confirmed", candidates=None):
    return CanonicalEntry(
        uuid.uuid4(),
        kind,
        value,
        Decimal("0.8"),
        status,
        False,
        (uuid.uuid4(),),
        candidates or [],
        {},
    )


def setup_details(entries=(), status="consolidated", missing=(), stored=True):
    process = facts(secop_id="CO1.REQ.11172521")
    source, opportunities, canonical = Mock(), Mock(), Mock()
    source.iter_processes.return_value = [process]
    opportunity = StoredOpportunity(
        uuid.uuid4(),
        process.process_id,
        65,
        "high",
        ("packaged_food",),
        False,
        "eureka-discovery-v1",
    )
    opportunities.get_by_process.return_value = opportunity if stored else None
    canonical.read.return_value = CanonicalInput(status, tuple(entries), tuple(missing), 39)
    return EurekaDetailsService(source, opportunities, canonical), opportunity, canonical


def covarachia_entries():
    return [
        entry(
            "PRODUCT", {"name": "jugo hit", "presentation_value": 200, "presentation_unit": "ml"}
        ),
        entry(
            "PRODUCT",
            {"name": "chocorramo tradicional", "presentation_value": 65, "presentation_unit": "g"},
        ),
        entry(
            "PURCHASE_ITEM",
            {
                "description": "Refrigerios",
                "quantity": 400,
                "unit": "PACK",
                "unit_price_cop": 5200,
                "total_cop": 2080000,
            },
        ),
        entry("BUDGET_COP", {"value": 2080000, "unit": "COP"}),
        entry("UNSPSC", {"code": "50192703"}),
        entry("EXECUTION_TERM", {"value": 5, "unit": "days", "kind": "calendar"}),
        entry("DELIVERY_LOCATION", "Institución Educativa San Luis Beltrán, Covarachía"),
        entry("PAYMENT_METHOD", {"mode": "single_payment", "percent": 100}),
        entry("PAYMENT_PERCENTAGE", {"value": 100, "unit": "percent"}),
        entry(
            "PAYMENT_TERM",
            {"value": 30, "unit": "days", "kind": "calendar", "trigger": "aprobación"},
        ),
        entry("GUARANTEE_REQUIRED", {"state": "not_required", "subject": "policy"}),
    ]


def test_covarachia_read_model_products_items_profile_and_unchanged_score():
    service, stored, canonical = setup_details(
        covarachia_entries(), missing=("RUP_REQUIRED", "EXPERIENCE_REQUIRED", "DELIVERY_COUNT")
    )
    result = service.get("CO1.REQ.11172521")
    assert result.score == stored.score == 65
    assert result.priority == "high"
    assert result.enrichment_status == "consolidated"
    assert len(result.commercial["products"]) == 2
    assert result.commercial["purchase_items"][0]["value"]["unit_price_cop"] == 5200
    assert result.commercial_profile["product_match"] is True
    assert result.commercial_profile["budget_cop"] == 2080000
    assert result.commercial_profile["execution_days"] == 5
    assert result.commercial_profile["payment_days"] == 30
    assert result.commercial_profile["guarantee_required"] == "not_required"
    assert result.commercial_profile["rup_required"] == "unknown"
    assert result.commercial_profile["experience_required"] == "unknown"
    assert result.evidence["commercial.products"][0]["structured_fact_ids"]
    assert not result.review_required
    canonical.run.assert_not_called()
    canonical.extract.assert_not_called()


@pytest.mark.parametrize("status", ["not_extracted", "extracted", "structured"])
def test_opportunity_without_canonical_facts_retains_score_and_unknown_requirements(status):
    service, stored, _ = setup_details(status=status, missing=("RUP_REQUIRED",))
    result = service.get("P")
    assert result.score == stored.score
    assert result.enrichment_status == status
    assert result.commercial["products"] == []
    assert result.commercial_profile["product_match"] is None
    assert result.commercial_profile["guarantee_required"] == "unknown"
    assert result.quality["missing_fields"] == ["RUP_REQUIRED"]


def test_conflict_keeps_candidates_evidence_and_no_chosen_budget():
    candidate = {"value": 2000000, "structured_fact_ids": [str(uuid.uuid4())]}
    service, _, _ = setup_details(
        [entry("BUDGET_COP", None, "conflict", [candidate])], status="conflict"
    )
    result = service.get("P")
    assert result.review_required
    assert result.commercial_profile["budget_cop"] is None
    assert result.quality["conflicts"][0]["candidates"] == [candidate]
    assert result.quality["conflicts"][0]["structured_fact_ids"]


def test_duplicate_canonical_ids_are_not_shown_twice():
    fact = entry(
        "PRODUCT", {"name": "chocorramo", "presentation_value": 65, "presentation_unit": "g"}
    )
    service, _, _ = setup_details([fact, fact])
    result = service.get("P")
    assert len(result.commercial["products"]) == 1
    assert result.quality["canonical_fact_count"] == 1


def test_missing_persisted_opportunity_is_not_recalculated():
    service, _, _ = setup_details(stored=False)
    result = service.get("P")
    assert result.score is None
    assert result.opportunity_id is None
    assert not result.quality["opportunity_persisted"]


def test_literal_nonmatching_product_is_false_not_missing_or_semantic_recommendation():
    service, _, _ = setup_details([entry("PRODUCT", {"name": "microscopio"})])
    result = service.get("P")
    assert result.commercial_profile["product_match"] is False
    assert "profitability" not in asdict(result)


def test_policy_negative_and_performance_requirement_remain_distinct():
    entries = [
        entry("GUARANTEE_REQUIRED", {"state": "not_required", "subject": "policy"}),
        entry("GUARANTEE_REQUIRED", {"state": "required", "subject": "performance_guarantee"}),
    ]
    service, _, _ = setup_details(entries)
    result = service.get("P")
    assert len(result.requirements["guarantee_required"]) == 2
    assert result.commercial_profile["guarantee_required"] == "not_required"
    assert not result.quality["conflicts"]


def test_existing_discovery_reviews_are_preserved_and_json_serialization_works():
    service, stored, _ = setup_details(covarachia_entries())
    service.opportunities.get_by_process.return_value = replace(
        stored, review_required=True, review_notes=("Cierre por confirmar",)
    )
    result = service.get("P")
    assert result.review_required
    assert result.quality["conflicts"] == []
    assert result.quality["discovery_review_notes"] == ["Cierre por confirmar"]
    serialized = jsonable_encoder(result)
    assert serialized["process_id"] == str(result.process_id)
    assert serialized["commercial_profile"]["rup_required"] == "unknown"


def test_process_not_found_is_explicit():
    service, _, _ = setup_details()
    service.source.iter_processes.return_value = []
    with pytest.raises(ValueError, match="no encontrado"):
        service.get("P")


def test_real_eureka_repository_is_read_without_modifying_score_or_evaluation_timestamp():
    from datetime import UTC, datetime

    from sqlalchemy import create_engine, select, text
    from sqlalchemy.orm import sessionmaker

    from public_procurement.eureka.config import DEFAULT_CONFIG
    from public_procurement.eureka.domain.discovery import evaluate_process
    from public_procurement.eureka.repositories import (
        OpportunityRecord,
        SqlOpportunityQueries,
        SqlOpportunityRepository,
    )

    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
            OpportunityRecord.__table__.create(connection)
        sessions = sessionmaker(engine, expire_on_commit=False)
        process = facts(title="Refrigerios", base_price_cop=2080000)
        with sessions.begin() as session:
            SqlOpportunityRepository(session).save(
                evaluate_process(process, DEFAULT_CONFIG), datetime.now(UTC), {}
            )
        with sessions() as session:
            before = session.execute(select(OpportunityRecord.__table__)).one()
        source = Mock()
        source.iter_processes.return_value = [process]
        canonical = Mock()
        canonical.read.return_value = CanonicalInput(
            "consolidated", tuple(covarachia_entries()), (), 39
        )
        details = EurekaDetailsService(source, SqlOpportunityQueries(sessions), canonical).get("P")
        with sessions() as session:
            after = session.execute(select(OpportunityRecord.__table__)).one()
        assert after == before
        assert details.score == before.score
        assert details.opportunity_id == before.id
    finally:
        engine.dispose()


def test_scoring_optional_context_does_not_change_evaluation():
    from public_procurement.eureka.services import EurekaService

    process = facts(title="Refrigerios", base_price_cop=2080000)
    source = Mock()
    source.iter_processes.return_value = [process]
    canonical = Mock()
    canonical.read.return_value = CanonicalInput(
        "consolidated", tuple(covarachia_entries()), (), 39
    )
    plain = EurekaService(Mock(), source)
    enriched = EurekaService(Mock(), source, canonical=canonical)
    assert list(plain.evaluate(reference="P", dry_run=True)) == list(
        enriched.evaluate(reference="P", dry_run=True)
    )
    canonical.read.assert_not_called()
    assert plain.canonical_context("P") is None
    assert enriched.canonical_context("P").status == "consolidated"
