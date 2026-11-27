"""Offline funnel report for an EN-01 exploration, separated by source. Read-only inputs.

Combines a stage-1 run with optional SECOP I stage-3 results and writes blind_report.json
and blind_report.md as new files. No network, no reclassification, no rule changes.

When ``findings_recomputed.json`` exists (eureka_nacional_findings_recompute.py), the report
adds the presentation layer: findings ordered by category and then by commercial priority
A/B/C, a table of processes that need human attention and the eligible processes that were
not analyzed. Documentary categories never remove a process from the report.
"""

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from eureka_nacional_findings import EFFORT, LABELS, RANK

FAVORABLE_STATUS = "no_experience_required"
FAVORABLE_REVIEW = "explicit_favorable"
OUTPUT_ROOT = Path(__file__).resolve().parents[2] / ".local" / "eureka-nacional-spike"
FINDINGS_FILE = "findings_recomputed.json"
COMMERCIAL_ORDER = {"A": 1, "B": 2, "C": 3}
NON_DOCUMENTARY_EXCLUSIONS = ("outside_geography_scope",)


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


def _finding_item(process, result, row):
    finding = (row or {}).get("finding") or result.get("finding") or {}
    documents = (row or {}).get("documents") or []
    coverage = finding.get("coverage") or {}
    category = finding.get("category", "not_computed")
    return {
        "source": process.get("source") or "unknown",
        "process_reference": process["process_reference"],
        "source_identity": process.get("source_identity"),
        "entity": process.get("entity_name"),
        "department": process.get("department"),
        "commercial_priority": process.get("commercial_priority"),
        "commercial_category": process.get("primary_category"),
        "category": category,
        "label": LABELS.get(category, "Hallazgo sin calcular"),
        "basis": finding.get("basis"),
        "formal_status": finding.get("formal_status", result.get("status")),
        "stored_status": (row or {}).get("stored_status", result.get("status")),
        "evidence_layer": (row or {}).get("evidence_layer"),
        "review_effort": finding.get("review_effort"),
        "needs_human_attention": finding.get("needs_human_attention", True),
        "warnings": finding.get("warnings", []),
        "habilitating_sections": [
            {
                key: section.get(key)
                for key in ("document", "heading", "pages", "closed", "item_count")
            }
            | {"experience_terms": section.get("experience_terms", [])}
            for section in finding.get("habilitating_sections", [])
        ],
        "requirement_indications": [
            {key: item.get(key) for key in ("document", "page", "basis", "scope")}
            for item in finding.get("requirement_indications", [])
        ],
        "documents_complete": [doc["document"] for doc in coverage.get("system_verified", [])]
        or [doc["name"] for doc in documents if doc.get("complete")],
        "documents_missing": coverage.get("not_verified_by_system", []),
        "auxiliary_pending": coverage.get("non_governing_pending", []),
        "why_not_formal": finding.get("why_not_formal"),
        "resolution_actions": finding.get("resolution_actions", []),
        "human_review": [
            {
                key: review.get(key)
                for key in ("observation", "documents_reviewed", "recorded_on", "system_verified")
            }
            for review in finding.get("human_review", [])
        ],
    }


def presentation(discovery, results, findings):
    """Findings ordered by category, commercial priority A/B/C and review effort."""
    items, not_analyzed = [], []
    for process in discovery["processes"]:
        if process.get("excluded_reason"):
            continue
        reference = process["process_reference"]
        result = results.get(reference)
        if not process.get("sampled") or result is None:
            not_analyzed.append(
                {
                    "source": process.get("source") or "unknown",
                    "source_identity": process.get("source_identity"),
                    "entity": process.get("entity_name"),
                    "commercial_priority": process.get("commercial_priority"),
                    "reason": (
                        process.get("not_selected_reason") or "unrecorded"
                        if not process.get("sampled")
                        else "selected_without_result"
                    ),
                }
            )
            continue
        items.append(_finding_item(process, result, findings.get(reference)))
    items.sort(
        key=lambda item: (
            RANK.get(item["category"], 9),
            COMMERCIAL_ORDER.get(item["commercial_priority"], 9),
            EFFORT.get(item["review_effort"], 9),
            item["source_identity"] or item["process_reference"],
        )
    )
    not_analyzed.sort(
        key=lambda item: (
            COMMERCIAL_ORDER.get(item["commercial_priority"], 9),
            item["source_identity"] or "",
        )
    )
    counts = Counter(item["category"] for item in items)
    attention = [item for item in items if item["needs_human_attention"]]
    excluded = Counter(
        process["excluded_reason"]
        for process in discovery["processes"]
        if process.get("excluded_reason") in NON_DOCUMENTARY_EXCLUSIONS
    )
    excluded.update(
        item["reason"] for item in not_analyzed if item["reason"] != "selected_without_result"
    )
    return {
        "categories_order": [LABELS[key] for key in sorted(RANK, key=RANK.get)],
        "counts": {LABELS.get(key, key): counts.get(key, 0) for key in sorted(RANK, key=RANK.get)}
        | ({"Hallazgo sin calcular": counts["not_computed"]} if counts["not_computed"] else {}),
        "visibility": {
            "analyzed": len(items),
            "visible": len(items),
            "needs_human_attention": len(attention),
            "attention_by_effort": dict(Counter(item["review_effort"] for item in attention)),
            "eligible_without_documentary_analysis": len(not_analyzed),
            "selected_without_result": sum(
                item["reason"] == "selected_without_result" for item in not_analyzed
            ),
            "excluded_for_non_documentary_reasons": dict(excluded),
            "excluded_by_documentary_category": 0,
        },
        "ordered": items,
        "attention": attention,
        "without_documentary_analysis": not_analyzed,
    }


