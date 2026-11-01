import json

import pytest

from public_procurement.agents.eureka_assistant.policy import (
    INVESTIGATION_POLICY,
    investigation_requested,
    with_investigation_policy,
)
from public_procurement.agents.eureka_assistant.schemas import SpikeError
from public_procurement.agents.eureka_assistant.service import EurekaAssistant

from .test_eureka_assistant import call, client, response
from .test_read_tools import RUN, tools


@pytest.mark.parametrize(
    "question",
    [
        "Revisa la última corrida CDP y dime si viste algo interesante para mí.",
        "¿Qué viste interesante?",
        "¿Hay algo participable?",
        "¿Qué debería revisar primero?",
        "Prioriza la última corrida",
        "Identifica oportunidades interesantes",
    ],
)
def test_investigation_intent(question):
    assert investigation_requested(question)


@pytest.mark.parametrize(
    "question",
    [
        "¿Qué salió en la última corrida CDP?",
        "Solo el resumen de la corrida",
        "Dame únicamente las métricas",
    ],
)
def test_summary_does_not_require_extra_investigation(question):
    assert not investigation_requested(question)


def test_premature_summary_is_not_returned_and_model_continues_reading():
    tool, reads = tools()
    reads.run_alerts.return_value = {"items": [], "total": 0}
    reads.run_review.return_value = {"items": [reads.process.return_value], "total": 1}
    reads.process.return_value.update(score=30, manual_review_reasons=[])
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        response(answer="¿Quieres que consulte los candidatos?"),
        response(call(json.dumps({"run_id": RUN}), "get_run_alerts", "c2")),
        response(call(json.dumps({"run_id": RUN}), "get_run_review_candidates", "c3")),
        response(call(json.dumps({"identity": "secop:CO1.NTC.123"}), "get_process_detail", "d1")),
        response(answer="Revisa TEST: compra de papelería; deadline no confirmado."),
    )
    result = EurekaAssistant(remote, tool).ask("¿Qué viste interesante?")
    assert result.answer.startswith("Revisa TEST")
    reads.run_alerts.assert_called_once_with(RUN)
    reads.run_review.assert_called_once_with(RUN)
    reads.evidence.assert_not_called()  # Enough context does not force every detail/evidence.
    reminder = remote.openai.responses.create.call_args_list[3].kwargs["input"][0]
    assert reminder["role"] == "developer"
    assert "No cierres con métricas" in reminder["content"]


def test_zero_new_alerts_skips_alert_tool_but_still_reads_candidates():
    tool, reads = tools()
    tool.queries.runs.return_value["items"][0]["alerts_created"] = 0
    reads.run_review.return_value = {"items": [], "total": 0}
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        response(call(json.dumps({"run_id": RUN}), "get_run_review_candidates", "c2")),
        response(answer="No hay candidatos actuales suficientemente interesantes."),
    )
    assert (
        EurekaAssistant(remote, tool).ask("Prioriza la última corrida").answer.startswith("No hay")
    )
    reads.run_alerts.assert_not_called()


def test_no_opportunities_in_summary_needs_no_candidate_tool():
    tool, reads = tools()
    raw = tool.queries.runs.return_value["items"][0]
    raw["alerts_created"] = 0
    raw["metrics"]["review_candidates_total"] = 0
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        response(answer="No se registraron alertas ni candidatos a revisión."),
    )
    assert EurekaAssistant(remote, tool).ask("¿Hay algo participable?").answer.startswith("No se")
    reads.run_review.assert_not_called()
    reads.run_alerts.assert_not_called()


def test_repeated_refusal_to_read_fails_without_inventing_opportunities():
    tool, reads = tools()
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        *(response(answer="¿Quieres que revise?") for _ in range(3)),
    )
    with pytest.raises(SpikeError, match="lecturas necesarias"):
        EurekaAssistant(remote, tool).ask("¿Qué viste interesante?")
    reads.run_review.assert_not_called()


def test_policy_append_preserves_base_and_is_idempotent():
    original = "Instrucciones remotas originales."
    updated = with_investigation_policy(original)
    assert updated.startswith(original)
    assert INVESTIGATION_POLICY in updated
    assert with_investigation_policy(updated) == updated
