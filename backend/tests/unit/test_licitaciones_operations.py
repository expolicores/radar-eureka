"""Operational integration tests: in-memory DB and fakes, never CDP or source HTTP."""

import copy
import uuid
from contextlib import nullcontext
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_procurement.documents.adapters.retry import RetryOnceDownloader
from public_procurement.documents.services import AcquisitionError
from public_procurement.eureka.domain.radar import AlertDecision
from public_procurement.eureka.radar_repositories import (
    AlertRecord,
    RadarProcessStateRecord,
    RadarRunProcessRecord,
    RadarRunRecord,
    SqlRadarRepository,
)
from public_procurement.ingestion.services import canonical_process_identity
from public_procurement.licitaciones_cdp import api
from public_procurement.licitaciones_cdp import services as operation
from public_procurement.shared.config import Settings


def candidate(n=1, **changes):
    return {
        "process_reference": f"licitaciones_info:1086005:{n}",
        "id_contrato": str(n),
        "id_ultima_fase": f"CO1.NTC.{n}",
        "codigo_proceso": f"P-{n}",
        "object": "Compra de refrigerios y papeleria",
        "entity_name": "Entidad",
        "department": "Boyacá",
        "municipality": "Tunja",
        "published_at": "2026-10-20T12:00:00",
        "deadline_at": "2026-10-23T09:00:00-05:00",
        "provider_status": "Published",
        "validity_status": "open",
        "validity_warning": None,
        "recent": True,
        "amount": "7000000",
        "id_fuente_contract": "3",
        "key_config": "secop2",
        "raw_source_reference": {
            "Link": f"https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.{n}"
        },
        **changes,
    }


class FakeRepository:
    def __init__(self):
        self.items, self.alerts = {}, []
        self.review_history = []

    def lock(self):
        return nullcontext()

    def start(self, run, snapshot):
        self.current = run

    def finish(self, run):
        self.current = run

    def outcome(self, run_id, item, at, update):
        self.items[item["secop_id"]] = copy.deepcopy(item)

    def alert_for_canonical(self, key):
        return None

    def document_review_history(self, source, reference, exclude_run_id):
        assert source == "licitaciones_info_cdp"
        assert reference.startswith("licitaciones_info:1086005:")
        return copy.deepcopy(self.review_history)

    def alert(self, run_id, opp, version, decision, at):
        self.alerts.append(decision)
        return True


