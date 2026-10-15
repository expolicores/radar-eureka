"""Explicit isolated database only. Real scopes use an injected HTTP simulation."""

import copy
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.entrypoints.api.app import create_app
from public_procurement.notifications.adapters.alerts import PersistedAlertSource
from public_procurement.notifications.adapters.file import DevEmailSender
from public_procurement.notifications.adapters.resend import ResendEmailSender
from public_procurement.notifications.domain.message import compose
from public_procurement.notifications.repositories import (
    DispatcherBusyError,
    NotificationAlertRecord,
    NotificationRecord,
    SqlNotificationRepository,
)
from public_procurement.notifications.services import DispatchPolicy, NotificationDispatcher
from public_procurement.shared.config import load_settings
from public_procurement.shared.testing import settings_for_test_database


class HttpLedger:
    def __init__(self):
        self.requests = []
        self.accepted = {}
        self.timeout_after_acceptance = False
        self.entered = None
        self.release = None
        self.lock = threading.Lock()

    def __call__(self, url, headers, body, timeout):
        assert url == "https://api.resend.com/emails"
        key = headers["Idempotency-Key"]
        with self.lock:
            self.requests.append(body)
            self.accepted.setdefault(key, str(uuid.uuid4()))
            receipt = self.accepted[key]
            fail = self.timeout_after_acceptance
            self.timeout_after_acceptance = False
        if self.entered is not None:
            self.entered.set()
            assert self.release.wait(5)
        if fail:
            raise TimeoutError("simulated response loss after provider acceptance")
        import json

        return 200, {}, json.dumps({"id": receipt}).encode()


@pytest.fixture
def setup(tmp_path):
    url = os.environ.get("NOTIFICATIONS_ACCEPTANCE_DATABASE_URL")
    if not url:
        pytest.skip("NOTIFICATIONS_ACCEPTANCE_DATABASE_URL required; dedicated *_test only")
    settings = settings_for_test_database(load_settings(test_database_url=url))
    engine = create_engine(settings.database_url)
    sessions = sessionmaker(engine, expire_on_commit=False)
    with engine.connect() as c:
        assert (
            c.scalar(text("SELECT version_num FROM alembic_version")) == "0015_eureka_notifications"
        )
    repo = SqlNotificationRepository(sessions)
    source = PersistedAlertSource(sessions)
    alert = next(iter(source.alerts(None, None)))
    address = "acceptance-" + uuid.uuid4().hex + "@example.invalid"
    ledger = HttpLedger()
    sender = ResendEmailSender("test-secret-not-real", 2, ledger)
    policy = DispatchPolicy(
        enabled=True, base_url="http://127.0.0.1:5173", sender="fixture@example.invalid"
    )
    service = NotificationDispatcher(repo, source, sender, policy)
    yield service, repo, source, ledger, address, alert, settings, sessions, tmp_path
    engine.dispose()


def owned(sessions, address):
    with sessions() as s:
        return list(
            s.scalars(select(NotificationRecord).where(NotificationRecord.recipient == address))
        )


@pytest.mark.parametrize("first_digest", [False, True])
def test_cross_type_unique_real_delivery(setup, first_digest):
    service, repo, _, ledger, address, alert, _, sessions, _ = setup
    first = service.run([address], digest=first_digest, allow_real_send=True)
    second = service.run([address], digest=not first_digest, allow_real_send=True)
    assert first["sent"] == 1
    assert second["sent"] == 0
    assert len(ledger.accepted) == 1
    assert len(owned(sessions, address)) == 1
    assert repo.assigned([uuid.UUID(str(alert["id"]))], address, "real")


def test_capture_then_real_and_golden_payload(setup):
    service, repo, source, ledger, address, _, _, sessions, path = setup
    capture = NotificationDispatcher(repo, source, DevEmailSender(path / "capture"), service.policy)
    result = capture.run([address])
    assert result["captured"] == 1
    message = repo.get(result["items"][0]["id"])
    assert message["sent_at"] is None
    for term in (
        "Covarachía",
        "Boyacá",
        "$2.080.000",
        "Jugo Hit",
        "Chocorramo",
        "5 días",
        "30 días",
        "No requerida",
        "vigencia",
    ):
        assert term in message["payload_snapshot"]["text"]
    assert service.run([address], allow_real_send=True)["sent"] == 1
    assert len(ledger.accepted) == 1
    assert len(owned(sessions, address)) == 2


