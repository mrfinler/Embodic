"""Inputs of the PR-14 round-off bound (U-E16): chords summed per path and the cancellation ratio of the fundamental.

Run from the worktree root:
    PYTHONPATH=src:. .venv/bin/python docs/phase3/engineering/checks/pr14_roundoff_inputs.py

For each path, N is the number of chords that integrate_path adds into the flux linkage, and
kappa = sum |B_z,1 r_m dr| / |sum B_z,1 r_m dr exp(-j p theta_m)| = PathField.edge_weight / |flux_linkage[0]|.
The recursive-summation forward error of the fundamental is at most gamma_N * kappa with gamma_N = N u / (1 - N u)
and u = 2**-53 (Higham, Accuracy and Stability of Numerical Algorithms, 2nd ed., section 4.2; cited from memory).
The board kappa (sum of edge_weight over sum of |flux_linkage[0]|) bounds the phase-level ratio when the paths of a
phase add in phase, which the series coils of one phase do (inferred).
"""

from tests.unit.generators.serpentine.make_example import example_design
from tests.unit.generators.serpentine.support import with_winding
from tests.unit.generators.wave.designs import wave

from embodic.generators import build_layout
from embodic.generators.wave.generate import generate_wave_rotated
from embodic.geometry.discretise import discretise_path
from embodic.geometry.layout import BoardStack
from embodic.model.winding_specs import CornerStyle, WaveStyle
from embodic.physics.emf import field_table, integrate_path
from embodic.physics.field import symmetry_plane_mm
from embodic.results import load_registry

REGISTRY = load_registry()
U = 2.0**-53


def _inputs(name: str, design, stack: BoardStack) -> None:  # type: ignore[no-untyped-def]
    rotor = design.rotor
    pole_pairs = rotor.poles // 2
    g_plane = symmetry_plane_mm(rotor, stack.stack_thickness_mm)
    n_max, kappa_max, n_total, weight, linkage = 0, 0.0, 0, 0.0, 0.0
    for layout in stack.boards:
        for path in layout.paths:
            z = layout.copper_z_mm[path.layer]
            table = field_table(rotor, g_plane, z + rotor.air_gap_mm, (1,))
            field = integrate_path(path.primitives, table, pole_pairs, 0.5, 1.0)
            n = len(discretise_path(path.primitives, 0.5))
            n_total += n
            lam = abs(field.flux_linkage_t_mm2[0])
            weight += field.edge_weight
            linkage += lam
            if lam > 0.0:
                n_max = max(n_max, n)
                kappa_max = max(kappa_max, field.edge_weight / lam)
    gamma = n_total * U / (1 - n_total * U)
    kappa_board = weight / linkage
    print(f"{name}: chords on the board {n_total}, largest path {n_max}, largest path kappa {kappa_max:.3f}, "
          f"board kappa {kappa_board:.3f}, gamma_N(board) {gamma:.2e}, "
          f"gamma_N(board) * board kappa {gamma * kappa_board:.2e}")  # fmt: skip


if __name__ == "__main__":
    serp = with_winding(example_design(), turns=1, corner_style=CornerStyle.SHARP)
    stack = build_layout(serp, REGISTRY)
    assert isinstance(stack, BoardStack)
    _inputs("serpentine sharp 1 turn", serp, stack)
    wav = wave(WaveStyle.OVERLAP, poles=8)
    wstack = generate_wave_rotated(wav, REGISTRY, 0.0)
    assert isinstance(wstack, BoardStack)
    _inputs("wave overlap", wav, wstack)
