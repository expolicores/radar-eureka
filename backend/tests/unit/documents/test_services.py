import uuid
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from public_procurement.documents.adapters.local_storage import LocalBinaryStorage
from public_procurement.documents.domain.document import AcquisitionError, SourceDocument
from public_procurement.documents.repositories import (
    AcquisitionAttemptRecord,
    DocumentProcessRecord,
    DocumentRecord,
    DocumentVersionRecord,
)
from public_procurement.documents.services import DocumentService
from public_procurement.ingestion.services import ProcessReference

PDF = b"%PDF-1.4\ncomplete\n%%EOF"


@pytest.fixture
def setup(tmp_path):
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("ATTACH DATABASE ':memory:' AS documents"))
        for model in (
            DocumentRecord,
            DocumentProcessRecord,
            DocumentVersionRecord,
            AcquisitionAttemptRecord,
        ):
            model.__table__.create(connection)
    sessions = sessionmaker(engine, expire_on_commit=False)
    process = ProcessReference(uuid.uuid4(), "CO1.REQ.1", "P")
    lookup = Mock()
    lookup.get_process.return_value = process
    inventory = Mock()
    inventory.fetch.return_value = [
        SourceDocument("1", "P", "name.pdf", None, "https://community.secop.gov.co/file")
    ]
    storage = LocalBinaryStorage(tmp_path)
    downloader = Mock()
    downloader.download.side_effect = lambda source, target: target.store(
        [PDF],
        original_name=source.original_name,
        content_type="application/pdf",
        expected_size=len(PDF),
        max_bytes=1000,
    )
    yield DocumentService(sessions, lookup, inventory, downloader, storage), sessions, process
    engine.dispose()


def count(sessions, model):
    with sessions() as session:
        return session.scalar(select(func.count()).select_from(model))


def test_bounded_selection_does_not_download_historical_inventory(setup) -> None:
    service, sessions, _ = setup
    service.sync("CO1.REQ.1")
    service.limit_to_synced = True
    service.inventory.fetch.return_value = [
        SourceDocument(
            str(i), "P", f"selected-{i}.pdf", None, "https://community.secop.gov.co/file"
        )
        for i in (2, 3)
    ]
    service.sync("CO1.REQ.1")
    assert count(sessions, DocumentRecord) == 3
    assert {d.source.id_documento for d in service.list_documents("CO1.REQ.1")} == {"2", "3"}
    result = service.download("CO1.REQ.1")
    assert result.available == 2
    assert service.downloader.download.call_count == 2


def test_empty_bounded_selection_preserves_history_without_downloads(setup) -> None:
    service, sessions, _ = setup
    service.sync("CO1.REQ.1")
    service.limit_to_synced = True
    service.inventory.fetch.return_value = []
    service.sync("CO1.REQ.1")
    assert count(sessions, DocumentRecord) == 1
    assert service.download("CO1.REQ.1").available == 0
    service.downloader.download.assert_not_called()


def test_dry_run_has_no_writes_or_downloads(setup) -> None:
    service, sessions, _ = setup
    assert len(service.sync("CO1.REQ.1", dry_run=True)) == 1
    assert count(sessions, DocumentRecord) == 0
    service.downloader.download.assert_not_called()


def test_repeated_sync_and_download_preserve_identity_and_version(setup) -> None:
    service, sessions, _ = setup
    service.sync("CO1.REQ.1")
    service.sync("CO1.REQ.1")
    assert count(sessions, DocumentRecord) == 1
    assert count(sessions, DocumentProcessRecord) == 1
    assert service.download("CO1.REQ.1").available == 1
    assert service.download("CO1.REQ.1").available == 1
    assert count(sessions, DocumentVersionRecord) == 1
    assert count(sessions, AcquisitionAttemptRecord) == 2


def test_only_missing_reuses_existing_versions_without_new_download_attempt(setup) -> None:
    service, sessions, _ = setup
    service.sync("CO1.REQ.1")
    service.download("CO1.REQ.1")
    result = service.download("CO1.REQ.1", only_missing=True)
    assert result.available == 0
    assert result.failed == 0
    assert service.downloader.download.call_count == 1
    assert count(sessions, AcquisitionAttemptRecord) == 1


