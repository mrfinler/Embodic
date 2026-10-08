"""Items 3 and 4 (U-V3): Ke_LL peak of ported layouts from Agent 4's own EQ-05/EQ-06 field (tests/independent/m2).

The field reads the design's rotor inputs; each copper layer sits at ``air_gap + z`` from the magnet face, with z the
BoardStack's ``copper_z_mm`` (stack z from the top surface, verified board by board in test_m3_layouts.py). The
double-rotor symmetry plane is at ``air_gap + stack_thickness / 2``. Phase flux linkage sums the members of each
series group and averages the parallel members, as in m2/or01.py.
"""

import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m2"))

import own_emf
from cases import xcoil_dumps
from subject import design_for, registry, stack_for

HARMONICS = (1, 3, 5, 7, 9, 11, 13)
STEP_MM = 0.05


def own_field(design: Any, stack: Any) -> own_emf.Field:
    """EQ-05 field of the design's arc-magnet double rotor for this stack."""
    rotor = design.rotor
    assert rotor.rotor_type.value == "double", rotor.rotor_type
    n = len(stack.boards)
    thickness = n * stack.board_thickness_mm + (n - 1) * stack.board_gap_mm
    return own_emf.Field(
        poles=rotor.poles,
        remanence_t=rotor.remanence_t,
        mu_r=rotor.recoil_permeability,
        magnet_mm=rotor.magnet.thickness_mm,
        g_plane_mm=rotor.air_gap_mm + thickness / 2,
        alpha=rotor.magnet.pole_arc_ratio,
        r_a_mm=rotor.magnet.r_inner_mm,
        r_b_mm=rotor.magnet.r_outer_mm,
    )


def own_ke_ll_peak(case_id: str, z_shift_per_board_mm: float = 0.0) -> float:
    """Own Ke_LL peak in V s/rad; ``z_shift_per_board_mm`` adds k times that to board k (to model DEF-M3a-01)."""
    design, stack = design_for(xcoil_dumps()[case_id]), stack_for(case_id)
    field = own_field(design, stack)
    lam: dict[str, np.ndarray] = {}
    for k, layout in enumerate(stack.boards):
        by_id = {p.id: p for p in layout.paths}
        for phase in layout.circuit.phases:
            total = lam.setdefault(phase.phase.value, np.zeros(len(HARMONICS), dtype=np.complex128))
            for group in phase.groups:
                members = [
                    sum(
                        own_emf.path_flux_linkage(
                            by_id[i].primitives,
                            field,
                            design.rotor.air_gap_mm + layout.copper_z_mm[by_id[i].layer] + k * z_shift_per_board_mm,
                            HARMONICS,
                            STEP_MM,
                        )
                        for i in m.path_ids
                    )
                    for m in group.members
                ]
                total += sum(members) / len(members)
    return own_emf.line_peak_v_s_per_rad(lam["A"], lam["B"], HARMONICS, field.poles)


def embodic_ke_ll_peak(case_id: str) -> float:
    """Embodic's Ke_LL peak through the public analyse()."""
    from embodic.physics import analyse

    design, stack = design_for(xcoil_dumps()[case_id]), stack_for(case_id)
    return analyse(design, stack, {}, registry()).ke_line_peak_v_s_per_rad.value


def main() -> None:
    """Print own and embodic Ke_LL peak for the item 3 and 4 layouts."""
    for cid in ("s-radial-t4", "w-involute-p20-l2-m3", "s-perphase-3-t5-gap0p3"):
        own, sub = own_ke_ll_peak(cid), embodic_ke_ll_peak(cid)
        print(f"{cid}: own {own:.7g} embodic {sub:.7g} rel {sub / own - 1:+.3e}")
    stack = stack_for("s-perphase-3-t5-gap0p3")
    pitch = stack.board_thickness_mm + stack.board_gap_mm
    doubled = own_ke_ll_peak("s-perphase-3-t5-gap0p3", z_shift_per_board_mm=pitch)
    print(f"s-perphase-3-t5-gap0p3 own with board k moved by a further k x {pitch:.2f} mm: {doubled:.7g}")


if __name__ == "__main__":
    main()
