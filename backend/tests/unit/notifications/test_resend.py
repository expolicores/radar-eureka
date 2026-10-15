import json

import pytest

from public_procurement.notifications.adapters.resend import ResendEmailSender
from public_procurement.notifications.domain.message import DeliveryError

PAYLOAD = {
    "from": "sender@example.invalid",
    "recipient": "r@example.invalid",
    "subject": "Test",
    "text": "Test",
    "html": "<p>Test</p>",
}


def test_simulated_http_acceptance_and_idempotency_header():
    calls = []

    def http(url, headers, body, timeout):
        calls.append((url, headers, body, timeout))
        return 200, {}, b'{"id":"provider-id"}'

    sender = ResendEmailSender("test-secret", 15, http)
    assert sender.send(PAYLOAD, "stable-key").message_id == "provider-id"
    assert calls[0][1]["Idempotency-Key"] == "stable-key"
    assert json.loads(calls[0][2])["to"] == ["r@example.invalid"]
    assert calls[0][3] == 15


@pytest.mark.parametrize(
    ("status", "retryable"),
    [(429, True), (500, True), (503, True), (401, False), (422, False), (302, False)],
)
def test_http_failures_sanitized(status, retryable):
    def http(*args):
        return status, {}, b'{"message":"test-secret private-body"}'

    sender = ResendEmailSender("test-secret", 15, http)
    with pytest.raises(DeliveryError) as caught:
        sender.send(PAYLOAD, "key")
    assert caught.value.retryable is retryable
    assert "test-secret" not in str(caught.value)
    assert "private-body" not in str(caught.value)


def test_ambiguous_network_and_missing_configuration():
    def http(*args):
        raise TimeoutError("test-secret")

    with pytest.raises(DeliveryError) as caught:
        ResendEmailSender("test-secret", 15, http).send(PAYLOAD, "k")
    assert caught.value.ambiguous
    assert "test-secret" not in str(caught.value)
    with pytest.raises(DeliveryError) as missing:
        ResendEmailSender("", 15, http).send(PAYLOAD, "k")
    assert not missing.value.retryable


def test_retry_after_and_idempotency_conflict():
    def limited(*args):
        return 429, {"Retry-After": "120"}, b"{}"

    with pytest.raises(DeliveryError) as caught:
        ResendEmailSender("x", 15, limited).send(PAYLOAD, "k")
    assert caught.value.retry_after == 120
    for name, expected in [
        ("concurrent_idempotent_requests", True),
        ("invalid_idempotent_request", False),
    ]:

        def conflict(*args, name=name):
            return 409, {}, json.dumps({"name": name}).encode()

        with pytest.raises(DeliveryError) as caught:
            ResendEmailSender("x", 15, conflict).send(PAYLOAD, "k")
        assert caught.value.retryable is expected
