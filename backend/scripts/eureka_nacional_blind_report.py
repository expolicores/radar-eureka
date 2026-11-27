"""Offline funnel report for an EN-01 exploration, separated by source. Read-only inputs.

Combines a stage-1 run with optional SECOP I stage-3 results and writes blind_report.json
and blind_report.md as new files. No network, no reclassification, no rule changes.
"""

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

FAVORABLE_STATUS = "no_experience_required"
FAVORABLE_REVIEW = "explicit_favorable"
OUTPUT_ROOT = Path(__file__).resolve().parents[2] / ".local" / "eureka-nacional-spike"


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def git_commit(root):
    try:
        out = subprocess.run(  # noqa: S603 -- fixed local git query
            ["git", "-C", str(root), "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError:
        return None
    return out.stdout.strip() or None


def build_report(run, secop1_results=None, *, commit=None):
    discovery = read_json(run / "processes.json")
    metrics = read_json(run / "metrics.json", {})
    results = {
        r["process_reference"]: r for r in read_json(run / "experience_requirements.json", [])
    }
    inventories = {
        c["process_reference"]: c["documents"] for c in read_json(run / "documents.json", [])
    }
    stage3 = {}
    if secop1_results is not None:
        stage3 = {
            r["process_reference"]: r
            for r in read_json(secop1_results / "experience_requirements.json", [])
        }
        results.update(stage3)
    receipts = read_json(run / "download_receipts.json", {})
    queue = read_json(run / "secop1_queue.json")
    attempts = (
        [read_json(path) for path in sorted((run / "secop1_attempts").glob("*.json"))]
        if (run / "secop1_attempts").is_dir()
        else []
    )

    sources = {}
    for process in discovery["processes"]:
        source = process.get("source") or "unknown"
        bucket = sources.setdefault(
            source,
            {
                "discovered": 0,
                "excluded_by_reason": Counter(),
                "eligible": 0,
                "selected": 0,
                "eligible_not_selected": Counter(),
                "analyzed": 0,
                "with_inventory": 0,
                "documents_downloaded": 0,
                "governing_complete": 0,
                "classification": Counter(),
                "review_categories": Counter(),
                "finding_categories": Counter(),
                "potentially_favorable": [],
            },
        )
        bucket["discovered"] += 1
        if process.get("excluded_reason"):
            bucket["excluded_by_reason"][process["excluded_reason"]] += 1
            continue
        bucket["eligible"] += 1
        if not process.get("sampled"):
            bucket["eligible_not_selected"][process.get("not_selected_reason") or "unrecorded"] += 1
            continue
        bucket["selected"] += 1
        reference = process["process_reference"]
        documents = inventories.get(reference, [])
        bucket["with_inventory"] += bool(documents)
        result = results.get(reference)
        if source == "secop1" and stage3:
            stage_docs = []
            for case in read_json(secop1_results / "documents.json", []):
                if case["process_reference"] == reference:
                    stage_docs = case["documents"]
            documents = stage_docs or documents
        bucket["documents_downloaded"] += sum(bool(d.get("sha256")) for d in documents)
        bucket["governing_complete"] += any(
            d.get("complete") and d.get("role") in {"primary", "amendment"} for d in documents
        )
        if result is None:
            continue
        bucket["analyzed"] += 1
        bucket["classification"][result["status"]] += 1
        bucket["review_categories"][result["review_category"]] += 1
        bucket["finding_categories"][
            (result.get("finding") or {}).get("category", "not_computed")
        ] += 1
        if result["status"] == FAVORABLE_STATUS or result["review_category"] == FAVORABLE_REVIEW:
            bucket["potentially_favorable"].append(
                {
                    "process_reference": reference,
                    "source_identity": process.get("source_identity"),
                    "entity": process.get("entity_name"),
                    "department": process.get("department"),
                    "commercial_priority": process.get("commercial_priority"),
                    "commercial_category": process.get("primary_category"),
                    "status": result["status"],
                    "review_category": result["review_category"],
                    "evidence_pages": sorted(
                        {e.get("page") for e in result.get("review_evidence", []) if e.get("page")}
                    ),
                }
            )
    for bucket in sources.values():
        for key in (
            "excluded_by_reason",
            "eligible_not_selected",
            "classification",
            "review_categories",
            "finding_categories",
        ):
            bucket[key] = dict(bucket[key])
    secop1_acquisition = None
    if queue is not None:
        secop1_acquisition = {
            "queued": len(queue["items"]),
            "batch_sha256": queue["batch_sha256"],
            "attempts": len(attempts),
            "stored": sum(a.get("outcome") == "stored" for a in attempts),
            "rejected": sum(a.get("outcome") == "rejected" for a in attempts),
            "receipts": sum(k.startswith("secop1:") for k in receipts),
        }
    return {
        "run": run.name,
        "secop1_results": secop1_results.name if secop1_results else None,
        "reproducibility": {
            "commit": commit,
            "cutoff": discovery.get("cutoff"),
            "recent_days": discovery.get("recent_days"),
            "geography": discovery.get("geography"),
            "commercial_profile": discovery.get("commercial_profile"),
            "limits": metrics.get("limits"),
            "discovery_stop_reason": discovery.get("stop_reason"),
            "provider_count_last_page": (discovery.get("pages") or [{}])[-1].get("provider_count"),
            "pages_read": len(discovery.get("pages", [])),
        },
        "run_status": metrics.get("status"),
        "request_credits_used": metrics.get("request_credits_used"),
        "by_source": sources,
        "secop1_acquisition": secop1_acquisition,
        "favorable_definition": (
            "status no_experience_required, o revision explicit_favorable "
            "(ausencia explicita que requiere corroboracion). El silencio documental no cuenta."
        ),
    }


def markdown(report):
    lines = [f"# Embudo EN-01 · {report['run']}", ""]
    repro = report["reproducibility"]
    lines += [
        f"- Commit: `{repro['commit']}`",
        f"- Corte: {repro['cutoff']} · ventana {repro['recent_days']} días",
        f"- Geografía: {json.dumps(repro['geography'], ensure_ascii=False)}",
        f"- Páginas leídas: {repro['pages_read']} · parada: {repro['discovery_stop_reason']} "
        f"· total del proveedor: {repro['provider_count_last_page']}",
        "",
    ]
    for source, b in sorted(report["by_source"].items()):
        lines += [
            f"## {source}",
            "",
            f"- Descubiertos: {b['discovered']} · elegibles: {b['eligible']} · "
            f"seleccionados: {b['selected']} · analizados: {b['analyzed']}",
            f"- Excluidos: {json.dumps(b['excluded_by_reason'], ensure_ascii=False)}",
            f"- Elegibles no seleccionados: {json.dumps(b['eligible_not_selected'])}",
            f"- Con inventario: {b['with_inventory']} · PDF descargados: "
            f"{b['documents_downloaded']} · rector completo: {b['governing_complete']}",
            f"- Clasificación: {json.dumps(b['classification'])}",
            f"- Revisión: {json.dumps(b['review_categories'])}",
            f"- Hallazgos (presentación): {json.dumps(b['finding_categories'])}",
            f"- Potencialmente favorables: {len(b['potentially_favorable'])}",
            "",
        ]
        for item in b["potentially_favorable"]:
            lines.append(
                f"  - {item['source_identity']} · {item['entity']} · {item['status']} / "
                f"{item['review_category']} · páginas {item['evidence_pages']}"
            )
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run")
    parser.add_argument("--secop1-results", help="Directorio de la etapa 3 SECOP I.")
    args = parser.parse_args(argv)
    run = OUTPUT_ROOT / args.run
    stage3 = OUTPUT_ROOT / args.secop1_results if args.secop1_results else None
    for path in filter(None, (run, stage3)):
        if path.resolve() != path or path.parent != OUTPUT_ROOT or not path.is_dir():
            print("EN-01: directorio de corrida invalido.")
            return 1
    report = build_report(run, stage3, commit=git_commit(Path(__file__).resolve().parents[2]))
    (run / "blind_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run / "blind_report.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({s: b["classification"] for s, b in report["by_source"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
