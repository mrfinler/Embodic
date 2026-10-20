"""Refusals every generator shares: a screw hole off the board (REQ-F-24) and parallel vias (D-054d).

Both packaged examples (serpentine, wave) carry one M3 pattern on a board of radius well under 1000 mm, so a
1000 mm pitch circle puts every hole off the board while staying inside the supported range (OUTLINE_MAX_MM).
"""

import dataclasses
import math

import pytest

from embodic.api import compute
from embodic.errors import Severity, Unbuildable
from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack
from embodic.io.examples import load_example
from embodic.model.design import DesignParameters
from embodic.model.provenance import derive_provenance
from embodic.model.validate import validate_design
from embodic.results import load_registry

REGISTRY = load_registry()
OPTION_NOT_IMPLEMENTED = {
    "spiral_12c16p_default": "UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED",
    "serpentine_16p_example": "UNBUILDABLE_SERPENTINE_OPTION_NOT_IMPLEMENTED",
    "wave_16p_example": "UNBUILDABLE_WAVE_OPTION_NOT_IMPLEMENTED",
}
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


@pytest.mark.req("REQ-F-14", "REQ-F-05")
@pytest.mark.parametrize("example_id", sorted(OPTION_NOT_IMPLEMENTED))
@pytest.mark.parametrize("vias_per_transition", [2, 3])
def test_ut_gen_06_parallel_vias_per_transition_are_refused_by_every_topology(
    example_id: str, vias_per_transition: int
) -> None:
    """Catches DEF-M7a-02: serpentine and wave built one via and gave R_ph unchanged for 2, without a message."""
    design = load_example(example_id)[1]
    parallel = dataclasses.replace(
        design, vias=dataclasses.replace(design.vias, vias_per_transition=vias_per_transition)
    )
    refused = build_layout(parallel, REGISTRY)
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        (OPTION_NOT_IMPLEMENTED[example_id], ("/vias/vias_per_transition",))
    ]


@pytest.mark.req("REQ-F-14", "REQ-F-05")
@pytest.mark.parametrize("example_id", sorted(OPTION_NOT_IMPLEMENTED))
def test_ut_gen_06_one_via_per_transition_still_builds_every_example(example_id: str) -> None:
    """Catches a refusal that also stops the packaged value 1."""
    design = load_example(example_id)[1]
    assert design.vias.vias_per_transition == 1
    assert isinstance(build_layout(design, REGISTRY), BoardStack)


@pytest.mark.req("REQ-F-05")
@pytest.mark.parametrize("example_id", sorted(OPTION_NOT_IMPLEMENTED))
def test_f05_one_via_per_transition_is_analysed_on_every_topology(example_id: str) -> None:
    """Catches a topology that builds one via per transition but gives no phase resistance for it (REQ-F-05).

    The example computes with no ERROR issue and its analysis holds a finite, positive phase resistance at 20 degC.
    """
    ref, design = load_example(example_id)
    assert design.vias.vias_per_transition == 1
    outcome = compute(design, derive_provenance(design, (ref, design), ()), registry=REGISTRY)
    assert outcome is not None
    assert [i.code for i in outcome.issues if i.severity is Severity.ERROR] == []
    assert outcome.analysis is not None
    resistance_ohm = outcome.analysis.resistance_phase_20c_ohm.value
    assert math.isfinite(resistance_ohm) and resistance_ohm > 0
