"""Existing validated acquisition code, bound to a single manual CDP worker."""

import importlib
import json
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from public_procurement.documents.services import SourceDocument

BACKEND = Path(__file__).resolve().parents[3]
SCRIPTS = BACKEND / "scripts"


def validated_modules() -> dict[str, ModuleType]:
    # Fixed repository-owned files, never paths supplied by HTTP clients.
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return {
        name: importlib.import_module("licitaciones_" + name)
        for name in ("cdp_runtime", "search_plan", "freshness", "validity", "sources")
    }


class SourceUnavailableError(RuntimeError):
    def __init__(self, code: str, preflight: dict[str, Any] | None = None) -> None:
        super().__init__("Preflight o fuente no disponible")
        self.code = code
        self.preflight = preflight or {}


class LicitacionesInfoSource:
    def __init__(self, observer: Callable[[str, dict[str, Any]], None]) -> None:
        self.observer = observer
        self.modules = validated_modules()
        self.processes: dict[str, dict[str, Any]] = {}

    def __enter__(self) -> "LicitacionesInfoSource":
        from playwright.sync_api import sync_playwright

        self.context = sync_playwright().start()
        runtime = self.modules["cdp_runtime"]
        try:
            self.browser = runtime.connect_browser(self.context, "http://127.0.0.1:9222")
            self.page = runtime.find_page(self.browser)
        except Exception:
            self.context.stop()
            raise
        self.client = runtime.PageClient(self.page, "1086005", lambda event: None)
        return self

    def __exit__(self, *args: Any) -> None:
        # Disconnect only. Never close/launch the user's browser or create a session.
        self.context.stop()

    def discover(self) -> tuple[dict[str, Any], dict[str, Any]]:
        module = self.modules["search_plan"]
        plan = module.load_plan(module.DEFAULT_PLAN)
        # Operational contract stays exactly the validated six searches and low-volume policy.
        expected = [
            (region, term)
            for region in ("boyaca", "casanare")
            for term in ("refrigerio", "papeleria", "aseo")
        ]
        if [(q["region"], q["object_term"]) for q in plan["searches"]] != expected or (
            plan["pauses"]["sleep_between_queries"] != 4
            or plan["limits"]
            != {"max_queries_per_run": 6, "limit": 30, "page": 1, "max_retries": 1}
            or any(q["unspsc"] for q in plan["searches"])
        ):
            raise ValueError("El plan operativo debe conservar las seis busquedas validadas.")
        self.modules["cdp_runtime"].LOCAL.mkdir(parents=True, exist_ok=True)
        output = Path(
            tempfile.mkdtemp(prefix="operational-cdp-", dir=self.modules["cdp_runtime"].LOCAL)
        )
        code = module.run_plan(
            self.client,
            plan,
            output,
            lambda seconds: self.page.wait_for_timeout(seconds * 1000),
            lambda event: self.observer("discovery_progress", event),
            recent_days=7,
        )
        summary = json.loads((output / "search_plan_summary.json").read_text(encoding="utf-8"))
        discovery = json.loads((output / "discovery.json").read_text(encoding="utf-8"))
        if summary["stop_reason"]:
            raise SourceUnavailableError(summary["stop_reason"], summary.get("preflight"))
        if code not in (0, 2):
            raise RuntimeError("Discovery no completado")
        discovery["processes"] = [
            self.modules["sources"].annotate_source(p) for p in discovery["processes"]
        ]
        self.processes = {
            p["source_identity"]: p for p in discovery["processes"] if p.get("source_identity")
        }
        return discovery, summary

    def fetch(self, notice: str) -> list[SourceDocument]:
        process = self.processes[notice]
        values, _, _ = self.modules["freshness"].apply_freshness([process], 7)
        values, _, _ = self.modules["validity"].apply_validity(values)
        if not values[0]["recent"] or values[0]["validity_status"] != "open":
            raise ValueError("El proceso ya no supera frescura/vigencia")
        if not self.modules["sources"].document_capable(process):
            self.observer("metadata_only", {"source": self.modules["sources"].source_kind(process)})
            return []
        row = {
            "idContrato": int(process["id_contrato"]),
            "id_fuente_contract": int(process["id_fuente_contract"]),
            "idUltimaFase": process.get("id_ultima_fase") or notice,
        }
        runtime = self.modules["cdp_runtime"]
        documents = runtime.fetch_inventory(self.client, row)
        select = importlib.import_module("spike_licitaciones_info").select_documents
        self.observer("inventory", {"count": len(documents)})
        selected = select(documents, 2)
        self.observer("documents_selected", {"count": len(selected)})
        return [
            SourceDocument(
                d.document_id,
                notice,
                d.original_name
                if Path(d.original_name).suffix
                else f"{d.original_name}.{d.extension}",
                None,
                d.source_url,
            )
            for d in selected
        ]

    def review(self, pipeline: Any, reference: str) -> dict[str, Any]:
        from public_procurement.eureka.services import source_pipeline_review

        policy = json.loads(
            (SCRIPTS / "licitaciones_fact_policy.v1.json").read_text(encoding="utf-8")
        )
        return source_pipeline_review(
            pipeline, reference, self.modules["cdp_runtime"].annotate_facts, policy
        )


def notice_identity(process: dict[str, Any]) -> str | None:
    notice = process.get("id_ultima_fase")
    if not isinstance(notice, str) or not re.fullmatch(r"CO1\.NTC\.\d+", notice):
        return None
    return notice


def provider_identity(process: dict[str, Any]) -> str | None:
    return validated_modules()["sources"].process_identity(process)  # type: ignore[no-any-return]


def provider_metadata(process: dict[str, Any]) -> dict[str, Any]:
    return dict(validated_modules()["sources"].annotate_source(process))
