"""Exercise EN-01 response streaming with synthetic loopback traffic only."""

import asyncio
import base64
import hashlib
import json
import re
import tempfile
import time
from contextlib import contextmanager, suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from threading import Thread

from eureka_nacional_en01 import DOCUMENT_BYTES
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from pypdf import PdfWriter

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError

DEADLINE = 12
CHUNK = 64 * 1024
CLOSE_TIMEOUT = 2
OVERSIZED_BYTES = 12 * 1024 * 1024
CASES = {
    "valid": "verified",
    "declared_oversize": "declared_size_limit",
    "undeclared_oversize": "stream_size_limit",
    "slow_body": "deadline",
    "slow_headers": "deadline",
    "truncated_pdf": "invalid_content",
    "lost_page_cdp": "cdp_lost",
    "uncertain_close": "cdp_lost",
}


class RejectionError(Exception):
    pass


def fixture_pdf():
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(buffer)
    return buffer.getvalue()


@contextmanager
def fixture_server(pdf):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            case = self.path.removeprefix("/")
            if case == "":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<title>EN-01 synthetic fixture</title>")
                return
            if case not in CASES:
                self.send_error(404)
                return
            if case == "slow_headers":
                time.sleep(DEADLINE + 1)
            oversized = case in {"declared_oversize", "undeclared_oversize"}
            body = pdf[:-20] if case == "truncated_pdf" else pdf
            size = OVERSIZED_BYTES if oversized else len(body)
            with suppress(OSError):
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", 'attachment; filename="synthetic.pdf"')
                if case != "undeclared_oversize":
                    self.send_header("Content-Length", str(size))
                self.end_headers()
                if oversized:
                    for _ in range(size // CHUNK):
                        self.wfile.write(b"x" * CHUNK)
                elif case == "slow_body":
                    self.wfile.write(body[:32])
                    self.wfile.flush()
                    time.sleep(DEADLINE + 1)
                    self.wfile.write(body[32:])
                else:
                    self.wfile.write(body)

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def response_length(event):
    status = event.get("responseStatusCode")
    headers = {}
    for header in event.get("responseHeaders", []):
        headers.setdefault(header["name"].lower(), []).append(header["value"])
    if (
        status != 200
        or headers.get("content-type") != ["application/pdf"]
        or headers.get("content-encoding", ["identity"]) != ["identity"]
    ):
        raise RejectionError("unexpected_response")
    lengths = headers.get("content-length", [])
    if not lengths:
        return None
    if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,18}", lengths[0]):
        raise RejectionError("invalid_length")
    length = int(lengths[0])
    if length > DOCUMENT_BYTES:
        raise RejectionError("declared_size_limit")
    return length


