"""DEF-M3a-01: a board of a stack is analysed at the z its Layout carries (interfaces.md section 5, D-016)."""

import dataclasses
import math

import pytest
from tests.unit.generators.serpentine.make_example import example_design
from tests.unit.generators.serpentine.support import per_phase

from embodic.errors import Unbuildable
from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack
from embodic.model.provenance import derive_provenance
from embodic.model.rotor import RotorType
from embodic.physics import analyse
from embodic.results import Registry, load_registry

pytestmark = pytest.mark.req("REQ-F-11")


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _ke_by_phase(design, stack: BoardStack, registry: Registry) -> dict[str, float]:  # type: ignore[no-untyped-def]
    result = analyse(design, stack, derive_provenance(design, None, ()), registry)
    assert result is not None
    return {p.phase.value: p.ke_peak_v_s_per_rad.value for p in result.phases}


@pytest.mark.parametrize("rotor_type", [RotorType.SINGLE_OPEN, RotorType.DOUBLE])
def test_ke_of_a_phase_does_not_depend_on_the_place_of_its_board_in_the_stack(
    rotor_type: RotorType, registry: Registry
) -> None:
    """Catches DEF-M3a-01: analyse() added k x pitch to a z that already holds it, so Ke was 11 % off.

    Every board carries its z in the stack frame (interfaces.md section 5), so listing the same boards in the reverse
    order must give the same Ke per phase. With the double count, board 0 moves from a shift of 0 to 2 pitches.
    """
    design = per_phase(example_design())
    design = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, rotor_type=rotor_type))
    stack = build_layout(design, registry)
    assert not isinstance(stack, Unbuildable)
    assert len(stack.boards) == 3
    assert stack.boards[1].copper_z_mm != stack.boards[0].copper_z_mm  # the frame is the stack's, not the board's
    reversed_stack = BoardStack(
        boards=tuple(reversed(stack.boards)),
        board_thickness_mm=stack.board_thickness_mm,
        board_gap_mm=stack.board_gap_mm,
    )
    forward = _ke_by_phase(design, stack, registry)
    backward = _ke_by_phase(design, reversed_stack, registry)
    assert forward.keys() == backward.keys()
    for phase, ke in forward.items():
        assert math.isclose(backward[phase], ke, rel_tol=1e-12), (phase, ke, backward[phase])
