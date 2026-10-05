"""The D08 12/10 spiral example (CF-10, O1-D08) as a DRC-checkable board.

The copper inputs are the OR-01 design of tests/unit/physics/test_oracles.py. Two things change, and neither enters
Ke: the DRC trace and via clearances become D08's s 0.8 mm (Table 4.5 p.54), so a pass shows the clearance table of
spiral_generator_spec.md worked example 2; and the outline, which O1-D08 does not give, becomes a circle of radius
60 mm with a 10 mm bore (`assumption`, example values), so the example board of tests/unit/model/designs.py (bore
12.5 mm) does not cut D08's copper from r 11.47 mm and the bus rings fit inside the edge.
"""

import dataclasses

from tests.unit.physics.test_oracles import _d08_design

from embodic.model.design import DesignParameters
from embodic.model.outline import CircleOutline

D08_CLEARANCE_MM = 0.8


def d08_design() -> DesignParameters:
    """O1-D08 with trace and via clearance rules at s and an outline that clears its copper."""
    base = _d08_design()
    rules = dataclasses.replace(base.drc_rules, trace_clearance_mm=D08_CLEARANCE_MM, via_clearance_mm=D08_CLEARANCE_MM)
    outline = dataclasses.replace(base.outline, board=CircleOutline(radius_mm=60.0), bore=CircleOutline(radius_mm=10.0))
    return dataclasses.replace(base, drc_rules=rules, outline=outline)
