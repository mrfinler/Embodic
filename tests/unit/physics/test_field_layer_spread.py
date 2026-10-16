"""UT-PHY-20 / F12-1 (V3-01 union ruling): the C1d per-layer B1 of a six-layer board, outer to middle (EQ-05).

Source: docs/phase1/engineering/checks/c1_field.js C1d, quoted in docs/phase1/engineering/existing_logic_review.md.
"""

import numpy as np
import pytest

from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.model.stackup import generate_even_stackup
from embodic.physics.field import field_harmonic, symmetry_plane_mm

BOARD_MM = 0.62
AIR_GAP_MM = 1.0
RADIUS_MM = 28.0
# C1d prints B1 of the three upper layers, outer to middle; the stack is symmetric about the board centre.
B1_UPPER_T = (0.6828, 0.6813, 0.6805)
SPREAD_PERCENT = 0.336


def _layer_b1_t() -> list[float]:
    """B1 at each of six 1 oz copper layers in a 0.62 mm board, double rotor, p = 8, r = 28 mm, alpha_p 0.55."""
    stackup = generate_even_stackup(6, 0.0348, BOARD_MM)
    rotor = RotorSpec(
        poles=16,
        rotor_type=RotorType.DOUBLE,
        magnet=ArcMagnet(pole_arc_ratio=0.55, r_inner_mm=18.0, r_outer_mm=38.0, thickness_mm=2.0),
        remanence_t=1.3,
        recoil_permeability=1.05,
        air_gap_mm=AIR_GAP_MM,
        back_iron_thickness_mm=0.0,
    )
    plane_mm = symmetry_plane_mm(rotor, BOARD_MM)
    radius, alpha = np.array(RADIUS_MM), np.array(0.55)
    return [
        float(field_harmonic(1, radius, np.array(z_mm + AIR_GAP_MM), rotor, plane_mm, alpha)[0])
        for z_mm in stackup.copper_z_mm().values()
    ]


@pytest.mark.req("REQ-F-12")
@pytest.mark.eq("EQ-05")
def test_ut_phy_20_b1_of_each_copper_layer_matches_c1d() -> None:
    """Catches every layer evaluated at one z: L1 to L3 give 0.6828, 0.6813, 0.6805 T, L4 to L6 mirror them."""
    b1 = _layer_b1_t()
    assert b1 == pytest.approx([*B1_UPPER_T, *reversed(B1_UPPER_T)], rel=1e-4, abs=0.0)


@pytest.mark.req("REQ-F-12")
@pytest.mark.eq("EQ-05")
def test_ut_phy_20_b1_spread_over_the_layers_is_0_336_percent() -> None:
    """Catches a spread of 0 (all layers at the board centre): max/min - 1 is 0.336 %, the printed C1d precision."""
    b1 = _layer_b1_t()
    spread = (max(b1) / min(b1) - 1.0) * 100.0
    assert spread == pytest.approx(SPREAD_PERCENT, abs=5e-4)
