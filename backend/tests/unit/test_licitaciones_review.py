"""Review propagation uses stored annotations, never another extraction or scoring path."""

import copy
import uuid
from datetime import UTC, date, datetime
from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_procurement.eureka.adapters.radar_pipeline import ExistingRadarPipeline
from public_procurement.eureka.domain.radar import AlertDecision
from public_procurement.eureka.radar_repositories import (
    COUNTERS,
    RadarRunProcessRecord,
    RadarRunRecord,
    SqlRadarRepository,
)
from public_procurement.extraction.services import StructuredExtractionService
from public_procurement.licitaciones_cdp import services as operation
from public_procurement.licitaciones_cdp.review import combine_document_reviews

from .test_licitaciones_operations import candidate, service


def prior(review, *, manual=True, warnings=None):
    return {
        "run_id": "first-run",
        "result": {
            "requires_manual_document_review": manual,
            "document_review": review,
            "warnings": warnings or [],
        },
    }


@pytest.mark.parametrize(
    ("flag", "reason"),
    [
        ("suspicious_fact", "suspicious_facts"),
        ("ocr_truncated", "ocr_truncated"),
        ("partial_document_coverage", "partial_document_coverage"),
        ("extraction_failed", "extraction_failed"),
        ("unsupported_format", "unsupported_format"),
        ("missing_documents", "missing_documents"),
        ("missing_selected_documents", "missing_documents"),
        ("missing_required_documents", "missing_documents"),
        ("document_download_failed", "document_download_failed"),
    ],
)
def test_reused_warnings_survive_empty_facts_and_clean_current_flags(monkeypatch, flag, reason):
    current = {flag: False, "facts": []}
    svc, repo, pipeline = service(monkeypatch, [candidate()], flags=current)
    repo.review_history = [prior({flag: True})]
    saved = copy.deepcopy(repo.review_history)
    run = svc.run()
    item = next(iter(repo.items.values()))
    assert item["requires_manual_document_review"]
    assert reason in item["manual_review_reasons"]
    assert item["document_review"]["facts"] == []
    assert item["manual_review_provenance"][0]["origin"] == "persisted_cdp_run"
    assert item["manual_review_provenance"][0]["run_id"] == "first-run"
    assert run["metrics"]["manual_review"] == 1
    assert run["metrics"]["extraction_attempted"] == 0
    assert run["alerts_created"] == 1  # No new commercial gate.
    assert repo.alerts[0].review_required
    assert repo.review_history == saved
    assert current == {flag: False, "facts": []}
    pipeline.structured.extract.assert_not_called()
    pipeline.consolidation.run.assert_not_called()
    pipeline.extraction.extract_process.assert_not_called()


def test_new_suspicious_fact_annotation_alone_requires_review(monkeypatch):
    facts = [{"id": "fact-1", "suspicious": True, "document_version_id": "version-1"}]
    svc, repo, _ = service(monkeypatch, [candidate()], flags={"facts": facts})
    svc.run()
    item = next(iter(repo.items.values()))
    assert item["requires_manual_document_review"]
    assert item["manual_review_reasons"] == ["suspicious_facts"]
    assert item["document_review"]["facts"] == facts
    assert item["manual_review_provenance"][0]["fact_ids"] == ["fact-1"]


def test_clean_reuse_stays_clean(monkeypatch):
    svc, repo, _ = service(monkeypatch, [candidate()], flags={"facts": []})
    repo.review_history = [prior({"facts": [], "suspicious_fact": False}, manual=False)]
    run = svc.run()
    item = next(iter(repo.items.values()))
    assert not item.get("requires_manual_document_review", False)
    assert item["manual_review_reasons"] == []
    assert item["manual_review_provenance"] == []
    assert run["metrics"]["manual_review"] == 0
    assert run["status"] == "completed"


def test_later_empty_review_does_not_erase_persisted_cmi_annotations():
    facts = [
        {"id": f"fact-{i}", "document_version_id": "v1", "suspicious": i < 6} for i in range(33)
    ]
    canonicals = [{"id": f"canonical-{i}"} for i in range(13)]
    persisted = {"facts": facts, "canonicals": canonicals}
    before = copy.deepcopy(persisted)
    first = prior({"facts": facts, "suspicious_fact": True})
    second = prior({"facts": [], "suspicious_fact": False}, manual=False)
    second["run_id"] = "second-run"
    combined = combine_document_reviews(
        {"facts": [], "suspicious_fact": False}, [first, second], current_run_id="offline"
    )
    assert combined["suspicious_fact"]
    assert combined["manual_review_reasons"] == ["suspicious_facts"]
    assert combined["facts"] == []
    assert len(combined["manual_review_provenance"][0]["fact_ids"]) == 6
    assert persisted == before
    assert len(facts) == 33
    assert len(canonicals) == 13


def test_canonical_reuse_propagates_review_without_sync_ocr_or_duplicate_facts(monkeypatch):
    svc, repo, fake_pipeline = service(monkeypatch, [candidate()], flags={"facts": []})
    persisted_facts = [
        {"id": str(i), "document_version_id": "v1", "suspicious": i < 6} for i in range(33)
    ]
    persisted_canonicals = [str(i) for i in range(13)]
    repo.review_history = [prior({"suspicious_fact": True, "facts": persisted_facts})]
    services = [Mock() for _ in range(8)]
    services[1].get_process.return_value = Mock()
    services[7].get.return_value = fake_pipeline.enrich.return_value
    pipeline = ExistingRadarPipeline(*services)
    svc.pipeline_factory = lambda *args: pipeline
    before = copy.deepcopy((persisted_facts, persisted_canonicals))
    run = svc.run()
    item = next(iter(repo.items.values()))
    assert item["requires_manual_document_review"]
    assert item["manual_review_reasons"] == ["suspicious_facts"]
    assert item["document_review"]["facts"] == []
    assert run["metrics"]["extraction_attempted"] == 0
    assert (persisted_facts, persisted_canonicals) == before
    services[2].sync.assert_not_called()
    services[2].download.assert_not_called()
    services[3].extract_process.assert_not_called()
    services[4].extract.assert_not_called()
    services[5].run.assert_not_called()
    services[6].evaluate.assert_not_called()


