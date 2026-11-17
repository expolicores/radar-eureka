"""One optional cheap query; no built-in search provider or retailer allowlist."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from xml.etree.ElementTree import ParseError

from .matching import observe
from .ports import WebSearch
from .schemas import MarketObservation, ProductIdentity, SearchResult
from .urls import canonical_url


@dataclass
class WebDiscoveryResult:
    candidates: list[SearchResult] = field(default_factory=list)
    observations: list[MarketObservation] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)


def discover_web(product: ProductIdentity, search: WebSearch) -> WebDiscoveryResult:
    queries = [f'{product.brand} "{product.canonical_model or product.model}" precio Colombia COP']
    result = WebDiscoveryResult()
    attempts = []
    for query in queries:
        try:
            rows = search.search(query)
            if not isinstance(rows, list) or not all(isinstance(row, SearchResult) for row in rows):
                raise ValueError("Invalid search response")
            observations = [observe(product, row) for row in rows[:10]]
            for observation in observations:
                observation.discovered_queries = [query]
            result.candidates.extend(rows[:10])
            result.observations.extend(observations)
            attempts.append(
                {"query": query, "status": "completed", "results_received": len(rows[:10])}
            )
        except (OSError, ValueError, TypeError, ParseError) as exc:
            error = {"code": "market_search_failed", "error_type": type(exc).__name__}
            result.errors.append(error)
            attempts.append({"query": query, "status": "degraded", **error})
            # No retry at the optional source boundary.
            break
    pairs = sorted(
        zip(result.candidates, result.observations, strict=True),
        key=lambda pair: (-pair[1].discovery_score, str(pair[0].url)),
    )
    result.candidates = [pair[0] for pair in pairs]
    result.observations = [pair[1] for pair in pairs]
    strong = [
        o
        for o in result.observations
        if o.page_type in {"product_page", "marketplace_listing"}
        and o.match_level in {"exact", "high"}
    ]
    result.diagnostics = {
        "version": "deterministic-single-query",
        "queries_planned": len(queries),
        "queries_executed": len(attempts),
        "queries": attempts,
        "canonical_model_used": product.canonical_model,
        "raw_candidates": len(result.candidates),
        "page_types": dict(Counter(o.page_type for o in result.observations)),
        "unique_candidate_urls": len({canonical_url(str(c.url)) for c in result.candidates}),
        "unique_strong_page_urls": len({canonical_url(str(o.url)) for o in strong}),
        "source_status": "degraded"
        if result.errors
        else "empty"
        if not result.candidates
        else "available",
    }
    return result
