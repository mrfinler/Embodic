# Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5
"""Decompose the generated D08 phase resistance by copper role and compare it with D08's loop model (U-E4).

Run from the repository root: .venv/bin/python docs/phase2/engineering/checks/d08_resistance_decomposition.py

The per-role sums use EQ-10 and EQ-11 with the registry constants, and the script asserts that they add up to the
phase resistance analyse() reports, so the table describes exactly what embodic sums. The D08 loop model is
D08 eq. 3.27-3.38 (PDF p.44-45, printed p.39-40) with the corrected straight-side term of EQ-03.
"""

import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tests.unit.generators.d08_example import d08_design  # noqa: E402
from tests.unit.physics.test_oracles import _d08_design  # noqa: E402

from embodic.errors import Unbuildable  # noqa: E402
from embodic.generators import build_layout  # noqa: E402
from embodic.geometry.primitives import Arc  # noqa: E402
from embodic.physics import analyse  # noqa: E402
from embodic.physics.resistance import copper_resistivity_ohm_m, via_resistance_ohm  # noqa: E402
from embodic.results import load_registry  # noqa: E402

D08_R_PHASE_OHM = 0.39  # D08 Table 4.6 PDF p.57 (printed p.52), loop-model calculation
D08_T_DEGC = 50.0  # D08 Table 4.5 PDF p.54 (printed p.49), track temperature
D08_R_I_MM, D08_R_O_MM = 12.5, 44.0  # D08 PDF p.55 (printed p.50), centre lines
D08_W_MM, D08_S_MM, D08_T_MM = 2.06, 0.8, 0.0348  # Table 4.6, Table 4.5, Table 4.5
D08_LOOPS, D08_POLE_PAIRS, D08_COILS = 3, 5, 12
COIL_LAYERS_PER_PHASE = 8  # 4 coils per phase x 2 layers in series (D08 PDF p.53, printed p.48)


def prim_length_mm(prim) -> float:
    """Chord of a line or r|sweep| of an arc, as EQ-03 primLength."""
    if isinstance(prim, Arc):
        return prim.r_mm * abs(prim.sweep_rad)
    return math.hypot(prim.x2_mm - prim.x1_mm, prim.y2_mm - prim.y1_mm)


def d08_loop_length_mm(span_rad: float) -> float:
    """Sum of D08's concentric loop lengths for one coil-layer (eq. 3.28-3.36, one straight side per L_s)."""
    w_d = D08_W_MM + D08_S_MM
    total = 0.0
    for i in range(D08_LOOPS):
        d = i * w_d + w_d / 2
        r_out, r_in = D08_R_O_MM - i * w_d, D08_R_I_MM + i * w_d
        phi_out, phi_in = math.asin(d / r_out), math.asin(d / r_in)
        beta_out, beta_in = span_rad / 2 - phi_out, span_rad / 2 - phi_in
        l_out = 2 * r_out * beta_out
        if beta_in > 0:
            l_in, l_s = 2 * r_in * beta_in, d / math.tan(phi_out) - d / math.tan(phi_in)
        else:
            l_in, l_s = 0.0, d / math.tan(phi_out) - d / math.tan(span_rad / 2)
        total += l_out + l_in + 2 * l_s
    return total


def decompose(design, registry):
    """Per-role length and 20 degC resistance of every phase member, checked against analyse()."""
    stack = build_layout(design, registry)
    assert not isinstance(stack, Unbuildable), stack
    layout = stack.boards[0]
    rho20 = registry.constant("copper_resistivity_20c_ohm_m").value
    thickness = {layer.name: layer.thickness_mm for layer in design.stackup.copper_layers()}
    paths = {p.id: p for p in layout.paths}
    vias = {v.id: v for v in layout.vias}
    # role -> phase -> [mm, ohm at 20 degC, count]; role -> widths
    rows: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0]))
    widths: dict[str, set[float]] = defaultdict(set)
    by_phase: dict[str, float] = {}
    for phase in layout.circuit.phases:
        total = 0.0
        for group in phase.groups:
            assert len(group.members) == 1, "D08 has no parallel members"
            member = group.members[0]
            for pid in member.path_ids:
                p = paths[pid]
                kind = "coil" if p.element is not None else "chain"
                for prim in p.primitives:
                    length = prim_length_mm(prim)
                    r = rho20 * (length / 1e3) / ((prim.width_mm / 1e3) * (thickness[p.layer] / 1e3))
                    total += r
                    row = rows[f"{kind} {prim.role.value}"][phase.phase.value]
                    row[0] += length
                    row[1] += r
                    row[2] += 1
                    widths[f"{kind} {prim.role.value}"].add(prim.width_mm)
            for vid in member.via_ids:
                v = vias[vid]
                r = via_resistance_ohm(v.drill_mm, design.vias.plating_um, stack.board_thickness_mm, rho20, 1)
                total += r
                row = rows[f"via {v.role.value}"][phase.phase.value]
                row[1] += r
                row[2] += 1
                widths[f"via {v.role.value}"].add(v.drill_mm)
        by_phase[phase.phase.value] = total
    ring = [0.0, 0.0, 0]
    for pid in layout.circuit.interconnect_path_ids:
        p = paths[pid]
        for prim in p.primitives:
            length = prim_length_mm(prim)
            ring[0] += length
            ring[1] += rho20 * (length / 1e3) / ((prim.width_mm / 1e3) * (thickness[p.layer] / 1e3))
            ring[2] += 1
    result = analyse(design, stack, {}, registry)
    analysed = {ph.phase.value: ph.resistance_20c_ohm.value for ph in result.phases}
    for name, value in by_phase.items():
        assert abs(value / analysed[name] - 1) < 1e-12, (name, value, analysed[name])
    return rows, widths, ring, by_phase, result


