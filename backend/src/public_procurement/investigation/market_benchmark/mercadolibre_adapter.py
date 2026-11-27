"""Bounded MCO read adapter. No anonymous fallback, redirects, retries or token refresh."""

import json
import logging
import re
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from public_procurement.shared.config import ENV_FILE
from public_procurement.shared.text import normalize_text

from .matching import IdentityMatch, match_identity
from .query_expansion import expanded_queries, model_family
from .schemas import ApiEvidence, MarketObservation, ProductIdentity

logger = logging.getLogger(__name__)
BASE_URL = "https://api.mercadolibre.com"
SITE_ID = "MCO"


class MercadoLibreSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )
    mercadolibre_access_token: SecretStr | None = Field(default=None, repr=False)
    mercadolibre_client_id: SecretStr | None = Field(default=None, repr=False)
    mercadolibre_client_secret: SecretStr | None = Field(default=None, repr=False)
    mercadolibre_refresh_token: SecretStr | None = Field(default=None, repr=False)


class MercadoLibreError(Exception):
    def __init__(self, code: str, status: int | None = None) -> None:
        self.code, self.status = code, status
        super().__init__(code)  # never include response body, request or credentials


class ApiTransport(Protocol):
    def get(self, path: str, params: dict[str, str] | None = None) -> Any: ...


def status_error(status: int) -> MercadoLibreError:
    return MercadoLibreError(
        {
            401: "token_expired_or_invalid",
            403: "access_forbidden",
            429: "rate_limited",
            404: "resource_not_found",
        }.get(status, "provider_http_error"),
        status,
    )


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        raise MercadoLibreError("unexpected_redirect", code)


class MercadoLibreHttp:
    def __init__(self, config: MercadoLibreSettings) -> None:
        self.config = config
        self.requests: list[dict[str, Any]] = []

    def get(self, path: str, params: dict[str, str] | None = None) -> Any:
        token = self.config.mercadolibre_access_token
        if not token or not token.get_secret_value().strip():
            raise MercadoLibreError("missing_auth_configuration")
        if not re.fullmatch(r"/(?:products/search|products/MCO\d+|items/MCO\d+)", path):
            raise MercadoLibreError("endpoint_not_allowed")
        if set(params or {}) - {"site_id", "status", "q", "limit", "offset"}:
            raise MercadoLibreError("query_parameter_not_allowed")
        query = urlencode(params or {})
        url = BASE_URL + path + ("?" + query if query else "")
        request = Request(  # noqa: S310 -- fixed HTTPS API origin and allowlisted paths
            url,
            headers={
                "Authorization": "Bearer " + token.get_secret_value(),
                "Accept": "application/json",
            },
        )
        status = None
        try:
            with build_opener(NoRedirect()).open(request, timeout=20) as response:
                status = response.status
                body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise MercadoLibreError("response_too_large")
            return json.loads(body, parse_float=Decimal)
        except HTTPError as exc:
            status = exc.code
            exc.close()
            raise status_error(status) from None
        except TimeoutError:
            raise MercadoLibreError("timeout") from None
        except URLError as exc:
            raise MercadoLibreError(
                "timeout" if isinstance(exc.reason, TimeoutError) else "network_error"
            ) from None
        except OSError:
            raise MercadoLibreError("network_error") from None
        except (ValueError, UnicodeError):
            raise MercadoLibreError("invalid_response") from None
        finally:
            self.requests.append({"endpoint": path, "query": params or {}, "http_status": status})
            logger.info("mercadolibre_api endpoint=%s status=%s", path, status)


@dataclass
class MercadoLibreResult:
    observations: list[MarketObservation] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(
        default_factory=lambda: {
            "site_id": SITE_ID,
            "catalog_candidates": [],
            "catalog_product_id": None,
            "catalog_selection_reason": "not_resolved",
            "listing_candidates": [],
            "errors": [],
            "warnings": [],
            "retries": 0,
        }
    )


def attributes(row: dict[str, Any]) -> dict[str, str]:
    return {
        a["id"]: str(a["value_name"])
        for a in row.get("attributes", [])
        if isinstance(a, dict) and isinstance(a.get("id"), str) and a.get("value_name") is not None
    }


