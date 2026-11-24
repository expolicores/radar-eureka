import base64
import sys
from collections import deque
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import eureka_nacional_edge_download as edge
from spike_licitaciones_info import SpikeDocument

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError


class FakePage:
    url = "https://col.licitaciones.info/cliente/contratos"

    def __init__(self, states):
        self.states = deque(states)
        self.cancelled = False
        self.started = None

    def evaluate(self, code, args):
        if code == edge.START:
            self.started = args
        elif code == edge.CANCEL:
            self.cancelled = True
            return True
        elif code == edge.STATE:
            return self.states.popleft()
        elif code == edge.READ:
            return True
        return None


PDF = b"%PDF-1.4\nprueba\n%%EOF"
DOC = SpikeDocument(
    "Invitación",
    "pdf",
    "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=1&extra=1",
    "1",
)
SETTINGS = SimpleNamespace(document_max_bytes=1024, document_timeout_seconds=12)


def test_edge_stream_preserves_query_and_stores_only_verified_pdf(tmp_path):
    page = FakePage(
        [
            {"size": len(PDF), "status": 200},
            {"chunk": base64.b64encode(PDF).decode(), "status": 200},
            {"eof": True, "status": 200},
        ]
    )
    diag = {}
    result = edge.download_from_edge(page, DOC, LocalBinaryStorage(tmp_path), SETTINGS, diag)
    assert result.observed_size == len(PDF)
    assert page.started["url"] == DOC.source_url
    assert page.started["timeout"] == 12000
    assert page.cancelled
    assert diag["cancellation_confirmed"]
    assert "url" not in diag


@pytest.mark.parametrize(
    ("states", "code"),
    [
        ([{"size": 2048, "status": 200}], "edge_length_invalid"),
        ([{"error": "edge_fetch_rejected"}], "edge_fetch_rejected"),
        ([{"error": "edge_timeout"}], "edge_timeout"),
        ([{"size": 6, "status": 200}, {"chunk": "PGh0bWw+", "status": 200}], "invalid_content"),
        (
            [{"size": 6, "status": 200}, {"chunk": base64.b64encode(b"X" * 1025).decode()}],
            "too_large",
        ),
    ],
)
def test_edge_rejections_abort_and_leave_no_published_file(tmp_path, states, code):
    page = FakePage(states)
    diag = {}
    with pytest.raises(AcquisitionError) as error:
        edge.download_from_edge(page, DOC, LocalBinaryStorage(tmp_path), SETTINGS, diag)
    assert error.value.code == code
    assert page.cancelled
    assert diag["cancellation_confirmed"]
    assert not (tmp_path / "sha256").exists()
