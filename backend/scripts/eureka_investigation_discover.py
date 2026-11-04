"""Controlled Socrata research discovery and documentary selection. No Radar/CDP."""

import argparse
import json
import re
import time
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from public_procurement.documents.adapters.socrata import SocrataDocumentSource
from public_procurement.ingestion.adapters.socrata_processes import FIELDS, SocrataProcessSource
from public_procurement.investigation.economic_cycle import classify_stage
from public_procurement.shared.text import normalize_text

TERMS = (
    "TELEVISOR",
    "TECNOLOG",
    "AUDIOVISUAL",
    "ELECTRONIC",
    "DOTACI",
    "MOBILIARIO",
    "EQUIPAMIENTO",
    "SUMINISTROS INSTITUCIONALES",
    "ELEMENTOS EDUCATIVOS",
)
MATURE = {"seleccionado", "adjudicado", "cerrado", "contratado", "finalizado", "celebrado"}


def rank(row: dict[str, Any], known: set[str]) -> tuple[int, list[str]]:
    text = normalize_text(
        (row.get("nombre_del_procedimiento") or "")
        + " "
        + (row.get("descripci_n_del_procedimiento") or "")
    )
    score, reasons = 0, []
    for points, reason, matches in (
        (
            120,
            "explicit_tv_metadata_not_confirmation",
            bool(re.search(r"\btelevisor|\bsmart\s*tv", text)),
        ),
        (40, "priority_55_65", bool(re.search(r"(?:55|65)\s*(?:pulg|[\"“”″])", text))),
        (
            60,
            "tv_unspsc_hint",
            any(
                c in str(row.get("codigo_principal_de_categoria"))
                for c in ("521615", "521600", "432119")
            ),
        ),
        (30, "existing_documentary_tv", row["id_del_proceso"] in known),
        (25, "purchase_supply", bool(re.search(r"adquisic|compra|suministr", text))),
        (25, "technology_audiovisual", bool(re.search(r"audiovisual|tecnolog|electronico", text))),
        (
            15,
            "institutional_educational_equipment",
            bool(re.search(r"dotacion|equipamiento|mobiliario|educativ", text)),
        ),
        (
            -120,
            "service_maintenance",
            bool(re.search(r"mantenimiento|reparacion|arrendamiento", text))
            and not re.search(r"adquisic|compra", text),
        ),
        (
            -60,
            "non_physical_scope",
            bool(re.search(r"servicios profesionales|software|licencia|apoyo a la gestion", text)),
        ),
    ):
        if matches:
            score += points
            reasons.append(reason)
    return score, reasons


def choose_documents(documents: list[dict[str, Any]], maximum: int) -> list[dict[str, Any]]:
    priority = {
        "contract": 100,
        "award": 90,
        "evaluation_report": 80,
        "economic_offer": 75,
        "technical_specification": 70,
        "studies_previous": 65,
        "invitation": 60,
    }
    ranked = []
    for doc in documents:
        name = normalize_text(doc["original_name"])
        if re.search(r"cedula|certificacion bancaria|hoja de vida|antecedentes|\brut\b", name):
            continue
        stage = classify_stage(doc["original_name"])[0]
        if stage not in priority:
            continue
        points = priority[stage] + (5 if "firmado" in name else 0)
        ranked.append((points, str(doc.get("fecha_carga") or ""), doc))
    ranked.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
    selected, names, per_stage = [], set(), {}
    for _, _, doc in ranked:
        stage = classify_stage(doc["original_name"])[0]
        name = normalize_text(doc["original_name"])
        if name in names or per_stage.get(stage, 0) >= (3 if stage == "economic_offer" else 2):
            continue
        selected.append(doc)
        names.add(name)
        per_stage[stage] = per_stage.get(stage, 0) + 1
        if len(selected) == maximum:
            break
    return selected


def dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-directory", type=Path, required=True)
    parser.add_argument("--before", type=date.fromisoformat, required=True)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--max-processes", type=int, default=48)
    parser.add_argument("--max-documents", type=int, default=10)
    parser.add_argument("--reuse-directory", type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if (
        not 1 <= args.days <= 60
        or not 1 <= args.max_processes <= 80
        or not 1 <= args.max_documents <= 16
    ):
        raise ValueError("Controlled research bounds exceeded")
    out = args.sample_directory
    out.mkdir(parents=True, exist_ok=True)
    reuse = args.reuse_directory
    previous = (
        json.loads((reuse / "research-report.json").read_text(encoding="utf8")) if reuse else {}
    )
    known = {p["id"] for p in previous.get("processes", []) if p.get("tv_confirmed")}
    discovery_path = out / "discovery.json"
    if discovery_path.exists():
        discovery = json.loads(discovery_path.read_text(encoding="utf8"))
        if discovery["window_before"] != str(args.before) or discovery["days"] != args.days:
            raise ValueError("Existing discovery belongs to a different window")
    else:
        start = args.before - timedelta(days=args.days)
        expressions = [
            f"upper({f}) like '%{t}%'"
            for t in TERMS
            for f in ("nombre_del_procedimiento", "descripci_n_del_procedimiento")
        ]
        expressions += [
            f"codigo_principal_de_categoria like '%{c}%'" for c in ("521615", "521600", "432119")
        ]
        where = (
            f"fecha_de_publicacion_del >= '{start}' "
            f"AND fecha_de_publicacion_del < '{args.before}' AND (" + " OR ".join(expressions) + ")"
        )
        source = SocrataProcessSource()
        counts = source._page(
            {
                "$select": "estado_del_procedimiento,count(*) as source_rows",
                "$where": where,
                "$group": "estado_del_procedimiento",
                "$limit": "100",
            }
        )
        print("SOURCE_COUNTS", json.dumps(counts), flush=True)
        rows = []
        for page in range(50):
            batch = source._page(
                {
                    "$select": "distinct " + ",".join(FIELDS),
                    "$where": where,
                    "$order": "id_del_proceso ASC",
                    "$limit": "1000",
                    "$offset": str(page * 1000),
                }
            )
            rows.extend(batch)
            dump(out / "discovery-progress.json", {"pages": page + 1, "rows": rows})
            print("PAGE", page + 1, len(batch), flush=True)
            if len(batch) < 1000:
                break
            time.sleep(1)
        else:
            raise ValueError("Discovery truncated")
        unique, conflicts = {}, set()
        for row in rows:
            identity = row["id_del_proceso"]
            if identity in unique and unique[identity] != row:
                conflicts.add(identity)
            unique[identity] = row
        discovery = {
            "source": "socrata_secop",
            "window_start": str(start),
            "window_before": str(args.before),
            "days": args.days,
            "where": where,
            "counts": counts,
            "unique_rows": list(unique.values()),
            "conflicting_identities": sorted(conflicts),
            "pagination_warning": "no_provider_snapshot_offset_pagination",
        }
        dump(discovery_path, discovery)
    mature = [
        r
        for r in discovery["unique_rows"]
        if normalize_text(r.get("estado_del_procedimiento") or "") in MATURE
        and r["id_del_proceso"] not in discovery["conflicting_identities"]
    ]
    ranked = sorted(mature, key=lambda r: (-rank(r, known)[0], str(r["id_del_proceso"])))
    explicit = [r for r in ranked if "explicit_tv_metadata_not_confirmation" in rank(r, known)[1]]
    broad = [r for r in ranked if r not in explicit and rank(r, known)[0] >= 40]
    chosen, entity_counts = [], {}
    # Reserve one quarter for broad objects; never treat the score as documentary truth.
    for pool, maximum in ((explicit, args.max_processes * 3 // 4), (broad, args.max_processes)):
        for row in pool:
            entity = row.get("entidad") or ""
            if len(chosen) >= maximum:
                break
            if entity_counts.get(entity, 0) >= 2:
                continue
            chosen.append(row)
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
    selection = {
        "window_start": discovery["window_start"],
        "window_before": discovery["window_before"],
        "discovered_unique": len(discovery["unique_rows"]),
        "mature_metadata": len(mature),
        "rows": chosen,
        "mature_statuses": sorted({r["estado_del_procedimiento"] for r in chosen}),
        "selection_method": "deterministic_rank_tv_size_55_65_with_broad_quota_not_exhaustive",
        "ranking": [
            {
                "identity": r["id_del_proceso"],
                "score": rank(r, known)[0],
                "reasons": rank(r, known)[1],
            }
            for r in chosen
        ],
        "research_policy": "research-60d-v1",
        "max_documents_per_process": args.max_documents,
    }
    dump(out / "selection.json", selection)
    print(
        "DISCOVERY",
        len(discovery["unique_rows"]),
        "MATURE",
        len(mature),
        "EXPLICIT",
        len(explicit),
        "SELECTED",
        len(chosen),
        flush=True,
    )
    if not args.prepare:
        return
    fields = [
        "proceso_de_compra",
        "id_contrato",
        "referencia_del_contrato",
        "estado_contrato",
        "proveedor_adjudicado",
        "fecha_de_firma",
        "fecha_de_inicio_del_contrato",
        "fecha_de_fin_del_contrato",
        "valor_del_contrato",
        "urlproceso",
        "objeto_del_contrato",
        "descripcion_del_proceso",
    ]
    ids = sorted({r["id_del_portafolio"] for r in chosen if r.get("id_del_portafolio")})
    params = {
        "$select": "distinct " + ",".join(fields),
        "$where": "proceso_de_compra in ("
        + ",".join("'" + i.replace("'", "''") + "'" for i in ids)
        + ")",
        "$limit": "1000",
    }
    with urlopen(
        Request(
            "https://www.datos.gov.co/resource/jbjy-vk9h.json?" + urlencode(params),
            headers={"User-Agent": "PublicProcurement/0.1"},
        ),
        timeout=45,
    ) as response:
        contracts = json.load(response)
    if len(contracts) >= 1000:
        raise ValueError("Contract query truncated")
    dump(
        out / "contracts-by-identity.json",
        {"dataset": "jbjy-vk9h", "params": params, "rows": contracts},
    )
    inventories = (
        json.loads((out / "inventories.json").read_text(encoding="utf8"))
        if (out / "inventories.json").exists()
        else {}
    )
    cached = json.loads((reuse / "inventories.json").read_text(encoding="utf8")) if reuse else {}
    errors, selected_docs, reused_inventories = {}, {}, []
    for row in chosen:
        ref = row["id_del_proceso"]
        try:
            if ref not in inventories:
                if ref in cached:
                    inventories[ref] = cached[ref]
                    reused_inventories.append(ref)
                else:
                    inventories[ref] = [
                        asdict(d) for d in SocrataDocumentSource().fetch(row["id_del_portafolio"])
                    ]
                    time.sleep(1)
            selected_docs[ref] = choose_documents(inventories[ref], args.max_documents)
            print(
                "INVENTORY",
                ref,
                len(inventories[ref]),
                "SELECTED",
                len(selected_docs[ref]),
                flush=True,
            )
        except Exception as exc:
            errors[ref] = type(exc).__name__
            print("INVENTORY_ERROR", ref, type(exc).__name__, flush=True)
        dump(out / "inventories.json", inventories)
        dump(out / "selected-documents.json", selected_docs)
        dump(out / "inventory-errors.json", errors)
    dump(out / "inventory-reuse.json", reused_inventories)


if __name__ == "__main__":
    main()
