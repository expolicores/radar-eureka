import pytest

from public_procurement.comparison.domain.facts import PurchaseSource
from public_procurement.comparison.domain.signal_code import signal_code


@pytest.mark.parametrize(
    ("source", "record_id", "year", "line", "expected"),
    [
        (PurchaseSource.SECOP_II, "CO1.PCCNTR.0000142", 2026, None, "SG-2026-0142"),
        (PurchaseSource.SECOP_II, "CO1.PCCNTR.0895870", 2026, None, "SG-2026-895870"),
        (PurchaseSource.TVEC, "163772", 2025, None, "SG-2025-T163772"),
        (PurchaseSource.SECOP_II, "CO1.PCCNTR.0000142", 2026, 2, "SG-2026-0142-2"),
    ],
)
def test_signal_code_is_readable_and_stable_when_built_from_the_purchase(
    source: PurchaseSource, record_id: str, year: int, line: int | None, expected: str
) -> None:
    # Arrange / Act
    code = signal_code(source, record_id, year, line)
    # Assert
    assert code == expected
