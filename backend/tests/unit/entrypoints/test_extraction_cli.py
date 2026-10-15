from unittest.mock import Mock

from typer.testing import CliRunner

from public_procurement.entrypoints.cli import __main__ as cli
from public_procurement.extraction.domain.content import (
    ExtractionResult,
    ExtractionStatus,
    ExtractorIdentity,
)

from ..extraction.test_services import Source


def setup_cli(monkeypatch):
    engine, service = Mock(), Mock()
    monkeypatch.setattr(cli, "load_settings", Mock())
    monkeypatch.setattr(cli, "create_db_engine", lambda settings: engine)
    monkeypatch.setattr(cli, "create_session_factory", lambda configured: Mock())
    monkeypatch.setattr(cli, "build_extraction_service", lambda sessions, settings: service)
    return engine, service


def test_extract_process_dry_run_and_status_output(monkeypatch) -> None:
    engine, service = setup_cli(monkeypatch)
    result = ExtractionResult(
        Source().documents[0],
        ExtractorIdentity("pdf-text", "v1"),
        ExtractionStatus.REQUIRES_OCR,
        None,
        pages_without_text=(1,),
        page_count=1,
    )
    service.extract_process.return_value = iter([result])
    response = CliRunner().invoke(
        cli.app, ["extract-documents", "--process", "CO1.REQ.1", "--dry-run"]
    )
    assert response.exit_code == 0
    assert "posible OCR requerido" in response.output
    assert "sin texto: [1]" in response.output
    service.extract_process.assert_called_once_with("CO1.REQ.1", dry_run=True)
    engine.dispose.assert_called_once()


def test_extract_document_reports_failure_and_nonzero_exit(monkeypatch) -> None:
    engine, service = setup_cli(monkeypatch)
    service.extract_document.return_value = ExtractionResult(
        Source().documents[0],
        ExtractorIdentity("pdf-text", "v1"),
        ExtractionStatus.FAILED,
        None,
        error_code="corrupt_file",
        error_message="Archivo corrupto",
    )
    response = CliRunner().invoke(cli.app, ["extract-document", "--document", "123"])
    assert response.exit_code == 1
    assert "corrupt_file" in response.output
    engine.dispose.assert_called_once()


def test_search_cli_uses_internal_search_service(monkeypatch) -> None:
    engine, service = setup_cli(monkeypatch)
    service.search.return_value = []
    result = CliRunner().invoke(
        cli.app, ["search-extracted-text", "--process", "P", "--term", "chocorramo"]
    )
    assert result.exit_code == 0
    assert "0 coincidencias" in result.output
    service.search.assert_called_once_with("P", "chocorramo", 50)
    engine.dispose.assert_called_once()


def test_cli_displays_docx_counts(monkeypatch) -> None:
    _, service = setup_cli(monkeypatch)
    service.extract_document.return_value = ExtractionResult(
        Source().documents[0],
        ExtractorIdentity("docx-text", "v1"),
        ExtractionStatus.COMPLETED,
        None,
        fragment_count=10,
        format_counts={"paragraphs": 5, "tables": 2},
    )
    response = CliRunner().invoke(cli.app, ["extract-document", "--document", "123"])
    assert response.exit_code == 0
    assert "Párrafos: 5" in response.output
    assert "Tablas: 2" in response.output


def test_force_ocr_diagnostic_is_explicit_and_does_not_hide_incomplete_coverage(monkeypatch):
    _, service = setup_cli(monkeypatch)
    service.extract_document.return_value = ExtractionResult(
        Source().documents[0],
        ExtractorIdentity("pdf-hybrid-local", "v1"),
        ExtractionStatus.PARTIAL_TEXT,
        None,
        diagnostics={
            "status": "ocr_truncated",
            "coverage_complete": False,
            "required_pages": [1, 2],
            "processed_pages": [1],
            "omitted_pages": [2],
        },
    )
    result = CliRunner().invoke(
        cli.app, ["extract-document", "--document", "D", "--force-ocr", "--dry-run"]
    )
    assert result.exit_code == 1
    assert "ocr_truncated" in result.output
    assert "INCOMPLETA" in result.output
    service.extract_document.assert_called_once_with("D", True, force_ocr=True)
