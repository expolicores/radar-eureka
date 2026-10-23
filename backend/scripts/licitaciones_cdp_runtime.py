"""Bounded experimental CDP transport and parsing; no product integration."""

import json
import re
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlsplit

from licitaciones_event_time import timed_warning
from observe_licitaciones_cdp import validate_cdp_url as validate_cdp_url
from spike_licitaciones_info import (
    COLUMNS,
    ROOT,
    SpikeError,
    build_process_payload,
    normalized,
    parse_document_rows,
)

LOCAL = ROOT / ".local" / "spike_licitaciones_info"
ORIGIN = "https://col.licitaciones.info"
IDS_FILE = ROOT / "scripts" / ".local" / "licitaciones_boyaca_ids.txt"
DOCUMENT_ENDPOINT = "/cliente/contratos/obtener-documentos-proceso"
POLICY_PATH = ROOT / "scripts" / "licitaciones_fact_policy.v1.json"
SESSION_ENRICHED_RATIO_MIN = 0.8
MANUAL_LOGIN = (
    "Inicia sesión manualmente y vuelve a ejecutar. "
    "Abre Contratos desktop desde el perfil Vila Frontier en el mismo Edge CDP."
)


class CandidateError(SpikeError):
    EXIT_CODES: ClassVar[dict[str, int]] = {
        "cdp_unavailable": 10,
        "invalid_tab": 11,
        "session_expired": 12,
        "profile_unavailable": 13,
        "invalid_get_info": 14,
        "preflight_failed": 15,
        "generic_dataset": 16,
        "invalid_response": 17,
        "insufficient_enriched_rows": 18,
        "insufficient_secop_sample": 19,
    }

    def __init__(self, code, message, criterion=None):
        super().__init__(message)
        self.code = code
        self.exit_code = self.EXIT_CODES[code]
        self.criterion = criterion


def connect_browser(playwright, endpoint):
    try:
        return playwright.chromium.connect_over_cdp(endpoint, timeout=10000)
    except Exception as error:
        raise CandidateError(
            "cdp_unavailable", "CDP no disponible. Abre Edge con scripts/licitaciones_cdp_open.py."
        ) from error


def find_page(browser):
    pages = [
        page
        for context in browser.contexts
        for page in context.pages
        if urlsplit(page.url).scheme == "https"
        and urlsplit(page.url).hostname == "col.licitaciones.info"
        and urlsplit(page.url).path.rstrip("/") == "/cliente/contratos"
    ]
    if len(pages) != 1:
        raise CandidateError(
            "invalid_tab", "Se requiere una unica pestana desktop de Contratos. " + MANUAL_LOGIN
        )
    return pages[0]


def load_payload(path: Path, term: str, limit: int):
    ids = path.read_text(encoding="utf-8-sig").strip()
    parts = ids.split(",")
    if len(parts) != 123 or len(set(parts)) != 123:
        raise SpikeError("El archivo local debe contener los 123 IDs unicos de Boyaca.")
    if not term.strip() or len(term) > 200:
        raise SpikeError("Objeto vacio o demasiado largo.")
    return build_process_payload(ids, term, limit)


