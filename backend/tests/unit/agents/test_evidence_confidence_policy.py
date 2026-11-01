"""Policy and transport contracts with mocked Foundry, not an evaluation of live LLM claims."""

import json

import pytest

from public_procurement.agents.eureka_assistant.policy import INVESTIGATION_POLICY
from public_procurement.agents.eureka_assistant.service import EurekaAssistant

from .test_eureka_assistant import call, client, response
from .test_read_tools import IDENTITY, RUN, tools

CASES = [
    (
        "Cubará",
        False,
        "Interesante por metadata: preliminar, pero con alta incertidumbre documental; "
        "no hay evidencia disponible. Monto superior al preferido: no implica exclusión "
        "automática. Validar documentos, requisitos y condiciones.",
    ),
    (
        "Corrales",
        True,
        "Interesante con evidencia documental: papelería, cafetería, aseo y tecnología. "
        "El pipeline lo dejó No elegible, pero la evidencia relevante matiza esa decisión; "
        "merece revisión humana. Validar especificaciones y requisitos.",
    ),
    (
        "Duitama",
        True,
        "Interesante con evidencia documental y preliminarmente manejable por su encaje. "
        "Requiere revisar detalles técnicos y requisitos antes de decidir; "
        "el pago no está confirmado en la evidencia recibida.",
    ),
]


@pytest.mark.parametrize(("case", "documentary", "answer"), CASES)
def test_reference_cases_receive_policy_and_preserve_pipeline_signals(case, documentary, answer):
    tool, reads = tools()
    tool.queries.runs.return_value["items"][0]["alerts_created"] = 0
    row = reads.process.return_value
    row.update(
        codigo_proceso="CASE-" + case,
        commercial_decision="No elegible",
        score=20,
        requires_manual_document_review=True,
        manual_review_reasons=["suspicious_facts"],
    )
    reads.run_review.return_value = {"items": [row], "total": 1}
    reads.evidence.return_value = {
        "facts": [
            {
                "fact_type": "product",
                "string_value": "Papelería y aseo",
                "evidence_text": "Productos de papelería y aseo",
                "source_locator": {},
            }
        ]
        if documentary
        else [],
        "documents": [
            {
                "name": "INVITACION.pdf",
                "status": "completed",
                "total_pages": 2,
                "processed_pages": 2,
                "coverage_ratio": 1,
                "extraction_mode": "native",
            }
        ]
        if documentary
        else [],
        "canonical_facts": [],
    }
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        response(call(json.dumps({"run_id": RUN}), "get_run_review_candidates", "r")),
        response(call(json.dumps({"identity": IDENTITY}), "get_process_detail", "d")),
        response(call(json.dumps({"identity": IDENTITY}), "get_process_evidence", "e")),
        response(answer=answer),
    )
    result = EurekaAssistant(remote, tool).ask("Qué viste interesante para mí")
    assert result.answer == answer
    assert row["commercial_decision"] == "No elegible"
    assert row["score"] == 20
    first = remote.openai.responses.create.call_args_list[0].kwargs
    assert first["tool_choice"]["name"] == "get_eureka_commercial_profile"
    instructions = first["input"][0]["content"]
    assert INVESTIGATION_POLICY in instructions
    assert "Ausencia de evidencia no es evidencia favorable" in instructions
    assert "no verdades definitivas" in instructions
    if not documentary:
        assert "alta incertidumbre" in result.answer
        assert "limpio" not in result.answer
        assert result.tool_results[-1]["documentary_evidence_available"] is False
    else:
        assert result.tool_results[-1]["documentary_evidence_available"] is True


def test_policy_explicitly_rejects_clean_case_and_automatic_pipeline_verdicts():
    for field in ("commercial_decision", "score", "no_alert_reason", "funnel_state", "has_alert"):
        assert field in INVESTIGATION_POLICY
    for phrase in (
        "«limpio»",
        "«menos problemático»",
        "«validado»",
        "«documentalmente favorable»",
        "Ausencia de evidencia no es evidencia favorable",
        "No priorices solo por score",
        "mayor monto o menor cantidad de warnings",
    ):
        assert phrase in INVESTIGATION_POLICY


def test_suspicious_without_detail_has_explicit_neutral_fallback():
    assert (
        "Existe una bandera de revisión documental cuyo\ndetalle requiere inspección adicional"
        in INVESTIGATION_POLICY
    )
    assert "suspicious_fact no es un motivo genérico de descarte" in INVESTIGATION_POLICY
    assert "No inventes el hecho, su causa ni gravedad" in INVESTIGATION_POLICY


def test_confidence_levels_are_distinct_and_examples_not_hardcoded_in_production():
    for category in (
        "A. Interesante por metadata",
        "B. Interesante con evidencia documental",
        "C. Incierto por falta de evidencia",
        "D. Poco atractivo por evidencia concreta",
    ):
        assert category in INVESTIGATION_POLICY
    assert (
        "Separa explícitamente\nmetadata, evidencia documental e inferencia" in INVESTIGATION_POLICY
    )
    assert "di no confirmado: nunca los" in INVESTIGATION_POLICY
    assert "Cubar" not in INVESTIGATION_POLICY
    assert "Corrales" not in INVESTIGATION_POLICY
    assert "Duitama" not in INVESTIGATION_POLICY


def test_conceptual_priority_places_documentary_conditions_before_pipeline_signals():
    order = (
        "encaje comercial real",
        "monto frente al perfil comercial",
        "deadline; condiciones de ejecución",
        "pago; evidencia documental",
        "complejidad/requisitos; señales del pipeline",
        "incertidumbre restante",
    )
    positions = [INVESTIGATION_POLICY.index(term) for term in order]
    assert positions == sorted(positions)
