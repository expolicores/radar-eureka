"""Bounded SECOP PDF streaming shared by EN-01 acquisition paths."""

import asyncio
import base64
import json
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from eureka_nacional_experience import document_title
from licitaciones_cdp_runtime import validate_cdp_url

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.adapters.secop import RETRIEVE_PATH, validate_url
from public_procurement.documents.domain.document import AcquisitionError, StoredBinary

DOCUMENT_BYTES = 10 * 1024 * 1024
# Exceptional ceiling, only when a hash-bound plan authorizes it for one governing document.
MAX_STREAM_BYTES = 16 * 1024 * 1024
DEADLINE = 12
CHUNK = 64 * 1024
CLOSE_TIMEOUT = 2
WORKER_TIMEOUT = 35
OPERATION_MARGIN = 38
WORKER_SCRIPT = Path(__file__).resolve()
MARKER_NAME = "cdp-stream-live-uncertain.lock"


class RejectionError(Exception):
    pass


def is_notice(title):
    return bool(re.match(r"^aviso de (?:la )?(?:invitacion|convocatoria)\b", document_title(title)))


def validate_target(document):
    url = document.source_url
    validate_url(url)
    parsed = urlsplit(url)
    if (
        not re.fullmatch(r"[0-9]{1,40}", document.document_id)
        or document.extension != "pdf"
        or parsed.path != RETRIEVE_PATH
        or parsed.fragment
        or parse_qs(parsed.query, keep_blank_values=True) != {"DocumentId": [document.document_id]}
    ):
        raise AcquisitionError("unverified_target", "Destino fuera del alcance de EN-01.")


def fallback_eligible(direct):
    trace = direct.get("diagnostics", {})
    return (
        direct.get("error") == "http_error"
        and trace.get("http_status") == 403
        and not trace.get("redirects")
    )


def stream_limit(max_bytes):
    if not isinstance(max_bytes, int) or not DOCUMENT_BYTES <= max_bytes <= MAX_STREAM_BYTES:
        raise RejectionError("invalid_size_limit")
    return max_bytes


def response_length(event, *, diagnostics=None, max_bytes=DOCUMENT_BYTES):
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
    if diagnostics is not None:
        diagnostics["declared_bytes"] = length
    if length > stream_limit(max_bytes):
        raise RejectionError("declared_size_limit")
    return length