def measurement_conflicts(expected: str, observed: str) -> bool:
    def normalized(value: str) -> str:
        text = normalize_text(value).replace("″", '"')
        text = re.sub(r"(?:pulgadas|inches|[\"])", "in", text)
        return re.sub(r"\s+", "", text).replace(",", ".")

    wanted, actual = normalized(expected), normalized(observed)
    a = re.fullmatch(r"(\d+(?:\.\d+)?)([a-z]+)", wanted)
    b = re.fullmatch(r"(\d+(?:\.\d+)?)([a-z]+)", actual)
    if a and b:
        return a[2] == b[2] and Decimal(a[1]) != Decimal(b[1])
    # Do not invent conversions between different units; compare explicit dimension tuples.
    unit_a, unit_b = re.search(r"[a-z]+$", wanted), re.search(r"[a-z]+$", actual)
    return bool(unit_a and unit_b and unit_a[0] == unit_b[0] and wanted != actual)


def structured_match(product: ProductIdentity, row: dict[str, Any]) -> IdentityMatch:
    if row.get("site_id", SITE_ID) != SITE_ID:
        return IdentityMatch("reject", "different_or_unknown_site", None, None)
    attrs = attributes(row)
    domain = row.get("domain_id")
    if product.expected_domain_id and domain and domain != product.expected_domain_id:
        return IdentityMatch("reject", "different_product_domain", None, None)
    for key, wanted in product.relevant_attributes.items():
        if key in attrs and normalize_text(attrs[key]) != normalize_text(wanted):
            return IdentityMatch("reject", "conflicting_relevant_attribute:" + key, None, None)
    for name, expected, keys in (
        ("size", product.size, ("SCREEN_SIZE", "SIZE", "DISPLAY_SIZE")),
        ("capacity", product.capacity, ("CAPACITY", "STORAGE_CAPACITY", "TOTAL_CAPACITY")),
        ("dimensions", product.dimensions, ("DIMENSIONS", "PRODUCT_DIMENSIONS")),
    ):
        if expected and any(
            key in attrs and measurement_conflicts(expected, attrs[key]) for key in keys
        ):
            return IdentityMatch("reject", "conflicting_" + name + "_attribute", None, None)
    title = str(row.get("title") or row.get("name") or "")
    observed_brand, observed_model = attrs.get("BRAND"), attrs.get("MODEL")
    if observed_brand and normalize_text(observed_brand) != normalize_text(product.brand):
        return IdentityMatch("reject", "different_brand_attribute", observed_brand, observed_model)
    attr_match = match_identity(
        product, " ".join([observed_brand or product.brand, observed_model or ""])
    )
    family = model_family(product)
    size_value = re.match(r"(\d+(?:[.,]\d+)?)", product.size or "")
    title_match = match_identity(product, title)
    contextual_family = (
        title_match.reason
        not in {"different_model", "conflicting_models_in_title", "different_size"}
        and family is not None
        and size_value is not None
        and product.expected_domain_id is not None
        and domain == product.expected_domain_id
        and re.search(
            r"\b" + re.escape(normalize_text(product.brand)) + r"\b",
            normalize_text(title + " " + (observed_brand or "")),
        )
        and re.search(
            r"\b" + re.escape(family) + r"\b", normalize_text(title + " " + (observed_model or ""))
        )
        and re.search(
            r"\b" + re.escape(size_value[1]) + r"\b",
            normalize_text(title + " " + attrs.get("SCREEN_SIZE", "")),
        )
    )
    if (
        observed_model
        and attr_match.level not in {"exact", "high"}
        and (not contextual_family or observed_model.casefold() != family)
    ):
        return replace(attr_match, level="reject", reason="different_model_attribute")
    # Append explicit attributes to strengthen generic titles, never replace conflicting titles.
    augmented = title + " " + (observed_brand or "") + " " + (observed_model or "")
    size = attrs.get("SCREEN_SIZE", "")
    if re.fullmatch(r'\d+(?:[.,]\d+)?\s*(?:["″]|pulgadas|inches|in)', size, re.I):
        augmented += " " + size
    matched = match_identity(product, augmented)
    if contextual_family and matched.reason in {
        "irrelevant_or_generic_result",
        "model_not_confirmed",
        "different_model",
        "conflicting_models_in_title",
    }:
        reconstructed = match_identity(product, augmented + " " + product.model)
        if reconstructed.reason not in {
            "different_size",
            "accessory_or_service",
            "used_or_refurbished",
            "non_comparable_bundle",
        }:
            return IdentityMatch(
                "high", "size_model_family_and_domain", product.brand, product.model
            )
    # A regional suffix and its base model are equivalent, not two conflicting models.
    if matched.reason == "conflicting_models_in_title" and observed_model:
        title_match = match_identity(product, title)
        if title_match.level in {"exact", "high"} and attr_match.level in {"exact", "high"}:
            return replace(
                title_match, level="high", reason="consistent_title_and_regional_attribute"
            )
    return matched


