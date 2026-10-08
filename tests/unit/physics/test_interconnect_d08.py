"""The D08 example with its interconnect classified by hand reproduces U-E4's interconnect copper sum (EQ-10, EQ-23).

U-E4 (docs/phase2/engineering/checks/d08_resistance_decomposition.py) sums every interconnect path of the generated D08
board at 20 degC: 0.136802 ohm, outside R_phase. The generator records no roles yet (U-M2d-5), so this test writes them
for the seven D08 paths it checks below: three tap stubs, the neutral ring through taps 60, 61, 62 and three leads.
"""

import dataclasses
import math

import pytest
from tests.unit.physics.test_oracles import _d08_design

from embodic.generators import build_layout
from embodic.geometry.circuit import LineLead, NeutralRing, PhaseLink
from embodic.model.vocabulary import Phase
from embodic.physics import analyse, path_resistance_ohm
from embodic.physics.interconnect import interconnect_resistance
from embodic.results import Status, load_registry

pytestmark = pytest.mark.req("REQ-F-11")
U_E4_INTERCONNECT_20C_OHM = 0.136802  # U-E4 report, "neutral ring 0.136802 not in R_phase" (6 digits)
ROLES = (
    PhaseLink(path_id=57, phase=Phase.B),
    PhaseLink(path_id=58, phase=Phase.A),
    PhaseLink(path_id=59, phase=Phase.C),
    NeutralRing(path_id=60, tap_via_ids=(60, 61, 62)),
    LineLead(path_id=61, phase=Phase.A),
    LineLead(path_id=62, phase=Phase.B),
    LineLead(path_id=63, phase=Phase.C),
)
EXPECTED_NETS = {57: "N", 58: "N", 59: "N", 60: "N", 61: "U", 62: "V", 63: "W"}


@pytest.fixture(scope="module")
def d08():
    """Return the D08 design, the registry, the generated stack and the stack with ROLES recorded."""
    registry = load_registry()
    design = _d08_design()
    stack = build_layout(design, registry)
    board = stack.boards[0]
    assert {pid: board.paths[pid].net for pid in board.circuit.interconnect_path_ids} == EXPECTED_NETS
    classified = dataclasses.replace(board, circuit=dataclasses.replace(board.circuit, interconnect_roles=ROLES))
    return design, registry, stack, dataclasses.replace(stack, boards=(classified,))


def test_hand_classified_d08_interconnect_reproduces_the_u_e4_sum(d08) -> None:
    """Defect caught: a ring segment measured from the wrong tap, or a role whose copper drops out of the sums."""
    design, registry, _, classified = d08
    board = classified.boards[0]
    rho20 = registry.constant("copper_resistivity_20c_ohm_m").value
    thickness = {layer.name: layer.thickness_mm for layer in design.stackup.copper_layers()}
    path_r = dict(enumerate(path_resistance_ohm(board.arrays(), thickness, rho20).tolist()))
    sums = interconnect_resistance(board, (Phase.A, Phase.B, Phase.C), path_r, thickness, rho20)
    assert len(sums.neutral_ring_ohm) == 2
    assert round(sums.total_ohm(), 6) == U_E4_INTERCONNECT_20C_OHM


def test_classification_adds_interconnect_copper_to_r_ll_and_p_ic(d08) -> None:
    """Defect caught: roles recorded but ignored, or P_ic labelled unresolved although every path is classified."""
    design, registry, unclassified, classified = d08
    before = analyse(design, unclassified, {}, registry)
    after = analyse(design, classified, {}, registry)
    assert before is not None and after is not None
    assert before.loss_interconnect_w.status is Status.UNRESOLVED
    assert "INTERNAL_INTERCONNECT_UNCLASSIFIED" not in {f.code for f in after.loss_interconnect_w.validity}
    assert after.loss_interconnect_w.value > 0.0
    assert after.resistance_line_ohm.value > before.resistance_line_ohm.value
    expected_total = (
        after.loss_copper_w.value
        + after.loss_eddy_w.value
        + after.loss_circulating_w.value
        + after.loss_delta_circulating_w.value
        + after.loss_interconnect_w.value
    )
    assert math.isclose(after.loss_total_w.value, expected_total, rel_tol=1e-15)
