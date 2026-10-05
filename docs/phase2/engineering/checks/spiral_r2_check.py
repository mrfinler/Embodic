# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Check of the spiral turn geometry revision 2026-10-05 (U-E3): flux linkage against the concentric-loop model and lead
# clearances, for worked examples 1 (CF-11) and 2 (D08). Uses spiral_reference.py for the geometry and embodic's own
# field table, path integrator and DRC distance kernels (read-only). Run from the repo root:
#     .venv/bin/python docs/phase2/engineering/checks/spiral_r2_check.py
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import spiral_reference as sr  # noqa: E402
from tests.unit.generators.default_example import default_design  # noqa: E402
from tests.unit.physics.test_oracles import _d08_design  # noqa: E402

from embodic.drc.kernels import closest_pairs  # noqa: E402
from embodic.geometry.primitives import Arc, Line, PrimitiveRole  # noqa: E402
from embodic.physics.emf import field_table, integrate_path  # noqa: E402
from embodic.physics.field import symmetry_plane_mm  # noqa: E402

ang = sr.ang


def line(a, b, w, role=PrimitiveRole.SIDE):
    return Line(x1_mm=a[0], y1_mm=a[1], x2_mm=b[0], y2_mm=b[1], width_mm=w, role=role)


def arc(r, a, b, w, role=PrimitiveRole.END_TURN):
    return Arc(cx_mm=0.0, cy_mm=0.0, r_mm=r, start_rad=ang(a), sweep_rad=ang(b) - ang(a), width_mm=w, role=role)


def x_path(g, turns, N):
    """Canonical layer X (revision 2026-10-05): stub, N turns with the outer-end jog, one lead arc at r_v."""
    p = sr.coil_path(g, turns, N)
    L, T, rv = p["lead_point_L"], p["terminal_point"], p["r_v"]
    prims = [("stub", line(T, turns[0]["A"], g.w, PrimitiveRole.STUB))]
    for t in range(N):
        tt = turns[t]
        top = turns[t + 1]["J"] if t < N - 1 else L
        prims += [(f"outer {t}", arc(tt["R_out"], tt["J"], tt["B"], g.w_out)),
                  (f"right {t}", line(tt["B"], tt["C"], g.w)),
                  (f"inner {t}", arc(tt["R_in_or_apex"], tt["C"], tt["D"], g.w_in)),
                  (f"left {t}", line(tt["D"], top, g.w))]
    prims.append(("lead", arc(rv, L, (rv, 0.0), g.w, PrimitiveRole.LEAD)))
    vias = {"centre": (rv, 0.0), "terminal X": T, "terminal Y": (T[0], -T[1])}
    return prims, vias


def concentric_loops(g, turns, N):
    """D08 Fig. 3.4 loop model with the same radii: N closed loops, both sides on d_k."""
    out = []
    for t in range(N):
        tt = turns[t]
        out.append([arc(tt["R_out"], tt["A"], tt["B"], g.w_out), line(tt["B"], tt["C"], g.w),
                    arc(tt["R_in_or_apex"], tt["C"], tt["D"], g.w_in), line(tt["D"], tt["A"], g.w)])
    return out


def mirror(pr):
    if isinstance(pr, Line):
        return Line(x1_mm=pr.x2_mm, y1_mm=-pr.y2_mm, x2_mm=pr.x1_mm, y2_mm=-pr.y1_mm, width_mm=pr.width_mm, role=pr.role)
    end = pr.start_rad + pr.sweep_rad
    return Arc(cx_mm=0.0, cy_mm=0.0, r_mm=pr.r_mm, start_rad=-end, sweep_rad=pr.sweep_rad, width_mm=pr.width_mm,
               role=pr.role)


def rotate(pr, a):
    c, s = math.cos(a), math.sin(a)
    if isinstance(pr, Line):
        return Line(x1_mm=c * pr.x1_mm - s * pr.y1_mm, y1_mm=s * pr.x1_mm + c * pr.y1_mm, x2_mm=c * pr.x2_mm - s * pr.y2_mm,
                    y2_mm=s * pr.x2_mm + c * pr.y2_mm, width_mm=pr.width_mm, role=pr.role)
    return Arc(cx_mm=0.0, cy_mm=0.0, r_mm=pr.r_mm, start_rad=pr.start_rad + a, sweep_rad=pr.sweep_rad,
               width_mm=pr.width_mm, role=pr.role)


def row(pr):
    if isinstance(pr, Line):
        return np.array([[pr.x1_mm, pr.y1_mm, pr.x2_mm, pr.y2_mm, pr.width_mm]]), False
    return np.array([[0.0, 0.0, pr.r_mm, pr.start_rad, pr.sweep_rad, pr.width_mm]]), True


def distance(a, b):
    ra, aa = row(a)
    rb, ab = row(b)
    return float(closest_pairs(ra, aa, rb, ab)[0][0])


def point(p):
    return Line(x1_mm=p[0], y1_mm=p[1], x2_mm=p[0], y2_mm=p[1], width_mm=0.0, role=PrimitiveRole.LEAD)


def lands_on(pr, v):
    return min(math.dist(pr.start_point(), v), math.dist(pr.end_point(), v)) < 1e-9


