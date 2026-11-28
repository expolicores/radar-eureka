"""Offline tests for the inventory-only batch. Synthetic runs; no network."""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_inventory_batch as batch


def process(identity, reference, *, keys=True, capable=True):
    return {
        "process_reference": reference,
        "source": "secop2",
        "source_identity": identity,
        "entity_name": f"Entidad {identity[-1]}",
        "department": "Huila",
        "deadline_at": "2026-12-03T18:00:00-05:00",
        "object": "Suministro",
        "inventory_capable": capable,
        "inventory_keys": {
            "idContrato": 1,
            "id_fuente_contract": 3,
            "idUltimaFase": identity if keys else None,
        },
    }


def row(identity, *, excluded=None, source="secop2", priority="A"):
    return {
        "source_identity": identity,
        "source": source,
        "excluded_reason": excluded,
        "commercial_priority": priority,
        "validity_status": "open",
    }


def stored_run(root, processes, rows):
    run = root / "en01-src"
    run.mkdir()
    (run / "processes.json").write_text(json.dumps({"processes": processes}), "utf-8")
    (run / "window_reevaluation_10d.json").write_text(json.dumps({"rows": rows}), "utf-8")
    return run


def two_process_run(root):
    return stored_run(
        root,
        [process("CO1.NTC.1", "r1"), process("CO1.NTC.2", "r2")],
        [row("CO1.NTC.1"), row("CO1.NTC.2", priority="B")],
    )


def test_plan_binds_identities_keys_and_budget_to_the_digest(tmp_path):
    # Arrange
    two_process_run(tmp_path)

    # Act
    plan = batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.1", "CO1.NTC.2"])

    # Assert
    assert [i["source_identity"] for i in plan["items"]] == ["CO1.NTC.1", "CO1.NTC.2"]
    assert plan["limits"]["downloads"] == plan["limits"]["feed_requests"] == 0
    assert plan["budget"]["expected_credits"] == 5
    assert plan["budget"]["worst_case_credits"] == 21
    assert plan["batch_sha256"] == batch.digest(plan)


@pytest.mark.parametrize(
    ("rows", "processes", "match"),
    [
        ([row("CO1.NTC.1", excluded="closed_process")], [process("CO1.NTC.1", "r1")], "elegible"),
        ([row("CO1.NTC.1", source="secop1")], [process("CO1.NTC.1", "r1")], "elegible"),
        ([row("CO1.NTC.1")], [process("CO1.NTC.1", "r1", keys=False)], "Claves"),
        ([row("CO1.NTC.1")], [process("CO1.NTC.1", "r1", capable=False)], "Claves"),
        ([], [process("CO1.NTC.1", "r1")], "unica"),
        (
            [row("CO1.NTC.1")],
            [process("CO1.NTC.1", "r1"), process("CO1.NTC.1", "r9")],
            "unica",
        ),
    ],
)
def test_plan_rejects_ineligible_or_ambiguous_processes(tmp_path, rows, processes, match):
    stored_run(tmp_path, processes, rows)

    with pytest.raises(ValueError, match=match):
        batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.1"])


def test_plan_rejects_duplicates_and_already_inventoried_processes(tmp_path):
    two_process_run(tmp_path)
    earlier = tmp_path / "en01-old"
    earlier.mkdir()
    (earlier / "processes.json").write_text(
        json.dumps({"processes": [process("CO1.NTC.2", "old")]}), "utf-8"
    )
    (earlier / "documents.json").write_text(
        json.dumps([{"process_reference": "old", "documents": [{"name": "x"}]}]), "utf-8"
    )

    with pytest.raises(ValueError, match="repetidas"):
        batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.1", "CO1.NTC.1"])
    with pytest.raises(ValueError, match="ya inventariado"):
        batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.2"])


def test_tampered_plan_is_rejected(tmp_path):
    two_process_run(tmp_path)
    plan = batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.1"])
    target = batch.write_plan(tmp_path, plan)
    data = json.loads((target / batch.PLAN_FILE).read_text("utf-8"))
    data["limits"]["credit_limit"] = 200
    (target / batch.PLAN_FILE).write_text(json.dumps(data), "utf-8")

    with pytest.raises(ValueError, match="alterado"):
        batch.load_plan(target, plan["batch_sha256"])


