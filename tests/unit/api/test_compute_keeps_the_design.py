"""F23-1 (V3-01 union ruling): the engine never returns a modified DesignParameters (REQ-F-23)."""

import dataclasses

import pytest

from embodic.api import compute
from embodic.io.canonical import design_hash
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, project_provenance

D08 = "spiral_12c10p_d08"
TYPED_AIR_GAP_MM = 60.0  # above the supported 50 mm


@pytest.mark.req("REQ-F-23")
def test_f23_1_a_value_above_the_supported_range_is_reported_and_never_clamped_in_the_outcome() -> None:
    """Catches an engine that clamps the input to 50 mm and returns the clamped design instead of the typed one."""
    ref, example = load_example(D08)
    design = dataclasses.replace(example, rotor=dataclasses.replace(example.rotor, air_gap_mm=TYPED_AIR_GAP_MM))
    outcome = compute(design, project_provenance(ProjectFile(design=design, origin=ref)))
    assert outcome is not None
    assert outcome.design == design
    assert outcome.design_hash == design_hash(design)
    assert outcome.design.rotor.air_gap_mm == TYPED_AIR_GAP_MM
    above = [i for i in outcome.issues if i.code == "RANGE_ABOVE_SUPPORTED"]
    assert [(i.pointers, i.suggestion.proposed_value) for i in above] == [(("/rotor/air_gap_mm",), 50)]
