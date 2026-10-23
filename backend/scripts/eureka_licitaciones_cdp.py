"""Experimental CDP discovery -> documents -> shared extraction; local files only."""

import argparse
import importlib.util
import json
import subprocess
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path

import spike_licitaciones_info as spike
from licitaciones_candidate_contracts import (
    CONTRACT_VERSION,
    CandidateProcess,
    deduplicate_facts,
    document_contract,
    fact_contract,
)
from licitaciones_cdp_runtime import (
    IDS_FILE,
    LOCAL,
    MANUAL_LOGIN,
    POLICY_PATH,
    CandidateError,
    PageClient,
    annotate_facts,
    check_session,
    connect_browser,
    coverage,
    fetch_inventory,
    filter_processes,
    find_page,
    load_payload,
    summarize_run,
    validate_cdp_url,
    validate_discovery,
    write_json,
)
from licitaciones_freshness import (
    DEFAULT_RECENT_DAYS,
    apply_freshness,
    local_now,
    validate_recent_days,
)
from licitaciones_search_plan import DEFAULT_PLAN, load_plan, run_plan
from licitaciones_sources import document_capable, process_identity
from licitaciones_validity import apply_validity


def check_ocr(settings):
    if not settings.extraction_ocr_enabled:
        raise spike.SpikeError("Activa OCR local en .env; esta prueba requiere Tesseract real spa.")
    policy = spike.load_ocr_policy(settings.extraction_ocr_config_path)
    if policy.language != "spa":
        raise spike.SpikeError("La politica OCR debe usar spa para este experimento.")
    for dependency in ("pypdfium2", "PIL", "pytesseract"):
        if importlib.util.find_spec(dependency) is None:
            raise spike.SpikeError("Falta una dependencia OCR local: " + dependency)
    command = settings.extraction_tesseract_cmd or "tesseract"
    try:
        version = subprocess.run(  # noqa: S603 -- configured local executable; no shell
            [command, "--version"], capture_output=True, text=True, check=True, timeout=10
        ).stdout.splitlines()[0]
        args = [command]
        if settings.extraction_tessdata_path:
            args.extend(["--tessdata-dir", str(settings.extraction_tessdata_path)])
        result = subprocess.run(  # noqa: S603
            [*args, "--list-langs"], capture_output=True, text=True, check=True, timeout=10
        )
        if "spa" not in result.stdout.splitlines():
            raise spike.SpikeError("Tesseract no tiene spa disponible.")
    except (OSError, subprocess.SubprocessError, IndexError) as error:
        raise spike.SpikeError(
            "Tesseract real no esta disponible; revisa la configuracion local."
        ) from error
    return {
        "engine": "tesseract",
        "version": version,
        "language": "spa",
        "policy_version": policy.version,
    }


