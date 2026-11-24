"""Opt-in, bounded SECOP transfer for the EN-01 browser session."""

import base64
import time
from contextlib import suppress
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from playwright.sync_api import Error as PlaywrightError

from public_procurement.documents.adapters.secop import RETRIEVE_PATH, validate_url
from public_procurement.documents.domain.document import AcquisitionError

CHUNK_BYTES = 65536

START = """({key, url, limit, timeout}) => {
    const controller = new AbortController();
    const state = {controller, pending: true, error: null, status: null, size: null};
    window[key] = state;
    state.timer = setTimeout(() => {
        state.error = "edge_timeout";
        controller.abort();
    }, timeout);
    fetch(url, {
        method: "GET", credentials: "include", redirect: "error",
        cache: "no-store", signal: controller.signal
    }).then(response => {
        state.status = response.status;
        const reject = code => { state.error = code; controller.abort(); };
        if (response.status !== 200 || response.redirected || response.url !== new URL(url).href) {
            reject("edge_http_error"); return;
        }
        const media = (response.headers.get("Content-Type") || "")
            .split(";")[0].trim().toLowerCase();
        if (media === "text/html" || !response.body) {
            reject("invalid_content"); return;
        }
        const length = response.headers.get("Content-Length") || "";
        if (!/^\\d+$/.test(length) || !Number.isSafeInteger(Number(length))) {
            reject("edge_length_unknown"); return;
        }
        state.size = Number(length);
        if (!state.size || state.size > limit) {
            reject(state.size ? "too_large" : "empty_file"); return;
        }
        state.reader = response.body.getReader();
    }).catch(() => {
        state.error ||= "edge_fetch_rejected";
        controller.abort();
    }).finally(() => { state.pending = false; });
}"""

READ = """({key, maxChunk}) => {
    const s = window[key];
    if (!s || s.error || s.busy || !s.reader) return false;
    s.busy = true;
    (async () => {
        if (!s.rest?.length) {
            const result = await s.reader.read();
            if (result.done) { s.eof = true; return; }
            s.rest = result.value;
            s.received = (s.received || 0) + s.rest.length;
            if (s.received > s.size) {
                s.error = "too_large"; s.controller.abort(); return;
            }
        }
        const part = s.rest.subarray(0, maxChunk);
        s.rest = s.rest.subarray(part.length);
        let text = "";
        for (const n of part) text += String.fromCharCode(n);
        s.chunk = btoa(text);
    })().catch(() => {
        s.error ||= "edge_read_failed";
        s.controller.abort();
    }).finally(() => { s.busy = false; });
    return true;
}"""

STATE = """key => {
    const s = window[key];
    if (!s) return null;
    const out = {error:s.error, pending:s.pending || s.busy, status:s.status,
                 size:s.size, eof:s.eof, chunk:s.chunk};
    delete s.chunk;
    return out;
}"""

CANCEL = """key => {
    const s = window[key];
    if (!s) return false;
    s.controller.abort();
    if (s.reader) s.reader.cancel().catch(() => {});
    clearTimeout(s.timer);
    delete window[key];
    return s.controller.signal.aborted;
}"""


def download_from_edge(page, document, storage, settings, diagnostics):
    url = document.source_url
    validate_url(url)
    parts = urlsplit(url)
    if (
        parts.path != RETRIEVE_PATH
        or parts.fragment
        or parse_qs(parts.query, keep_blank_values=True).get("DocumentId") != [document.document_id]
        or document.extension not in {"pdf", "docx"}
        or urlsplit(page.url).hostname != "col.licitaciones.info"
    ):
        raise AcquisitionError("edge_target_invalid", "Destino o formato fuera de EN-01.")
    max_bytes = min(settings.document_max_bytes, 16 * 1024 * 1024)
    timeout = min(settings.document_timeout_seconds, 12)
    deadline = time.monotonic() + timeout
    key = "__en01_download_" + uuid4().hex
    diagnostics.update(stage="edge_headers", cancellation_confirmed=False)
    started = False

    def state():
        while time.monotonic() < deadline:
            current = page.evaluate(STATE, key)
            if time.monotonic() >= deadline:
                break
            if not current:
                raise AcquisitionError("edge_session_lost", "Se perdi? el contexto de descarga.")
            diagnostics["http_status"] = current.get("status")
            if current.get("error"):
                raise AcquisitionError(current["error"], "Edge cancel? o rechaz? la descarga.")
            if not current.get("pending"):
                return current
            page.wait_for_timeout(25)
        raise AcquisitionError("edge_timeout", "Se agot? el plazo de descarga en Edge.")

    try:
        # Mark before evaluation so an uncertain start also triggers cancellation.
        started = True
        page.evaluate(
            START, {"key": key, "url": url, "limit": max_bytes, "timeout": int(timeout * 1000)}
        )
        initial = state()
        size = initial.get("size")
        if not isinstance(size, int) or not 0 < size <= max_bytes:
            raise AcquisitionError("edge_length_invalid", "Tama?o no verificable en Edge.")
        diagnostics["stage"] = "edge_stream"

        def chunks():
            observed = 0
            while time.monotonic() < deadline:
                if not page.evaluate(READ, {"key": key, "maxChunk": CHUNK_BYTES}):
                    state()
                    raise AcquisitionError("edge_read_failed", "Edge no inici? la lectura.")
                item = state()
                if item.get("eof"):
                    return
                chunk = base64.b64decode(item.get("chunk") or "", validate=True)
                if not chunk or len(chunk) > CHUNK_BYTES or observed + len(chunk) > max_bytes:
                    raise AcquisitionError("too_large", "Bloque excede el l?mite establecido.")
                if not observed:
                    signature = b"%PDF-" if document.extension == "pdf" else b"PK\x03\x04"
                    if not chunk.startswith(signature):
                        raise AcquisitionError(
                            "invalid_content", "El binario no coincide con el tipo anunciado."
                        )
                observed += len(chunk)
                yield chunk
            raise AcquisitionError("edge_timeout", "Se agot? el plazo de descarga en Edge.")

        media = (
            "application/pdf"
            if document.extension == "pdf"
            else ("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        )
        stored = storage.store(
            chunks(),
            original_name=f"{document.original_name}.{document.extension}",
            content_type=media,
            expected_size=size,
            max_bytes=max_bytes,
        )
        diagnostics["stage"] = "completed"
        return stored
    except AcquisitionError as error:
        diagnostics["rejection_reason"] = error.code
        raise
    except (PlaywrightError, ValueError, TypeError) as error:
        diagnostics.update(rejection_reason="edge_protocol", exception_type=type(error).__name__)
        raise AcquisitionError(
            "edge_protocol", "Edge no devolvi? una transferencia verificable."
        ) from None
    finally:
        if started:
            with suppress(PlaywrightError):
                diagnostics["cancellation_confirmed"] = page.evaluate(CANCEL, key) is True
