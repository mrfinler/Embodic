# Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5
"""F-OR07 diagnosis: sensitivity probes of the OR-07 D09 phase EMF through the public API (U-E11).

Run from the repository root:
    PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/f_or07_probe.py

Every probe changes one thing against the pre-registered O2-D09 variant A build of
docs/phase2/engineering/checks/oracles_probe.py (imported read-only) and prints the new emf_phase_rms_v and its
deviation from D09's 6.21 V. A sensitivity run is not a re-registration: the OR-07 verdict stays the one of the
pre-registered builds. The FEA radial profile is the Phase 1 digitisation of D09 Fig. 7
(docs/phase1/engineering/checks/edge_zone_d09.js, a figure reading, `inferred`).
"""

import dataclasses
import importlib.util
import math
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location(
    "oracles_probe", ROOT / "docs/phase2/engineering/checks/oracles_probe.py"
)
assert _spec is not None and _spec.loader is not None
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)

from embodic.geometry.discretise import discretise_path  # noqa: E402
from embodic.physics import field_harmonic, field_table, integrate_path, symmetry_plane_mm  # noqa: E402
from embodic.physics.emf import FieldTable  # noqa: E402

D09_CALC_V = 6.21  # D09 Table 4 p.6
D09_PHASE_LENGTH_MM = 3244.0  # D09 Table 1 p.3
D09_MID_LOOP_AREA_MM2 = 171.0  # D09 Table 1 p.3, "the loop in the middle of the number of turns"


def fea_profile() -> np.ndarray:
    """(r_mm, |B|_T) points of D09 Fig. 7 as digitised in Phase 1 (edge_zone_d09.js, `inferred`)."""
    text = (ROOT / "docs/phase1/engineering/checks/edge_zone_d09.js").read_text()
    body = re.search(r"const FIG = \[(.*?)\];", text, re.S)
    assert body is not None
    return np.array([[float(a), float(b)] for a, b in re.findall(r"\[([\d.]+), ([\d.]+)\]", body.group(1))])


def run(design):
    outcome = probe.run(design)
    a = outcome.analysis
    return outcome, a.emf_phase_rms_v.value


def dev(v: float) -> str:
    return f"{v:.5f} V ({v / D09_CALC_V - 1:+.2%})"


def with_coil(design, **changes):
    coil = dataclasses.replace(design.winding.coil, **changes)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


def with_rotor(design, **changes):
    return dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, **changes))


def with_magnet(design, **changes):
    return with_rotor(design, magnet=dataclasses.replace(design.rotor.magnet, **changes))


def centre_lines(design, r_i0: float, r_o0: float, turns: int):
    half = design.winding.coil.trace_width_mm / 2
    return with_coil(design, r_inner_mm=r_i0 - half, r_outer_mm=r_o0 + half, turns=turns)


def phase_a(outcome):
    """Phase A coil paths and chain paths of board 0, in the circuit's series order (one member per group)."""
    layout = outcome.boards.boards[0]
    paths = {p.id: p for p in layout.paths}
    groups = layout.circuit.phases[0].groups
    assert all(len(g.members) == 1 for g in groups), "phase A has parallel members; the recomputation assumes none"
    ids = [pid for g in groups for m in g.members for pid in m.path_ids]
    return layout, [paths[i] for i in ids]


def tables(outcome):
    design, layout = outcome.design, outcome.boards.boards[0]
    rotor = design.rotor
    g = symmetry_plane_mm(rotor, outcome.boards.stack_thickness_mm)
    return g, {
        z: field_table(rotor, g, z + rotor.air_gap_mm, design.analysis.harmonics) for z in layout.copper_z_mm.values()
    }


def ke_phase_a(outcome, table_of) -> tuple[float, list[complex]]:
    """|sum lambda_1| of phase A in V*s/rad and the per-path fundamental phasors, for any field table per layer."""
    design = outcome.design
    layout, paths = phase_a(outcome)
    p = design.rotor.poles // 2
    lam = []
    for path in paths:
        f = integrate_path(
            path.primitives, table_of(layout.copper_z_mm[path.layer]), p, design.analysis.max_segment_mm, 1.0
        )
        lam.append(complex(f.flux_linkage_t_mm2[0]))
    return abs(sum(lam)) * 1e-6, lam