class FakeSource:
    def __init__(self, rows, error=None, flags=None):
        self.rows, self.error, self.flags = rows, error, flags or {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def discover(self):
        if self.error:
            raise self.error
        return {"processes": self.rows}, {
            "total_rows_received": len(self.rows),
            "queries": [],
            "warnings": [],
            **{
                k: len(self.rows)
                for k in (
                    "unique_processes_total",
                    "unique_processes_recent",
                    "secop_ii_total",
                    "secop_ii_recent",
                    "secop_ii_open",
                )
            },
            "secop_ii_closed": 0,
            "secop_ii_unknown": 0,
            "provider_status_deadline_conflicts": 0,
        }

    def review(self, *args):
        return self.flags


def service(monkeypatch, rows, *, flags=None, error=None):
    repo = FakeRepository()
    source = FakeSource(rows, error, flags)
    pipeline = Mock()
    pipeline.enrich.return_value = SimpleNamespace(
        process_id=uuid.uuid4(),
        opportunity_id=uuid.uuid4(),
        enrichment_status="consolidated",
        score=65,
        quality={},
    )
    # Only isolate the already-tested commercial decision, not duplicate its rules here.
    monkeypatch.setattr(
        operation,
        "evaluate_source_alert",
        lambda *a: AlertDecision(True, True, "high", False, [], {}),
    )
    settings = Settings(database_url="sqlite://", _env_file=None)
    return (
        operation.LicitacionesInfoRunService(
            repo, settings, lambda observer: source, lambda *a: pipeline
        ),
        repo,
        pipeline,
    )


def test_recent_open_reaches_shared_pipeline_independently_of_source(monkeypatch):
    rows = [
        candidate(),
        candidate(2, validity_status="closed"),
        candidate(3, validity_status="unknown"),
        candidate(4, recent=False),
        candidate(5, id_fuente_contract="1", key_config="secop1"),
    ]
    svc, repo, pipeline = service(monkeypatch, rows)
    run = svc.run()
    assert pipeline.enrich.call_count == 2
    assert len(repo.items) == 5
    assert len(repo.alerts) == 2
    assert repo.alerts[0].snapshot["source"] == "licitaciones_info_cdp"
    assert repo.alerts[0].snapshot["canonical_identity"] == "secop:CO1.NTC.1"
    assert run["metrics"]["alerts_created"] == 2
    assert {i.get("reason") for i in repo.items.values()} >= {
        "validity_closed",
        "validity_unknown",
        "stale",
    }


@pytest.mark.parametrize(
    "flag",
    ["partial_document_coverage", "suspicious_fact", "missing_documents", "extraction_failed"],
)
def test_quality_flags_require_manual_review_without_blocking_alert(monkeypatch, flag):
    svc, repo, _ = service(
        monkeypatch, [candidate()], flags={flag: True, "facts": [{"evidence_text": "original"}]}
    )
    run = svc.run()
    assert run["status"] == "completed_with_warnings"
    assert repo.alerts[0].review_required
    assert repo.alerts[0].snapshot[flag]
    assert run["metrics"]["manual_review"] == 1
    assert run["metrics"]["process_warnings"] == 1
    assert (
        next(iter(repo.items.values()))["document_review"]["facts"][0]["evidence_text"]
        == "original"
    )


@pytest.mark.parametrize(
    "code", ["session_expired", "cdp_unavailable", "invalid_tab", "profile_unavailable"]
)
def test_session_failure_stops_without_pipeline_and_has_manual_instruction(monkeypatch, code):
    error = RuntimeError("secret provider body")
    error.code = code
    svc, _repo, pipeline = service(monkeypatch, [], error=error)
    run = svc.run()
    assert run["status"] == "session_unavailable"
    assert "inicia sesión" in run["metrics"]["instruction"]
    assert "secret" not in str(run)
    assert run["errors"][0]["generated_at"]
    assert run["errors"][0]["run_id"] == str(run["id"])
    pipeline.enrich.assert_not_called()


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("insufficient_secop_sample", "inconclusive"),
        ("insufficient_enriched_rows", "unhealthy_response"),
        ("invalid_response", "unhealthy_response"),
        ("generic_dataset", "unhealthy_response"),
    ],
)
def test_preflight_quality_failure_is_visible_without_login_or_pipeline(monkeypatch, code, status):
    from public_procurement.licitaciones_cdp.adapters import SourceUnavailableError

    quality = {"preflight_status": status, "reason": code, "rows_total": 30}
    error = SourceUnavailableError(code, quality)
    svc, _repo, pipeline = service(monkeypatch, [], error=error)
    run = svc.run()
    assert run["status"] == "failed"
    assert run["metrics"]["preflight"] == quality
    assert "instruction" not in run["metrics"]
    assert run["errors"][0]["code"] == code
    pipeline.enrich.assert_not_called()


def test_process_failure_is_isolated_and_next_process_completes(monkeypatch):
    svc, repo, pipeline = service(monkeypatch, [candidate(), candidate(2)])
    success = pipeline.enrich.return_value
    pipeline.enrich.side_effect = [ValueError("document download"), success]
    run = svc.run()
    assert run["failures"] == 1
    assert run["alerts_created"] == 1
    assert len(repo.items) == 2
    assert run["metrics"]["process_errors"] == 1
    assert run["errors"][0]["codigo_proceso"] == "P-1"
    assert run["status"] == "completed_with_warnings"


def test_warning_generation_is_recorded_separately_for_each_run(monkeypatch):
    svc, repo, _ = service(monkeypatch, [candidate()], flags={"suspicious_fact": True})
    first_at = datetime(2026, 10, 21, 23, 42, 16, tzinfo=UTC)
    svc.clock = lambda: first_at
    first = copy.deepcopy(svc.run())
    from datetime import timedelta

    svc.clock = lambda: first_at + timedelta(minutes=10)
    second = svc.run()
    a = first["metrics"]["process_warning_details"][0]
    b = second["metrics"]["process_warning_details"][0]
    assert a["generated_at"] != b["generated_at"]
    assert a["run_id"] == str(first["id"])
    assert b["run_id"] == str(second["id"])
    assert a["process_identity"] == b["process_identity"] == "secop:CO1.NTC.1"
    assert (
        repo.items["licitaciones_info:1086005:1"]["warnings"][0]["generated_at"]
        == b["generated_at"]
    )


