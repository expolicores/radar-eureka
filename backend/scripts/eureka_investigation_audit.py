"""Export receipts and readable results for a completed real research exercise, offline."""

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, required=True)
    args = parser.parse_args()
    root = args.sample_directory
    sample = load(root / "sample-result.json")
    report = load(root / "research-cycle-report.json")
    cycle = load(root / "economic-cycle.json")
    selection = load(root / "selection.json")
    discovery = load(root / "discovery.json")
    by_id = {p["id"]: p for p in report["processes"]}
    cycles = {p["process_identity"]: p for p in cycle["processes"]}
    extractions = [e for p in sample["processes"] for e in p.get("extractions", [])]
    all_items = [
        i
        for p in cycle["processes"]
        for i in p["products"]
        if i["normalized_product"] == "televisor"
    ]
    started = datetime.fromisoformat(sample["started_at"])
    finished = datetime.fromisoformat(sample["finished_at"])
    failures = [
        {
            "process": p["process"]["referencia_del_proceso"],
            "document_id": e["document"]["document_id"],
            "status": e["status"],
            "code": e.get("error_code"),
            "coverage_complete": e.get("diagnostics", {}).get("coverage_complete"),
        }
        for p in sample["processes"]
        for e in p.get("extractions", [])
        if e["status"] != "completed"
        or not e.get("text_length")
        or e.get("diagnostics", {}).get("coverage_complete") is False
    ]
    summary = {
        "window_start": sample["window_start"],
        "window_before": sample["window_before"],
        "source": "socrata_secop",
        "comparison_policy": report.get("comparison_policy"),
        "started_at_bogota": started.astimezone(ZoneInfo("America/Bogota")).isoformat(),
        "finished_at_bogota": finished.astimezone(ZoneInfo("America/Bogota")).isoformat(),
        "duration_seconds": round((finished - started).total_seconds(), 2),
        "processes_found": selection["discovered_unique"],
        "mature_metadata_candidates": selection["mature_metadata"],
        "selected": len(selection["rows"]),
        "processes_attempted": len(sample["processes"]),
        "reviewed": sum(bool(p.get("extractions")) for p in sample["processes"]),
        "tv_documented_scope": sum(p.get("tv_confirmed", False) for p in report["processes"]),
        "tv_processes_with_reconstructed_records": sum(
            any(i["normalized_product"] == "televisor" for i in p["products"])
            for p in cycle["processes"]
        ),
        "documents_in_inventory": sum(len(p["inventory"]) for p in sample["processes"]),
        "documents_selected": sum(
            len(p.get("selected_documents", [])) for p in sample["processes"]
        ),
        "documents_reused": sum(p.get("reused_downloads", 0) for p in sample["processes"]),
        "new_downloads": sum(
            p.get("download", {}).get("available", 0) for p in sample["processes"]
        ),
        "download_failures": sum(
            p.get("download", {}).get("failed", 0) for p in sample["processes"]
        ),
        "extraction_attempts": len(extractions),
        "extractions_reused": sum(bool(e.get("reused")) for e in extractions),
        "extraction_statuses": dict(Counter(e["status"] for e in extractions)),
        "empty_text_documents": sum(not e.get("text_length") for e in extractions),
        "partial_coverage": sum(
            e.get("diagnostics", {}).get("coverage_complete") is False for e in extractions
        ),
        "ocr_documents": sum(
            bool(e.get("diagnostics", {}).get("required_pages")) for e in extractions
        ),
        "ocr_pages_processed": sum(
            len(e.get("diagnostics", {}).get("processed_pages", [])) for e in extractions
        ),
        "ocr_pages_computed_this_run": sum(
            len(e.get("diagnostics", {}).get("processed_pages", []))
            for e in extractions
            if not e.get("reused")
        ),
        "ocr_pages_reused": sum(
            len(e.get("diagnostics", {}).get("processed_pages", []))
            for e in extractions
            if e.get("reused")
        ),
        "facts": sum(p["facts_count"] for p in report["processes"]),
        "canonicals": sum(p["canonicals_count"] for p in report["processes"]),
        "observations_normalized": report["summary"]["tv_observations"],
        "cycle_summary": cycle["summary"],
        "contract_unit_prices_recovered": sum(
            i.get("contract_unit_price") is not None for i in all_items
        ),
        "awarded_unit_prices_recovered": sum(
            i.get("awarded_unit_price") is not None for i in all_items
        ),
        "evaluated_unit_prices_recovered": sum(
            i.get("evaluated_offer_unit_price") is not None for i in all_items
        ),
        "comparability": cycle["comparability_counts"],
        "valid_monetary_pairs": cycle["comparisons_possible"],
        "signals": len(cycle["signals"]),
        "exclusion_reasons": cycle.get("comparison_exclusion_reasons", {}),
        "process_errors": [
            {"process": p["process"]["referencia_del_proceso"], "errors": p["errors"]}
            for p in sample["processes"]
            if p.get("errors")
        ],
        "failures": failures,
        "warnings": [
            "purposeful_ranked_sample_not_exhaustive",
            discovery["pagination_warning"],
            "socrata_may_lag",
            "no_inflation_or_fx_adjustment",
        ],
    }
    (root / "run-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf8"
    )

    def cell(value: Any) -> str:
        return (
            str(value if value is not None else "Desconocido").replace("|", "/").replace("\n", " ")
        )

    lines = [
        "# Tercer ejercicio investigativo real: 60 días",
        "",
        f"Ventana de publicaciones: **{sample['window_start']} inclusive / "
        f"{sample['window_before']} exclusivo**. "
        "Para comparar se exige además fecha de compra verificada dentro de esta ventana, "
        "sin sustituirla por publicación.",
        "",
        "Fuentes únicas: Socrata/SECOP. Muestra por ranking determinístico, "
        "prioridad 55/65 y objetos amplios; "
        "no es exhaustiva ni representativa estadísticamente. No se ejecutaron Radar, "
        "CDP, Web Search, agentes/LLM, mercado privado ni TVEC.",
        "",
        "## Resumen",
        "",
        "```json",
        json.dumps(
            {k: v for k, v in summary.items() if k not in ("process_errors", "failures")},
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Procesos revisados",
        "",
        "| Proceso | Identidad | Entidad | Publicación | Docs seleccionados | TV en documentos | "
        "Registros del ciclo | Precios de compra verificados | Errores |",
        "|---|---|---|---|---:|---|---:|---:|---|",
    ]
    for p in sample["processes"]:
        row = p["process"]
        identifier = row["id_del_proceso"]
        view = by_id[identifier]
        items = cycles.get(identifier, {}).get("products", [])
        lines.append(
            "| "
            + " | ".join(
                cell(v)
                for v in [
                    row["referencia_del_proceso"],
                    identifier,
                    row["entidad"],
                    row["fecha_de_publicacion_del"],
                    len(p.get("selected_documents", [])),
                    view["tv_confirmed"],
                    len(items),
                    sum(i["purchase_price"] is not None for i in items),
                    p.get("errors", []),
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Precios de compra recuperados",
        "",
        "| Proceso | Producto | Cantidad | Precio unitario | Columna | "
        "Fecha de compra | Conflictos | Evidencia |",
        "|---|---|---:|---:|---|---|---|---|",
    ]
    for p in cycle["processes"]:
        for i in p["products"]:
            chosen = i["purchase_price"]
            if not chosen or i["normalized_product"] != "televisor":
                continue
            refs = [
                e["source_document"] + " p." + str(e["source_page"])
                for a in chosen["evidence"]
                for e in a["evidence"]
            ]
            lines.append(
                "| "
                + " | ".join(
                    cell(v)
                    for v in [
                        p["process_code"],
                        i["item_description"][:180],
                        i["quantity"],
                        chosen["value"],
                        chosen["column"],
                        i.get("purchase_date"),
                        i["conflicts"],
                        "; ".join(refs),
                    ]
                )
                + " |"
            )
    lines += ["", "## Pares monetarios válidos", ""]
    for pair in cycle["comparisons"]:
        if not pair.get("comparison_eligible"):
            continue
        lines += ["### " + pair["id"], "", "| Campo | A | B |", "|---|---|---|"]
        for field in (
            "entity",
            "process_code",
            "process_identity",
            "description",
            "date",
            "date_source",
            "unit_price",
            "quantity",
            "unit",
            "currency",
            "tax_basis",
            "characteristics",
        ):
            lines.append(
                "| " + field + " | " + " | ".join(cell(s[field]) for s in pair["sides"]) + " |"
            )
        lines += [
            "",
            f"Comparabilidad: {pair['comparability_level']}. "
            f"Diferencia absoluta: {pair['absolute_difference_cop']}. "
            f"Diferencia porcentual respecto al menor: {pair['difference_pct']} %. "
            f"Días: {pair['days_between']}.",
            "",
            "Limitaciones: " + cell(pair["limitations"]),
            "",
        ]
        for side in pair["sides"]:
            lines.append("Evidencia " + side["process_identity"] + ":")
            for a in side["evidence"]:
                for e in a.get("evidence", []):
                    lines.append(
                        "- "
                        + e["source_document"]
                        + " p."
                        + str(e["source_page"])
                        + " / "
                        + e["extraction_method"]
                        + " / "
                        + a["value_origin"]
                    )
            lines.append("")
    if not cycle["comparisons_possible"]:
        lines += [
            "No se encontró un par monetario que cumpla todos los requisitos. "
            "No se imputaron valores globales ni se promovieron "
            "presupuestos/ofertas no aceptadas a compras.",
            "",
        ]
    lines += [
        "## Fallos y cobertura",
        "",
        "```json",
        json.dumps(
            {"process_errors": summary["process_errors"], "documents": failures},
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "Cobertura detallada y todas las columnas por producto: "
        "`economic-cycle.md` y `economic-cycle.json`. "
        "Los conteos de documentos representan asociaciones documentales "
        "seleccionadas por proceso. "
        "La presencia documental de TV se informa por separado del ítem económico reconstruido.",
        "",
    ]
    (root / "results.md").write_text("\n".join(lines), encoding="utf8")
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "selected",
                    "reviewed",
                    "tv_documented_scope",
                    "new_downloads",
                    "documents_reused",
                    "download_failures",
                    "valid_monetary_pairs",
                    "signals",
                )
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
