"""Offline coverage of the synchronous runner's isolated CDP worker."""

import asyncio
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_cdp_stream as streaming

PDF = b"%PDF-1.7\nsynthetic body\n%%EOF\n"
CDP = "http://127.0.0.1:1"


@pytest.fixture
def fake_worker(tmp_path, monkeypatch):
    script = tmp_path / "synthetic_worker.py"
    script.write_text(
        """
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

payload = json.load(sys.stdin)
case = payload["document_id"]
assert payload["cdp_url"] == "http://127.0.0.1:1"
assert sys.argv[1:] == ["--stream-worker"]
assert payload["source_url"].endswith("?DocumentId=" + case)
Path(__file__).with_name("staging-path").write_text(payload["staging"], encoding="utf8")
if case == "103":
    time.sleep(60)
if case == "104":
    print("malformed worker output")
    sys.exit(0)
closed = case in {"100", "101", "105"}
data = b"%PDF-1.7\\nsynthetic body\\n%%EOF\\n"
stored = None
diagnostics = dict(tab_opened=True, target_closed=closed, requests_forwarded=1,
                   io_closed=closed, navigation_abort_ack=closed, stream_bytes=0)
if case in {"100", "105"}:
    staging = LocalBinaryStorage(Path(payload["staging"]))
    stored = staging.store([data], original_name="fixture.pdf", content_type="application/pdf",
                           expected_size=len(data), max_bytes=10 * 1024 * 1024)
    diagnostics["stream_bytes"] = len(data)
    if case == "105":
        (staging.root / stored.storage_path).write_bytes(data.replace(b"body", b"edit"))
else:
    diagnostics["error"] = "deadline" if closed else "protocol_error"
print(json.dumps(dict(stored=asdict(stored) if stored else None, diagnostics=diagnostics)))
""",
        encoding="utf8",
    )
    monkeypatch.setattr(streaming, "WORKER_SCRIPT", script)
    return script


def download(case, storage, marker, diagnostics):
    url = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=" + case
    document = SimpleNamespace(source_url=url, document_id=case, extension="pdf")
    return streaming.download_stream_pdf(document, storage, marker, diagnostics, cdp_url=CDP)


def test_fallback_isolated_from_running_sync_playwright_loop(tmp_path, fake_worker):
    storage = streaming.LocalBinaryStorage(tmp_path / "validated")
    marker, trace = tmp_path / "uncertain.lock", {}
    with sync_playwright():
        assert asyncio.get_running_loop().is_running()
        result = download("100", storage, marker, trace)

    assert result.observed_size == len(PDF)
    assert result.sha256 == hashlib.sha256(PDF).hexdigest()
    assert (storage.root / result.storage_path).read_bytes() == PDF
    assert trace["requests_forwarded"] == 1
    assert all(trace[k] is True for k in ("worker_closed", "target_closed", "io_closed"))
    assert not trace["session_blocked"]
    assert not marker.exists()
    assert not Path(fake_worker.with_name("staging-path").read_text(encoding="utf8")).exists()


@pytest.mark.parametrize(
    ("case", "error", "blocked"),
    [
        ("101", "deadline", False),
        ("102", "protocol_error", True),
        ("103", "worker_timeout", True),
        ("104", "worker_protocol", True),
        ("105", "hash_mismatch", False),
    ],
)
def test_failure_verifies_closure_or_blocks_next_acquisition(
    case, error, blocked, tmp_path, fake_worker, monkeypatch
):
    if case == "103":
        monkeypatch.setattr(streaming, "WORKER_TIMEOUT", 3)
    storage = streaming.LocalBinaryStorage(tmp_path / "validated")
    marker, trace = tmp_path / "uncertain.lock", {}
    with pytest.raises(streaming.AcquisitionError) as failure:
        download(case, storage, marker, trace)
    assert failure.value.code == error
    assert trace["worker_closed"] is True
    assert trace["session_blocked"] is blocked
    assert marker.exists() is blocked
    assert not list(storage.root.glob("sha256/*/*"))
    assert not Path(fake_worker.with_name("staging-path").read_text(encoding="utf8")).exists()

    if blocked:
        with pytest.raises(streaming.AcquisitionError) as again:
            download("100", storage, marker, {})
        assert again.value.code == "stream_close_unverified"
    else:
        assert download("100", storage, marker, {}).observed_size == len(PDF)
