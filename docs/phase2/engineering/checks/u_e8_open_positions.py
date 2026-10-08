"""U-E8 measurements for open_positions_m3.md: overlap-wave interconnect copper and serpentine strand-via gaps.

Run from the worktree root:
    PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase2/engineering/checks/u_e8_open_positions.py

Reuses the GR-22 and GR-20 pipelines (same design map, registry and generators as the golden tests), so a number here
is the number those tests see. Resistances of single interconnect paths are recomputed by EQ-10 (R = rho L / (w t))
with Xcoil's operating resistivity and copper thickness from the golden case.
"""

import dataclasses
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "tests" / "golden")]

from m3_serpentine.design_map import design_from_xcoil as serpentine_design  # noqa: E402
from m3_serpentine.test_gr20_drc import AREA, _raw  # noqa: E402
from m3_wave.test_gr22_results import OVERLAP_STAR, _layout_case, _run  # noqa: E402

from embodic.drc import DrcCheckKind, run_drc  # noqa: E402
from embodic.generators import build_layout  # noqa: E402
from embodic.geometry.layout import ViaRole  # noqa: E402
from embodic.geometry.primitives import Arc, Line, primitive_length_mm  # noqa: E402
from embodic.results import load_registry  # noqa: E402


def _ends(prim):
    if isinstance(prim, Line):
        return (prim.x1_mm, prim.y1_mm), (prim.x2_mm, prim.y2_mm)
    a, b = prim.start_rad, prim.start_rad + prim.sweep_rad
    return ((prim.cx_mm + prim.r_mm * math.cos(a), prim.cy_mm + prim.r_mm * math.sin(a)),
            (prim.cx_mm + prim.r_mm * math.cos(b), prim.cy_mm + prim.r_mm * math.sin(b)))  # fmt: skip


def _nearest_via(vias, xy):
    v = min(vias, key=lambda v: math.hypot(v.x_mm - xy[0], v.y_mm - xy[1]))
    return v, math.hypot(v.x_mm - xy[0], v.y_mm - xy[1])


def _eq10_ohm(path, rho_ohm_m, t_mm):
    """EQ-10 per primitive, R = rho L / (w t), lengths in mm."""
    return math.fsum(rho_ohm_m * primitive_length_mm(q) / (q.width_mm * t_mm) * 1e3 for q in path.primitives)


def wave(case_id: str) -> None:
    """Interconnect paths of an overlap-wave board by role, their EQ-10 resistance and the P_ic against Xcoil."""
    xcoil, result, stack = _run(case_id)
    board = stack.boards[0]
    raw = _layout_case(case_id).calls[0].output
    thickness = {L["copperT"] for L in raw["layers"]}
    assert len(thickness) == 1, thickness
    t_mm = thickness.pop()
    rho, i_line, conn = xcoil["rho"], raw["params"]["currentRms"], raw["params"]["connection"]
    paths = {p.id: p for p in board.paths}
    terminals = [v for v in board.vias if v.role is ViaRole.TERMINAL]
    print(f"\n== wave {case_id} ({conn}, I_line {i_line} A rms, rho {rho:.6e} ohm*m, t {t_mm} mm)")
    sums = {"LineLead": 0.0, "PhaseLink": 0.0}
    touched = set()
    for role in board.circuit.interconnect_roles:
        path = paths[role.path_id]
        start, end = _ends(path.primitives[0])[0], _ends(path.primitives[-1])[1]
        vs, ds = _nearest_via(board.vias, start)
        ve, de = _nearest_via(board.vias, end)
        for v, d in ((vs, ds), (ve, de)):
            if d < 1e-9:
                touched.add(v.id)
        r_ohm = _eq10_ohm(path, rho, t_mm)
        name = type(role).__name__
        if name in sums:
            sums[name] += r_ohm
        length = math.fsum(primitive_length_mm(q) for q in path.primitives)
        print(f"  {name:11s} path {path.id:3d} net {path.net:3s} layer {path.layer:5s} len {length:.4f} mm "
              f"w {path.primitives[0].width_mm} mm R(EQ-10) {r_ohm:.6e} ohm | start: via {vs.id} {vs.role} {vs.net} "
              f"at {ds:.1e} mm, r={math.hypot(*start):.4f} | end: r={math.hypot(*end):.4f}")  # fmt: skip
    untouched = [v for v in terminals if v.id not in touched]
    print(f"  terminal vias {len(terminals)}; with no interconnect path ending on them: "
          f"{[(v.id, v.net, round(math.hypot(v.x_mm, v.y_mm), 4)) for v in untouched]}")  # fmt: skip
    p_e, p_x = result.loss_interconnect_w.value, xcoil["pInterconnect"]
    print(f"  P_ic embodic {p_e:.6e} W, Xcoil {p_x:.6e} W, embodic/Xcoil - 1 = "
          f"{(p_e / p_x - 1) if p_x else math.inf:+.4f}")  # fmt: skip
    print(f"  I_line^2 * sum R(PhaseLink) = {i_line**2 * sums['PhaseLink']:.6e} W; P_e - P_x = {p_e - p_x:.6e} W")
    if conn == "delta":
        i_ph = i_line / math.sqrt(3.0)
        print(f"  I_line^2 * sum R(LineLead) = {i_line**2 * sums['LineLead']:.6e} W (lead carries I_line)")
        print(f"  I_ph^2   * sum R(LineLead) = {i_ph**2 * sums['LineLead']:.6e} W (lead carries I_ph)")


