"""Combine operational review evidence without extracting or reclassifying facts."""

from typing import Any

REVIEW_FLAGS = {
    "suspicious_fact": "suspicious_facts",
    "extraction_failed": "extraction_failed",
    "unsupported_format": "unsupported_format",
    "ocr_truncated": "ocr_truncated",
    "partial_document_coverage": "partial_document_coverage",
    "missing_documents": "missing_documents",
    "document_download_failed": "document_download_failed",
}
REASON_FLAGS = {reason: flag for flag, reason in REVIEW_FLAGS.items()}
REASON_FLAGS.update(
    suspicious_fact="suspicious_fact",
    partial_coverage="partial_document_coverage",
    missing_selected_documents="missing_documents",
    missing_required_documents="missing_documents",
)


def review_reasons(review: dict[str, Any]) -> list[str]:
    reasons = [reason for flag, reason in REVIEW_FLAGS.items() if review.get(flag) is True]
    for alias, flag in REASON_FLAGS.items():
        if review.get(alias) is True and REVIEW_FLAGS[flag] not in reasons:
            reasons.append(REVIEW_FLAGS[flag])
    for reason in review.get("manual_review_reasons", []):
        if isinstance(reason, str) and reason not in reasons:
            reasons.append(REVIEW_FLAGS.get(REASON_FLAGS.get(reason, ""), reason))
    # Read the already-persisted annotation; never run a policy on old facts here.
    if "suspicious_facts" not in reasons and any(
        f.get("suspicious") is True for f in review.get("facts", [])
    ):
        reasons.append("suspicious_facts")
    return list(dict.fromkeys(reasons))


def combine_document_reviews(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    *,
    current_run_id: str,
) -> dict[str, Any]:
    """OR current and persisted review state for one exact process identity.

    Empty facts and false flags are not evidence that an older warning was resolved.
    Keep old facts as references in provenance, never insert/copy them as new facts.
    """
    combined = dict(current)
    reasons = review_reasons(current)
    provenance = list(current.get("manual_review_provenance", []))
    sources: list[tuple[str, str, dict[str, Any], dict[str, Any]]] = [
        ("current_run", current_run_id, current, {})
    ]
    sources.extend(
        (
            "persisted_cdp_run",
            str(entry["run_id"]),
            entry["result"].get("document_review", {}),
            entry["result"],
        )
        for entry in history
    )
    for origin, run_id, review, result in sources:
        source_reasons = review_reasons(review)
        for reason in result.get("manual_review_reasons", []):
            if reason not in source_reasons:
                source_reasons.append(reason)
        if result.get("requires_manual_document_review") is True:
            for warning in result.get("warnings", []):
                code = warning.get("code")
                if code and code not in source_reasons:
                    source_reasons.append(REVIEW_FLAGS.get(REASON_FLAGS.get(code, ""), code))
            if not source_reasons:
                source_reasons.append("persisted_document_review")
        if not source_reasons:
            continue
        for reason in source_reasons:
            if reason not in reasons:
                reasons.append(reason)
            flag = REASON_FLAGS.get(reason)
            if flag:
                combined[flag] = True
        facts = [f for f in review.get("facts", []) if f.get("suspicious") is True]
        evidence = {
            "origin": origin,
            "run_id": run_id,
            "reasons": source_reasons,
            "fact_ids": sorted({str(f["id"]) for f in facts if f.get("id")}),
            "document_version_ids": sorted(
                {str(f["document_version_id"]) for f in facts if f.get("document_version_id")}
                | {
                    str(w["document_version_id"])
                    for w in result.get("warnings", [])
                    if w.get("document_version_id")
                }
            ),
        }
        if evidence not in provenance:
            provenance.append(evidence)
    combined["manual_review_reasons"] = reasons
    combined["manual_review_provenance"] = provenance
    return combined
