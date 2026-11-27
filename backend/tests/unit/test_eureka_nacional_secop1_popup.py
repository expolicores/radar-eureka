"""Offline SECOP I regression. The browser fixtures use synthetic loopback only."""

import asyncio
import hashlib
import os
import sys
from contextlib import contextmanager, suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import parse_qs

import pytest
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from eureka_nacional_cdp_stream import (
    DEADLINE,
    DOCUMENT_BYTES,
    RejectionError,
    read_stream,
    response_length,
)
from eureka_nacional_cdp_stream_lab import fixture_pdf, fixture_server
from eureka_nacional_secop1_popup import Secop1PopupGuard

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

ROUTE = "/synthetic/26-13-12345678/fixture.pdf"
FORM = """({url, route, detached}) => {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = url;
    if (detached) {
        form.target = '_blank';
        form.rel = 'noopener';
    }
    const field = document.createElement('input');
    field.type = 'hidden';
    field.name = 'ruta';
    field.value = route;
    form.append(field);
    document.body.append(form);
    setTimeout(() => form.submit(), 0);
}"""
LAB = pytest.mark.skipif(
    os.getenv("RUN_EN01_POPUP_LAB") != "1", reason="requires isolated local Edge"
)


@contextmanager
def attachment_server(pdf, received, *, observe_headers=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if self.path != "/fixture" or not 0 < length <= 1024:
                self.send_error(400)
                return
            data = parse_qs(self.rfile.read(length).decode("ascii"))
            received.append(data == {"ruta": [ROUTE]})
            if observe_headers is not None:
                observe_headers(self.headers)
            with suppress(OSError):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(pdf)))
                self.send_header("Content-Disposition", 'attachment; filename="synthetic.pdf"')
                self.end_headers()
                self.wfile.write(pdf)

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/fixture"
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
def test_legacy_form_can_download_after_opener_identity_is_lost(tmp_path):
    received = []
    pdf = fixture_pdf()

    async def run(origin, target):
        async with async_playwright() as pw:
            browser = await launch(pw, tmp_path)
            try:
                context = await browser.new_context(accept_downloads=True)
                source = await context.new_page()
                await source.goto(origin, timeout=4000)
                control = await browser.new_browser_cdp_session()
                source_cdp = await context.new_cdp_session(source)
                source_info = (await source_cdp.send("Target.getTargetInfo"))["targetInfo"]
                created = []
                progress = asyncio.Queue()
                control.on(
                    "Target.targetCreated", lambda event: created.append(event["targetInfo"])
                )
                control.on("Browser.downloadProgress", progress.put_nowait)
                await control.send("Target.setDiscoverTargets", {"discover": True})
                await control.send(
                    "Browser.setDownloadBehavior",
                    {
                        "behavior": "allow",
                        "downloadPath": str(tmp_path),
                        "browserContextId": source_info["browserContextId"],
                        "eventsEnabled": True,
                    },
                )
                baseline = {
                    info["targetId"]
                    for info in (await control.send("Target.getTargets"))["targetInfos"]
                }
                await source.evaluate(FORM, {"url": target, "route": ROUTE, "detached": True})
                async with asyncio.timeout(4):
                    while (terminal := await progress.get())["state"] == "inProgress":
                        pass
                assert terminal["state"] == "completed"
                assert any(
                    not info.get("canAccessOpener")
                    for info in created
                    if info["type"] == "page"
                    and info.get("browserContextId") == source_info["browserContextId"]
                    and info["targetId"] not in baseline
                )
                assert received == [True]
                await context.close()
            finally:
                await browser.close()

    with fixture_server(pdf) as origin, attachment_server(pdf, received) as target:
        asyncio.run(run(origin, target))


