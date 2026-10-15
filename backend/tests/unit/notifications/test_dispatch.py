import copy
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.notifications.adapters.file import DevEmailSender
from public_procurement.notifications.domain.message import (
    DeliveryError,
    DeliveryReceipt,
    compose,
    recipient,
)
from public_procurement.notifications.repositories import (
    NotificationAlertRecord,
    NotificationRecord,
    SqlNotificationRepository,
)
from public_procurement.notifications.services import (
    DispatchPolicy,
    NotificationDispatcher,
    NotificationQueries,
    digest_window,
)

NOW = datetime(2026, 10, 14, 15, tzinfo=UTC)


def golden():
    return {
        "id": str(uuid.uuid4()),
        "opportunity_id": "6e94cc77-9f88-4f4c-bfb8-2e832976f4c0",
        "created_at": (NOW - timedelta(hours=1)).isoformat(),
        "priority": "high",
        "review_required": True,
        "reasons": [
            {"code": "confirmed_commercial_match", "concept": "Jugo Hit"},
            {"code": "review", "value": "Vigencia por confirmar"},
        ],
        "snapshot": {
            "secop_id": "CO1.REQ.11172521",
            "entity": "Institución Educativa Técnica San Luis Beltrán",
            "municipality": "Covarachía",
            "department": "Boyacá",
            "budget": 2080000,
            "score": 65,
            "execution_days": 5,
            "payment_days": 30,
            "guarantee_required": "not_required",
            "products": [
                {"name": "jugo hit", "presentation_value": 200, "presentation_unit": "ml"},
                {
                    "name": "chocorramo tradicional",
                    "presentation_value": 65,
                    "presentation_unit": "g",
                },
            ],
            "confirmed_matches": [{"label": "Refrigerios y bebidas"}],
        },
    }


class Source:
    def __init__(self, alerts):
        self.values = alerts
        self.calls = 0

    def alerts(self, alert_id, window):
        self.calls += 1
        return [
            copy.deepcopy(a)
            for a in self.values
            if (not alert_id or str(alert_id) == a["id"])
            and (not window or window[0] <= datetime.fromisoformat(a["created_at"]) < window[1])
        ]


class Sender:
    provider = "resend"
    scope = "real"
    idempotency_seconds = 86400

    def __init__(self):
        self.calls = []
        self.errors = []
        self.accepted = {}

    def send(self, payload, key):
        self.calls.append(copy.deepcopy(payload))
        if self.errors:
            raise self.errors.pop(0)
        self.accepted.setdefault(key, "provider:" + key)
        return DeliveryReceipt(self.accepted[key])


@pytest.fixture
def setup(tmp_path):
    engine = create_engine("sqlite://")
    with engine.connect() as c:
        c.execute(text("ATTACH DATABASE ':memory:' AS notifications"))
        NotificationRecord.__table__.create(c)
        NotificationAlertRecord.__table__.create(c)
    sessions = sessionmaker(engine, expire_on_commit=False)
    repo = SqlNotificationRepository(sessions)
    source = Source([golden()])
    sender = Sender()
    policy = DispatchPolicy(
        enabled=True, base_url="http://127.0.0.1:5173", sender="sender@example.invalid"
    )
    service = NotificationDispatcher(repo, source, sender, policy)
    yield service, repo, source, sender, sessions, tmp_path
    engine.dispose()


def run(service, **options):
    return service.run(["Reviewer@Example.invalid"], allow_real_send=True, now=NOW, **options)


def count(sessions, record=NotificationRecord):
    with sessions() as s:
        return len(list(s.scalars(select(record))))


def test_a_preparation_pending_snapshot(setup):
    service, repo, source, _, sessions, _ = setup
    a = source.values[0]
    payload = compose(
        [a], "reviewer@example.invalid", service.policy.base_url, "immediate", service.policy.sender
    )
    identifier = repo.prepare(
        [a], "reviewer@example.invalid", "real", "resend", "immediate", payload, NOW, None
    )
    assert repo.get(identifier)["status"] == "pending"
    assert count(sessions, NotificationAlertRecord) == 1


def test_b_success_is_provider_acceptance_and_history(setup):
    service, repo, _, sender, _, _ = setup
    report = run(service)
    assert report["sent"] == 1
    value = repo.get(report["items"][0]["id"])
    assert value["attempt_count"] == 1
    assert value["retry_count"] == 0
    assert value["attempt_history"][0]["result"] == "sent"
    assert value["attempt_history"][0]["provider_message_id"]
    assert len(sender.accepted) == 1


