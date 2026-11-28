"""Offline re-evaluation of stored discovery rows with a different publication window.

Reuses the runner's selection (freshness, validity, geography, SECOP I readiness, quotas)
over ``processes.json`` of an exploration, without querying Licitaciones.info. Commercial
assessment is not recomputed: the stored result of the original run is replayed in order, so
filters and MPNE stay exactly as they were. The reference clock is the original cutoff.
Output is a new file ``window_reevaluation_<N>d.json``; an existing file is never overwritten.
"""

import argparse
import json
import os
from collections import Counter
from datetime import datetime
from types import SimpleNamespace

import eureka_nacional_en01 as en01

COMMERCIAL_KEYS = (
    "category_matches",
    "primary_category",
    "commercial_priority",
    "commercial_reason",
    "commercial_exclusion",
    "category_exclusions",
    "excluded_product_codes",
    "description_available",
    "accessory_service_signal",
    "commercial_confidence",
)
RUNTIME_KEYS = (
    "age_days",
    "recent",
    "freshness_warnings",
    "validity_status",
    "validity_warning",
    "excluded_reason",
    "sampled",
    "not_selected_reason",
    "supply_prefilter_match",
    "preferred_modality",
)


def known_identities(root, exclude):
    known = set()
    for path in sorted(root.glob("en01-*/processes.json")):
        if path.parent.name == exclude:
            continue
        for process in json.loads(path.read_text(encoding="utf-8")).get("processes", []):
            if process.get("source_identity"):
                known.add(process["source_identity"])
    return known


def reevaluate(run, recent_days, *, processes=15, secop1_processes=5, root=None):
    discovery = json.loads((run / "processes.json").read_text(encoding="utf-8"))
    now = datetime.fromisoformat(discovery["cutoff"])
    stored = discovery["processes"]
    candidates, replay = {}, []
    for process in stored:
        candidate = {k: v for k, v in process.items() if k not in COMMERCIAL_KEYS + RUNTIME_KEYS}
        candidate.update(description="", raw_source_reference={})
        candidates[process["process_reference"]] = candidate
        replay.append((process["object"], {k: process.get(k) for k in COMMERCIAL_KEYS}))
    queue = iter(replay)

    def stored_commercial(_profile, obj, _description, _codes):
        expected, values = next(queue)
        if obj != expected:
            raise ValueError("El orden de los avisos no coincide con el almacenado.")
        return dict(values)

    args = SimpleNamespace(
        recent_days=recent_days,
        processes=processes,
        secop1_processes=secop1_processes,
        include_secop1=True,
        exploratory=True,
        excluded_secop_ids=frozenset(),
    )
    selection = {}
    original = en01.assess_commercial
    en01.assess_commercial = stored_commercial
    try:
        en01.select_processes(candidates, args, now, selection, en01.load_commercial_profile())
    finally:
        en01.assess_commercial = original
    known = known_identities(root or run.parent, run.name)
    rows = []
    for process in selection["processes"]:
        rows.append(
            {
                key: process.get(key)
                for key in (
                    "source",
                    "source_identity",
                    "department",
                    "municipality",
                    "entity_name",
                    "object",
                    "published_at",
                    "age_days",
                    "modality",
                    "validity_status",
                    "commercial_priority",
                    "primary_category",
                    "commercial_exclusion",
                    "excluded_reason",
                    "sampled",
                    "not_selected_reason",
                )
            }
            | {"known_before": process.get("source_identity") in known}
        )
    eligible = [r for r in rows if not r["excluded_reason"]]
    summary = {
        "run": run.name,
        "recent_days": recent_days,
        "reference_clock": discovery["cutoff"],
        "network_requests": 0,
        "commercial_assessment": "replayed_from_original_run",
        "discovered": len(rows),
        "excluded_by_reason": dict(
            Counter(r["excluded_reason"] for r in rows if r["excluded_reason"])
        ),
        "eligible": len(eligible),
        "eligible_by_source_department": dict(
            Counter(f"{r['source']}|{r['department']}" for r in eligible)
        ),
        "eligible_by_priority": dict(Counter(r["commercial_priority"] for r in eligible)),
        "selected_under_quotas": sum(bool(r["sampled"]) for r in eligible),
        "not_selected_by_quota": dict(
            Counter(r["not_selected_reason"] for r in eligible if not r["sampled"])
        ),
        "eligible_new": sum(not r["known_before"] for r in eligible),
    }
    return {"summary": summary, "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run")
    parser.add_argument("--recent-days", type=int, choices=range(1, 61), required=True)
    args = parser.parse_args(argv)
    root = en01.OUTPUT_ROOT
    run = root / args.run
    if not args.run.startswith("en01-") or run.resolve() != run or not run.is_dir():
        print("EN-01: corrida invalida.")
        return 1
    result = reevaluate(run, args.recent_days)
    path = run / f"window_reevaluation_{args.recent_days}d.json"
    if path.exists():
        print(f"EN-01: {path.name} ya existe; no se sobrescribe.")
        return 1
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
