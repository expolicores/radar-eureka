"""EN-01: bounded national SECOP II supply sampling with local, deterministic evidence."""

import argparse
import json
import re
import tempfile
import time
from collections import Counter, deque
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import spike_licitaciones_info as spike
from eureka_nacional_commercial import (
    DEFAULT_PROFILE,
    assess_commercial,
    commercial_metrics,
    fraction,
    load_commercial_profile,
    parse_unspsc,
    plain,
    selection_rank,
)
from eureka_nacional_experience import (
    STATUSES,
    classify_experience,
    document_role,
)
from licitaciones_candidate_contracts import CandidateProcess
from licitaciones_cdp_runtime import (
    CandidateError,
    PageClient,
    check_session,
    connect_browser,
    coverage,
    fetch_inventory,
    find_page,
    validate_cdp_url,
    validate_discovery,
    write_json,
)
from licitaciones_freshness import apply_freshness, local_now
from licitaciones_sources import document_capable, process_identity, source_kind
from licitaciones_validity import apply_validity

from public_procurement.documents.domain.document import AcquisitionError
from public_procurement.extraction.adapters.ocr import probe_engine

PROFILE = "1086005"
DISCOVERY_PAGE_SIZE = 30
PAGES_PER_DOCUMENT = 12
OCR_PER_DOCUMENT = 2
REQUEST_CREDITS = 60
DURATION_SECONDS = 360
START_EXTRACTION_MARGIN = 50
DOCUMENT_BYTES = 10 * 1024 * 1024
OUTPUT_ROOT = spike.ROOT.parent / ".local" / "eureka-nacional-spike"
ROLE_ORDER = {"primary": 0, "amendment": 1, "support": 2, "unknown": 3}


class BudgetReached(spike.SpikeError):
    pass


class SmokeClient(PageClient):
    def __init__(self, page, deadline):
        super().__init__(page, PROFILE, lambda _event: None)
        self.deadline = deadline

    def reserve(self, count=1):
        if time.monotonic() + 25 > self.deadline:
            raise BudgetReached("duration_budget")
        if self.requests + count > REQUEST_CREDITS:
            raise BudgetReached("request_budget")
        super().reserve(count)


def safe_public_url(value, identifier):
    try:
        parts = urlsplit(str(value or ""))
        spike.validate_url(str(value or ""))
        match = parse_qs(parts.query).get(identifier, [""])[0]
    except (AcquisitionError, ValueError):
        return None
    query = urlencode({identifier: match}) if re.fullmatch(r"[\w.-]{1,80}", match) else ""
    return urlunsplit(("https", "community.secop.gov.co", parts.path, query, ""))


def discover(client, args, now, discovery, profile):
    candidates = {}
    signatures = set()
    provider_fields = {
        "unspsc_shapes": Counter(),
        "unspsc_rows_parsed": 0,
        "description_rows": 0,
        "modality_rows": 0,
    }
    discovery["provider_fields"] = provider_fields
    try:
        for page in range(1, args.discovery_pages + 1):
            body = client.post(
                f"/cliente/contratos/get-info/MP?perfiles={PROFILE}",
                {
                    "query": {},
                    "limit": DISCOVERY_PAGE_SIZE,
                    "ascending": 0,
                    "page": page,
                    "byColumn": 1,
                    "orderBy": "FechaPublicacion",
                    "columns": spike.COLUMNS,
                },
            )
            rows = validate_discovery(body, DISCOVERY_PAGE_SIZE, validate_dates=False)
            signature = frozenset(str(row["idContrato"]) for row in rows)
            discovery["pages"].append(
                {"page": page, "provider_count": int(body["count"]), "received": len(rows)}
            )
            if signature in signatures:
                discovery["duplicates"] += len(rows)
                discovery["stop_reason"] = "provider_repeated_page"
                break
            signatures.add(signature)
            for row in rows:
                candidate = CandidateProcess.from_source(row, PROFILE)
                process = candidate.to_dict()
                kind = source_kind(process)
                identity = process_identity(process)
                key = identity or candidate.reference
                raw_unspsc = row.get("UNSPSC")
                unspsc = parse_unspsc(raw_unspsc)
                provider_fields["unspsc_shapes"][
                    "missing" if raw_unspsc is None else type(raw_unspsc).__name__
                ] += 1
                provider_fields["unspsc_rows_parsed"] += bool(unspsc)
                description = next(
                    (
                        row[field]
                        for field in ("Descripcion", "Descripci\u00f3n", "DescripcionProceso")
                        if isinstance(row.get(field), str) and row[field].strip()
                    ),
                    "",
                )
                modality = row.get("modalidad") or row.get("Modalidad")
                provider_fields["description_rows"] += bool(description)
                provider_fields["modality_rows"] += isinstance(modality, str) and bool(
                    modality.strip()
                )
                if key in candidates:
                    discovery["duplicates"] += 1
                    existing = candidates[key]
                    existing["unspsc"] = sorted(set(existing["unspsc"]) | set(unspsc))
                    if not existing["description"]:
                        existing["description"] = description
                    continue
                phase = candidate.id_ultima_fase
                if not phase and identity and identity.startswith("CO1.NTC."):
                    phase = identity
                process.update(
                    source=kind,
                    source_identity=identity,
                    source_url=safe_public_url(row.get("Link"), "noticeUID"),
                    modality=modality,
                    unspsc=unspsc,
                    description=description,
                    inventory_capable=document_capable(process),
                    inventory_keys={
                        "idContrato": row["idContrato"],
                        "id_fuente_contract": row.get("id_fuente_contract"),
                        "idUltimaFase": phase,
                    },
                )
                candidates[key] = process
            if not rows or page * DISCOVERY_PAGE_SIZE >= int(body["count"]):
                discovery["stop_reason"] = "provider_end"
                break
        else:
            discovery["stop_reason"] = "page_budget"
    finally:
        sample = select_processes(candidates, args, now, discovery, profile)
    return sample