def test_previous_document_warning_without_facts_keeps_reason_and_provenance():
    history = [prior({}, warnings=[{"code": "required_attachment_unavailable"}])]
    combined = combine_document_reviews({"facts": []}, history, current_run_id="current")
    assert combined["manual_review_reasons"] == ["required_attachment_unavailable"]
    assert combined["manual_review_provenance"][0]["run_id"] == "first-run"


def test_persisted_document_warning_is_visible_in_process_summary(monkeypatch):
    svc, repo, _ = service(monkeypatch, [candidate()], flags={"facts": []})
    repo.review_history = [prior({}, warnings=[{"code": "required_attachment_unavailable"}])]
    run = svc.run()
    item = next(iter(repo.items.values()))
    assert item["requires_manual_document_review"]
    assert run["metrics"]["manual_review"] == run["metrics"]["process_warnings"] == 1
    assert item["warnings"][0]["code"] == "required_attachment_unavailable"


@pytest.mark.parametrize("create", [False, True])
def test_persisted_manual_review_changes_neither_commercial_decision_nor_score(monkeypatch, create):
    svc, repo, pipeline = service(monkeypatch, [candidate()])
    repo.review_history = [prior({"ocr_truncated": True})]
    details = pipeline.enrich.return_value
    original = AlertDecision(
        create, True, "high", False, [{"code": "commercial_evidence"}], {"score": 65}
    )
    evaluate = Mock(return_value=original)
    monkeypatch.setattr(operation, "evaluate_source_alert", evaluate)
    run = svc.run()
    item = next(iter(repo.items.values()))
    assert item["decision"]["create"] is create
    assert item["decision"]["confirmed"]
    assert item["decision"]["priority"] == "high"
    assert item["decision"]["reasons"] == [{"code": "commercial_evidence"}]
    assert item["decision"]["snapshot"]["score"] == details.score == 65
    assert run["metrics"]["commercially_eligible"] == int(create)
    assert item["decision"]["review_required"]
    assert evaluate.call_args.args[1] is details


def test_current_fact_filter_is_empty_when_reused_scope_has_no_fragments(monkeypatch):
    # limit_to_synced scope has not been populated because canonical_reused skips sync.
    content = Mock()
    content.documents.process_id.return_value = uuid.uuid4()
    content.content_for_process.return_value = (content.documents.process_id.return_value, [])
    sessions = MagicMock()
    repository = Mock()
    repository.list_facts.return_value = [
        Mock(source_locator={"sources": [{"content_fragment_id": str(i)}]}) for i in range(33)
    ]
    monkeypatch.setattr(
        "public_procurement.extraction.services.SqlStructuredRepository", lambda session: repository
    )
    assert StructuredExtractionService(sessions, content).list_facts("CMI") == []
    assert len(repository.list_facts.return_value) == 33
    content.extract_process.assert_not_called()


def test_history_read_is_scoped_read_only_and_keeps_earlier_warning_after_empty_review():
    engine = create_engine("sqlite://")
    with engine.begin() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        RadarRunRecord.__table__.create(c)
        RadarRunProcessRecord.__table__.create(c)
    repo = SqlRadarRepository(sessionmaker(engine, expire_on_commit=False))
    at = datetime(2026, 10, 21, tzinfo=UTC)
    ids = []
    for n, (source, reference, finished) in enumerate(
        [
            ("licitaciones_info_cdp", "CMI", True),
            ("licitaciones_info_cdp", "CMI", True),
            ("licitaciones_info_cdp", "CMI", False),
            ("socrata", "CMI", True),
            ("licitaciones_info_cdp", "other", True),
        ]
    ):
        run = {
            "id": uuid.uuid4(),
            "source": source,
            "started_at": at,
            "finished_at": at if finished else None,
            "status": "completed" if finished else "running",
            "start_date": date(2026, 10, 14),
            "before_date": date(2026, 10, 22),
            "regions": ["Boyacá"],
            "rule_version": "v1",
            "config_hash": "hash",
            "errors": [],
            **dict.fromkeys(COUNTERS, 0),
        }
        ids.append(run["id"])
        repo.start(run, {})
        repo.outcome(
            run["id"],
            {
                "dataset_id": "licitaciones",
                "secop_id": reference,
                "requires_manual_document_review": n == 0,
                "document_review": {"facts": [], "suspicious_fact": n == 0},
                "metadata": {"unneeded_raw_payload": "not-in-review-projection"},
            },
            at,
            False,
        )
    before = repo.get_run(ids[0])
    history = repo.document_review_history("licitaciones_info_cdp", "CMI", ids[2])
    assert {h["run_id"] for h in history} == {str(ids[0]), str(ids[1])}
    assert "not-in-review-projection" not in str(history)
    combined = combine_document_reviews({"facts": []}, history, current_run_id=str(ids[2]))
    assert combined["suspicious_fact"]
    assert repo.get_run(ids[0]) == before
    engine.dispose()
