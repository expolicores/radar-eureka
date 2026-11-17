"""Allowlisted read projection. Does not run providers, matching, or calculations."""

import hashlib
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PRODUCT = "brand model canonical_model product_type size"
PUBLIC = (
    PRODUCT
    + " public_process_identity public_process_code public_entity public_product_description"
    " public_unit_price public_price_date public_evidence_ref public_document public_page_reference"
    " public_price_stage price_origin price_tax_basis evidence_warnings public_document_url"
    " contract_identifier supplier quantity item_total document_heading_process_code"
)
OBSERVATION = (
    "retailer market_product_title model brand price currency url match_level match_reason"
    " captured_at"
    " availability valid_for_benchmark promotion_detected source_type source seller_id seller_name"
    " listing_id condition duplicate_of web_source_kind domain_id page_type discovery_score"
    " discovery_method extraction_method price_evidence_level currency_inferred"
)
BENCHMARK = (
    "benchmark_status valid_observations_count retailers_count independent_sources_count"
    " distinct_sellers_count evidence_sufficiency min_price median_price max_price captured_at"
    " confidence limitations observations_count"
)
COMPARISON = (
    "public_entity public_unit_price private_median_price absolute_difference percentage_difference"
    " public_price_date market_captured_at time_gap_days confidence limitations"
)


def _pick(value: Any, fields: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {k: value[k] for k in fields.split() if k in value}


def _url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        u = urlsplit(value)
        if u.scheme != "https" or not u.hostname or u.username or u.password:
            return None
        query = [
            (k, v)
            for k, v in parse_qsl(u.query, keep_blank_values=True)
            if not any(s in k.lower() for s in ("key", "token", "password", "secret", "signature"))
        ]
        return urlunsplit((u.scheme, u.netloc, u.path, urlencode(query), ""))
    except ValueError:
        return None


def present_market_reports(data: dict[str, Any]) -> dict[str, Any]:
    reports = []
    source_reports = data.get("reports", [])
    if not isinstance(source_reports, list):
        raise ValueError("Invalid market report collection")
    for raw in source_reports:
        if (
            not isinstance(raw, dict)
            or not isinstance(raw.get("benchmark"), dict)
            or not isinstance(raw.get("product"), dict)
        ):
            raise ValueError("Invalid market report")
        public = _pick(raw.get("public_product"), PUBLIC)
        if public:
            public["public_document_url"] = _url(public.get("public_document_url"))
        key = "|".join(
            str(v or "")
            for v in (
                public.get("public_evidence_ref"),
                raw.get("product", {}).get("brand"),
                raw.get("product", {}).get("model"),
                raw["benchmark"].get("captured_at"),
            )
        )
        report: dict[str, Any] = {
            "report_id": hashlib.sha256(key.encode()).hexdigest()[:20],
            "status": raw.get("status"),
            "product": _pick(raw.get("product"), PRODUCT),
            "public_product": public or None,
            "public_evidence_status": raw.get("public_evidence_status"),
            "benchmark": _pick(raw["benchmark"], BENCHMARK),
            "comparison": _pick(raw.get("comparison"), COMPARISON) or None,
            "signal": _pick(raw.get("signal"), "type meaning") or None,
            "preliminary_comparison": _pick(raw.get("preliminary_comparison"), "status limitations")
            or None,
            "errors": [_pick(e, "code http_status") for e in raw.get("errors", [])],
        }
        for kind in ("observations", "duplicates"):
            rows = []
            observations = raw["benchmark"].get(kind, [])
            if not isinstance(observations, list):
                raise ValueError("Invalid market observations")
            for observation in observations:
                if not isinstance(observation, dict):
                    raise ValueError("Invalid market observation")
                row = _pick(observation, OBSERVATION)
                row["url"] = _url(row.get("url"))
                # Only a text delivery summary, never arbitrary nested provider data.
                shipping = observation.get("shipping")
                row["shipping"] = shipping if isinstance(shipping, str) else None
                rows.append(row)
            report["benchmark"][kind] = rows
        for name, fields in {
            "shopping_discovery": "source_status request_count valid_observations",
            "market_price_scout": (
                "activated status requested_missing_observations candidates_received"
            ),
            "mercadolibre": "catalog_product_id catalog_selection_reason source_status",
            "web_discovery": (
                "queries_planned queries_executed unique_strong_page_urls canonical_model_used"
            ),
        }.items():
            if name in raw:
                report[name] = _pick(raw[name], fields)
        reports.append(report)
    return {"schema_version": data.get("schema_version"), "reports": reports}
