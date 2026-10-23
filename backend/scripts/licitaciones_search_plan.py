"""Declarative, sequential discovery only. No document, OCR or persistence services."""

import json
import math
import time
from pathlib import Path

from licitaciones_candidate_contracts import CONTRACT_VERSION, CandidateProcess
from licitaciones_cdp_runtime import (
    MANUAL_LOGIN,
    CandidateError,
    check_session,
    load_payload,
    write_json,
)
from licitaciones_event_time import timed_warning
from licitaciones_freshness import (
    DEFAULT_RECENT_DAYS,
    apply_freshness,
    local_now,
    validate_recent_days,
)
from licitaciones_sources import annotate_source, source_kind
from licitaciones_validity import apply_validity, validity_counts
from spike_licitaciones_info import SpikeError, build_process_payload, normalized

DEFAULT_PLAN = Path(__file__).with_name("licitaciones_search_plan.v1.json")
VERSION = "licitaciones-search-plan-v1"


def load_plan(path):
    """Reject unsupported filters/volume before connecting to any browser."""
    try:
        return _load_plan(Path(path))
    except (KeyError, TypeError, ValueError, OSError, AttributeError) as error:
        raise SpikeError("Plan invalido: revisa estructura, IDs y limites locales.") from error


def _load_plan(path):
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    if (
        set(config) - {"default_recent_days"}
        != {
            "version",
            "profile_id",
            "regions",
            "object_terms",
            "unspsc",
            "limits",
            "pauses",
            "searches",
        }
        or config["version"] != VERSION
        or config["profile_id"] != "1086005"
    ):
        raise ValueError("Unsupported contract")
    config["default_recent_days"] = validate_recent_days(
        config.get("default_recent_days", DEFAULT_RECENT_DAYS)
    )
    limits, pauses = config["limits"], config["pauses"]
    if set(limits) != {"max_queries_per_run", "limit", "page", "max_retries"}:
        raise ValueError("Unsupported limits")
    if any(type(value) is not int for value in limits.values()):
        raise ValueError("Integer limits required")
    if not (
        1 <= limits["max_queries_per_run"] <= 6
        and limits["limit"] == 30
        and limits["page"] == 1
        and 0 <= limits["max_retries"] <= 1
    ):
        raise ValueError("Unsafe limits")
    if set(pauses) != {"sleep_between_queries", "retry_wait_seconds"} or any(
        type(value) not in (int, float) or not math.isfinite(value) or not 3 <= value <= 60
        for value in pauses.values()
    ):
        raise ValueError("Pauses must be between 3 and 60 seconds")
    regions = config["regions"]
    if set(regions) != {"boyaca", "casanare"}:
        raise ValueError("Unsupported regions")
    if set(regions["boyaca"]) != {"ids_file", "expected_count"} or set(regions["casanare"]) != {
        "ids",
        "expected_count",
    }:
        raise ValueError("Unsupported region options")
    if regions["boyaca"].get("expected_count") != 123:
        raise ValueError("Boyaca count")
    boyaca = load_payload(path.parent / regions["boyaca"]["ids_file"], "refrigerio", 30)
    casanare = regions["casanare"]["ids"]
    if casanare != [str(value) for value in range(4009001, 4009020)] or (
        regions["casanare"].get("expected_count") != 19
    ):
        raise ValueError("Casanare IDs differ from validated contract")
    locations = {"boyaca": boyaca["query"]["ubicacion_filter"], "casanare": ",".join(casanare)}
    terms = config["object_terms"]
    if (
        not isinstance(terms, list)
        or not terms
        or any(not isinstance(term, str) or not term.strip() or len(term) > 200 for term in terms)
    ):
        raise ValueError("Explicit object terms required")
    unspsc = config["unspsc"]
    if set(unspsc) != {"status", "catalog_file"} or unspsc["status"] != "pending_remote_mapping":
        raise ValueError("Remote UNSPSC mapping has not been validated")
    # Read existing declarative catalog only; never load Radar services or invent codes.
    catalog = json.loads((path.parent / unspsc["catalog_file"]).read_text(encoding="utf-8"))
    codes = sorted({code for family in catalog["families"] for code in family["unspsc"]})
    if not codes or any(
        not isinstance(code, str) or len(code) != 8 or not code.isdigit() for code in codes
    ):
        raise ValueError("Invalid local UNSPSC catalog")
    searches = config["searches"]
    if not isinstance(searches, list) or not 1 <= len(searches) <= limits["max_queries_per_run"]:
        raise ValueError("At most six explicit searches")
    seen, resolved = set(), []
    for search in searches:
        if set(search) - {"id", "region", "object_term", "unspsc"} or not {
            "id",
            "region",
            "object_term",
        } <= set(search):
            raise ValueError("Unsupported search filters")
        if not isinstance(search["id"], str) or not search["id"] or search["id"] in seen:
            raise ValueError("Unique search IDs required")
        seen.add(search["id"])
        if search["region"] not in locations or search["object_term"] not in terms:
            raise ValueError("Undeclared region or term")
        requested = search.get("unspsc", [])
        if not isinstance(requested, list) or any(code not in codes for code in requested):
            raise ValueError("UNSPSC code absent from existing catalog")
        resolved.append(
            {
                **search,
                "unspsc": requested,
                "payload": build_process_payload(
                    locations[search["region"]], search["object_term"], 30
                ),
            }
        )
    return {
        **config,
        "searches": resolved,
        "unspsc_catalog_codes": codes,
        "unspsc_catalog_families": len(catalog["families"]),
    }


