"""Check supporting reads; selection of opportunities remains with the model."""

import json
import re
from typing import Any

from .policy import investigation_requested
from .schemas import LatestCdpRunSummary


def call_key(name: str, arguments: dict[str, Any]) -> str:
    return name + json.dumps(arguments, sort_keys=True)


def required_reads(
    question: str, results: list[Any], cache: dict[str, str], answer: str
) -> list[dict[str, Any]]:
    if not investigation_requested(question):
        return []
    missing: list[dict[str, Any]] = []

    def need(name: str, args: dict[str, Any]) -> dict[str, Any] | None:
        key = call_key(name, args)
        if key not in cache:
            missing.append({"name": name, "arguments": args})
            return None
        return dict(json.loads(cache[key]))

    need("get_eureka_commercial_profile", {})
    latest = next((r for r in results if isinstance(r, LatestCdpRunSummary)), None)
    if latest is None:
        need("get_latest_cdp_run", {})
        return missing
    if not latest.has_run:
        return missing
    pools: list[dict[str, Any]] = []
    for name, count in (
        ("get_run_alerts", latest.alerts_created),
        ("get_run_review_candidates", latest.review_candidates_total),
    ):
        if count is None or count > 0:
            data = need(name, {"run_id": latest.run_id})
            if data:
                pools.extend(data.get("items") or [])
    if missing:
        return missing
    # Verify the concrete cases mentioned in the answer, rather than reading every
    # candidate or choosing winners with a second scoring implementation.
    mentioned = []
    for item in pools:
        identity = item.get("identity") or item.get("process_identity")
        code = item.get("process_code")
        terms = [str(t) for t in (identity, code) if t]
        positions = [
            m.start()
            for t in terms
            if (m := re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", answer, re.IGNORECASE))
        ]
        if identity and positions:
            mentioned.append((min(positions), identity, item))
    seen: set[str] = set()
    for _, identity, _item in sorted(mentioned, key=lambda entry: entry[0]):
        if identity in seen:
            continue
        if len(seen) == 3:
            break
        seen.add(identity)
        detail = need("get_process_detail", {"identity": identity})
        if not detail or detail.get("found") is False:
            continue
        uncertain = (
            detail.get("manual_review_required")
            or detail.get("manual_review_reasons")
            or detail.get("score") is None
            or detail.get("funnel_state")
            in {
                "limit_deferred",
                "metadata",
                "missing_documents",
                "extraction_failed",
                "pipeline_required",
            }
        )
        if uncertain:
            need("get_process_evidence", {"identity": identity})
    return missing
