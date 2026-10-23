import copy
import json
from dataclasses import replace

import pytest

from public_procurement.eureka.domain.radar import AlertDecision
from public_procurement.eureka.metadata_alert_policy import (
    DEFAULT_POLICY_PATH,
    apply_metadata_alert_exclusions,
    load_metadata_alert_exclusions,
)
from public_procurement.eureka.radar_config import load_radar_config
from public_procurement.shared.config import Settings

from .test_affinity import details, process
from .test_radar import run, setup


@pytest.fixture
def config():
    return load_radar_config(
        Settings(database_url="sqlite://", _env_file=None).eureka_radar_config_path
    )


def decision(**changes):
    return replace(
        AlertDecision(
            True,
            False,
            "medium",
            True,
            [],
            {
                "evidence_level": "metadata_only",
                "document_status": "unavailable",
                "score": 35,
            },
        ),
        **changes,
    )


def provisional_details():
    normal = details()
    return replace(
        normal,
        enrichment_status="documents_unavailable",
        quality={"document_status": "unavailable"},
        evidence={},
        commercial={**normal.commercial, "products": [], "purchase_items": [], "unspsc": []},
    )


@pytest.mark.parametrize(
    ("text", "term"),
    [
        ("PRESTAR EL SERVICIO DE TRANSPORTE TERRESTRE", "transporte"),
        ("SISTEMAS DE ACUEDUCTO URBANO Y RURALES", "acueducto"),
        ("ARRENDAMIENTO DE ESPACIO FÍSICO", "arrendamiento"),
        ("PLANTA DE TRATAMIENTO DE AGUA POTABLE", "agua potable"),
        ("  TrÁnsPÓrTe   terrestre ", "transporte"),
        ("AGUA\n  PÓTABLE", "agua potable"),
        ("ACUEDUCTO y AGUA POTABLE", "agua potable"),
    ],
)
def test_metadata_only_candidate_matches_normalized_object(text, term):
    original = decision()
    result = apply_metadata_alert_exclusions(
        original,
        source="socrata",
        object_text=text,
        policy=load_metadata_alert_exclusions(DEFAULT_POLICY_PATH),
    )
    assert not result.create
    assert original.create
    assert result.snapshot["score"] == original.snapshot["score"]
    assert result.snapshot["metadata_exclusion_term"] == term
    assert result.reasons[-1]["code"] == "metadata_object_exclusion"


@pytest.mark.parametrize(
    "text", ["Compra de papelería y oficina", "Refrigerios", "Ferretería", "Tecnología"]
)
def test_no_match_preserves_original_decision(text):
    original = decision()
    assert (
        apply_metadata_alert_exclusions(
            original,
            source="socrata",
            object_text=text,
            policy=load_metadata_alert_exclusions(DEFAULT_POLICY_PATH),
        )
        is original
    )


@pytest.mark.parametrize(
    ("source", "changes"),
    [
        ("licitaciones_info_cdp", {}),
        ("other_source", {}),
        ("socrata", {"confirmed": True}),
        ("socrata", {"create": False}),
        (
            "socrata",
            {"snapshot": {"evidence_level": "document_confirmed", "document_status": "available"}},
        ),
    ],
)
def test_policy_never_intervenes_outside_provisional_socrata_alert(source, changes):
    original = decision(**changes)
    # Invalid config also cannot interfere with another source or a documentary decision.
    assert (
        apply_metadata_alert_exclusions(
            original, source=source, object_text="transporte", policy=None
        )
        is original
    )


def test_disabled_policy_and_editable_json(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"version": 1, "enabled": False, "terms": ["transporte"]}))
    original = decision()
    assert (
        apply_metadata_alert_exclusions(
            original,
            source="socrata",
            object_text="transporte",
            policy=load_metadata_alert_exclusions(path),
        )
        is original
    )
    path.write_text(json.dumps({"version": 1, "enabled": True, "terms": ["prueba"]}))
    assert load_metadata_alert_exclusions(path).match("PRUEBA") == "prueba"