def write_preflight(target, *, minutes_ago=1, profile="only_configured", count=1):
    record = {
        "feed_requests_forwarded": 0,
        "dedicated_browser": {"single_owner": True, "is_msedge": True},
        "verdict": {"session": "valid", "profile": profile, "profile_count": count},
        "recorded_at": (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat(),
    }
    (target / batch.PREFLIGHT_FILE).write_text(json.dumps(record), "utf-8")


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"minutes_ago": 30}, "preflight_stale"),
        ({"profile": "configured_with_others", "count": 2}, "preflight_not_satisfactory"),
    ],
)
def test_run_requires_a_recent_single_profile_preflight(tmp_path, kwargs, reason):
    two_process_run(tmp_path)
    plan = batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.1"])
    target = batch.write_plan(tmp_path, plan)
    write_preflight(target, **kwargs)

    assert batch.preflight_ok(target) == (False, reason)


class FakeClient:
    def __init__(self, limit=30):
        self.requests, self.limit, self.bootstraps = 0, limit, 0

    def bootstrap(self):
        self.bootstraps += 1
        self.requests += 1


class BudgetReachedError(Exception):
    pass


def fake_fetch(pages_by_identity):
    def fetch(client, keys):
        pages = pages_by_identity[keys["idUltimaFase"]]
        if client.requests + pages > client.limit:
            raise BudgetReachedError("request_budget")
        client.requests += pages
        return [
            SimpleNamespace(
                document_id=f"{keys['idUltimaFase']}-{n}",
                original_name=name,
                source_url=f"https://community.secop.gov.co/x?DocumentId={n}",
                extension="pdf",
            )
            for n, name in enumerate(
                ["CDP", "CONDICIONES GENERALES DE PARTICIPACION", "ESTUDIOS PREVIOS"]
            )
        ]

    return fetch


def planned_target(tmp_path):
    two_process_run(tmp_path)
    plan = batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.1", "CO1.NTC.2"])
    target = batch.write_plan(tmp_path, plan)
    write_preflight(target)
    return target, plan


def test_run_inventories_every_process_once_without_downloads(tmp_path):
    # Arrange
    target, plan = planned_target(tmp_path)
    client = FakeClient()

    # Act
    summary = batch.run_inventories(
        target, plan["batch_sha256"], client, fake_fetch({"CO1.NTC.1": 2, "CO1.NTC.2": 2})
    )

    # Assert
    assert summary["inventoried"] == 2
    assert summary["credits_used"] == 5
    assert summary["downloads"] == summary["feed_requests"] == 0
    assert client.bootstraps == 1
    documents = json.loads((target / "documents.json").read_text("utf-8"))
    assert {d["role"] for d in documents[0]["documents"]} == {"unknown", "primary", "support"}
    with pytest.raises(ValueError, match="no se repite"):
        batch.run_inventories(target, plan["batch_sha256"], client, fake_fetch({}))


def test_budget_stop_leaves_remaining_processes_pending(tmp_path):
    target, plan = planned_target(tmp_path)

    summary = batch.run_inventories(
        target,
        plan["batch_sha256"],
        FakeClient(limit=4),
        fake_fetch({"CO1.NTC.1": 2, "CO1.NTC.2": 2}),
    )

    assert summary["inventoried"] == 1
    assert summary["failed"] == 1
    assert summary["stop_reason"] == "request_budget"


def test_tranches_prefer_governing_documents_and_skip_administrative_support(tmp_path):
    target, plan = planned_target(tmp_path)
    batch.run_inventories(
        target, plan["batch_sha256"], FakeClient(), fake_fetch({"CO1.NTC.1": 2, "CO1.NTC.2": 2})
    )

    proposals = batch.proposed_tranches(target)

    assert [p["commercial_priority"] for p in proposals] == ["A", "B"]
    assert [d["name"] for d in proposals[0]["documents"]] == [
        "CONDICIONES GENERALES DE PARTICIPACION",
        "ESTUDIOS PREVIOS",
    ]