def _foot(prim, xy):
    """(distance from xy to prim, distance along prim to the foot point)."""
    x, y = xy
    if isinstance(prim, Line):
        dx, dy = prim.x2_mm - prim.x1_mm, prim.y2_mm - prim.y1_mm
        n = math.hypot(dx, dy)
        t = min(1.0, max(0.0, ((x - prim.x1_mm) * dx + (y - prim.y1_mm) * dy) / n**2)) if n else 0.0
        return math.hypot(x - prim.x1_mm - t * dx, y - prim.y1_mm - t * dy), t * n
    assert isinstance(prim, Arc)
    off = (
        math.copysign(1.0, prim.sweep_rad) * (math.atan2(y - prim.cy_mm, x - prim.cx_mm) - prim.start_rad)
    ) % math.tau
    off = min(off, abs(prim.sweep_rad))
    a = prim.start_rad + math.copysign(off, prim.sweep_rad)
    return math.hypot(
        x - prim.cx_mm - prim.r_mm * math.cos(a), y - prim.cy_mm - prim.r_mm * math.sin(a)
    ), prim.r_mm * off


def serpentine(case_id: str) -> None:
    """Every DRC violation of a serpentine case, with the along-path position of each strand-via pair."""
    raw = _raw(AREA[case_id])
    p = raw["params"]
    design = serpentine_design(p, raw["rMinAll"], raw["rMaxAll"])
    stack = build_layout(design, load_registry())
    skip_len = p["viaPad"] + p["strands"] * (p["traceWidth"] + p["clearance"]) + 1.0
    print(f"\n== serpentine {case_id} (strands {p['strands']}, w {p['traceWidth']}, s {p['clearance']}, "
          f"viaPad {p['viaPad']}; Xcoil drcPadVsLayer skipLen {skip_len:.3f} mm)")  # fmt: skip
    for k, board in enumerate(stack.boards):
        rep = run_drc(board, design.drc_rules)
        paths = {q.id: q for q in board.paths}
        vias = {v.id: v for v in board.vias}
        print(f"  board {k}: {rep.violation_count} violations")
        for v in rep.violations:
            ids = dict(o.split(":", 1) for o in (s.split("/")[0] for s in v.objects))
            line = f"    {v.kind.value:11s} {v.layer} measured {v.measured_mm:+.4f} req {v.required_mm:.3f} {v.objects}"
            if v.kind is DrcCheckKind.TRACE_VIA and "path" in ids and "via" in ids:
                path, via = paths[int(ids["path"])], vias[int(ids["via"])]
                lengths = [primitive_length_mm(q) for q in path.primitives]
                feet = [_foot(q, (via.x_mm, via.y_mm)) for q in path.primitives]
                i = min(range(len(feet)), key=lambda j: feet[j][0])
                s = math.fsum(lengths[:i]) + feet[i][1]
                total = math.fsum(lengths)
                line += (f" | path net {path.net} element {path.element}, via {via.role} net {via.net}, same net "
                         f"{path.net == via.net}, along path from start {s:.3f} / to end {total - s:.3f} of {total:.3f} mm,"
                         f" within skipLen of an end {min(s, total - s) < skip_len}")  # fmt: skip
            elif v.kind is DrcCheckKind.TRACE_TRACE:
                nets = [paths[int(o.split("/")[0].split(":")[1])].net for o in v.objects if o.startswith("path:")]
                line += f" | nets {nets}"
            print(line)


def _moved(board, offsets):
    """Board with each via id in `offsets` moved radially to (strand end radius + offset)."""
    vias = []
    for v in board.vias:
        if v.id in offsets:
            r_end, d = offsets[v.id]
            k = (r_end + d) / math.hypot(v.x_mm, v.y_mm)
            v = dataclasses.replace(v, x_mm=v.x_mm * k, y_mm=v.y_mm * k)
        vias.append(v)
    return dataclasses.replace(board, vias=tuple(vias))