class PageClient:
    """Use the app's existing axios instance; never copy authentication state."""

    def __init__(self, page, profile_id, event):
        self.page, self.profile_id, self.event = page, profile_id, event
        self.requests = 0
        self.last = None
        self.last_get_info_diagnostic = None

    def reserve(self, count=1):
        if self.requests + count > 60:
            raise SpikeError("Presupuesto experimental de 60 requests agotado.")
        if self.last is not None:
            # Pump CDP while throttling; do not freeze browser event delivery.
            self.page.wait_for_timeout(max(0, 2100 - (time.monotonic() - self.last) * 1000))
        self.requests += count
        self.last = time.monotonic()

    def call(self, method, path, payload=None):
        discovery = f"/cliente/contratos/get-info/MP?perfiles={self.profile_id}"
        if (method, path) not in {
            ("GET", "/cliente/get-config-user"),
            ("POST", discovery),
            ("POST", DOCUMENT_ENDPOINT),
        }:
            raise SpikeError("Endpoint fuera del alcance experimental.")
        if urlsplit(self.page.url).hostname != "col.licitaciones.info":
            raise CandidateError("invalid_tab", "La pestaña cambio de host. " + MANUAL_LOGIN)
        self.reserve()
        # No values from axios defaults, cookies, headers or browser storage cross CDP.
        result = self.page.evaluate(
            """async ({method,path,payload}) => {
              if (location.origin !== 'https://col.licitaciones.info' ||
                  typeof window.axios?.request !== 'function') return {status:null};
              try {
                const r = await window.axios.request({method,url:path,data:payload,timeout:20000});
                const ct = String(r.headers['content-type'] ?? '');
                const final = r.request?.responseURL ? new URL(r.request.responseURL) : null;
                const sameEndpoint = final && final.origin === location.origin &&
                  final.pathname === new URL(path,location.origin).pathname &&
                  (!path.includes('/get-info/') ||
                    final.searchParams.get('perfiles') ===
                      new URL(path,location.origin).searchParams.get('perfiles'));
                // Bootstrap response can contain user details: keep them in the page.
                const bootstrap = path === '/cliente/get-config-user';
                return {status:r.status,json:ct.includes('json'),sameEndpoint,
                  data:bootstrap ? null : r.data,
                  configObject:bootstrap && !!r.data && typeof r.data==='object' &&
                    !Array.isArray(r.data) && r.data.status!==false && !r.data.error};
              } catch(e) {return {status:e.response?.status??null,
                timeout:['ECONNABORTED','ETIMEDOUT'].includes(e.code)};}
            }""",
            {"method": method, "path": path, "payload": payload},
        )
        stage = (
            "documents"
            if path == DOCUMENT_ENDPOINT
            else "preflight"
            if method == "GET" or payload.get("query") == {}
            else "discovery"
        )
        self.event({"stage": stage, "method": method, "path": path, "status": result["status"]})
        if path == discovery:
            self.last_get_info_diagnostic = get_info_diagnostic(
                result.get("data"), payload, result, urlsplit(self.page.url).hostname
            )
        if result.get("status") in (401, 419):
            raise CandidateError(
                "session_expired", "Sesion expirada o no aceptada. " + MANUAL_LOGIN
            )
        if path == discovery and result.get("status") in (403, 404):
            raise CandidateError(
                "profile_unavailable",
                "El endpoint del perfil no esta disponible. "
                "Selecciona Vila Frontier desde la UI y vuelve a ejecutar.",
            )
        if result.get("status") != 200 or not result.get("json") or not result.get("sameEndpoint"):
            code = "invalid_response" if path == discovery else "preflight_failed"
            error = CandidateError(
                code,
                "La API no devolvio 200 JSON en el endpoint esperado. Revisa el diagnostico."
                if path == discovery
                else "Preflight no disponible. " + MANUAL_LOGIN,
                criterion="status_not_200_or_not_json_or_endpoint_mismatch",
            )
            # Public transport metadata only; the plan owns its bounded retry policy.
            error.http_status = result.get("status")
            error.transient = result.get("timeout") is True or (
                isinstance(error.http_status, int) and 500 <= error.http_status <= 599
            )
            raise error
        return result

    def bootstrap(self):
        response = self.call("GET", "/cliente/get-config-user")
        if not response.get("configObject"):
            raise CandidateError(
                "preflight_failed", "Configuracion de usuario no reconocida. " + MANUAL_LOGIN
            )
        return {"get_config_user_status": 200}

    def post(self, path, payload):
        return self.call("POST", path, payload)["data"]


