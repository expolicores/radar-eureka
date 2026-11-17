"""Bounded function loop over read-only investigation DTOs, with mandatory grounding."""

import json
import re
import time
from typing import Any
from uuid import UUID

from public_procurement.investigation.services import InvestigationAssistantQueries

from .policy import POLICY

READERS = (
    "get_run_products",
    "get_run_benchmarks",
    "get_run_comparisons",
    "get_run_signals",
    "get_run_review_candidates",
)
TOOL_NAMES = ("get_latest_investigation_run", "get_investigation_run", *READERS)
TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": name,
        "description": "Solo lectura de resultados investigativos persistidos: " + name,
        "parameters": {
            "type": "object",
            "properties": {}
            if name == TOOL_NAMES[0]
            else {"run_id": {"type": "string", "format": "uuid"}},
            "required": [] if name == TOOL_NAMES[0] else ["run_id"],
            "additionalProperties": False,
        },
        "strict": True,
    }
    for name in TOOL_NAMES
]


class AssistantError(RuntimeError):
    def __init__(
        self, code: str, status: int = 503, *, diagnostic: dict[str, Any] | None = None
    ) -> None:
        super().__init__(code)
        self.code, self.status = code, status
        self.diagnostic = diagnostic


def arguments(name: str, raw: str, selected: str | None) -> dict[str, Any]:
    if name not in TOOL_NAMES:
        raise AssistantError("tool_not_allowed", 502)
    try:
        value = json.loads(raw)
        if not isinstance(value, dict) or set(value) != (
            set() if name == TOOL_NAMES[0] else {"run_id"}
        ):
            raise ValueError
        if "run_id" in value and (str(UUID(value["run_id"])) != selected):
            raise ValueError
        if "run_id" in value:
            value["run_id"] = str(UUID(value["run_id"]))
        return value
    except (ValueError, TypeError, AttributeError):
        raise AssistantError("invalid_tool_arguments", 502) from None


def summary(metadata: dict[str, Any], reads: dict[str, dict[str, Any]]) -> str:
    """Safe grounded fallback; never calls a model or infers a missing result as zero."""
    if not metadata.get("found"):
        return "No hay una corrida investigativa persistida que corresponda a esa selección."
    if metadata.get("provisional"):
        return (
            "La corrida sigue en ejecución, en etapa "
            + str(metadata.get("stage"))
            + ". Los conteos disponibles son provisionales; los resultados pueden cambiar. "
            + json.dumps(metadata.get("counts", {}), ensure_ascii=False)
        )
    if not metadata.get("result_available"):
        return (
            "La corrida está registrada, pero su resultado no está disponible. "
            "No puedo concluir que no haya hallazgos."
        )
    products, benchmarks, comparisons, signals, reviews = [reads.get(n, {}) for n in READERS]
    counts = metadata.get("counts", {})
    progress = ""
    if "processes_discovered" in counts:
        progress += f"Descubrió {counts['processes_discovered']} procesos. "
    if "processes_selected" in counts:
        progress += f"Seleccionó {counts['processes_selected']} procesos. "
    if "private_market_candidates" in counts:
        progress += (
            f"Productos elegibles para mercado privado: {counts['private_market_candidates']}. "
        )
    text = (
        progress + f"La corrida {metadata['run_id']} identificó "
        f"{products.get('total', 'no registrado')} productos. "
        f"Hay {benchmarks.get('total', 'no registrado')} benchmarks, "
        f"{comparisons.get('total', 'no registrado')} comparaciones existentes y "
        f"{signals.get('total', 'no registrado')} señales existentes. "
        f"{reviews.get('total', 'no registrado')} procesos tienen razones de revisión humana. "
    )
    if comparisons.get("total") == 0 and signals.get("total") == 0:
        text += (
            "No se generaron comparaciones ni señales con la evidencia disponible; "
            "esto no demuestra ausencia de posibles problemas. "
        )
    if any(b.get("benchmark_status") != "ready" for b in benchmarks.get("items", [])):
        text += (
            "Hay referencias privadas, pero el benchmark es insuficiente "
            "para una conclusión monetaria definitiva. "
        )
    if any(p.get("conflicts") for p in products.get("items", [])):
        text += "Existe evidencia conflictiva que requiere verificación manual. "
    if metadata.get("warnings") or metadata.get("errors"):
        text += "La corrida conserva advertencias o errores de cobertura que deben revisarse."
    if "extraction_failed" in counts:
        text += f" Extracciones fallidas: {counts['extraction_failed']}."
    if "partial_coverage_documents" in counts:
        text += f" Documentos con cobertura parcial: {counts['partial_coverage_documents']}."
    return text