def run(page, args, settings, output, ocr, *, now=None):
    discovery, documents, extraction = {}, [], []
    errors, warnings = [], []
    status = "running"
    client = None
    discovery_only = getattr(args, "discovery_only", False)
    now = now or local_now()
    recent_days = validate_recent_days(getattr(args, "recent_days", DEFAULT_RECENT_DAYS))
    freshness_metrics = {}

    def save():
        write_json(output / "discovery.json", discovery)
        if not discovery_only:
            write_json(output / "documents.json", documents)
            write_json(output / "extraction.json", extraction)
        write_json(
            output / "run_summary.json",
            {
                "status": status,
                "experimental": True,
                "contract_version": CONTRACT_VERSION,
                "mode": "discovery_only" if discovery_only else "full",
                "ocr": ocr,
                "recent_days": recent_days,
                "freshness_evaluated_at": now.isoformat(),
                "validity_evaluated_at": now.isoformat(),
                "freshness_timezone": "America/Bogota (UTC-05:00)",
                "limits": {
                    "processes": args.max_processes,
                    "document_processes": args.max_document_processes,
                    "documents_per_process": args.max_documents,
                },
                "request_budget_used": client.requests if client else 0,
                **summarize_run(discovery, documents, extraction, errors, warnings),
                **freshness_metrics,
            },
        )

    def event(data):
        # Known metadata only. Never print request headers, response config or exceptions.
        print(json.dumps(data, ensure_ascii=True), flush=True)

    client = PageClient(page, args.profile_id, event)
    save()
    try:
        payload = load_payload(args.location_ids_file, args.term, args.max_processes)
        bootstrap = check_session(client, args.profile_id, aggregator=True)
        warnings.extend(
            {"stage": "preflight", **warning} for warning in bootstrap.get("warnings", [])
        )
        event({"stage": "preflight", "status": "healthy", "profile_id": args.profile_id})
        path = f"/cliente/contratos/get-info/MP?perfiles={args.profile_id}"
        body = client.post(path, payload)
        rows = validate_discovery(body, args.max_processes, validate_dates=False)
        eligible, excluded = filter_processes(rows, args.term)
        candidates = {
            str(row["idContrato"]): CandidateProcess.from_source(row, args.profile_id)
            for row in rows
        }
        scoped = {
            str(row["idContrato"]): candidates[str(row["idContrato"])].to_dict()
            for row in rows
            if spike.normalized(row["TextoDepartamento"]).split(":")[0].strip() == "boyaca"
            and spike.normalized(args.term) in spike.normalized(row["Objeto"])
        }
        processes, freshness_metrics, freshness_warnings = apply_freshness(
            list(scoped.values()), recent_days, now
        )
        warnings.extend(freshness_warnings)
        processes, validity_metrics, validity_warnings = apply_validity(processes, now)
        freshness_metrics.update(validity_metrics)
        warnings.extend(validity_warnings)
        fresh_index = {p["id_contrato"]: p for p in processes}
        eligible_total = [fresh_index[str(row["idContrato"])] for row in eligible]
        eligible_recent = [p for p in eligible_total if p["recent"]]
        eligible = [
            row
            for row in eligible
            if fresh_index[str(row["idContrato"])]["recent"]
            and fresh_index[str(row["idContrato"])]["validity_status"] == "open"
        ]
        discovery.update(
            contract_version=CONTRACT_VERSION,
            host="col.licitaciones.info",
            endpoint=path,
            payload=payload,
            count=body.get("count"),
            bootstrap=bootstrap,
            enriched_discovery_verified=bool(rows),
            recent_days=recent_days,
            freshness_evaluated_at=now.isoformat(),
            validity_evaluated_at=now.isoformat(),
            processes=processes,
            eligible_total=eligible_total,
            eligible_recent=eligible_recent,
            eligible=[fresh_index[str(row["idContrato"])] for row in eligible],
            excluded=excluded,
        )
        event(
            {
                "stage": "discovery",
                "count": body.get("count"),
                "received": len(rows),
                "eligible_secop_ii": len(eligible),
                **freshness_metrics,
            }
        )
        if not rows:
            warnings.append(
                {"stage": "bootstrap", "code": "empty_filtered_result_enrichment_not_verified"}
            )
        save()
        if discovery_only:
            status = "completed_with_warnings" if warnings else "completed"
            save()
            event(
                {
                    "stage": "summary",
                    "status": status,
                    "eligible_secop_ii": len(eligible),
                    **freshness_metrics,
                }
            )
            return 0
        storage = spike.LocalBinaryStorage(output / "binaries")
        fact_policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        for process in eligible[: args.max_document_processes]:
            candidate = candidates[str(process["idContrato"])]
            if not document_capable(candidate.to_dict()):
                warnings.append({"code": "metadata_only", "process_reference": candidate.reference})
                continue
            document_entry = {
                "process": fresh_index[candidate.id_contrato],
                "inventory": [],
                "downloads": [],
            }
            extraction_entry = {
                "process_reference": candidate.reference,
                "documents": [],
                "facts": [],
            }
            documents.append(document_entry)
            extraction.append(extraction_entry)
            evidence, incomplete, version_documents = [], set(), {}
            try:
                inventory = fetch_inventory(
                    client,
                    {
                        **process,
                        "idUltimaFase": process.get("idUltimaFase")
                        or process_identity(candidate.to_dict()),
                    },
                )
                document_entry["inventory"] = [
                    document_contract(candidate, doc, spike.normalized) for doc in inventory
                ]
                document_index = {
                    doc["secop_document_id"]: doc for doc in document_entry["inventory"]
                }
                document_entry["inventory_complete"] = True
                selected = spike.select_documents(inventory, args.max_documents)
                document_entry["selected"] = [doc.document_id for doc in selected]
                event(
                    {
                        "stage": "documents",
                        "process_reference": candidate.reference,
                        "inventory": len(inventory),
                        "selected": len(selected),
                    }
                )
                if not selected:
                    warnings.append(
                        {
                            "stage": "selection",
                            "process_id": process["idContrato"],
                            "code": "no_priority_documents",
                        }
                    )
                save()
                for document in selected:
                    contract = document_index[document.document_id]
                    contract["extraction_status"] = "pending"
                    stage = "download"
                    try:
                        stored = spike.download_document(client, document, storage, settings)
                        document_entry["downloads"].append(
                            {
                                "document_id": document.document_id,
                                "document_reference": contract["document_reference"],
                                "name": document.original_name,
                                "http_status": 200,
                                **asdict(stored),
                            }
                        )
                        stage = "extraction"
                        save()
                        detail, fragments = spike.run_existing_extractor(
                            document, stored, storage, settings
                        )
                        detail.update(coverage(detail))
                        contract.update(
                            document_contract(candidate, document, spike.normalized, detail)
                        )
                        detail.update(contract)
                        extraction_entry["documents"].append(detail)
                        for fragment in fragments:
                            version_documents[str(fragment.document_version_id)] = detail
                        evidence.extend(fragments)
                        if not detail["coverage_complete"]:
                            incomplete.update(str(f.document_version_id) for f in fragments)
                            warnings.append(
                                {
                                    "stage": "extraction",
                                    "document_id": document.document_id,
                                    "code": detail["extraction_status"],
                                    "coverage_ratio": detail["coverage_ratio"],
                                }
                            )
                        event(
                            {
                                "stage": "extraction",
                                "name": detail["name"],
                                "mode": detail["extraction_mode"],
                                "status": detail["extraction_status"],
                                "text_length": detail["text_length"],
                            }
                        )
                        save()
                    except CandidateError:
                        raise
                    except Exception as error:
                        contract["extraction_status"] = stage + "_failed"
                        contract["warnings"].append(stage + "_failed")
                        errors.append(
                            {
                                "stage": stage,
                                "process_id": process["idContrato"],
                                "document_id": document.document_id,
                                "type": type(error).__name__,
                                "code": getattr(error, "code", None),
                            }
                        )
                        save()
            except CandidateError:
                raise
            except Exception as error:
                document_entry["inventory_complete"] = False
                errors.append(
                    {
                        "stage": "inventory",
                        "process_id": process["idContrato"],
                        "type": type(error).__name__,
                        "code": getattr(error, "code", None),
                    }
                )
            facts = spike.summarize_result(uuid.uuid4(), evidence)["structured_facts"]
            extraction_entry["raw_fact_count"] = len(facts)
            annotated = annotate_facts(facts, incomplete, fact_policy)
            contracts = []
            for fact in annotated:
                document = version_documents[str(fact["document_version_id"])]
                contracts.append(fact_contract(candidate, fact, document))
            extraction_entry["facts"] = deduplicate_facts(contracts)
            save()
        status = "completed_with_warnings" if errors or warnings else "completed"
        save()
        event(
            {
                "stage": "summary",
                "status": status,
                **{
                    key: value
                    for key, value in summarize_run(
                        discovery, documents, extraction, errors, warnings
                    ).items()
                    if key not in ("errors", "warnings")
                },
                **freshness_metrics,
            }
        )
        return 0 if not errors else 2
    except Exception as error:
        status = "failed"
        errors.append(
            {
                "stage": "run",
                "type": type(error).__name__,
                "code": getattr(error, "code", "unexpected_error"),
            }
        )
        save()
        if isinstance(error, CandidateError):
            print(f"{error.code}: {error}")
            return error.exit_code
        print("Flujo detenido: " + type(error).__name__ + ". Revisa el resumen local.")
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=["boyaca"], default="boyaca")
    parser.add_argument("--object", dest="term", default="refrigerio")
    parser.add_argument("--profile-id", choices=["1086005"], default="1086005")
    parser.add_argument("--max-processes", type=int, choices=range(1, 31), default=30)
    parser.add_argument("--max-document-processes", type=int, choices=range(1, 4), default=3)
    parser.add_argument("--max-documents", type=int, choices=range(1, 3), default=2)
    parser.add_argument("--location-ids-file", type=Path, default=IDS_FILE)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--check-session",
        action="store_true",
        help="Sondeo de salud; sin discovery comercial, archivos ni OCR.",
    )
    modes.add_argument(
        "--discovery-only",
        action="store_true",
        help="Discovery y JSON local; sin documentos, descargas ni OCR.",
    )
    modes.add_argument(
        "--discovery-plan-only",
        action="store_true",
        help="Plan secuencial de hasta seis busquedas; sin documentos ni OCR.",
    )
    parser.add_argument("--search-plan", type=Path, help="Archivo declarativo de discovery.")
    parser.add_argument(
        "--recent-days", type=int, help="Ventana local de frescura; default configurable: 7 dias."
    )
    parser.add_argument(
        "--diagnose-preflight",
        action="store_true",
        help="Con --check-session, guardar diagnostico publico local sin cambiar validacion.",
    )
    args = parser.parse_args(argv)
    if args.diagnose_preflight and not args.check_session:
        parser.error("--diagnose-preflight requiere --check-session")
    if args.search_plan and not args.discovery_plan_only:
        parser.error("--search-plan requiere --discovery-plan-only")
    if args.recent_days is not None and args.recent_days < 1:
        parser.error("--recent-days debe ser un entero positivo")
    try:
        validate_cdp_url(args.cdp_url)
        settings, ocr = None, None
        plan = load_plan(args.search_plan or DEFAULT_PLAN) if args.discovery_plan_only else None
        if not args.check_session:
            defaults = (
                plan if plan is not None else json.loads(DEFAULT_PLAN.read_text(encoding="utf-8"))
            )
            args.recent_days = validate_recent_days(
                args.recent_days
                if args.recent_days is not None
                else defaults.get("default_recent_days", DEFAULT_RECENT_DAYS)
            )
        if not args.check_session and not args.discovery_plan_only:
            load_payload(args.location_ids_file, args.term, args.max_processes)
        if not args.check_session and not args.discovery_only and not args.discovery_plan_only:
            settings = spike.Settings(
                _env_file=spike.ROOT / ".env", database_url="disabled://no-db"
            )
            ocr = check_ocr(settings)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = connect_browser(playwright, args.cdp_url)
            page = find_page(browser)
            if args.check_session:
                client = PageClient(page, args.profile_id, lambda item: print(json.dumps(item)))
                try:
                    health = check_session(client, args.profile_id, aggregator=True)
                finally:
                    if args.diagnose_preflight:
                        LOCAL.mkdir(parents=True, exist_ok=True)
                        diagnostic_path = (
                            LOCAL / f"preflight-diagnostic-{uuid.uuid4().hex[:12]}.json"
                        )
                        diagnostic = client.last_get_info_diagnostic or {
                            "get_info_not_reached": True
                        }
                        write_json(diagnostic_path, diagnostic)
                        print("DIAGNOSTIC=" + str(diagnostic_path))
                print(
                    json.dumps(
                        {"stage": "preflight", "status": "healthy", **health}, ensure_ascii=True
                    )
                )
                return 0
            LOCAL.mkdir(parents=True, exist_ok=True)
            output = Path(tempfile.mkdtemp(prefix="experimental-cdp-", dir=LOCAL))
            print("OUTPUT=" + str(output), flush=True)
            if args.discovery_plan_only:

                def event(item):
                    print(json.dumps(item, ensure_ascii=True), flush=True)

                return run_plan(
                    PageClient(page, args.profile_id, event),
                    plan,
                    output,
                    lambda seconds: page.wait_for_timeout(seconds * 1000),
                    event,
                    recent_days=args.recent_days,
                )
            # Exiting Playwright disconnects; never browser.close() on the user's Edge.
            return run(page, args, settings, output, ocr)
    except CandidateError as error:
        print(f"{error.code}: {error}")
        return error.exit_code
    except spike.SpikeError as error:
        print(str(error))
    except Exception as error:
        print("No se pudo iniciar el experimento: " + type(error).__name__ + ". " + MANUAL_LOGIN)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