def select_processes(candidates, args, now, discovery, profile):
    processes, _, _ = apply_freshness(list(candidates.values()), args.recent_days, now)
    processes, _, _ = apply_validity(processes, now)
    preferred = {plain(value) for value in profile.preferred_modalities}
    terminal = {plain(value) for value in profile.terminal_states}
    buckets = {}
    excluded_samples = {}
    for process in processes:
        process.pop("raw_source_reference")
        process.update(
            assess_commercial(
                profile, process["object"], process.pop("description"), process["unspsc"]
            )
        )
        process["preferred_modality"] = plain(process["modality"]) in preferred
        provider_terminal = plain(process["provider_status"]).removeprefix("proceso ") in terminal
        if provider_terminal:
            process["validity_status"] = "closed"
            process["validity_warning"] = "terminal_provider_status"
        process["supply_prefilter_match"] = (
            process["recent"] and process["commercial_exclusion"] is None
        )
        reason = process["commercial_exclusion"]
        if not process["recent"]:
            reason = "outside_publication_window"
        elif not reason and (process["source"] != "secop2" or not process["inventory_capable"]):
            reason = "inventory_unavailable_for_source"
        process["excluded_reason"] = reason
        process["sampled"] = False
        if reason:
            examples = excluded_samples.setdefault(reason, [])
            if len(examples) < 2:
                examples.append(process["process_reference"])
            continue
        departments = buckets.setdefault(selection_rank(process), {})
        department = plain(process["department"])
        departments.setdefault(department, deque()).append(process)
    sample = []
    for rank in sorted(buckets):
        departments = buckets[rank]
        while departments and len(sample) < args.processes:
            for department, queue in list(departments.items()):
                process = queue.popleft()
                process["sampled"] = True
                sample.append(process)
                if not queue:
                    del departments[department]
                if len(sample) == args.processes:
                    break
        if len(sample) == args.processes:
            break
    discovery["processes"] = processes
    discovery["exclusion_review_sample"] = excluded_samples
    return sample