def test_inventory_failures_keep_the_reason_and_the_batch_continues(tmp_path):
    target, plan = planned_target(tmp_path)

    def fetch(client, keys):
        client.requests += 2
        if keys["idUltimaFase"] == "CO1.NTC.1":
            raise ValueError("Pagina documental repetida; inventario incompleto.")
        return []

    summary = batch.run_inventories(target, plan["batch_sha256"], FakeClient(), fetch)

    attempts = json.loads((target / batch.ATTEMPTS_FILE).read_text("utf-8"))["items"]
    assert attempts["r1"]["error_detail"].startswith("Pagina documental repetida")
    assert summary["failed"] == 1
    assert summary["inventoried"] == 1


def test_retry_plan_has_its_own_limits_name_and_prior_attempts(tmp_path):
    # Arrange: a first batch where CO1.NTC.1 failed.
    target, plan = planned_target(tmp_path)

    def fetch(client, keys):
        client.requests += 2
        if keys["idUltimaFase"] == "CO1.NTC.1":
            raise ValueError("Fila documental invalida.")
        return []

    batch.run_inventories(target, plan["batch_sha256"], FakeClient(), fetch)

    # Act
    retry = batch.build_plan(
        tmp_path, "en01-src", 10, ["CO1.NTC.1"], credit_limit=10, duration_seconds=120, suffix="r1"
    )
    retry_target = batch.write_plan(tmp_path, retry)

    # Assert
    assert retry_target.name == "en01-inv_src_r1"
    assert retry["limits"]["credit_limit"] == 10
    assert retry["limits"]["duration_seconds"] == 120
    [attempt] = retry["prior_attempts"]["CO1.NTC.1"]
    assert attempt["outcome"] == "failed"
    assert attempt["error_detail"] == "Fila documental invalida."
    assert (
        retry["batch_sha256"]
        != batch.build_plan(tmp_path, "en01-src", 10, ["CO1.NTC.1"])["batch_sha256"]
    )


@pytest.mark.parametrize(("credits", "seconds"), [(31, 120), (10, 361), (0, 120)])
def test_retry_limits_never_exceed_the_authorized_maximum(tmp_path, credits, seconds):
    two_process_run(tmp_path)

    with pytest.raises(ValueError, match="Limites"):
        batch.build_plan(
            tmp_path, "en01-src", 10, ["CO1.NTC.1"], credit_limit=credits, duration_seconds=seconds
        )


class Incomplete(Exception):  # noqa: N818 -- mirrors runtime.InventoryIncomplete
    def __init__(self, documents):
        super().__init__("Contrato de tabla documental desconocido.")
        self.documents = documents

    def diagnostic(self):
        return {"reason": "unreadable_page", "failed_page": 2, "shape": {"documentos_type": "dict"}}


def test_partial_inventory_is_kept_marked_incomplete_and_does_not_block_a_new_plan(tmp_path):
    target, plan = planned_target(tmp_path)
    full = fake_fetch({"CO1.NTC.1": 2, "CO1.NTC.2": 2})

    def fetch(client, keys):
        documents = full(client, keys)
        if keys["idUltimaFase"] == "CO1.NTC.1":
            raise Incomplete(documents[:1])
        return documents

    summary = batch.run_inventories(target, plan["batch_sha256"], FakeClient(), fetch)

    attempts = json.loads((target / batch.ATTEMPTS_FILE).read_text("utf-8"))["items"]
    assert attempts["r1"]["outcome"] == "incomplete"
    assert attempts["r1"]["diagnostic"]["failed_page"] == 2
    cases = {c["process_reference"]: c for c in json.loads((target / "documents.json").read_text())}
    assert cases["r1"]["inventory_complete"] is False
    assert len(cases["r1"]["documents"]) == 1
    assert cases["r2"]["inventory_complete"] is True
    assert summary["incomplete"] == 1
    assert "CO1.NTC.1" not in batch.inventoried_identities(tmp_path)
    assert "CO1.NTC.2" in batch.inventoried_identities(tmp_path)
