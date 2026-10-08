"""Fable's M3 acceptance probe (read-only; run from the repository root with the project venv).

Prints, for every packaged example: the `compute_project` outcome (ok flag, validation issues, board count, build
warnings, DRC verdict per board, the main analysis quantities with their status), and for the serpentine example the
one-board-per-phase variant (board count, copper z per board, Ke and R with status). It asserts nothing beyond what
it prints; the pass/fail reading is Fable's and is recorded in decision_log.md D-037.
"""

from __future__ import annotations

from pathlib import Path

from tests.unit.generators.serpentine.support import per_phase

from embodic.api import compute, compute_project
from embodic.io.examples import list_examples, load_example
from embodic.outcome import ComputeOutcome

QUANTITIES = (
    "ke_line_peak_v_s_per_rad",
    "resistance_phase_operating_ohm",
    "torque_n_m",
    "loss_copper_w",
    "loss_eddy_w",
    "loss_interconnect_w",
    "efficiency",
)


def describe(name: str, outcome: ComputeOutcome) -> None:
    """Print the outcome of one compute run: issues, boards, DRC verdicts and the main quantities."""
    print(f"== {name}: ok={outcome.ok} issues={[i.code for i in outcome.issues]}")
    stack = outcome.boards
    if stack is None:
        print("   no boards built")
        return
    print(f"   boards={len(stack.boards)} build_issues={[i.code for i in stack.issues]} gap={stack.board_gap_mm} mm")
    for k, board in enumerate(stack.boards):
        z = {layer: round(v, 4) for layer, v in board.copper_z_mm.items()}
        print(f"   board {k}: paths={len(board.paths)} vias={len(board.vias)} copper_z_mm={z}")
    for k, report in enumerate(outcome.drc or ()):
        print(f"   drc board {k}: passed={report.passed} violations={report.violation_count}")
    analysis = outcome.analysis
    if analysis is None:
        print("   no analysis")
        return
    for q in QUANTITIES:
        t = getattr(analysis, q)
        print(f"   {q} = {t.value:.6g} {t.unit.value} [{t.status.value}]")


def main() -> None:
    """Run every packaged example, then the serpentine example as one board per phase."""
    root = Path("resources/examples")
    for info in list_examples():
        name = info.example_id
        result = compute_project(root / f"{name}.embodic.json")
        if isinstance(result, tuple):
            print(f"== {name}: compute_project refused: {[i.code for i in result]}")
            continue
        describe(name, result)
    _, design = load_example("serpentine_16p_example")
    stacked = per_phase(design)
    outcome = compute(stacked, {})
    assert outcome is not None
    describe("serpentine_16p_example / one_board_per_phase (gap 0.1 mm, 2 layers per phase)", outcome)


if __name__ == "__main__":
    main()