def process_key(process):
    identity = (
        ("id", process["id_contrato"])
        if process.get("id_contrato")
        else ("codigo", process["codigo_proceso"])
    )
    return process["external_source"], process["profile_id"], identity


def merge_process(index, process, search):
    key = process_key(process)
    duplicate = key in index
    if not duplicate:
        index[key] = {
            **process,
            "matched_searches": [],
            "matched_objects": [],
            "matched_regions": [],
            "matched_unspsc": [],
        }
    target = index[key]
    for field, values in (
        ("matched_searches", [search["id"]]),
        ("matched_objects", [search["object_term"]]),
        ("matched_regions", [search["region"]]),
    ):
        for value in values:
            if value not in target[field]:
                target[field].append(value)
    # Pending UNSPSC is not a filter or an observed match. Keep requested codes per query only.
    return duplicate


def plan_rows(body):
    if isinstance(body, dict) and str(body.get("count")) == "1337370":
        raise CandidateError("generic_dataset", "Universo generico conocido.")
    if isinstance(body, dict) and body.get("data") == []:
        count = body.get("count")
        if (type(count) is int and count >= 0) or (isinstance(count, str) and count.isdigit()):
            return [], []
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("data"), list)
        or not str(body.get("count", "")).isdigit()
    ):
        raise CandidateError("invalid_response", "Discovery JSON invalido.")
    rows = body["data"]
    if len(rows) > 30:
        raise CandidateError("invalid_response", "Discovery excede las 30 filas permitidas.")
    warnings = []
    accepted = []
    for row in rows:
        try:
            if (
                not (row.get("idContrato") or row.get("CodigoProceso"))
                or not all(isinstance(row.get(key), str) for key in ("Objeto", "TextoDepartamento"))
                or not row.get("Objeto", "").strip()
                or not row.get("TextoDepartamento", "").strip()
            ):
                raise ValueError
        except (ValueError, KeyError, AttributeError, TypeError):
            warnings.append(timed_warning({"code": "unenriched_row_skipped"}))
            continue
        accepted.append(row)
    return accepted, warnings