def test_c_d_retry_preserves_each_attempt_and_snapshot(setup):
    service, repo, source, sender, _, _ = setup
    sender.errors = [
        DeliveryError("timeout", "Respuesta no confirmada", retryable=True, ambiguous=True)
    ]
    first = run(service)
    identifier = first["items"][0]["id"]
    snapshot = repo.get(identifier)["payload_snapshot"]
    source.values[0]["snapshot"]["budget"] = 999
    assert first["retryable"] == 1
    assert (
        service.run(
            ["reviewer@example.invalid"],
            retry=True,
            allow_real_send=True,
            now=NOW + timedelta(seconds=61),
        )["sent"]
        == 1
    )
    value = repo.get(identifier)
    assert value["payload_snapshot"] == snapshot
    assert len(value["attempt_history"]) == 2
    assert value["attempt_history"][0]["error_code"] == "timeout"
    assert sender.calls[0] == sender.calls[1]


def test_e_max_retries_does_not_loop(setup):
    service, repo, _, sender, _, _ = setup
    service.policy = replace(service.policy, max_retries=1)
    sender.errors = [DeliveryError("429", "Límite", retryable=True)] * 3
    run(service)
    report = service.run(
        ["reviewer@example.invalid"],
        retry=True,
        allow_real_send=True,
        now=NOW + timedelta(minutes=2),
    )
    assert report["failed"] == 1
    value = repo.get(report["items"][0]["id"])
    assert value["error_code"] == "retry_exhausted"
    assert value["retry_count"] == 1
    run(service, retry=True)
    assert len(sender.calls) == 2


def test_f_permanent_error_recorded_without_retry(setup):
    service, repo, _, sender, _, _ = setup
    sender.errors = [DeliveryError("config_missing", "Falta configuración")]
    report = run(service)
    assert report["failed"] == 1
    assert (
        repo.get(report["items"][0]["id"])["attempt_history"][0]["error_code"] == "config_missing"
    )
    run(service, retry=True)
    assert len(sender.calls) == 1


@pytest.mark.parametrize("first_digest", [False, True])
def test_g_h_real_alert_once_across_immediate_and_digest(setup, first_digest):
    service, _, _, sender, sessions, _ = setup
    first = run(
        service,
        digest=first_digest,
        window=(NOW - timedelta(days=1), NOW) if first_digest else None,
    )
    second = run(
        service,
        digest=not first_digest,
        window=(NOW - timedelta(days=2), NOW) if not first_digest else None,
    )
    assert first["sent"] == 1
    assert second["sent"] == 0
    assert count(sessions) == 1
    assert count(sessions, NotificationAlertRecord) == 1
    assert len(sender.calls) == 1


def test_capture_does_not_consume_real_claim(setup):
    service, repo, source, sender, sessions, path = setup
    capture = NotificationDispatcher(repo, source, DevEmailSender(path / "capture"), service.policy)
    local = run(capture)
    assert local["captured"] == 1
    assert repo.get(local["items"][0]["id"])["sent_at"] is None
    assert run(service)["sent"] == 1
    assert len(sender.calls) == 1
    assert count(sessions) == 2
    assert count(sessions, NotificationAlertRecord) == 2


def test_i_recipients_normalized_and_independent(setup):
    service, _, _, sender, sessions, _ = setup
    result = service.run(
        ["One@Example.invalid", "one@example.invalid", "two@example.invalid"],
        allow_real_send=True,
        now=NOW,
    )
    assert result["sent"] == 2
    assert count(sessions) == 2
    assert {p["recipient"] for p in sender.calls} == {"one@example.invalid", "two@example.invalid"}


def test_j_dry_run_no_rows_no_capture_no_send(setup):
    service, repo, source, sender, sessions, path = setup
    capture = NotificationDispatcher(repo, source, DevEmailSender(path / "absent"), service.policy)
    preview = run(capture, dry_run=True)
    assert preview["preview"][0]["payload"]["recipient"] == "reviewer@example.invalid"
    assert not (path / "absent").exists()
    assert count(sessions) == 0
    assert count(sessions, NotificationAlertRecord) == 0
    assert sender.calls == []


