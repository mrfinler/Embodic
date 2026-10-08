# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Series-pair via fan of spiral_generator_spec.md G6 (revision 2026-10-08, U-E6; check updated U-E7): closed form,
# then a DRC proof. not product code. It compares main's ring vias (series.ring_vias, public) with the closed form
# below, runs main's generator unchanged, and runs embodic.drc.run_drc on the whole board and on the fan copper alone,
# printing the smallest clearance per check kind. Rule D-006, no exemption beyond interfaces.md section 7.
# Run: .venv/bin/python docs/phase2/engineering/checks/series_fan_check.py   (from the repository root)
"""Series via fan of spiral_generator_spec.md G6 (U-E6): closed form and DRC runs on CF-11 and D08."""

import dataclasses
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tests.unit.generators.d08_example import d08_design  # noqa: E402
from tests.unit.generators.default_example import default_design  # noqa: E402

import embodic.generators.spiral.generate as gen  # noqa: E402
from embodic.drc import run_drc  # noqa: E402
from embodic.generators.spiral.artwork import sharp_artwork  # noqa: E402
from embodic.generators.spiral.series import ring_vias  # noqa: E402
from embodic.geometry.layout import BoardStack, ViaRole  # noqa: E402
from embodic.geometry.primitives import PrimitiveRole  # noqa: E402
from embodic.model.layers import LayerConfig, LayerPair  # noqa: E402
from embodic.model.stackup import generate_even_stackup  # noqa: E402
from embodic.results import load_registry  # noqa: E402


def fan_pitch(pad, w, bw, s):
    """G6: centre distance of neighbouring fan vias, c_f = max(pad, w, bw) + s."""
    return max(pad, w, bw) + s


def fan_angles(r_t, a_v, a_a, r_o0, h, pad, w, bw, s, levels):
    """G6: a_0 = a_V; a_l = min(a_V - da, h - asin((d_0 + w + s) / R_o0)) - (l - 1) da for l >= 1, da = asin(c_f / r_T).

    The first term keeps a radial stub at a_l clear of via l - 1. The second keeps its foot w + s from the side line d_0
    that ends at the corner A_0 on the same layer (two main primitives away, so D-022 rule 1 does not exempt it).
    d_0 = R_o0 sin(h - a_A) holds for parallel sides.
    """
    da = math.asin(fan_pitch(pad, w, bw, s) / r_t)
    d0 = r_o0 * math.sin(h - a_a)
    a1 = min(a_v - da, h - math.asin((d0 + w + s) / r_o0))
    return [a_v] + [a1 - (lv - 1) * da for lv in range(1, levels)], da