def turn_areas_mm2(path) -> list[float]:
    """Shoelace area of each full turn of one spiral coil path, split at each 2 pi of winding angle about its centroid."""
    seg = discretise_path(path.primitives, 0.2)
    pts = np.array([(g.x1_mm, g.y1_mm) for g in seg] + [(seg[-1].x2_mm, seg[-1].y2_mm)])
    c = pts.mean(axis=0)
    ang = np.unwrap(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
    ang = np.abs(ang - ang[0])
    out = []
    k = 0
    while True:
        sel = (ang >= 2 * math.pi * k) & (ang <= 2 * math.pi * (k + 1))
        if ang[-1] < 2 * math.pi * (k + 1) - 1e-9:
            break
        q = pts[sel]
        out.append(float(abs(np.dot(q[:, 0], np.roll(q[:, 1], -1)) - np.dot(q[:, 1], np.roll(q[:, 0], -1))) / 2))
        k += 1
    return out


def main() -> None:
    base = probe.d09_design("A", 20.0)
    out_a, emf_a = run(base)
    a = out_a.analysis
    layout, paths_a = phase_a(out_a)
    coils_a = [p for p in paths_a if p.element is not None]
    print(
        f"P0 baseline A: emf_phase_rms_v {dev(emf_a)}; band [-5.00%, +{5 + 100 * a.edge_leakage_fraction.value:.2f}%]"
    )
    _, emf_b = run(probe.d09_design("B", 20.0))
    print(f"P0 baseline B: emf_phase_rms_v {dev(emf_b)}")

    # H-arith: rms, speed and the Ke chain
    omega_m = 2000 * 2 * math.pi / 60
    ke = a.ke_phase_v_s_per_rad.value
    print(
        f"H-arith: ke_phase {ke:.6f} V*s/rad x omega_m {omega_m:.4f} rad/s / sqrt2 = {ke * omega_m / math.sqrt(2):.5f} V; "
        f"f_e = 8 x 2000/60 = {8 * 2000 / 60:.2f} Hz (D09 266.67 Hz); peak would be {ke * omega_m:.4f} V"
    )

    # Instrument check: my recomputation of phase A from public kernels equals the product's Ke
    g, tab = tables(out_a)
    ke_mine, lam = ke_phase_a(out_a, lambda z: tab[z])
    print(
        f"Instrument: recomputed |sum lambda| phase A {ke_mine:.9f} vs product ke_phase {ke:.9f} (rel {ke_mine / ke - 1:.2e})"
    )

    # H-count: coils per phase, layers, in-phase sum
    print(
        f"H-count: phase A paths {len(paths_a)}, coil paths {len(coils_a)} on layers "
        f"{sorted({p.layer for p in coils_a})}; |sum|/sum|.| = {abs(sum(lam)) / sum(abs(x) for x in lam):.6f}"
    )

    # H-geometry: per-turn areas of one generated coil, against D09's mid-loop area
    areas = turn_areas_mm2(coils_a[0])
    n = len(areas)
    mid = (areas[n // 2 - 1] + areas[n // 2]) / 2 if n % 2 == 0 else areas[n // 2]
    print(
        f"H-geometry A: {n} full turns, areas outer->inner {[round(x, 1) for x in areas]} mm^2; mid-turn {mid:.1f} mm^2 "
        f"(D09 171 mm^2, {mid / D09_MID_LOOP_AREA_MM2 - 1:+.1%}); sum of turn areas {sum(areas):.1f} mm^2"
    )
    coil_len, chain_len = probe.phase_a_lengths_mm(out_a)
    print(f"  phase A coil paths {coil_len:.1f} mm + chain {chain_len:.1f} mm (D09 3244 mm)")
    mean_perimeter = D09_PHASE_LENGTH_MM / 8
    for nn in (6, 7, 8):
        p_turn = mean_perimeter / nn
        print(
            f"  D09 numbers alone, N {nn}: mean turn perimeter {p_turn:.2f} mm, isoperimetric ratio 4 pi A / P^2 = "
            f"{4 * math.pi * D09_MID_LOOP_AREA_MM2 / p_turn**2:.3f} (circle 1, square 0.785)"
        )

    # H-turns: N at A's centre lines, and N with D09-consistent radii
    for nn in (6, 7, 8, 9):
        o, e = run(centre_lines(base, 25.2, 47.6, nn))
        cl, ch = probe.phase_a_lengths_mm(o)
        print(
            f"H-turns N {nn} at 25.2/47.6: turns_achieved {o.boards.boards[0].detail.turns_achieved}, {dev(e)}, coil length {cl:.1f} mm"
        )

    # H-radii: sweep the centre lines at N 8 and N 7
    for nn, ri, ro in (
        (8, 25.2, 46.6),
        (8, 26.2, 47.6),
        (7, 25.2, 47.6),
        (7, 25.2, 46.0),
        (7, 26.0, 46.0),
        (7, 25.0, 45.0),
    ):
        o, e = run(centre_lines(base, ri, ro, nn))
        cl, _ = probe.phase_a_lengths_mm(o)
        _, pa = phase_a(o)
        ar = turn_areas_mm2([p for p in pa if p.element is not None][0])
        m = len(ar)
        mid_ar = (ar[m // 2 - 1] + ar[m // 2]) / 2 if m % 2 == 0 else ar[m // 2]
        print(f"H-radii N {nn} {ri}/{ro}: {dev(e)}; coil length {cl:.1f} mm; mid-turn area {mid_ar:.1f} mm^2")

    # H-method: D09 multiplies the flux of the middle loop by N (p.5); embodic sums every turn
    emf_n = [0.0] + [run(centre_lines(base, 25.2, 47.6, nn))[1] for nn in range(1, 9)]
    per_turn = [emf_n[k] - emf_n[k - 1] for k in range(1, 9)]
    print(f"H-method: EMF added by turn k (outer->inner) {[round(x, 4) for x in per_turn]} V")
    mid_x_n = 8 * (per_turn[3] + per_turn[4]) / 2
    print(
        f"  D09 method, N x (mean of turns 4 and 5) = {dev(mid_x_n)}; embodic sum {dev(emf_n[8])}; ratio {emf_n[8] / mid_x_n:.4f}"
    )

    # H-consistent: generated coils that meet both D09 Table 1 numbers (phase length incl. chain, mid-turn area)
    grid = {
        "parallel": ((6, 7, 8), (22.0, 23.0, 24.0, 25.0, 26.0, 27.0)),
        "radial": ((6, 7), (22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0)),
    }
    print(
        "H-consistent: side, N, R_i0, R_o0 | EMF | length (coil+chain) vs 3244 | mid-turn area vs 171, both within 5 %:"
    )
    for side, (turn_set, inner_set) in ({} if "--no-grid" in sys.argv else grid).items():
        rows = []
        for nn in turn_set:
            for ri in inner_set:
                for ro in (44.0, 45.0, 46.0, 47.0, 48.0):
                    design = with_coil(centre_lines(base, ri, ro, nn), side_style=probe.SideStyle(side))
                    try:
                        o, e = run(design)
                    except AssertionError:
                        continue
                    if o.boards.boards[0].detail.turns_achieved != nn:
                        continue
                    cl, ch = probe.phase_a_lengths_mm(o)
                    _, pa = phase_a(o)
                    ar = turn_areas_mm2([p for p in pa if p.element is not None][0])
                    m = len(ar)
                    mid_ar = (ar[m // 2 - 1] + ar[m // 2]) / 2 if m % 2 == 0 else ar[m // 2]
                    rows.append(
                        (nn, ri, ro, e, (cl + ch) / D09_PHASE_LENGTH_MM - 1, mid_ar / D09_MID_LOOP_AREA_MM2 - 1)
                    )
        hits = [r for r in rows if abs(r[4]) <= 0.05 and abs(r[5]) <= 0.05]
        for nn, ri, ro, e, dl, da in hits:
            print(f"  {side} N {nn} {ri}/{ro} | {dev(e)} | {dl:+.1%} | {da:+.1%}")
        print(
            f"  {side}: {len(rows)} buildable grid points, {len(hits)} within 5 % of both; N per hit {sorted({r[0] for r in hits})}"
        )

    # H-side and H-gap (assumptions of the build)
    try:
        run(with_coil(base, side_style=probe.SideStyle("radial")))
    except AssertionError as err:
        print(f"H-side radial at N 8: not buildable ({err.args[0][0].code}, limit {err.args[0][0].limit})")
    e6r = run(with_coil(centre_lines(base, 25.2, 47.6, 6), side_style=probe.SideStyle("radial")))[1]
    o6 = run(with_coil(centre_lines(base, 25.2, 47.6, 6), side_style=probe.SideStyle("radial")))[0]
    cl6, ch6 = probe.phase_a_lengths_mm(o6)
    ar6 = turn_areas_mm2([p for p in phase_a(o6)[1] if p.element is not None][0])
    print(
        f"H-side radial N 6: {dev(e6r)} against parallel N 6 {dev(emf_n[6])}; radial N 6 length (coil+chain) "
        f"{cl6 + ch6:.1f} mm, mid-turn area {(ar6[2] + ar6[3]) / 2:.1f} mm^2"
    )
    for gap in (0.0, 0.5, 1.0):
        o, e = run(with_coil(base, coil_gap_mm=gap))
        print(f"H-gap {gap} mm: {dev(e)}")

    # H-mur, H-Br, H-magnet
    for mu in (1.03, 1.10):
        print(f"H-mur {mu}: {dev(run(with_rotor(base, recoil_permeability=mu))[1])}")
    print(f"H-Br 1.20 T (sensitivity only): {dev(run(with_rotor(base, remanence_t=1.20))[1])}")
    for ra, rb in ((26.0, 45.0), (25.0, 45.0), (26.0, 46.0)):
        print(f"H-magnet span {ra}-{rb} mm: {dev(run(with_magnet(base, r_inner_mm=ra, r_outer_mm=rb))[1])}")
    for ap in (0.70, 0.75):
        print(f"H-magnet pole-arc ratio {ap}: {dev(run(with_magnet(base, pole_arc_ratio=ap))[1])}")

    # H-z: field at the copper z against the centre plane (D09 does not state its axial position)
    rotor = base.rotor
    r_mid = np.array([35.5])
    alpha = np.array([rotor.magnet.pole_arc_ratio])
    z_cu = min(layout.copper_z_mm.values()) + rotor.air_gap_mm
    b_cu = field_harmonic(1, r_mid, np.array([z_cu]), rotor, g, alpha)[0][0]
    b_c = field_harmonic(1, r_mid, np.array([g]), rotor, g, alpha)[0][0]
    b_face = field_harmonic(1, r_mid, np.array([0.0]), rotor, g, alpha)[0][0]
    print(
        f"H-z: B1 at mid-radius: copper z {z_cu:.4f} mm {b_cu:.5f} T, centre plane {g:.2f} mm {b_c:.5f} T ({b_c / b_cu - 1:+.2%}), magnet face {b_face:.5f} T"
    )

    # H-edge and H-2D: replace the 2-D radial profile by the FEA profile of D09 Fig. 7 (Phase 1 normalisation)
    fig = fea_profile()
    peak = lambda r, z: sum(
        field_harmonic(k, np.array([r]), np.array([z]), rotor, g, alpha)[0][0] for k in range(1, 14, 2)
    )  # noqa: E731
    plateau = np.arange(30.0, 41.0 + 1e-9, 0.25)
    norm = np.mean(np.interp(plateau, fig[:, 0], fig[:, 1])) / np.mean([peak(r, g) for r in plateau])
    print(f"H-edge: FEA plateau 30-41 mm / 2-D model plateau = {norm:.4f} (Phase 1: same method)")

    def table_with(z, factor):
        t = tab[z]
        steps = t.bz_t.shape[1] - 1
        radii = t.r_inner_mm + (t.r_outer_mm - t.r_inner_mm) * np.arange(steps + 1) / steps
        bz = t.bz_t * factor(t.bz_t[0], radii)[None, :]
        return FieldTable(r_inner_mm=t.r_inner_mm, r_outer_mm=t.r_outer_mm, harmonics=t.harmonics, bz_t=bz, bt_t=t.bt_t)

    def edge_k(b1, radii):
        return np.interp(radii, fig[:, 0], fig[:, 1]) / (np.array([peak(r, g) for r in radii]) * norm)

    def flat(b1, radii):
        return np.interp(35.5, radii, b1) / b1

    def d09_method(b1, radii):
        shape = np.interp(radii, fig[:, 0], fig[:, 1]) / np.interp(35.5, fig[:, 0], fig[:, 1])
        return np.interp(35.5, radii, b1) * shape / b1

    for label, fac in (
        ("H-edge FEA radial profile (Fig. 7 / 2-D model, plateau-normalised)", edge_k),
        ("H-2D flat B1(35.5 mm) at every radius", flat),
        ("H-2D D09 method: B1(35.5 mm) x Fig. 7 shape normalised at 35.5 mm", d09_method),
    ):
        k2, _ = ke_phase_a(out_a, lambda z, fac=fac: table_with(z, fac))
        print(f"{label} on the generated A paths: Ke x {k2 / ke:.4f} -> {dev(emf_a * k2 / ke)}")
    print(f"  e_edge (EC-05) of the A build {a.edge_leakage_fraction.value:.4f}")
    print(
        f"H-kw: A x 0.866 (pitch factor sin(240 deg/2), if D09's k_w were applied on top of the loop integral) -> {dev(emf_a * math.sin(math.radians(120)))}"
    )
    print(
        f"Needed: model/calc must fall to 1.05 + e_edge = {1.05 + a.edge_leakage_fraction.value:.4f}; A is {emf_a / D09_CALC_V:.4f}; "
        f"a cause must remove {1 - (1.05 + a.edge_leakage_fraction.value) / (emf_a / D09_CALC_V):.2%} of the A value to reach the band edge"
    )


if __name__ == "__main__":
    main()
