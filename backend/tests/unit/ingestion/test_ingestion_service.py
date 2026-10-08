from datetime import UTC, datetime

from public_procurement.ingestion.domain.purchase import Source
from public_procurement.ingestion.services import IngestionService

from ...builders import SourceItemBuilder, SourcePurchaseBuilder
from ...doubles import InMemoryPurchaseRepository, InMemoryUnitOfWork, ListPublicDataSource

CUTOFF = datetime(2026, 10, 6, 8, 10, tzinfo=UTC)


def _service(repository: InMemoryPurchaseRepository) -> IngestionService:
    return IngestionService(lambda: InMemoryUnitOfWork(repository))


def _source(*identifiers: str) -> ListPublicDataSource:
    records = [
        SourcePurchaseBuilder().with_identifier(identifier).build() for identifier in identifiers
    ]
    return ListPublicDataSource(Source.SECOP_II, records, CUTOFF)


def test_run_registers_new_purchases_and_run_log_when_database_is_empty() -> None:
    # Arrange
    repository = InMemoryPurchaseRepository()
    # Act
    result = _service(repository).run(_source("CO1.PCCNTR.0000001", "CO1.PCCNTR.0000002"))
    # Assert
    assert (result.read_count, result.new_count, result.updated_count) == (2, 2, 0)
    assert result.cutoff_at == CUTOFF
    assert repository.runs == [result]


def test_run_does_not_duplicate_purchases_when_executed_twice() -> None:
    # Arrange
    repository = InMemoryPurchaseRepository()
    service = _service(repository)
    service.run(_source("CO1.PCCNTR.0000001"))
    # Act
    second = service.run(_source("CO1.PCCNTR.0000001"))
    # Assert
    assert (second.new_count, second.updated_count) == (0, 0)
    assert len(repository.purchases) == 1
    assert len(repository.runs) == 2


def test_run_counts_updated_purchase_when_source_changes_a_field() -> None:
    # Arrange
    repository = InMemoryPurchaseRepository()
    service = _service(repository)
    service.run(_source("CO1.PCCNTR.0000001"))
    corrected_item = (
        SourceItemBuilder().with_description("Televisor Smart TV 65 4K (corregido)").build()
    )
    changed = (
        SourcePurchaseBuilder()
        .with_identifier("CO1.PCCNTR.0000001")
        .with_items(corrected_item)
        .build()
    )
    # Act
    result = service.run(ListPublicDataSource(Source.SECOP_II, [changed], CUTOFF))
    # Assert
    assert (result.new_count, result.updated_count) == (0, 1)
