"""Offline tests for SECOP I stage 2 (batch acquisition). Synthetic loopback only."""

import asyncio
import hashlib
import json
import os
import sys
from contextlib import contextmanager, suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from urllib.parse import parse_qs

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_en01 as en01
import eureka_nacional_secop1_acquire as acquire
import eureka_nacional_secop1_flow as flow
from eureka_nacional_cdp_stream_lab import fixture_pdf, fixture_server
from eureka_nacional_secop1_popup import Secop1PopupGuard

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

LAB = pytest.mark.skipif(
    os.getenv("RUN_EN01_POPUP_LAB") != "1", reason="requires isolated local Edge"
)
CONSTANCIA = "26-13-12345678"


def item(number):
    path = f"/synthetic/{CONSTANCIA}/doc_{number}.pdf"
    return {
        "process_reference": f"licitaciones_info:1:{number}",
        "constancia": CONSTANCIA,
        "document_id": f"secop1:{CONSTANCIA}:{hashlib.sha256(path.encode()).hexdigest()}",
        "name": "Invitación",
        "extension": "pdf",
        "relative_path": path,
    }


def queued_run(tmp_path, count=3):
    run = tmp_path / "en01-lab"
    run.mkdir()
    return run, flow.write_queue(run, [item(n) for n in range(1, count + 1)], run.name)


# ---------------------------------------------------------------- attempts, plan, confirmation


def test_attempt_is_exclusive_and_never_repeated(tmp_path):
    # Arrange
    run, queue = queued_run(tmp_path)

    # Act
    first = acquire.reserve_attempt(run, queue["items"][0], queue["batch_sha256"])
    second = acquire.reserve_attempt(run, queue["items"][0], queue["batch_sha256"])

    # Assert
    assert first is not None
    assert second is None
    assert json.loads(first.read_text(encoding="utf-8"))["state"] == "reserved"


def test_plan_counts_recorded_attempts_against_the_confirmed_maximum(tmp_path):
    run, queue = queued_run(tmp_path, count=3)
    acquire.reserve_attempt(run, queue["items"][1], queue["batch_sha256"])

    items, recorded = acquire.plan_batch(queue, run)

    assert recorded == 1
    assert [i["document_id"] for i in items] == [
        queue["items"][0]["document_id"],
        queue["items"][2]["document_id"],
    ]


def test_plan_never_exceeds_max_posts(tmp_path):
    run, queue = queued_run(tmp_path, count=5)
    for entry in queue["items"][:5]:
        acquire.reserve_attempt(run, entry, queue["batch_sha256"])

    items, recorded = acquire.plan_batch(queue, run)

    assert (items, recorded) == ([], 5)


@pytest.mark.parametrize(
    ("content", "valid"),
    [("{digest}", True), ("{digest}\n", True), ("0" * 64, False), ("", False), (None, False)],
)
def test_confirmation_is_bound_to_the_batch_digest(tmp_path, content, valid):
    run, queue = queued_run(tmp_path)
    flag = run / "confirmed-batch.flag"
    if content is not None:
        flag.write_text(content.format(digest=queue["batch_sha256"]), encoding="utf-8")

    assert acquire.confirmation_valid(flag, queue) is valid


def test_receipt_matches_runner_download_state(tmp_path):
    # Arrange
    run, queue = queued_run(tmp_path, count=1)
    storage = LocalBinaryStorage(run / "binaries")
    pdf = b"%PDF-1.4\n%%EOF\n"
    trace = {"received_bytes": len(pdf), "sha256": hashlib.sha256(pdf).hexdigest()}
    staged = acquire.store_pdf(storage, pdf, trace)

    # Act
    acquire.write_receipt(
        run,
        queue["items"][0],
        {
            "storage_path": staged.storage_path,
            "sha256": staged.sha256,
            "received_bytes": staged.observed_size,
        },
    )

    # Assert: the runner's own cache accepts it without any download.
    state = en01.DownloadState(run, storage)
    document = en01.spike.SpikeDocument("Invitación", "pdf", "", queue["items"][0]["document_id"])
    assert state.cached(document, en01.DOCUMENT_BYTES).sha256 == staged.sha256
    with pytest.raises(acquire.RejectionError, match="receipt_already_present"):
        acquire.write_receipt(
            run, queue["items"][0], {"storage_path": "x", "sha256": "y", "received_bytes": 1}
        )


def test_store_removes_copy_that_does_not_match(tmp_path):
    storage = LocalBinaryStorage(tmp_path / "binaries")
    pdf = b"%PDF-1.4\n%%EOF\n"

    with pytest.raises(acquire.RejectionError, match="staged_hash_mismatch"):
        acquire.store_pdf(storage, pdf, {"received_bytes": len(pdf), "sha256": "0" * 64})

    assert not list((tmp_path / "binaries").glob("sha256/*/*"))


