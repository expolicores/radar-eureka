"""Reconstruct completed research samples offline. No DB, network, downloads or OCR."""

import argparse
import csv
import json
from pathlib import Path

from public_procurement.investigation.economic_cycle import ECONOMIC_FIELDS, build_cycles
from public_procurement.investigation.research import ResearchReportStore
from public_procurement.shared.config import Settings


def write_markdown(cycle: dict, directory: Path) -> None:
    def cell(value: object) -> str:
        return (
            str(value if value is not None else "Desconocido").replace("|", "/").replace("\n", " ")
        )

    lines = [
        "# Reconstrucción económica determinística",
        "",
        "Solo los 12 procesos con TV documental de la muestra previa. "
        "Sin requests, descargas, OCR adicional, IA ni cambios en DB.",
        "",
        "## Métricas",
        "",
        "```json",
        json.dumps(cycle["summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Comparaciones",
        "",
        json.dumps(cycle["comparability_counts"], ensure_ascii=False),
        "",
        f"Comparaciones de precios sustentadas: {cycle['comparisons_possible']}. "
        f"Señales: {len(cycle['signals'])}.",
        "",
        "Los pares parciales son pares de registros de evidencia, no compras independientes. "
        "Los registros sin enlace seguro permanecen separados.",
        "",
    ]
    for process in cycle["processes"]:
        lines += [
            "## " + process["process_code"],
            "",
            process["process_identity"],
            "",
            "### Cobertura documental",
            "",
            "| Etapa | Documento | Seleccionado | Extracción | Cobertura completa | "
            "Páginas con texto |",
            "|---|---|---|---|---|---|",
        ]
        for d in process["document_coverage"]:
            lines.append(
                "| "
                + " | ".join(
                    cell(v)
                    for v in [
                        d["stage"],
                        d["document"],
                        d["selected"],
                        d["extraction_status"],
                        d["coverage_complete"],
                        d["pages_with_text"],
                    ]
                )
                + " |"
            )
        lines += [
            "",
            "### Valores globales: no asignados a productos",
            "",
            "```json",
            json.dumps(process["process_global_contracts"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
        for item in process["products"]:
            lines += [
                "### " + cell(item["item_description"][:200]),
                "",
                "Identidad local: `" + item["id"] + "`.",
                "",
                "Conflictos: " + cell(item["conflicts"]),
                "",
                "Notas: " + cell(item["notes"]),
                "",
                "Precio de compra seleccionado: "
                + (
                    cell(
                        {
                            "column": item["purchase_price"]["column"],
                            "value": item["purchase_price"]["value"],
                            "origin": item["purchase_price"]["origin"],
                        }
                    )
                    if item["purchase_price"]
                    else "Desconocido"
                ),
                "",
                "| Campo | Valor consistente | Estado | Alternativas / origen / documento-página |",
                "|---|---|---|---|",
            ]
            for key, field in item["fields"].items():
                alternatives = "; ".join(
                    a["value"]
                    + " ("
                    + a["value_origin"]
                    + "): "
                    + ", ".join(
                        e["source_document"]
                        + " p."
                        + str(e["source_page"])
                        + " / "
                        + e["extraction_method"]
                        for e in a["evidence"]
                    )
                    for a in field["alternatives"]
                )
                lines.append(
                    "| "
                    + " | ".join(
                        cell(v) for v in [key, field["value"], field["status"], alternatives]
                    )
                    + " |"
                )
            lines += [
                "",
                "La evidencia textual, IDs de facts/canonicals previos cuando existen, hashes, "
                "métodos, fórmulas y sus entradas están en `economic-cycle.json`.",
                "",
            ]
    (directory / "economic-cycle.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    directory = args.sample_directory.resolve()
    report = json.loads((directory / "research-report.json").read_text(encoding="utf-8"))
    fragments = {
        p["id"]: json.loads(
            (directory / (p["id"].replace(".", "-") + "-fragments.json")).read_text(
                encoding="utf-8"
            )
        )
        for p in report["processes"]
        if p.get("tv_confirmed")
    }
    cycle = build_cycles(report, fragments)
    write_markdown(cycle, directory)
    (directory / "economic-cycle.json").write_text(
        json.dumps(cycle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    columns = [
        "process_code",
        "process_identity",
        "item_description",
        "brand",
        "model",
        "quantity",
        "unit",
        *ECONOMIC_FIELDS,
        "conflict_status",
        "conflicts",
        "notes",
    ]
    with (directory / "economic-cycle.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for process in cycle["processes"]:
            for item in process["products"]:
                writer.writerow({k: item[k] for k in columns})
    by_process = {p["process_identity"]: p for p in cycle["processes"]}
    for process in report["processes"]:
        if process["id"] in by_process:
            process["economic_cycle"] = by_process[process["id"]]
    report["economic_cycle_summary"] = cycle["summary"]
    report["economic_cycle_version"] = cycle["version"]
    if report.get("comparison_policy") == "research-60d-v1":
        report["analysis_config"] = {
            "policy": "research-60d-v1",
            "max_days": 60,
            "signal_type": "PUBLIC_PRICE_DIFFERENCE",
            "percentage_threshold": None,
            "minimum_public_entities": 2,
            "price_basis": "verified_purchase_unit_price",
            "temporal_basis": "verified_purchase_date_not_publication",
            "macroeconomic_adjustment": None,
        }
    report["economic_cycle_comparisons"] = {
        k: cycle[k]
        for k in (
            "comparisons",
            "comparable_groups",
            "signals",
            "comparability_counts",
            "comparisons_possible",
        )
    }
    # Comparisons now follow reconstructed purchase prices, keeping the old projection on disk.
    for key in (
        "comparisons",
        "comparable_groups",
        "signals",
        "comparability_counts",
        "comparisons_possible",
    ):
        report[key] = cycle[key]
    report["summary"] = {
        **report["summary"],
        "reliable_purchase_unit_prices": cycle["summary"]["verified_purchase_unit_prices"],
        "comparisons_possible": cycle["comparisons_possible"],
        "signals_generated": len(cycle["signals"]),
    }
    report["signal_status"] = "signals_supported" if cycle["signals"] else "insufficient_evidence"
    report["signal_reason"] = (
        "Comparación posterior a reconstrucción por producto y etapa: contrato, "
        "adjudicación u oferta aceptada verificable. Presupuestos, referencias y "
        "ofertas no aceptadas solo son contexto."
    )
    (directory / "research-cycle-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.publish:
        ResearchReportStore(Settings().local_storage_path.parent / "investigation").write(report)
    print(
        json.dumps(
            {
                "summary": cycle["summary"],
                "comparability_counts": cycle["comparability_counts"],
                "comparisons_possible": cycle["comparisons_possible"],
                "signals": len(cycle["signals"]),
                "published": args.publish,
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
