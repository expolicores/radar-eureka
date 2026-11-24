"""EN-01: bounded national SECOP II supply sampling with local, deterministic evidence."""

import argparse
import hashlib
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
    ASSERTION_TYPES,
    STATUSES,
    classify_experience,
    document_cover_metadata,
    document_priority,
    document_role,
)
from licitaciones_candidate_contracts import CandidateProcess
from licitaciones_cdp_runtime import (
    CandidateError,
    PageClient,
    check_session,
    connect_browser,
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
from public_procurement.licitaciones_cdp.configuration import (
    ProfileConfigurationError,
    resolve_profile_id,
)

DISCOVERY_PAGE_SIZE = 30
GEOGRAPHY_SOURCE = "Licitaciones.info"
NATIONAL_LOCATION_COUNT = 1130
DEFAULT_GEOGRAPHY = Path(__file__).with_name(
    "eureka_nacional_geography(from_licitaciones_info).v1.json"
)
OCR_PER_DOCUMENT = 2
REQUEST_CREDITS = 60
DURATION_SECONDS = 360
START_EXTRACTION_MARGIN = 50
DOCUMENT_BYTES = 10 * 1024 * 1024
OUTPUT_ROOT = spike.ROOT.parent / ".local" / "eureka-nacional-spike"


class BudgetReached(spike.SpikeError):
    pass


class SmokeClient(PageClient):
    def __init__(self, page, profile_id, deadline):
        super().__init__(page, profile_id, lambda _event: None)
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


def load_national_locations(path=DEFAULT_GEOGRAPHY):
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise spike.SpikeError(
            "No se pudo leer la configuraci\u00f3n geogr\u00e1fica nacional."
        ) from error
    if not isinstance(config, dict) or config.get("source") != GEOGRAPHY_SOURCE:
        raise spike.SpikeError(
            "La geograf\u00eda nacional debe identificar a Licitaciones.info como fuente."
        )

    ids = config.get("location_ids")
    if (
        not isinstance(ids, list)
        or config.get("location_count") != NATIONAL_LOCATION_COUNT
        or len(ids) != NATIONAL_LOCATION_COUNT
        or not all(isinstance(item, str) and re.fullmatch(r"[0-9]+", item) for item in ids)
        or len(set(ids)) != NATIONAL_LOCATION_COUNT
    ):
        raise spike.SpikeError(
            "Se requieren los 1.130 identificadores de ubicaci\u00f3n capturados, \u00fanicos."
        )
    return tuple(ids)


def discover(client, args, now, discovery, profile, locations):
    location_filter = ",".join(locations)
    payload = spike.build_process_payload(location_filter, None, DISCOVERY_PAGE_SIZE)
    discovery["geography"] = {
        "source": GEOGRAPHY_SOURCE,
        "location_count": len(locations),
        "ubicacion_filter_sha256": hashlib.sha256(location_filter.encode("ascii")).hexdigest(),
    }
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
                f"/cliente/contratos/get-info/MP?perfiles={client.profile_id}",
                {**payload, "page": page},
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
                candidate = CandidateProcess.from_source(row, client.profile_id)
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


def select_ocr_pages(native, low_text, budget):
    if not budget or native.error_code:
        return []
    visited = native.diagnostics.get("native_pages_visited", 0)
    candidates = set(low_text).intersection(range(1, visited + 1))
    likely = set()
    for fragment in native.fragments:
        number = fragment.page_number
        for line in fragment.text.splitlines():
            heading = plain(line).strip()
            if len(heading) <= 110 and re.search(
                r"\b(?:experiencia|requisitos? habilitantes?|acreditacion)\b", heading
            ):
                likely.update({number - 1, number + 1})
    # For a named rector, an unreadable cover can identify scope and document type.
    cover = {1} if document_role(native.document.original_name) == "primary" else set()
    return (sorted(candidates & likely) + sorted((candidates & cover) - likely))[:budget]


def extract_document(document, stored, storage, settings, entry, *, ocr_pages=OCR_PER_DOCUMENT):
    detail, fragments = spike.run_existing_extractor(
        document,
        stored,
        storage,
        settings,
        select_ocr_pages=lambda native, low_text: select_ocr_pages(native, low_text, ocr_pages),
    )
    diagnostics = detail.get("diagnostics", {})
    total = detail["page_count"]
    quality = diagnostics.get("native_quality", [])
    native_useful = {page["page_number"] for page in quality if not page["ocr_required"]}
    native_text = {
        f.source_locator["page_number"]
        for f in fragments
        if f.source_locator.get("extraction_method") == "native_pdf_text"
    }
    if not quality:
        native_useful = native_text
    ocr_success = set(diagnostics.get("successful_pages", []))
    processed = native_useful | ocr_success
    pending = set(range(1, total + 1)) - processed
    incomplete_from = diagnostics.get("native_incomplete_from")
    if incomplete_from is not None:
        pending.update(range(incomplete_from, total + 1))
    visited = diagnostics.get("native_pages_visited", total)
    selected = set(diagnostics.get("required_pages", []))
    first_page = "".join(f.text for f in fragments if f.source_locator.get("page_number") == 1)
    cover_role, cover_metadata = document_cover_metadata(first_page)
    if cover_role == "excluded" or (cover_role and entry["role"] == "unknown"):
        entry.update(role=cover_role, role_source="cover")
    entry.update(
        cover_metadata=cover_metadata,
        complete=bool(total and not pending and not detail.get("error_code")),
        status=diagnostics.get("status", detail["status"]),
        pages_seen=sorted(processed),
        total_pages=total,
        native_pages=sorted(native_text),
        native_pages_visited=visited,
        ocr_required_pages=[
            p["page_number"] for p in quality if p["ocr_required"] and p["page_number"] <= visited
        ],
        ocr_pages=detail.get("ocr_pages", []),
        ocr_success_pages=sorted(ocr_success),
        ocr_omitted_pages=diagnostics.get("omitted_pages", []),
        ocr_unselected_pages=[
            p["page_number"]
            for p in quality
            if p["ocr_required"]
            and p["page_number"] <= visited
            and p["page_number"] not in selected
        ],
        ocr_diagnostics=diagnostics.get("pages", []),
        pending_pages=sorted(pending),
        error_code=detail.get("error_code"),
        native_stop_reason=diagnostics.get("native_stop_reason"),
        native_page_errors=diagnostics.get("native_page_errors", []),
        native_cpu_seconds=diagnostics.get("native_cpu_seconds"),
        extraction_seconds=detail["elapsed_seconds"],
        fragments=fragments,
    )


def analyze_documents(
    client,
    process,
    storage,
    settings,
    allowance,
    metrics,
    documents,
    errors,
    *,
    ocr_pages=OCR_PER_DOCUMENT,
):
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
            "role_source": "filename",
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
        key=lambda document: document_priority(
            document.original_name, all_documents[document.document_id]["role"]
        ),
    )
    for entry in documents:
        entry["selection"] = (
            "irrelevant_document"
            if entry["role"] == "excluded"
            else "unsupported_format"
            if entry["extension"] != "pdf"
            else "document_limit"
        )
    prior_limit = False
    for index, document in enumerate(eligible[:allowance]):
        if index and classify_experience(documents)["status"] in {
            "experience_required",
            "no_experience_required",
        }:
            break
        if time.monotonic() + START_EXTRACTION_MARGIN + 12 > client.deadline:
            raise BudgetReached("duration_budget")
        entry = all_documents[document.document_id]
        entry["selection"] = "selected"
        entry["selection_reason"] = "alternative_after_limit" if prior_limit else "priority"
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
            extract_document(document, stored, storage, settings, entry, ocr_pages=ocr_pages)
            code = entry["error_code"] or entry["native_stop_reason"]
            prior_limit = code in {
                "too_large",
                "text_limit",
                "fragment_limit",
                "memory_limit",
                "native_time_limit",
                "timeout",
                "reader_failed",
            }
            metrics["documents_processed"] += bool(entry["fragments"])
            metrics["pages_reported"] += entry["total_pages"]
            metrics["pages_with_text"] += len(entry["pages_seen"])
            metrics["ocr_pages_reported"] += len(entry["ocr_pages"])
            metrics["native_pages_with_text"] += len(entry["native_pages"])
            metrics["pending_pages"] += len(entry["pending_pages"])
            if code:
                metrics["extraction_failures"] += 1
                errors.append(
                    {
                        "stage": stage,
                        "code": code,
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
            prior_limit = code in {"page_limit", "too_large"}
            entry.update(status=f"{stage}_failed", error_code=code)
            errors.append({"stage": stage, "code": code, "document_id": document.document_id})
            metrics[f"{stage}_failures"] += 1


def metrics_summary(discovery, results, metrics, client, started, profile):
    counts = Counter(result["status"] for result in results)
    analyzed = len(results)
    resolved = counts["experience_required"] + counts["no_experience_required"]
    supply = sum(p["supply_prefilter_match"] for p in discovery["processes"])
    eligible = sum(p["excluded_reason"] is None for p in discovery["processes"])
    assertions = Counter(
        item["assertion_type"] for result in results for item in result["evidence"]
    )
    review = Counter(result["review_category"] for result in results)

    return {
        "assertions": {kind: assertions[kind] for kind in ASSERTION_TYPES},
        "review_categories": dict(review),
        "review_prioritized": sum(r["review_priority"] <= 3 for r in results),
        "human_verified_errors": None,
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


def run(client, args, settings, output, *, now=None, profile=None, locations=None):
    profile = profile or load_commercial_profile()
    locations = load_national_locations() if locations is None else locations
    started, now = time.monotonic(), now or local_now()
    discovery = {
        "scope": "national_explicit_location_filter",
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
                "documents_processed",
                "bytes_downloaded",
                "pages_reported",
                "native_pages_with_text",
                "pending_pages",
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
        check_session(client, client.profile_id, aggregator=True)
        sample = discover(client, args, now, discovery, profile, locations)
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
                    ocr_pages=getattr(args, "ocr_pages", OCR_PER_DOCUMENT),
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
            classification = classify_experience(documents, inventory_complete=bool(documents))
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
            "native_pages_per_pdf": None,
            "ocr_pages_per_pdf": getattr(args, "ocr_pages", OCR_PER_DOCUMENT),
            "ocr_pages_per_run_upper_bound": args.documents
            * getattr(args, "ocr_pages", OCR_PER_DOCUMENT),
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
            ("review_queue.json", sorted(results, key=lambda result: result["review_priority"])),
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


def settings_for_run(output, tesseract, tessdata, ocr_pages=OCR_PER_DOCUMENT):
    policy = spike.load_ocr_policy(spike.ROOT / "config" / "extraction_ocr.v1.json")
    policy = policy.model_copy(
        update={
            "fallback_language": "spa",
            "max_ocr_pages": max(1, ocr_pages),
            "page_timeout_seconds": 6,
            "document_timeout_seconds": 14,
            "max_retry_attempts": 0,
        }
    )
    policy_path = output / "ocr_policy.json"
    write_json(policy_path, policy.model_dump())
    return spike.Settings(
        _env_file=None,
        database_url="disabled://no-db",
        document_timeout_seconds=12,
        document_max_bytes=DOCUMENT_BYTES,
        extraction_max_bytes=DOCUMENT_BYTES,
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
    parser.add_argument(
        "--ocr-pages", type=int, choices=range(OCR_PER_DOCUMENT + 1), default=OCR_PER_DOCUMENT
    )
    parser.add_argument(
        "--profile-id", help="Override de LICITACIONES_PROFILE_ID para esta ejecucion."
    )
    parser.add_argument("--commercial-profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--geography", type=Path, default=DEFAULT_GEOGRAPHY)
    args = parser.parse_args(argv)
    try:
        profile_id = resolve_profile_id(args.profile_id)
        validate_cdp_url(args.cdp_url)
        profile = load_commercial_profile(args.commercial_profile)
        locations = load_national_locations(args.geography)
        from playwright.sync_api import sync_playwright

        if OUTPUT_ROOT.resolve() != OUTPUT_ROOT:
            raise ValueError("Ruta de salida fuera del directorio experimental.")
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="en01-", dir=OUTPUT_ROOT))
        print(json.dumps({"output": str(output)}), flush=True)
        deadline = time.monotonic() + DURATION_SECONDS
        settings = settings_for_run(output, args.tesseract, args.tessdata, args.ocr_pages)
        with sync_playwright() as playwright:
            browser = connect_browser(playwright, args.cdp_url)
            return run(
                SmokeClient(find_page(browser), profile_id, deadline),
                args,
                settings,
                output,
                profile=profile,
                locations=locations,
            )
    except ProfileConfigurationError as error:
        print(f"EN-01: {error}")
        return 1
    except spike.SpikeError as error:
        print(f"EN-01: {error.code}" if isinstance(error, CandidateError) else f"EN-01: {error}")
        return error.exit_code if isinstance(error, CandidateError) else 1
    except Exception as error:
        # Provider and reader exceptions can include response content or local paths.
        print(f"EN-01: {type(error).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