def get_info_diagnostic(body, payload, transport, host):
    """Public response summary only; never headers, browser state or full response."""
    rows = body.get("data") if isinstance(body, dict) else None
    dictionaries = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    return {
        "stage": "preflight_diagnostic",
        "host": host,
        "status": transport.get("status"),
        "json": transport.get("json"),
        "same_endpoint": transport.get("sameEndpoint"),
        "payload": payload,
        "limit_requested": payload.get("limit"),
        "page_requested": payload.get("page"),
        "count": body.get("count") if isinstance(body, dict) else None,
        "rows_received": len(rows) if isinstance(rows, list) else None,
        "first_three_codigo_proceso": [row.get("CodigoProceso") for row in dictionaries[:3]],
        "id_fuente_contract": {
            "present": sum("id_fuente_contract" in row for row in dictionaries),
            "non_null": sum(row.get("id_fuente_contract") is not None for row in dictionaries),
        },
        "key_config": {
            "present": sum("key_config" in row for row in dictionaries),
            "non_empty": sum(bool(row.get("key_config")) for row in dictionaries),
        },
    }


def classify_preflight_source(row):
    """Classify source independently of the fields later tested for enrichment.

    Only exact official hosts or full recognized process identifiers are evidence.
    Provider source IDs, key_config and unvalidated EsSecop flags are not evidence.
    """
    link = row.get("Link")
    try:
        parsed = urlsplit(link.strip()) if isinstance(link, str) else None
        host = parsed.hostname.lower() if parsed and parsed.hostname else None
        valid_url = bool(
            parsed and parsed.scheme in {"http", "https"} and host and not parsed.username
        )
    except ValueError:
        host, valid_url = None, False
    official_hosts = {"community.secop.gov.co", "www.contratos.gov.co", "contratos.gov.co"}
    identifiers = (row.get("idUltimaFase"), row.get("noticeUID"), row.get("CodigoProceso"))
    recognized_id = any(
        isinstance(value, str) and re.fullmatch(r"CO1\.(?:NTC|REQ)\.\d+", value.strip())
        for value in identifiers
    )
    if (valid_url and host in official_hosts) or recognized_id:
        return "secop_candidate"
    if valid_url:
        return "external_candidate"
    return "unknown_source"


