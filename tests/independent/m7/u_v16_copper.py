"""U-V16: per-layer copper clearance of every pair, measured from the DXF export without the section 7 exemptions.

usage: PYTHONPATH=src python tests/independent/m7/u_v16_copper.py [--example NAME ...] [--out DIR] [--png]

Geometry: each packaged example goes through ``compute_project`` and ``write_dxf(..., "complete")``. The copper is read
back from the DXF text by the reader below (copper layers ``CU<k>_<layer>_<PH_x|IC>_W<um>``, lines, arcs, circles,
``VIA_PAD`` and ``PAD`` circles), not from ``embodic.drc`` items. A via or pad is a disc on every copper layer of its
board, which is what a through land is.

Designed joints, from the DXF topology alone: two traces of one layer that share an end point within 1e-6 mm (the
consecutive primitives of a path, or path ends that meet), a trace whose end point lies on a land, and two traces whose
ends lie on one land. No other pair is exempt. Every other pair of one layer is measured with the M1 certified kernels
(``m1/brute_clearance.py``): clearance is edge to edge, centreline distance minus both half widths, with round ends.

The rule of a pair follows the interfaces.md section 7 table: trace-trace and pad-trace use ``trace_clearance_mm``;
any pair with a via, and pad-pad, use ``via_clearance_mm``. D-006: a violation is clearance < rule - 1e-6 mm.

Only after the measurement does the script read the product: the layout, to name each DXF entity
(``path:<id>/prim:<k>``, ``via:<id>``, ``pad:<id>``), and ``embodic.drc.items``, to list which close pairs the product
exempts and under which section 7 rule.
"""

import argparse
import json
import math
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m1"))

from brute_clearance import DRC_EPSILON_MM, Verdict, bounding_boxes, clearance_bracket, verdict  # noqa: E402
from records import Arc, Line, Prim, disc, end_point, start_point  # noqa: E402

from embodic.api import compute_project  # noqa: E402
from embodic.drc.items import ItemClass, _junctions, _path_ends, _taps, build_items, exempt_pairs  # noqa: E402
from embodic.geometry.primitives import Arc as ProductArc  # noqa: E402
from embodic.io.dxf_writer import write_dxf  # noqa: E402

REPO = HERE.parents[2]
EXAMPLES = REPO / "resources" / "examples"
JOINT_MM = 1e-6
KEY_DECIMALS = 5
COPPER_LAYER = re.compile(r"^(?:B(?P<board>\d+)_)?CU(?P<index>\d+)_(?P<layer>.+)_(?P<group>PH_[ABC]|IC)_W(?P<um>\d+)$")
LAND_LAYER = re.compile(r"^(?:B(?P<board>\d+)_)?(?P<what>VIA_PAD|PAD)$")


@dataclass(frozen=True, slots=True)
class Copper:
    """One copper shape read from the DXF; ``layer`` None is a land on every layer of its board."""

    board: int
    layer: str | None
    kind: str  # "trace", "via" or "pad"
    group: str  # PH_A, PH_B, PH_C, IC for traces; "" for lands
    prim: Prim


def dxf_entities(text: str) -> list[tuple[str, str, dict[int, str]]]:
    """Return (type, layer, codes) of each entity in the ENTITIES section of an R12 ASCII DXF."""
    lines = text.splitlines()
    pairs = [(int(lines[i].strip()), lines[i + 1].strip()) for i in range(0, len(lines) - 1, 2)]
    start = next(i for i in range(1, len(pairs)) if pairs[i] == (2, "ENTITIES") and pairs[i - 1] == (0, "SECTION"))
    out: list[tuple[str, str, dict[int, str]]] = []
    current: tuple[str, dict[int, str]] | None = None
    for code, value in pairs[start + 1 :]:
        if code == 0:
            if current is not None:
                out.append((current[0], current[1][8], current[1]))
            if value == "ENDSEC":
                return out
            current = (value, {})
        elif current is not None:
            current[1][code] = value
    raise ValueError("DXF has no ENDSEC after ENTITIES")