async def read_stream(cdp, request_id, length, result, case):
    stream = (await cdp.send("Fetch.takeResponseBodyAsStream", {"requestId": request_id}))["stream"]
    chunks = []
    while result["stream_bytes"] < DOCUMENT_BYTES:
        size = min(CHUNK, DOCUMENT_BYTES - result["stream_bytes"])
        part = await cdp.send("IO.read", {"handle": stream, "size": size})
        chunk = (
            base64.b64decode(part["data"], validate=True)
            if part.get("base64Encoded")
            else part["data"].encode()
        )
        if len(chunk) > size:
            raise RejectionError("cdp_chunk_exceeded")
        chunks.append(chunk)
        result["stream_bytes"] += len(chunk)
        if case in {"lost_page_cdp", "uncertain_close"}:
            cdp.on("close", lambda _session: result.update(page_cdp_closed=True))
            result["page_cdp_detach_ack"] = False
            try:
                async with asyncio.timeout(0.75):
                    await cdp.detach()
                    result["page_cdp_detach_ack"] = True
                    await cdp.send("IO.read", {"handle": stream, "size": 1})
            except PlaywrightError:
                result["page_cdp_result"] = "channel_error"
                raise RejectionError("cdp_lost") from None
            except TimeoutError:
                result["page_cdp_result"] = "channel_unresponsive"
                raise RejectionError("cdp_lost") from None
            raise RejectionError("fault_not_observed")
        if part["eof"]:
            await cdp.send("IO.close", {"handle": stream})
            result["io_closed"] = True
            await cdp.send("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})
            result["navigation_abort_ack"] = True
            if length is not None and result["stream_bytes"] != length:
                raise RejectionError("length_mismatch")
            return chunks
    raise RejectionError("stream_size_limit")


async def intercept(page, cdp, target, frame, result, case):
    paused = asyncio.get_running_loop().create_future()

    def on_response(event):
        if not paused.done():
            paused.set_result(event)

    cdp.on("Fetch.requestPaused", on_response)
    await cdp.send(
        "Fetch.enable", {"patterns": [{"urlPattern": target, "requestStage": "Response"}]}
    )
    await page.evaluate(
        """url => {
          const link = document.createElement('a');
          link.id = 'fixture';
          link.href = url;
          link.textContent = 'Synthetic PDF';
          document.body.append(link);
        }""",
        target,
    )
    started = time.monotonic()
    try:
        async with asyncio.timeout(DEADLINE):
            await page.locator("#fixture").click(no_wait_after=True, timeout=DEADLINE * 1000)
            event = await paused
            response = event["request"]
            if (
                response["url"] != target
                or response["method"] != "GET"
                or event["frameId"] != frame
            ):
                raise RejectionError("identity_mismatch")
            result["http_status"] = event.get("responseStatusCode")
            result["stage"] = "headers"
            length = response_length(event)
            result["declared_bytes"] = length
            result["stage"] = "body"
            chunks = await read_stream(cdp, event["requestId"], length, result, case)
            if time.monotonic() - started >= DEADLINE:
                raise TimeoutError
            return chunks
    finally:
        result["acquisition_seconds"] = round(time.monotonic() - started, 3)


async def close_target(page, browser_cdp, target_id):
    try:
        async with asyncio.timeout(CLOSE_TIMEOUT):
            closed = await browser_cdp.send("Target.closeTarget", {"targetId": target_id})
            if closed.get("success") and not page.is_closed():
                await page.wait_for_event("close", timeout=CLOSE_TIMEOUT * 1000)
    except (TimeoutError, PlaywrightError):
        return False
    return page.is_closed()


class LabSession:
    def __init__(self, browser, directory, origin, resource_origin, expected_hash):
        self.browser = browser
        self.directory = directory
        self.origin = origin
        self.resource_origin = resource_origin
        self.expected_hash = expected_hash
        self.context = None
        self.browser_cdp = None
        self.blocked = False

    async def start(self):
        self.context = await self.browser.new_context(accept_downloads=False)
        self.browser_cdp = await self.browser.new_browser_cdp_session()
        self.blocked = False

    async def recover(self):
        # The old, disposable context must be destroyed before the gate can reopen.
        async with asyncio.timeout(CLOSE_TIMEOUT):
            await self.context.close()
            await self.browser_cdp.detach()
        await self.start()

    async def run(self, case, label=None):
        result = {
            "case": label or case,
            "status": "started",
            "stage": "setup",
            "stream_bytes": 0,
            "io_closed": False,
            "navigation_abort_ack": False,
            "target_closed": False,
            "published": False,
        }
        if self.blocked:
            return {**result, "status": "session_blocked"}
        page = await self.context.new_page()
        await page.goto(self.origin, timeout=3000)
        cdp = await self.context.new_cdp_session(page)
        target_id = (await cdp.send("Target.getTargetInfo"))["targetInfo"]["targetId"]
        frame = (await cdp.send("Page.getFrameTree"))["frameTree"]["frame"]["id"]
        chunks = None
        result["stage"] = "navigation"
        try:
            chunks = await intercept(
                page, cdp, f"{self.resource_origin}/{case}", frame, result, case
            )
        except TimeoutError:
            result["status"] = "deadline"
        except PlaywrightError as error:
            result.update(status="protocol_error", exception_type=type(error).__name__)
        except RejectionError as error:
            result["status"] = str(error)
        finally:
            result["close_fault_simulated"] = case == "uncertain_close"
            close_started = time.monotonic()
            if not result["close_fault_simulated"]:
                result["target_closed"] = await close_target(page, self.browser_cdp, target_id)
            result["cleanup_seconds"] = round(time.monotonic() - close_started, 3)
            self.blocked = not result["target_closed"]
            result["session_blocked"] = self.blocked
        if chunks is not None and not self.blocked:
            store = LocalBinaryStorage(self.directory / result["case"])
            try:
                digest = hashlib.sha256()
                for chunk in chunks:
                    digest.update(chunk)
                if digest.hexdigest() != self.expected_hash:
                    raise AcquisitionError("invalid_content", "Unexpected synthetic PDF.")
                stored = store.store(
                    chunks,
                    original_name="synthetic.pdf",
                    content_type="application/pdf",
                    expected_size=result["stream_bytes"],
                    max_bytes=DOCUMENT_BYTES,
                )
                with store.open_verified(
                    stored.storage_path, stored.sha256, stored.observed_size, DOCUMENT_BYTES
                ) as pdf:
                    if pdf.read(5) != b"%PDF-" or stored.sha256 != self.expected_hash:
                        raise AcquisitionError("invalid_content", "Unexpected synthetic PDF.")
                result.update(status="verified", published=True, stage="verified")
            except AcquisitionError as error:
                result["status"] = error.code
        folder = self.directory / result["case"]
        result["stored_files"] = sum(path.is_file() for path in folder.glob("sha256/*/*"))
        return result


def validate_result(result, expected):
    saved = expected == "verified"
    if (
        result["status"] != expected
        or result["published"] != saved
        or result.get("stored_files", 0) != int(saved)
        or result["stream_bytes"] > DOCUMENT_BYTES
        or (saved and not (result["io_closed"] and result["target_closed"]))
    ):
        raise RuntimeError("Laboratory acceptance failed.")
    case = result["case"]
    if case in {"declared_oversize", "blocked_retry"} and result["stream_bytes"] != 0:
        raise RuntimeError("The body was read unexpectedly.")
    if case == "undeclared_oversize" and result["stream_bytes"] != DOCUMENT_BYTES:
        raise RuntimeError("The stream guard was not exercised.")
    if case == "lost_page_cdp" and not (result["target_closed"] and result["stream_bytes"]):
        raise RuntimeError("Independent target cleanup was not exercised after losing the channel.")
    if case == "uncertain_close" and not result["session_blocked"]:
        raise RuntimeError("Uncertain cleanup did not lock the session.")
    if case in {"valid", "recovered"} and not result["navigation_abort_ack"]:
        raise RuntimeError("Completed stream did not release the paused navigation.")
    if case in {"slow_body", "slow_headers"}:
        elapsed = result["acquisition_seconds"]
        if elapsed < DEADLINE or not result["target_closed"]:
            raise RuntimeError("The deadline or cancellation was not exercised.")


async def laboratory(directory, origin, resource_origin, pdf):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            channel="msedge",
            headless=True,
            args=[
                "--disable-background-networking",
                "--disable-component-update",
                "--no-proxy-server",
                "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
            ],
        )
        try:
            print(json.dumps({"edge": browser.version, "timeout": DEADLINE}), flush=True)
            lab = LabSession(
                browser, directory, origin, resource_origin, hashlib.sha256(pdf).hexdigest()
            )
            await lab.start()
            for case, expected in CASES.items():
                result = await lab.run(case)
                print(json.dumps(result), flush=True)
                validate_result(result, expected)
            blocked = await lab.run("valid", "blocked_retry")
            print(json.dumps(blocked), flush=True)
            validate_result(blocked, "session_blocked")
            await lab.recover()
            recovered = await lab.run("valid", "recovered")
            print(json.dumps(recovered), flush=True)
            validate_result(recovered, "verified")
        finally:
            await browser.close()


def main():
    pdf = fixture_pdf()
    with (
        tempfile.TemporaryDirectory(prefix="en01-cdp-stream-") as directory,
        fixture_server(pdf) as origin,
        fixture_server(pdf) as resource_origin,
    ):
        asyncio.run(laboratory(Path(directory), origin, resource_origin, pdf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