def validate_session_response(body, requested_limit, *, validate_dates=True, scope_secop=True):
    """Session health tolerates provider page size and heterogeneous source rows.

    Commercial discovery retains its separate strict contract/limits.
    """
    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        raise CandidateError(
            "invalid_response",
            "get-info no contiene una lista JSON valida.",
            criterion="body_not_object_or_data_not_list",
        )
    rows = body["data"]
    try:
        if isinstance(body.get("count"), bool) or int(body["count"]) < 0:
            raise ValueError
        count = int(body["count"])
    except (KeyError, TypeError, ValueError) as error:
        raise CandidateError(
            "invalid_response", "count de get-info no reconocido.", criterion="invalid_count"
        ) from error
    if count == 1337370:
        raise CandidateError(
            "generic_dataset",
            "get-info devolvio el universo generico conocido.",
            criterion="known_generic_count_1337370",
        )
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise CandidateError(
            "invalid_response",
            "get-info sin filas o con filas no reconocidas.",
            criterion="empty_or_non_object_rows",
        )
    required = {"CodigoProceso", "FechaPublicacion", "id_fuente_contract", "key_config"}
    if not validate_dates:
        # Discovery dates are preserved and classified by local freshness.
        required.remove("FechaPublicacion")
    fields = set().union(*(row.keys() for row in rows))
    if (not scope_secop and not required <= fields) or (
        scope_secop and not fields.intersection({"Objeto", "FechaPublicacion", "idContrato"})
    ):
        raise CandidateError(
            "invalid_response",
            "get-info no expone los campos esperados.",
            criterion="expected_fields_not_present",
        )
    classifications = [classify_preflight_source(row) for row in rows]
    population = (
        [
            row
            for row, source in zip(rows, classifications, strict=True)
            if source == "secop_candidate"
        ]
        if scope_secop
        else rows
    )
    enriched = []
    for row in population:
        if (
            not required <= row.keys()
            or not row.get("CodigoProceso")
            or row.get("id_fuente_contract") is None
            or not row.get("key_config")
        ):
            continue
        if validate_dates:
            try:
                datetime.fromisoformat(str(row["FechaPublicacion"]).replace("Z", "+00:00"))
            except ValueError:
                continue
        enriched.append(row)
    ratio = len(enriched) / len(population) if population else None
    warnings = (
        [
            timed_warning(
                {
                    "code": "provider_ignores_limit",
                    "requested_limit": requested_limit,
                    "rows_received": len(rows),
                }
            )
        ]
        if len(rows) > requested_limit
        else []
    )
    quality = {
        "rows_total": len(rows),
        "secop_candidates": classifications.count("secop_candidate"),
        "external_candidates": classifications.count("external_candidate"),
        "unknown_source_rows": classifications.count("unknown_source"),
        "rows_received": len(rows),
        "enriched_rows": len(enriched),
        "enriched_ratio": ratio,
        "min_enriched_ratio": SESSION_ENRICHED_RATIO_MIN,
        "warnings": warnings,
    }
    if scope_secop:
        quality.update(
            secop_enriched=len(enriched),
            secop_unenriched=len(population) - len(enriched),
            secop_enriched_ratio=ratio,
        )
    if not population:
        quality.update(preflight_status="inconclusive", reason="insufficient_secop_sample")
        error = CandidateError(
            "insufficient_secop_sample",
            "Preflight inconcluso: no hay muestra SECOP identificable; no se solicita otro login.",
            criterion="no_independently_identified_secop_rows",
        )
        error.quality = quality
        raise error
    if ratio < SESSION_ENRICHED_RATIO_MIN:
        quality.update(preflight_status="unhealthy_response", reason="insufficient_enriched_rows")
        error = CandidateError(
            "insufficient_enriched_rows",
            "Proporcion de filas enriquecidas inferior al 80%; no se solicita otro login.",
            criterion="enriched_ratio_below_0_8",
        )
        error.quality = quality
        raise error
    return {
        **quality,
        "preflight_status": "healthy",
        "reason": "secop_enrichment_threshold_met" if scope_secop else "enrichment_threshold_met",
        "latest_published_at_observed": enriched[0].get("FechaPublicacion"),
    }


def validate_aggregator_response(body, requested_limit):
    """Same 80% quality threshold, measured on useful aggregator metadata, not origin."""
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("data"), list)
        or not str(body.get("count", "")).isdigit()
    ):
        raise CandidateError("invalid_response", "Respuesta JSON invalida.")
    if str(body["count"]) == "1337370":
        raise CandidateError("generic_dataset", "Universo generico conocido.")
    rows = body["data"]
    if not rows or any(not isinstance(r, dict) for r in rows):
        raise CandidateError("invalid_response", "Filas vacias o invalidas.")
    enriched = [
        r
        for r in rows
        if (r.get("idContrato") or r.get("CodigoProceso"))
        and all(
            isinstance(r.get(k), str) and r[k].strip()
            for k in ("Objeto", "TextoDepartamento", "FechaPublicacion")
        )
    ]
    dated = []
    for row in enriched:
        try:
            datetime.fromisoformat(row["FechaPublicacion"].replace("Z", "+00:00"))
            dated.append(row)
        except ValueError:
            continue
    enriched = dated
    ratio = len(enriched) / len(rows)
    if ratio < SESSION_ENRICHED_RATIO_MIN:
        raise CandidateError(
            "insufficient_enriched_rows",
            "Metadata util inferior al 80%.",
            criterion="aggregator_metadata_ratio_below_0_8",
        )
    return {
        "preflight_status": "healthy",
        "reason": "aggregator_metadata_threshold_met",
        "rows_total": len(rows),
        "rows_received": len(rows),
        "enriched_rows": len(enriched),
        "enriched_ratio": ratio,
        "min_enriched_ratio": SESSION_ENRICHED_RATIO_MIN,
        "warnings": [timed_warning({"code": "provider_ignores_limit"})]
        if len(rows) > requested_limit
        else [],
    }