def analyze_documents(client, process, storage, settings, allowance, metrics, documents, errors):
    inventory = fetch_inventory(client, process["inventory_keys"])
    if not inventory:
        return
    metrics["with_inventory"] += 1
    all_documents = {}
    for document in inventory:
        all_documents[document.document_id] = {
            "document_id": document.document_id,
            "name": document.original_name,
            "url": safe_public_url(document.source_url, "DocumentId"),
            "extension": document.extension,
            "role": document_role(document.original_name),
            "status": "not_selected",
            "complete": False,
        }
    documents.extend(all_documents.values())
    eligible = sorted(
        (
            document
            for document in inventory
            if document.extension == "pdf"
            and all_documents[document.document_id]["role"] != "excluded"
        ),
        key=lambda document: ROLE_ORDER[all_documents[document.document_id]["role"]],
    )
    selected_ids = {document.document_id for document in eligible[:allowance]}
    for entry in documents:
        entry["selection"] = (
            "selected"
            if entry["document_id"] in selected_ids
            else "post_award_or_draft"
            if entry["role"] == "excluded"
            else "unsupported_format"
            if entry["extension"] != "pdf"
            else "document_limit"
        )
    for document in eligible[:allowance]:
        if time.monotonic() + START_EXTRACTION_MARGIN + 12 > client.deadline:
            raise BudgetReached("duration_budget")
        entry = all_documents[document.document_id]
        stage = "download"
        try:
            metrics["documents_attempted"] += 1
            stored = spike.download_document(client, document, storage, settings)
            metrics["documents_downloaded"] += 1
            metrics["bytes_downloaded"] += stored.observed_size
            entry["sha256"] = stored.sha256
            stage = "extraction"
            if time.monotonic() + START_EXTRACTION_MARGIN > client.deadline:
                entry["status"] = "extraction_not_started"
                raise BudgetReached("duration_budget")
            detail, fragments = spike.run_existing_extractor(document, stored, storage, settings)
            result = coverage(detail)
            processed = {fragment.source_locator.get("page_number") for fragment in fragments}
            processed.discard(None)
            entry.update(
                complete=bool(result["coverage_complete"])
                and set(range(1, result["total_pages"] + 1)) <= processed
                and bool(processed),
                status=result["extraction_status"],
                pages_seen=sorted(processed),
                total_pages=result["total_pages"],
                ocr_pages=result["ocr_processed_pages"],
                ocr_omitted_pages=result["ocr_omitted_pages"],
                error_code=detail.get("error_code"),
                extraction_seconds=detail["elapsed_seconds"],
                fragments=fragments,
            )
            metrics["pages_reported"] += result["total_pages"]
            metrics["pages_with_text"] += len(processed)
            metrics["ocr_pages_reported"] += len(result["ocr_processed_pages"])
            if detail.get("error_code"):
                metrics["extraction_failures"] += 1
                errors.append(
                    {
                        "stage": stage,
                        "code": detail["error_code"],
                        "document_id": document.document_id,
                    }
                )
        except BudgetReached:
            if stage == "download":
                metrics["documents_attempted"] -= 1
                entry["status"] = "download_not_started"
            raise
        except (AcquisitionError, spike.SpikeError, OSError) as error:
            code = getattr(error, "code", type(error).__name__)
            entry.update(status=f"{stage}_failed", error_code=code)
            errors.append({"stage": stage, "code": code, "document_id": document.document_id})
            metrics[f"{stage}_failures"] += 1


def metrics_summary(discovery, results, metrics, client, started, profile):
    counts = Counter(result["status"] for result in results)
    analyzed = len(results)
    resolved = counts["experience_required"] + counts["no_experience_required"]
    supply = sum(p["supply_prefilter_match"] for p in discovery["processes"])
    eligible = sum(p["excluded_reason"] is None for p in discovery["processes"])

    return {
        **metrics,
        **commercial_metrics(discovery["processes"], results, profile),
        "discovered_rows": sum(page["received"] for page in discovery["pages"]),
        "duplicates": discovery["duplicates"],
        "unique_processes": len(discovery["processes"]),
        "excluded_by_reason": dict(
            Counter(p["excluded_reason"] for p in discovery["processes"] if p["excluded_reason"])
        ),
        "supply_candidates": supply,
        "inventory_eligible": eligible,
        "sampled": sum(p["sampled"] for p in discovery["processes"]),
        "analyzed": analyzed,
        "resolved": resolved,
        "classification": {status: counts[status] for status in STATUSES},
        "by_validity": {
            status: dict(Counter(r["status"] for r in results if r["validity_status"] == status))
            for status in ("open", "closed", "unknown")
        },
        "no_experience_rate_among_resolved": fraction(counts["no_experience_required"], resolved),
        "experience_rate_among_resolved": fraction(counts["experience_required"], resolved),
        "resolution_rate": fraction(resolved, analyzed),
        "unresolved_rate": fraction(analyzed - resolved, analyzed),
        "candidate_yield": fraction(counts["no_experience_required"], supply),
        "request_credits_used": client.requests,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "ai_calls": 0,
        "human_reviewed": 0,
    }


