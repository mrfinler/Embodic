"""Session fixtures: the packaged registry and its contract-shaped variant."""

import pytest
from tests.unit.results.registries import contract_shaped

from embodic.results.registry import Registry, load_registry


@pytest.fixture(scope="session")
def packaged() -> Registry:
    """Return the registry exactly as shipped."""
    return load_registry()


@pytest.fixture(scope="session")
def contract_registry() -> Registry:
    """Return the shipped registry with EC-05 in the requirements.md section 6 shape."""
    return contract_shaped()
