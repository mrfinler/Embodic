# Prepared by: Agent 2 — Motor Design Expert — model: claude-opus-5-5
# Series-pair via fan of spiral_generator_spec.md G6 (revision 2026-10-08, U-E6): closed form, then a DRC proof.
# not product code. It builds the G6 fan on main's generator by replacing generate.series_coil in this process only
# (no file of src/ changes), runs embodic.drc.run_drc on the whole board and on the fan copper alone, and prints the
# smallest clearance per check kind. Rule D-006, no exemption beyond interfaces.md section 7.
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
from embodic.generators.spiral.artwork import coil_artwork, sharp_artwork  # noqa: E402
from embodic.generators.spiral.series import GroupCopper, SeriesCoil  # noqa: E402
from embodic.generators.spiral.series import _group as main_group  # noqa: E402
from embodic.generators.spiral.turns import group_closing  # noqa: E402
from embodic.geometry.layout import BoardStack, ViaRole  # noqa: E402
from embodic.geometry.primitives import Arc, Line, PrimitiveRole  # noqa: E402
from embodic.geometry.transforms import mirror, reverse_path  # noqa: E402
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


def _radial(a_rad, r_from, r_to, width_mm):
    return Line(
        x1_mm=r_from * math.cos(a_rad),
        y1_mm=r_from * math.sin(a_rad),
        x2_mm=r_to * math.cos(a_rad),
        y2_mm=r_to * math.sin(a_rad),
        width_mm=width_mm,
        role=PrimitiveRole.STUB,
    )


def _trim_start(arc, a_rad):
    end = arc.start_rad + arc.sweep_rad
    return dataclasses.replace(arc, start_rad=a_rad, sweep_rad=end - a_rad)


def _trim_end(arc, a_rad):
    return dataclasses.replace(arc, sweep_rad=a_rad - arc.start_rad)


def fan_series_coil(frame, closing, bus_width_mm, groups, filleted):
    """G6 revision 2026-10-08 (U-E6): level 0 keeps the U-E3 straight stubs, level l >= 1 enters on a radial stub."""
    terminal = sharp_artwork(frame, closing, bus_width_mm).terminal
    r_t, a_v = math.hypot(*terminal), math.atan2(terminal[1], terminal[0])
    w, s, pad = frame.trace_width_mm, frame.clearance_mm, frame.via_pad_mm
    arc0 = sharp_artwork(frame, closing, bus_width_mm).primitives[1]
    a_a = arc0.start_rad
    a, _ = fan_angles(r_t, a_v, a_a, arc0.r_mm, frame.half_angle_rad, pad, w, bus_width_mm, s, groups // 2 + 1)
    side = [1 if i % 2 == 0 else -1 for i in range(groups + 1)]
    level = [i // 2 for i in range(groups + 1)]
    rings = tuple(
        (r_t * math.cos(side[i] * a[level[i]]), r_t * math.sin(side[i] * a[level[i]])) for i in range(groups + 1)
    )
    built = []
    for g in range(groups):
        own = group_closing(frame, closing, g)
        art = coil_artwork(frame, own, bus_width_mm, filleted) if filleted else sharp_artwork(frame, own, bus_width_mm)
        if art is None:
            return None
        old = main_group(art, g, rings[g], rings[g + 1], w)
        body = art.primitives[1:]
        arc0 = body[0]
        assert isinstance(arc0, Arc) and arc0.role is PrimitiveRole.END_TURN
        if level[g] == 0:
            x = old.x
        else:
            a_in = side[g] * a[level[g]]
            x = (_radial(a_in, r_t, arc0.r_mm, w), _trim_start(arc0, a_in), *body[1:])
        if level[g + 1] == 0:
            y = old.y
        else:
            a_out = side[g + 1] * a[level[g + 1]]
            core = reverse_path(mirror(body, 0.0))
            y = (*core[:-1], _trim_end(core[-1], a_out), _radial(a_out, arc0.r_mm, r_t, w))
        built.append(GroupCopper(x=x, y=y, centre_via=art.centre_via))
    return SeriesCoil(groups=tuple(built), ring_vias=rings)


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
    """Return the fan copper of every coil: each stub with the primitive it joins, legs, ring arcs, and ring-side vias."""
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


def run(name, base, k, turns, use_fan):
    """Generate the board with main's fan or the U-E6 fan and report its DRC; return the violation count."""
    gen.series_coil = fan_series_coil if use_fan else main_series_coil
    gen._series_fails_drc = lambda design, layout: False
    stack = gen.generate_spiral(series_design(base, k, turns), load_registry())
    if not isinstance(stack, BoardStack):
        print(f" {name} k {k}: refused {[i.code for i in stack.issues]}")
        return None
    board = stack.boards[0]
    print(
        f" {name} k {k} ({'G6 U-E6 fan' if use_fan else 'main fan'}): turns {board.detail.turns_achieved},"
        f" vias per coil {sum(v.role in (ViaRole.TERMINAL, ViaRole.TRANSFER, ViaRole.CENTRE) for v in board.vias) // 12}"
    )
    bad = report("whole board", board, base.drc_rules)
    report("fan copper only", fan_only(board), base.drc_rules)
    return bad


main_series_coil = gen.series_coil

if __name__ == "__main__":
    cf11, d08 = default_design(), d08_design()
    print("G6 series via fan, closed form (revision 2026-10-08, U-E6)")
    for name, design in (("CF-11", cf11), ("D08", d08)):
        c = design.winding.coil
        frame = gen.CoilFrame.of(c, design.vias.pad_mm)
        loops, _ = gen.loop_turns(frame)
        closing = gen.max_closing(frame, loops, 1)
        art = sharp_artwork(frame, closing, design.connection.ring_width_mm)
        r_t, a_v = math.hypot(*art.terminal), math.atan2(art.terminal[1], art.terminal[0])
        a_a = math.atan2(art.primitives[0].end_point()[1], art.primitives[0].end_point()[0])
        r_o0 = c.r_outer_mm - c.trace_width_mm / 2
        for k in (2, 3):
            least = closed_form(
                name,
                design.vias.pad_mm,
                c.trace_width_mm,
                design.connection.ring_width_mm,
                c.clearance_mm,
                r_t,
                a_v,
                a_a,
                r_o0,
                frame.half_angle_rad,
                k,
            )
            print(
                f"   smallest closed-form fan clearance {least:.4f} mm, rule s {c.clearance_mm}:",
                "PASS" if least >= c.clearance_mm - 1e-6 else "FAIL",
            )
    print("DRC (embodic.drc.run_drc, rule D-006, whole board and fan copper alone)")
    failures = 0
    for name, design, turns in (("CF-11", cf11, "keep"), ("D08", d08, None)):
        for k in (2, 3):
            run(name, design, k, turns, use_fan=False)
            failures += bool(run(name, design, k, turns, use_fan=True))
    print("RESULT", "PASS" if failures == 0 else f"FAIL ({failures} boards with violations)")