def main() -> None:
    """Print the role table and the 50 degC comparison with D08 Table 4.6."""
    registry = load_registry()
    rho20 = registry.constant("copper_resistivity_20c_ohm_m").value
    alpha = registry.constant("copper_temp_coeff_per_k").value
    k50 = copper_resistivity_ohm_m(D08_T_DEGC, rho20, alpha) / rho20
    rows, widths, ring, by_phase, result = decompose(d08_design(), registry)
    _, _, _, by_phase_or01, _ = decompose(_d08_design(), registry)
    phases = sorted(by_phase)
    mean = {name: [sum(rows[name][ph][k] for ph in phases) / len(phases) for k in range(3)] for name in rows}
    r_mean = sum(by_phase.values()) / len(phases)

    print("Generated D08 coil (tests/unit/generators/d08_example.py), 20 degC, mean over phases unless named")
    print(
        f"{'role':<18}{'width mm':>10}{'n/ph':>6}{'mm/ph':>11}"
        + "".join(f"{'R ' + ph:>10}" for ph in phases)
        + f"{'R mean':>10}{'share':>8}"
    )
    for name in sorted(rows, key=lambda n: -mean[n][1]):
        w = "/".join(f"{x:g}" for x in sorted(widths[name]))
        print(
            f"{name:<18}{w:>10}{mean[name][2]:>6.0f}{mean[name][0]:>11.4f}"
            + "".join(f"{rows[name][ph][1]:>10.6f}" for ph in phases)
            + f"{mean[name][1]:>10.6f}"
            + f"{mean[name][1] / r_mean:>8.1%}"
        )
    print(
        f"{'sum = R_phase':<18}{'':>16}{sum(m[0] for m in mean.values()):>11.4f}"
        + "".join(f"{by_phase[ph]:>10.6f}" for ph in phases)
        + f"{r_mean:>10.6f}{1:>8.1%}"
    )
    print(f"neutral ring, not in R_phase: {ring[2]} segments, {ring[0]:.4f} mm, {ring[1]:.6f} ohm")
    print(
        "analyse() resistance_phase_20c",
        round(result.resistance_phase_20c_ohm.value, 6),
        "| OR-01 design R_phase by phase",
        {k: round(v, 6) for k, v in by_phase_or01.items()},
    )

    body = sum(mean[n][1] for n in mean if n in ("coil side", "coil end_turn"))
    body_mm = sum(mean[n][0] for n in mean if n in ("coil side", "coil end_turn")) / COIL_LAYERS_PER_PHASE
    r_a = r_mean
    area = D08_W_MM * D08_T_MM / 1e6
    rho50 = rho20 * k50
    print(f"\nComparison at {D08_T_DEGC:.0f} degC (x {k50:.6f}, EQ-10 with the registry constants)")
    for span_name, span in (
        ("2 pi / Q (30 deg)", 2 * math.pi / D08_COILS),
        ("pi / p (36 deg)", math.pi / D08_POLE_PAIRS),
    ):
        loop_mm = d08_loop_length_mm(span)
        r_loop = rho50 * COIL_LAYERS_PER_PHASE * loop_mm / 1e3 / area
        print(
            f"D08 loop model, span {span_name:<18} {loop_mm:9.4f} mm/coil-layer  R {r_loop:.6f} ohm "
            f"({r_loop / D08_R_PHASE_OHM - 1:+.2%} vs 0.39)"
        )
    print(
        f"embodic coil body (sides + end-turns)        {body_mm:9.4f} mm/coil-layer  R {body * k50:.6f} ohm "
        f"({body * k50 / D08_R_PHASE_OHM - 1:+.2%} vs 0.39)"
    )
    print(
        f"embodic R_phase mean (body + stubs + chains + vias)               R {r_a * k50:.6f} ohm "
        f"({r_a * k50 / D08_R_PHASE_OHM - 1:+.2%} vs 0.39)"
    )
    print(
        f"non-loop copper in R_phase (full - body)                          R {(r_a - body) * k50:.6f} ohm "
        f"({(r_a - body) * k50 / D08_R_PHASE_OHM:+.2%} of 0.39)"
    )

    r_loop = rho50 * COIL_LAYERS_PER_PHASE * d08_loop_length_mm(2 * math.pi / D08_COILS) / 1e3 / area
    groups = {
        "stubs": ("coil stub",),
        "chains": ("chain ring", "chain leg"),
        "vias": ("via ring", "via terminal", "via centre"),
    }
    steps = [
        ("D08 0.39 -> loop model 2 pi/Q", r_loop - D08_R_PHASE_OHM),
        ("loop model -> generated coil body", body * k50 - r_loop),
        *((f"+ {g}", sum(mean[n][1] for n in names if n in mean) * k50) for g, names in groups.items()),
    ]
    print(f"\nBridge at {D08_T_DEGC:.0f} degC from 0.39 ohm to the mean R_phase")
    running = D08_R_PHASE_OHM
    for name, delta in steps:
        running += delta
        print(f"{name:<36}{delta:+11.6f} ohm {delta / D08_R_PHASE_OHM:+8.2%}   -> {running:.6f}")
    assert abs(running - r_a * k50) < 1e-12, (running, r_a * k50)


if __name__ == "__main__":
    main()