def test_k_digest_frozen_sorted_and_overlapping_windows(setup):
    service, repo, source, _, sessions, _ = setup
    low = golden()
    low["priority"] = "low"
    source.values.append(low)
    report = run(service, digest=True, window=(NOW - timedelta(days=1), NOW))
    payload = repo.get(report["items"][0]["id"])["payload_snapshot"]
    assert len(payload["alerts"]) == 2
    assert payload["alerts"][0]["priority"] == "high"
    new = golden()
    source.values.append(new)
    report = run(service, digest=True, window=(NOW - timedelta(days=2), NOW))
    assert report["sent"] == 1
    assert len(repo.get(report["items"][0]["id"])["payload_snapshot"]["alerts"]) == 1
    assert count(sessions, NotificationAlertRecord) == 3


def test_l_empty_digest_does_not_prepare(setup):
    service, _, source, _, sessions, _ = setup
    source.values = []
    report = run(service, digest=True)
    assert report["prepared"] == 0
    assert count(sessions) == 0
    assert count(sessions, NotificationAlertRecord) == 0


def test_n_o_links_escaping_recipient_validation(setup):
    service, _, source, _, sessions, _ = setup
    source.values[0]["snapshot"]["entity"] = '<script>alert("x")</script>'
    payload = run(service, dry_run=True)["preview"][0]["payload"]
    assert "<script>" not in payload["html"]
    assert "&lt;script&gt;" in payload["html"]
    assert payload["links"] == ["http://127.0.0.1:5173/eureka/6e94cc77-9f88-4f4c-bfb8-2e832976f4c0"]
    for value in (
        "notemail",
        "a@example.invalid\r\nBcc: x@y.com",
        "@example.com",
        "a..b@example.com",
    ):
        with pytest.raises(ValueError, match="Destinatario"):
            recipient(value)
    service.policy = replace(service.policy, base_url="javascript:alert(1)")
    with pytest.raises(ValueError, match="Base URL"):
        run(service, dry_run=True)
    assert count(sessions) == 0


def test_p_disabled_and_real_authorization_guard(setup):
    service, _, source, sender, sessions, _ = setup
    service.policy = replace(service.policy, enabled=False)
    assert run(service)["disabled"]
    assert source.calls == 0
    service.policy = replace(service.policy, enabled=True)
    with pytest.raises(ValueError, match="no autorizado"):
        service.run(["r@example.invalid"], now=NOW)
    assert sender.calls == []
    assert count(sessions) == 0


def test_s_covarachia_email_content_from_historical_alert(setup):
    service, _, _, _, _, _ = setup
    p = run(service, dry_run=True)["preview"][0]["payload"]
    for term in (
        "Alta",
        "65",
        "Covarachía",
        "Boyacá",
        "$2.080.000",
        "Jugo Hit",
        "Chocorramo",
        "Plazo: 5 días",
        "Pago: 30 días",
        "Póliza: No requerida",
        "Confirmar vigencia",
    ):
        assert term in p["text"] + p["subject"]


def test_processing_stale_recovers_same_file_after_acceptance(setup):
    service, repo, source, _, _, path = setup
    capture = NotificationDispatcher(repo, source, DevEmailSender(path / "capture"), service.policy)
    a = source.values[0]
    address = "reviewer@example.invalid"
    payload = compose([a], address, service.policy.base_url, "immediate", "")
    identifier = repo.prepare([a], address, "capture", "file", "immediate", payload, NOW, None)
    record = repo.begin_attempt(identifier, NOW, "file", None, 3)
    capture.sender.send(record["payload_snapshot"], record["idempotency_key"])
    result = capture.run([address], retry=True, now=NOW + timedelta(seconds=301))
    assert result["captured"] == 1
    assert result["recovered"][0]["status"] == "retryable"
    assert len(list((path / "capture").glob("*.json"))) == 1
    assert repo.get(identifier)["attempt_history"][0]["result"] == "interrupted"
    assert repo.get(identifier)["attempt_count"] == 2


@pytest.mark.parametrize(
    ("age", "sent", "status"), [(301, 1, "sent"), (90000, 0, "failed"), (10, 0, "processing")]
)
def test_processing_real_lease_and_expired_idempotency(setup, age, sent, status):
    service, repo, source, sender, _, _ = setup
    a = source.values[0]
    address = "reviewer@example.invalid"
    identifier = repo.prepare(
        [a],
        address,
        "real",
        "resend",
        "immediate",
        compose([a], address, service.policy.base_url, "immediate", service.policy.sender),
        NOW,
        None,
    )
    repo.begin_attempt(identifier, NOW, "resend", 86400, 3)
    result = service.run(
        [address], retry=True, allow_real_send=True, now=NOW + timedelta(seconds=age)
    )
    assert result["sent"] == sent
    assert repo.get(identifier)["status"] == status
    assert len(sender.calls) == sent