def run(client, args, settings, output, *, now=None, profile=None):
    profile = profile or load_commercial_profile()
    started, now = time.monotonic(), now or local_now()
    discovery = {
        "scope": "profile_feed_without_geographic_filter",
        "commercial_profile": {
            "version": profile.version,
            "sha256": profile.fingerprint,
            "catalog_version": profile.catalog["version"],
        },
        "cutoff": now.isoformat(),
        "date_field": "FechaPublicacion",
        "recent_days": args.recent_days,
        "pages": [],
        "processes": [],
        "duplicates": 0,
    }
    results, inventories, errors = [], [], []
    metrics = Counter(
        dict.fromkeys(
            (
                "with_inventory",
                "documents_attempted",
                "documents_downloaded",
                "download_failures",
                "extraction_failures",
                "bytes_downloaded",
                "pages_reported",
                "pages_with_text",
                "ocr_pages_reported",
                "unique_document_hashes",
            ),
            0,
        )
    )
    hashes = set()
    status = "failed"
    exit_code = 1
    try:
        check_session(client, PROFILE, aggregator=True)
        sample = discover(client, args, now, discovery, profile)
        write_json(output / "processes.json", discovery)
        storage = spike.LocalBinaryStorage(output / "binaries")
        for index, process in enumerate(sample):
            reference = process["process_reference"]
            documents, process_errors = [], []
            remaining = args.documents - metrics["documents_attempted"]
            allowance = min(2, remaining, max(1, remaining - (len(sample) - index - 1)))
            stop = None
            request_start = client.requests
            process_start = time.monotonic()
            downloads_before = metrics["documents_downloaded"]
            ocr_before = metrics["ocr_pages_reported"]
            try:
                analyze_documents(
                    client,
                    process,
                    storage,
                    settings,
                    allowance,
                    metrics,
                    documents,
                    process_errors,
                )
            except (BudgetReached, CandidateError) as error:
                stop = error
                process_errors.append(
                    {
                        "stage": "pipeline",
                        "code": error.code if isinstance(error, CandidateError) else str(error),
                    }
                )
            except (AcquisitionError, spike.SpikeError, OSError) as error:
                process_errors.append(
                    {"stage": "inventory", "code": getattr(error, "code", type(error).__name__)}
                )
            if allowance == 0:
                process_errors.append({"stage": "selection", "code": "document_budget"})
            classification = classify_experience(documents)
            if not documents and not process_errors:
                classification["reason"] = "empty_inventory"
            for document in documents:
                document.pop("fragments", None)
                if document.get("sha256"):
                    hashes.add(document["sha256"])
            inventories.append({"process_reference": reference, "documents": documents})
            results.append(
                {
                    "run_id": output.name,
                    "process_reference": reference,
                    "validity_status": process["validity_status"],
                    "commercial_category": process["primary_category"],
                    "commercial_priority": process["commercial_priority"],
                    "operational_cost": {
                        "elapsed_seconds": round(time.monotonic() - process_start, 3),
                        "request_credits": client.requests - request_start,
                        "downloads": metrics["documents_downloaded"] - downloads_before,
                        "ocr_pages_reported": metrics["ocr_pages_reported"] - ocr_before,
                    },
                    "coverage": {
                        "inventory_available": bool(documents),
                        "documents_complete": sum(d["complete"] for d in documents),
                    },
                    **classification,
                }
            )
            errors.extend({"process_reference": reference, **error} for error in process_errors)
            if stop:
                raise stop
        complete = (
            len(sample) == args.processes
            and discovery["stop_reason"] != "provider_repeated_page"
            and not errors
        )
        status, exit_code = ("completed", 0) if complete else ("partial", 2)
    except BudgetReached as error:
        status, exit_code = "partial", 2
        errors.append({"stage": "budget", "code": str(error)})
    except CandidateError as error:
        exit_code = error.exit_code
        errors.append({"stage": "cdp", "code": error.code, "criterion": error.criterion})
    except KeyboardInterrupt:
        status, exit_code = "partial", 2
        errors.append({"stage": "run", "code": "interrupted"})
    except (spike.SpikeError, OSError) as error:
        errors.append({"stage": "run", "code": type(error).__name__})
    finally:
        metrics["unique_document_hashes"] = len(hashes)
        limits = {
            "processes": args.processes,
            "discovery_pages": args.discovery_pages,
            "documents": args.documents,
            "documents_per_process": 2,
            "document_max_bytes": DOCUMENT_BYTES,
            "pages_per_pdf": PAGES_PER_DOCUMENT,
            "pages_per_run_upper_bound": args.documents * PAGES_PER_DOCUMENT,
            "ocr_pages_per_pdf": OCR_PER_DOCUMENT,
            "ocr_pages_per_run_upper_bound": args.documents * OCR_PER_DOCUMENT,
            "request_credits": REQUEST_CREDITS,
            "duration_seconds": DURATION_SECONDS,
            "ai_calls": 0,
        }
        summary = {
            "run_id": output.name,
            "status": status,
            "limits": limits,
            **metrics_summary(discovery, results, metrics, client, started, profile),
        }
        for filename, data in (
            ("processes.json", discovery),
            ("documents.json", inventories),
            ("experience_requirements.json", results),
            ("metrics.json", summary),
            ("errors.json", errors),
        ):
            write_json(output / filename, data)
        (output / "summary.md").write_text(
            f"# EN-01 · {output.name}\n\n"
            f"- Estado: {status}\n"
            f"- Procesos analizados: {summary['analyzed']} de {summary['sampled']} seleccionados\n"
            f"- Procesos resueltos: {summary['resolved']}\n"
            f"- Documentos descargados: {summary['documents_downloaded']}\n"
            f"- Revisión humana: pendiente\n",
            encoding="utf-8",
        )
    return exit_code


