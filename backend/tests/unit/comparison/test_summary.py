import pytest

from public_procurement.comparison.domain.evaluation import Outcome
from public_procurement.comparison.domain.summary import purchase_outcome


@pytest.mark.parametrize(
    ("outcomes", "expected"),
    [
        ([Outcome.NO_SIGNAL, Outcome.SIGNAL], Outcome.SIGNAL),
        ([Outcome.NO_SIGNAL, Outcome.LOW_PRICE_REVIEW], Outcome.LOW_PRICE_REVIEW),
        ([Outcome.INSUFFICIENT_COMPARABLES, Outcome.NO_SIGNAL], Outcome.NO_SIGNAL),
        (
            [Outcome.NO_UNIT_PRICE, Outcome.INSUFFICIENT_COMPARABLES],
            Outcome.INSUFFICIENT_COMPARABLES,
        ),
        ([Outcome.NO_UNIT_PRICE, Outcome.VAT_INCOMPLETE], Outcome.VAT_INCOMPLETE),
        ([], None),
    ],
)
def test_purchase_outcome_keeps_the_most_relevant_result_when_items_differ(
    outcomes: list[Outcome], expected: Outcome | None
) -> None:
    # Arrange / Act
    outcome = purchase_outcome(outcomes)
    # Assert
    assert outcome is expected
