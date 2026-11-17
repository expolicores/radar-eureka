import copy
import json
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace as Ns
from typing import ClassVar
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from public_procurement.agents.investigation_assistant.api import router
from public_procurement.agents.investigation_assistant.chat import AzureTransport, InvestigationChat
from public_procurement.agents.investigation_assistant.policy import POLICY
from public_procurement.agents.investigation_assistant.service import (
    READERS,
    TOOL_SCHEMAS,
    AssistantError,
    InvestigationAssistant,
    arguments,
    summary,
)
from public_procurement.investigation.services import build_assistant_queries
from public_procurement.shared.config import Settings

NOW = datetime(2026, 11, 11, 15, tzinfo=UTC)


def fixture_result():
    return {
        "processes": [
            {
                "id": "CO1.REQ.123",
                "reference": "MC-NEW",
                "entity": "Entidad A",
                "documents": [
                    {
                        "selected": True,
                        "downloaded": True,
                        "coverage_complete": False,
                        "extraction_status": "failed",
                    }
                ],
                "economic_cycle": {
                    "products": [
                        {
                            "id": "item1",
                            "item_description": "Samsung 58U8000H",
                            "brand": "Samsung",
                            "model": "58U8000H",
                            "quantity": "1",
                            "requires_manual_review": True,
                            "conflicts": ["offer_contract_price_conflict"],
                            "observations": [
                                {
                                    "evidence": [
                                        {
                                            "source_document": "OFERTA.pdf",
                                            "source_page": 339,
                                            "input_sha256": "abc",
                                            "headers": {"Authorization": "SECRET"},
                                        }
                                    ]
                                }
                            ],
                        }
                    ]
                },
            }
        ],
        "private_market_candidates": [
            {
                "candidate_id": "c1",
                "product_id": "item1",
                "process_identity": "CO1.REQ.123",
                "process_code": "MC-NEW",
                "status": "pending_review",
                "reasons": ["no_documented_public_unit_price"],
                "public_evidence_status": "unresolved",
            }
        ],
        "comparisons": [],
        "signals": [],
        "market_reports": [],
    }


def persist(
    directory,
    kind="state_vs_private_market",
    created=NOW,
    status="completed_with_warnings",
    result=None,
):
    identifier = uuid4()
    root = "runs" if kind == "state_vs_state" else "market-date-runs"
    folder = directory / root / str(identifier)
    folder.mkdir(parents=True)
    data = {
        "run_id": str(identifier),
        "run_type": kind,
        "status": status,
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "window_start_at": "2026-10-01T05:00:00Z",
        "window_before_at": "2026-11-01T05:00:00Z",
        "created_at": created.isoformat(),
        "started_at": created.isoformat(),
        "finished_at": None,
        "stage": "documents_extraction" if status == "running" else "finished",
        "warnings": ["partial_document_coverage", "TOKEN=SECRET"],
        "errors": [],
        "counts": {
            "processes_discovered": 865,
            "processes_selected": 48,
            "products_identified": 1,
            "private_market_candidates": 0,
            "signals_generated": 0,
        },
    }
    (folder / "run.json").write_text(json.dumps(data), encoding="utf8")
    if result is not None:
        (folder / "result.json").write_text(
            json.dumps({**result, "investigation_run_id": str(identifier)}), encoding="utf8"
        )
    return identifier


def query(directory, identifier=None):
    q = build_assistant_queries(directory)
    q.select(str(identifier) if identifier else None, None, False, NOW)
    return q


def market():
    return {
        "product": {"brand": "Samsung", "model": "58U8000H"},
        "public_product": {
            "public_process_identity": "CO1.REQ.123",
            "public_process_code": "MC-NEW",
            "public_price_stage": "offer",
            "public_unit_price": "3767123",
        },
        "public_evidence_status": "documented_unconfirmed_offer",
        "benchmark": {
            "benchmark_status": "insufficient_market_evidence",
            "valid_observations_count": 2,
            "retailers_count": 2,
            "min_price": "1799900",
            "median_price": "2569900",
            "max_price": "3339900",
            "evidence_sufficiency": "insufficient_market_evidence",
            "captured_at": NOW.isoformat(),
            "limitations": ["current_market_not_historic_price"],
            "observations": [
                {
                    "retailer": name,
                    "price": price,
                    "match_level": "high",
                    "provider_raw": {"api_key": "SECRET"},
                }
                for name, price in [("Exito", "1799900"), ("Puntos Colombia", "3339900")]
            ],
        },
        "comparison": None,
        "signal": None,
        "raw_provider": {"api_key": "SECRET"},
    }


