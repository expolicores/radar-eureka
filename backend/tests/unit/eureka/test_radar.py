from contextlib import nullcontext
from dataclasses import replace
from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest

from public_procurement.eureka.radar_config import load_radar_config
from public_procurement.eureka.radar_services import RadarService
from public_procurement.shared.config import Settings

from .test_affinity import details, process


@pytest.fixture
def config():
    return load_radar_config(
        Settings(database_url="postgresql://unused", _env_file=None).eureka_radar_config_path
    )


class MemoryRepository:
    def __init__(self):
        self.states, self.alerts, self.outcomes, self.runs = {}, set(), [], []

    def lock(self):
        return nullcontext()

    def start(self, run, snapshot):
        self.runs.append(run)

    def state(self, dataset, secop_id):
        return self.states.get((dataset, secop_id))

    def claim(self, run_id, dataset, secop_id, at):
        key = dataset, secop_id
        self.states[key] = {
            "status": "processing",
            "attempts": self.states.get(key, {}).get("attempts", 0) + 1,
        }

    def stage(self, *args):
        pass

    def outcome(self, run_id, item, at, update_state):
        self.outcomes.append(item)
        if update_state:
            self.states[(item["dataset_id"], item["secop_id"])]["status"] = (
                "pending_documents"
                if item.get("document_status") == "unavailable"
                else "failed"
                if item["outcome"] == "failed" or item.get("coverage_incomplete")
                else "completed"
            )
            if item.get("document_status") == "unavailable":
                self.states[(item["dataset_id"], item["secop_id"])]["attempts"] = 0

    def finish(self, run):
        pass

    def alert(self, run_id, opportunity_id, version, decision, at):
        key = opportunity_id, version
        created = key not in self.alerts
        self.alerts.add(key)
        return created


def setup(config):
    repository, pipeline = MemoryRepository(), Mock()
    pipeline.enrich.return_value = pipeline.preview.return_value = details()
    pipeline.evidence.return_value = [
        {"document_version_id": "document", "source_locator": {"page_number": 3}}
    ]
    return RadarService(repository, pipeline, config, 30_000_000), repository, pipeline


def run(service, source, **kwargs):
    return service.run(
        source,
        start=date(2026, 10, 7),
        before=date(2026, 10, 14),
        regions=("Boyacá", "Casanare"),
        **kwargs,
    )


def test_review_admission_for_socrata_discards_never_reexecutes_the_pipeline(config):
    service, repo, pipeline = setup(config)
    service.clock = lambda: datetime(2026, 10, 10, tzinfo=UTC)
    original = repo.outcome

    def persist(run_id, item, at, claimed):
        original(run_id, item, at, claimed)
        if item.get("review_candidate"):
            item["review_entry"] = {"status": "new"}

    repo.outcome = persist
    records = [
        replace(
            process(),
            id_del_proceso="no_match",
            title="Servicio genérico",
            description=None,
            category_code=None,
        ),
        replace(
            process(),
            id_del_proceso="excluded",
            title="Interventoría general",
            description=None,
            category_code=None,
        ),
        replace(
            process(),
            id_del_proceso="deadline_only",
            title="Servicio genérico",
            description=None,
            category_code=None,
            offer_deadline_raw=None,
        ),
        replace(
            process(),
            id_del_proceso="commercial_unknown",
            title="Suministro de papelería",
            description=None,
            category_code=None,
            offer_deadline_raw=None,
        ),
    ]
    report = run(service, records)
    assert report["skipped"] == 4
    pipeline.enrich.assert_not_called()
    assert [i["review_candidate"] for i in report["items"]] == [False, False, False, True]
    assert report["metrics"]["review_candidates_total"] == 1
    assert report["metrics"]["review_new_entries"] == 1
    assert report["metrics"]["review_existing_entries"] == 0
    assert report["metrics"]["review_rejected_no_goods_intent"] == 2
    assert report["metrics"]["review_rejected_irrelevant_service"] == 1