def catalog_rank(product: ProductIdentity, row: dict[str, Any], match: IdentityMatch) -> int:
    if match.level == "reject":
        return -100
    score = {"exact": 100, "high": 75, "partial": 25}[match.level]
    if product.expected_domain_id and row.get("domain_id") == product.expected_domain_id:
        score += 40
    if product.expected_catalog_product_id and row.get("id") == product.expected_catalog_product_id:
        score += 10
    if product.product_type and normalize_text(product.product_type) in normalize_text(
        str(row.get("name", ""))
    ):
        score += 5
    return score


ITEM_FIELDS = (
    "id",
    "site_id",
    "title",
    "price",
    "original_price",
    "currency_id",
    "condition",
    "seller_id",
    "official_store_id",
    "catalog_product_id",
    "permalink",
    "available_quantity",
    "status",
    "attributes",
    "warranty",
    "tags",
    "domain_id",
    "category_id",
    "buying_mode",
    "bundle",
    "variations",
    "date_created",
    "last_updated",
)


def item_observation(
    product: ProductIdentity, row: dict[str, Any], captured_at: datetime
) -> MarketObservation | None:
    match = structured_match(product, row)
    url = row.get("permalink")
    try:
        parsed = urlsplit(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme != "https" or not parsed.hostname or parsed.username:
            return None
        if not (
            parsed.hostname == "mercadolibre.com.co"
            or parsed.hostname.endswith(".mercadolibre.com.co")
        ):
            return None
    except ValueError:
        return None
    price = None
    try:
        if not isinstance(row.get("price"), bool):
            value = Decimal(str(row.get("price")))
            if value.is_finite() and value > 0:
                price = value
    except InvalidOperation:
        pass
    notes = [
        "available_quantity_is_referential_not_exact_stock",
        "listed_price_excludes_shipping_not_checkout_verified",
    ]
    condition = row.get("condition")
    quantity = row.get("available_quantity")
    quantity = quantity if isinstance(quantity, int) and not isinstance(quantity, bool) else None
    availability = (
        "unavailable"
        if quantity is not None and quantity <= 0
        else ("available" if quantity is not None else "unknown")
    )
    reject = None
    if row.get("site_id") != SITE_ID or not re.fullmatch(r"MCO\d+", str(row.get("id", ""))):
        reject = "different_or_unknown_site"
    elif row.get("status") != "active":
        reject = "listing_not_active"
    elif condition != "new":
        reject = "condition_not_new_or_unknown"
    elif row.get("currency_id") != "COP":
        reject = "currency_not_cop"
    elif price is None:
        reject = "invalid_listing_total_price"
    elif row.get("buying_mode") not in (None, "buy_it_now"):
        reject = "not_fixed_total_price"
    elif availability == "unavailable":
        reject = "listing_unavailable"
    elif not row.get("seller_id"):
        reject = "seller_not_identified"
    elif row.get("bundle"):
        reject = "non_comparable_bundle"
    elif any(
        v.get("price") not in (None, row.get("price"))
        for v in row.get("variations", [])
        if isinstance(v, dict)
    ):
        reject = "ambiguous_variation_price"
    if reject:
        match = replace(match, level="reject", reason=reject)
    original = row.get("original_price")
    try:
        promotion = price is not None and Decimal(str(original)) > price
    except InvalidOperation:
        promotion = False
    raw = {key: row[key] for key in ITEM_FIELDS if key in row}
    return MarketObservation(
        source="mercadolibre",
        source_type="marketplace_api",
        extraction_method="mercadolibre_api",
        price_evidence_level="api_verified_price",
        verification_status="verified" if match.level in {"exact", "high"} else "rejected",
        page_type="marketplace_listing",
        discovery_score=100,
        retailer="Mercado Libre",
        marketplace="Mercado Libre Colombia",
        listing_id=str(row.get("id")),
        seller_id=str(row["seller_id"]) if row.get("seller_id") is not None else None,
        official_store_id=str(row["official_store_id"])
        if row.get("official_store_id") is not None
        else None,
        catalog_product_id=row.get("catalog_product_id"),
        condition=condition,
        currency=row.get("currency_id"),
        provider_status=row.get("status"),
        available_quantity_reference=quantity,
        market_product_title=str(row.get("title") or ""),
        brand=match.brand,
        model=match.model,
        price=price,
        url=url,
        captured_at=captured_at,
        availability=availability,
        match_level=match.level,
        match_reason=match.reason,
        promotion_detected=promotion,
        notes=notes,
        valid_for_benchmark=match.level in {"exact", "high"},
        domain_id=row.get("domain_id"),
        evidence=ApiEvidence(
            endpoint="/items/" + str(row.get("id")), captured_at=captured_at, response=raw
        ),
    )


class MercadoLibreAdapter:
    """Optional catalog discovery (4 queries/3 details) and up to 10 explicit item IDs."""

    def __init__(self, transport: ApiTransport, enable_catalog: bool = True) -> None:
        self.transport = transport
        self.enable_catalog = enable_catalog

    def collect(
        self,
        product: ProductIdentity,
        listing_ids: list[str] | None = None,
        discover_catalog: bool | None = None,
    ) -> MercadoLibreResult:
        result = MercadoLibreResult()
        d = result.diagnostics
        history = getattr(self.transport, "requests", [])
        start = len(history) if isinstance(history, list) else 0
        blocked = False
        if discover_catalog if discover_catalog is not None else self.enable_catalog:
            try:
                self._catalog(product, result)
            except MercadoLibreError as exc:
                self._degrade(result, exc, "catalog")
                blocked = exc.status in {401, 403, 429} or exc.code == "missing_auth_configuration"
            except (TypeError, ValueError, KeyError):
                self._degrade(result, MercadoLibreError("invalid_catalog_response"), "catalog")
        ids = list(dict.fromkeys(listing_ids or []))[:10]
        for iid in ids:
            if blocked:
                break
            if not re.fullmatch(r"MCO\d+", iid):
                self._degrade(result, MercadoLibreError("invalid_listing_id"), "item", iid)
                continue
            d["listing_candidates"].append({"id": iid, "origin": "explicit_or_web_url"})
            try:
                body = self.transport.get("/items/" + iid)
                required = {
                    "id",
                    "site_id",
                    "title",
                    "price",
                    "currency_id",
                    "condition",
                    "status",
                    "seller_id",
                    "permalink",
                }
                if (
                    not isinstance(body, dict)
                    or body.get("id") != iid
                    or not required.issubset(body)
                ):
                    raise MercadoLibreError("invalid_item_response")
                observation = item_observation(product, body, datetime.now(UTC))
                if observation is None:
                    raise MercadoLibreError("missing_or_invalid_colombian_permalink")
                result.observations.append(observation)
            except MercadoLibreError as exc:
                self._degrade(result, exc, "item", iid)
                blocked = exc.status in {401, 403, 429} or exc.code == "missing_auth_configuration"
            except (TypeError, ValueError, KeyError):
                self._degrade(result, MercadoLibreError("invalid_item_response"), "item", iid)
        history = getattr(self.transport, "requests", [])
        d["requests"] = history[start:] if isinstance(history, list) else []
        d["request_count"] = len(d["requests"])
        d["source_status"] = "degraded" if d["errors"] or d["warnings"] else "available"
        d["listing_discovery"] = "explicit_ids_only_no_site_search"
        return result

    @staticmethod
    def _degrade(
        result: MercadoLibreResult, exc: MercadoLibreError, stage: str, iid: str | None = None
    ) -> None:
        code = (
            ("listing_not_found" if stage == "item" else "catalog_product_not_found")
            if exc.status == 404
            else exc.code
        )
        result.diagnostics["errors"].append(
            {
                "code": code,
                "http_status": exc.status,
                "stage": stage,
                **(
                    {"catalog_product_id" if stage == "catalog_detail" else "listing_id": iid}
                    if iid
                    else {}
                ),
            }
        )
        if exc.code == "missing_auth_configuration":
            result.diagnostics["action_required"] = (
                "Configure MERCADOLIBRE_ACCESS_TOKEN in backend/.env."
            )
        elif exc.status == 401:
            result.diagnostics["action_required"] = (
                "Renew access token manually; no automatic refresh."
            )
        logger.info("mercadolibre_degraded stage=%s code=%s status=%s", stage, exc.code, exc.status)

    def _catalog(self, product: ProductIdentity, result: MercadoLibreResult) -> None:
        d = result.diagnostics
        potential: dict[str, int] = {}
        d["queries"] = []
        for query in expanded_queries(product):
            d["queries"].append(query)
            catalog = self.transport.get(
                "/products/search",
                {
                    "site_id": SITE_ID,
                    "status": "active",
                    "q": query,
                    "limit": "5",
                },
            )
            if not isinstance(catalog, dict) or not isinstance(catalog.get("results"), list):
                raise MercadoLibreError("invalid_catalog_response")
            for candidate in catalog["results"][:5]:
                if not isinstance(candidate, dict):
                    raise MercadoLibreError("invalid_catalog_response")
                match = structured_match(product, candidate)
                rank = catalog_rank(product, candidate, match)
                cid = candidate.get("id")
                summary = {
                    k: candidate[k]
                    for k in ("id", "name", "status", "domain_id", "attributes", "permalink")
                    if k in candidate
                }
                summary.update(
                    query=query, match_level=match.level, match_reason=match.reason, rank=rank
                )
                d["catalog_candidates"].append(summary)
                if match.level in {"exact", "high"} and re.fullmatch(r"MCO\d+", str(cid)):
                    potential[str(cid)] = max(potential.get(str(cid), -100), rank)
        if not d["catalog_candidates"]:
            d["warnings"].append({"code": "catalog_empty_results", "stage": "catalog"})
        verified = []
        for cid in sorted(potential, key=lambda key: (-potential[key], key))[:3]:
            try:
                detail = self.transport.get("/products/" + cid)
            except MercadoLibreError as exc:
                if exc.status in {401, 403, 429}:
                    raise
                self._degrade(result, exc, "catalog_detail", cid)
                continue
            if not isinstance(detail, dict):
                raise MercadoLibreError("invalid_catalog_detail")
            match = structured_match(product, detail)
            rank = catalog_rank(product, detail, match)
            d.setdefault("catalog_details", []).append(
                {
                    **{
                        k: detail[k]
                        for k in (
                            "id",
                            "status",
                            "name",
                            "attributes",
                            "domain_id",
                            "permalink",
                            "children_ids",
                        )
                        if k in detail
                    },
                    "match_level": match.level,
                    "match_reason": match.reason,
                    "rank": rank,
                }
            )
            if (
                detail.get("id") == cid
                and detail.get("status") == "active"
                and detail.get("site_id", SITE_ID) == SITE_ID
                and match.level in {"exact", "high"}
            ):
                verified.append((cid, match.level))
        exact = [cid for cid, level in verified if level == "exact"]
        eligible = exact or [cid for cid, _ in verified]
        selected = eligible[0] if len(eligible) == 1 and len(potential) <= 3 else None
        d["catalog_product_id"] = selected
        d["catalog_selection_reason"] = (
            "unique_verified_match"
            if selected
            else (
                "ambiguous_or_unvalidated_catalog" if potential else "no_matching_catalog_product"
            )
        )