class InvestigationAssistant:
    def __init__(self, transport: Any, timeout: float = 120) -> None:
        self.transport, self.timeout = transport, timeout

    def ask(
        self,
        message: str,
        queries: InvestigationAssistantQueries,
        history: list[dict[str, Any]] | None = None,
        *,
        explicit: bool = False,
    ) -> dict[str, Any]:
        metadata = queries.metadata()
        reads: dict[str, dict[str, Any]] = {}
        calls: list[dict[str, Any]] = []
        if not metadata.get("found"):
            return {
                "response": summary(metadata, reads),
                "tool_calls": [],
                "run_references": [],
                "process_references": [],
            }
        selected = metadata["run_id"]
        first = "get_investigation_run" if explicit else "get_latest_investigation_run"
        inputs: list[Any] = [
            {"role": "developer", "content": POLICY},
            *(history or [])[-8:],
            {"role": "user", "content": message},
        ]
        # Every substantive analysis must inspect the five relevant read DTOs.
        status_only = bool(
            re.search(r"c[oó]mo va|estado de ejecuci[oó]n|sigue ejecut", message, re.I)
        )
        required = [first] if status_only else [first, *READERS]
        deadline = time.monotonic() + self.timeout
        forced: str | None = first
        for _ in range(12):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssistantError("timeout", 504)
            response = self.transport.respond(inputs, TOOL_SCHEMAS, forced, remaining)
            if response.status != "completed":
                raise AssistantError("incomplete_response", 502)
            outputs = list(response.output)
            if any(o.type not in {"function_call", "message", "reasoning"} for o in outputs):
                raise AssistantError("tool_not_allowed", 502)
            requested = [o for o in outputs if o.type == "function_call"]
            forced = None
            if not requested:
                missing = [n for n in required if n not in reads]
                if missing:
                    forced = missing[0]
                    inputs.append(
                        {
                            "role": "developer",
                            "content": "Faltan lecturas obligatorias antes de concluir: "
                            + ", ".join(missing),
                        }
                    )
                    continue
                answer = response.output_text.strip()
                if not answer:
                    raise AssistantError("empty_response", 502)
                # Reject an invented signal or conclusion with an evidence-bound summary.
                invented = reads.get("get_run_signals", {}).get("total") == 0 and bool(
                    re.search(
                        r"(?:hay|gener[oó]|generaron|detect[oó]|detectaron)\s+(?:una|[1-9]\d*)\s+señal",
                        answer,
                        re.I,
                    )
                )
                condemnatory = bool(
                    re.search(
                        r"(?:hay fraude|corrupción confirmada|sobreprecio probado|"
                        r"responsabilidad demostrada)",
                        answer,
                        re.I,
                    )
                )
                if invented or condemnatory:
                    answer = summary(metadata, reads)
                identities = sorted(
                    {
                        p["process_identity"]
                        for data in reads.values()
                        for p in data.get("items", [])
                        if isinstance(p.get("process_identity"), str)
                    }
                    | {
                        identity
                        for data in reads.values()
                        for p in data.get("items", [])
                        for identity in p.get("processes", [])
                        if isinstance(identity, str)
                    }
                )
                return {
                    "response": answer,
                    "tool_calls": calls,
                    "run_references": [selected],
                    "process_references": identities,
                }
            for call in requested:
                if len(calls) >= 12:
                    raise AssistantError("tool_limit", 502)
                args = arguments(call.name, call.arguments, selected)
                if call.name not in reads:
                    reads[call.name] = queries.dispatch(call.name, args)
                data = reads[call.name]
                calls.append({"name": call.name, "arguments": args, "output": data})
                inputs.append(
                    call.model_dump(exclude_none=True)
                    if hasattr(call, "model_dump")
                    else {
                        "type": "function_call",
                        "name": call.name,
                        "arguments": call.arguments,
                        "call_id": call.call_id,
                    }
                )
                inputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(data, ensure_ascii=False),
                    }
                )
        raise AssistantError("tool_limit", 502)