@pytest.mark.parametrize("code", ["unsupported_format", "extraction_failed"])
def test_extraction_exception_marks_manual_review_and_exposes_summary_error(monkeypatch, code):
    svc, repo, pipeline = service(monkeypatch, [candidate()])
    error = RuntimeError("private provider content")
    error.code = code

    def enrich(record, stage):
        stage("extraction_partial")
        raise error

    pipeline.enrich.side_effect = enrich
    run = svc.run()
    item = next(iter(repo.items.values()))
    assert item["requires_manual_document_review"]
    assert item["document_review"]["extraction_failed"]
    assert run["metrics"]["manual_review"] == 1
    assert run["metrics"]["process_errors"] == 1
    assert run["errors"][0]["code"] == code
    assert "private provider" not in str(run)
    assert run["status"] == "completed_with_warnings"


def test_failed_and_partial_results_have_separate_counters_and_do_not_gate_alert(monkeypatch):
    svc, repo, pipeline = service(monkeypatch, [candidate()])

    def factory(source, event):
        success = pipeline.enrich.return_value

        def enrich(record, stage):
            stage("extraction")
            event(
                "extraction_result",
                {
                    "succeeded": False,
                    "status": "failed",
                    "error_code": "unsupported_format",
                    "document_version_id": "failed-document",
                },
            )
            event(
                "extraction_result",
                {
                    "succeeded": True,
                    "status": "partial_text",
                    "coverage_complete": False,
                    "ocr": "ocr_truncated",
                    "document_version_id": "partial-document",
                },
            )
            return success

        pipeline.enrich.side_effect = enrich
        return pipeline

    svc.pipeline_factory = factory
    run = svc.run()
    metrics = run["metrics"]
    assert metrics["extraction_attempted"] == 2
    assert metrics["extraction_succeeded"] == metrics["extracted"] == 1
    assert metrics["extraction_failed"] == 1
    assert metrics["process_errors"] == metrics["process_warnings"] == 1
    assert metrics["manual_review"] == 1
    assert run["status"] == "completed_with_warnings"
    assert repo.alerts[0].review_required
    assert repo.alerts[0].snapshot["extraction_failed"]
    assert run["alerts_created"] == 1
    assert {e["code"] for e in run["errors"]} == {"unsupported_format"}
    assert any(e["code"] == "ocr_truncated" for e in metrics["process_warning_details"])


def test_failed_result_without_usable_text_never_counts_as_success(monkeypatch):
    svc, _repo, pipeline = service(monkeypatch, [candidate()])

    def factory(source, event):
        def enrich(record, stage):
            stage("extraction")
            event(
                "extraction_result",
                {"succeeded": False, "status": "failed", "error_code": "unsupported_format"},
            )
            stage("extraction_partial")
            raise ValueError("sin evidencia útil")

        pipeline.enrich.side_effect = enrich
        return pipeline

    svc.pipeline_factory = factory
    run = svc.run()
    assert run["metrics"]["extraction_attempted"] == 1
    assert run["metrics"]["extraction_failed"] == 1
    assert run["metrics"]["extraction_succeeded"] == run["metrics"]["extracted"] == 0
    assert run["metrics"]["process_errors"] == 1
    assert run["alerts_created"] == 0


def test_duplicate_remains_in_run_without_second_pipeline_or_alert(monkeypatch):
    svc, repo, pipeline = service(monkeypatch, [candidate()])
    repo.alert_for_canonical = lambda key: {"id": uuid.uuid4()}
    run = svc.run()
    assert len(repo.items) == 1
    assert next(iter(repo.items.values()))["reason"] == "duplicate_canonical"
    assert run["metrics"]["duplicate_alerts_skipped"] == 1
    assert run["metrics"]["alert_candidates"] == 1
    pipeline.enrich.assert_not_called()


@pytest.mark.parametrize("first_source", ["socrata", "licitaciones_info_cdp"])
def test_atomic_global_alert_identity_in_both_directions(first_source):
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS eureka"))
        for model in (RadarRunRecord, RadarProcessStateRecord, RadarRunProcessRecord, AlertRecord):
            model.__table__.create(connection)
    repo = SqlRadarRepository(sessionmaker(engine, expire_on_commit=False))
    first = canonical_process_identity(
        "CO1.REQ.999", "https://community.secop.gov.co/Public/?noticeUID=CO1.NTC.123"
    )
    second = canonical_process_identity("CO1.NTC.123")
    assert first == second
    decision = AlertDecision(
        True, True, "high", False, [], {"canonical_identity": first, "source": first_source}
    )
    now = datetime.now(UTC)
    assert repo.alert(uuid.uuid4(), uuid.uuid4(), "v1", decision, now)
    other = "licitaciones_info_cdp" if first_source == "socrata" else "socrata"
    decision = AlertDecision(
        True, True, "high", False, [], {"canonical_identity": second, "source": other}
    )
    assert not repo.alert(uuid.uuid4(), uuid.uuid4(), "v2", decision, now)
    assert repo.alerts(1, 25)["total"] == 1
    assert repo.alerts(1, 25)["items"][0]["source"] == first_source
    engine.dispose()


