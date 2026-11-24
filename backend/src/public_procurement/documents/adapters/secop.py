"""Descarga HTTPS con redirecciones manuales y streaming acotado."""

import time
from collections.abc import Iterator
from http.client import HTTPException
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..domain.document import AcquisitionError, SourceDocument, StoredBinary
from ..ports import BinaryStorage

ALLOWED_HOST = "community.secop.gov.co"
RETRIEVE_PATH = "/Public/Archive/RetrieveFile/Index"
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
REPORTED_MEDIA_TYPES = {
    "application/pdf",
    "application/octet-stream",
    "application/json",
    "application/problem+json",
    "application/xml",
    "text/xml",
    "text/html",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def diagnostic_media_type(headers) -> str | None:
    value = (headers.get("Content-Type") or "").partition(";")[0].strip().lower() if headers else ""
    if not value:
        return None
    return value if value in REPORTED_MEDIA_TYPES else "other"


def validate_url(url: str) -> None:
    try:
        parsed = urlsplit(url)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname == ALLOWED_HOST
            and parsed.port in (None, 443)
            and not parsed.username
            and not parsed.password
        )
    except ValueError:
        valid = False
    if not valid:
        raise AcquisitionError(
            "unsafe_url", "La URL no pertenece al origen HTTPS permitido de SECOP."
        )


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


class SecopDownloader:
    def __init__(self, timeout_seconds: float, max_bytes: int) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes
        self._opener = build_opener(_NoRedirect())

    def download(
        self,
        source: SourceDocument,
        storage: BinaryStorage,
        *,
        diagnostics: dict[str, Any] | None = None,
    ) -> StoredBinary:
        trace: dict[str, Any] = {
            "stage": "validate_url",
            "http_status": None,
            "exception_type": None,
            "content_type": None,
            "rejection_reason": None,
            "redirects": [],
        }
        url = source.source_url
        try:
            if not url:
                raise AcquisitionError("missing_url", "La fuente no publica URL de descarga.")
            started = time.monotonic()
            for _ in range(6):
                trace["stage"] = "validate_url"
                validate_url(url)
                trace.update(
                    stage="open_response",
                    http_status=None,
                    exception_type=None,
                    content_type=None,
                )
                remaining = self.timeout_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    raise AcquisitionError("timeout", "Se agotó el tiempo de descarga.")
                request = Request(  # noqa: S310 — URL validada antes de abrir
                    url,
                    headers={
                        "User-Agent": "PublicProcurement/0.1",
                        "Accept-Encoding": "identity",
                    },
                )
                try:
                    response = self._opener.open(request, timeout=remaining)
                except HTTPError as exc:
                    trace.update(
                        stage="response_headers",
                        http_status=exc.code,
                        exception_type=type(exc).__name__,
                        content_type=diagnostic_media_type(exc.headers),
                    )
                    location = exc.headers.get("Location") if exc.headers else None
                    exc.close()
                    if exc.code in REDIRECT_STATUSES:
                        trace["stage"] = "validate_redirect"
                        hop = {
                            "http_status": exc.code,
                            "content_type": trace["content_type"],
                            "destination": "missing" if not location else "blocked",
                        }
                        trace["redirects"].append(hop)
                        if not location:
                            raise AcquisitionError(
                                "invalid_redirect", "Redirección sin destino."
                            ) from None
                        url = urljoin(url, location)
                        validate_url(url)
                        hop["destination"] = (
                            "secop_retrieve_file"
                            if urlsplit(url).path == RETRIEVE_PATH
                            else "secop_other_path"
                        )
                        continue
                    raise AcquisitionError(
                        "http_error", f"SECOP respondió HTTP {exc.code}."
                    ) from None
                with response:
                    trace.update(
                        stage="response_headers",
                        http_status=response.status,
                        content_type=diagnostic_media_type(response.headers),
                    )
                    validate_url(response.geturl())
                    if response.status != 200:
                        raise AcquisitionError(
                            "http_error", "La respuesta no es una descarga completa."
                        )
                    content_type = response.headers.get("Content-Type", "application/octet-stream")
                    if "text/html" in content_type.lower():
                        raise AcquisitionError(
                            "invalid_content", "SECOP devolvió HTML en lugar del archivo."
                        )
                    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise AcquisitionError(
                            "invalid_encoding", "Respuesta comprimida inesperada."
                        )
                    length = response.headers.get("Content-Length")
                    try:
                        expected_size = int(length) if length is not None else None
                    except ValueError:
                        raise AcquisitionError("invalid_size", "Tamaño HTTP inválido.") from None
                    if expected_size is not None and expected_size < 0:
                        raise AcquisitionError("invalid_size", "Tamaño HTTP inválido.")

                    def chunks(stream: Any = response) -> Iterator[bytes]:
                        while True:
                            trace["stage"] = "read_body"
                            if time.monotonic() - started >= self.timeout_seconds:
                                raise AcquisitionError("timeout", "Se agotó el tiempo de descarga.")
                            # read1 devuelve los bytes recibidos sin esperar a llenar el bloque:
                            # permite comprobar el plazo incluso con servidores muy lentos.
                            chunk = stream.read1(65536)
                            if time.monotonic() - started >= self.timeout_seconds:
                                raise AcquisitionError("timeout", "Se agotó el tiempo de descarga.")
                            trace["stage"] = "storage"
                            if not chunk:
                                return
                            yield chunk

                    trace["stage"] = "storage"
                    stored = storage.store(
                        chunks(),
                        original_name=source.original_name,
                        content_type=content_type,
                        expected_size=expected_size,
                        max_bytes=self.max_bytes,
                    )
                    trace["stage"] = "completed"
                    return stored
            raise AcquisitionError("redirect_limit", "Demasiadas redirecciones de descarga.")
        except AcquisitionError as exc:
            trace["rejection_reason"] = exc.code
            trace["exception_type"] = trace["exception_type"] or type(exc).__name__
            raise
        except (URLError, TimeoutError, ConnectionError, HTTPException) as exc:
            trace.update(rejection_reason="network_error", exception_type=type(exc).__name__)
            if isinstance(exc, URLError) and isinstance(exc.reason, BaseException):
                trace["underlying_exception_type"] = type(exc.reason).__name__
            raise AcquisitionError(
                "network_error", "La descarga fue interrumpida por un error de red."
            ) from exc
        except OSError as exc:
            trace.update(rejection_reason="os_error", exception_type=type(exc).__name__)
            raise
        finally:
            if diagnostics is not None:
                diagnostics.clear()
                diagnostics.update(trace)
