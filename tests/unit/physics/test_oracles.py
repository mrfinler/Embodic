"""OR rows of test_plan.md that need analyse() on a generated layout (oracle_cases.json O1-D08).

The D08 design takes every O1-D08 input from oracle_cases.json, with the pre-registered 'assumed' value where an input
is unresolved. Board outline, vias, DRC minima and the operating point come from tests/unit/model/designs.py (example
values); Ke does not read them.
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
from tests.unit.model.designs import spiral_design

from embodic.errors import Unbuildable
from embodic.generators import build_layout
from embodic.model.design import DesignParameters
from embodic.model.rotor import ArcMagnet, RotorType
from embodic.model.stackup import generate_even_stackup
from embodic.model.vocabulary import ConnectionTopology
from embodic.model.winding_specs import SideStyle, SpiralWindingSpec
from embodic.physics import analyse
from embodic.results import load_registry

ORACLE = Path(__file__).resolve().parents[3] / "docs" / "phase2" / "engineering" / "oracle_cases.json"
D08_TOLERANCE = 0.08  # D08 p.98: D08's own analytical model deviated from this measurement by at most 8 %
# assumption: a constant pole-arc ratio stands in for the two-block T-arrangement, as Phase 1 did for O1
# (docs/phase1/engineering/checks/edge_zone_d09.js l.36); EQ-04 lists the T-arrangement as approximated.
D08_POLE_ARC_RATIO = 0.72


def _o1_d08() -> dict[str, Any]:
    return next(c for c in json.loads(ORACLE.read_text())["cases"] if c["case_id"] == "O1-D08")


def _inputs() -> dict[str, Any]:
    """Input values by name; an unresolved input takes its pre-registered 'assumed' value (primary case)."""
    return {
        name: entry["assumed"] if entry["value"] is None else entry["value"]
        for name, entry in _o1_d08()["inputs"].items()
    }


def _d08_design() -> DesignParameters:
    """O1-D08: 12 coils, 10 poles, 2 layers in series, 3 turns, w 2.06 mm, s 0.8 mm, double rotor, star."""
    v = _inputs()
    base = spiral_design()
    assert isinstance(base.winding, SpiralWindingSpec)
    half_width = v["trace_width_mm"] / 2
    coil = dataclasses.replace(
        base.winding.coil,
        coil_count=v["coil_count"],
        # D08 radii are centre lines; SpiralCoilSpec takes copper edges (spiral_generator_spec.md worked example 2)
        r_inner_mm=v["coil_r_inner_mm"] - half_width,
        r_outer_mm=v["coil_r_outer_mm"] + half_width,
        trace_width_mm=v["trace_width_mm"],
        clearance_mm=v["clearance_mm"],
        coil_gap_mm=v["clearance_mm"],  # inferred equal to s (spiral_generator_spec.md worked example 2)
        turns=v["turns_per_coil_per_layer"],
        side_style=SideStyle(v["side_style"]),
    )
    rotor = dataclasses.replace(
        base.rotor,
        poles=v["poles"],
        rotor_type=RotorType(v["rotor_type"]),
        magnet=ArcMagnet(
            pole_arc_ratio=D08_POLE_ARC_RATIO,
            r_inner_mm=v["magnet_r_inner_mm"],
            r_outer_mm=v["magnet_r_outer_mm"],
            thickness_mm=v["magnet_thickness_mm"],
        ),
        remanence_t=v["magnet_remanence_T"],
        recoil_permeability=v["magnet_recoil_permeability"],
        # O1 gives G from the magnet face to the board mid-plane; RotorSpec wants the gap to the board surface
        air_gap_mm=v["magnet_face_to_midplane_G_mm"] - v["board_thickness_mm"] / 2,
    )
    return dataclasses.replace(
        base,
        name="UGent D08 12/10 (O1-D08)",
        rotor=rotor,
        winding=dataclasses.replace(base.winding, coil=coil),
        stackup=generate_even_stackup(v["copper_layers"], v["copper_thickness_mm"], v["board_thickness_mm"]),
        connection=dataclasses.replace(base.connection, topology=ConnectionTopology(v["connection"])),
    )


@pytest.mark.req("REQ-F-11")
def test_or01_d08_line_line_ke_within_the_registry_band() -> None:
    """OR-01: model Ke_LL peak against D08's measured 0.031 V*s/rad in [-8 %, +8 % + e_edge] (test_plan.md section 4).

    Defect caught: a D08 layout or an EMF chain (EQ-05, EQ-06, EQ-07, EQ-09, EQ-18) that misses the measured line-line
    Ke. The compared value is the synthesised line waveform peak per rad/s, as D08 Table 9.1 measures it.
    e_edge is the computed edge_leakage_fraction of this design, not a constant (test_plan.md section 4). Only the band
    check raises AssertionError, so an Unbuildable D08 design fails this test outright instead of hiding in the xfail.
    """
    registry = load_registry()
    design = _d08_design()
    stack = build_layout(design, registry)
    if isinstance(stack, Unbuildable):
        pytest.fail(f"the D08 design must build: {stack.issues}")
    result = analyse(design, stack, {}, registry)
    if result is None:
        pytest.fail("analyse() returned None without a cancel token")
    measured = next(e for e in _o1_d08()["expected"] if e["quantity"].startswith("Ke_LL_peak"))["value"]
    model = result.ke_line_peak_v_s_per_rad.value
    deviation = model / measured - 1.0
    upper = D08_TOLERANCE + result.edge_leakage_fraction.value
    assert -D08_TOLERANCE <= deviation <= upper, (
        f"Ke_LL {model:.5f} V*s/rad is {deviation:+.1%} against D08's {measured}; band [{-D08_TOLERANCE:+.1%}, "
        f"{upper:+.1%}]"
    )