def via_shift(case_id: str) -> None:
    """Radial T-via placement against the strand ends: the current offset, on the bus centreline, and pad/2."""
    raw = _raw(AREA[case_id])
    p = raw["params"]
    design = serpentine_design(p, raw["rMinAll"], raw["rMaxAll"])
    board = build_layout(design, load_registry()).boards[0]
    rep = run_drc(board, design.drc_rules)
    paths = {q.id: q for q in board.paths}
    vias = {v.id: v for v in board.vias}
    current = {}
    for v in rep.violations:
        if v.kind is not DrcCheckKind.TRACE_VIA:
            continue
        ids = dict(o.split(":", 1) for o in (s.split("/")[0] for s in v.objects))
        path, via = paths[int(ids["path"])], vias[int(ids["via"])]
        ends = [_ends(path.primitives[0])[0], _ends(path.primitives[-1])[1]]
        end = min(ends, key=lambda e: math.hypot(e[0] - via.x_mm, e[1] - via.y_mm))
        r_end = math.hypot(*end)
        current[via.id] = (r_end, math.hypot(via.x_mm, via.y_mm) - r_end)
        gap = math.hypot(end[0] - via.x_mm, end[1] - via.y_mm)
        print(f"  {case_id} via {via.id}: radial offset from strand end {current[via.id][1]:+.4f} mm, "
              f"via centre to strand end {gap:.4f} mm, pad/2 {via.pad_mm / 2:.4f} mm")  # fmt: skip
    half = {vid: abs(v.pad_mm) / 2 for vid, v in vias.items()}
    for label, offsets in (
        ("as built", current),
        ("on bus centreline (offset 0)", {vid: (r, 0.0) for vid, (r, _) in current.items()}),
        ("offset pad/2 away", {vid: (r, math.copysign(half[vid], d)) for vid, (r, d) in current.items()}),
    ):
        moved = run_drc(_moved(board, offsets), design.drc_rules)
        kinds = {}
        for v in moved.violations:
            kinds.setdefault(v.kind.value, []).append(v.measured_mm)
        print(f"  {case_id} board 0, T vias {label}: {moved.violation_count} violations "
              f"{ {k: (len(m), round(min(m), 4)) for k, m in kinds.items()} }")  # fmt: skip


def main() -> None:
    """Print every measurement open_positions_m3.md quotes."""
    wave(OVERLAP_STAR)
    wave(OVERLAP_STAR + "-delta")
    serpentine("layout-seeded-03")
    serpentine("layout-strands-3-turns-2")
    print()
    via_shift("layout-seeded-03")
    via_shift("layout-strands-3-turns-2")
    strands3_without_interconnect()


def strands3_without_interconnect() -> None:
    """strands-3 with `interconnect: false`, so no stub starts on a T via and moving the via tests only the strands."""
    case_id = "layout-strands-3-turns-2"
    raw = _raw(AREA[case_id])
    p = {**raw["params"], "interconnect": False}
    design = serpentine_design(p, raw["rMinAll"], raw["rMaxAll"])
    board = build_layout(design, load_registry()).boards[0]
    rep = run_drc(board, design.drc_rules)
    t_vias = {v.id for v in board.vias if v.role is ViaRole.TERMINAL}
    paths = {q.id: q for q in board.paths}
    current = {}
    for v in rep.violations:
        ids = dict(o.split(":", 1) for o in (s.split("/")[0] for s in v.objects))
        if v.kind is DrcCheckKind.TRACE_VIA and int(ids["via"]) in t_vias:
            via = next(x for x in board.vias if x.id == int(ids["via"]))
            path = paths[int(ids["path"])]
            ends = [_ends(path.primitives[0])[0], _ends(path.primitives[-1])[1]]
            end = min(ends, key=lambda e: math.hypot(e[0] - via.x_mm, e[1] - via.y_mm))
            current[via.id] = (math.hypot(*end), math.hypot(via.x_mm, via.y_mm) - math.hypot(*end))
    print(f"  {case_id} interconnect off, as built: {rep.violation_count} violations "
          f"{sorted({(v.kind.value, round(v.measured_mm, 4)) for v in rep.violations})}")  # fmt: skip
    for label, offsets, pad in (
        ("offset 0 (bus centreline)", {k: (r, 0.0) for k, (r, _) in current.items()}, None),
        ("offset 0.299 mm (inside pad/2)", {k: (r, 0.299) for k, (r, _) in current.items()}, None),
        ("as built, T via pad 0.418 mm", current, 0.418),
        ("as built, T via pad 0.420 mm", current, 0.420),
    ):
        moved = _moved(board, offsets)
        if pad is not None:
            moved = dataclasses.replace(moved, vias=tuple(
                dataclasses.replace(v, pad_mm=pad) if v.id in current else v for v in moved.vias))  # fmt: skip
        r2 = run_drc(moved, design.drc_rules)
        print(f"  {case_id} interconnect off, {label}: {r2.violation_count} violations "
              f"{sorted({(v.kind.value, round(v.measured_mm, 4)) for v in r2.violations})}")  # fmt: skip


if __name__ == "__main__":
    main()
