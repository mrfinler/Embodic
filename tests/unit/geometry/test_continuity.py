"""UT-GEO-01: a primitive list is continuous when every joint closes within 1e-6 mm; transforms keep it so."""

import math

import pytest
from hypothesis import given

from embodic.geometry.paths import COINCIDENCE_MM, is_continuous, joint_gaps_mm
from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.geometry.transforms import mirror, reverse_path, rotate

from .strategies import angle_rad, chains

pytestmark = pytest.mark.req("REQ-N-21")

SIDE = Line(x1_mm=10.0, y1_mm=0.0, x2_mm=20.0, y2_mm=0.0, width_mm=0.2, role=PrimitiveRole.SIDE)
TURN = Arc(
    cx_mm=20.0,
    cy_mm=1.0,
    r_mm=1.0,
    start_rad=-math.pi / 2,
    sweep_rad=math.pi,
    width_mm=0.2,
    role=PrimitiveRole.END_TURN,
)
BACK = Line(x1_mm=20.0, y1_mm=2.0, x2_mm=10.0, y2_mm=2.0, width_mm=0.2, role=PrimitiveRole.SIDE)


def test_ut_geo_01_hairpin_is_continuous() -> None:
    """Catches an arc end point taken from the wrong angle: the hairpin's joints would open by 2 mm."""
    gaps = joint_gaps_mm((SIDE, TURN, BACK))
    assert len(gaps) == 2
    assert max(gaps) < 1e-12


def test_ut_geo_01_gap_just_above_tolerance_is_detected() -> None:
    """Catches a tolerance that is looser than 1e-6 mm or a check that skips the last joint."""
    shifted = Line(x1_mm=20.0, y1_mm=2.0 + 1.5 * COINCIDENCE_MM, x2_mm=10.0, y2_mm=2.0, width_mm=0.2, role=BACK.role)
    assert not is_continuous((SIDE, TURN, shifted))
    assert is_continuous((SIDE, TURN, BACK))


@given(chains(), angle_rad, angle_rad)
def test_ut_geo_01_rotation_mirror_and_reversal_keep_any_chain_continuous(chain, turn_rad, axis_rad) -> None:
    """Catches a transform that moves an arc's centre and angles inconsistently, or a reversal that keeps order."""
    assert is_continuous(chain)
    for moved in (rotate(chain, turn_rad), mirror(chain, axis_rad), reverse_path(chain)):
        assert is_continuous(moved), joint_gaps_mm(moved)


@given(chains(max_size=1))
def test_ut_geo_01_a_single_primitive_has_no_joint(chain) -> None:
    """Catches a joint counter that compares a primitive with itself."""
    assert joint_gaps_mm(chain) == ()
