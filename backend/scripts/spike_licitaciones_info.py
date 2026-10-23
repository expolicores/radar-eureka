"""Experimento aislado: archivos locales, extracción compartida y cero sesiones DB."""

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
import unicodedata
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.adapters.secop import SecopDownloader, validate_url
from public_procurement.extraction.adapters.hybrid import LocalOcrFallback
from public_procurement.extraction.adapters.isolated import IsolatedExtractor
from public_procurement.extraction.domain.content import (
    DocumentInput,
    EvidenceFragment,
    ExtractionLimits,
)
from public_procurement.extraction.ocr_config import load_ocr_policy
from public_procurement.extraction.services import ExtractionService
from public_procurement.extraction.structured_rules import extract_facts
from public_procurement.shared.config import Settings

ROOT = Path(__file__).resolve().parents[1]
SPIKE_ROOT = ROOT / ".local" / "spike_licitaciones_info"
COLUMNS = [
    "selecciones",
    "tipo_secop",
    "EntidadContratante",
    "Objeto",
    "valor_range",
    "modalidad_filter",
    "CodigoProceso",
    "estado_agrupado",
    "FechaPublicacion",
    "ubicacion_filter",
    "ganadores",
    "proponentes",
    "actividad_filter",
    "Grupo",
    "rapida",
]
PROCESS_FIELDS = (
    "idContrato",
    "id_fuente_contract",
    "idUltimaFase",
    "CodigoProceso",
    "EntidadContratante",
    "Objeto",
    "FechaPublicacion",
    "FechaVencimiento",
    "Valor",
    "TextoDepartamento",
    "Grupo",
    "UNSPSC",
    "NumeroDocumentos",
    "Link",
    "EstadoProceso",
    "modalidad",
    "key_config",
)


class SpikeError(Exception):
    """Errores seguros: nunca incluyen respuestas HTTP, headers o credenciales."""


def normalized(value: Any) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", str(value)).lower()
        if not unicodedata.combining(char)
    )


def rows(payload: Any) -> list[dict[str, Any]]:
    """Wrappers conocidos; rechaza cambios de contrato en vez de fingir lista vacía."""
    if isinstance(payload, list):
        if not all(isinstance(row, dict) for row in payload):
            raise SpikeError("Respuesta con filas inválidas.")
        return payload
    if isinstance(payload, dict) and not payload.get("error"):
        for key in ("data", "rows", "contratos", "documentos", "results"):
            if key in payload:
                return rows(payload[key])
    raise SpikeError("Contrato JSON desconocido; se necesita una muestra anonimizada.")


def parse_process_rows(payload: Any) -> list[dict[str, Any]]:
    result = []
    for row in rows(payload):
        if not row.get("idContrato"):
            raise SpikeError("Proceso sin idContrato.")
        if str(row.get("id_fuente_contract")) == "3" or row.get("key_config") == "secop2":
            result.append({key: row.get(key) for key in PROCESS_FIELDS})
    return result


def build_process_payload(locations: str, term: str, limit: int = 30) -> dict[str, Any]:
    if not 1 <= limit <= 30 or not re.fullmatch(r"\d+(,\d+)*", locations):
        raise SpikeError("Use 1–30 procesos y IDs de ubicación separados por comas.")
    return {
        "query": {"Objeto": term, "ubicacion_filter": locations},
        "limit": limit,
        "ascending": 0,
        "page": 1,
        "byColumn": 1,
        "orderBy": "FechaPublicacion",
        "columns": COLUMNS,
    }


@dataclass(frozen=True)
class SpikeDocument:
    original_name: str
    extension: str
    source_url: str
    document_id: str