async def read_stream(
    cdp, request_id, length, result, *, after_chunk=None, max_bytes=DOCUMENT_BYTES
):
    limit = stream_limit(max_bytes)
    stream = (await cdp.send("Fetch.takeResponseBodyAsStream", {"requestId": request_id}))["stream"]
    chunks = []
    while result["stream_bytes"] < limit:
        size = min(CHUNK, limit - result["stream_bytes"])
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
        if after_chunk is not None:
            await after_chunk(stream)
        if part["eof"]:
            await cdp.send("IO.close", {"handle": stream})
            result["io_closed"] = True
            await cdp.send("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})
            result["navigation_abort_ack"] = True
            if length is not None and result["stream_bytes"] != length:
                raise RejectionError("length_mismatch")
            return chunks
    raise RejectionError("stream_size_limit")


async def close_target(page, browser_cdp, target_id):
    from playwright.async_api import Error as PlaywrightError

    try:
        async with asyncio.timeout(CLOSE_TIMEOUT):
            closed = await browser_cdp.send("Target.closeTarget", {"targetId": target_id})
            if closed.get("success") and not page.is_closed():
                await page.wait_for_event("close", timeout=CLOSE_TIMEOUT * 1000)
    except (TimeoutError, PlaywrightError):
        return False
    return page.is_closed()


async def stream_pdf(url, result, *, cdp_url="http://127.0.0.1:9232", max_bytes=DOCUMENT_BYTES):
    from playwright.async_api import Error as PlaywrightError
    from playwright.async_api import async_playwright

    result.update(tab_opened=False, stage="driver_start")
    validate_cdp_url(cdp_url)
    async with async_playwright() as pw:
        result["stage"] = "cdp_connect"
        browser = await pw.chromium.connect_over_cdp(cdp_url, timeout=5000, no_defaults=True)
        result["stage"] = "context_lookup"
        pages = [
            p
            for ctx in browser.contexts
            for p in ctx.pages
            if urlsplit(p.url).scheme == "https"
            and urlsplit(p.url).hostname == "col.licitaciones.info"
            and urlsplit(p.url).path.rstrip("/") == "/cliente/contratos"
        ]
        if len(pages) != 1:
            raise RejectionError("authorized_tab_unavailable")
        source = pages[0]
        async with asyncio.timeout(8):
            result["stage"] = "browser_session"
            control = await browser.new_browser_cdp_session()
            result["stage"] = "popup_open"
            result.pop("tab_opened")
            async with source.context.expect_page(timeout=3500) as popup:
                opened = await source.evaluate(
                    """() => window.open('about:blank', '_blank') !== null"""
                )
                if not opened:
                    result["tab_opened"] = False
                    raise RejectionError("popup_blocked")
            page = await popup.value
        result["tab_opened"] = True
        target_id = None
        chunks = None
        try:
            async with asyncio.timeout(8):
                result["stage"] = "popup_validate"
                if page.url != "about:blank" or await page.opener() != source:
                    raise RejectionError("target_not_isolated")
                if not await page.evaluate(
                    """() => {
                        const expected = 'https://col.licitaciones.info';
                        return window.opener?.location?.origin === expected && origin === expected;
                    }"""
                ):
                    raise RejectionError("authorized_origin_not_preserved")
                result["authorized_origin_preserved"] = True
                result["stage"] = "page_session"
                cdp = await source.context.new_cdp_session(page)
                target_id = (await cdp.send("Target.getTargetInfo"))["targetInfo"]["targetId"]
                frame = (await cdp.send("Page.getFrameTree"))["frameTree"]["frame"]["id"]
                await cdp.send("Network.enable")
                await cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
                await cdp.send("Network.setBypassServiceWorker", {"bypass": True})
                queue = asyncio.Queue()
                result["stage"] = "interception_setup"
                cdp.on("Fetch.requestPaused", queue.put_nowait)
                await cdp.send(
                    "Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]}
                )
                result["stage"] = "link_prepare"
                await page.evaluate(
                    """href => {
                    const a=document.createElement('a');
                    a.id='en01-single-link';
                    a.href=href;
                    a.textContent='Documento SECOP';
                    document.body.append(a);
                }""",
                    url,
                )
            result["stage"] = "click"
            started = time.monotonic()
            try:
                async with asyncio.timeout(DEADLINE):
                    await page.locator("#en01-single-link").click(
                        no_wait_after=True, timeout=DEADLINE * 1000
                    )
                    while True:
                        event = await queue.get()
                        data = event["request"]
                        ident = (
                            data["url"] == url
                            and data["method"] == "GET"
                            and event["frameId"] == frame
                        )
                        rid = event["requestId"]
                        if "responseStatusCode" not in event and "responseErrorReason" not in event:
                            if not ident or result["requests_forwarded"]:
                                await cdp.send(
                                    "Fetch.failRequest",
                                    {"requestId": rid, "errorReason": "BlockedByClient"},
                                )
                                continue
                            result["requests_forwarded"] = 1
                            result["stage"] = "waiting_headers"
                            await cdp.send(
                                "Fetch.continueRequest",
                                {"requestId": rid, "interceptResponse": True},
                            )
                            continue
                        if not ident:
                            raise RejectionError("response_identity_mismatch")
                        result["response_intercepted"] = True
                        result["http_status"] = event.get("responseStatusCode")
                        result["stage"] = "headers"
                        length = response_length(event, diagnostics=result, max_bytes=max_bytes)
                        if not length:
                            raise RejectionError("missing_declared_size")
                        result["stage"] = "body"
                        chunks = await read_stream(cdp, rid, length, result, max_bytes=max_bytes)
                        if time.monotonic() - started >= DEADLINE:
                            chunks = None
                            raise TimeoutError
                        result["body_complete"] = True
                        break
            finally:
                result["acquisition_seconds"] = round(time.monotonic() - started, 3)
        finally:
            cleanup = time.monotonic()
            if target_id is not None:
                result["target_closed"] = await close_target(page, control, target_id)
            else:
                with suppress(PlaywrightError, TimeoutError), asyncio.timeout(CLOSE_TIMEOUT):
                    await page.close()
                result["target_closed"] = page.is_closed()
            result["cleanup_seconds"] = round(time.monotonic() - cleanup, 3)
        return chunks


async def acquire_pdf(url, storage, diagnostics, *, cdp_url, max_bytes=DOCUMENT_BYTES):
    chunks = await stream_pdf(url, diagnostics, cdp_url=cdp_url, max_bytes=max_bytes)
    if diagnostics.get("requests_forwarded") != 1 or not all(
        diagnostics.get(key) is True
        for key in ("io_closed", "navigation_abort_ack", "target_closed")
    ):
        raise RejectionError("unverified_close")
    if not next((chunk for chunk in chunks if chunk), b"").startswith(b"%PDF-"):
        raise RejectionError("invalid_pdf_signature")
    return storage.store(
        chunks,
        original_name="document.pdf",
        content_type="application/pdf",
        expected_size=diagnostics["stream_bytes"],
        max_bytes=stream_limit(max_bytes),
    )


def worker_main():
    from playwright.async_api import Error as PlaywrightError

    payload = json.load(sys.stdin)
    document = SimpleNamespace(
        source_url=payload["source_url"], document_id=payload["document_id"], extension="pdf"
    )
    diagnostics = {
        "stream_bytes": 0,
        "requests_forwarded": 0,
        "tab_opened": False,
        "stage": "worker_init",
    }
    stored = None
    try:
        validate_target(document)
        staged = LocalBinaryStorage(Path(payload["staging"]))
        stored = asyncio.run(
            acquire_pdf(
                document.source_url,
                staged,
                diagnostics,
                cdp_url=payload["cdp_url"],
                max_bytes=stream_limit(payload.get("max_bytes", DOCUMENT_BYTES)),
            )
        )
    except TimeoutError as error:
        diagnostics.update(error="deadline", exception_type=type(error).__name__)
    except (PlaywrightError, RejectionError, AcquisitionError, OSError) as error:
        code = getattr(error, "code", None)
        if not code:
            code = str(error) if isinstance(error, RejectionError) else "protocol_error"
        diagnostics.update(error=code, exception_type=type(error).__name__)
    print(json.dumps({"stored": asdict(stored) if stored else None, "diagnostics": diagnostics}))


def invoke_worker(document, staging, diagnostics, *, cdp_url, max_bytes=DOCUMENT_BYTES):
    payload = {
        "source_url": document.source_url,
        "document_id": document.document_id,
        "staging": str(staging.root),
        "cdp_url": cdp_url,
        "max_bytes": stream_limit(max_bytes),
    }
    try:
        worker = subprocess.run(  # noqa: S603
            [sys.executable, str(WORKER_SCRIPT), "--stream-worker"],
            input=json.dumps(payload),
            capture_output=True,
            encoding="utf-8",
            timeout=WORKER_TIMEOUT,
            check=True,
        )
    except subprocess.TimeoutExpired:
        diagnostics.update(worker_closed=True, error="worker_timeout")
        raise AcquisitionError("worker_timeout", "Se agotó el plazo del trabajador Edge.") from None
    except subprocess.CalledProcessError:
        diagnostics.update(worker_closed=True, error="worker_failed")
        raise AcquisitionError("worker_failed", "El trabajador Edge terminó con error.") from None
    except OSError:
        diagnostics["error"] = "worker_start_failed"
        raise AcquisitionError(
            "worker_start_failed", "No se pudo completar el trabajador Edge."
        ) from None
    diagnostics["worker_closed"] = True
    try:
        result = json.loads(worker.stdout)
        metadata = result["stored"]
        diagnostics.update(result["diagnostics"], worker_closed=True)
        if metadata is not None:
            return StoredBinary(**metadata)
    except (KeyError, TypeError, ValueError):
        diagnostics["error"] = "worker_protocol"
        raise AcquisitionError(
            "worker_protocol", "Respuesta inválida del trabajador Edge."
        ) from None
    raise AcquisitionError(
        diagnostics.get("error", "worker_failed"), "Descarga Edge no verificada."
    )


def wait_for_worker(
    document, staging, diagnostics, *, cdp_url, parent_page, max_bytes=DOCUMENT_BYTES
):
    from playwright.sync_api import Error as PlaywrightError

    # The parent's Playwright routes may need dispatch before the child can attach.
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            invoke_worker,
            document,
            staging,
            diagnostics,
            cdp_url=cdp_url,
            **({} if max_bytes == DOCUMENT_BYTES else {"max_bytes": max_bytes}),
        )
        while not future.done():
            try:
                parent_page.wait_for_timeout(50)
            except PlaywrightError:
                diagnostics["parent_pump_interrupted"] = True
                break
        return future.result()


