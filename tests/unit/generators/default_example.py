"""The default 12/16 spiral example built from CF-11 in docs/phase2/engineering/oracle_cases.json.

Board, rotor, stack-up and DRC minima not in CF-11 come from tests/unit/model/designs.py (example values); the DRC
trace and via clearances equal the CF-11 clearance s.
"""

import dataclasses
import json
from pathlib import Path

from tests.unit.model.designs import spiral_design

from embodic.model.design import DesignParameters
from embodic.model.vias import ViaSpec
from embodic.model.winding_specs import SpiralCoilSpec, SpiralWindingSpec

ORACLE = Path(__file__).resolve().parents[3] / "docs" / "phase2" / "engineering" / "oracle_cases.json"


def cf11_inputs() -> dict[str, float]:
    """CF-11 input values by name."""
    case = next(c for c in json.loads(ORACLE.read_text())["cases"] if c["case_id"] == "CF-11")
    return {name: entry["value"] for name, entry in case["inputs"].items()}


def default_design() -> DesignParameters:
    """CF-11: Q 12, 2p 16, copper edges 18 to 38 mm, w 0.5, s 0.2, gap 0.2, via pad 0.6, bus width 1.0 mm."""
    v = cf11_inputs()
    base = spiral_design()
    assert isinstance(base.winding, SpiralWindingSpec)
    coil = SpiralCoilSpec(
        coil_count=int(v["Q"]),
        r_inner_mm=v["r_inner_mm"],
        r_outer_mm=v["r_outer_mm"],
        trace_width_mm=v["w_mm"],
        clearance_mm=v["s_mm"],
        coil_gap_mm=v["coil_gap_mm"],
    )
    return dataclasses.replace(
        base,
        rotor=dataclasses.replace(base.rotor, poles=int(v["poles"])),
        winding=dataclasses.replace(base.winding, coil=coil),
        vias=ViaSpec(drill_mm=base.vias.drill_mm, pad_mm=v["via_pad_mm"], plating_um=base.vias.plating_um),
        connection=dataclasses.replace(base.connection, ring_width_mm=v["bus_width_mm"]),
        drc_rules=dataclasses.replace(base.drc_rules, trace_clearance_mm=v["s_mm"], via_clearance_mm=v["s_mm"]),
    )
