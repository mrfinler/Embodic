"""EQ-17 on a stack of boards: heat leaves through the two outer faces, 2 A_1, with the loss of all boards.

Specification: docs/phase3/engineering/fix_wave_f1.md section C (T-C1, T-C2; DEF-UE17-02). The ruling is inferred
(a 0.1 mm air gap ties the inner faces to their neighbours), and Xcoil does the same (engine.js l.1390). EQ-16 stays
additive: the laminate of n boards weighs n times one board, which test_gr_f11_mass_thermal_current.py pins on
Xcoil's numbers.
"""

import pytest
from tests.unit.generators.serpentine.make_example import example_design
from tests.unit.generators.serpentine.support import per_phase

from embodic.errors import Unbuildable
from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.provenance import derive_provenance
from embodic.physics import analyse
from embodic.physics.analyse import board_area_mm2
from embodic.results import AnalysisResult, load_registry

pytestmark = [pytest.mark.req("REQ-F-11"), pytest.mark.eqt("EQT-17-GR")]


def _analyse(design: DesignParameters) -> tuple[BoardStack, AnalysisResult]:
    registry = load_registry()
    stack = build_layout(design, registry)
    assert not isinstance(stack, Unbuildable)
    result = analyse(design, stack, derive_provenance(design, None, ()), registry)
    assert result is not None
    return stack, result


def _expected_rise_k(design: DesignParameters, stack: BoardStack, result: AnalysisResult) -> float:
    """Return P / (h 2 A_1) with P the loss of all boards and A_1 the face area of one board in m^2."""
    return result.loss_total_w.value / (
        design.operating.convection_h_w_m2k * 2 * board_area_mm2(stack.boards[0]) * 1e-6
    )


def test_three_board_stack_cools_through_two_outer_faces_of_one_board() -> None:
    """Catches DEF-UE17-02: the cooling area was n times 2 A_1, so three boards cooled the winding three times too well.

    The serpentine example as one board per phase gave 3.4320 K for 5.4631 W, so h 2 A_1 dT / P was 1/3 instead of 1
    (section C.2). The preconditions make the n-board area the only difference between the two sides.
    """
    design = per_phase(example_design())
    stack, result = _analyse(design)
    assert len(stack.boards) == 3
    assert stack.board_gap_mm == 0.1
    assert all(board_area_mm2(b) == pytest.approx(board_area_mm2(stack.boards[0]), rel=1e-12) for b in stack.boards)
    assert result.temperature_rise_k.value == pytest.approx(_expected_rise_k(design, stack, result), rel=1e-12)


def test_single_board_cools_through_its_two_faces() -> None:
    """Catches a fix that divides the area by the board count or special-cases one board (the ratio stays 1)."""
    design = example_design()
    stack, result = _analyse(design)
    assert len(stack.boards) == 1
    assert result.temperature_rise_k.value == pytest.approx(_expected_rise_k(design, stack, result), rel=1e-12)
