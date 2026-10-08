"""UT-GEO-07, criteria updated to the U-E3 construction (spiral_generator_spec.md G4 to G6, acceptance checks).

The Phase 1 criteria compared against a true-spiral reference that predates U-E3 (D-028 turns, lead arc, half
closing). The criteria now are:

(i) Sharp corners: the generated track length of each coil layer equals Agent 2's reference construction
    (checks/spiral_reference.py `coil_path` total = turns + lead + stub, via fixtures/spiral_r2_turns.json) within
    1e-6 relative, for CF-11 (full closing, 10 turns) and CF-10/D08 (half closing, 3 turns) at via pads 0.6 and 1.2 mm.
(ii) Fillets on: the change from the sharp length equals the sum of the exact per-corner closed forms
    (test_spiral_fillet_length.py). The Phase 1 "within 1 % of the reference" is not applied: the G9 concentric radii
    remove 12.72 % on CF-11 at rho 0.5 mm (DEF-M2d3-02), so that bound waits for Agent 2's U-E5 ruling.
(iii) The EQ-03 loop formula as an upper bound is `not tested` here.
"""

import dataclasses
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.generators import generate_spiral
from embodic.geometry.details import SpiralDetail
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.vias import ViaSpec
from embodic.results import load_registry

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "spiral_r2_turns.json").read_text())


def _pad(make: Callable[[], DesignParameters], pad_mm: float) -> Callable[[], DesignParameters]:
    def design() -> DesignParameters:
        base = make()
        vias = ViaSpec(drill_mm=base.vias.drill_mm, pad_mm=pad_mm, plating_um=base.vias.plating_um)
        return dataclasses.replace(base, vias=vias)

    return design


CASES = {"CF-11": default_design, "CF-10": d08_design, "CF-10 pad 1.2": _pad(d08_design, 1.2)}


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize("case", list(CASES))
def test_ut_geo_07_sharp_track_length_equals_the_reference_construction(case: str) -> None:
    """(i): X and Y lengths equal the reference total within 1e-6 relative; catches a lost stub, lead or jog."""
    stack = generate_spiral(CASES[case](), load_registry())
    assert isinstance(stack, BoardStack)
    detail = stack.boards[0].detail
    assert isinstance(detail, SpiralDetail)
    assert detail.turns_achieved == GOLDEN[case]["n"]
    for layer in ("X", "Y"):
        assert detail.track_length_per_coil_layer_mm[layer] == pytest.approx(GOLDEN[case]["total"], rel=1e-6, abs=0.0)