def read_copper(text: str) -> list[Copper]:
    """Copper traces and lands of a complete DXF export; refuses an entity it cannot model."""
    found: list[Copper] = []
    for kind, layer, c in dxf_entities(text):
        copper, land = COPPER_LAYER.match(layer), LAND_LAYER.match(layer)
        if copper:
            board = int(copper["board"] or 1)
            width = int(copper["um"]) / 1000.0
            name, group = copper["layer"], copper["group"]
            if kind == "LINE":
                prim: Prim = Line(float(c[10]), float(c[20]), float(c[11]), float(c[21]), width)
            elif kind == "ARC":
                a1, a2 = float(c[50]), float(c[51])
                sweep = (a2 - a1) % 360.0
                prim = Arc(float(c[10]), float(c[20]), float(c[40]), math.radians(a1), math.radians(sweep), width)
            elif kind == "CIRCLE":
                prim = Arc(float(c[10]), float(c[20]), float(c[40]), 0.0, 2 * math.pi, width)
            else:
                raise ValueError(f"copper entity {kind} on {layer} is not modelled")
            found.append(Copper(board, name, "trace", group, prim))
        elif land:
            if kind != "CIRCLE":
                raise ValueError(f"land entity {kind} on {layer}: only round lands are modelled")
            what = "via" if land["what"] == "VIA_PAD" else "pad"
            found.append(
                Copper(int(land["board"] or 1), None, what, "", disc(float(c[10]), float(c[20]), 2 * float(c[40])))
            )
    return found


def ends(p: Prim) -> tuple[tuple[float, float], tuple[float, float]]:
    """Both end points of a centreline."""
    return start_point(p), end_point(p)


def _groups(a: Copper, b: Copper) -> str:
    return "/".join(sorted((a.group, b.group)))


def _shared_end_joints(shapes: list[Copper], traces: list[int], pts: dict) -> Iterator[tuple[int, int, str]]:
    """Yield two traces of one layer that share an end point within JOINT_MM."""
    for a_pos, i in enumerate(traces):
        for j in traces[a_pos + 1 :]:
            si, sj = shapes[i], shapes[j]
            if (si.board, si.layer) == (sj.board, sj.layer) and any(
                math.dist(p, q) <= JOINT_MM for p in pts[i] for q in pts[j]
            ):
                yield i, j, f"trace-trace {_groups(si, sj)}"


def _land_joints(shapes: list[Copper], traces: list[int], pts: dict) -> Iterator[tuple[int, int, str]]:
    """Yield a trace end on a land, and two trace ends of one layer on one land."""
    for k, land in enumerate(shapes):
        if land.kind == "trace":
            continue
        centre, radius = (land.prim.x1, land.prim.y1), land.prim.width / 2
        members = [
            i for i in traces if shapes[i].board == land.board and any(math.dist(p, centre) <= radius for p in pts[i])
        ]
        yield from ((i, k, f"trace-{land.kind} {shapes[i].group}") for i in members)
        for x, i in enumerate(members):
            yield from (
                (i, j, f"trace-trace on one land {_groups(shapes[i], shapes[j])}")
                for j in members[x + 1 :]
                if shapes[i].layer == shapes[j].layer
            )


def designed_joints(shapes: list[Copper]) -> tuple[set[frozenset[int]], Counter]:
    """Pairs joined by design (module docstring) and a count of joints by the groups they join."""
    traces = [i for i, s in enumerate(shapes) if s.kind == "trace"]
    pts = {i: ends(shapes[i].prim) for i in traces}
    joints: set[frozenset[int]] = set()
    kinds: Counter = Counter()
    for i, j, kind in [*_shared_end_joints(shapes, traces, pts), *_land_joints(shapes, traces, pts)]:
        if frozenset((i, j)) not in joints:
            joints.add(frozenset((i, j)))
            kinds[kind] += 1
    return joints, kinds


def rule_of(a: Copper, b: Copper, rules: object) -> float:
    """Section 7 table: trace-trace and pad-trace take the trace rule, any via pair and pad-pad the via rule."""
    kinds = {a.kind, b.kind}
    if "via" in kinds or kinds == {"pad"}:
        return rules.via_clearance_mm
    return rules.trace_clearance_mm


