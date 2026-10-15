from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.documents.domain.document import DownloadSummary
from public_procurement.entrypoints.cli import __main__ as cli


def configure(monkeypatch):
    settings, engine, service = Mock(), Mock(), Mock()
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    monkeypatch.setattr(cli, "create_db_engine", lambda configuration: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda configured_engine: Mock())
    monkeypatch.setattr(cli, "build_document_service", lambda sessions, configuration: service)
    return service, engine


def test_sync_dry_run_does_not_download(monkeypatch) -> None:
    service, engine = configure(monkeypatch)
    service.sync.return_value = []
    result = CliRunner().invoke(cli.app, ["sync-documents", "--process", "CO1.REQ.1", "--dry-run"])
    assert result.exit_code == 0
    service.sync.assert_called_once_with("CO1.REQ.1", dry_run=True)
    service.download.assert_not_called()
    engine.dispose.assert_called_once()


def test_download_failure_is_nonzero_and_preserves_disposal(monkeypatch) -> None:
    service, engine = configure(monkeypatch)
    service.download.return_value = DownloadSummary(2, 1)
    result = CliRunner().invoke(cli.app, ["download-documents", "--process", "CO1.REQ.1"])
    assert result.exit_code == 1
    assert "1 fallidos" in result.output
    engine.dispose.assert_called_once()
