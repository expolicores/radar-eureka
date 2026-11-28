"""Offline candidate queue for an EN-01 discovery run (no network).

Re-evaluates the stored notices with the current commercial profile (object only), keeps
every eligible process in a visible queue ordered by closing date, commercial priority and
confidence, attaches what is already known (inventory, findings, human reviews) and
reconciles the run's original eligible set: every original candidate ends up selected,
pending (quota) or excluded with a verifiable reason. Commercial eligibility never implies
anything about experience requirements.
"""

import argparse
import json
from collections import Counter

import eureka_nacional_window_reevaluation as window
from eureka_nacional_findings import human_reviews_for, load_human_reviews

PRIORITY_ORDER = {"A": 0, "B": 1, "C": 2}
QUEUE_FILE = "candidate_queue.json"


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def history(root):
    """What earlier runs already know about each identity (inventory and findings)."""
    known = {}
    for run in sorted(p for p in root.glob("en01-*") if p.is_dir()):
        processes = (read_json(run / "processes.json", {}) or {}).get("processes", [])
        identity_of = {p["process_reference"]: p.get("source_identity") for p in processes}
        for case in read_json(run / "documents.json", []) or []:
            identity = identity_of.get(case["process_reference"])
            if identity and case.get("documents"):
                entry = known.setdefault(identity, {})
                complete = case.get("inventory_complete", True) is not False
                entry["inventory"] = (
                    "complete" if complete or entry.get("inventory") == "complete" else "incomplete"
                )
                entry.setdefault("inventory_runs", []).append(run.name)
        result_files = [run / "experience_requirements.json", *run.glob("validation_results*.json")]
        for path in result_files:
            data = read_json(path)
            results = data.get("results", []) if isinstance(data, dict) else data or []
            for result in results:
                identity = (
                    result.get("source_identity")
                    or identity_of.get(result["process_reference"])
                    # SECOP I stage-3 runs keep the constancia but no processes.json.
                    or (f"secop1:{result['constancia']}" if result.get("constancia") else None)
                )
                finding = result.get("finding") or {}
                if identity and (finding or result.get("status")):
                    known.setdefault(identity, {})["analysis"] = {
                        "run": run.name,
                        "status": result.get("status"),
                        "finding": finding.get("category"),
                        "human_review": [
                            h.get("observation") for h in finding.get("human_review", [])
                        ],
                    }
    return known


def order_key(row):
    open_with_deadline = row["validity_status"] == "open" and bool(row.get("deadline_at"))
    tier = 0 if open_with_deadline else 1 if row["validity_status"] == "unknown" else 2
    return (
        tier,
        row.get("deadline_at") or "9999",
        PRIORITY_ORDER.get(row.get("commercial_priority"), 9),
        row.get("commercial_confidence") == "mixed_review",
        row.get("source_identity") or "",
    )


def build_queue(run, recent_days, *, root=None):
    root = root or run.parent
    stored = {p["process_reference"]: p for p in read_json(run / "processes.json")["processes"]}
    result = window.reevaluate(run, recent_days, root=root, replay_commercial=False)
    known = history(root)
    reviews = load_human_reviews()
    rows = {row["process_reference"]: row for row in result["rows"]}
    eligible = [row for row in result["rows"] if not row["excluded_reason"]]
    queue = []
    for position, row in enumerate(sorted(eligible, key=order_key), start=1):
        identity = row["source_identity"]
        queue.append(
            {
                "position": position,
                "source": row["source"],
                "source_identity": identity,
                "process_reference": row["process_reference"],
                "entity": row["entity_name"],
                "department": row["department"],
                "validity_status": row["validity_status"],
                "deadline_at": row.get("deadline_at"),
                "commercial_priority": row["commercial_priority"],
                "commercial_confidence": row["commercial_confidence"],
                "primary_category": row["primary_category"],
                "category_terms": row["category_terms"],
                "selected_in_original_run": bool(stored[row["process_reference"]].get("sampled")),
                "inventory": known.get(identity, {}).get("inventory", "none"),
                "analysis": known.get(identity, {}).get("analysis"),
                "human_review": [
                    review["observation"]
                    for review in human_reviews_for([identity, row["process_reference"]], reviews)
                ],
                "experience": "undetermined_until_documents_are_read",
                "object": row["object"],
            }
        )
    reconciliation = Counter()
    detail = []
    for reference, original in stored.items():
        if original.get("excluded_reason"):
            continue
        now = rows[reference]
        if now["excluded_reason"]:
            outcome = f"excluded:{now['excluded_reason']}"
        elif original.get("sampled"):
            outcome = "eligible:selected_in_original_run"
        else:
            outcome = "eligible:pending_queue"
        reconciliation[outcome] += 1
        if outcome.startswith("excluded"):
            detail.append(
                {
                    "source_identity": original["source_identity"],
                    "reason": now["excluded_reason"],
                    "category_exclusions": now.get("category_exclusions"),
                    "object": original["object"],
                }
            )
    newly = [
        row["source_identity"]
        for row in eligible
        if stored[row["process_reference"]].get("excluded_reason")
    ]
    return {
        "run": run.name,
        "network_requests": 0,
        "commercial_profile": result["summary"]["commercial_profile"],
        "commercial_assessment": result["summary"]["commercial_assessment"],
        "descriptions_stored": result["summary"]["descriptions_stored"],
        "original_eligible": sum(1 for p in stored.values() if not p.get("excluded_reason")),
        "current_eligible": len(eligible),
        "reconciliation": dict(reconciliation),
        "excluded_now": detail,
        "newly_eligible": newly,
        "queue": queue,
    }


def main(argv=None):
    import eureka_nacional_en01 as runner

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run")
    parser.add_argument("--recent-days", type=int, required=True)
    args = parser.parse_args(argv)
    run = runner.OUTPUT_ROOT / args.run
    if not args.run.startswith("en01-") or run.resolve() != run or not run.is_dir():
        print("EN-01: corrida invalida.")
        return 1
    result = build_queue(run, args.recent_days)
    path = run / QUEUE_FILE
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
    print(
        json.dumps(
            {k: result[k] for k in ("original_eligible", "current_eligible", "reconciliation")}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
