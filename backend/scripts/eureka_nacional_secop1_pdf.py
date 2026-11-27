"""Bounded body acceptance for the SECOP I VerDocumento PDF response.

Reuses the existing CDP stream reader. The only policy change against SECOP II is that a
missing Content-Length is accepted; then the received size is recorded instead and the PDF
must start with `%PDF-` and carry `%%EOF` near its end. `%%EOF` is a heuristic completeness
check, not an integrity guarantee. Nothing is written here: the caller stores the returned
bytes only after this function has accepted them.
"""

import asyncio
import hashlib
import time

from eureka_nacional_cdp_stream import (
    DEADLINE,
    DOCUMENT_BYTES,
    RejectionError,
    read_stream,
    response_length,
)

PDF_SIGNATURE = b"%PDF-"
PDF_EOF_MARKER = b"%%EOF"
EOF_WINDOW = 1024  # PDF readers accept %%EOF within the last 1024 bytes.


def has_eof_marker(body):
    return PDF_EOF_MARKER in body[-EOF_WINDOW:]


def validate_pdf_body(chunks, declared, trace):
    """Accept a fully read body or raise; on success record size, hash and size origin."""
    if trace.get("io_closed") is not True or trace.get("navigation_abort_ack") is not True:
        raise RejectionError("stream_close_unverified")
    body = b"".join(chunks)
    size = len(body)
    if size != trace.get("stream_bytes"):
        raise RejectionError("stream_accounting_mismatch")
    if size == 0:
        raise RejectionError("empty_body")
    if size > DOCUMENT_BYTES:
        raise RejectionError("stream_size_limit")
    if declared is not None and size != declared:
        raise RejectionError("length_mismatch")
    if not body.startswith(PDF_SIGNATURE):
        raise RejectionError("invalid_pdf_signature")
    if not has_eof_marker(body):
        raise RejectionError("pdf_eof_marker_missing")
    trace.update(
        size_origin="declared" if declared is not None else "received_undeclared",
        received_bytes=size,
        sha256=hashlib.sha256(body).hexdigest(),
        pdf_signature=True,
        pdf_eof_marker=True,
    )
    return body


async def read_secop1_pdf(cdp, request_id, event, trace, *, started):
    """Headers, bounded stream and body checks within the acquisition deadline.

    Any failure raises RejectionError and returns no bytes, so nothing partial is stored.
    """
    declared = response_length(event, diagnostics=trace)
    trace["declared_size"] = declared is not None
    remaining = DEADLINE - (time.monotonic() - started)
    if remaining <= 0:
        raise RejectionError("acquisition_timeout")
    try:
        async with asyncio.timeout(remaining):
            chunks = await read_stream(cdp, request_id, declared, trace)
    except TimeoutError:
        raise RejectionError("acquisition_timeout") from None
    except RejectionError:
        raise
    except Exception as error:  # CDP stream errors: interrupted, never accepted
        raise RejectionError("stream_interrupted") from error
    if time.monotonic() - started >= DEADLINE:
        raise RejectionError("acquisition_timeout")
    return validate_pdf_body(chunks, declared, trace)
