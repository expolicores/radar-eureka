import json
from unittest.mock import Mock

import pytest

from public_procurement.agents.eureka_assistant.read_tools import EurekaReadTools
from public_procurement.agents.eureka_assistant.schemas import TOOL_SCHEMAS, SpikeError
from public_procurement.agents.eureka_assistant.service import EurekaAssistant, validate_call

from .test_eureka_assistant import call, client, response, run

RUN = "9e578b72-0e2d-4582-bbd6-4491d9764437"
IDENTITY = "secop:CO1.NTC.123"


def tools():
    queries = Mock(spec=["runs"])
    queries.runs.return_value = {"items": [{**run(), "id": RUN}]}
    reads = Mock(spec=["run_alerts", "run_review", "process", "evidence"])
    reads.process.return_value = {
        "canonical_identity": IDENTITY,
        "codigo_proceso": "TEST",
        "object": "Compra de papelería",
        "sources": ["licitaciones_info_cdp"],
        "manual_review_reasons": ["suspicious_facts"],
        "history": [],
        "score": None,
    }
    return EurekaReadTools(
        queries, reads, profile=lambda: {"regions": ["Boyacá"], "preferred_amount_max": 30000000}
    ), reads


def test_exactly_six_strict_tool_schemas():
    assert len(TOOL_SCHEMAS) == 6
    assert {s["name"] for s in TOOL_SCHEMAS} == {
        "get_latest_cdp_run",
        "get_eureka_commercial_profile",
        "get_run_alerts",
        "get_run_review_candidates",
        "get_process_detail",
        "get_process_evidence",
    }
    assert all(s["strict"] and not s["parameters"]["additionalProperties"] for s in TOOL_SCHEMAS)


def test_empty_alerts_distinguishes_existing_and_absent_run():
    tool, reads = tools()
    reads.run_alerts.return_value = {"items": [], "total": 0}
    assert tool.get_run_alerts(RUN)["found"] is True
    reads.run_alerts.side_effect = LookupError()
    assert tool.get_run_alerts(RUN)["found"] is False


def test_run_alert_projection_is_limited_and_does_not_leak_snapshot():
    tool, reads = tools()
    reads.run_alerts.return_value = {
        "items": [
            {
                "id": "alert",
                "snapshot": {
                    "canonical_identity": IDENTITY,
                    "score": 30,
                    "headers": {"Authorization": "secret"},
                },
                "reasons": [{"code": "budget"}],
            }
        ]
        * 11,
        "total": 11,
    }
    result = tool.get_run_alerts(RUN)
    assert len(result["items"]) == 10
    assert result["truncated"]
    assert result["items"][0]["deadline"] is None
    assert "secret" not in json.dumps(result)


def test_review_candidates_limit_and_no_run():
    tool, reads = tools()
    reads.run_review.return_value = {"items": [], "total": 0}
    assert tool.get_run_review_candidates(RUN)["items"] == []
    reads.run_review.return_value = {"items": [reads.process.return_value] * 11, "total": 11}
    assert len(tool.get_run_review_candidates(RUN)["items"]) == 10
    reads.run_review.side_effect = LookupError()
    assert not tool.get_run_review_candidates(RUN)["found"]


def test_detail_missing_fields_are_null_and_unknown_identity_is_explicit():
    tool, reads = tools()
    assert tool.get_process_detail(IDENTITY)["deadline"] is None
    assert tool.get_process_detail(IDENTITY)["score"] is None
    reads.process.side_effect = LookupError()
    assert tool.get_process_detail(IDENTITY) == {"found": False, "identity": IDENTITY}
    assert not tool.get_process_evidence(IDENTITY)["found"]


def test_evidence_is_bounded_with_provenance_and_no_document_body():
    tool, reads = tools()
    reads.evidence.return_value = {
        "facts": [
            {
                "fact_type": "quantity",
                "numeric_value": 5,
                "evidence_text": "x" * 1000,
                "source_locator": {
                    "sources": [{"original_name": "INVITACION", "locator": {"page_number": 2}}]
                },
            }
        ]
        * 25,
        "documents": [
            {
                "name": "PDF",
                "coverage_ratio": 0.5,
                "extraction_mode": "ocr",
                "body": "must not leak",
            }
        ]
        * 12,
        "canonical_facts": [
            {
                "id": "c1",
                "canonical_type": "QUANTITY",
                "status": "conflict",
                "canonical_value": {"value": 5, "candidates": "must not leak"},
            }
        ],
    }
    result = tool.get_process_evidence(IDENTITY)
    assert len(result["facts"]) == 20
    assert result["facts_truncated"]
    assert len(result["documents"]) == 10
    assert result["documents_truncated"]
    assert result["facts"][0]["references"][0]["page"] == 2
    assert len(result["facts"][0]["evidence_text"]) == 250
    assert result["facts"][0]["suspicious"] is None
    assert result["ocr_used"]
    assert result["partial_coverage"]
    assert result["suspicious_facts_reported"]
    assert "must not leak" not in json.dumps(result)


def test_no_document_evidence_is_not_invented():
    tool, reads = tools()
    reads.evidence.return_value = {"facts": [], "documents": [], "canonical_facts": []}
    result = tool.get_process_evidence(IDENTITY)
    assert result["documentary_evidence_available"] is False
    assert result["facts"] == result["documents"] == result["canonicals"] == []


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("get_run_alerts", '{"run_id":"bad"}'),
        ("get_run_alerts", "{}"),
        ("get_process_detail", '{"identity":"x","extra":1}'),
        ("get_process_evidence", '{"identity":"../../secret"}'),
    ],
)
def test_tool_inputs_are_validated_before_dispatch(name, args):
    with pytest.raises(SpikeError):
        validate_call(name, args)


def test_tool_chaining_returns_outputs_and_final_answer():
    tool, reads = tools()
    reads.run_alerts.return_value = {"items": [], "total": 0}
    reads.run_review.return_value = {"items": [reads.process.return_value], "total": 1}
    remote = client(
        response(call(name="get_eureka_commercial_profile", call_id="p")),
        response(call()),
        response(call(json.dumps({"run_id": RUN}), "get_run_alerts", "c2")),
        response(call(json.dumps({"run_id": RUN}), "get_run_review_candidates", "c3")),
        response(call(json.dumps({"identity": IDENTITY}), "get_process_detail", "c4")),
        response(answer="Metadata pendiente de confirmar documentalmente."),
    )
    result = EurekaAssistant(remote, tool).ask("Revisa la corrida")
    assert len(result.tool_results) == 5
    assert result.answer == "Metadata pendiente de confirmar documentalmente."
    assert remote.openai.responses.create.call_count == 6
    assert all(
        c.kwargs["conversation"] == "conversation-1"
        for c in remote.openai.responses.create.call_args_list
    )