# ---------------------------------------------------------------- batch rules


def fake_acquire(outcomes):
    calls = []

    async def run_one(_guard, entry, _storage, *, target):
        calls.append(entry["document_id"])
        result = outcomes[len(calls) - 1]
        if isinstance(result, Exception):
            raise result
        if result == "stored":
            return {
                "outcome": "stored",
                "posts_forwarded": 1,
                "storage_path": "sha256/aa/x",
                "sha256": "a" * 64,
                "received_bytes": 10,
            }, b"%PDF-"
        return {"outcome": "rejected", "posts_forwarded": 1, "reason": result}, None

    return run_one, calls


def run_batch(tmp_path, monkeypatch, outcomes, count=4):
    run, queue = queued_run(tmp_path, count=count)
    run_one, calls = fake_acquire(outcomes)
    monkeypatch.setattr(acquire, "acquire_one", run_one)
    items, _ = acquire.plan_batch(queue, run)
    report = asyncio.run(acquire.run_batch(None, items, run, None, queue["batch_sha256"]))
    return run, report, calls


def test_two_consecutive_failures_stop_the_batch(tmp_path, monkeypatch):
    run, report, calls = run_batch(
        tmp_path, monkeypatch, ["stored", "invalid_pdf_signature", "acquisition_timeout", "stored"]
    )

    assert len(calls) == 3
    assert report["stop_reason"] == "consecutive_failures"
    assert (report["stored"], report["rejected"]) == (1, 2)
    receipts = json.loads((run / flow.RECEIPTS_FILE).read_text(encoding="utf-8"))
    assert len(receipts) == 1


def test_isolated_failure_does_not_stop_the_batch(tmp_path, monkeypatch):
    _, report, calls = run_batch(
        tmp_path,
        monkeypatch,
        ["invalid_pdf_signature", "stored", "pdf_eof_marker_missing", "stored"],
    )

    assert len(calls) == 4
    assert report["stop_reason"] == "batch_complete"


def test_uncertain_close_stops_and_is_recorded(tmp_path, monkeypatch):
    with pytest.raises(acquire.UncertainCloseError):
        run, _, _ = run_batch(
            tmp_path, monkeypatch, ["stored", acquire.UncertainCloseError("popup_close_failed")]
        )
    run = tmp_path / "en01-lab"
    records = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in (run / acquire.ATTEMPTS_DIR).glob("*.json")
    ]
    assert sorted(r["outcome"] for r in records) == ["stored", "uncertain_close"]


def test_unexpected_error_is_recorded_and_stops(tmp_path, monkeypatch):
    with pytest.raises(RuntimeError):
        run_batch(tmp_path, monkeypatch, [RuntimeError("boom")])
    records = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in (tmp_path / "en01-lab" / acquire.ATTEMPTS_DIR).glob("*.json")
    ]
    assert [r["outcome"] for r in records] == ["error"]


def test_rerun_skips_every_recorded_attempt(tmp_path, monkeypatch):
    run, _, _ = run_batch(
        tmp_path, monkeypatch, ["stored", "invalid_pdf_signature", "stored", "stored"]
    )
    queue = flow.load_queue(run)

    items, recorded = acquire.plan_batch(queue, run)

    assert (items, recorded) == ([], 4)


# ---------------------------------------------------------------- isolated Edge lab


