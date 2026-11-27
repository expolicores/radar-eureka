"""Offline tests for cross-run reuse of verified SECOP I receipts. Synthetic data only."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_secop1_acquire as acquire
import eureka_nacional_secop1_flow as flow

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage

CONSTANCIA = "26-13-12345678"
PDF = b"%PDF-1.7\n" + b"0" * (759_314 - 16) + b"\n%%EOF\n"  # 742 KB as displayed


def item(path_number, displayed="742 KB", constancia=CONSTANCIA):
    path = f"/2020/2020Q2/2026/INVMC/1/{constancia}/INVMC_PROCESO_{constancia}_1_{path_number}.pdf"
    return {
        "process_reference": f"licitaciones_info:1:{path_number}",
        "constancia": constancia,
        "document_id": f"secop1:{constancia}:{hashlib.sha256(path.encode()).hexdigest()}",
        "name": "Invitación",
        "extension": "pdf",
        "relative_path": path,
        "role": "primary",
        "role_hint": None,
        "displayed_size": displayed,
        "displayed_size_bytes": None,
    }


def run_dir(root, name, items, *, documents=True):
    run = root / name
    run.mkdir()
    flow.write_queue(run, items, run.name)
    if documents:
        (run / "documents.json").write_text(
            json.dumps(
                [
                    {
                        "process_reference": i["process_reference"],
                        "documents": [{**i, "complete": False, "role_source": "filename"}],
                    }
                    for i in items
                ]
            ),
            "utf-8",
        )
        (run / "processes.json").write_text(
            json.dumps(
                {"processes": [{"process_reference": i["process_reference"]} for i in items]}
            ),
            "utf-8",
        )
    return run


def acquired_source(root, entry, body=PDF, *, attempt_sha=None, name="en01-earlier"):
    """An earlier run that queued `entry`, stored `body` and recorded the attempt."""
    run = run_dir(root, name, [entry])
    storage = LocalBinaryStorage(run / "binaries")
    if body.rstrip().endswith(b"%%EOF"):
        stored = storage.store(
            [body],
            original_name="x.pdf",
            content_type="application/pdf",
            expected_size=len(body),
            max_bytes=flow.DOCUMENT_BYTES,
        )
    else:
        # The storage itself refuses PDFs without %%EOF; plant one to test the reuse check.
        digest = hashlib.sha256(body).hexdigest()
        path = run / "binaries" / "sha256" / digest[:2] / digest
        path.parent.mkdir(parents=True)
        path.write_bytes(body)
        stored = SimpleNamespace(
            storage_path=f"sha256/{digest[:2]}/{digest}", sha256=digest, observed_size=len(body)
        )
    outcome = {
        "storage_path": stored.storage_path,
        "sha256": stored.sha256,
        "received_bytes": stored.observed_size,
    }
    acquire.write_receipt(run, entry, outcome)
    path = acquire.reserve_attempt(run, entry, "a" * 64)
    acquire.finish_attempt(
        path,
        {
            "outcome": "stored",
            "sha256": attempt_sha or stored.sha256,
            "received_bytes": stored.observed_size,
            "pdf_eof_marker": True,
        },
    )
    return run, stored


def snapshot(run):
    return {p.relative_to(run): p.read_bytes() for p in run.rglob("*") if p.is_file()}


def test_verified_receipt_of_the_same_identity_is_reused_and_dequeued(tmp_path):
    # Arrange
    jerico, new_doc = item(1), item(2, "559 KB")
    source, stored = acquired_source(tmp_path, jerico)
    before = snapshot(source)
    target = run_dir(tmp_path, "en01-blind", [jerico, new_doc])

    # Act
    decisions = flow.reuse_receipts(target, tmp_path, LocalBinaryStorage)
    queue, record = flow.rebuild_queue(target)

    # Assert
    assert [d["decision"] for d in decisions] == ["reused_receipt", "acquire"]
    assert decisions[0]["source_run"] == "en01-earlier"
    assert decisions[0]["sha256"] == stored.sha256
    receipt = flow.load_receipts(target)[f"{jerico['document_id']}:pdf"]
    copy = (target / "binaries" / receipt["storage_path"]).read_bytes()
    assert hashlib.sha256(copy).hexdigest() == stored.sha256
    assert [i["document_id"] for i in queue["items"]] == [new_doc["document_id"]]
    assert queue["max_posts"] == 1
    assert [d["decision"] for d in record["decisions"]] == ["reused_receipt", "queued"]
    assert snapshot(source) == before  # sources are never modified
    items, recorded = acquire.plan_batch(queue, target)
    assert [i["document_id"] for i in items] == [new_doc["document_id"]]
    assert recorded == 0


def test_same_constancia_and_title_with_another_path_is_not_reused(tmp_path):
    acquired_source(tmp_path, item(1))
    target = run_dir(tmp_path, "en01-blind", [item(9)])  # same constancia, other document

    decisions = flow.reuse_receipts(target, tmp_path, LocalBinaryStorage)

    assert [d["decision"] for d in decisions] == ["acquire"]
    assert flow.load_receipts(target) == {}


@pytest.mark.parametrize(
    ("setup", "reason"),
    [
        ("drop_queue", "identity_not_in_source_queue"),
        ("attempt_sha", "no_matching_stored_attempt"),
        ("tamper_binary", "binary_unverified"),
        ("no_eof", "pdf_markers_missing"),
        ("displayed", "displayed_size_mismatch"),
    ],
)
def test_each_failed_check_blocks_reuse(tmp_path, setup, reason):
    # Arrange
    jerico = item(1)
    body = PDF if setup != "no_eof" else PDF.replace(b"%%EOF", b"%%END")
    source, stored = acquired_source(
        tmp_path, jerico, body, attempt_sha="f" * 64 if setup == "attempt_sha" else None
    )
    if setup == "drop_queue":
        flow.write_queue(source, [item(5)], source.name)
    if setup == "tamper_binary":
        path = source / "binaries" / stored.storage_path
        path.write_bytes(path.read_bytes()[:-1] + b"X")
    target_item = item(1, "2.10 MB") if setup == "displayed" else jerico
    target = run_dir(tmp_path, "en01-blind", [target_item])

    # Act
    decisions = flow.reuse_receipts(target, tmp_path, LocalBinaryStorage)

    # Assert
    assert decisions[0]["decision"] == "acquire"
    assert decisions[0]["rejected_sources"] == [{"source_run": "en01-earlier", "reason": reason}]
    assert flow.load_receipts(target) == {}


def test_displayed_size_tolerance_follows_the_rounding():
    assert flow.displayed_size_matches({"displayed_size": "742 KB"}, 759_314) is True
    assert flow.displayed_size_matches({"displayed_size": "742 KB"}, 760_400) is False
    assert flow.displayed_size_matches({"displayed_size": "2.10 MB"}, 2_203_048) is True
    assert flow.displayed_size_matches({"displayed_size": "2.10 MB"}, 2_215_000) is False
    assert flow.displayed_size_matches({"displayed_size": ""}, 10) is None


def test_reuse_is_deterministic_and_idempotent(tmp_path):
    jerico, new_doc = item(1), item(2, "559 KB")
    acquired_source(tmp_path, jerico)
    target = run_dir(tmp_path, "en01-blind", [jerico, new_doc])

    flow.reuse_receipts(target, tmp_path, LocalBinaryStorage)
    first = flow.rebuild_queue(target)[0]["batch_sha256"]
    again = flow.reuse_receipts(target, tmp_path, LocalBinaryStorage)

    # The reused document already left the queue; repeating changes nothing.
    assert [d["decision"] for d in again] == ["acquire"]
    assert flow.rebuild_queue(target)[0]["batch_sha256"] == first
    assert len(flow.load_receipts(target)) == 1


def test_cli_refuses_reuse_once_the_batch_has_attempts(tmp_path, monkeypatch):
    import eureka_nacional_en01 as en01

    monkeypatch.setattr(en01, "OUTPUT_ROOT", tmp_path)
    target = run_dir(tmp_path, "en01-blind", [item(1)])
    (target / "secop1_attempts").mkdir()

    assert flow.main([target.name, "--reuse-receipts"]) == 1
    assert not (target / flow.REUSE_FILE).exists()
