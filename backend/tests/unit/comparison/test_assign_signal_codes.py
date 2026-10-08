import uuid

from public_procurement.comparison.domain.config import DEFAULT_CONFIG
from public_procurement.comparison.domain.evaluation import ItemEvaluation, evaluate_item
from public_procurement.comparison.services import assign_signal_codes

from ...builders import MOCKUP_COMPARABLE_PRICES, ItemFactsBuilder, comparables_at

COMPARABLES = comparables_at(MOCKUP_COMPARABLE_PRICES)


def _signal(purchase_id: uuid.UUID, line_number: int) -> ItemEvaluation:
    target = ItemFactsBuilder().with_purchase_id(purchase_id).with_line_number(line_number).build()
    return evaluate_item(target, COMPARABLES, [], DEFAULT_CONFIG)


def test_assign_signal_codes_omits_line_suffix_when_purchase_has_one_signal() -> None:
    # Arrange
    purchase_id = uuid.uuid4()
    evaluations = [_signal(purchase_id, 1)]
    # Act
    codes = assign_signal_codes(evaluations)
    # Assert
    assert codes == {(purchase_id, 1): "SG-2026-0142"}


def test_assign_signal_codes_adds_line_suffix_when_purchase_has_several_signals() -> None:
    # Arrange
    purchase_id = uuid.uuid4()
    evaluations = [_signal(purchase_id, 1), _signal(purchase_id, 3)]
    # Act
    codes = assign_signal_codes(evaluations)
    # Assert
    assert codes == {(purchase_id, 1): "SG-2026-0142-1", (purchase_id, 3): "SG-2026-0142-3"}
