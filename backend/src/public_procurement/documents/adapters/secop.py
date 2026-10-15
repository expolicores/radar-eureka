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

    def download(self, source: SourceDocument, storage: BinaryStorage) -> StoredBinary:
        url = source.source_url
        if not url:
            raise AcquisitionError("missing_url", "La fuente no publica URL de descarga.")
        started = time.monotonic()
        try:
            for _ in range(6):
                validate_url(url)
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
                    if exc.code in (301, 302, 303, 307, 308):
                        location = exc.headers.get("Location")
                        exc.close()
                        if not location:
                            raise AcquisitionError(
                                "invalid_redirect", "Redirección sin destino."
                            ) from None
                        url = urljoin(url, location)
                        continue
                    code = exc.code
                    exc.close()
                    raise AcquisitionError("http_error", f"SECOP respondió HTTP {code}.") from None
                with response:
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
                            if time.monotonic() - started >= self.timeout_seconds:
                                raise AcquisitionError("timeout", "Se agotó el tiempo de descarga.")
                            # read1 devuelve los bytes recibidos sin esperar a llenar el bloque:
                            # permite comprobar el plazo incluso con servidores muy lentos.
                            chunk = stream.read1(65536)
                            if time.monotonic() - started >= self.timeout_seconds:
                                raise AcquisitionError("timeout", "Se agotó el tiempo de descarga.")
                            if not chunk:
                                return
                            yield chunk

                    return storage.store(
                        chunks(),
                        original_name=source.original_name,
                        content_type=content_type,
                        expected_size=expected_size,
                        max_bytes=self.max_bytes,
                    )
            raise AcquisitionError("redirect_limit", "Demasiadas redirecciones de descarga.")
        except (URLError, TimeoutError, ConnectionError, HTTPException) as exc:
            raise AcquisitionError(
                "network_error", "La descarga fue interrumpida por un error de red."
            ) from exc