def same_layer(a: Copper, b: Copper) -> bool:
    """Whether two shapes share copper on one layer of one board."""
    return a.board == b.board and (a.layer is None or b.layer is None or a.layer == b.layer)


def sweep_pairs(shapes: list[Copper], rules: object, exempt: set[frozenset[int]]) -> tuple[list[dict], int]:
    """Every same-layer pair not exempt whose boxes allow a violation; return non-clean findings and pairs measured."""
    prims = [s.prim for s in shapes]
    boxes = bounding_boxes(prims)
    widths = np.array([p.width for p in prims])
    top = max(rules.trace_clearance_mm, rules.via_clearance_mm)
    findings, measured = [], 0
    for i in range(len(shapes) - 1):
        rest = boxes[i + 1 :]
        gap_x = np.maximum(0.0, np.maximum(rest[:, 0] - boxes[i, 2], boxes[i, 0] - rest[:, 2]))
        gap_y = np.maximum(0.0, np.maximum(rest[:, 1] - boxes[i, 3], boxes[i, 1] - rest[:, 3]))
        need = top + (widths[i] + widths[i + 1 :]) / 2.0
        for j in (int(k) + i + 1 for k in np.flatnonzero(np.hypot(gap_x, gap_y) < need)):
            a, b = shapes[i], shapes[j]
            if not same_layer(a, b) or frozenset((i, j)) in exempt:
                continue
            rule = rule_of(a, b, rules)
            measured += 1
            bracket = clearance_bracket(a.prim, b.prim, threshold=rule - DRC_EPSILON_MM)
            result = verdict(bracket, rule)
            if result is not Verdict.CLEAN:
                exact = clearance_bracket(a.prim, b.prim, tol=1e-9)
                findings.append({"i": i, "j": j, "verdict": result.value, "rule_mm": rule,
                                 "clearance_mm": [exact.lo, exact.hi]})  # fmt: skip
    return findings, measured


def _key_point(p: tuple[float, float]) -> tuple[float, float]:
    return (round(p[0], KEY_DECIMALS) + 0.0, round(p[1], KEY_DECIMALS) + 0.0)


def shape_key(board: int, layer: str | None, prim: Prim) -> tuple:
    """Geometry key that one DXF entity and one product primitive share: board, layer, end points, radius."""
    if isinstance(prim, Arc):
        if abs(abs(prim.sweep) - 2 * math.pi) < 1e-9:
            return (board, layer, "circle", _key_point((prim.cx, prim.cy)), round(prim.r, KEY_DECIMALS))
        return (board, layer, "arc", frozenset(map(_key_point, ends(prim))), round(prim.r, KEY_DECIMALS))
    if (prim.x1, prim.y1) == (prim.x2, prim.y2):
        return (board, layer, "disc", _key_point((prim.x1, prim.y1)), round(prim.width, 4))
    return (board, layer, "line", frozenset(map(_key_point, ends(prim))))


def product_names(layouts: list) -> dict[tuple, str]:
    """Map shape keys to product labels; layer None for lands."""
    names: dict[tuple, str] = {}
    for b, layout in enumerate(layouts, start=1):
        prefix = f"B{b}:" if len(layouts) > 1 else ""
        for path in layout.paths:
            for k, q in enumerate(path.primitives):
                if isinstance(q, ProductArc):
                    prim: Prim = Arc(q.cx_mm, q.cy_mm, q.r_mm, q.start_rad, q.sweep_rad, q.width_mm)
                else:
                    prim = Line(q.x1_mm, q.y1_mm, q.x2_mm, q.y2_mm, q.width_mm)
                key = shape_key(b, path.layer, prim)
                if key in names:
                    raise ValueError(f"two product primitives share one key: {names[key]} and path:{path.id}/prim:{k}")
                names[key] = f"{prefix}path:{path.id}/prim:{k}"
        for v in layout.vias:
            names.setdefault(shape_key(b, None, disc(v.x_mm, v.y_mm, v.pad_mm)), f"{prefix}via:{v.id}")
        for pad in layout.pads:
            names.setdefault(shape_key(b, None, disc(pad.x_mm, pad.y_mm, pad.width_mm)), f"{prefix}pad:{pad.id}")
    return names


