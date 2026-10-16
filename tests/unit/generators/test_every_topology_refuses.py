"""Refusals every generator shares: a screw hole off the board (REQ-F-24).

Both packaged examples (serpentine, wave) carry one M3 pattern on a board of radius well under 1000 mm, so a
1000 mm pitch circle puts every hole off the board while staying inside the supported range (OUTLINE_MAX_MM).
"""

import dataclasses

import pytest

from embodic.errors import Unbuildable
from embodic.generators import build_layout
from embodic.io.examples import load_example
from embodic.model.design import DesignParameters
from embodic.model.validate import validate_design
from embodic.results import load_registry

REGISTRY = load_registry()
SCREWED_EXAMPLES = ("serpentine_16p_example", "wave_16p_example")


def _with_pitch_radius(example_id: str, pitch_radius_mm: float) -> DesignParameters:
    design = load_example(example_id)[1]
    pattern = dataclasses.replace(design.outline.screws[0], pitch_radius_mm=pitch_radius_mm)
    return dataclasses.replace(design, outline=dataclasses.replace(design.outline, screws=(pattern,)))


@pytest.mark.req("REQ-F-24")
@pytest.mark.parametrize("example_id", SCREWED_EXAMPLES)
def test_a_screw_hole_off_the_board_is_refused_by_every_topology(example_id: str) -> None:
    """Catches DEF-M7a-01's second cause: serpentine and wave built holes off the board that spiral refuses."""
    design = _with_pitch_radius(example_id, 1000.0)
    assert [i.code for i in validate_design(design) if "/outline/screws/0/pitch_radius_mm" in i.pointers] == []
    refused = build_layout(design, REGISTRY)
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        ("UNBUILDABLE_SCREW_HOLE_EDGE", ("/outline/screws/0/pitch_radius_mm", "/outline/screws/0/hole_diameter_mm"))
    ]