def settings_for_run(output, tesseract, tessdata):
    policy = spike.load_ocr_policy(spike.ROOT / "config" / "extraction_ocr.v1.json")
    policy = policy.model_copy(
        update={
            "fallback_language": "spa",
            "max_ocr_pages": OCR_PER_DOCUMENT,
            "page_timeout_seconds": 6,
            "document_timeout_seconds": 14,
            "max_retry_attempts": 0,
        }
    )
    engine = probe_engine(tesseract, tessdata, policy)
    if not engine.get("available") or engine.get("language") != "spa":
        raise spike.SpikeError("Tesseract spa no disponible.")
    policy_path = output / "ocr_policy.json"
    write_json(policy_path, policy.model_dump())
    return spike.Settings(
        _env_file=None,
        database_url="disabled://no-db",
        document_timeout_seconds=12,
        document_max_bytes=DOCUMENT_BYTES,
        extraction_max_bytes=DOCUMENT_BYTES,
        extraction_max_pages=PAGES_PER_DOCUMENT,
        extraction_timeout_seconds=12,
        extraction_ocr_enabled=True,
        extraction_ocr_config_path=policy_path,
        extraction_tesseract_cmd=tesseract,
        extraction_tessdata_path=tessdata,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processes", type=int, choices=range(5, 11), default=5)
    parser.add_argument("--documents", type=int, choices=range(5, 8), default=5)
    parser.add_argument("--discovery-pages", type=int, choices=range(1, 7), default=4)
    parser.add_argument("--recent-days", type=int, choices=range(1, 61), default=30)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9232")
    parser.add_argument("--tesseract", default="tesseract")
    parser.add_argument("--tessdata", type=Path)
    parser.add_argument("--commercial-profile", type=Path, default=DEFAULT_PROFILE)
    args = parser.parse_args(argv)
    from playwright.sync_api import sync_playwright

    try:
        validate_cdp_url(args.cdp_url)
        profile = load_commercial_profile(args.commercial_profile)
        if OUTPUT_ROOT.resolve() != OUTPUT_ROOT:
            raise ValueError("Ruta de salida fuera del directorio experimental.")
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="en01-", dir=OUTPUT_ROOT))
        print(json.dumps({"output": str(output)}), flush=True)
        deadline = time.monotonic() + DURATION_SECONDS
        settings = settings_for_run(output, args.tesseract, args.tessdata)
        with sync_playwright() as playwright:
            browser = connect_browser(playwright, args.cdp_url)
            return run(
                SmokeClient(find_page(browser), deadline), args, settings, output, profile=profile
            )
    except spike.SpikeError as error:
        print(f"EN-01: {error.code}" if isinstance(error, CandidateError) else f"EN-01: {error}")
        return error.exit_code if isinstance(error, CandidateError) else 1
    except Exception as error:
        # Provider and reader exceptions can include response content or local paths.
        print(f"EN-01: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
