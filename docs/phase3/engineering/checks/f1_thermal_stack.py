"""Fix wave F1 item C: cooling area of a multi-board stack in EQ-17 (U-E17, Agent 2).

Run from the repository root: PYTHONPATH=src:. python3 docs/phase3/engineering/checks/f1_thermal_stack.py

Part 1 reads what analyse() returns today for the serpentine example as one board per phase (the UT-GEN-03 design of
tests/unit/generators/serpentine/support.py) and for the same example as a single board. It prints the ratio
dT * h * 2 * A_1 / P_loss, where A_1 is the face area of one board: Xcoil's form gives 1, embodic's gives 1 / n.
Part 2 compares the conduction resistance of the inter-board air gap with the convection resistance of a face, per
unit area, from D01 Table 3 (k_air) and D01 p.4 (h_t 10) or the default h 30 (Xcoil engine.js l.65, unsourced).
"""

from tests.unit.generators.serpentine.make_example import example_design
from tests.unit.generators.serpentine.support import per_phase

from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack
from embodic.physics import analyse
from embodic.physics.analyse import board_area_mm2
from embodic.results import load_registry

K_AIR_D01_W_PER_M_K = 0.0275  # D01 Table 3, p.4 (journal p.808)
K_AIR_D08_W_PER_M_K = 0.02514  # D08 eq. 7.3 constants, PDF p.82 (printed p.77)


def stack_ratio(label: str, design: object) -> None:
    """Print n, A_1, P, dT and dT h 2 A_1 / P for one design."""
    registry = load_registry()
    stack = build_layout(design, registry)
    assert isinstance(stack, BoardStack), stack
    result = analyse(design, stack, {}, registry)
    assert result is not None
    areas = [board_area_mm2(b) for b in stack.boards]
    h = design.operating.convection_h_w_m2k
    p, dt = result.loss_total_w.value, result.temperature_rise_k.value
    ratio = dt * h * 2 * areas[0] * 1e-6 / p
    print(f"{label}: n {len(stack.boards)}, gap {stack.board_gap_mm} mm, board t {stack.board_thickness_mm} mm")
    print(f"  A per board {areas} mm2, h {h} W/m2K, P_loss {p!r} W, dT {dt!r} K")
    print(f"  dT h 2 A_1 / P = {ratio!r}  (1 = stack outer faces, 1/n = every face of every board)")
    height = len(stack.boards) * stack.board_thickness_mm + (len(stack.boards) - 1) * stack.board_gap_mm
    rims = [abs(q.sweep_rad) * q.r_mm for q in stack.boards[0].outline.outer if hasattr(q, "sweep_rad")]
    print(f"  outer rim {sum(rims):.3f} mm x stack height {height:.3f} mm = {sum(rims) * height:.1f} mm2, "
          f"{100 * sum(rims) * height / (2 * areas[0]):.1f} % of 2 A_1 (rim not in EQ-17)")  # fmt: skip


def gap_versus_face() -> None:
    """Per unit area: conduction across the gap t/k against convection 1/h."""
    for gap_mm in (0.1, 0.5):
        for k, src in ((K_AIR_D01_W_PER_M_K, "D01"), (K_AIR_D08_W_PER_M_K, "D08")):
            r_gap = gap_mm * 1e-3 / k
            for h in (10.0, 30.0):
                print(f"gap {gap_mm} mm, k_air {k} ({src}): R_gap {r_gap:.4e} m2K/W; h {h}: 1/h {1 / h:.4e} m2K/W, "
                      f"(1/h) / R_gap = {(1 / h) / r_gap:.1f}")  # fmt: skip


if __name__ == "__main__":
    stack_ratio("one board per phase", per_phase(example_design()))
    stack_ratio("single board", example_design())
    gap_versus_face()