def test_exact_identity_namespaces_provider_ids_and_never_guesses_req():
    assert canonical_process_identity("CO1.NTC.123") == "secop:CO1.NTC.123"
    assert canonical_process_identity("CO1.REQ.123") == "secop:CO1.REQ.123"
    record = operation.source_record(candidate(id_ultima_fase=None, raw_source_reference={}))
    assert record.id_del_proceso == "licitaciones_info:1086005:1"
    assert canonical_process_identity(record.id_del_proceso) == "licitaciones_info:1086005:1"


def test_source_factory_reuses_shared_pipeline_and_bounded_document_service():
    from public_procurement.eureka.adapters.radar_pipeline import ExistingRadarPipeline
    from public_procurement.eureka.services import build_source_pipeline

    settings = Settings(database_url="sqlite://", _env_file=None)
    inventory = Mock()
    pipeline = build_source_pipeline(sessionmaker(create_engine("sqlite://")), settings, inventory)
    assert isinstance(pipeline, ExistingRadarPipeline)
    assert pipeline.documents.inventory is inventory
    assert pipeline.documents.limit_to_synced
    assert pipeline.extraction.documents.documents is pipeline.documents
    assert pipeline.structured.content is pipeline.extraction
    assert pipeline.extraction.ocr.policy.max_ocr_pages <= 20


def test_manual_runner_waits_for_persisted_start_without_auto_execution():
    from public_procurement.licitaciones_cdp.background import ManualCdpRunner

    factory = Mock()

    def run(identifier, on_started):
        on_started({"id": identifier, "status": "running"})

    factory.return_value.run.side_effect = run
    runner = ManualCdpRunner(Mock(), Mock(), factory)
    factory.assert_not_called()
    assert runner.start()["status"] == "running"
    factory.assert_called_once()
    runner.close()
    with pytest.raises(RuntimeError, match="cerrando"):
        runner.start()


def test_single_transient_download_retry_and_permanent_error_no_retry():
    delegate, wait = Mock(), Mock()
    delegate.download.side_effect = [AcquisitionError("network_error", "network"), "binary"]
    assert RetryOnceDownloader(delegate, wait).download("source", "storage") == "binary"
    wait.assert_called_once_with(4)
    delegate.download.side_effect = AcquisitionError("http_error", "401")
    delegate.reset_mock()
    with pytest.raises(AcquisitionError):
        RetryOnceDownloader(delegate, wait).download("s", "t")
    assert delegate.download.call_count == 1


def test_operational_endpoints_read_and_manual_start_without_live_worker():
    app = FastAPI()
    app.include_router(api.router)
    identifier = uuid.uuid4()
    app.state.manual_cdp_runner = Mock()
    app.state.manual_cdp_runner.start.return_value = {"id": identifier, "status": "running"}
    app.state.cdp_queries = Mock()
    run = {
        "id": identifier,
        "source": "licitaciones_info_cdp",
        "status": "session_unavailable",
        "started_at": datetime.now(UTC),
        "metrics": {"instruction": operation.SESSION_HELP},
        "errors": [],
    }
    app.state.cdp_queries.runs.return_value = {
        "items": [run],
        "page": 1,
        "page_size": 25,
        "total": 1,
    }
    app.state.cdp_queries.get_run.return_value = run
    with TestClient(app) as client:
        assert client.post("/api/eureka/licitaciones-cdp/runs").status_code == 202
        assert client.get("/api/eureka/licitaciones-cdp/runs").json()["total"] == 1
        assert (
            client.get(f"/api/eureka/licitaciones-cdp/runs/{identifier}").json()["source"]
            == "licitaciones_info_cdp"
        )
        app.state.manual_cdp_runner.start.side_effect = RuntimeError("Ya activa")
        assert client.post("/api/eureka/licitaciones-cdp/runs").status_code == 409
