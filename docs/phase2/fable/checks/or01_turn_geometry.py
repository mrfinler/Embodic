"""OR-01 investigation lever (Fable 5.1, claude-fable-5-1, 2026-10-05).

Reproduces the two numbers behind D-028: embodic's per-coil flux linkage on the generated UGent D08 coil, and the
same integral for concentric loops (D08 Fig. 3.4 loop model) with embodic's own B_z(r) table. Run from the repo root:

    .venv/bin/python docs/phase2/fable/checks/or01_turn_geometry.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tests.unit.physics.test_oracles import _d08_design  # noqa: E402

from embodic.generators import build_layout  # noqa: E402
from embodic.physics.emf import FieldTable, field_table, integrate_path  # noqa: E402
from embodic.physics.field import symmetry_plane_mm  # noqa: E402
from embodic.results import load_registry  # noqa: E402

SECTOR_HALF_RAD = math.radians(15.0)  # 12 coils
PITCH_MM = 2.06 + 0.8  # w_d = w + s (D08 Table 3.2)


def loop_linkage(
    table: FieldTable, pole_pairs: int, offset_mm: float, r_out_mm: float, apex_half_width_mm: float
) -> float:
    """Return p times the peak flux of one loop whose sides are the sector edges offset inward by offset_mm."""
    r_in = max(12.5, (apex_half_width_mm + offset_mm) / math.sin(SECTOR_HALF_RAD))
    if r_in >= r_out_mm:
        return 0.0
    radii = np.linspace(r_in, r_out_mm, 4000)
    dr = radii[1] - radii[0]
    total = 0.0
    for r in radii:
        if r < table.r_inner_mm or r > table.r_outer_mm:
            continue
        half_width = r * math.sin(SECTOR_HALF_RAD) - offset_mm
        total += 2.0 * float(table.at(r)[0][0]) * r * math.sin(pole_pairs * half_width / r) * dr
    return total * 1e-6  # T*mm^2 -> V*s/rad


def main() -> int:
    """Print the three linkages and their ratios."""
    registry = load_registry()
    design = _d08_design()
    stack = build_layout(design, registry)
    board = stack.boards[0]
    rotor = design.rotor
    g_plane = symmetry_plane_mm(rotor, stack.stack_thickness_mm)
    z = board.copper_z_mm[board.paths[0].layer]
    table = field_table(rotor, g_plane, z + rotor.air_gap_mm, (1,))
    pole_pairs = rotor.poles // 2
    generated = abs(integrate_path(board.paths[0].primitives, table, pole_pairs, 0.5, 1.0).flux_linkage_t_mm2[0]) * 1e-6
    half = PITCH_MM / 2.0
    concentric = sum(loop_linkage(table, pole_pairs, (k + 0.5) * PITCH_MM, 44.0 - k * PITCH_MM, half) for k in range(3))
    spiral = sum(loop_linkage(table, pole_pairs, (k + 1.0) * PITCH_MM, 44.0 - k * PITCH_MM, half) for k in range(3))
    print(f"embodic generated coil, one layer: p*flux = {generated:.5f} V*s/rad")
    print(f"concentric loops (both sides at offset (k+0.5) w_d, D08 Fig. 3.4): {concentric:.5f} V*s/rad")
    print(f"spiral-equivalent loops (left side one pitch further in): {spiral:.5f} V*s/rad")
    print(f"ratios: generated/concentric = {generated / concentric:.3f}; spiral/concentric = {spiral / concentric:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