def closed_form(name, pad, w, bw, s, r_t, a_v, a_a, r_o0, h, k):
    """Print the fan positions and the closed-form clearances of G6 for k series groups."""
    levels = k // 2 + 1
    a, da = fan_angles(r_t, a_v, a_a, r_o0, h, pad, w, bw, s, levels)

    def pt(r, ang):
        return (r * math.cos(ang), r * math.sin(ang))

    via = [pt(r_t, x) for x in a]
    chord = math.dist(via[0], via[1])
    radial_1 = seg_point(pt(r_o0, a[1]), via[1], via[0])
    straight_0 = seg_point(pt(r_o0, a_a), via[0], via[1])
    foot_corner = r_o0 * math.sin(h - a[1]) - r_o0 * math.sin(h - a_a)  # foot to the side line d_0
    sides = 2 * r_t * math.sin(a[-1])  # innermost CCW via to innermost CW via
    print(
        f" {name}: k {k}, r_T {r_t:.4f}, R_o0 {r_o0:.4f}, a_V {math.degrees(a_v):.4f} deg,"
        f" corner A_0 {math.degrees(a_a):.4f} deg, c_f {fan_pitch(pad, w, bw, s):.4f} mm, da {math.degrees(da):.4f} deg"
    )
    print("   level angles (deg):", [round(math.degrees(x), 4) for x in a])
    print(f"   copper clearances (mm, rule s {s:.4f}):")
    print(f"     via 0 - via 1 pads: {chord - pad:.4f}")
    print(f"     radial stub l=1 - via 0: {radial_1 - w / 2 - pad / 2:.4f}")
    print(f"     straight stub l=0 - via 1: {straight_0 - w / 2 - pad / 2:.4f}")
    print(
        f"     leg at via 0 - via 1: {chord - bw / 2 - pad / 2:.4f}; leg - leg (k even, same side): {chord - bw:.4f};"
        f" leg - straight stub l=0 (other end): {straight_0 - bw / 2 - w / 2:.4f}"
    )
    print(f"     radial stub foot l=1 - side line d_0 ending at A_0, same layer: {foot_corner - w:.4f}")
    print(f"     innermost CCW via - innermost CW via: {sides - pad:.4f}")
    print(f"     fan via - outer arc 0 (r_T - pad/2 - R_o0 - w/2): {r_t - pad / 2 - r_o0 - w / 2:.4f}")
    return min(
        chord - pad,
        radial_1 - w / 2 - pad / 2,
        straight_0 - w / 2 - pad / 2,
        chord - bw / 2 - pad / 2,
        chord - bw,
        straight_0 - bw / 2 - w / 2,
        foot_corner - w,
        sides - pad,
        r_t - pad / 2 - r_o0 - w / 2,
    )


def seg_point(a, b, p):
    """Distance from point p to segment ab."""
    ab, ap = (b[0] - a[0], b[1] - a[1]), (p[0] - a[0], p[1] - a[1])
    u = max(0.0, min(1.0, (ab[0] * ap[0] + ab[1] * ap[1]) / (ab[0] ** 2 + ab[1] ** 2)))
    return math.dist(p, (a[0] + u * ab[0], a[1] + u * ab[1]))


def series_design(base, k, turns=None):
    """Return ``base`` on 2k layers with k series groups of one pair; turns "keep" leaves the request as it is."""
    pairs = tuple(LayerPair(index=i, layer_in=f"L{2 * i + 1}", layer_out=f"L{2 * i + 2}") for i in range(k))
    layers = LayerConfig(pairs=pairs, series_groups=tuple((i,) for i in range(k)))
    coil = dataclasses.replace(base.winding.coil, turns=turns) if turns != "keep" else base.winding.coil
    return dataclasses.replace(
        base,
        stackup=generate_even_stackup(2 * k, 0.0348, 1.6),
        winding=dataclasses.replace(base.winding, layers=layers, coil=coil),
    )


def fan_only(board):
    """Return the fan copper of every coil: each stub with the primitive it joins, legs, ring arcs, ring-side vias."""
    paths = []
    for p in board.paths:
        idx = [i for i, q in enumerate(p.primitives) if q.role is PrimitiveRole.STUB]
        if p.primitives[0].role in (PrimitiveRole.LEG, PrimitiveRole.RING):
            paths.append(p)
        for i in idx:
            j0, j1 = (i, i + 2) if i == 0 else (i - 1, i + 1)
            paths.append(dataclasses.replace(p, id=len(paths) + 10_000, primitives=p.primitives[j0:j1]))
    paths = [dataclasses.replace(p, id=n) for n, p in enumerate(paths)]
    paths = [p for p in paths if p.net.startswith("PHASE_")]  # star/delta links and their vias are not the fan
    vias = tuple(
        v
        for v in board.vias
        if v.role in (ViaRole.TERMINAL, ViaRole.TRANSFER, ViaRole.RING) and v.net.startswith("PHASE_")
    )
    circuit = dataclasses.replace(board.circuit, interconnect_path_ids=())
    return dataclasses.replace(board, paths=tuple(paths), vias=vias, pads=(), circuit=circuit)