def download_stream_pdf(
    document, storage, marker, diagnostics, *, cdp_url, parent_page=None, max_bytes=DOCUMENT_BYTES
):
    limit = stream_limit(max_bytes)
    # The default ceiling keeps the historical call shape; only an exception is forwarded.
    extra = {} if limit == DOCUMENT_BYTES else {"max_bytes": limit}
    validate_target(document)
    validate_cdp_url(cdp_url)
    diagnostics.update(stream_bytes=0, requests_forwarded=0, worker_closed=False)
    try:
        with marker.open("x", encoding="utf-8") as lock:
            lock.write(document.document_id + "\n")
    except FileExistsError:
        raise AcquisitionError(
            "stream_close_unverified", "Hay un cierre pendiente en Edge."
        ) from None
    try:
        with tempfile.TemporaryDirectory(prefix="en01-edge-worker-") as temporary:
            staging = LocalBinaryStorage(Path(temporary))
            if parent_page is None:
                result = invoke_worker(document, staging, diagnostics, cdp_url=cdp_url, **extra)
            else:
                result = wait_for_worker(
                    document,
                    staging,
                    diagnostics,
                    cdp_url=cdp_url,
                    parent_page=parent_page,
                    **extra,
                )
            if diagnostics["requests_forwarded"] != 1 or not all(
                diagnostics.get(key) is True
                for key in ("worker_closed", "io_closed", "navigation_abort_ack", "target_closed")
            ):
                raise AcquisitionError("unverified_close", "Cierre no verificado en Edge.")
            with staging.open_verified(
                result.storage_path, result.sha256, result.observed_size, limit
            ) as stream:
                if stream.read(5) != b"%PDF-":
                    raise AcquisitionError("invalid_pdf_signature", "El archivo no es un PDF.")
                stream.seek(0)
                return storage.store(
                    iter(lambda: stream.read(CHUNK), b""),
                    original_name="document.pdf",
                    content_type="application/pdf",
                    expected_size=result.observed_size,
                    max_bytes=limit,
                )
    finally:
        safe = (diagnostics.get("worker_closed") is True) and (
            diagnostics.get("tab_opened") is False or diagnostics.get("target_closed") is True
        )
        diagnostics["session_blocked"] = not safe
        if safe:
            marker.unlink()


if __name__ == "__main__" and sys.argv[1:] == ["--stream-worker"]:
    worker_main()
