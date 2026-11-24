"""Replay human corrections from a local EN-01.1 JSONL file without CDP."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from eureka_nacional_experience import NEG, classify_experience


def evaluate(cases):
    matched = errors = false_positives = false_negatives = 0
    for case in cases:
        documents = [
            {
                **document,
                "fragments": [SimpleNamespace(**fragment) for fragment in document["fragments"]],
            }
            for document in case["documents"]
        ]
        result = classify_experience(documents, inventory_complete=case["inventory_complete"])
        kinds = {item["assertion_type"] for item in result["evidence"]}
        favorable = NEG in kinds
        expected = case["expected_favorable"]
        false_positives += favorable and not expected
        false_negatives += expected and not favorable
        if result["status"] != case["expected_status"] or favorable != expected:
            errors += 1
        else:
            matched += 1
    return {
        "matched": matched,
        "discrepancies": errors,
        "false_positive_favorable": false_positives,
        "false_negative_favorable": false_negatives,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", type=Path)
    args = parser.parse_args(argv)
    with args.labels.open(encoding="utf-8") as stream:
        result = evaluate(json.loads(line) for line in stream if line.strip())
    print(json.dumps(result))
    return 1 if result["discrepancies"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