def test_provider_accepted_timeout_retry_same_request_no_duplicate(setup):
    service, repo, _, ledger, address, _, _, _, _ = setup
    ledger.timeout_after_acceptance = True
    now = datetime.now(UTC)
    first = service.run([address], allow_real_send=True, now=now)
    snapshot = copy.deepcopy(repo.get(first["items"][0]["id"])["payload_snapshot"])
    second = service.run(
        [address], allow_real_send=True, retry=True, now=now + timedelta(seconds=61)
    )
    assert first["retryable"] == 1
    assert second["sent"] == 1
    assert len(ledger.requests) == 2
    assert len(ledger.accepted) == 1
    assert ledger.requests[0] == ledger.requests[1]
    value = repo.get(first["items"][0]["id"])
    assert value["payload_snapshot"] == snapshot
    assert len(value["attempt_history"]) == 2


def test_two_dispatchers_global_lock_and_one_delivery(setup):
    service, _repo, source, ledger, address, _, _, sessions, _ = setup
    second = NotificationDispatcher(
        SqlNotificationRepository(sessions), source, service.sender, service.policy
    )
    ledger.entered = threading.Event()
    ledger.release = threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(service.run, [address], allow_real_send=True)
        assert ledger.entered.wait(5)
        contender = pool.submit(second.run, [address], allow_real_send=True)
        try:
            with pytest.raises(DispatcherBusyError, match="activo"):
                contender.result(timeout=5)
        finally:
            ledger.release.set()
        assert first.result(timeout=5)["sent"] == 1
    assert len(owned(sessions, address)) == 1
    assert len(ledger.accepted) == 1


def test_database_claim_unique_without_application_lock(setup):
    service, repo, _, _, address, alert, _, sessions, _ = setup

    def reserve(kind):
        return repo.prepare(
            [alert],
            address,
            "real",
            "resend",
            kind,
            compose([alert], address, service.policy.base_url, kind, service.policy.sender),
            datetime.now(UTC),
            None,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(reserve, kind) for kind in ("immediate", "digest")]
        ids = [f.result(timeout=5) for f in futures]
    assert len([i for i in ids if i]) == 1
    assert len(owned(sessions, address)) == 1
    with sessions() as s:
        assert (
            s.scalar(
                select(func.count())
                .select_from(NotificationAlertRecord)
                .where(NotificationAlertRecord.recipient == address)
            )
            == 1
        )


@pytest.mark.parametrize(("age", "expected"), [(301, "sent"), (90000, "failed")])
def test_stale_processing_recovery_or_review(setup, age, expected):
    service, repo, _, ledger, address, alert, _, _, _ = setup
    now = datetime.now(UTC)
    payload = compose([alert], address, service.policy.base_url, "immediate", service.policy.sender)
    identifier = repo.prepare([alert], address, "real", "resend", "immediate", payload, now, None)
    r = repo.begin_attempt(identifier, now, "resend", 86400, 3)
    # Simulate provider acceptance followed by death before the local commit.
    service.sender.send(r["payload_snapshot"], r["idempotency_key"])
    result = service.run(
        [address], retry=True, allow_real_send=True, now=now + timedelta(seconds=age)
    )
    assert result["recovered"]
    assert repo.get(identifier)["status"] == expected
    assert len(ledger.accepted) == 1
    assert len(ledger.requests) == (2 if expected == "sent" else 1)


def test_dry_run_and_read_api_no_new_rows(setup):
    service, _repo, _, ledger, address, _, settings, sessions, _ = setup
    preview = service.run([address], dry_run=True)
    assert preview["preview"][0]["would_send"]
    assert owned(sessions, address) == []
    assert ledger.requests == []
    sent = service.run([address], allow_real_send=True)
    with TestClient(create_app(settings)) as client:
        response = client.get(
            "/api/eureka/notifications", params={"recipient": address, "status": "sent"}
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert "payload_snapshot" not in response.json()["items"][0]
        response = client.get("/api/eureka/notifications/" + str(sent["items"][0]["id"]))
        assert response.status_code == 200
        assert response.json()["payload_snapshot"]["alerts"][0]["snapshot"]["score"] == 65
        assert client.post("/api/eureka/notifications").status_code == 405
