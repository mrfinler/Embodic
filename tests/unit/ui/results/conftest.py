"""Computed outcomes of the packaged examples, shared by the results view-model tests (each compute is under 1 s)."""

import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.io.project import project_from_example, project_provenance
from embodic.results import load_registry


def computed(example_id: str):
    """Return the ComputeOutcome of a packaged example."""
    project = project_from_example(load_example(example_id))
    return compute(project.design, project_provenance(project))


@pytest.fixture(scope="session")
def registry():
    """Return the packaged registry."""
    return load_registry()


@pytest.fixture(scope="session")
def d08():
    """Return the computed D08 spiral example (DRC passes, no DC link)."""
    return computed("spiral_12c10p_d08")


@pytest.fixture(scope="session")
def spiral_14p():
    """Return the computed 12-coil 14-pole spiral example."""
    return computed("spiral_12c14p")


@pytest.fixture(scope="session")
def wave():
    """Return the computed wave example (186 DRC failures, D-034)."""
    return computed("wave_16p_example")


@pytest.fixture(scope="session")
def serpentine():
    """Return the computed serpentine example (it has a DC link, so a torque-speed estimate)."""
    return computed("serpentine_16p_example")
