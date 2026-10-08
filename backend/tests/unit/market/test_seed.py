from public_procurement.market.adapters.seed import generate_seed_observations
from public_procurement.market.domain.observation import AcquisitionMethod, MarketVatBasis


def test_seed_observations_are_marked_as_simulated_when_generated() -> None:
    # Arrange / Act
    observations = generate_seed_observations()
    # Assert
    assert observations
    assert {o.method for o in observations} == {AcquisitionMethod.SIMULATED}


def test_seed_observations_have_unique_references_per_store_when_generated() -> None:
    # Arrange
    observations = generate_seed_observations()
    # Act
    keys = {(o.store, o.source_reference) for o in observations}
    # Assert
    assert len(keys) == len(observations)


def test_seed_includes_observations_that_benchmark_two_must_discard_when_generated() -> None:
    # Arrange
    observations = generate_seed_observations()
    # Act
    third_party = [o for o in observations if not o.seller_is_store]
    special = [o for o in observations if o.has_special_conditions]
    # Assert
    assert third_party
    assert special
    assert all(o.vat_basis is MarketVatBasis.INCLUDED for o in observations)