class Model:
    def __init__(self, answer="Hay evidencia insuficiente y requiere revisión humana."):
        self.answer = answer
        self.calls = []

    def respond(self, inputs, tools, forced, timeout):
        self.calls.append((copy.deepcopy(inputs), tools, forced))
        if forced:
            data = {} if forced == "get_latest_investigation_run" else {"run_id": self.run_id}
            return Ns(
                status="completed",
                output=[
                    Ns(
                        type="function_call",
                        name=forced,
                        arguments=json.dumps(data),
                        call_id="call" + str(len(self.calls)),
                    )
                ],
                output_text="",
            )
        return Ns(status="completed", output=[], output_text=self.answer)


def ask(q, message="¿Qué encontró y qué vale la pena revisar?", answer=None):
    model = Model(answer or "Hay evidencia insuficiente y requiere revisión humana.")
    model.run_id = str(q.run.run_id)
    return InvestigationAssistant(model).ask(message, q), model


def test_latest_across_run_types_today_and_explicit_are_metadata_based(tmp_path):
    old = persist(tmp_path, kind="state_vs_state", created=datetime(2026, 11, 10, 23, tzinfo=UTC))
    new = persist(tmp_path, result=fixture_result())
    assert query(tmp_path).metadata()["run_id"] == str(new)
    assert query(tmp_path, old).metadata()["run_type"] == "state_vs_state"
    q = build_assistant_queries(tmp_path)
    q.select(None, "state_vs_state", True, NOW)
    assert not q.metadata()["found"]
    assert list(tmp_path.iterdir())  # Reads do not create a missing root.


@pytest.mark.parametrize("status", ["completed", "completed_with_warnings"])
def test_tool_chaining_cannot_finish_at_run_funnel(status, tmp_path):
    identifier = persist(tmp_path, status=status, result=fixture_result())
    result, model = ask(query(tmp_path, identifier))
    assert {c["name"] for c in result["tool_calls"]} == {"get_latest_investigation_run", *READERS}
    assert result["run_references"] == [str(identifier)]
    assert result["process_references"] == ["CO1.REQ.123"]
    assert len(model.calls) <= 12
    serialized = json.dumps(result)
    assert "SECRET" not in serialized
    assert "headers" not in serialized


def test_no_products_no_benchmarks_no_signals_is_insufficient_not_clean(tmp_path):
    identifier = persist(tmp_path, result={"processes": [], "comparisons": [], "signals": []})
    q = query(tmp_path, identifier)
    reads = {name: q.dispatch(name, {"run_id": str(identifier)}) for name in READERS}
    answer = summary(q.metadata(), reads)
    assert "0 productos" in answer
    assert "no demuestra ausencia" in answer
    assert "irregular" not in answer
    assert reads["get_run_signals"]["total"] == 0


def test_products_but_no_eligible_keep_explicit_reason(tmp_path):
    identifier = persist(tmp_path, result=fixture_result())
    q = query(tmp_path, identifier)
    product = q.products()["items"][0]
    assert product["private_market_eligibility"] == "pending_review"
    assert product["eligibility_reasons"] == ["no_documented_public_unit_price"]
    assert product["public_evidence_status"] == "unresolved"
    assert product["provenance"][0]["source_page"] == 339


def test_investigative_policy_receives_documented_price_without_promoting_purchase(tmp_path):
    data = fixture_result()
    item = data["processes"][0]["economic_cycle"]["products"][0]
    item.update(brand=None, model=None, offer_unit_price="1700000")
    candidate = data["private_market_candidates"][0]
    candidate.update(status="ineligible", reasons=["unresolved_product_identity"])
    identifier = persist(tmp_path, result=data)
    receipt = tmp_path / "market-date-runs" / str(identifier) / "result.json"
    original = receipt.read_bytes()

    result, model = ask(
        query(tmp_path, identifier), "¿Qué fue lo más importante de la última corrida?"
    )

    assert model.calls[0][0][0] == {"role": "developer", "content": POLICY}
    reads = {call["name"]: call["output"] for call in result["tool_calls"]}
    product = reads["get_run_products"]["items"][0]
    assert product["documented_public_unit_price"] == "1700000"
    assert product["verified_public_unit_price"] is None
    assert product["public_evidence_status"] == "unresolved"
    assert product["brand"] is None
    assert product["model"] is None
    assert product["private_market_eligibility"] == "ineligible"
    assert product["eligibility_reasons"] == ["unresolved_product_identity"]
    assert product["provenance"][0]["source_document"] == "OFERTA.pdf"
    assert product["provenance"][0]["source_page"] == 339
    assert reads["get_run_benchmarks"]["total"] == 0
    assert reads["get_run_comparisons"]["total"] == 0
    assert reads["get_run_signals"]["total"] == 0
    assert receipt.read_bytes() == original


