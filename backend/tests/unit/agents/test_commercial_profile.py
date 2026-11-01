import json
from pathlib import Path

from public_procurement.agents.eureka_assistant.readiness import call_key, required_reads
from public_procurement.agents.eureka_assistant.schemas import TOOL_SCHEMAS, LatestCdpRunSummary
from public_procurement.agents.eureka_assistant.service import EurekaAssistant
from public_procurement.eureka.services import get_eureka_commercial_profile
from public_procurement.shared.config import Settings

from .test_eureka_assistant import call, client, response
from .test_read_tools import IDENTITY, RUN, tools


def test_profile_reads_real_settings_and_reloads_catalog_changes(tmp_path):
    actual = Path(__file__).resolve().parents[3] / "config/eureka_radar.v1.json"
    raw = json.loads(actual.read_text(encoding="utf-8"))
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    settings = Settings(
        _env_file=None,
        database_url="unused-without-database-access",
        eureka_radar_config_path=path,
        eureka_radar_regions="Arauca, Casanare",
        eureka_preferred_budget_max=45000000,
    )
    first = get_eureka_commercial_profile(settings)
    assert first["regions"] == ["Arauca", "Casanare"]
    assert first["preferred_amount_max"] == 45000000
    assert first["above_preferred_amount_automatically_excluded"] is False
    assert first["above_preferred_amount_requires_review"] is True
    assert len(first["commercial_categories"]) == sum(
        not f.get("discovery_only") for f in raw["families"]
    )
    raw["families"][0]["label"] = "Etiqueta cambiada en configuración"
    path.write_text(json.dumps(raw), encoding="utf-8")
    second = get_eureka_commercial_profile(settings)
    assert second["commercial_categories"][0]["label"] == "Etiqueta cambiada en configuración"
    assert second["provenance"]["catalog_fingerprint"] != first["provenance"]["catalog_fingerprint"]


def test_sixth_tool_is_strict_and_has_no_parameters():
    schema = next(s for s in TOOL_SCHEMAS if s["name"] == "get_eureka_commercial_profile")
    assert schema["parameters"] == {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    assert schema["strict"]


def test_prioritization_forces_profile_first_but_summary_stays_light():
    tool, _reads = tools()
    raw = tool.queries.runs.return_value["items"][0]
    raw["alerts_created"] = 0
    raw["metrics"]["review_candidates_total"] = 0
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        response(answer="Sin candidatos que priorizar."),
    )
    EurekaAssistant(remote, tool).ask("Qué viste interesante para mí")
    assert (
        remote.openai.responses.create.call_args_list[0].kwargs["tool_choice"]["name"]
        == "get_eureka_commercial_profile"
    )
    summary = client(response(call()), response(answer="Resumen de métricas."))
    EurekaAssistant(summary, tool).ask("Solo el resumen")
    assert (
        summary.openai.responses.create.call_args_list[0].kwargs["tool_choice"]["name"]
        == "get_latest_cdp_run"
    )


def supported_cache():
    latest = LatestCdpRunSummary(
        has_run=True, run_id=RUN, alerts_created=0, review_candidates_total=1
    )
    cache = {
        call_key("get_eureka_commercial_profile", {}): "{}",
        call_key("get_run_review_candidates", {"run_id": RUN}): json.dumps(
            {"items": [{"identity": IDENTITY, "process_code": "TEST"}]}
        ),
    }
    return latest, cache


def test_concrete_recommendation_requires_detail_and_evidence_when_uncertain():
    latest, cache = supported_cache()
    request = {"name": "get_process_detail", "arguments": {"identity": IDENTITY}}
    assert required_reads("Prioriza la corrida", [latest], cache, "Recomiendo TEST") == [request]
    cache[call_key("get_process_detail", {"identity": IDENTITY})] = json.dumps(
        {"found": True, "score": 30, "manual_review_required": True}
    )
    assert required_reads("Prioriza la corrida", [latest], cache, "Recomiendo TEST") == [
        {"name": "get_process_evidence", "arguments": {"identity": IDENTITY}}
    ]
    cache[call_key("get_process_evidence", {"identity": IDENTITY})] = json.dumps(
        {"found": True, "documentary_evidence_available": False}
    )
    assert (
        required_reads(
            "Prioriza la corrida",
            [latest],
            cache,
            "Revisar TEST, sin evidencia documental disponible",
        )
        == []
    )


def test_clean_detail_does_not_force_documentary_read_or_all_other_candidates():
    latest, cache = supported_cache()
    cache[call_key("get_process_detail", {"identity": IDENTITY})] = json.dumps(
        {"found": True, "score": 30, "manual_review_required": False, "manual_review_reasons": []}
    )
    assert required_reads("Prioriza la corrida", [latest], cache, "Primero TEST") == []
    assert (
        required_reads(
            "Prioriza la corrida",
            [latest],
            cache,
            "No encontré oportunidades suficientemente interesantes.",
        )
        == []
    )