def test_content_changes_create_version_and_failure_preserves_previous(setup) -> None:
    service, sessions, _ = setup
    service.sync("CO1.REQ.1")
    service.download("CO1.REQ.1")
    changed = PDF.replace(b"complete", b"changed")
    service.downloader.download.side_effect = lambda source, target: target.store(
        [changed],
        original_name=source.original_name,
        content_type="application/pdf",
        expected_size=None,
        max_bytes=1000,
    )
    service.download("CO1.REQ.1")
    assert count(sessions, DocumentVersionRecord) == 2
    service.downloader.download.side_effect = AcquisitionError("network_error", "Interrumpida")
    assert service.download("CO1.REQ.1").failed == 1
    assert count(sessions, DocumentVersionRecord) == 2
    with sessions() as session:
        record = session.scalar(select(DocumentRecord))
        assert record.status == "failed"
        assert record.last_error_code == "network_error"
        versions = session.scalars(select(DocumentVersionRecord)).all()
        assert all((service.storage.root / v.storage_path).is_file() for v in versions)
    service.downloader.download.side_effect = lambda source, target: target.store(
        [changed],
        original_name=source.original_name,
        content_type="application/pdf",
        expected_size=None,
        max_bytes=1000,
    )
    assert service.download("CO1.REQ.1").available == 1
    assert count(sessions, DocumentVersionRecord) == 2


def test_two_processes_share_portfolio_and_documents(setup) -> None:
    service, sessions, process = setup
    service.sync("first")
    service.processes.get_process.return_value = ProcessReference(
        uuid.uuid4(), "CO1.REQ.2", process.portfolio_id
    )
    service.sync("second")
    assert count(sessions, DocumentRecord) == 1
    assert count(sessions, DocumentProcessRecord) == 2


def test_process_without_portfolio_never_consults_socrata(setup) -> None:
    service, _, process = setup
    service.processes.get_process.return_value = ProcessReference(
        process.id, process.id_del_proceso, None
    )
    with pytest.raises(ValueError, match="no tiene portafolio"):
        service.sync("process")
    service.inventory.fetch.assert_not_called()


def test_metadata_change_during_download_records_error_without_new_version(setup) -> None:
    service, sessions, _ = setup
    service.sync("first")
    initial = service.downloader.download.side_effect

    def changed_inventory(source, target):
        with sessions.begin() as session:
            record = session.scalar(select(DocumentRecord))
            record.original_name = "updated.pdf"
        return initial(source, target)

    service.downloader.download.side_effect = changed_inventory
    assert service.download("first").failed == 1
    assert count(sessions, DocumentVersionRecord) == 0
    with sessions() as session:
        assert session.scalar(select(DocumentRecord.last_error_code)) == "inventory_changed"


def test_shared_queries_return_documents_and_versions_without_exposing_orm(setup) -> None:
    service, _, _ = setup
    service.sync("first")
    service.download("first")
    documents = service.list_documents("first")
    versions = service.versions(documents[0].id)
    assert len(versions) == 1
    assert versions[0].observed_size == len(PDF)


def test_changed_inventory_is_pending_but_keeps_available_versions(setup) -> None:
    service, sessions, _ = setup
    service.sync("first")
    service.download("first")
    service.inventory.fetch.return_value = [
        SourceDocument("1", "P", "updated.pdf", None, "https://community.secop.gov.co/file")
    ]
    service.sync("first")
    assert service.list_documents("first")[0].status.value == "pending"
    assert count(sessions, DocumentVersionRecord) == 1


def test_extraction_reads_last_successful_version_even_when_content_reverts(setup) -> None:
    service, sessions, _ = setup
    service.sync("first")
    document = service.get_document("1")
    assert service.get_document(str(document.id)) == document
    assert service.latest_version(document.id) is None
    service.download("first")
    first_version = service.latest_version(document.id)
    original_downloader = service.downloader.download.side_effect
    changed = PDF.replace(b"complete", b"changed")
    service.downloader.download.side_effect = lambda source, target: target.store(
        [changed],
        original_name=source.original_name,
        content_type="application/pdf",
        expected_size=None,
        max_bytes=1000,
    )
    service.download("first")
    assert service.latest_version(document.id).id != first_version.id
    service.downloader.download.side_effect = original_downloader
    service.download("first")
    assert service.latest_version(document.id).id == first_version.id
    assert count(sessions, DocumentVersionRecord) == 2
    with service.open_version(first_version.id, max_bytes=1000) as file:
        assert file.read() == PDF


def test_document_reads_without_portfolio_are_empty_but_acquisition_still_rejects(setup):
    service, _, process = setup
    service.processes.get_process.return_value = ProcessReference(
        process.id, process.id_del_proceso, None
    )
    assert service.process_id("P") == process.id
    assert service.list_documents("P") == []
    with pytest.raises(ValueError, match="portafolio"):
        service.sync("P")
    with pytest.raises(ValueError, match="portafolio"):
        service.download("P")
