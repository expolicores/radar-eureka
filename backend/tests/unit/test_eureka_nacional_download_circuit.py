"""Regression tests for the SECOP II download circuit classification. Offline fakes only."""

import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_cdp_stream as edge
import eureka_nacional_en01 as en01
from spike_licitaciones_info import SpikeDocument

SECOP = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId="


class Harness:
    """Runs analyze_documents for successive processes sharing one DownloadState."""

    def __init__(self, tmp_path, monkeypatch, *, edge_enabled=True):
        self.monkeypatch = monkeypatch
        # The stream marker lives in the run's parent: keep it inside this test's tmp_path.
        run = tmp_path / "run"
        run.mkdir()
        self.storage = en01.spike.LocalBinaryStorage(run / "binaries")
        self.state = en01.DownloadState(run, self.storage, edge_enabled=edge_enabled)
        assert self.state.stream_marker.parent == tmp_path
        self.settings = en01.settings_for_run(tmp_path, "tesseract", None)
        self.metrics, self.errors = Counter(), []
        self.client = SimpleNamespace(deadline=time.monotonic() + 360, page=Mock(), reserve=Mock())
        self.edge_calls = 0

    def process(
        self,
        reference,
        name,
        *,
        direct_status=403,
        direct_code="http_error",
        edge_error=None,
        allowance=2,
    ):
        doc = SpikeDocument(name, "pdf", SECOP + reference, reference)
        self.monkeypatch.setattr(en01, "fetch_inventory", Mock(return_value=[doc]))

        def direct(*_args, diagnostics):
            if direct_status is not None:
                diagnostics["http_status"] = direct_status
            raise en01.AcquisitionError(direct_code, "rechazado")

        def stream(*args, cdp_url, parent_page):
            self.edge_calls += 1
            args[3]["error"] = edge_error
            raise en01.AcquisitionError(edge_error, "rechazado")

        self.monkeypatch.setattr(en01.spike, "download_document", direct)
        self.monkeypatch.setattr(edge, "download_stream_pdf", stream)
        en01.analyze_documents(
            self.client,
            {"inventory_keys": {}, "process_reference": reference},
            self.storage,
            self.settings,
            allowance,
            self.metrics,
            [],
            self.errors,
            download_state=self.state,
        )

    def kinds(self):
        return [e.get("failure_kind") for e in self.errors]


def test_size_rejections_after_streaming_never_open_the_circuit(tmp_path, monkeypatch):
    # Arrange
    h = Harness(tmp_path, monkeypatch)

    # Act
    for ref in ("1", "2", "3", "4"):
        h.process(ref, "Invitación", edge_error="declared_size_limit")

    # Assert
    assert h.edge_calls == 4
    assert h.kinds() == ["size_rejection"] * 4
    assert h.metrics["download_size_rejection"] == 4
    assert h.state.failed_processes == []


def test_403_on_documents_without_authorized_streaming_never_open_the_circuit(
    tmp_path, monkeypatch
):
    h = Harness(tmp_path, monkeypatch)

    for ref in ("1", "2", "3", "4"):
        h.process(ref, "Estudios previos")

    assert h.edge_calls == 0
    assert h.kinds() == ["access_restricted_no_fallback"] * 4
    assert h.metrics["download_access_restricted_no_fallback"] == 4


def test_skipped_stream_for_allowance_is_recorded_and_not_counted(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)

    for ref in ("1", "2", "3"):
        h.process(ref, "Invitación", allowance=1)

    assert h.edge_calls == 0
    assert h.kinds() == ["fallback_skipped"] * 3
    assert {e["download_diagnostics"]["edge_skipped"] for e in h.errors} == {"document_allowance"}
    assert h.state.failed_processes == []


def test_disabled_streaming_is_a_skipped_fallback_not_infrastructure(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch, edge_enabled=False)

    for ref in ("1", "2", "3"):
        h.process(ref, "Invitación")

    assert h.kinds() == ["fallback_skipped"] * 3
    assert h.errors[0]["download_diagnostics"]["edge_skipped"] == "fallback_disabled"


def test_real_stream_failures_keep_the_same_threshold(tmp_path, monkeypatch):
    # Arrange
    h = Harness(tmp_path, monkeypatch)
    h.process("1", "Invitación", edge_error="protocol_error")
    h.process("11", "Invitación", edge_error="unexpected_response")

    # Act / Assert: the third infrastructure failure across two processes opens it.
    with pytest.raises(en01.BudgetReached, match="download_circuit_open"):
        h.process("2", "Invitación", edge_error="protocol_error")
    assert h.kinds() == ["infrastructure"] * 3


@pytest.mark.parametrize(("status", "code"), [(500, "http_error"), (None, "timeout")])
def test_direct_errors_other_than_403_are_infrastructure(tmp_path, monkeypatch, status, code):
    h = Harness(tmp_path, monkeypatch)
    h.process("1", "Estudios previos", direct_status=status, direct_code=code)
    h.process("2", "Estudios previos", direct_status=status, direct_code=code)

    with pytest.raises(en01.BudgetReached, match="download_circuit_open"):
        h.process("3", "Estudios previos", direct_status=status, direct_code=code)


def test_predictable_rejections_neither_count_nor_reset_real_failures(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    h.process("1", "Invitación", edge_error="protocol_error")
    h.process("2", "Invitación", edge_error="declared_size_limit")
    h.process("3", "Estudios previos")
    h.process("4", "Invitación", edge_error="protocol_error")

    with pytest.raises(en01.BudgetReached, match="download_circuit_open"):
        h.process("5", "Invitación", edge_error="protocol_error")
    assert h.kinds() == [
        "infrastructure",
        "size_rejection",
        "access_restricted_no_fallback",
        "infrastructure",
        "infrastructure",
    ]


def test_uncertain_close_still_stops_immediately(tmp_path, monkeypatch):
    h = Harness(tmp_path, monkeypatch)
    h.state.stream_marker.write_text("x", encoding="utf-8")

    with pytest.raises(en01.BudgetReached, match="download_close_unverified"):
        h.process("1", "Estudios previos")


@pytest.mark.parametrize(
    ("code", "diagnostics", "role", "expected"),
    [
        ("too_large", {}, "primary", "size_rejection"),
        ("stream_size_limit", {}, "support", "size_rejection"),
        ("http_error", {"http_status": 403}, "support", "access_restricted_no_fallback"),
        ("http_error", {"http_status": 403}, "primary", "fallback_skipped"),
        (
            "protocol_error",
            {"http_status": 403, "edge": {"error": "protocol_error"}},
            "primary",
            "infrastructure",
        ),
        ("invalid_content", {}, "primary", "infrastructure"),
    ],
)
def test_failure_kind_table(code, diagnostics, role, expected):
    state = SimpleNamespace(edge_enabled=True)

    assert en01.download_failure_kind(code, diagnostics, {"role": role}, state) == expected