def test_commercial_limit_deferred_can_enter_review_without_changing_pipeline_limit(config):
    service, _, pipeline = setup(config)
    service.clock = lambda: datetime(2026, 10, 10, tzinfo=UTC)
    result = run(
        service, [process(), replace(process(), id_del_proceso="deferred")], max_processes=1
    )
    assert result["status"] == "limited"
    assert result["items"][-1]["reason"] == "limit_deferred"
    assert result["items"][-1]["review_candidate"]
    pipeline.enrich.assert_called_once()


@pytest.mark.parametrize("status", ["dataset_lag", "no_rows_in_window", "diagnostic_failed"])
def test_empty_source_availability_is_nonfatal_and_does_not_persist_processes(config, status):
    service, repo, pipeline = setup(config)
    service.availability_diagnostic = Mock(return_value={"performed": True, "status": status})
    result = run(service, [])
    service.availability_diagnostic.assert_called_once_with(date(2026, 10, 7), date(2026, 10, 14))
    assert result["status"] == "completed"
    assert result["metrics"]["socrata_availability_diagnostic"]["status"] == status
    assert result["start_date"] == date(2026, 10, 7)
    assert result["before_date"] == date(2026, 10, 14)
    assert len(repo.runs) == 1
    assert repo.outcomes == []
    assert not pipeline.mock_calls


def test_diagnostic_exception_never_changes_completed(config):
    service, _, _ = setup(config)
    service.availability_diagnostic = Mock(side_effect=RuntimeError("secret"))
    result = run(service, [])
    assert result["status"] == "completed"
    assert result["failures"] == 0
    assert result["errors"] == []
    assert result["metrics"]["socrata_availability_diagnostic"]["status"] == "diagnostic_failed"
    assert "secret" not in str(result)


def test_nonempty_or_failed_or_dry_source_never_queries_availability(config):
    service, _, _ = setup(config)
    service.availability_diagnostic = Mock()
    run(service, [process()])
    run(service, [], dry_run=True)

    def broken():
        raise TimeoutError()
        yield  # pragma: no cover

    result = run(service, broken())
    assert result["status"] == "failed"
    service.availability_diagnostic.assert_not_called()


def test_new_seen_idempotence_and_explanations(config):
    service, repo, pipeline = setup(config)
    first = run(service, [process(), process()])
    second = run(service, [process()])
    assert (
        first["new_processes"]
        == first["candidates"]
        == first["enriched"]
        == first["alerts_created"]
        == 1
    )
    assert first["items"][0]["decision"]["snapshot"]["score"] == 65
    assert any(
        reason["code"] == "document_evidence" for reason in first["items"][0]["decision"]["reasons"]
    )
    assert second["alerts_created"] == second["new_processes"] == 0
    assert second["items"][0]["reason"] == "already_seen"
    assert pipeline.enrich.call_count == 1
    assert len(repo.alerts) == 1


def test_partial_failure_does_not_abort_and_failed_process_retries(config):
    service, repo, pipeline = setup(config)
    pipeline.enrich.side_effect = [ValueError("Download interrupted"), details()]
    first = run(service, [process(), replace(process(), id_del_proceso="second")])
    assert first["status"] == "partial"
    assert first["failures"] == 1
    assert first["alerts_created"] == 1
    pipeline.enrich.side_effect = None
    retry = run(service, [process()])
    assert retry["new_processes"] == 0
    assert retry["enriched"] == 1
    assert repo.states[process().identity]["attempts"] == 2


