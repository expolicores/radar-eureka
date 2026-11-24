import io
import json
from http.client import IncompleteRead
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.adapters.secop import SecopDownloader, validate_url
from public_procurement.documents.domain.document import AcquisitionError, SourceDocument

URL = "https://community.secop.gov.co/Public/Archive/RetrieveFile/Index?DocumentId=1"
PDF = b"%PDF-1.4\ncomplete\n%%EOF"


class Response(io.BytesIO):
    status = 200

    def __init__(self, data=PDF, headers=None, url=URL):
        super().__init__(data)
        self.headers = headers or {
            "Content-Type": "application/pdf",
            "Content-Length": str(len(data)),
        }
        self.url = url

    def geturl(self):
        return self.url


def source(url=URL):
    return SourceDocument("1", "P", "file.pdf", None, url)


@pytest.mark.parametrize(
    "url",
    [
        "http://community.secop.gov.co/file",
        "https://evil.test/file",
        "https://community.secop.gov.co.evil.test/file",
        "file:///C:/secret",
        "https://user@community.secop.gov.co/file",
        "https://community.secop.gov.co:8080/file",
    ],
)
def test_unsafe_urls_are_rejected_before_request(url) -> None:
    with pytest.raises(AcquisitionError, match="HTTPS"):
        validate_url(url)


def test_redirect_is_validated_before_following(tmp_path) -> None:
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.side_effect = HTTPError(
        URL, 302, "redirect", {"Location": "https://evil.test"}, None
    )
    with pytest.raises(AcquisitionError) as error:
        downloader.download(source(), LocalBinaryStorage(tmp_path))
    assert error.value.code == "unsafe_url"
    assert downloader._opener.open.call_count == 1


def test_allowed_relative_redirect_downloads_stream(tmp_path) -> None:
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.side_effect = [
        HTTPError(URL, 302, "redirect", {"Location": "/download"}, None),
        Response(),
    ]
    result = downloader.download(source(), LocalBinaryStorage(tmp_path))
    assert result.observed_size == len(PDF)
    assert (
        downloader._opener.open.call_args.args[0].full_url
        == "https://community.secop.gov.co/download"
    )


@pytest.mark.parametrize(
    ("headers", "code"),
    [
        ({"Content-Type": "text/html"}, "invalid_content"),
        ({"Content-Length": "10000"}, "too_large"),
        ({"Content-Length": "bad"}, "invalid_size"),
        ({"Content-Encoding": "gzip"}, "invalid_encoding"),
    ],
)
def test_invalid_headers_do_not_publish_files(tmp_path, headers, code) -> None:
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.return_value = Response(headers=headers)
    with pytest.raises(AcquisitionError) as error:
        downloader.download(source(), LocalBinaryStorage(tmp_path))
    assert error.value.code == code
    assert not (tmp_path / "sha256").exists()


def test_interrupted_stream_is_reported_and_cleans_temporary(tmp_path) -> None:
    class Broken(Response):
        def read1(self, size=-1):
            raise IncompleteRead(b"partial")

    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.return_value = Broken()
    with pytest.raises(AcquisitionError) as error:
        downloader.download(source(), LocalBinaryStorage(tmp_path))
    assert error.value.code == "network_error"
    assert list((tmp_path / ".tmp").iterdir()) == []


def test_deadline_is_checked_during_stream(monkeypatch, tmp_path) -> None:
    from public_procurement.documents.adapters import secop

    times = iter([0, 0, 0, 20])
    monkeypatch.setattr(secop.time, "monotonic", lambda: next(times))
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.return_value = Response()
    with pytest.raises(AcquisitionError) as error:
        downloader.download(source(), LocalBinaryStorage(tmp_path))
    assert error.value.code == "timeout"


@pytest.mark.parametrize("status", [403, 429, 503])
def test_http_diagnostics_do_not_persist_headers_or_url(tmp_path, status):
    diagnostics = {}
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.side_effect = HTTPError(
        URL + "&token=private",
        status,
        "secret-error-body",
        {"Content-Type": "text/html; charset=utf-8", "Set-Cookie": "session=secret"},
        None,
    )
    with pytest.raises(AcquisitionError) as error:
        downloader.download(source(), LocalBinaryStorage(tmp_path), diagnostics=diagnostics)
    assert error.value.code == "http_error"
    assert diagnostics == {
        "stage": "response_headers",
        "http_status": status,
        "exception_type": "HTTPError",
        "content_type": "text/html",
        "rejection_reason": "http_error",
        "redirects": [],
    }
    assert not (tmp_path / "sha256").exists()


def test_non_200_response_and_blocked_redirect_are_distinguishable(tmp_path):
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    response = Response()
    response.status = 206
    downloader._opener.open.return_value = response
    diagnostics = {}
    with pytest.raises(AcquisitionError, match="descarga completa"):
        downloader.download(source(), LocalBinaryStorage(tmp_path), diagnostics=diagnostics)
    assert diagnostics["http_status"] == 206
    assert diagnostics["rejection_reason"] == "http_error"
    downloader._opener.open.reset_mock()
    downloader._opener.open.side_effect = HTTPError(
        URL,
        302,
        "redirect",
        {"Location": "https://user:secret@example.test/?token=private"},
        None,
    )
    with pytest.raises(AcquisitionError) as error:
        downloader.download(source(), LocalBinaryStorage(tmp_path), diagnostics=diagnostics)
    assert error.value.code == "unsafe_url"
    assert diagnostics["stage"] == "validate_redirect"
    assert diagnostics["redirects"] == [
        {"http_status": 302, "content_type": None, "destination": "blocked"}
    ]
    rendered = json.dumps(diagnostics)
    assert all(marker not in rendered for marker in ("secret", "private", "example.test"))
    downloader._opener.open.assert_called_once()


def test_successful_redirect_records_only_safe_origin_class_and_media_type(tmp_path):
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.side_effect = [
        HTTPError(
            URL,
            302,
            "redirect",
            {"Location": "/download?token=private", "Content-Type": "bad/path/private"},
            None,
        ),
        Response(),
    ]
    diagnostics = {}
    downloader.download(source(), LocalBinaryStorage(tmp_path), diagnostics=diagnostics)
    assert diagnostics["stage"] == "completed"
    assert diagnostics["http_status"] == 200
    assert diagnostics["content_type"] == "application/pdf"
    assert diagnostics["rejection_reason"] is None
    assert diagnostics["redirects"] == [
        {"http_status": 302, "content_type": "other", "destination": "secop_other_path"}
    ]
    assert "private" not in json.dumps(diagnostics)


def test_transport_diagnostics_keep_exception_type_without_reason_text(tmp_path):
    downloader = SecopDownloader(10, 1000)
    downloader._opener = Mock()
    downloader._opener.open.side_effect = URLError(TimeoutError("private network detail"))
    diagnostics = {}
    with pytest.raises(AcquisitionError) as error:
        downloader.download(source(), LocalBinaryStorage(tmp_path), diagnostics=diagnostics)
    assert error.value.code == "network_error"
    assert diagnostics["stage"] == "open_response"
    assert diagnostics["exception_type"] == "URLError"
    assert diagnostics["underlying_exception_type"] == "TimeoutError"
    assert diagnostics["http_status"] is None
    assert "private" not in json.dumps(diagnostics)