@LAB
@pytest.mark.parametrize("case", ["associated", "unknown", "before_fetch", "native_denied"])
def test_isolated_popup_controls(case, tmp_path):
    pdf = fixture_pdf()
    received = []
    guard = Secop1PopupGuard(tmp_path / "uncertain.lock")

    async def run(origin, target):
        chunks = None
        async with async_playwright() as pw:
            browser = await launch(pw, tmp_path / "downloads")
            try:
                source = await guard.start(browser)
                await source.goto(origin, timeout=4000)
                if case == "unknown":
                    async with guard.context.expect_page(timeout=3500) as pending:
                        await source.evaluate(
                            "() => { window.open('about:blank','_blank','noopener'); }"
                        )
                    popup = await pending.value
                    with pytest.raises(RejectionError, match="popup_identity_unverified"):
                        await guard.prepare(popup, lambda _event: None)
                else:
                    popup = await guard.open_blank()
                    if case == "native_denied":
                        progress = asyncio.Queue()
                        guard.control.on("Browser.downloadProgress", progress.put_nowait)
                        await popup.evaluate(
                            FORM, {"url": target, "route": ROUTE, "detached": False}
                        )
                        async with asyncio.timeout(4):
                            while (terminal := await progress.get())["state"] == "inProgress":
                                pass
                        assert terminal["state"] == "canceled"
                    elif case == "before_fetch":
                        await popup.close()
                        with pytest.raises(RejectionError, match="popup_identity_unverified"):
                            await guard.prepare(popup, lambda _event: None)
                    elif case == "associated":
                        queue = asyncio.Queue()
                        cdp, frame = await guard.prepare(popup, queue.put_nowait)
                        result = {"stream_bytes": 0}
                        async with asyncio.timeout(DEADLINE):
                            await popup.evaluate(
                                FORM, {"url": target, "route": ROUTE, "detached": False}
                            )
                            request = await queue.get()
                            assert request["frameId"] == frame
                            assert request["request"]["method"] == "POST"
                            assert request["request"]["url"] == target
                            assert parse_qs(request["request"]["postData"]) == {"ruta": [ROUTE]}
                            rid = request["requestId"]
                            await cdp.send(
                                "Fetch.continueRequest",
                                {"requestId": rid, "interceptResponse": True},
                            )
                            response = await queue.get()
                            assert response["requestId"] == rid
                            assert response["frameId"] == frame
                            length = response_length(response, diagnostics=result)
                            chunks = await read_stream(cdp, rid, length, result)
                            assert result["io_closed"]
                            assert result["navigation_abort_ack"]
                assert await guard.close()
                assert popup.is_closed()
                assert source.is_closed()
                assert not guard.release_after_worker(worker_closed=False)
            finally:
                await browser.close()
        return chunks

    with fixture_server(pdf) as origin, attachment_server(pdf, received) as target:
        chunks = asyncio.run(run(origin, target))
    assert guard.release_after_worker(worker_closed=True)
    assert not guard.marker.exists()
    assert not list((tmp_path / "downloads").glob("*"))
    storage = LocalBinaryStorage(tmp_path / "binaries")
    if case == "associated":
        assert received == [True]
        stored = storage.store(
            chunks,
            original_name="fixture.pdf",
            content_type="application/pdf",
            expected_size=len(pdf),
            max_bytes=DOCUMENT_BYTES,
        )
        assert stored.sha256 == hashlib.sha256(pdf).hexdigest()
        with storage.open_verified(
            stored.storage_path, stored.sha256, stored.observed_size, DOCUMENT_BYTES
        ) as stream:
            assert stream.read() == pdf
    else:
        assert received == ([True] if case == "native_denied" else [])
        assert chunks is None
        assert not list(storage.root.glob("sha256/*/*"))


@contextmanager
def sign_in_fixture():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            if self.path == "/login":
                self.send_response(200)
                body = b"<form method='post'><button>Sign in</button></form>"
            elif self.path == "/contratos":
                signed_in = self.headers.get("Cookie") == "en01_fixture_session=issued"
                self.send_response(200 if signed_in else 401)
                body = b"<title>Contracts</title>" if signed_in else b"<title>Signed out</title>"
            else:
                self.send_error(404)
                return
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/login":
                self.send_error(404)
                return
            self.send_response(303)
            self.send_header("Location", "/contratos")
            self.send_header(
                "Set-Cookie", "en01_fixture_session=issued; Path=/; HttpOnly; SameSite=Lax"
            )
            self.end_headers()

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