def test_metadata_only_alert_is_not_failure_and_later_documents_reuse_identity(config):
    service, repo, pipeline = setup(config)
    normal = details()
    provisional = replace(
        normal,
        enrichment_status="documents_unavailable",
        quality={"document_status": "unavailable"},
        evidence={},
        commercial={**normal.commercial, "products": [], "purchase_items": [], "unspsc": []},
    )
    pipeline.enrich.return_value = provisional
    record = replace(
        process(),
        id_del_proceso="CO1.REQ.11195961",
        department="Casanare",
        title=(
            "SUMINISTRO DE ELEMENTOS DE OFICINA; PAPELERÍA Y CONSUMIBLES DE IMPRESORAS "
            "PARA LA PERSONERÍA MUNICIPAL DE YOPAL."
        ),
        description=None,
        category_code=None,
    )
    for iteration in range(5):
        report = run(service, [record])
        assert report["status"] == "completed"
        assert report["failures"] == report["enriched"] == 0
        assert report["alerts_created"] == (1 if iteration == 0 else 0)
        item = report["items"][0]
        assert item["outcome"] == "alert"
        assert item["retryable"] is True
        assert item["decision"]["confirmed"] is False
        assert item["decision"]["snapshot"]["evidence_level"] == "metadata_only"
        assert repo.states[record.identity]["status"] == "pending_documents"
    pipeline.enrich.return_value = normal
    confirmed = run(service, [record])
    assert confirmed["enriched"] == 1
    assert confirmed["alerts_created"] == 0
    assert confirmed["items"][0]["decision"]["snapshot"]["evidence_level"] == "document_confirmed"
    assert repo.states[record.identity]["status"] == "completed"
    assert run(service, [record])["items"][0]["reason"] == "already_seen"


def test_actual_pipeline_empty_inventory_reaches_metadata_alert(config):
    from .test_radar_pipeline import build

    pipeline, services = build()
    normal = details()
    empty = replace(
        normal,
        enrichment_status="not_extracted",
        quality={},
        evidence={},
        commercial={**normal.commercial, "products": [], "purchase_items": [], "unspsc": []},
    )
    services[7].get.side_effect = [replace(empty, opportunity_id=None), empty]
    services[2].sync.return_value = []
    repository = MemoryRepository()
    radar = RadarService(repository, pipeline, config, 30_000_000)
    report = run(
        radar,
        [
            replace(
                process(),
                id_del_proceso="CO1.REQ.11195961",
                department="Casanare",
                title=(
                    "SUMINISTRO DE ELEMENTOS DE OFICINA; PAPELERÍA Y CONSUMIBLES DE IMPRESORAS "
                    "PARA LA PERSONERÍA MUNICIPAL DE YOPAL."
                ),
                description=None,
                category_code=None,
            )
        ],
    )
    assert report["alerts_created"] == 1
    assert report["failures"] == report["enriched"] == 0
    assert report["items"][0]["decision"]["snapshot"]["evidence_level"] == "metadata_only"
    services[2].sync.assert_called_once()
    services[3].extract_process.assert_not_called()


@pytest.mark.parametrize("raw", [None, "", "-", " \t ", "not-a-date"])
def test_invalid_deadline_is_traced_and_does_not_block_later_processes(config, raw):
    service, repo, pipeline = setup(config)
    events = []
    service.observer = lambda event, data: events.append((event, data))
    invalid = replace(process(), id_del_proceso="invalid-deadline", offer_deadline_raw=raw)
    report = run(service, [invalid, process()], max_processes=1)
    item = report["items"][0]
    assert item["reason"] == "missing_or_invalid_offer_deadline"
    assert item["field"] == "fecha_de_recepcion_de"
    assert item["raw_value"] == raw
    assert item["rule"] == "valid_offer_deadline_required"
    assert repo.outcomes[0] == item
    event = next(data for event, data in events if event == "process_result")
    assert event["raw_value"] == raw
    assert event["field"] == item["field"]
    assert event["rule"] == item["rule"]
    assert invalid.identity not in repo.states
    assert report["status"] == "completed"
    assert report["candidates"] == report["enriched"] == 1
    assert report["new_processes"] == 1
    assert not any(i.get("reason") == "limit_deferred" for i in report["items"])
    pipeline.enrich.assert_called_once()


