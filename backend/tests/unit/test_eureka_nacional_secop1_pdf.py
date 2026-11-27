"""Offline tests for SECOP I PDF acceptance without Content-Length. Synthetic bytes only."""

import asyncio
import base64
import hashlib
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from eureka_nacional_cdp_stream import CHUNK, DEADLINE, DOCUMENT_BYTES, RejectionError
from eureka_nacional_secop1_pdf import has_eof_marker, read_secop1_pdf, validate_pdf_body

PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def response(status=200, content_type="application/pdf", length=None, encoding=None):
    headers = [{"name": "Content-Type", "value": content_type}]
    if length is not None:
        headers.append({"name": "Content-Length", "value": str(length)})
    if encoding is not None:
        headers.append({"name": "Content-Encoding", "value": encoding})
    return {"responseStatusCode": status, "responseHeaders": headers}


class FakeCDP:
    """In-memory CDP stream: serves `body` in chunks of at most the requested size."""

    def __init__(
        self,
        body=PDF,
        *,
        endless=False,
        read_delay=0,
        read_error=None,
        abort_error=None,
        max_part=None,
    ):
        self.body, self.offset = body, 0
        self.endless, self.read_delay = endless, read_delay
        self.read_error, self.abort_error = read_error, abort_error
        self.max_part = max_part
        self.calls = []

    async def send(self, method, params=None):
        self.calls.append(method)
        if method == "Fetch.takeResponseBodyAsStream":
            return {"stream": "stream-1"}
        if method == "IO.read":
            if self.read_delay:
                await asyncio.sleep(self.read_delay)
            if self.read_error:
                raise self.read_error
            size = min(params["size"], self.max_part or params["size"])
            if self.endless:
                return {
                    "data": base64.b64encode(b"x" * size).decode(),
                    "base64Encoded": True,
                    "eof": False,
                }
            part = self.body[self.offset : self.offset + size]
            self.offset += len(part)
            return {
                "data": base64.b64encode(part).decode(),
                "base64Encoded": True,
                "eof": self.offset >= len(self.body),
            }
        if method == "IO.close":
            return {}
        if method == "Fetch.failRequest":
            if self.abort_error:
                raise self.abort_error
            return {}
        raise AssertionError(method)


def new_trace():
    return {"stream_bytes": 0, "io_closed": False, "navigation_abort_ack": False}


def run(cdp, event, trace=None, started=None):
    trace = new_trace() if trace is None else trace
    started = time.monotonic() if started is None else started
    return asyncio.run(read_secop1_pdf(cdp, "req-1", event, trace, started=started)), trace


def rejected(cdp, event, started=None):
    with pytest.raises(RejectionError) as error:
        run(cdp, event, started=started)
    return str(error.value)


def test_pdf_without_content_length_is_accepted_with_received_size_and_hash():
    # Arrange
    cdp = FakeCDP(PDF)

    # Act
    body, trace = run(cdp, response())

    # Assert
    assert body == PDF
    assert trace["declared_size"] is False
    assert trace["size_origin"] == "received_undeclared"
    assert trace["received_bytes"] == len(PDF)
    assert trace["sha256"] == hashlib.sha256(PDF).hexdigest()
    assert trace["io_closed"] is True
    assert trace["navigation_abort_ack"] is True
    assert cdp.calls[-2:] == ["IO.close", "Fetch.failRequest"]


def test_multi_chunk_pdf_without_length_is_reassembled():
    body = b"%PDF-1.4\n" + b"0" * (3 * CHUNK + 17) + b"\n%%EOF"

    accepted, trace = run(FakeCDP(body), response())

    assert accepted == body
    assert trace["received_bytes"] == len(body)


def test_signature_is_checked_on_whole_body_not_first_chunk():
    accepted, _ = run(FakeCDP(PDF, max_part=2), response())

    assert accepted == PDF


def test_declared_length_still_must_match():
    body, trace = run(FakeCDP(PDF), response(length=len(PDF)))

    assert trace["size_origin"] == "declared"
    assert body == PDF
    assert rejected(FakeCDP(PDF), response(length=len(PDF) + 1)) == "length_mismatch"


@pytest.mark.parametrize(
    ("event", "reason"),
    [
        (response(length=DOCUMENT_BYTES + 1), "declared_size_limit"),
        (response(status=302), "unexpected_response"),
        (response(status=206), "unexpected_response"),
        (response(content_type="text/html"), "unexpected_response"),
        (response(content_type="application/pdf; charset=binary"), "unexpected_response"),
        (response(encoding="gzip"), "unexpected_response"),
        (response(length="12a"), "invalid_length"),
    ],
)
def test_existing_header_rejections_are_kept_and_nothing_is_read(event, reason):
    cdp = FakeCDP(PDF)

    assert rejected(cdp, event) == reason
    assert cdp.calls == []


def test_undeclared_stream_over_ten_mib_is_rejected():
    cdp = FakeCDP(endless=True)

    assert rejected(cdp, response()) == "stream_size_limit"
    assert "IO.close" not in cdp.calls


def test_slow_stream_hits_deadline():
    started = time.monotonic() - (DEADLINE - 0.2)

    assert rejected(FakeCDP(PDF, read_delay=1), response(), started=started) == (
        "acquisition_timeout"
    )


def test_deadline_already_spent_before_reading():
    cdp = FakeCDP(PDF)

    assert rejected(cdp, response(), started=time.monotonic() - DEADLINE) == "acquisition_timeout"
    assert cdp.calls == []


def test_interrupted_stream_is_rejected():
    assert rejected(FakeCDP(read_error=RuntimeError("io")), response()) == "stream_interrupted"


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (PDF[: len(PDF) // 2], "pdf_eof_marker_missing"),  # truncated: no trailer
        (b"<html>%%EOF</html>", "invalid_pdf_signature"),
        (b"PDF-1.7 ... %%EOF", "invalid_pdf_signature"),
        (b"%PDF-1.7\n" + b"0" * 2000, "pdf_eof_marker_missing"),
    ],
)
def test_incomplete_or_invalid_pdf_is_rejected(body, reason):
    assert rejected(FakeCDP(body), response()) == reason


def test_eof_marker_far_from_end_is_not_accepted():
    body = b"%PDF-1.7\n%%EOF\n" + b"0" * 2000

    assert has_eof_marker(body) is False
    assert rejected(FakeCDP(body), response()) == "pdf_eof_marker_missing"


def test_uncertain_navigation_abort_is_rejected():
    cdp = FakeCDP(PDF, abort_error=RuntimeError("target closed"))

    assert rejected(cdp, response()) == "stream_interrupted"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"io_closed": False}, "stream_close_unverified"),
        ({"navigation_abort_ack": False}, "stream_close_unverified"),
        ({"stream_bytes": len(PDF) + 1}, "stream_accounting_mismatch"),
    ],
)
def test_body_validation_requires_verified_close_and_accounting(changes, reason):
    trace = {"stream_bytes": len(PDF), "io_closed": True, "navigation_abort_ack": True, **changes}

    with pytest.raises(RejectionError) as error:
        validate_pdf_body([PDF], None, trace)

    assert str(error.value) == reason
    assert "sha256" not in trace


def test_empty_body_is_rejected():
    trace = {"stream_bytes": 0, "io_closed": True, "navigation_abort_ack": True}

    with pytest.raises(RejectionError, match="empty_body"):
        validate_pdf_body([b""], None, trace)
