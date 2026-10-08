"""The D08 12/10 spiral example (CF-10, O1-D08) as a DRC-checkable board.

The copper inputs are the OR-01 design of tests/unit/physics/test_oracles.py, which also takes its outline from here:
a circle of radius 66 mm with a 10 mm bore (`assumption`, example values; O1-D08 gives no outline), so the example
board of tests/unit/model/designs.py (bore 12.5 mm) does not cut D08's copper from r 11.47 mm and the bus rings fit
inside the edge. The outline does not enter Ke. This module adds the DRC trace and via clearances at D08's s 0.8 mm
(Table 4.5 p.54), so a pass shows the clearance table of spiral_generator_spec.md worked example 2.
"""

import dataclasses

from embodic.model.design import DesignParameters
from embodic.model.outline import CircleOutline, OutlineSpec

D08_CLEARANCE_MM = 0.8
D08_OUTLINE = OutlineSpec(board=CircleOutline(radius_mm=66.0), bore=CircleOutline(radius_mm=10.0))


def d08_design() -> DesignParameters:
    """O1-D08 with trace and via clearance rules at s."""
    from tests.unit.physics.test_oracles import _d08_design  # test_oracles imports D08_OUTLINE from here

    base = _d08_design()
    rules = dataclasses.replace(base.drc_rules, trace_clearance_mm=D08_CLEARANCE_MM, via_clearance_mm=D08_CLEARANCE_MM)
    return dataclasses.replace(base, drc_rules=rules)