def test_samsung_two_high_observations_are_not_a_comparison_or_signal(tmp_path):
    data = fixture_result()
    data["market_reports"] = [market()]
    data["private_market_candidates"][0].update(
        status="eligible",
        public_evidence_status="documented_unconfirmed_offer",
        public_product={"public_unit_price": "3767123"},
    )
    identifier = persist(tmp_path, result=data)
    q = query(tmp_path, identifier)
    b = q.benchmarks()["items"][0]
    assert b["valid_observations_count"] == 2
    assert b["benchmark_status"] == "insufficient_market_evidence"
    assert all(o["match_level"] == "high" for o in b["observations"])
    assert q.comparisons()["total"] == 0
    assert q.signals()["total"] == 0
    assert "insufficient_market_evidence" in q.reviews()["items"][0]["reasons"]
    assert "SECRET" not in json.dumps(b)


def test_existing_comparisons_and_signals_are_only_read_not_generated(tmp_path):
    data = fixture_result()
    data["comparisons"] = [
        {
            "id": "pair1",
            "processes": ["CO1.REQ.123", "CO1.REQ.456"],
            "comparison_eligible": True,
            "unit_price_a_cop": "100",
            "unit_price_b_cop": "200",
            "difference_pct": "100",
            "limitations": ["human_review"],
        },
        {"id": "noteligible", "comparison_eligible": False},
    ]
    data["signals"] = [
        {
            "id": "s1",
            "type": "PUBLIC_PRICE_DIFFERENCE",
            "processes": ["CO1.REQ.123"],
            "requires_human_review": True,
        }
    ]
    identifier = persist(tmp_path, kind="state_vs_state", result=data)
    before = (tmp_path / "runs" / str(identifier) / "result.json").read_bytes()
    q = query(tmp_path, identifier)
    assert q.comparisons()["total"] == 1
    assert q.signals()["items"][0]["id"] == "s1"
    assert (tmp_path / "runs" / str(identifier) / "result.json").read_bytes() == before


def test_document_conflict_partial_coverage_and_failed_extraction_are_review_reasons(tmp_path):
    identifier = persist(tmp_path, result=fixture_result())
    reasons = query(tmp_path, identifier).reviews()["items"][0]["reasons"]
    assert {"documentary_conflict", "partial_document_coverage", "extraction_failed"} <= set(
        reasons
    )


def test_fake_model_cannot_invent_signal_when_none_is_stored(tmp_path):
    identifier = persist(tmp_path, result=fixture_result())
    result, _ = ask(query(tmp_path, identifier), answer="Hay 1 señal de sobreprecio probado.")
    assert "0 señales existentes" in result["response"]
    assert "sobreprecio probado" not in result["response"]


@pytest.mark.parametrize(
    ("name", "raw"),
    [
        ("execute_run", "{}"),
        ("web_search", "{}"),
        ("sql", "{}"),
        ("get_run_products", '{"run_id":"../secret"}'),
        ("get_run_products", '{"run_id":"' + str(uuid4()) + '"}'),
        ("get_latest_investigation_run", '{"sql":"select"}'),
    ],
)
def test_unsafe_or_cross_run_tool_calls_are_rejected(name, raw):
    with pytest.raises(AssistantError):
        arguments(name, raw, str(uuid4()))


def chat_at(tmp_path, factory):
    settings = Settings(
        _env_file=None,
        database_url="postgresql://unused",
        local_storage_path=tmp_path / "documents",
    )
    return InvestigationChat(settings, factory, now=lambda: NOW)