def check_session(client, profile_id, *, aggregator=False):
    bootstrap = client.bootstrap()
    # Health probe only: no commercial discovery, persistence, candidate filtering or OCR.
    payload = {
        "query": {},
        "limit": 30,
        "ascending": 0,
        "page": 1,
        "byColumn": 1,
        "orderBy": "FechaPublicacion",
        "columns": COLUMNS,
    }
    try:
        body = client.post(f"/cliente/contratos/get-info/MP?perfiles={profile_id}", payload)
        quality = (validate_aggregator_response if aggregator else validate_session_response)(
            body, payload["limit"]
        )
    except CandidateError as error:
        if isinstance(client, PageClient) and client.last_get_info_diagnostic is not None:
            client.last_get_info_diagnostic.update(
                error_code=error.code,
                invalid_criterion=error.criterion,
                preflight_status="session_expired"
                if error.code == "session_expired"
                else "unhealthy_response",
                reason=error.code,
            )
            client.last_get_info_diagnostic.update(getattr(error, "quality", {}))
            client.event(client.last_get_info_diagnostic)
        raise
    if isinstance(client, PageClient) and client.last_get_info_diagnostic is not None:
        client.last_get_info_diagnostic.update(error_code=None, invalid_criterion=None, **quality)
        client.event(client.last_get_info_diagnostic)
    for warning in quality["warnings"]:
        if isinstance(client, PageClient):
            client.event({"stage": "preflight", "level": "warning", **warning})
    return {
        **bootstrap,
        "profile_id": profile_id,
        "profile_available": True,
        "get_info_status": 200,
        "enriched_verified": True,
        **quality,
        "verification": "profile_scoped_get_info_probe",
    }


def validate_discovery(body, limit, *, validate_dates=True):
    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        raise CandidateError(
            "invalid_get_info",
            "Contrato get-info desconocido. " + MANUAL_LOGIN,
            criterion="body_not_object_or_data_not_list",
        )
    rows = body["data"]
    try:
        if isinstance(body.get("count"), bool) or int(body["count"]) < 0:
            raise ValueError
    except (KeyError, TypeError, ValueError) as error:
        raise CandidateError(
            "invalid_get_info",
            "count de get-info no reconocido.",
            criterion="count_missing_boolean_negative_or_not_integer",
        ) from error
    if str(body.get("count")) == "1337370" or len(rows) > limit:
        raise CandidateError(
            "invalid_get_info",
            "Universo generico o limite ignorado. " + MANUAL_LOGIN,
            criterion="known_generic_count_1337370"
            if str(body.get("count")) == "1337370"
            else "rows_received_exceeds_requested_limit",
        )
    for row in rows:
        if not isinstance(row, dict) or not row.get("idContrato"):
            raise CandidateError(
                "invalid_get_info",
                "Fila get-info sin identidad.",
                criterion="row_not_object_or_missing_id_contrato",
            )
        if not isinstance(row.get("Objeto"), str) or not isinstance(
            row.get("TextoDepartamento"), str
        ):
            raise CandidateError(
                "invalid_get_info",
                "Metadata get-info incompleta.",
                criterion="object_or_department_not_string",
            )
        if not validate_dates:
            continue
        try:
            datetime.fromisoformat(str(row["FechaPublicacion"]).replace("Z", "+00:00"))
        except (ValueError, KeyError) as error:
            raise CandidateError(
                "invalid_get_info",
                "FechaPublicacion no reconocida.",
                criterion="published_at_not_parseable",
            ) from error
    # Empty is a valid filtered result, but cannot prove enriched/current data.
    return rows


