"""OR-01 with an own field: D08 Ke_LL peak from own_emf.py on the subject's generated layout.

Run: python tests/independent/m2/or01.py  (prints own Ke, embodic's Ke, D08's measured value and the differences)

Field inputs come from docs/phase2/engineering/oracle_cases.json O1-D08 directly (G from the magnet face to the
board mid-plane, 'assumed' value where unresolved) and the constant pole-arc ratio 0.72 that test_oracles.py
pre-registers (assumption). Copper z: centre of each copper foil, foils on the two board faces (2-layer board).
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import own_emf  # noqa: E402

HARMONICS = (1, 3, 5, 7, 9, 11, 13)
STEP_MM = 0.05
POLE_ARC_RATIO = 0.72


def o1_d08() -> dict:
    """Return the O1-D08 case of oracle_cases.json."""
    cases = json.loads((ROOT / "docs/phase2/engineering/oracle_cases.json").read_text())["cases"]
    return next(c for c in cases if c["case_id"] == "O1-D08")


def own_field_and_z() -> tuple[own_emf.Field, list[float]]:
    """Return the own field and the copper-foil z from the magnet face, both from O1-D08 inputs."""
    v = {k: e["assumed"] if e["value"] is None else e["value"] for k, e in o1_d08()["inputs"].items()}
    t, cu, g = v["board_thickness_mm"], v["copper_thickness_mm"], v["magnet_face_to_midplane_G_mm"]
    field = own_emf.Field(
        poles=v["poles"],
        remanence_t=v["magnet_remanence_T"],
        mu_r=v["magnet_recoil_permeability"],
        magnet_mm=v["magnet_thickness_mm"],
        g_plane_mm=g,
        alpha=POLE_ARC_RATIO,
        r_a_mm=v["magnet_r_inner_mm"],
        r_b_mm=v["magnet_r_outer_mm"],
    )
    return field, [g - t / 2 + cu / 2, g + t / 2 - cu / 2]


def run() -> dict[str, float]:
    """Build D08 through the public API and return own and embodic Ke_LL with their differences."""
    from tests.unit.physics.test_oracles import _d08_design

    from embodic.generators import build_layout
    from embodic.physics import analyse
    from embodic.results import load_registry

    registry = load_registry()
    design = _d08_design()
    stack = build_layout(design, registry)
    layout = stack.boards[0]
    field, z_faces = own_field_and_z()
    z_of = dict(zip(layout.copper_layers, z_faces, strict=True))
    by_id = {p.id: p for p in layout.paths}
    lam = {}
    for phase in layout.circuit.phases:
        total = np.zeros(len(HARMONICS), dtype=np.complex128)
        for group in phase.groups:
            members = [
                sum(
                    own_emf.path_flux_linkage(by_id[i].primitives, field, z_of[by_id[i].layer], HARMONICS, STEP_MM)
                    for i in m.path_ids
                )
                for m in group.members
            ]
            total += sum(members) / len(members)
        lam[phase.phase.value] = total
    own = own_emf.line_peak_v_s_per_rad(lam["A"], lam["B"], HARMONICS, field.poles)
    result = analyse(design, stack, {}, registry)
    subject = result.ke_line_peak_v_s_per_rad.value
    measured = next(e for e in o1_d08()["expected"] if e["quantity"].startswith("Ke_LL_peak"))["value"]
    return {
        "own_ke_ll_peak": own,
        "embodic_ke_ll_peak": subject,
        "measured": measured,
        "embodic_vs_own_rel": subject / own - 1.0,
        "own_vs_measured_rel": own / measured - 1.0,
        "subject_copper_z_mm": dict(layout.copper_z_mm),
        "own_z_from_magnet_mm": z_of,
        "air_gap_mm": design.rotor.air_gap_mm,
    }


if __name__ == "__main__":
    for key, value in run().items():
        print(f"{key}: {value}")