def test_incomplete_ocr_can_alert_but_remains_retryable_without_changing_decision(config):
    service, repo, pipeline = setup(config)
    incomplete = replace(
        details(),
        quality={
            **details().quality,
            "extraction_coverage": {
                "coverage_complete": False,
                "documents": [{"diagnostics": {"status": "ocr_truncated", "omitted_pages": [21]}}],
            },
        },
    )
    pipeline.enrich.return_value = incomplete
    first = run(service, [process()])
    assert first["alerts_created"] == 1
    assert first["status"] == "partial"
    assert first["items"][0]["decision"]["snapshot"]["score"] == 65
    assert (
        first["items"][0]["decision"]["snapshot"]["extraction_coverage"]["coverage_complete"]
        is False
    )
    assert repo.states[process().identity]["status"] == "failed"
    pipeline.enrich.return_value = replace(
        incomplete, quality={"extraction_coverage": {"coverage_complete": True}}
    )
    second = run(service, [process()])
    assert second["enriched"] == 1
    assert second["alerts_created"] == 0
    assert repo.states[process().identity]["status"] == "completed"
    assert len(repo.alerts) == 1


def test_dry_run_no_writes_or_pipeline_and_unknown_enrichment_is_not_predicted(config):
    service, repo, pipeline = setup(config)
    report = run(service, [process()], dry_run=True)
    assert report["items"][0]["would_create_alert"]
    assert report["alerts_created"] == 0
    assert not repo.states
    assert not repo.runs
    assert not repo.alerts
    pipeline.enrich.assert_not_called()
    pipeline.preview.return_value = None
    report = run(service, [process()], dry_run=True)
    assert report["items"][0]["outcome"] == "pending_enrichment"


def test_outside_window_is_not_marked_seen_for_golden_window(config):
    service, repo, _ = setup(config)
    report = service.run(
        [process()], start=date(2026, 10, 13), before=date(2026, 10, 14), regions=("Boyacá",)
    )
    assert report["items"][0]["reason"] == "outside_window"
    assert not repo.states
    assert run(service, [process()])["alerts_created"] == 1
    outside = service.run(
        [process()], start=date(2026, 10, 13), before=date(2026, 10, 14), regions=("Boyacá",)
    )
    assert outside["items"][0]["reason"] == "outside_window"


def test_limits_do_not_starve_new_processes_behind_seen(config):
    service, _, _ = setup(config)
    run(service, [process()])
    report = run(
        service,
        [
            process(),
            replace(process(), id_del_proceso="next"),
            replace(process(), id_del_proceso="last"),
        ],
        max_processes=1,
    )
    assert report["candidates"] == 1
    assert report["status"] == "limited"
    assert report["items"][0]["reason"] == "already_seen"


def test_validation_capacity_covers_1872_rows_without_limit_deferred(config):
    service, _, pipeline = setup(config)
    # Unit capacity check only: synthetic metadata, no documents, database or provider.
    records = [
        replace(
            process(),
            id_del_proceso=f"capacity-{i}",
            title="Sin coincidencia",
            description=None,
            category_code=None,
        )
        for i in range(1872)
    ]
    report = run(service, records, max_processes=2500)
    assert report["processes_seen"] == 1872
    assert report["status"] == "completed"
    assert not any(item.get("reason") == "limit_deferred" for item in report["items"])
    pipeline.enrich.assert_not_called()


def test_exhausted_failures_and_source_failure_are_auditable(config):
    service, repo, pipeline = setup(config)
    repo.states[process().identity] = {"status": "failed", "attempts": config.max_attempts}
    assert run(service, [process()])["items"][0]["reason"] == "attempts_exhausted"
    pipeline.enrich.assert_not_called()

    def failing():
        yield replace(process(), id_del_proceso="other")
        raise RuntimeError("Socrata unavailable")

    report = run(service, failing())
    assert report["status"] == "failed"
    assert report["errors"]
