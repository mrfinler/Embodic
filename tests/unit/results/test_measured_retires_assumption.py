"""REQ-T-06: a B_r marked measured with a named source leaves the assumed inputs of the EMF Traceable."""

import pytest

from embodic.api import compute
from embodic.errors import ValidationIssue
from embodic.io.examples import load_example
from embodic.model.provenance import Measurement, derive_provenance, mark_measured

BR = "/rotor/remanence_t"
SOURCE = "magnet datasheet rev C, grade N42"
EMF_QUANTITIES = ("emf_phase_rms_v", "ke_phase_v_s_per_rad", "torque_n_m")


def assumed_items(example_id: str, measurements: list[Measurement]) -> dict[str, tuple[str, ...]]:
    """Return the assumed-input items of the EMF Traceables of an example computed with the given measurements."""
    ref, design = load_example(example_id)
    outcome = compute(design, derive_provenance(design, (ref, design), measurements))
    assert outcome is not None and outcome.analysis is not None
    return {q: tuple(a.item for a in getattr(outcome.analysis, q).assumed_inputs) for q in EMF_QUANTITIES}


@pytest.mark.req("REQ-T-06")
@pytest.mark.parametrize("example_id", ["spiral_12c10p_d08", "serpentine_16p_example"])
def test_t06_marking_br_measured_with_a_source_removes_it_from_the_assumed_inputs(example_id):
    """Catches a magnet property that the retirement rule skips: B_r leaves the tag and the count drops by one."""
    _, design = load_example(example_id)
    marked = mark_measured(design, [], BR, SOURCE)
    assert isinstance(marked, tuple)
    before = assumed_items(example_id, [])
    after = assumed_items(example_id, list(marked))
    for quantity in EMF_QUANTITIES:
        assert BR in before[quantity], quantity
        assert BR not in after[quantity], quantity
        assert len(after[quantity]) == len(before[quantity]) - 1, quantity
        assert [i for i in before[quantity] if i != BR] == list(after[quantity]), quantity


@pytest.mark.req("REQ-T-06")
def test_t06_marking_br_measured_without_a_source_is_refused_and_the_assumption_stays():
    """Catches a mark accepted without a named source, which would retire the assumption on no evidence."""
    _, design = load_example("spiral_12c10p_d08")
    refused = mark_measured(design, [], BR, "  ")
    assert isinstance(refused, ValidationIssue)
    assert refused.code == "INVALID_MEASURED_SOURCE_EMPTY"
    assert BR in assumed_items("spiral_12c10p_d08", [])["emf_phase_rms_v"]