@contextmanager
def secop1_server(responses, received):
    """POST /VerDocumento: per-ruta response mode (chunked PDF, html, truncated)."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_args):
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if self.path != "/VerDocumento" or not 0 < length <= 1024:
                self.send_error(400)
                return
            route = parse_qs(self.rfile.read(length).decode("ascii"))["ruta"][0]
            received.append(route)
            mode, body = responses[route]
            with suppress(OSError):
                self.send_response(200)
                self.send_header(
                    "Content-Type", "application/pdf" if mode != "html" else "text/html"
                )
                self.send_header("Transfer-Encoding", "chunked")
                self.send_header("Connection", "close")
                self.end_headers()
                data = body if mode != "truncated" else body[: len(body) // 2]
                for start in range(0, len(data), 4096):
                    part = data[start : start + 4096]
                    self.wfile.write(b"%x\r\n" % len(part) + part + b"\r\n")
                if mode != "truncated":
                    self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
                self.close_connection = True

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/VerDocumento"
        finally:
            server.shutdown()
            thread.join()


async def launch(playwright, directory):
    return await playwright.chromium.launch(
        channel="msedge",
        headless=True,
        downloads_path=directory,
        args=[
            "--disable-background-networking",
            "--disable-component-update",
            "--no-proxy-server",
            "--host-resolver-rules=MAP localhost 127.0.0.1, MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
        ],
    )


@LAB
def test_lab_batch_acquires_valid_rejects_invalid_and_stops_after_two(tmp_path):
    # Arrange: valid, html, truncated, valid. The fourth must never be posted.
    from playwright.async_api import async_playwright

    pdf = fixture_pdf()
    run, queue = queued_run(tmp_path, count=4)
    modes = ["chunked", "html", "truncated", "chunked"]
    responses = {i["relative_path"]: (m, pdf) for i, m in zip(queue["items"], modes, strict=True)}
    received = []
    guard = Secop1PopupGuard(tmp_path / "uncertain.lock")
    storage = LocalBinaryStorage(run / "binaries")
    outcome = {}

    async def scenario(origin, target):
        async with async_playwright() as pw:
            browser = await launch(pw, tmp_path / "downloads")
            try:
                source = await guard.start(browser)
                await source.goto(origin, timeout=4000)
                items, _ = acquire.plan_batch(queue, run)
                # Act
                outcome["report"] = await acquire.run_batch(
                    guard, items, run, storage, queue["batch_sha256"], target=target
                )
                assert await guard.close()
            finally:
                await browser.close()

    with fixture_server(pdf) as origin, secop1_server(responses, received) as target:
        asyncio.run(scenario(origin, target))

    # Assert
    report = outcome["report"]
    assert received == [i["relative_path"] for i in queue["items"][:3]]
    assert report["stop_reason"] == "consecutive_failures"
    assert [i["outcome"] for i in report["items"]] == ["stored", "rejected", "rejected"]
    assert report["items"][1]["reason"] == "unexpected_response"
    assert report["items"][2]["reason"] == "pdf_eof_marker_missing"
    assert report["items"][0]["size_origin"] == "received_undeclared"
    assert report["items"][0]["sha256"] == hashlib.sha256(pdf).hexdigest()
    assert guard.release_after_worker(worker_closed=True)
    assert not list((tmp_path / "downloads").glob("*"))
    receipts = json.loads((run / flow.RECEIPTS_FILE).read_text(encoding="utf-8"))
    assert list(receipts) == [f"{queue['items'][0]['document_id']}:pdf"]
    assert len(list((run / acquire.ATTEMPTS_DIR).glob("*.json"))) == 3
    state = en01.DownloadState(run, storage)
    document = SimpleNamespace(extension="pdf", document_id=queue["items"][0]["document_id"])
    assert state.cached(document, en01.DOCUMENT_BYTES).sha256 == hashlib.sha256(pdf).hexdigest()


# ---------------------------------------------------------------- worker with in-memory fakes

CONTRACTS = "https://col.licitaciones.info/cliente/contratos"
PROFILE = "1234"


class FakeRequest:
    def __init__(self, url, method="GET", resource_type="xhr", post_data=None):
        self.url, self.method = url, method
        self.resource_type, self.post_data = resource_type, post_data


class FakeRoute:
    def __init__(self, request):
        self.request, self.aborted = request, False

    async def abort(self, _reason):
        self.aborted = True

    async def continue_(self):
        return None


class FakeResponse:
    def __init__(self, url, status=200, method="GET", resource_type="xhr", json_body=True):
        self.url, self.status = url, status
        self.request = FakeRequest(url, method, resource_type)
        self.headers = {"content-type": "application/json" if json_body else "text/html"}


class FakePage:
    def __init__(self, context, url="about:blank"):
        self.context, self.url = context, url

    def is_closed(self):
        return False

    async def goto(self, url, **_kwargs):
        # The provider app boots after the operator's manual login (simulated here).
        context = self.context
        self.url = CONTRACTS
        for response in (
            FakeResponse(CONTRACTS, resource_type="document", json_body=False),
            FakeResponse("https://col.licitaciones.info/cliente/get-config-user"),
        ):
            context.handlers["response"](response)
        feed = FakeRequest(
            "https://col.licitaciones.info/cliente/contratos/get-info/MP?perfiles="
            + context.perfiles,
            "POST",
        )
        route = FakeRoute(feed)
        await context.routes[0](route)
        context.feed_aborted = route.aborted

    async def evaluate(self, *_args):
        return {
            "url": CONTRACTS,
            "password_field": False,
            "client": True,
            "download_control": True,
            "ready_state": "complete",
            "text": "Contratos",
        }


class FakeContext:
    def __init__(self, perfiles):
        self.perfiles, self.handlers, self.routes, self.unrouted = perfiles, {}, [], []
        self.pages = [FakePage(self)]

    async def route(self, _pattern, handler):
        self.routes.append(handler)

    async def unroute(self, pattern, _handler):
        self.unrouted.append(pattern)

    def on(self, event, handler):
        self.handlers[event] = handler


def fake_worker_env(monkeypatch, tmp_path, *, perfiles=PROFILE, dedicated=True, confirm=True):
    run, queue = queued_run(tmp_path, count=2)
    work = run / acquire.WORKDIR
    work.mkdir()
    (work / "operator-ready.flag").write_text("", encoding="utf-8")
    if confirm:
        (work / "confirmed-batch.flag").write_text(
            queue["batch_sha256"] if confirm is True else "0" * 64, encoding="utf-8"
        )
    seen = {}

    class Guard:
        def __init__(self, marker):
            self.marker, self._owns_marker, self.context = marker, False, None
            self.native_downloads_denied, self.source = False, None

        async def start(self, _browser):
            self._owns_marker = True
            self.context = FakeContext(perfiles)
            self.native_downloads_denied = True
            seen["context"] = self.context
            return self.context.pages[0]

        async def close(self):
            return True

    class Manager:
        chromium = SimpleNamespace(connect_over_cdp=None)

        async def __aenter__(self):
            async def connect(*_a, **_k):
                return SimpleNamespace(contexts=[])

            self.chromium = SimpleNamespace(connect_over_cdp=connect)
            return self

        async def __aexit__(self, *_exc):
            return False

    async def fake_run_batch(guard, items, run_dir, storage, digest, *, log=None):
        seen["batch"] = {"items": len(items), "source": guard.source, "digest": digest}
        return {"items": [{"posts_forwarded": 1}], "stop_reason": "batch_complete"}

    monkeypatch.setattr("playwright.async_api.async_playwright", lambda: Manager())
    monkeypatch.setattr("eureka_nacional_secop1_popup.Secop1PopupGuard", Guard)
    monkeypatch.setattr(acquire, "run_batch", fake_run_batch)
    monkeypatch.setattr(acquire.asyncio, "sleep", _no_sleep)
    command = (
        f"msedge.exe --remote-debugging-port=9232 --user-data-dir={acquire.PROFILE_DIR}"
        if dedicated
        else "msedge.exe --remote-debugging-port=9232 --user-data-dir=X"
    )
    monkeypatch.setattr(
        acquire,
        "listener_info",
        lambda: {
            "owners": 1,
            "addresses": ["127.0.0.1"],
            "name": "msedge.exe",
            "command_line": command,
        },
    )
    asyncio.run(acquire.worker(run, tmp_path / "marker.lock", lambda: PROFILE))
    trace = json.loads((work / "result.json").read_text(encoding="utf-8"))
    closure = json.loads((work / "closure.json").read_text(encoding="utf-8"))
    flags = sorted(p.name for p in work.glob("*.flag"))
    return trace, closure, flags, seen


async def _no_sleep(_seconds):
    return None


def test_worker_runs_batch_only_after_ready_preflight_and_bound_confirmation(tmp_path, monkeypatch):
    trace, closure, flags, seen = fake_worker_env(monkeypatch, tmp_path)

    assert trace["preflight"]["ready_for_acquisition"] is True
    assert trace["preflight"]["profile"] == "only_configured"
    assert seen["context"].feed_aborted is True
    assert seen["batch"]["items"] == 2
    assert seen["batch"]["source"].url == CONTRACTS
    assert acquire.OFFICIAL_HOSTS in seen["context"].unrouted
    assert trace["stage"] == "batch_done"
    assert closure == {"marker_owned": True, "context_closed": True, "disconnected": True}
    assert flags == []


def test_worker_refuses_batch_without_matching_confirmation(tmp_path, monkeypatch):
    trace, closure, flags, seen = fake_worker_env(monkeypatch, tmp_path, confirm="wrong")

    assert trace["reason"] == "batch_confirmation_missing_or_mismatch"
    assert "batch" not in seen
    assert seen["context"].unrouted == []
    assert closure["context_closed"] is True
    assert flags == []


def test_worker_refuses_batch_with_other_profiles(tmp_path, monkeypatch):
    trace, _, _, seen = fake_worker_env(monkeypatch, tmp_path, perfiles=f"{PROFILE},999")

    assert trace["reason"] == "preflight_not_ready"
    assert trace["preflight"]["profile"] == "configured_with_others"
    assert "batch" not in seen


def test_worker_aborts_on_non_dedicated_browser_before_any_context(tmp_path, monkeypatch):
    trace, closure, _, seen = fake_worker_env(monkeypatch, tmp_path, dedicated=False)

    assert trace["reason"] == "not_dedicated_browser"
    assert "context" not in seen
    assert closure == {"marker_owned": False, "context_closed": False, "disconnected": False}