def linkage(design, prims_list):
    from embodic.generators import build_layout
    from embodic.results import load_registry
    stack = build_layout(design, load_registry())
    board = stack.boards[0]
    rotor = design.rotor
    z = board.copper_z_mm[board.paths[0].layer]
    table = field_table(rotor, symmetry_plane_mm(rotor, stack.stack_thickness_mm), z + rotor.air_gap_mm, (1,))
    p = rotor.poles // 2
    return [complex(integrate_path(tuple(pr), table, p, 0.5, 1.0).flux_linkage_t_mm2[0]) * 1e-6 for pr in prims_list]


def report(name, g, design, n_override=None):
    turns, _ = sr.turn_limit(g)
    N = sr.max_turns_with_eye(g, turns) if n_override is None else n_override
    prims, vias = x_path(g, turns, N)
    x = [pr for _, pr in prims]
    y = [mirror(pr) for pr in reversed(x)]
    loops_all = concentric_loops(g, turns, len(turns))
    lam = linkage(design, [x, y] + loops_all)
    lx, ly, lc = lam[0], lam[1], lam[2:]
    conc_n, conc_all = abs(sum(lc[:N])), abs(sum(lc))
    pair = abs(lx - ly) / 2 if abs(lx - ly) > abs(lx + ly) else abs(lx + ly) / 2
    print("=" * 100)
    print(f"{name}: loop-rule turns {len(turns)}, eye-limited N = {N}, r_v {vias['centre'][0]:.4f} mm")
    print(f" p*flux one layer X (stub+body+lead) |lambda_X| = {abs(lx):.6f} V*s/rad; X+Y pair per layer = {pair:.6f}")
    print(f" concentric loops (same radii): first N = {conc_n:.6f}, all {len(turns)} = {conc_all:.6f} V*s/rad; "
          f"per-loop {[round(abs(v), 6) for v in lc]}")
    print(f" ratios: X/conc(N) = {abs(lx) / conc_n:.4f}; pair/conc(N) = {pair / conc_n:.4f}; "
          f"pair/conc(all {len(turns)}) = {pair / conc_all:.4f}")
    # clearances: own coil and both neighbours, layer X (L1) and layer Y (L2), all vias through
    th = 2 * g.h
    own = {"X": prims, "Y": [(n, mirror(pr)) for n, pr in reversed(prims)]}
    nb = {lay: [(f"nb{sgn:+d} {n}", rotate(pr, sgn * th)) for sgn in (-1, 1) for n, pr in own[lay]] for lay in own}
    all_vias = dict(vias)
    for sgn in (-1, 1):
        for vn, v in vias.items():
            c, s = math.cos(sgn * th), math.sin(sgn * th)
            all_vias[f"nb{sgn:+d} {vn}"] = (c * v[0] - s * v[1], s * v[0] + c * v[1])
    worst_tt, worst_tv = (math.inf, ""), (math.inf, "")
    lead_rows = []
    for lay in ("X", "Y"):
        seq = own[lay]
        for i, (na, a) in enumerate(seq):
            for j, (nbn, b) in enumerate(seq):
                if j > i + 1:
                    c = distance(a, b) - a.width_mm / 2 - b.width_mm / 2
                    if c < worst_tt[0]:
                        worst_tt = (c, f"{lay}: {na} / {nbn}")
            for nbn, b in nb[lay]:
                c = distance(a, b) - a.width_mm / 2 - b.width_mm / 2
                if c < worst_tt[0]:
                    worst_tt = (c, f"{lay}: {na} / {nbn}")
            for vn, v in all_vias.items():
                if lands_on(a, v):
                    continue
                c = distance(a, point(v)) - a.width_mm / 2 - g.pad / 2
                if c < worst_tv[0]:
                    worst_tv = (c, f"{lay}: {na} / via {vn}")
            if na in ("stub", "lead"):
                tv = min((distance(a, point(v)) - a.width_mm / 2 - g.pad / 2, vn) for vn, v in all_vias.items()
                         if not lands_on(a, v))
                own_t = min((distance(a, b) - a.width_mm / 2 - b.width_mm / 2, nbn) for j, (nbn, b) in enumerate(seq)
                            if abs(j - i) > 1)
                nb_t = min((distance(a, b) - a.width_mm / 2 - b.width_mm / 2, nbn) for nbn, b in nb[lay])
                lead_rows.append((lay, na, tv, own_t, nb_t))
    print(" lead clearance table (copper edge to edge, mm; rule s = %.3f):" % g.s)
    for lay, na, tv, own_t, nb_t in lead_rows:
        print(f"   layer {lay} {na:5s}: to nearest via {tv[0]:.4f} ({tv[1]}); to own turns {own_t[0]:.4f} ({own_t[1]}); "
              f"to neighbours {nb_t[0]:.4f} ({nb_t[1]})")
    print(f" smallest trace-trace clearance (non-adjacent, own + neighbours): {worst_tt[0]:.4f} mm ({worst_tt[1]})")
    print(f" smallest trace-via clearance (pairs that do not land): {worst_tv[0]:.4f} mm ({worst_tv[1]})")
    return pair / conc_all


if __name__ == "__main__":
    g11 = sr.Geo(12, 18.0, 38.0, 0.5, 0.2, 0.2, 0.6)
    report("CF-11 default 12/16", g11, default_design())
    g08 = sr.Geo(12, 11.47, 45.03, 2.06, 0.8, 0.8, 0.6)
    report("CF-10 D08 12/10", g08, _d08_design())
