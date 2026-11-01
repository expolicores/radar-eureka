"""Auditable, conservative cleanup of review membership; operational history is read-only."""

import hashlib
import json
from collections import Counter
from typing import Any

from sqlalchemy import delete, select, text

from .review_policy import POLICY_VERSION, human_intervention
from .review_repositories import ManualProcessReviewRecord


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def cleanup_plan(data: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_identity = {identity: row for row in rows for identity in row["equivalent_identities"]}
    remove, keep, protected = [], [], []
    for identity, rating in sorted(data["ratings"].items()):
        row = by_identity.get(identity)
        equivalent = row["equivalent_identities"] if row else [identity]
        human = [i for i in equivalent if human_intervention(data["ratings"].get(i, {}))]
        entry = {"identity": identity, "rating_fingerprint": fingerprint(rating)}
        if human:
            protected.append(
                {**entry, "reason": "human_intervention", "protected_identities": human}
            )
        elif row is None:
            keep.append({**entry, "reason": "unresolved_identity_preserved"})
        elif row.get("review_fit_rejected_reason"):
            remove.append(
                {
                    **entry,
                    "reason": row["review_fit_rejected_reason"],
                    "run_reasons": sorted(
                        {
                            h["result"].get("reason") or h["result"].get("outcome")
                            for h in row["history"]
                        }
                    ),
                    "run_ids": sorted({h["run_id"] for h in row["history"]}),
                }
            )
        elif row["review_evidence_sufficient"]:
            keep.append(
                {
                    **entry,
                    "reason": "commercial_evidence",
                    "evidence": row["review_admission_reasons"],
                }
            )
        elif row["manual_review_reasons"]:
            keep.append(
                {
                    **entry,
                    "reason": "documentary_evidence",
                    "evidence": row["manual_review_reasons"],
                }
            )
        elif row["sources"] != ["socrata"]:
            keep.append({**entry, "reason": "non_socrata_history_preserved"})
        elif row["has_alert"]:
            keep.append({**entry, "reason": "alert_association_preserved"})
        else:
            reasons = sorted(
                {h["result"].get("reason") or h["result"].get("outcome") for h in row["history"]}
            )
            remove.append(
                {
                    **entry,
                    "reason": "no_commercial_evidence",
                    "run_reasons": reasons,
                    "run_ids": sorted({h["run_id"] for h in row["history"]}),
                }
            )
    result = {
        "policy_version": POLICY_VERSION,
        "before": len(data["ratings"]),
        "delete_count": len(remove),
        "keep_count": len(keep),
        "protected_count": len(protected),
        "expected_remaining": len(keep) + len(protected),
        "delete": remove,
        "keep": keep,
        "protected": protected,
        "retained_reasons": dict(Counter(e["reason"] for e in keep + protected)),
    }
    if result["before"] != len(remove) + len(keep) + len(protected):
        raise ValueError("Cleanup classification is incomplete")
    result["selection_hash"] = fingerprint(result)
    return result


def execute_cleanup(sessions: Any, plan: dict[str, Any], rebuild: Any) -> dict[str, Any]:
    """Exact-ID transactional delete with selection revalidation and human-edit protection."""
    with sessions.begin() as session:
        if session.get_bind().dialect.name == "postgresql":
            session.execute(text("SET LOCAL lock_timeout='5s'"))
            session.execute(
                text("LOCK TABLE eureka.manual_process_review IN SHARE ROW EXCLUSIVE MODE")
            )
        fresh = rebuild()
        if fresh["selection_hash"] != plan["selection_hash"]:
            ids = [e["identity"] for e in plan["delete"]]
            remaining = list(
                session.scalars(
                    select(ManualProcessReviewRecord.canonical_identity).where(
                        ManualProcessReviewRecord.canonical_identity.in_(ids)
                    )
                )
            )
            if not remaining and fresh["delete_count"] == 0:
                return {
                    "deleted": 0,
                    "identities": [],
                    "already_cleaned": True,
                    "selection_hash": plan["selection_hash"],
                }
            raise ValueError("Cleanup selection changed; regenerate the audit before deleting")
        identities = [e["identity"] for e in plan["delete"]]
        actual = list(
            session.scalars(
                select(ManualProcessReviewRecord)
                .where(ManualProcessReviewRecord.canonical_identity.in_(identities))
                .with_for_update()
            )
        )
        if len(actual) != len(identities):
            raise ValueError("Cleanup membership changed")
        for record in actual:
            if human_intervention(
                {
                    k: getattr(record, k)
                    for k in ("manual_rating", "manual_note", "reviewed_at", "reviewed_by")
                }
            ):
                raise ValueError("Human assessment detected; cleanup rolled back")
        deleted = list(
            session.scalars(
                delete(ManualProcessReviewRecord)
                .where(ManualProcessReviewRecord.canonical_identity.in_(identities))
                .returning(ManualProcessReviewRecord.canonical_identity)
            )
        )
        if set(deleted) != set(identities):
            raise ValueError("Cleanup delete count mismatch")
    return {
        "deleted": len(deleted),
        "identities": sorted(deleted),
        "selection_hash": plan["selection_hash"],
    }
