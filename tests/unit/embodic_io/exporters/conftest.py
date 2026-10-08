"""Computed outcomes of the packaged examples, shared by the exporter tests (one compute per example per session)."""

import functools
from collections.abc import Callable

import pytest

from embodic.api import ComputeOutcome, compute_project
from embodic.io.examples import examples_dir

EXAMPLE_IDS = tuple(sorted(path.name.split(".")[0] for path in examples_dir().glob("*.embodic.json")))
WAVE = "wave_16p_example"  # fails DRC (186 violations on main 8a297a0): the refusal case


@functools.cache
def _outcome(example_id: str) -> ComputeOutcome:
    outcome = compute_project(examples_dir() / f"{example_id}.embodic.json")
    assert isinstance(outcome, ComputeOutcome), outcome
    return outcome


@pytest.fixture
def outcome_of() -> Callable[[str], ComputeOutcome]:
    """Return the computed outcome of a packaged example by id."""
    return _outcome


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrise every test that takes ``example_id`` over all packaged examples."""
    if "example_id" in metafunc.fixturenames:
        metafunc.parametrize("example_id", EXAMPLE_IDS)
