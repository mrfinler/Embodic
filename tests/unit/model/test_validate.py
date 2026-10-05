"""Cross-field rules added in the U-M2a fix round: R12 coil gap hint."""

import dataclasses

import pytest

from embodic.errors import IssueCategory, Severity
from embodic.model.design import DesignParameters
from embodic.model.validate import validate_design
from embodic.model.winding_specs import SpiralWindingSpec

from .designs import spiral_design


def _with_coil_gap(gap_mm: float) -> DesignParameters:
    design = spiral_design()
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, coil_gap_mm=gap_mm)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


@pytest.mark.req("REQ-F-14")
def test_coil_gap_below_trace_spacing_is_an_info_hint_proposing_the_spacing():
    """R12. Defect caught: a gap below s rejected as an error, or reported without the spacing as Suggestion."""
    found = [i for i in validate_design(_with_coil_gap(0.1)) if i.code == "RANGE_COIL_GAP_BELOW_CLEARANCE"]
    assert len(found) == 1
    hint = found[0]
    assert hint.severity is Severity.INFO
    assert hint.category is IssueCategory.UNSUPPORTED_RANGE
    assert hint.pointers == ("/winding/coil/coil_gap_mm", "/winding/coil/clearance_mm")
    assert hint.suggestion is not None
    assert (hint.suggestion.pointer, hint.suggestion.proposed_value) == ("/winding/coil/coil_gap_mm", 0.2)
    assert "0.2 mm" in hint.message


@pytest.mark.req("REQ-F-14")
@pytest.mark.parametrize("gap_mm", [0.2, 0.5])
def test_coil_gap_at_or_above_trace_spacing_gives_no_hint(gap_mm):
    """R12. Defect caught: the hint shown when the generator uses the gap as entered."""
    codes = [i.code for i in validate_design(_with_coil_gap(gap_mm))]
    assert "RANGE_COIL_GAP_BELOW_CLEARANCE" not in codes