def filter_processes(rows, term):
    eligible, excluded, seen = [], [], set()
    for row in rows:
        reason = None
        if normalized(row.get("TextoDepartamento", "")).split(":")[0].strip() != "boyaca":
            reason = "outside_boyaca"
        elif normalized(term) not in normalized(row.get("Objeto", "")):
            reason = "object_mismatch"
        elif str(row["idContrato"]) in seen:
            reason = "duplicate"
        if reason:
            excluded.append({"idContrato": row.get("idContrato"), "reason": reason})
        else:
            seen.add(str(row["idContrato"]))
            eligible.append(dict(row))
    return eligible, excluded


class _TableMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.images = [], []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
        if tag == "img" and attributes.get("src"):
            self.images.append(attributes["src"])


def parse_document_page(body):
    if not isinstance(body, dict) or body.get("status") != 1:
        raise SpikeError("Estado documental desconocido; no se interpreta como inventario vacio.")
    table = body.get("documentos")
    if table == []:
        return []
    if not isinstance(table, dict) or table.get("encabezados") != [
        "Item",
        "Nombre",
        "Tipo",
        "Documento",
    ]:
        raise SpikeError("Contrato de tabla documental desconocido.")
    rows = table.get("campos")
    if not isinstance(rows, list):
        raise SpikeError("Filas documentales desconocidas.")
    converted = []
    for row in rows:
        if not isinstance(row, list) or len(row) != 5 or not isinstance(row[2], str):
            raise SpikeError("Fila documental invalida.")
        link, image = _TableMarkup(), _TableMarkup()
        link.feed(row[4])
        image.feed(row[3])
        if len(link.links) != 1 or len(image.images) != 1:
            raise SpikeError("Enlace o formato documental ambiguo.")
        extension = re.fullmatch(r"/img/extensiones/([a-z0-9]+)\.svg", image.images[0])
        if not extension:
            raise SpikeError("Formato documental desconocido.")
        converted.append({"nombre": row[2], "extension": extension[1], "url": link.links[0]})
    return parse_document_rows(converted)


def fetch_inventory(client, process):
    documents, signatures = {}, set()
    for page in range(1, 11):
        payload = {
            key: process.get(key) for key in ("idContrato", "id_fuente_contract", "idUltimaFase")
        }
        if any(value is None for value in payload.values()):
            raise SpikeError("Faltan identificadores documentales.")
        parsed = parse_document_page(client.post(DOCUMENT_ENDPOINT, {**payload, "page": page}))
        if not parsed:
            return list(documents.values())
        signature = tuple(doc.document_id for doc in parsed)
        if signature in signatures:
            raise SpikeError("Pagina documental repetida; inventario incompleto.")
        signatures.add(signature)
        for document in parsed:
            documents[document.document_id] = document
    raise SpikeError("Limite de diez paginas; inventario incompleto.")


def coverage(detail):
    diagnostics = detail.get("diagnostics", {})
    total = detail.get("page_count", 0)
    required = diagnostics.get("required_pages", [])
    successful = diagnostics.get("successful_pages", diagnostics.get("processed_pages", []))
    truncated = diagnostics.get("status") == "ocr_truncated" or bool(
        diagnostics.get("omitted_pages")
    )
    native = {
        item["page_number"]
        for item in diagnostics.get("native_quality", [])
        if item.get("status") == "native_text_ok"
    }
    if not native:
        native = {
            f.get("source_locator", {}).get("page_number", f.get("page_number"))
            for f in detail.get("fragments", [])
            if f.get("source_locator", {}).get("extraction_method") == "native_pdf_text"
        } - {None}
    processed = sorted(native | set(successful))
    complete = (
        bool(diagnostics.get("coverage_complete", detail.get("status") == "completed"))
        and not truncated
    )
    return {
        "extraction_status": "ocr_truncated" if truncated else detail.get("status"),
        "total_pages": total,
        "processed_pages": processed,
        "ocr_processed_pages": diagnostics.get("processed_pages", []),
        "ocr_required_pages": required,
        "ocr_omitted_pages": diagnostics.get("omitted_pages", []),
        "coverage_ratio": round(len(processed) / total, 4) if total else None,
        "coverage_complete": complete,
        "ocr_truncated": truncated,
    }


