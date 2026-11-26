"""Bounded SECOP PDF streaming shared by EN-01 acquisition paths."""

import asyncio
import base64
import re
import time
from contextlib import suppress
from urllib.parse import parse_qs, urlsplit

from eureka_nacional_experience import document_title
from licitaciones_cdp_runtime import validate_cdp_url

from public_procurement.documents.adapters.secop import RETRIEVE_PATH, validate_url
from public_procurement.documents.domain.document import AcquisitionError

DOCUMENT_BYTES = 10 * 1024 * 1024
DEADLINE = 12
CHUNK = 64 * 1024
CLOSE_TIMEOUT = 2
OPERATION_MARGIN = 38
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


def response_length(event, *, diagnostics=None):
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
    if length > DOCUMENT_BYTES:
        raise RejectionError("declared_size_limit")
    return length


async def read_stream(cdp, request_id, length, result, *, after_chunk=None):
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


async def stream_pdf(url, result, *, cdp_url="http://127.0.0.1:9232"):
    from playwright.async_api import Error as PlaywrightError
    from playwright.async_api import async_playwright

    result["tab_opened"] = False
    validate_cdp_url(cdp_url)
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(cdp_url, timeout=5000, no_defaults=True)
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
            control = await browser.new_browser_cdp_session()
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
                result["stage"] = "preflight"
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
                cdp = await source.context.new_cdp_session(page)
                target_id = (await cdp.send("Target.getTargetInfo"))["targetInfo"]["targetId"]
                frame = (await cdp.send("Page.getFrameTree"))["frameTree"]["frame"]["id"]
                await cdp.send("Network.enable")
                await cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
                await cdp.send("Network.setBypassServiceWorker", {"bypass": True})
                queue = asyncio.Queue()
                cdp.on("Fetch.requestPaused", queue.put_nowait)
                await cdp.send(
                    "Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]}
                )
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
                        length = response_length(event, diagnostics=result)
                        if not length:
                            raise RejectionError("missing_declared_size")
                        result["stage"] = "body"
                        chunks = await read_stream(cdp, rid, length, result)
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


def download_stream_pdf(document, storage, marker, diagnostics, *, cdp_url):
    from playwright.async_api import Error as PlaywrightError

    validate_target(document)
    diagnostics.update(stream_bytes=0, requests_forwarded=0)
    try:
        with marker.open("x", encoding="utf-8") as lock:
            lock.write(document.document_id + "\n")
    except FileExistsError:
        raise AcquisitionError(
            "stream_close_unverified", "Hay un cierre pendiente en Edge."
        ) from None
    try:
        chunks = asyncio.run(stream_pdf(document.source_url, diagnostics, cdp_url=cdp_url))
        if not all(
            diagnostics.get(key) for key in ("io_closed", "navigation_abort_ack", "target_closed")
        ):
            raise RejectionError("unverified_close")
        if not next((chunk for chunk in chunks if chunk), b"").startswith(b"%PDF-"):
            raise RejectionError("invalid_pdf_signature")
        stored = storage.store(
            chunks,
            original_name="document.pdf",
            content_type="application/pdf",
            expected_size=diagnostics["stream_bytes"],
            max_bytes=DOCUMENT_BYTES,
        )
        with storage.open_verified(
            stored.storage_path, stored.sha256, stored.observed_size, DOCUMENT_BYTES
        ) as stream:
            if stream.read(5) != b"%PDF-":
                raise RejectionError("invalid_pdf_signature")
        return stored
    except TimeoutError:
        diagnostics["error"] = "deadline"
        raise AcquisitionError("deadline", "Se agotó el plazo de Edge.") from None
    except (PlaywrightError, RejectionError) as error:
        code = str(error) if isinstance(error, RejectionError) else "protocol_error"
        diagnostics.update(error=code, exception_type=type(error).__name__)
        raise AcquisitionError(code, "Descarga de Edge no verificada.") from None
    finally:
        # If interrupted before the browser reported whether a target exists, keep the marker.
        state_known = "tab_opened" in diagnostics
        diagnostics["session_blocked"] = not (
            (state_known and not diagnostics["tab_opened"]) or diagnostics.get("target_closed")
        )
        if not diagnostics["session_blocked"]:
            marker.unlink()