def run_plan(
    client, plan, output, wait, event, clock=time.monotonic, *, recent_days=None, now=None
):
    """One preflight, then at most six sequential queries; preserve partial local results."""
    started = clock()
    now = now or local_now()
    recent_days = validate_recent_days(
        plan["default_recent_days"] if recent_days is None else recent_days
    )
    index, eligible_keys = {}, set()
    summary = {
        "version": VERSION,
        "mode": "discovery_plan_only",
        "experimental": True,
        "host": "col.licitaciones.info",
        "profile_id": plan["profile_id"],
        "recent_days": recent_days,
        "freshness_evaluated_at": now.isoformat(),
        "validity_evaluated_at": now.isoformat(),
        "freshness_timezone": "America/Bogota (UTC-05:00)",
        "limits": plan["limits"],
        "pauses": plan["pauses"],
        "status": "running",
        "stop_reason": None,
        "total_queries_planned": len(plan["searches"]),
        "total_queries_executed": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "total_rows_received": 0,
        "duplicates_across_queries": 0,
        "warnings": [],
        "queries": [],
        "unspsc_status": plan["unspsc"]["status"],
        "unspsc_catalog_codes": plan["unspsc_catalog_codes"],
        "unspsc_catalog_families": plan["unspsc_catalog_families"],
    }
    exit_code, consecutive_invalid = 0, 0

    warning_times = {}

    def save():
        processes, freshness, freshness_warnings = apply_freshness(
            list(index.values()), recent_days, now
        )
        processes, validity, validity_warnings = apply_validity(processes, now)
        processes = [annotate_source(p) for p in processes]
        summary.update(freshness)
        summary.update(validity)
        recent = [p for p in processes if p["recent"]]
        summary.update(
            processes_total=len(processes),
            recent_processes=len(recent),
            open_processes=sum(p["validity_status"] == "open" for p in recent),
            closed_processes=sum(p["validity_status"] == "closed" for p in recent),
            unknown_validity_processes=sum(p["validity_status"] == "unknown" for p in recent),
        )
        summary["warnings"] = (
            [w for w in summary["warnings"] if w.get("stage") not in {"freshness", "validity"}]
            + freshness_warnings
            + validity_warnings
        )
        for query in summary["queries"]:
            matching = [p for p in processes if query["id"] in p["matched_searches"]]
            query.update(validity_counts(matching))
            references = {p["process_reference"] for p in matching}
            query["warnings"] = [w for w in query["warnings"] if w.get("stage") != "validity"] + [
                w for w in validity_warnings if w["process_reference"] in references
            ]
        # Freshness/validity diagnostics are regenerated while saving; preserve the
        # first event time within this run, never import it from a previous run.
        for warning in summary["warnings"]:
            identity = tuple(
                str(warning.get(k)) for k in ("code", "stage", "process_reference", "search_id")
            )
            warning["generated_at"] = warning_times.setdefault(
                identity, warning.get("generated_at") or timed_warning({})["generated_at"]
            )
        for query in summary["queries"]:
            for warning in query["warnings"]:
                warning.setdefault("generated_at", timed_warning({})["generated_at"])
        summary.update(
            unique_processes=len(index),
            unique_secop_ii=len(eligible_keys),
            duration=round(clock() - started, 3),
            request_budget_used=client.requests,
        )
        discovery = {
            "contract_version": CONTRACT_VERSION,
            "mode": "discovery_plan_only",
            "recent_days": recent_days,
            "freshness_evaluated_at": now.isoformat(),
            "validity_evaluated_at": now.isoformat(),
            "processes": processes,
            "eligible_total": processes,
            "eligible_recent": [p for p in processes if p["recent"]],
            "eligible": [p for p in processes if p["recent"] and p["validity_status"] == "open"],
        }
        write_json(output / "discovery.json", discovery)
        write_json(output / "search_plan_summary.json", summary)
        write_json(output / "run_summary.json", summary)

    save()
    try:
        health = check_session(client, plan["profile_id"], aggregator=True)
        summary["preflight"] = health
        summary["warnings"].extend(health.get("warnings", []))
        event({"stage": "preflight", "status": "healthy", **health})
        for number, search in enumerate(plan["searches"]):
            if number:
                wait(plan["pauses"]["sleep_between_queries"])
            query_started = clock()
            query = {
                key: search[key] for key in ("id", "region", "object_term", "unspsc", "payload")
            }
            query.update(
                status="running",
                provider_count=None,
                rows_received=0,
                eligible_secop_ii=0,
                warnings=[],
                attempts=0,
            )
            if search["unspsc"]:
                query["warnings"].append(
                    timed_warning({"code": "pending_remote_mapping", "filter_sent": False})
                )
            summary["queries"].append(query)
            summary["total_queries_executed"] += 1
            try:
                for attempt in range(plan["limits"]["max_retries"] + 1):
                    query["attempts"] += 1
                    try:
                        body = client.post(
                            f"/cliente/contratos/get-info/MP?perfiles={plan['profile_id']}",
                            search["payload"],
                        )
                        break
                    except CandidateError as error:
                        if (
                            not getattr(error, "transient", False)
                            or attempt == plan["limits"]["max_retries"]
                        ):
                            raise
                        query["warnings"].append(
                            timed_warning(
                                {
                                    "code": "transient_retry",
                                    "http_status": getattr(error, "http_status", None),
                                }
                            )
                        )
                        wait(plan["pauses"]["retry_wait_seconds"])
                query["provider_count"] = body.get("count") if isinstance(body, dict) else None
                received = body.get("data") if isinstance(body, dict) else None
                query["rows_received"] = len(received) if isinstance(received, list) else 0
                summary["total_rows_received"] += query["rows_received"]
                rows, warnings = plan_rows(body)
                query["warnings"].extend(warnings)
                query_seen = set()
                for row in rows:
                    if normalized(row["TextoDepartamento"]).split(":")[0].strip() != search[
                        "region"
                    ] or normalized(search["object_term"]) not in normalized(row["Objeto"]):
                        query["warnings"].append(
                            timed_warning(
                                {
                                    "code": "outside_local_scope",
                                    "stage": "scope",
                                    "source": source_kind(row),
                                    "codigo_proceso": row.get("CodigoProceso"),
                                    "search_id": search["id"],
                                }
                            )
                        )
                        continue
                    process = CandidateProcess.from_source(row, plan["profile_id"]).to_dict()
                    key = process_key(process)
                    if key in query_seen:
                        continue
                    query_seen.add(key)
                    summary["duplicates_across_queries"] += int(
                        merge_process(index, process, search)
                    )
                    if (
                        str(row.get("id_fuente_contract")) == "3"
                        or row.get("key_config") == "secop2"
                    ):
                        eligible_keys.add(key)
                        query["eligible_secop_ii"] += 1
                query["status"] = "completed"
                summary["successful_queries"] += 1
                consecutive_invalid = 0
            except CandidateError as error:
                query.update(status="failed", error_code=error.code, criterion=error.criterion)
                query["error"] = timed_warning({"code": error.code})
                query["http_status"] = getattr(error, "http_status", None)
                if error.code == "session_expired":
                    summary["action"] = MANUAL_LOGIN
                summary["failed_queries"] += 1
                consecutive_invalid += 1
                fatal = error.code not in {
                    "invalid_response",
                    "invalid_get_info",
                    "insufficient_enriched_rows",
                }
                rate_limited = getattr(error, "http_status", None) == 429
                if (
                    fatal
                    or rate_limited
                    or getattr(error, "transient", False)
                    or consecutive_invalid >= 2
                ):
                    summary["stop_reason"] = (
                        "rate_limited"
                        if rate_limited
                        else "repeated_provider_failure"
                        if getattr(error, "transient", False)
                        else "repeated_invalid_response"
                        if not fatal
                        else error.code
                    )
                    exit_code = error.exit_code
                    break
            except Exception:
                query.update(status="failed", error_code="unexpected_error")
                query["error"] = timed_warning({"code": "unexpected_error"})
                summary["failed_queries"] += 1
                raise
            finally:
                query["duration"] = round(clock() - query_started, 3)
                summary["warnings"].extend(
                    {"search_id": search["id"], **item} for item in query["warnings"]
                )
                save()
                event(
                    {
                        "stage": "discovery",
                        **{
                            key: query[key]
                            for key in (
                                "id",
                                "status",
                                "rows_received",
                                "eligible_secop_ii",
                                "secop_ii_recent",
                                "secop_ii_open",
                                "secop_ii_closed",
                                "secop_ii_unknown",
                                "provider_status_deadline_conflicts",
                            )
                        },
                    }
                )
        summary["status"] = (
            "aborted"
            if summary["stop_reason"]
            else (
                "completed_with_errors"
                if summary["failed_queries"]
                else "completed_with_warnings"
                if summary["warnings"]
                else "completed"
            )
        )
        exit_code = exit_code or (2 if summary["failed_queries"] else 0)
    except CandidateError as error:
        summary.update(status="aborted", stop_reason=error.code, criterion=error.criterion)
        summary["preflight"] = summary.get("preflight") or {
            "preflight_status": "session_expired"
            if error.code == "session_expired"
            else "unhealthy_response",
            "reason": error.code,
            **getattr(error, "quality", {}),
        }
        event({"stage": "preflight", **summary["preflight"]})
        if error.code == "session_expired":
            summary["action"] = MANUAL_LOGIN
        exit_code = error.exit_code
    except Exception as error:
        summary.update(
            status="failed", stop_reason="unexpected_error", error_type=type(error).__name__
        )
        exit_code = 1
    finally:
        save()
        event(
            {
                "stage": "summary",
                "status": summary["status"],
                "stop_reason": summary["stop_reason"],
                "unique_processes": len(index),
                "unique_secop_ii": len(eligible_keys),
                **{
                    key: summary[key]
                    for key in (
                        "unique_processes_total",
                        "unique_processes_recent",
                        "secop_ii_total",
                        "secop_ii_recent",
                        "secop_ii_open",
                        "secop_ii_closed",
                        "secop_ii_unknown",
                        "provider_status_deadline_conflicts",
                        "stale_processes",
                        "invalid_published_at",
                    )
                },
                **({"action": summary["action"]} if "action" in summary else {}),
            }
        )
    return exit_code
