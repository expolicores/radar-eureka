"""EN-01 inventory-only batch for explicitly approved SECOP II processes (no downloads).

plan       offline: take named identities from a window re-evaluation of a stored run, verify
           they are eligible, SECOP II, uniquely identified, with complete inventory keys and
           never inventoried before; bind them and the budget to a digest.
preflight  real but passive: a temporary tab of the dedicated Edge, the app's own feed request
           blocked, only categories recorded (session, single configured profile).
run        real (needs authorization): requires the approved digest and a recent satisfactory
           preflight; one bootstrap (GET get-config-user) and the existing paginated inventory
           endpoint per process. No feed, discovery, download, stream or POST to SECOP.

Output is a run directory shaped like the runner's (processes.json, documents.json), so the
targeted plan can later select governing documents from it.
"""

import argparse
import hashlib
import json
import os
import time
from datetime import UTC, datetime, timedelta

from eureka_nacional_experience import document_priority, document_role, document_role_hint

PREFIX = "en01-inv_"
PLAN_FILE = "inventory_plan.json"
PREFLIGHT_FILE = "preflight.json"
ATTEMPTS_FILE = "inventory_attempts.json"
INVENTORY_KEYS = ("idContrato", "id_fuente_contract", "idUltimaFase")
MAX_PROCESSES = 10
INVENTORY_PAGE_LIMIT = 10  # existing fetch_inventory ceiling per process
CREDIT_LIMIT = 30
DURATION_SECONDS = 360
PREFLIGHT_MAX_AGE = timedelta(minutes=15)
BUDGET_STOPS = frozenset({"request_budget", "duration_budget"})
SESSION_STOPS = frozenset({"session_expired", "invalid_tab"})


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def write_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def digest(plan):
    core = {
        "source_run": plan["source_run"],
        "limits": plan["limits"],
        "items": sorted(
            [
                i["source_identity"],
                i["process_reference"],
                *[str(i["keys"][k]) for k in INVENTORY_KEYS],
            ]
            for i in plan["items"]
        ),
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def inventoried_identities(root, *, exclude=()):
    """Identities that already have an inventory in any stored run."""
    found = set()
    for path in sorted(root.glob("en01-*/documents.json")):
        if path.parent.name in exclude:
            continue
        references = {c["process_reference"] for c in read_json(path, []) if c.get("documents")}
        processes = read_json(path.parent / "processes.json", {}) or {}
        for process in processes.get("processes", []):
            if process["process_reference"] in references and process.get("source_identity"):
                found.add(process["source_identity"])
    return found


def prior_inventory_attempts(root, identity):
    """Attempts recorded for this identity in earlier inventory batches."""
    found = []
    for plan_path in sorted(root.glob(f"{PREFIX}*/{PLAN_FILE}")):
        plan = read_json(plan_path) or {}
        attempts = (read_json(plan_path.parent / ATTEMPTS_FILE) or {}).get("items", {})
        for item in plan.get("items", []):
            record = attempts.get(item["process_reference"])
            if item["source_identity"] == identity and record is not None:
                found.append(
                    {
                        "run": plan_path.parent.name,
                        "batch_sha256": plan.get("batch_sha256"),
                        **{
                            k: record.get(k)
                            for k in ("outcome", "error", "error_detail", "credits")
                        },
                    }
                )
    return found


def build_plan(
    root,
    source_run,
    recent_days,
    identities,
    *,
    credit_limit=CREDIT_LIMIT,
    duration_seconds=DURATION_SECONDS,
    suffix=None,
):
    if not 1 <= credit_limit <= CREDIT_LIMIT or not 30 <= duration_seconds <= DURATION_SECONDS:
        raise ValueError("Limites fuera del maximo autorizado (30 creditos, 360 s).")
    if suffix is not None and not (suffix.isalnum() and suffix == suffix.lower()):
        raise ValueError("Sufijo invalido.")
    source = root / source_run
    evaluation = read_json(source / f"window_reevaluation_{recent_days}d.json")
    if evaluation is None:
        raise ValueError("Falta la reevaluacion de ventana para la corrida.")
    if not 1 <= len(identities) <= MAX_PROCESSES or len(set(identities)) != len(identities):
        raise ValueError("Identidades vacias, repetidas o por encima del maximo.")
    stored = {}
    for process in read_json(source / "processes.json")["processes"]:
        stored.setdefault(process.get("source_identity"), []).append(process)
    rows = {r["source_identity"]: r for r in evaluation["rows"]}
    inventoried = inventoried_identities(root)
    items = []
    for identity in identities:
        row, matches = rows.get(identity), stored.get(identity, [])
        if row is None or len(matches) != 1:
            raise ValueError(f"Identidad no unica o ausente: {identity}")
        process = matches[0]
        if row["excluded_reason"] or row["source"] != "secop2":
            raise ValueError(f"Proceso no elegible o fuera de SECOP II: {identity}")
        if identity in inventoried:
            raise ValueError(f"Proceso ya inventariado: {identity}")
        keys = process.get("inventory_keys") or {}
        if not all(keys.get(k) for k in INVENTORY_KEYS) or not process.get("inventory_capable"):
            raise ValueError(f"Claves de inventario incompletas: {identity}")
        items.append(
            {
                "source_identity": identity,
                "process_reference": process["process_reference"],
                "keys": {k: keys[k] for k in INVENTORY_KEYS},
                "entity": process.get("entity_name"),
                "department": process.get("department"),
                "commercial_priority": row["commercial_priority"],
                "validity_status": row["validity_status"],
                "deadline_at": process.get("deadline_at"),
                "object": process.get("object"),
            }
        )
    plan = {
        "source_run": source_run,
        "recent_days": recent_days,
        "limits": {
            "processes": len(items),
            "credit_limit": credit_limit,
            "duration_seconds": duration_seconds,
            "inventory_pages_per_process": INVENTORY_PAGE_LIMIT,
            "bootstrap_requests": 1,
            "downloads": 0,
            "feed_requests": 0,
        },
        "items": items,
        "network_requests": 0,
    }
    plan["suffix"] = suffix
    plan["prior_attempts"] = {i: prior_inventory_attempts(root, i) for i in identities}
    plan["batch_sha256"] = digest(plan)
    plan["budget"] = {
        "expected_credits": 1 + 2 * len(items),
        "worst_case_credits": 1 + INVENTORY_PAGE_LIMIT * len(items),
        "hard_credit_limit": credit_limit,
        "note": "Cada pagina del inventario cuesta un credito; un inventario corto usa dos "
        "(la pagina con documentos y la pagina vacia que lo cierra). El limite duro corta la "
        "corrida antes del peor caso y deja los procesos restantes registrados como pendientes.",
    }
    return plan


def write_plan(root, plan):
    name = f"{PREFIX}{plan['source_run'][5:]}" + (
        f"_{plan['suffix']}" if plan.get("suffix") else ""
    )
    target = root / name
    target.mkdir(exist_ok=False)
    write_json(target / PLAN_FILE, {**plan, "created_at": datetime.now(UTC).isoformat()})
    return target


def load_plan(target, expected_sha256):
    plan = read_json(target / PLAN_FILE)
    if plan is None or plan["batch_sha256"] != expected_sha256 or digest(plan) != expected_sha256:
        raise ValueError("Plan alterado o distinto del lote aprobado.")
    return plan


def preflight_ok(target, now=None):
    record = read_json(target / PREFLIGHT_FILE)
    if record is None:
        return False, "preflight_missing"
    verdict = record.get("verdict") or {}
    age = (now or datetime.now(UTC)) - datetime.fromisoformat(record["recorded_at"])
    if age > PREFLIGHT_MAX_AGE:
        return False, "preflight_stale"
    if not (
        verdict.get("session") == "valid"
        and verdict.get("profile") == "only_configured"
        and verdict.get("profile_count") == 1
        and record.get("feed_requests_forwarded") == 0
        and all((record.get("dedicated_browser") or {}).values())
    ):
        return False, "preflight_not_satisfactory"
    return True, None


def document_entry(document):
    role = document_role(document.original_name)
    return {
        "document_id": document.document_id,
        "name": document.original_name,
        "url": document.source_url,
        "extension": document.extension,
        "role": role,
        "role_hint": document_role_hint(document.original_name, role),
        "role_source": "filename",
        "status": "not_selected",
        "selection": "inventory_only",
        "complete": False,
    }


def run_inventories(target, expected_sha256, client, fetch_inventory, *, safe_url=lambda u: u):
    """Inventory every approved process once; stop cleanly on budget or session errors."""
    plan = load_plan(target, expected_sha256)
    ok, reason = preflight_ok(target)
    if not ok:
        raise ValueError(f"Preflight no valido: {reason}")
    if (target / ATTEMPTS_FILE).exists():
        raise ValueError("El lote ya se ejecuto; no se repite.")
    attempts = {"batch_sha256": plan["batch_sha256"], "items": {}}
    write_json(target / ATTEMPTS_FILE, attempts)
    source = target.parent / plan["source_run"]
    stored = {p["process_reference"]: p for p in read_json(source / "processes.json")["processes"]}
    processes, inventories, stop = [], [], None
    client.bootstrap()
    for item in plan["items"]:
        reference = item["process_reference"]
        record = {"started_at": datetime.now(UTC).isoformat()}
        attempts["items"][reference] = record
        write_json(target / ATTEMPTS_FILE, attempts)
        before = client.requests
        try:
            documents = fetch_inventory(client, item["keys"])
            entries = [document_entry(d) for d in documents]
            for entry in entries:
                entry["url"] = safe_url(entry["url"])
            record.update(outcome="inventoried", documents=len(entries))
        except Exception as error:
            # Budget errors carry their reason as message; session errors carry a code.
            budget = str(error) if str(error) in BUDGET_STOPS else None
            code = budget or getattr(error, "code", None) or type(error).__name__
            # Our own inventory messages (repeated page, page limit, missing keys) are safe.
            record.update(outcome="failed", error=code, error_detail=str(error)[:200])
            entries = []
            if code in BUDGET_STOPS | SESSION_STOPS:
                stop = code
        record["credits"] = client.requests - before
        processes.append({**stored[reference], "sampled": True, "inventory_batch": True})
        inventories.append({"process_reference": reference, "documents": entries})
        write_json(target / ATTEMPTS_FILE, attempts)
        if stop:
            break
    pending = [
        i["source_identity"]
        for i in plan["items"]
        if i["process_reference"] not in attempts["items"]
    ]
    write_json(
        target / "processes.json",
        {"scope": "inventory_batch", "source_run": plan["source_run"], "processes": processes},
    )
    write_json(target / "documents.json", inventories)
    summary = {
        "batch_sha256": plan["batch_sha256"],
        "credits_used": client.requests,
        "stop_reason": stop,
        "inventoried": sum(r.get("outcome") == "inventoried" for r in attempts["items"].values()),
        "failed": sum(r.get("outcome") == "failed" for r in attempts["items"].values()),
        "pending": pending,
        "downloads": 0,
        "feed_requests": 0,
    }
    write_json(target / "inventory_summary.json", summary)
    return summary


def proposed_tranches(target, per_process=2):
    """Offline: governing documents and studies first; administrative support never chosen."""
    plan = read_json(target / PLAN_FILE)
    items = {i["process_reference"]: i for i in plan["items"]}
    proposals = []
    for case in read_json(target / "documents.json", []):
        docs = [
            d
            for d in case["documents"]
            if d["extension"] == "pdf"
            and d["role"] in {"primary", "amendment", "support", "unknown"}
        ]
        docs.sort(key=lambda d: document_priority(d["name"], d["role"], d["role_hint"]))
        chosen = [
            d for d in docs if document_priority(d["name"], d["role"], d["role_hint"])[0] <= 4
        ]
        item = items[case["process_reference"]]
        proposals.append(
            {
                "source_identity": item["source_identity"],
                "commercial_priority": item["commercial_priority"],
                "deadline_at": item["deadline_at"],
                "documents": [
                    {"document_id": d["document_id"], "name": d["name"], "role": d["role"]}
                    for d in chosen[:per_process]
                ],
            }
        )
    order = {"A": 0, "B": 1, "C": 2}
    proposals.sort(
        key=lambda p: (order.get(p["commercial_priority"], 9), p["deadline_at"] or "9999")
    )
    return proposals


def main(argv=None):
    import eureka_nacional_en01 as runner

    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("source_run")
    p_plan.add_argument("--recent-days", type=int, required=True)
    p_plan.add_argument("--identity", action="append", required=True)
    p_plan.add_argument("--credit-limit", type=int, default=CREDIT_LIMIT)
    p_plan.add_argument("--duration-seconds", type=int, default=DURATION_SECONDS)
    p_plan.add_argument("--suffix")
    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("target_run")
    p_run = sub.add_parser("run")
    p_run.add_argument("target_run")
    p_run.add_argument("--expect-sha256", required=True)
    args = parser.parse_args(argv)
    root = runner.OUTPUT_ROOT
    try:
        if args.command == "plan":
            plan = build_plan(
                root,
                args.source_run,
                args.recent_days,
                args.identity,
                credit_limit=args.credit_limit,
                duration_seconds=args.duration_seconds,
                suffix=args.suffix,
            )
            target = write_plan(root, plan)
            print(
                json.dumps(
                    {
                        "target": target.name,
                        "batch_sha256": plan["batch_sha256"],
                        "budget": plan["budget"],
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        target = root / args.target_run
        if not args.target_run.startswith(PREFIX) or target.resolve() != target:
            raise ValueError("Corrida de inventario invalida.")
        if (root / runner.streaming.MARKER_NAME).exists():
            raise ValueError("Marcador preventivo presente.")
        if args.command == "preflight":
            from eureka_nacional_profile_preflight import passive_profile_check

            record = passive_profile_check()
            record["recorded_at"] = datetime.now(UTC).isoformat()
            write_json(target / PREFLIGHT_FILE, record)
            print(json.dumps(record, ensure_ascii=False))
            return 0
        from playwright.sync_api import sync_playwright

        profile_id = runner.resolve_profile_id(None)
        limits = load_plan(target, args.expect_sha256)["limits"]
        deadline = time.monotonic() + limits["duration_seconds"]
        with sync_playwright() as playwright:
            browser = runner.connect_browser(playwright, "http://127.0.0.1:9232")
            client = runner.SmokeClient(
                runner.find_page(browser),
                profile_id,
                deadline,
                request_limit=limits["credit_limit"],
            )
            summary = run_inventories(
                target,
                args.expect_sha256,
                client,
                runner.fetch_inventory,
                safe_url=lambda url: runner.safe_public_url(url, "DocumentId"),
            )
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    except ValueError as error:
        print(f"EN-01: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
