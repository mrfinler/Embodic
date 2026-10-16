"""F06-1 (V3-01 union ruling): reference-mode track length at the 1e-6 mm absolute tolerance REQ-F-06 (b) states."""

import pytest
from tests.unit.generators.test_spiral_length import CASES, GOLDEN

from embodic.generators import generate_spiral
from embodic.geometry.details import SpiralDetail
from embodic.geometry.layout import BoardStack
from embodic.results import load_registry


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize("case", list(CASES))
def test_f06_1_sharp_track_length_equals_the_reference_total_within_1e_6_mm(case: str) -> None:
    """Catches a length error between 1e-6 mm and 4e-4 mm, such as a lead arc built from a rounded angle.

    The reference is Agent 2's construction (fixtures/spiral_r2_turns.json). The sibling test uses rel 1e-6, which is
    about 4e-4 mm at 415 mm.
    """
    stack = generate_spiral(CASES[case](), load_registry())
    assert isinstance(stack, BoardStack)
    detail = stack.boards[0].detail
    assert isinstance(detail, SpiralDetail)
    for layer in ("X", "Y"):
        assert detail.track_length_per_coil_layer_mm[layer] == pytest.approx(GOLDEN[case]["total"], rel=0.0, abs=1e-6)