def parse_document_rows(payload: Any) -> list[SpikeDocument]:
    result = []
    for row in rows(payload):

        def first(*keys, row=row):
            return next((row[key] for key in keys if row.get(key) is not None), "")

        name = str(first("nombre", "nombre_documento", "NombreDocumento", "Nombre", "name"))
        url = str(first("url", "URL", "Link", "link", "UrlDocumento", "url_documento"))
        validate_url(url)
        query = parse_qs(urlsplit(url).query)
        identifier = query.get("DocumentId", [""])[0]
        if not name or not identifier:
            raise SpikeError("Documento sin nombre o URL SECOP sin DocumentId.")
        extension = str(first("extension", "Extension", "tipo", "Tipo")).lower().lstrip(".")
        if extension not in ("pdf", "docx", "xlsx"):
            extension = Path(name).suffix.lower().lstrip(".")
        # La URL es la recibida, nunca se construye desde un identificador interno.
        result.append(SpikeDocument(name, extension, url, identifier))
    return result


def load_session(path: Path | None) -> dict[str, str]:
    config = {}
    if path:
        path = path.resolve()
        ignored = subprocess.run(  # noqa: S603 — argumentos fijos, sin shell
            ["git", "check-ignore", "--quiet", "--", str(path)],  # noqa: S607
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if ignored.returncode != 0:
            raise SpikeError("El archivo de sesión debe estar ignorado por Git.")
        config = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise SpikeError("El archivo de sesión debe ser un objeto JSON.")
    keys = (
        "LICITACIONES_BASE_URL",
        "LICITACIONES_COOKIE",
        "LICITACIONES_X_CSRF_TOKEN",
        "LICITACIONES_X_XSRF_TOKEN",
        "LICITACIONES_BOYACA_LOCATION_IDS",
        "LICITACIONES_PROFILE_ID",
    )
    return {key: os.environ.get(key, str(config.get(key, ""))) for key in keys}


class Client:
    def __init__(
        self,
        config: dict[str, str],
        *,
        transport=None,
        sleep=time.sleep,
        storage_state=None,
    ):
        self.sleep, self.requests, self.last = sleep, 0, None
        self.blocked = False
        if storage_state is not None:
            from licitaciones_auth import LOCAL, ORIGIN, BrowserSession

            if config["LICITACIONES_BASE_URL"] != ORIGIN:
                raise SpikeError("La sesión Playwright requiere https://col.licitaciones.info.")
            self.http = BrowserSession(storage_state, LOCAL / "request_headers.json")
            return
        base = urlsplit(config["LICITACIONES_BASE_URL"])
        if (
            base.scheme != "https"
            or not base.hostname
            or not (
                base.hostname == "licitaciones.info" or base.hostname.endswith(".licitaciones.info")
            )
            or base.username
            or base.password
            or base.port not in (None, 443)
            or base.path not in ("", "/")
            or base.query
            or base.fragment
        ):
            raise SpikeError("Configure el origen HTTPS real de Licitaciones.info, sin ruta.")
        if not config["LICITACIONES_COOKIE"]:
            raise SpikeError("Falta LICITACIONES_COOKIE; no se automatiza login ni CAPTCHA.")
        headers = {"Cookie": config["LICITACIONES_COOKIE"], "Accept": "application/json"}
        for variable, header in (
            ("LICITACIONES_X_CSRF_TOKEN", "X-CSRF-TOKEN"),
            ("LICITACIONES_X_XSRF_TOKEN", "X-XSRF-TOKEN"),
        ):
            if config[variable]:
                headers[header] = config[variable]
        origin = f"https://{base.netloc}"
        headers.update({"Origin": origin, "Referer": origin + "/cliente/contratos"})
        self.http = httpx.Client(
            base_url=origin,
            headers=headers,
            timeout=20,
            follow_redirects=False,
            transport=transport,
        )
        self.sleep, self.requests, self.last = sleep, 0, None
        self.blocked = False

    def reserve(self, count=1):
        # Techo total conservador. Cada descarga reserva hasta seis saltos SECOP.
        if self.requests + count > 60:
            raise SpikeError("Presupuesto de 60 requests agotado; inventario incompleto.")
        if self.last is not None:
            self.sleep(max(0, 2.1 - (time.monotonic() - self.last)))
        self.requests += count
        self.last = time.monotonic()

    def post(self, path: str, payload: dict[str, Any]):
        if self.blocked:
            raise SpikeError("Cliente detenido por autenticación o rate limit.")
        for attempt in range(2):
            self.reserve()
            try:
                response = self.http.post(path, json=payload)
            except httpx.TransportError:
                if attempt == 0:
                    continue
                raise SpikeError("Red no disponible; reintento agotado.") from None
            if response.is_redirect:
                from licitaciones_auth import safe_location

                print(
                    json.dumps(
                        {
                            "stage": "auth_redirect",
                            "status": response.status_code,
                            "location": safe_location(response.headers.get("location")),
                            "redirects_followed": False,
                        }
                    ),
                    flush=True,
                )
            if response.status_code in (401, 403, 419) or response.is_redirect:
                self.blocked = True
                raise SpikeError("Sesión expirada/no autorizada; renueve la sesión manualmente.")
            if response.status_code == 429:
                self.blocked = True
                raise SpikeError("Rate limit HTTP 429; detenido sin reintentos.")
            if response.status_code >= 500 and attempt == 0:
                continue
            if response.status_code != 200 or len(response.content) > 5 * 1024 * 1024:
                raise SpikeError(f"Respuesta HTTP {response.status_code} o tamaño inválido.")
            try:
                return response.json()
            except ValueError:
                raise SpikeError("Respuesta no JSON; revise la sesión manualmente.") from None
        raise SpikeError("Solicitud no completada.")


def fetch_processes(client, config, term, limit):
    profile = config["LICITACIONES_PROFILE_ID"] or "1086005"
    if not profile.isdigit():
        raise SpikeError("Perfil inválido.")
    payload = build_process_payload(config["LICITACIONES_BOYACA_LOCATION_IDS"], term, limit)
    received = rows(client.post(f"/cliente/contratos/get-info/MP?perfiles={profile}", payload))
    if len(received) > limit:
        raise SpikeError("La fuente ignoró el límite de procesos; se cancela el spike.")
    processes = parse_process_rows(received)
    unique = {}
    for process in processes:
        if normalized(process["TextoDepartamento"]).strip() != "boyaca":
            continue
        unique[str(process["idContrato"])] = process
    return list(unique.values()), len(received)


def fetch_documents(client, process):
    seen_pages, documents = set(), {}
    for page in range(1, 11):
        payload = {
            key: process[key] for key in ("idContrato", "id_fuente_contract", "idUltimaFase")
        }
        if any(value is None for value in payload.values()):
            raise SpikeError("Faltan identificadores para consultar documentos.")
        received = rows(
            client.post(
                "/cliente/contratos/obtener-documentos-proceso",
                {**payload, "page": page},
            )
        )
        if not received:
            return list(documents.values())
        parsed = parse_document_rows(received)
        signature = tuple(document.document_id for document in parsed)
        if signature in seen_pages:
            raise SpikeError("Paginación documental repetida; inventario incompleto.")
        seen_pages.add(signature)
        for document in parsed:
            documents[document.document_id] = document
    raise SpikeError("Límite de diez páginas documentales; inventario incompleto.")


def select_documents(documents, limit):
    priorities = (
        "invitacion",
        "estudios previos",
        "especificaciones",
        "anexo tecnico",
        "ficha tecnica",
    )

    def priority(document):
        name = normalized(document.original_name)
        return next((index for index, term in enumerate(priorities) if term in name), 99)

    return sorted(
        (
            document
            for document in documents
            if document.extension in ("pdf", "docx", "xlsx") and priority(document) != 99
        ),
        key=priority,
    )[:limit]


def deny_database(*args, **kwargs):
    raise AssertionError("El spike no permite abrir sesiones de base de datos.")


class LocalSource:
    def __init__(self, document, storage, stored):
        self.document, self.storage, self.stored = document, storage, stored

    def for_document(self, reference):
        return self.document

    @contextmanager
    def open_version(self, version_id, max_bytes):
        if version_id != self.document.document_version_id:
            raise SpikeError("Versión local desconocida.")
        with self.storage.open_verified(
            self.stored.storage_path,
            self.stored.sha256,
            self.stored.observed_size,
            max_bytes,
        ) as stream:
            yield stream


def download_document(client, document, storage, settings):
    client.reserve(6)
    if Path(document.original_name).suffix.lower() != f".{document.extension}":
        document = replace(document, original_name=f"{document.original_name}.{document.extension}")
    return SecopDownloader(
        min(settings.document_timeout_seconds, 60),
        min(settings.document_max_bytes, 20 * 1024 * 1024),
    ).download(document, storage)


def run_existing_extractor(document, stored, storage, settings):
    name = document.original_name
    if Path(name).suffix.lower() != f".{document.extension}":
        name += f".{document.extension}"
    input_document = DocumentInput(
        uuid.uuid4(), uuid.uuid4(), name, stored.sha256, stored.observed_size
    )
    source = LocalSource(input_document, storage, stored)
    limits = ExtractionLimits(
        max_bytes=min(settings.extraction_max_bytes, 20 * 1024 * 1024),
        timeout_seconds=settings.extraction_timeout_seconds,
        max_chars=settings.extraction_max_chars,
        max_fragments=settings.extraction_max_fragments,
        max_pages=settings.extraction_max_pages,
    )
    fallback = (
        LocalOcrFallback(
            source,
            limits,
            load_ocr_policy(settings.extraction_ocr_config_path),
            settings.extraction_tesseract_cmd,
            settings.extraction_tessdata_path,
        )
        if settings.extraction_ocr_enabled
        else None
    )
    service = ExtractionService(
        deny_database,
        source,
        IsolatedExtractor(source, limits),
        limits,
        fallback,
    )
    started = time.monotonic()
    result = service.extract_document("local", dry_run=True)
    run_id = uuid.uuid4()
    evidence = [
        EvidenceFragment(
            uuid.uuid4(),
            input_document.document_version_id,
            run_id,
            name,
            fragment.ordinal,
            fragment.text,
            fragment.source_locator,
        )
        for fragment in result.fragments
    ]
    methods = {fragment.source_locator.get("extraction_method") for fragment in result.fragments}
    mode = (
        "mixed"
        if "ocr_text" in methods and len(methods) > 1
        else ("ocr" if "ocr_text" in methods else "native")
    )
    return {
        "name": name,
        "url": document.source_url,
        "document_id": document.document_id,
        "sha256": stored.sha256,
        "storage_path": stored.storage_path,
        "status": result.status.value,
        "error_code": result.error_code,
        "extraction_mode": mode,
        "text_length": result.text_length,
        "page_count": result.page_count,
        "ocr_pages": result.diagnostics.get("processed_pages", []),
        "diagnostics": result.diagnostics,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "fragments": [asdict(fragment) for fragment in result.fragments],
    }, evidence


def summarize_result(process_id, evidence):
    facts = extract_facts(process_id, evidence)
    groups = {
        "products_found": {"purchase_item", "item_description", "brand", "product", "presentation"},
        "commercial_terms_found": {
            "quantity",
            "unit_price_cop",
            "total_cop",
            "official_budget_cop",
        },
        "experience_requirements": {"experience"},
        "payment_terms": {"payment_term", "payment_method", "payment_percentage"},
        "execution_terms": {"execution_term", "delivery_count", "delivery_location"},
        "guarantees": {"guarantee"},
        "other_restrictions": {"rup"},
    }
    serialized = [asdict(fact) for fact in facts]
    return {
        **{
            key: [fact for fact in serialized if fact["fact_type"] in types]
            for key, types in groups.items()
        },
        "structured_facts": serialized,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=["Boyaca", "Boyacá"], default="Boyaca")
    parser.add_argument("--object", default="refrigerio", dest="term")
    parser.add_argument("--max-processes", type=int, choices=range(1, 31), default=30)
    parser.add_argument("--max-document-processes", type=int, choices=range(1, 4), default=3)
    parser.add_argument("--max-documents", type=int, choices=range(1, 3), default=2)
    parser.add_argument("--session-file", type=Path)
    parser.add_argument("--storage-state", type=Path)
    parser.add_argument("--auth-check-only", action="store_true")
    parser.add_argument(
        "--location-ids-file",
        type=Path,
        default=ROOT / "scripts" / ".local" / "licitaciones_boyaca_ids.txt",
    )
    args = parser.parse_args(argv)
    client = None
    try:
        config = load_session(args.session_file)
        if not config["LICITACIONES_BOYACA_LOCATION_IDS"]:
            if not args.location_ids_file.is_file():
                raise SpikeError("Falta el archivo local con IDs de ubicación de Boyacá.")
            config["LICITACIONES_BOYACA_LOCATION_IDS"] = args.location_ids_file.read_text(
                encoding="utf-8-sig",
            ).strip()
        # Validar datos locales antes de efectuar cualquier llamada.
        build_process_payload(
            config["LICITACIONES_BOYACA_LOCATION_IDS"], args.term, args.max_processes
        )
        client = (
            Client(config, storage_state=args.storage_state)
            if args.storage_state
            else Client(config)
        )
        if args.auth_check_only:
            profile = config["LICITACIONES_PROFILE_ID"] or "1086005"
            if not profile.isdigit():
                raise SpikeError("Perfil inválido.")
            client.post(
                f"/cliente/contratos/get-info/MP?perfiles={profile}",
                build_process_payload(
                    config["LICITACIONES_BOYACA_LOCATION_IDS"], args.term, args.max_processes
                ),
            )
            print("get-info: 200 JSON. No se ejecutaron inventarios ni descargas.")
            return 0
        settings = Settings(_env_file=ROOT / ".env", database_url="disabled://spike-no-database")
        SPIKE_ROOT.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="run-", dir=SPIKE_ROOT))
        storage = LocalBinaryStorage(output / "binaries")
        processes, received = fetch_processes(client, config, args.term, args.max_processes)
        report = {
            "source": "licitaciones_info",
            "records_received": received,
            "region": "Boyacá",
            "object": args.term,
            "processes": [],
        }
        for index, process in enumerate(processes):
            entry = {
                "source": "licitaciones_info",
                "process": process,
                "documents": [],
                "errors": [],
                "document_inventory": [],
                "document_status": "not_requested",
            }
            evidence = []
            if index < args.max_document_processes:
                try:
                    documents = fetch_documents(client, process)
                    entry["document_inventory"] = [asdict(document) for document in documents]
                    entry["document_status"] = "available" if documents else "empty"
                    for document in select_documents(documents, args.max_documents):
                        try:
                            stored = download_document(client, document, storage, settings)
                            detail, fragments = run_existing_extractor(
                                document, stored, storage, settings
                            )
                            entry["documents"].append(detail)
                            evidence.extend(fragments)
                        except Exception as error:
                            entry["errors"].append(
                                {
                                    "stage": "document",
                                    "type": type(error).__name__,
                                    "document_id": document.document_id,
                                }
                            )
                except Exception as error:
                    entry["document_status"] = "error"
                    entry["errors"].append({"stage": "inventory", "type": type(error).__name__})
            entry["signals"] = summarize_result(uuid.uuid4(), evidence)
            report["processes"].append(entry)
            print(json.dumps(process, ensure_ascii=True, default=str))
            (output / "results.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        report["request_budget_used"] = client.requests
        (output / "results.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"Procesos SECOP II/Boyaca: {len(processes)}; JSON: {output / 'results.json'}")
        return 0
    except Exception as error:
        print(
            str(error)
            if isinstance(error, SpikeError)
            else f"Spike detenido: {type(error).__name__}."
        )
        return 1
    finally:
        if client:
            client.http.close()


if __name__ == "__main__":
    raise SystemExit(main())
