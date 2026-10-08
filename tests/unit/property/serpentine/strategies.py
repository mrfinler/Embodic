"""Serpentine designs for the property tests: Xcoil's default preset with the options a user can flip."""

import dataclasses

from hypothesis import strategies as st
from tests.unit.generators.serpentine.make_example import example_design
from tests.unit.generators.serpentine.support import per_phase, with_winding

from embodic.model.design import DesignParameters
from embodic.model.winding_specs import CornerStyle, SideStyle, TerminalSide


@st.composite
def serpentine_designs(draw: st.DrawFn, corners: tuple[CornerStyle, ...] = tuple(CornerStyle)) -> DesignParameters:
    """Draw a serpentine design: side style, corner style, terminal side, turns, strands and the stack mode."""
    design = with_winding(
        example_design(),
        side_style=draw(st.sampled_from(SideStyle)),
        corner_style=draw(st.sampled_from(corners)),
        terminal_side=draw(st.sampled_from(TerminalSide)),
        turns=draw(st.integers(min_value=1, max_value=5)),
        strands=draw(st.integers(min_value=1, max_value=2)),
    )
    if draw(st.booleans()):
        design = per_phase(design, gap_mm=draw(st.sampled_from([0.1, 0.5])))
    return dataclasses.replace(design, name="Property design")