def annotate_facts(facts, incomplete_versions, policy):
    """Review-only annotations. Preserve values, evidence and original confidence."""
    annotated = []
    for fact in facts:
        result, reasons = dict(fact), []
        kind, value = fact.get("fact_type"), fact.get("numeric_value")
        bounds = policy["numeric_ranges"].get(kind)
        if kind == "presentation":
            bounds = policy["presentation_ranges"].get(str(fact.get("unit", "")).lower())
            if not bounds and value is not None:
                reasons.append("unrecognized_presentation_unit")
        if bounds and value is not None:
            try:
                number = float(value)
                if not bounds[0] <= number <= bounds[1]:
                    reasons.append("numeric_value_outside_review_range")
            except (ValueError, TypeError, OverflowError):
                reasons.append("invalid_numeric_value")
        evidence = fact.get("evidence_text", "")
        sources = fact.get("source_locator", {}).get("sources", [])
        if not evidence.strip() or not sources:
            reasons.append("insufficient_evidence_or_provenance")
        if kind in {"product", "purchase_item", "item_description"}:
            tokens = re.findall(r"[a-z0-9]+", normalized(fact.get("string_value") or ""))
            evidence_tokens = set(re.findall(r"[a-z0-9]+", normalized(evidence)))
            if not tokens or not set(tokens) <= evidence_tokens:
                reasons.append("product_not_supported_by_evidence")
        partial = str(fact.get("document_version_id")) in incomplete_versions
        result.update(
            suspicious=bool(reasons),
            suspicious_reasons=reasons,
            original_confidence=fact.get("confidence"),
            document_coverage_complete=not partial,
            usable_as_complete_evidence=not partial and not reasons,
            review_policy_version=policy["version"],
        )
        if reasons:
            result["confidence"] = str(
                min(float(fact.get("confidence") or 0), policy["suspicious_confidence_max"])
            )
        annotated.append(result)
    return annotated


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    temporary.replace(path)


def summarize_run(discovery, documents, extraction, errors, warnings):
    details = [d for process in extraction for d in process["documents"]]
    facts = [fact for process in extraction for fact in process["facts"]]
    return {
        "processes_found": len(discovery.get("processes", [])),
        "provider_count": discovery.get("count"),
        "secop_ii_eligible": len(discovery.get("eligible", [])),
        "processes_analyzed": len(documents),
        "documents_downloaded": sum(len(p["downloads"]) for p in documents),
        "documents_extracted": len(details),
        "extraction_modes": {
            mode: sum(d["extraction_mode"] == mode for d in details)
            for mode in ("native", "ocr", "mixed")
        },
        "ocr_truncated": sum(d["ocr_truncated"] for d in details),
        "full_coverage_documents": sum(bool(d.get("coverage_complete")) for d in details),
        "partial_coverage_documents": sum(not d.get("coverage_complete", False) for d in details),
        "native_documents": sum(d["extraction_mode"] == "native" for d in details),
        "ocr_documents": sum(d["extraction_mode"] == "ocr" for d in details),
        "mixed_documents": sum(d["extraction_mode"] == "mixed" for d in details),
        "facts_found": len(facts),
        "raw_facts_found": sum(p.get("raw_fact_count", len(p["facts"])) for p in extraction),
        "facts_deduplicated": sum(p.get("raw_fact_count", len(p["facts"])) for p in extraction)
        - len(facts),
        "suspicious_facts": sum(f["suspicious"] for f in facts),
        "errors": errors,
        "warnings": warnings,
    }