def product_exemptions(layout) -> dict[frozenset[str], str]:
    """Label pairs the product DRC exempts, each with the section 7 rule that exempts it."""
    items, first = build_items(layout)
    keys = exempt_pairs(layout, items, first)
    n = len(items)
    via_base = int(np.count_nonzero(items.item_class == ItemClass.TRACE))
    interconnects = frozenset(layout.circuit.interconnect_path_ids)
    tap = {frozenset(p) for p in _taps(layout, items, interconnects, via_base)}
    tee = {frozenset(p) for p in _junctions(layout, items, first, list(_path_ends(layout, items, first)))}
    out: dict[frozenset[str], str] = {}
    traces = np.flatnonzero(items.item_class == ItemClass.TRACE)
    for x, i in enumerate(traces):
        same = traces[x + 1 :][(items.path[traces[x + 1 :]] == items.path[i])]
        for j in same[np.abs(items.slot[same] - items.slot[i]) <= 2]:
            out[frozenset((items.labels[i], items.labels[int(j)]))] = "1"
    for key in keys:
        i, j = int(key // n), int(key % n)
        pair = frozenset((i, j))
        classes = {int(items.item_class[i]), int(items.item_class[j])}
        if pair in tap:
            rule = "2 tap / 2b"
        elif pair in tee:
            rule = "5"
        elif classes == {ItemClass.TRACE}:
            rule = "3"
        elif classes == {ItemClass.PAD, ItemClass.VIA}:
            rule = "4"
        else:
            rule = "2"
        out.setdefault(frozenset((items.labels[i], items.labels[j])), rule)
    return out


def closest_point(a: Prim, b: Prim) -> tuple[float, float]:
    """Midpoint of the closest sampled pair of centreline points (0.01 mm steps), for locating a finding."""

    def sample(p: Prim) -> np.ndarray:
        if isinstance(p, Line):
            n = max(2, int(math.hypot(p.x2 - p.x1, p.y2 - p.y1) / 0.01) + 1)
            t = np.linspace(0.0, 1.0, n)
            return np.column_stack([p.x1 + t * (p.x2 - p.x1), p.y1 + t * (p.y2 - p.y1)])
        n = max(2, int(abs(p.sweep) * p.r / 0.01) + 1)
        t = p.start + np.linspace(0.0, p.sweep, n)
        return np.column_stack([p.cx + p.r * np.cos(t), p.cy + p.r * np.sin(t)])

    pa, pb = sample(a), sample(b)
    best = (math.inf, (0.0, 0.0))
    for chunk in range(0, len(pa), 2000):
        part = pa[chunk : chunk + 2000]
        d = np.hypot(part[:, None, 0] - pb[None, :, 0], part[:, None, 1] - pb[None, :, 1])
        k = int(d.argmin())
        if d.flat[k] < best[0]:
            u, v = divmod(k, len(pb))
            best = (float(d.flat[k]), (float((part[u, 0] + pb[v, 0]) / 2), float((part[u, 1] + pb[v, 1]) / 2)))
    return best[1]


def _premises(outcome, shapes: list[Copper], labels: list[str], summary) -> dict:
    """Return what the measurement assumes about the export, checked against the product layout."""
    layouts, rules = outcome.boards.boards, outcome.design.drc_rules
    widths_um = sorted({round(q.width_mm * 1000, 6) for lay in layouts for p in lay.paths for q in p.primitives})
    return {
        "dxf_summary": {"lines": summary.lines, "arcs": summary.arcs, "circles": summary.circles},
        "shapes": dict(Counter(s.kind for s in shapes)),
        "unnamed_shapes": [x for x in labels if x.startswith("unnamed")],
        "product_widths_um": widths_um,
        "widths_whole_um": all(abs(w - round(w)) < 1e-6 for w in widths_um),
        "vias_through": all(
            (v.layer_from, v.layer_to) == (lay.copper_layers[0], lay.copper_layers[-1])
            for lay in layouts
            for v in lay.vias
        ),
        "pads_every_layer": all(p.layer is None for lay in layouts for p in lay.pads),
        "boards": len(layouts),
        "layers": [list(lay.copper_layers) for lay in layouts],
        "rules": {"trace_clearance_mm": rules.trace_clearance_mm, "via_clearance_mm": rules.via_clearance_mm},
        "product_drc": [{"passed": r.passed, "violations": r.violation_count} for r in outcome.drc],
    }


def _prefix(b: int, layouts: list) -> str:
    return f"B{b}:" if len(layouts) > 1 else ""


def _same_path_roles(rows: list[dict], layouts: list) -> Counter:
    """For close pairs inside one path: the roles between them and whether the closest point lies at that corner."""
    corners: Counter = Counter()
    for r in rows:
        ma = re.match(r"^path:(\d+)/prim:(\d+)$", r["a"])
        mb = re.match(r"^path:(\d+)/prim:(\d+)$", r["b"])
        if len(layouts) > 1 or not (ma and mb and ma[1] == mb[1]):
            continue
        copper = next(p for p in layouts[0].paths if p.id == int(ma[1]))
        lo, hi = sorted((int(ma[2]), int(mb[2])))
        between = copper.primitives[lo + 1 : hi]
        near = all(
            min(math.dist(r["at_mm"], q.start_point()), math.dist(r["at_mm"], q.end_point())) <= q.width_mm
            for q in between
        )
        r["between_roles"] = [q.role.value for q in between]
        r["closest_point_at_corner_piece"] = bool(between) and near
        roles = " | ".join(
            [copper.primitives[lo].role.value, "+".join(r["between_roles"]), copper.primitives[hi].role.value]
        )
        corners[f"{roles} | closest point at the corner piece: {r['closest_point_at_corner_piece']}"] += 1
    return corners


def _agreement(rows: list[dict], outcome, layouts: list) -> dict:
    """Own close pairs the product does not exempt against the pairs the product reports."""
    reported = set()
    for b, report in enumerate(outcome.drc, start=1):
        prefix = _prefix(b, layouts)
        reported |= {frozenset(prefix + o for o in v.objects) for v in report.violations if len(v.objects) == 2}
    own = {frozenset((r["a"], r["b"])) for r in rows if r["product_exempts_by_rule"] is None}
    return {
        "own_not_exempt_by_product": len(own),
        "product_reported_pairs": len(reported),
        "equal": own == reported,
        "own_only": sorted(sorted(p) for p in own - reported)[:20],
        "product_only": sorted(sorted(p) for p in reported - own)[:20],
    }


def _exemption_width(exempt: dict, labels: list[str], shapes: list[Copper], joints: set, rules: object) -> dict:
    """Same-layer pairs the product exempts: those touching, and those that are not designed joints, by rule."""
    index = {name: n for n, name in enumerate(labels)}
    hidden, touching, beyond = [], Counter(), {}
    for pair, rule in sorted(exempt.items(), key=lambda kv: sorted(kv[0])):
        x, y = sorted(pair)
        if x not in index or y not in index or not same_layer(shapes[index[x]], shapes[index[y]]):
            continue
        a, b = shapes[index[x]], shapes[index[y]]
        bracket = clearance_bracket(a.prim, b.prim, tol=1e-9)
        designed = frozenset((index[x], index[y])) in joints
        if bracket.hi <= 0.0:
            touching[f"rule {rule}, designed joint {designed}"] += 1
        if designed:
            continue
        row = beyond.setdefault(rule, {"pairs": 0, "least_clearance_mm": None, "least_pair": None})
        row["pairs"] += 1
        if row["least_clearance_mm"] is None or bracket.lo < row["least_clearance_mm"]:
            row["least_clearance_mm"], row["least_pair"] = bracket.lo, [x, y]
        if bracket.lo < rule_of(a, b, rules) - DRC_EPSILON_MM:
            hidden.append({"a": x, "b": y, "rule": rule, "clearance_mm": [bracket.lo, bracket.hi],
                           "touching": bracket.hi <= 0.0, "at_mm": closest_point(a.prim, b.prim)})  # fmt: skip
    return {
        "product_exempt_pairs_closer_than_rule_not_designed": hidden,
        "product_exempt_pairs_touching": dict(touching),
        "product_exempt_same_layer_pairs_not_designed_joints_by_rule": beyond,
    }


def check_example(path: Path, out_dir: Path | None) -> dict:
    """Measure one example; return the record (findings, joints, exemption comparison, premises)."""
    outcome = compute_project(path)
    layouts = list(outcome.boards.boards)
    rules = outcome.design.drc_rules
    with tempfile.TemporaryDirectory() as tmp:
        dxf_path = Path(tmp) / f"{path.stem}.dxf"
        summary = write_dxf(outcome, dxf_path, "complete", allow_drc_errors=True)
        text = dxf_path.read_text(encoding="ascii")
    if out_dir is not None:
        (out_dir / f"U-V16_{path.name.split('.')[0]}.dxf").write_text(text, encoding="ascii", newline="\n")
    shapes = read_copper(text)
    joints, joint_kinds = designed_joints(shapes)
    findings, measured = sweep_pairs(shapes, rules, joints)

    names = product_names(layouts)
    labels = [names.get(shape_key(s.board, s.layer, s.prim), f"unnamed:{n}") for n, s in enumerate(shapes)]
    exempt = {
        frozenset(_prefix(b, layouts) + x for x in pair): rule
        for b, layout in enumerate(layouts, start=1)
        for pair, rule in product_exemptions(layout).items()
    }
    rows = []
    for f in findings:
        a, b = shapes[f["i"]], shapes[f["j"]]
        rows.append({
            "a": labels[f["i"]], "b": labels[f["j"]], "layer": a.layer or b.layer or "every",
            "groups": [a.group or a.kind, b.group or b.kind], "verdict": f["verdict"], "rule_mm": f["rule_mm"],
            "clearance_mm": f["clearance_mm"], "at_mm": closest_point(a.prim, b.prim),
            "product_exempts_by_rule": exempt.get(frozenset((labels[f["i"]], labels[f["j"]]))),
        })  # fmt: skip
    return {
        "example": path.name.split(".")[0],
        "premises": _premises(outcome, shapes, labels, summary),
        "designed_joints": dict(joint_kinds),
        "pairs_measured": measured,
        "violations": rows,
        "same_path_pairs_by_roles": dict(_same_path_roles(rows, layouts)),
        "agreement_with_product_violations": _agreement(rows, outcome, layouts),
        **_exemption_width(exempt, labels, shapes, joints, rules),
        "_shapes": shapes,
        "_labels": labels,
        "_outcome": outcome,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the sweep on the named examples (default: all five) and print one block per example."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--example", action="append", help="example stem, e.g. spiral_12c10p_d08")
    parser.add_argument("--out", type=Path, help="write U-V16_<example>.dxf and U-V16_copper.json here")
    args = parser.parse_args(argv)
    stems = args.example or sorted(p.name.split(".")[0] for p in EXAMPLES.glob("*.embodic.json"))
    results = []
    for stem in stems:
        r = check_example(EXAMPLES / f"{stem}.embodic.json", args.out)
        public = {k: v for k, v in r.items() if not k.startswith("_")}
        results.append(public)
        print(f"== {stem}")
        print(json.dumps(public["premises"], default=str))
        print("designed joints", json.dumps(public["designed_joints"]))
        print("pairs measured", public["pairs_measured"], "violations", len(public["violations"]))
        print("agreement with the product's reported pairs", json.dumps(public["agreement_with_product_violations"]))
        print("same-path close pairs by roles", json.dumps(public["same_path_pairs_by_roles"]))
        for v in public["violations"][:40]:
            print("  VIOLATION", json.dumps(v, default=str))
        print("product-exempt pairs closer than the rule that are not designed joints",
              len(public["product_exempt_pairs_closer_than_rule_not_designed"]))  # fmt: skip
        for v in public["product_exempt_pairs_closer_than_rule_not_designed"][:40]:
            print("  HIDDEN", json.dumps(v, default=str))
        print("product-exempt pairs touching", json.dumps(public["product_exempt_pairs_touching"]))
        print("product-exempt same-layer pairs that are not designed joints, by rule",
              json.dumps(public["product_exempt_same_layer_pairs_not_designed_joints_by_rule"]))  # fmt: skip
    if args.out is not None:
        (args.out / "U-V16_copper.json").write_text(json.dumps(results, indent=1, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