def build_report(run, secop1_results=None, *, commit=None, findings=None):
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
            ((findings or {}).get(reference) or result)
            .get("finding", {})
            .get("category", "not_computed")
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
        "findings": (presentation(discovery, results, findings) if findings is not None else None),
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
    if report.get("findings"):
        lines += findings_markdown(report["findings"])
    return "\n".join(lines) + "\n"


def _cell(value):
    return str(value).replace("|", "/").replace("\n", " ")


def findings_markdown(findings):
    lines = ["", "## Hallazgos (capa de presentación)", ""]
    lines += [
        "Orden: categoría, luego prioridad comercial A/B/C y esfuerzo de revisión. "
        "Ninguna categoría documental excluye procesos.",
        "",
        "| Categoría | Procesos |",
        "|---|---|",
    ]
    lines += [f"| {label} | {count} |" for label, count in findings["counts"].items()]
    visibility = findings["visibility"]
    lines += [
        "",
        f"- Analizados y visibles: {visibility['visible']} · requieren atención humana: "
        f"{visibility['needs_human_attention']} "
        f"({json.dumps(visibility['attention_by_effort'], ensure_ascii=False)})",
        f"- Elegibles sin análisis documental: "
        f"{visibility['eligible_without_documentary_analysis']} (de ellos, seleccionados sin "
        f"resultado por la corrida: {visibility['selected_without_result']})",
        f"- Excluidos por motivos no documentales: "
        f"{json.dumps(visibility['excluded_for_non_documentary_reasons'], ensure_ascii=False)}",
        "",
    ]
    current = None
    for item in findings["ordered"]:
        if item["label"] != current:
            current = item["label"]
            lines += ["", f"### {current}", ""]
        lines.append(
            f"- [{item['commercial_priority'] or '-'}] {item['source_identity']} · "
            f"{item['entity']} · estado formal {item['formal_status']} · {item['basis']}"
        )
    lines += [
        "",
        "### Procesos que requieren atención humana",
        "",
        "| Proceso | Prioridad | Hallazgo | Evidencia de Eureka | Completos | Faltan | "
        "Por qué | Acción documental | Revisión humana (aparte) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for item in findings["attention"]:
        evidence = [
            f"{s['heading']} (p. {s['pages']}, {s['item_count']} ítems, "
            f"{'cerrada' if s['closed'] else 'sin cierre'}"
            f"{', términos: ' + ', '.join(s['experience_terms']) if s['experience_terms'] else ''})"
            for s in item["habilitating_sections"]
        ] + [
            f"exigencia en {i['document']} p. {i['page']} ({i['basis']})"
            for i in item["requirement_indications"]
        ]
        missing = [f"{d['document']} ({d['reason']})" for d in item["documents_missing"]]
        why = item["basis"]
        if item["why_not_formal"]:
            why += f"; sin conclusión formal: {item['why_not_formal']['reason']}"
        human = "; ".join(
            f"{h['observation']} en {', '.join(h['documents_reviewed'])}"
            f" (no verificado por el sistema)"
            for h in item["human_review"]
        )
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    f"{item['source_identity']} · {item['entity']}",
                    item["commercial_priority"] or "-",
                    item["label"],
                    "; ".join(evidence) or "sin sección habilitante ni cláusulas",
                    ", ".join(item["documents_complete"]) or "ninguno",
                    ", ".join(missing) or "ninguno",
                    why,
                    " ".join(item["resolution_actions"]) or "-",
                    human or "-",
                )
            )
            + " |"
        )
    lines += ["", "### Elegibles sin análisis documental (trazabilidad)", ""]
    lines += [
        f"- [{item['commercial_priority'] or '-'}] {item['source_identity']} · {item['entity']} "
        f"· {item['reason']}"
        for item in findings["without_documentary_analysis"]
    ]
    return lines


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
    recomputed = read_json(run / FINDINGS_FILE)
    findings = {row["process_reference"]: row for row in recomputed["rows"]} if recomputed else None
    report = build_report(
        run, stage3, commit=git_commit(Path(__file__).resolve().parents[2]), findings=findings
    )
    # The enriched report is a separate file; the original funnel report is preserved.
    stem = "blind_report_findings" if findings is not None else "blind_report"
    (run / f"{stem}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run / f"{stem}.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({s: b["classification"] for s, b in report["by_source"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