@pytest.mark.parametrize("status", ["running", "queued"])
def test_running_returns_provisional_stage_without_azure_or_old_result(tmp_path, status):
    root = tmp_path / "investigation"
    persist(root, created=datetime(2026, 11, 10, tzinfo=UTC), result=fixture_result())
    new = persist(root, status=status)
    factory = Mock(side_effect=AssertionError("No Azure for provisional status"))
    service = chat_at(tmp_path, factory)
    reply = service.chat("¿Cómo va la última corrida?", None, None, uuid4())
    assert reply.run_references == [str(new)]
    assert "provisionales" in reply.response
    assert "865" in reply.response
    assert "0 señales" not in reply.response
    factory.assert_not_called()


def test_missing_run_or_no_run_does_not_open_foundry_or_create_directories(tmp_path):
    factory = Mock(side_effect=AssertionError("No Azure"))
    service = chat_at(tmp_path, factory)
    reply = service.chat("¿Qué encontró?", None, None, uuid4())
    assert reply.run_references == []
    assert not (tmp_path / "investigation").exists()
    factory.assert_not_called()


def test_http_chat_owner_context_and_exact_run(tmp_path):
    root = tmp_path / "investigation"
    identifier = persist(root, result=fixture_result())

    @contextmanager
    def factory():
        model = Model()
        model.run_id = str(identifier)
        yield InvestigationAssistant(model)

    service = chat_at(tmp_path, factory)
    app = FastAPI()
    owner = uuid4()
    app.state.investigation_assistant_chat = service
    app.state.current_user_provider = lambda _: owner
    app.include_router(router)
    client = TestClient(app)
    response = client.post(
        "/api/v1/investigation/assistant/chat",
        json={"message": "¿Qué encontró?", "run_id": str(identifier)},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_references"] == [str(identifier)]
    assert payload["process_references"] == ["CO1.REQ.123"]
    second = client.post(
        "/api/v1/investigation/assistant/chat",
        json={"message": "¿Qué dejó esta corrida?", "conversation_id": payload["conversation_id"]},
    )
    assert second.status_code == 200
    app.state.current_user_provider = lambda _: uuid4()
    assert (
        client.post(
            "/api/v1/investigation/assistant/chat",
            json={"message": "hola", "conversation_id": payload["conversation_id"]},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/investigation/assistant/chat", json={"message": "hola", "execute": True}
        ).status_code
        == 422
    )


def test_transport_uses_only_local_function_contracts_and_no_remote_agent_updates():
    remote = Mock()
    AzureTransport(remote, "deployment").respond(
        [], TOOL_SCHEMAS, "get_latest_investigation_run", 10
    )
    call = remote.responses.create.call_args.kwargs
    assert call["store"] is False
    assert call["parallel_tool_calls"] is False
    assert all(t["type"] == "function" for t in call["tools"])
    assert "agent_reference" not in json.dumps(call)
    assert "documented_unconfirmed_offer" in POLICY


def test_result_from_other_run_is_rejected_without_falling_back(tmp_path):
    identifier = persist(tmp_path, result=fixture_result())
    path = tmp_path / "market-date-runs" / str(identifier) / "result.json"
    data = json.loads(path.read_text())
    data["investigation_run_id"] = str(uuid4())
    path.write_text(json.dumps(data), encoding="utf8")
    with pytest.raises(ValueError, match="another run"):
        query(tmp_path, identifier)


def test_query_filters_requested_type_but_not_a_question_about_products(tmp_path):
    root = tmp_path / "investigation"
    private = persist(root, created=datetime(2026, 11, 11, 14, tzinfo=UTC), result=fixture_result())
    public = persist(root, kind="state_vs_state", result=fixture_result())
    service = chat_at(tmp_path, Mock())
    assert service.query("¿Qué encontró la última corrida Estado vs mercado privado?").metadata()[
        "run_id"
    ] == str(private)
    assert service.query("¿Qué productos llegaron a mercado privado?").metadata()["run_id"] == str(
        public
    )
    assert service.query("¿Qué encontró la última corrida Estado vs Estado?").metadata()[
        "run_id"
    ] == str(public)


def test_today_uses_bogota_day_not_utc_calendar(tmp_path):
    root = tmp_path / "investigation"
    persist(root, created=datetime(2026, 11, 11, 3, tzinfo=UTC), result=fixture_result())
    service = chat_at(tmp_path, Mock())
    assert service.query("¿Qué encontró la corrida de hoy?").metadata()["found"] is False


def test_private_comparison_and_existing_signal_are_exposed_without_calculation(tmp_path):
    data = fixture_result()
    r = market()
    r["comparison"] = {
        "public_unit_price": "100",
        "private_median_price": "50",
        "percentage_difference": "100",
    }
    r["signal"] = {
        "type": "PUBLIC_VS_PRIVATE_PRICE_DIFFERENCE",
        "meaning": "Diferencia persistida para revisar",
    }
    data["market_reports"] = [r]
    identifier = persist(tmp_path, result=data)
    q = query(tmp_path, identifier)
    assert q.comparisons()["items"][0]["kind"] == "state_vs_private_market"
    assert q.comparisons()["items"][0]["percentage_difference"] == "100"
    assert q.signals()["total"] == 1


def test_unknown_specific_run_does_not_use_latest_even_if_it_exists(tmp_path):
    root = tmp_path / "investigation"
    persist(root, result=fixture_result())
    service = chat_at(tmp_path, Mock(side_effect=AssertionError("No model")))
    reply = service.chat("¿Qué encontró?", None, uuid4(), uuid4())
    assert reply.run_references == []


def test_provider_failure_does_not_leak_secret_or_paths(tmp_path):
    root = tmp_path / "investigation"
    persist(root, result=fixture_result())

    @contextmanager
    def factory():
        raise RuntimeError("api_key=SECRET C:/private/folder")
        yield

    service = chat_at(tmp_path, factory)
    with pytest.raises(AssistantError, match="investigation_read_unavailable") as error:
        service.chat("¿Qué encontró?", None, None, uuid4())
    assert "SECRET" not in str(error.value)


def test_private_products_do_not_double_count_old_extraction_observations(tmp_path):
    data = fixture_result()
    data["processes"].append(
        {
            "id": "CO1.REQ.OLD",
            "reference": "OLD",
            "entity": "Entidad B",
            "products": [{"id": "old-observation", "description": "Context only"}],
        }
    )
    identifier = persist(tmp_path, result=data)
    q = query(tmp_path, identifier)
    assert q.products()["total"] == 1
    assert q.products()["items"][0]["product_id"] == "item1"


def test_cli_snapshot_has_no_foundry_or_data_writes(tmp_path, monkeypatch, capsys):
    import importlib.util

    path = Path(__file__).resolve().parents[3] / "scripts/eureka_investigation_assistant.py"
    spec = importlib.util.spec_from_file_location("investigation_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    settings = Settings(
        _env_file=None,
        database_url="postgresql://unused",
        local_storage_path=tmp_path / "documents",
    )
    identifier = persist(tmp_path / "investigation", result=fixture_result())
    monkeypatch.setattr(module, "Settings", lambda: settings)
    assert module.main(["--snapshot", "--run-id", str(identifier)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["mode"] == "offline_snapshot"
    assert data["run"]["run_id"] == str(identifier)
    assert data["tools"]["get_run_signals"]["total"] == 0


def test_unreadable_run_metadata_does_not_silently_select_old_run(tmp_path):
    persist(tmp_path, result=fixture_result())
    newest = persist(tmp_path, status="running")
    (tmp_path / "market-date-runs" / str(newest) / "run.json").write_text("broken", encoding="utf8")
    with pytest.raises(ValueError, match="unreadable metadata"):
        query(tmp_path)


def test_azure_serializes_all_messages_explicitly_without_mutating_history():
    remote = Mock()
    inputs = [
        {"role": "developer", "content": "policy"},
        {"role": "user", "content": "previous"},
        {"role": "assistant", "content": "answer"},
        {"role": "user", "content": "question"},
        {"type": "function_call", "name": "get_run_products", "call_id": "call_1"},
        {"type": "function_call_output", "call_id": "call_1", "output": "{}"},
        {"role": "developer", "content": "grounding reminder"},
    ]
    original = copy.deepcopy(inputs)
    AzureTransport(remote, "deployment").respond(inputs, TOOL_SCHEMAS, None, 10)
    actual = remote.responses.create.call_args.kwargs["input"]
    assert all(item["type"] == "message" for item in actual if "role" in item)
    assert actual[4:6] == original[4:6]
    assert inputs == original


def test_strict_azure_wire_contract_completes_real_tool_dispatch_loop(tmp_path):
    identifier = persist(tmp_path, result=fixture_result())
    q = query(tmp_path, identifier)
    model = Model()
    model.run_id = str(identifier)

    def create(**kwargs):
        # Reproduces Azure's discriminated input contract, missed by the old mock.
        assert all(item.get("type") == "message" for item in kwargs["input"] if "role" in item)
        choice = kwargs["tool_choice"]
        return model.respond(
            kwargs["input"],
            kwargs["tools"],
            choice["name"] if isinstance(choice, dict) else None,
            kwargs["timeout"],
        )

    remote = Mock()
    remote.responses.create.side_effect = create
    result = InvestigationAssistant(AzureTransport(remote, "deployment")).ask("¿Qué encontró?", q)
    assert {c["name"] for c in result["tool_calls"]} == {"get_latest_investigation_run", *READERS}
    assert result["run_references"] == [str(identifier)]


def test_provider_400_preserves_safe_stage_status_code_and_param():
    from public_procurement.agents.investigation_assistant.diagnostics import failure

    class ProviderError(Exception):
        status_code = 400
        body: ClassVar[dict] = {
            "error": {"code": "invalid_value", "param": "input[1]", "message": "Invalid value: ''."}
        }

    remote = Mock()
    remote.responses.create.side_effect = ProviderError("DO_NOT_PRINT")
    with pytest.raises(AssistantError) as caught:
        AzureTransport(remote, "deployment").respond([], TOOL_SCHEMAS, None, 5)
    diagnostic = caught.value.diagnostic
    assert diagnostic == failure("responses.create", ProviderError())
    assert diagnostic["http_status"] == 400
    assert diagnostic["parameter"] == "input[1]"
    assert diagnostic["error_code"] == "invalid_value"
    assert "DO_NOT_PRINT" not in json.dumps(diagnostic)


def test_diagnostics_never_dump_sdk_headers_tokens_or_credential_trace(monkeypatch, tmp_path):
    from public_procurement.agents.investigation_assistant.diagnostics import failure

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TEST_API_KEY", "unlabelled-secret")
    (tmp_path / ".env").write_text("SERVICE_SECRET=dotenv-secret\n", encoding="utf8")

    class ProviderError(Exception):
        body: ClassVar[dict] = {
            "message": (
                'Invalid unlabelled-secret dotenv-secret; api_key="quoted-secret" '
                "Bearer bearer-secret https://example.test/?token=url-secret "
                'ConnectionString="Server=private;Password=pass-secret" '
                "eyJabc.def.ghi C:/private/cache"
            ),
            "headers": {"Authorization": "HEADER_SECRET"},
        }

    serialized = json.dumps(failure("responses.create", ProviderError("RAW_SECRET")))
    for secret in (
        "unlabelled-secret",
        "dotenv-secret",
        "quoted-secret",
        "bearer-secret",
        "url-secret",
        "pass-secret",
        "eyJabc",
        "C:/private",
        "RAW_SECRET",
        "HEADER_SECRET",
    ):
        assert secret not in serialized

    class ClientAuthenticationError(Exception):
        pass

    diagnostic = failure("responses.create", ClientAuthenticationError("TRACE_TOKEN"))
    assert "TRACE_TOKEN" not in json.dumps(diagnostic)
    assert "DefaultAzureCredential" in diagnostic["message"]


def test_foundry_configuration_diagnostic_contains_only_presence_booleans():
    from public_procurement.agents.investigation_assistant.diagnostics import configuration

    result = configuration(
        Ns(
            azure_foundry_project_endpoint="https://private.example/api/projects/project",
            eureka_foundry_model_deployment="deployment",
            eureka_foundry_timeout_seconds=120,
        )
    )
    assert result["project_endpoint_present"] is True
    assert result["remote_agent_required"] is False
    assert all(isinstance(value, bool) for value in result.values())
    assert "private.example" not in json.dumps(result)


def test_cli_failure_prints_structured_safe_error(monkeypatch, capsys):
    import importlib.util

    path = Path(__file__).resolve().parents[3] / "scripts/eureka_investigation_assistant.py"
    spec = importlib.util.spec_from_file_location("investigation_cli_failure", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    error = AssistantError(
        "foundry_unavailable",
        diagnostic={
            "stage": "responses.create",
            "http_status": 401,
            "exception_class": "AuthenticationError",
            "message": "Authentication required",
        },
    )
    monkeypatch.setattr(module, "InvestigationChat", Mock(side_effect=error))
    assert module.main(["--diagnose"]) == 1
    output = capsys.readouterr()
    assert not output.out
    first = json.loads(output.err.splitlines()[0])
    assert first["diagnostic"]["http_status"] == 401
    assert first["diagnostic"]["stage"] == "responses.create"
