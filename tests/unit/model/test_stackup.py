"""UT-GEO-12 (Phase 1 meaning): copper z and board thickness derive exactly from the explicit stack-up (REQ-F-04)."""

import pytest

from embodic.model.stackup import CopperLayer, DielectricLayer, Stackup

# Example values: ten 0.1 mm dielectrics, where a left-to-right float sum drifts to 1.0749999999999997 and 1.0999...
STACKUP = Stackup(
    layers=(
        CopperLayer(name="L1", thickness_mm=0.05),
        *(DielectricLayer(name=f"D{n}", thickness_mm=0.1, material="FR-4") for n in range(1, 11)),
        CopperLayer(name="L2", thickness_mm=0.05),
    )
)


@pytest.mark.req("REQ-F-04")
def test_copper_z_is_the_exact_sum_of_the_layers_above_plus_half_its_own():
    """UT-GEO-12. Defect caught: z accumulated with plain float addition, off by ulps from the decimal stack-up."""
    assert STACKUP.copper_z_mm() == {"L1": 0.025, "L2": 1.075}


@pytest.mark.req("REQ-F-04")
def test_board_thickness_is_the_exact_sum_of_all_layers():
    """UT-GEO-12. Defect caught: a board thickness that drops a layer or drifts by ulps from 1.1 mm."""
    assert STACKUP.board_thickness_mm() == 1.1