@pytest.mark.parametrize(
    "raw",
    [
        "{",
        '{"version":2,"enabled":true,"terms":[]}',
        '{"version":1,"enabled":"false","terms":["transporte"]}',
        '{"version":1,"enabled":true,"terms":[""]}',
        '{"version":1,"enabled":true,"terms":[42]}',
    ],
)
def test_invalid_json_is_not_silently_disabled(tmp_path, raw):
    path = tmp_path / "policy.json"
    path.write_text(raw)
    with pytest.raises(ValueError, match=r".+"):
        load_metadata_alert_exclusions(path)


def test_exclusion_is_only_at_alert_boundary_and_preserves_outcome_score_and_future_docs(config):
    service, repo, pipeline = setup(config)
    pipeline.enrich.return_value = provisional_details()
    record = replace(
        process(), title="Compra de papelería", description="Papelería para transporte"
    )
    report = run(service, [record])
    item = report["items"][0]
    assert len(repo.outcomes) == 1
    assert not repo.alerts
    assert report["metrics"]["metadata_alerts_excluded_by_object"] == 1
    assert item["reason"] == "metadata_object_exclusion"
    assert item["metadata_exclusion_term"] == "transporte"
    assert item["decision"]["snapshot"]["score"] == details().score
    assert item["stage"] == "documents_pending"
    assert item["retryable"]
    assert repo.states[record.identity]["status"] == "pending_documents"
    assert report["metrics"]["metadata_alert_exclusions"][0]["process_identity"]
    pipeline.enrich.return_value = details()
    later = run(service, [record])
    assert later["alerts_created"] == 1
    assert later["metrics"]["metadata_alerts_excluded_by_object"] == 0
    assert later["items"][0]["decision"]["confirmed"]


def test_entity_and_other_metadata_do_not_trigger_object_exclusion(config):
    service, _repo, pipeline = setup(config)
    pipeline.enrich.return_value = provisional_details()
    record = replace(
        process(),
        entity_name="Empresa de transporte y acueducto",
        title="ARRENDAMIENTO",
        description="Compra de papelería",
    )
    report = run(service, [record])
    assert report["alerts_created"] == 1
    assert report["metrics"]["metadata_alerts_excluded_by_object"] == 0


def test_invalid_config_blocks_only_provisional_candidates_explicitly(config, tmp_path):
    service, repo, pipeline = setup(config)
    path = tmp_path / "invalid.json"
    path.write_text("{")
    service.metadata_exclusion_path = path
    pipeline.enrich.return_value = provisional_details()
    report = run(service, [process()])
    assert not repo.alerts
    assert report["items"][0]["reason"] == "metadata_exclusion_policy_invalid"
    assert report["metrics"]["metadata_exclusion_policy_errors"] == 1
    assert report["metrics"]["metadata_alerts_excluded_by_object"] == 0
    assert report["items"][0]["decision"]["snapshot"]["score"] == details().score
    pipeline.enrich.return_value = details()
    assert run(service, [process()])["alerts_created"] == 1


def test_excluded_process_still_appears_in_review_with_readable_reason():
    from .test_human_review import observation, service

    obs = observation(source="socrata")
    result = apply_metadata_alert_exclusions(
        decision(),
        source="socrata",
        object_text="transporte",
        policy=load_metadata_alert_exclusions(DEFAULT_POLICY_PATH),
    )
    from dataclasses import asdict

    obs["result"].update(
        reason="metadata_object_exclusion", outcome="no_alert", decision=asdict(result)
    )
    svc, repo, _ = service([obs])
    before = copy.deepcopy(repo.data["observations"])
    row = svc.list({})["items"][0]
    assert row["no_alert_reason"] == "Alerta provisional excluida por objeto: transporte"
    assert row["score"] == 35
    assert not row["has_alert"]
    assert repo.data["observations"] == before
