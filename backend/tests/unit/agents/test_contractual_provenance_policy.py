"""Instruction/transport contracts; live model compliance is assessed in the single trial."""

import json

from public_procurement.agents.eureka_assistant.policy import INVESTIGATION_POLICY
from public_procurement.agents.eureka_assistant.service import EurekaAssistant

from .test_eureka_assistant import call, client, response
from .test_read_tools import IDENTITY, RUN, tools


def test_internal_processing_limit_is_only_an_operational_explanation():
    assert (
        "Eureka no lo procesó\ncompletamente en esa corrida por límite interno de procesamiento"
        in INVESTIGATION_POLICY
    )
    assert (
        "Nunca lo reformules como «quedó para evaluación hasta cierto límite»"
        in INVESTIGATION_POLICY
    )
    for field in (
        "no_alert_reason",
        "funnel_state",
        "manual_review_required",
        "manual_review_reasons",
        "review_first_seen_at",
        "review_membership_persisted",
        "associated_runs",
        "limit_deferred",
    ):
        assert field in INVESTIGATION_POLICY
    assert (
        "describen comportamiento interno de Eureka, NO condiciones contractuales"
        in INVESTIGATION_POLICY
    )


def test_deadline_requires_explicit_contractual_source_not_run_or_review_timestamps():
    assert "El deadline solo puede proceder de metadata.deadline" in INVESTIGATION_POLICY
    assert "evidencia documental/canonical explícito del cronograma" in INVESTIGATION_POLICY
    assert (
        "No lo derives\nde no_alert_reason, funnel_state, run timestamps, review timestamps"
        in INVESTIGATION_POLICY
    )
    assert "di «deadline no confirmado»" in INVESTIGATION_POLICY


def test_conflicting_canonicals_require_explicit_conflict_not_a_silent_winner():
    assert (
        "Existe evidencia conflictiva sobre X y requiere verificación manual"
        in INVESTIGATION_POLICY
    )
    assert "NO selecciones silenciosamente un valor como verdadero" in INVESTIGATION_POLICY
    for status in (
        "confirmed: evidencia consistente",
        "uncertain: evidencia incompleta",
        "conflicting: dos o más evidencias incompatibles",
        "absent: sin evidencia disponible",
    ):
        assert status in INVESTIGATION_POLICY


def test_conflicting_payment_method_cannot_be_presented_as_confirmed():
    assert "Para PAYMENT_METHOD/payment facts" in INVESTIGATION_POLICY
    assert (
        "NO afirmes «El pago es contra entrega» como condición confirmada" in INVESTIGATION_POLICY
    )
    assert "presenta conflicto entre fuentes/extracciones" in INVESTIGATION_POLICY
    assert (
        "Solo presenta una forma de pago como confirmada cuando la evidencia sea consistente"
        in INVESTIGATION_POLICY
    )


def test_recommendation_separates_commercial_attraction_contractual_evidence_and_operations():
    assert (
        "Toda afirmación contractual relevante debe atribuirse conceptualmente a metadata"
        in INVESTIGATION_POLICY
    )
    assert "Los campos internos solo explican qué hizo o no hizo Eureka" in INVESTIGATION_POLICY
    assert "atractivo comercial; evidencia contractual confirmada" in INVESTIGATION_POLICY
    assert "incertidumbres; conflictos; señales internas del pipeline" in INVESTIGATION_POLICY


def test_model_receives_provenance_policy_and_conflict_payload_without_fabricated_deadline():
    tool, reads = tools()
    tool.queries.runs.return_value["items"][0]["alerts_created"] = 0
    row = reads.process.return_value
    row.update(
        codigo_proceso="TEST",
        deadline_at=None,
        no_alert_reason="Diferido por límite de procesamiento",
        funnel_state="limit_deferred",
    )
    reads.run_review.return_value = {"items": [row], "total": 1}
    reads.evidence.return_value = {
        "facts": [],
        "documents": [],
        "canonical_facts": [
            {
                "canonical_type": "PAYMENT_METHOD",
                "status": "conflict",
                "canonical_value": {"value": None},
            }
        ],
    }
    answer = (
        "TEST tiene encaje por metadata. Deadline no confirmado. "
        "Existe evidencia conflictiva sobre forma de pago y requiere verificación manual. "
        "Eureka no lo procesó completamente por un límite interno; "
        "eso no es un plazo contractual."
    )
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        response(call(json.dumps({"run_id": RUN}), "get_run_review_candidates", "r")),
        response(call(json.dumps({"identity": IDENTITY}), "get_process_detail", "d")),
        response(call(json.dumps({"identity": IDENTITY}), "get_process_evidence", "e")),
        response(answer=answer),
    )
    result = EurekaAssistant(remote, tool).ask("Qué viste interesante")
    assert result.answer == answer
    instructions = remote.openai.responses.create.call_args_list[0].kwargs["input"][0]["content"]
    assert INVESTIGATION_POLICY in instructions
    outputs = [
        json.loads(c.kwargs["input"][0]["output"])
        for c in remote.openai.responses.create.call_args_list[1:]
        if c.kwargs["input"][0].get("type") == "function_call_output"
    ]
    detail = next(d for d in outputs if d.get("process_code") == "TEST")
    assert detail["deadline"] is None
    assert detail["no_alert_reason"] == "Diferido por límite de procesamiento"
    evidence = next(d for d in outputs if "canonicals" in d)
    assert evidence["canonicals"][0]["status"] == "conflict"
    assert evidence["canonicals"][0]["value"] is None