@LAB
def test_disposable_context_can_sign_in_and_send_a_prearmed_cross_site_post(tmp_path):
    pdf = fixture_pdf()
    received, metadata = [], []
    guard = Secop1PopupGuard(tmp_path / "uncertain.lock")

    def check_headers(headers):
        metadata.append(
            {
                "origin": headers.get("Origin"),
                "cross_site": headers.get("Sec-Fetch-Site") == "cross-site",
                "provider_cookie_present": "en01_fixture_session" in headers.get("Cookie", ""),
            }
        )

    async def sign_in(source, origin):
        await source.goto(origin + "/login", timeout=4000)
        async with source.expect_navigation(url=origin + "/contratos", timeout=4000) as pending:
            await source.get_by_role("button", name="Sign in").click()
        response = await pending.value
        assert response.status == 200

    async def run(origin, target):
        async with async_playwright() as pw:
            browser = await launch(pw, tmp_path / "downloads")
            try:
                earlier = await browser.new_context()
                prior_page = await earlier.new_page()
                await sign_in(prior_page, origin)
                source = await guard.start(browser)
                status = await source.goto(origin + "/contratos", timeout=4000)
                assert status.status == 401
                await sign_in(source, origin)
                popup = await guard.open_blank()
                events = asyncio.Queue()
                cdp, frame = await guard.prepare(popup, events.put_nowait)
                result = {"stream_bytes": 0}
                async with asyncio.timeout(DEADLINE):
                    await popup.evaluate(FORM, {"url": target, "route": ROUTE, "detached": False})
                    event = await events.get()
                    request = event["request"]
                    assert received == []
                    assert event["frameId"] == frame
                    assert request["method"] == "POST"
                    assert request["url"] == target
                    assert parse_qs(request["postData"], strict_parsing=True) == {"ruta": [ROUTE]}
                    rid = event["requestId"]
                    await cdp.send(
                        "Fetch.continueRequest", {"requestId": rid, "interceptResponse": True}
                    )
                    response = await events.get()
                    assert response["requestId"] == rid
                    assert response["frameId"] == frame
                    length = response_length(response, diagnostics=result)
                    assert length == len(pdf)
                    body = b"".join(await read_stream(cdp, rid, length, result))
                    assert result["io_closed"]
                    assert result["navigation_abort_ack"]
                    assert hashlib.sha256(body).digest() == hashlib.sha256(pdf).digest()
                assert await guard.close()
                assert popup.is_closed()
                assert source.is_closed()
                assert not guard.release_after_worker(worker_closed=False)
                status = await prior_page.reload(timeout=4000)
                assert status.status == 200
                replacement = await browser.new_context()
                replacement_page = await replacement.new_page()
                status = await replacement_page.goto(origin + "/contratos", timeout=4000)
                assert status.status == 401
            finally:
                await browser.close()

    with (
        sign_in_fixture() as origin,
        attachment_server(pdf, received, observe_headers=check_headers) as target,
    ):
        asyncio.run(run(origin, target.replace("127.0.0.1", "localhost", 1)))
    assert received == [True]
    assert metadata == [{"origin": origin, "cross_site": True, "provider_cookie_present": False}]
    assert guard.release_after_worker(worker_closed=True)
    assert not list((tmp_path / "downloads").glob("*"))


def test_uncertain_context_close_blocks_next_attempt(tmp_path):
    async def run():
        marker = tmp_path / "uncertain.lock"
        control = SimpleNamespace(
            send=AsyncMock(
                side_effect=[
                    {"browserContextIds": ["owned"]},
                    {},
                    {"browserContextIds": []},
                    {"targetInfos": [{"browserContextId": "owned"}]},
                ]
            )
        )
        context = SimpleNamespace(
            new_page=AsyncMock(return_value=SimpleNamespace()),
            new_cdp_session=AsyncMock(
                return_value=SimpleNamespace(
                    send=AsyncMock(return_value={"targetInfo": {"browserContextId": "owned"}})
                )
            ),
            close=AsyncMock(),
        )
        browser = SimpleNamespace(
            new_browser_cdp_session=AsyncMock(return_value=control),
            new_context=AsyncMock(return_value=context),
        )
        guard = Secop1PopupGuard(marker)
        await guard.start(browser)
        assert not await guard.close()
        assert not guard.release_after_worker(worker_closed=True)
        assert marker.exists()
        with pytest.raises(RejectionError, match="stream_close_unverified"):
            await Secop1PopupGuard(marker).start(browser)
        browser.new_context.assert_awaited_once()
        assert [item.args[0] for item in control.send.await_args_list] == [
            "Target.getBrowserContexts",
            "Browser.setDownloadBehavior",
            "Target.getBrowserContexts",
            "Target.getTargets",
        ]

    asyncio.run(run())
