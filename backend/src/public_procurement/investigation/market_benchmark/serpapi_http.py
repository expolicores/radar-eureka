"""Single bounded SerpApi transport. Fixed origin, no retries, sanitized receipts/errors."""

import hashlib
import json
import logging
import re
from typing import Any, Protocol, cast
from urllib.parse import quote, quote_plus

import httpx
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from public_procurement.shared.config import ENV_FILE

ENDPOINT = "https://serpapi.com/search.json"
ENGINES = {"google_shopping", "google_product", "google_immersive_product"}


class SerpApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", hide_input_in_errors=True)
    serpapi_api_key: SecretStr | None = Field(default=None, repr=False)
    serpapi_timeout_seconds: float = Field(default=45, ge=5, le=60)


class SerpApiError(Exception):
    def __init__(self, code: str, http_status: int | None = None):
        super().__init__(code)
        self.code, self.http_status = code, http_status


class SerpApiTransport(Protocol):
    def search(self, parameters: dict[str, str]) -> dict[str, Any]: ...


def sanitize(value: Any, secret: str) -> Any:
    if isinstance(value, dict):
        return {
            k: "[REDACTED]"
            if re.search(r"api[_-]?key|authorization|password|secret|access_token", k, re.I)
            else sanitize(v, secret)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [sanitize(v, secret) for v in value]
    if isinstance(value, str):
        for variant in {secret, quote(secret, safe=""), quote_plus(secret)} - {""}:
            value = value.replace(variant, "[REDACTED]")
        return re.sub(r"(?i)(api[_-]?key|access_token)(=|%3D)[^&\s\"<>]+", r"\1\2[REDACTED]", value)
    return value


def public_parameters(parameters: dict[str, str]) -> dict[str, str]:
    return {
        k: hashlib.sha256(v.encode()).hexdigest() if "token" in k else v
        for k, v in parameters.items()
        if k != "api_key"
    }


class SerpApiHttp:
    def __init__(self, config: SerpApiSettings) -> None:
        self.config = config

    def search(self, parameters: dict[str, str]) -> dict[str, Any]:
        if parameters.get("engine") not in ENGINES or set(parameters) - {
            "engine",
            "q",
            "gl",
            "hl",
            "location",
            "product_id",
            "offer_view",
            "page_token",
            "more_stores",
            "next_page_token",
        }:
            raise SerpApiError("invalid_request_parameters")
        secret = (
            self.config.serpapi_api_key.get_secret_value().strip()
            if self.config.serpapi_api_key
            else ""
        )
        if not secret:
            raise SerpApiError("missing_api_key")
        for name in ("httpx", "httpcore", "httpx2", "httpcore2"):
            logging.getLogger(name).setLevel(logging.CRITICAL)
        try:
            with (
                httpx.Client(
                    timeout=self.config.serpapi_timeout_seconds,
                    follow_redirects=False,
                    trust_env=False,
                ) as client,
                client.stream(
                    "GET", ENDPOINT, params={**parameters, "api_key": secret}
                ) as response,
            ):
                if response.status_code != 200:
                    code = {
                        401: "authentication_failed",
                        403: "authentication_failed",
                        429: "rate_limited",
                    }.get(response.status_code, "provider_http_error")
                    raise SerpApiError(code, response.status_code)
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > 8_000_000:
                        raise SerpApiError("response_too_large")
                payload = json.loads(body)
                if not isinstance(payload, dict):
                    raise SerpApiError("invalid_payload")
                return cast(dict[str, Any], sanitize(payload, secret))
        except SerpApiError:
            raise
        except httpx.TimeoutException:
            raise SerpApiError("timeout") from None
        except httpx.HTTPError:
            raise SerpApiError("network_error") from None
        except (ValueError, UnicodeError):
            raise SerpApiError("invalid_payload") from None