def test_late_retry_ambiguous_timeout_requires_review(setup):
    service, repo, _, sender, _, _ = setup
    sender.errors = [DeliveryError("timeout", "No confirmado", retryable=True, ambiguous=True)]
    first = run(service)
    later = service.run(
        ["reviewer@example.invalid"], retry=True, allow_real_send=True, now=NOW + timedelta(days=2)
    )
    assert later["failed"] == 1
    assert repo.get(first["items"][0]["id"])["error_code"] == "delivery_unknown_review"
    assert len(sender.calls) == 1


def test_bogota_digest_windows_inclusive_exclusive():
    window = digest_window("daily", NOW.date(), NOW)
    assert window[0] == datetime(2026, 10, 14, 5, tzinfo=UTC)
    assert window[1] == datetime(2026, 10, 15, 5, tzinfo=UTC)
    assert digest_window("since-last", None, NOW)[1] == NOW


def test_q_queries_filter_and_pagination(setup):
    service, _, source, _, sessions, _ = setup
    run(service)
    q = NotificationQueries(sessions)
    assert q.listing(1, 25, {"status": "sent"})["total"] == 1
    assert q.listing(1, 25, {"delivery_scope": "capture"})["total"] == 0
    assert q.listing(2, 25, {})["items"] == []
    value = q.listing(1, 25, {"alert_id": uuid.UUID(source.values[0]["id"])})["items"][0]
    assert "payload_snapshot" not in value
    assert len(q.detail(value["id"])["attempt_history"]) == 1


def test_dry_run_stale_processing_projects_recovery_without_writing(setup):
    service, repo, source, sender, _, _ = setup
    a = source.values[0]
    address = "reviewer@example.invalid"
    identifier = repo.prepare(
        [a],
        address,
        "real",
        "resend",
        "immediate",
        compose([a], address, service.policy.base_url, "immediate", service.policy.sender),
        NOW,
        None,
    )
    repo.begin_attempt(identifier, NOW, "resend", 86400, 3)
    before = repo.get(identifier)
    preview = service.run([address], retry=True, dry_run=True, now=NOW + timedelta(seconds=301))
    assert preview["recovered"][0]["would_status"] == "retryable"
    assert preview["preview"][0]["would_send"]
    assert repo.get(identifier) == before
    assert sender.calls == []


def test_dry_run_cap_and_ambiguous_expiry_do_not_preview_send(setup):
    service, repo, _, sender, _, _ = setup
    sender.errors = [DeliveryError("timeout", "No confirmado", retryable=True, ambiguous=True)]
    result = run(service)
    identifier = result["items"][0]["id"]
    preview = service.run(
        ["reviewer@example.invalid"], retry=True, dry_run=True, now=NOW + timedelta(days=2)
    )
    assert not preview["preview"][0]["would_send"]
    assert preview["preview"][0]["blocked_reason"] == "delivery_unknown_review"
    assert repo.get(identifier)["status"] == "retryable"


def test_provider_expiration_margin_blocks_ambiguous_retry(setup):
    service, repo, _, sender, _, _ = setup
    sender.errors = [DeliveryError("timeout", "No confirmado", retryable=True, ambiguous=True)]
    first = run(service)
    report = service.run(
        ["reviewer@example.invalid"],
        retry=True,
        allow_real_send=True,
        now=NOW + timedelta(seconds=86400 - 30),
    )
    assert report["failed"] == 1
    assert repo.get(first["items"][0]["id"])["error_code"] == "delivery_unknown_review"
    assert len(sender.calls) == 1


def test_digest_selection_does_not_send_unrelated_pending(setup):
    service, repo, source, sender, _, _ = setup
    a = source.values[0]
    address = "reviewer@example.invalid"
    repo.prepare(
        [a],
        address,
        "real",
        "resend",
        "immediate",
        compose([a], address, service.policy.base_url, "immediate", service.policy.sender),
        NOW,
        None,
    )
    report = run(service, digest=True, window=(NOW, NOW + timedelta(hours=1)))
    assert report["sent"] == 0
    assert sender.calls == []


def test_payload_excludes_full_documentary_evidence(setup):
    service, _, source, _, _, _ = setup
    source.values[0]["reasons"].append(
        {"code": "document_evidence", "references": [{"text": "unnecessary full document"}]}
    )
    payload = run(service, dry_run=True)["preview"][0]["payload"]
    assert "unnecessary full document" not in str(payload)
