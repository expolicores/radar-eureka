import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..domain.message import DeliveryError, DeliveryReceipt

Transport = Callable[[str, dict[str, str], bytes, float], tuple[int, dict[str, str], bytes]]


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def http_transport(
    url: str, headers: dict[str, str], body: bytes, timeout: float
) -> tuple[int, dict[str, str], bytes]:
    if url != "https://api.resend.com/emails":
        raise DeliveryError("provider_url", "URL de proveedor no permitida.")
    request = Request(url, body, headers, method="POST")  # noqa: S310 - fixed HTTPS URL above
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read(65536)
    except HTTPError as error:
        return error.code, dict(error.headers.items()), error.read(65536)


class ResendEmailSender:
    provider, scope = "resend", "real"
    idempotency_seconds: int | None = 24 * 3600

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def __init__(self, api_key: str, timeout: float, transport: Transport = http_transport):
        self.api_key, self.timeout, self.transport = api_key, timeout, transport

    def send(self, payload: dict[str, Any], key: str) -> DeliveryReceipt:
        if not self.api_key or not payload.get("from"):
            raise DeliveryError("provider_configuration", "Falta configuración del proveedor.")
        body = json.dumps(
            {
                "from": payload["from"],
                "to": [payload["recipient"]],
                "subject": payload["subject"],
                "text": payload["text"],
                "html": payload["html"],
            }
        ).encode()
        try:
            status, headers, raw = self.transport(
                "https://api.resend.com/emails",
                {
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json",
                    "Idempotency-Key": key,
                },
                body,
                self.timeout,
            )
        except (TimeoutError, URLError, OSError) as error:
            raise DeliveryError(
                "provider_timeout",
                "Respuesta del proveedor no confirmada.",
                retryable=True,
                ambiguous=True,
            ) from error
        # Never persist provider response bodies: they may echo recipients or credentials.
        if 200 <= status < 300:
            try:
                message_id = json.loads(raw)["id"]
                if not isinstance(message_id, str) or not message_id or len(message_id) > 256:
                    raise ValueError("invalid receipt")
            except (ValueError, KeyError, TypeError) as error:
                raise DeliveryError(
                    "provider_receipt_unknown",
                    "Aceptación sin recibo válido.",
                    retryable=True,
                    ambiguous=True,
                    status_code=status,
                ) from error
            return DeliveryReceipt(message_id, status_code=status)
        retryable = status == 429 or status >= 500
        if status == 409:
            try:
                retryable = json.loads(raw).get("name") == "concurrent_idempotent_requests"
            except (ValueError, AttributeError):
                retryable = False
        value = next((v for k, v in headers.items() if k.lower() == "retry-after"), "0")
        seconds = min(int(value), 86400) if value.isdigit() else 0
        raise DeliveryError(
            "provider_http_" + str(status),
            "El proveedor rechazó la solicitud.",
            retryable=retryable,
            ambiguous=status >= 500,
            retry_after=seconds,
            status_code=status,
        )
