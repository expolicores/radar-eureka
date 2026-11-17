"""Read-only explanations from stored decisions; never re-run matching or providers."""

from collections import Counter
from typing import Any
from urllib.parse import urlsplit

from .urls import extract_mco_listing_id

PREFERRED_DOMAINS = (
    "mercadolibre.com.co",
    "falabella.com.co",
    "alkosto.com",
    "ktronix.com",
    "exito.com",
)


def rejected_diagnostic(report: dict[str, Any]) -> dict[str, Any]:
    benchmark = report.get("benchmark", {})
    rows = []
    for observation in [*benchmark.get("observations", []), *benchmark.get("duplicates", [])]:
        if observation.get("source_type") not in {
            "web_search",
            "shopping_provider",
        } or observation.get("valid_for_benchmark"):
            continue
        evidence = observation.get("evidence", {})
        search_evidence = evidence.get("candidate", evidence)
        if search_evidence.get("source") == "serpapi":
            search_evidence = search_evidence.get("response", {})
        url = str(observation.get("url") or evidence.get("url") or "")
        domain = urlsplit(url).hostname or ""
        reasons = []
        if observation.get("rejection_reason"):
            reasons.append(observation["rejection_reason"])
        if observation.get("duplicate_of"):
            reasons.append("duplicate_offer")
        if observation.get("match_level") not in {"exact", "high"}:
            reasons.append(str(observation.get("match_reason") or "identity_not_confirmed"))
        if observation.get("page_type", "unknown") not in {"product_page", "marketplace_listing"}:
            reasons.append("candidate_page_not_concrete")
        if observation.get("price") is None:
            reasons.append("no_unambiguous_total_price")
        if observation.get("availability") == "unavailable":
            reasons.append("unavailable")
        reasons.extend(
            note
            for note in observation.get("notes", [])
            if note
            in {
                "commercial_context_not_observed",
                "installments_not_total_price",
                "ambiguous_multiple_prices",
                "currency_not_cop",
                "currency_not_confirmed",
            }
        )
        rows.append(
            {
                "query": search_evidence.get("query"),
                "domain": domain,
                "url": url,
                "title": evidence.get("title", observation.get("market_product_title")),
                "snippet": search_evidence.get("snippet"),
                "verification_status": observation.get("verification_status", "not_attempted"),
                "price_evidence_level": observation.get("price_evidence_level", "snippet_price"),
                "extraction_method": observation.get("extraction_method"),
                "page_type": observation.get("page_type", "unknown"),
                "rejection_reason": "; ".join(dict.fromkeys(reasons))
                or "excluded_by_stored_decision",
                "extracted_mco_id": extract_mco_listing_id(url),
                "price_detected": observation.get("price"),
            }
        )

    def priority(row: dict[str, Any]) -> tuple[int, str, str]:
        domain = row["domain"]
        rank = next(
            (
                i
                for i, host in enumerate(PREFERRED_DOMAINS)
                if domain == host or domain.endswith("." + host)
            ),
            len(PREFERRED_DOMAINS),
        )
        return rank, domain, str(row["query"])

    rows.sort(key=priority)
    return {
        "mode": "stored_rejections_read_only",
        "rejected_records": len(rows),
        "unique_rejected_urls": len({row["url"] for row in rows}),
        "domains": dict(Counter(row["domain"] for row in rows)),
        "page_types": dict(Counter(row["page_type"] for row in rows)),
        "rejected_candidates": rows,
    }
