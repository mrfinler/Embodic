"""UT-PHY-11, half (1) (U-D26 1b, D-084): the analysis gives every via of an example one barrel (REQ-F-05).

`analyse` passes `board_thickness_mm` as the barrel length of every via, and path resistance does not read it. One
extra millimetre of board therefore raises the 20 degC phase resistance by the sum, over the vias of that phase, of
the one-barrel resistance of a 1 mm barrel (EQ-11), if the phase is one series chain. The three packaged examples have
no parallel coil group, and the test asserts that premise, so no Xcoil board is needed for the oracle.
"""

import dataclasses
import math

import pytest

from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack, Via
from embodic.io.examples import load_example
from embodic.model.provenance import derive_provenance
from embodic.model.vocabulary import Phase
from embodic.physics import analyse
from embodic.physics.resistance import via_resistance_ohm
from embodic.results import load_registry

EXAMPLES = ("spiral_12c16p_default", "serpentine_16p_example", "wave_16p_example")
EXTRA_THICKNESS_MM = 1.0
REL_TOL = 1e-9


def _phase_vias(stack: BoardStack) -> dict[Phase, list[Via]]:
    """Return the vias in the members of each phase, across the boards of the stack."""
    by_phase: dict[Phase, list[Via]] = {}
    for board in stack.boards:
        vias = {v.id: v for v in board.vias}
        for circuit in board.circuit.phases:
            for group in circuit.groups:
                assert len(group.members) == 1, "the oracle needs every phase to be one series chain"
                by_phase.setdefault(circuit.phase, []).extend(vias[i] for m in group.members for i in m.via_ids)
    return by_phase


@pytest.mark.req("REQ-F-05")
@pytest.mark.parametrize("example_id", EXAMPLES)
def test_ut_phy_11_every_phase_via_of_an_example_is_analysed_as_one_barrel(example_id: str) -> None:
    """Catches a via term built with the wrong barrel count or a phase that drops a via (U-D26 1b).

    Two barrels halve the term and none makes it infinite. One extra mm of board thickness raises R_ph,20 by the mean
    over the phases of their one-barrel via terms, within 1e-9 relative. Measured on 5c99afe: 8.7e-15 (spiral),
    3.3e-13 (serpentine), 7.2e-15 (wave). The expected value comes from the EQ-11 kernel at count 1.
    """
    registry = load_registry()
    design = load_example(example_id)[1]
    stack = build_layout(design, registry)
    assert isinstance(stack, BoardStack)
    provenance = derive_provenance(design, None, ())
    rho20 = registry.constant("copper_resistivity_20c_ohm_m").value

    expected_per_phase = [
        math.fsum(
            via_resistance_ohm(via.drill_mm, design.vias.plating_um, EXTRA_THICKNESS_MM, rho20, 1) for via in vias
        )
        for vias in _phase_vias(stack).values()
    ]
    assert expected_per_phase and all(term > 0 for term in expected_per_phase), "the example has a via in every phase"

    thicker = dataclasses.replace(stack, board_thickness_mm=stack.board_thickness_mm + EXTRA_THICKNESS_MM)
    before = analyse(design, stack, provenance, registry)
    after = analyse(design, thicker, provenance, registry)
    assert before is not None and after is not None

    raised_ohm = after.resistance_phase_20c_ohm.value - before.resistance_phase_20c_ohm.value
    assert raised_ohm == pytest.approx(math.fsum(expected_per_phase) / len(expected_per_phase), rel=REL_TOL, abs=0.0)