def report(label, board, rules):
    """Print the violation count and the smallest clearance per trace and via check kind."""
    rep = run_drc(board, rules)
    mins = {
        x.kind.value: round(x.measured_min_mm, 4)
        for x in rep.summaries
        if x.measured_min_mm is not None and x.kind.value in ("trace_trace", "trace_via", "via_via", "pad_trace")
    }
    print(f"   {label}: violations {rep.violation_count}, smallest clearance {mins}")
    return rep.violation_count


def run(name, base, k, turns):
    """Generate the board with main's generator, unchanged, and report its DRC; return the violation count."""
    stack = gen.generate_spiral(series_design(base, k, turns), load_registry())
    if not isinstance(stack, BoardStack):
        print(f" {name} k {k}: refused {[i.code for i in stack.issues]}")
        return 1
    board = stack.boards[0]
    per_coil = sum(v.role in (ViaRole.TERMINAL, ViaRole.TRANSFER, ViaRole.CENTRE) for v in board.vias) // 12
    print(f" {name} k {k} (main): turns {board.detail.turns_achieved}, vias per coil {per_coil}")
    bad = report("whole board", board, base.drc_rules)
    report("fan copper only", fan_only(board), base.drc_rules)
    return bad


def via_gap(frame, art, closing, bus_width_mm, k, local):
    """Largest distance between main's ring vias (series.ring_vias) and the closed-form fan of this check."""
    main = [v.point for v in ring_vias(frame, art.terminal, closing.start_corner, bus_width_mm, k)]
    r_t = math.hypot(*art.terminal)
    side = [1 if i % 2 == 0 else -1 for i in range(k + 1)]
    mine = [(r_t * math.cos(side[i] * local[i // 2]), r_t * math.sin(side[i] * local[i // 2])) for i in range(k + 1)]
    return max(math.dist(a, b) for a, b in zip(main, mine, strict=True))


if __name__ == "__main__":
    cf11, d08 = default_design(), d08_design()
    failures = 0
    print("G6 series via fan, closed form (revision 2026-10-08, U-E6)")
    for name, design in (("CF-11", cf11), ("D08", d08)):
        c = design.winding.coil
        bw = design.connection.ring_width_mm
        frame = gen.CoilFrame.of(c, design.vias.pad_mm)
        loops, _ = gen.loop_turns(frame)
        closing = gen.max_closing(frame, loops, 1)
        art = sharp_artwork(frame, closing, bw)
        r_t, a_v = math.hypot(*art.terminal), math.atan2(art.terminal[1], art.terminal[0])
        a_a = math.atan2(art.primitives[0].end_point()[1], art.primitives[0].end_point()[0])
        r_o0 = c.r_outer_mm - c.trace_width_mm / 2
        h = frame.half_angle_rad
        for k in (2, 3):
            least = closed_form(
                name, design.vias.pad_mm, c.trace_width_mm, bw, c.clearance_mm, r_t, a_v, a_a, r_o0, h, k
            )
            local, _ = fan_angles(
                r_t, a_v, a_a, r_o0, h, design.vias.pad_mm, c.trace_width_mm, bw, c.clearance_mm, k // 2 + 1
            )
            gap = via_gap(frame, art, closing, bw, k, local)
            ok = least >= c.clearance_mm - 1e-6 and gap <= 1e-9
            failures += not ok
            print(
                f"   smallest closed-form fan clearance {least:.4f} mm, rule s {c.clearance_mm};"
                f" main ring vias vs closed form max diff {gap:.2e} mm:",
                "PASS" if ok else "FAIL",
            )
    print("DRC (embodic.drc.run_drc, rule D-006, whole board and fan copper alone)")
    for name, design, turns in (("CF-11", cf11, "keep"), ("D08", d08, None)):
        for k in (2, 3):
            failures += bool(run(name, design, k, turns))
    print("RESULT", "PASS" if failures == 0 else f"FAIL ({failures} failed checks)")
