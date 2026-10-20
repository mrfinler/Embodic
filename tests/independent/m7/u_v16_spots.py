"""U-V16: the D08 spots of the user's screenshot, and a red-capable check of the copper sweep.

usage: PYTHONPATH=src python tests/independent/m7/u_v16_spots.py [--json FILE]

Spots (product ids from the D08 inventory in records/U-V16/U-V16.md): for each spot, the least clearance between the
two groups on one layer, and the least distance between them when L1 and L2 are drawn on one plane (cross-layer, which
is what an overlaid view shows). Negative means the copper overlaps.

Red-capable check: the copper sweep of u_v16_copper.py runs again with both clearance rules raised by MARGIN_MM. Every
pair the generator placed at the rule must then be reported. The set is compared with ``run_drc`` at the same raised
rules, so both instruments are seen to reach the same boundary pairs.
"""

import argparse
import dataclasses
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from u_v16_copper import EXAMPLES, check_example, closest_point, designed_joints, same_layer, sweep_pairs  # noqa: E402

sys.path.insert(0, str(HERE.parent / "m1"))
from brute_clearance import clearance_bracket  # noqa: E402

from embodic.drc import run_drc  # noqa: E402

MARGIN_MM = 0.01
D08 = "spiral_12c10p_d08"


def coil(*paths: int) -> set[str]:
    """Labels prefix set for whole paths."""
    return {f"path:{p}/" for p in paths}


SPOTS = {
    "1 A2- and A1+ along the shared radial sides": (coil(2, 3), coil(0, 1)),
    "2 A2- and B1- at the top left": (coil(2, 3), coil(4, 5)),
    "3 rings A, B, C over the outer ends and tails of the red and green coils": (
        coil(32, 33, 44, 56) | {"via:36", "via:37", "via:38", "via:39", "via:47", "via:48", "via:57", "via:58"},
        coil(0, 1, 2, 3, 20, 21, 22, 23, 24, 25, 26, 27, 50, 51, 52, 53)
        | {"via:0", "via:2", "via:3", "via:5", "via:30", "via:32", "via:33", "via:35"},
    ),
}


def member(label: str, group: set[str]) -> bool:
    """Whether a label is one of the group's vias or a primitive of one of its paths."""
    return label in group or any(label.startswith(g) for g in group if g.endswith("/"))


def spot_distances(shapes: list, labels: list[str], x: set[str], y: set[str]) -> dict:
    """Least same-layer clearance and least cross-layer (projected) distance between groups x and y, joints skipped."""
    joints, _ = designed_joints(shapes)
    best: dict[str, dict | None] = {}
    for i, li in enumerate(labels):
        if not member(li, x):
            continue
        for j, lj in enumerate(labels):
            if i == j or not member(lj, y) or member(lj, x) or frozenset((i, j)) in joints:
                continue
            a, b = shapes[i], shapes[j]
            slot = f"same layer {a.layer or b.layer or 'lands'}" if same_layer(a, b) else "cross layer (plan view)"
            bracket = clearance_bracket(a.prim, b.prim, tol=1e-7)
            if best.get(slot) is None or bracket.hi < best[slot]["clearance_mm"][1]:
                best[slot] = {"a": li, "b": lj, "layers": [a.layer or "every", b.layer or "every"],
                              "clearance_mm": [bracket.lo, bracket.hi]}  # fmt: skip
    for slot in best.values():
        if slot is not None:
            i, j = labels.index(slot["a"]), labels.index(slot["b"])
            slot["at_mm"] = closest_point(shapes[i].prim, shapes[j].prim)
    return best


def red_check(record: dict) -> dict:
    """Raise both clearance rules by MARGIN_MM; compare own boundary pairs with run_drc's."""
    shapes, labels, outcome = record["_shapes"], record["_labels"], record["_outcome"]
    rules = outcome.design.drc_rules
    raised = dataclasses.replace(
        rules,
        trace_clearance_mm=rules.trace_clearance_mm + MARGIN_MM,
        via_clearance_mm=rules.via_clearance_mm + MARGIN_MM,
    )
    joints, _ = designed_joints(shapes)
    found, measured = sweep_pairs(shapes, raised, joints)
    own = {frozenset((labels[f["i"]], labels[f["j"]])) for f in found}
    layout = outcome.boards.boards[0]
    report = run_drc(layout, raised)
    pair = re.compile(r"^(path|via|pad):")
    product = {
        frozenset(v.objects) for v in report.violations if len(v.objects) == 2 and all(pair.match(o) for o in v.objects)
    }
    return {
        "margin_mm": MARGIN_MM,
        "own_pairs": len(own),
        "product_pairs": len(product),
        "product_violation_count": report.violation_count,
        "own_only": sorted(sorted(p) for p in own - product),
        "product_only": sorted(sorted(p) for p in product - own),
        "own_pairs_measured": measured,
        "examples": sorted(sorted(p) for p in own)[:12],
    }


def _leg_mutant(layout, leg_id: int, width_mm: float, start_shift_mm: float):
    """D08 with one leg widened, and its start moved along the leg by ``start_shift_mm`` (0 keeps the joint)."""
    paths = []
    for path in layout.paths:
        if path.id == leg_id:
            (line,) = path.primitives
            length = math.hypot(line.x2_mm - line.x1_mm, line.y2_mm - line.y1_mm)
            ux, uy = (line.x2_mm - line.x1_mm) / length, (line.y2_mm - line.y1_mm) / length
            line = dataclasses.replace(
                line, width_mm=width_mm, x1_mm=line.x1_mm + ux * start_shift_mm, y1_mm=line.y1_mm + uy * start_shift_mm
            )
            path = dataclasses.replace(path, primitives=(line,))
        paths.append(path)
    return dataclasses.replace(layout, paths=tuple(paths))


def rule5_mutant(record: dict) -> dict:
    """Widen leg 25 (L2, on the end of coil path 1) to 0.8 mm and ask whether run_drc sees path 1's turn prim 9.

    Control: the same leg with its start moved 0.001 mm along the leg, off the coil end, so rule 5 cannot apply
    (the leg end stays on via 2, rule 2). Own clearance from the M1 kernel on the mutated primitives.
    """
    sys.path.insert(0, str(HERE.parent / "m1"))
    from records import Arc, Line

    def own(q):
        if hasattr(q, "r_mm"):
            return Arc(q.cx_mm, q.cy_mm, q.r_mm, q.start_rad, q.sweep_rad, q.width_mm)
        return Line(q.x1_mm, q.y1_mm, q.x2_mm, q.y2_mm, q.width_mm)

    outcome = record["_outcome"]
    layout, rules = outcome.boards.boards[0], outcome.design.drc_rules
    rows = {}
    for name, shift in (("joint kept (rule 5 applies)", 0.0), ("control: start 0.001 mm off the coil end", 0.001)):
        mutant = _leg_mutant(layout, 25, 0.8, shift)
        leg = next(p for p in mutant.paths if p.id == 25).primitives[0]
        turn = next(p for p in mutant.paths if p.id == 1).primitives[9]
        bracket = clearance_bracket(own(leg), own(turn), tol=1e-9)
        report = run_drc(mutant, rules, use_symmetry=False)
        hits = [
            {"objects": list(v.objects), "clearance_mm": v.clearance_mm}
            for v in report.violations
            if "path:25/prim:0" in v.objects
        ]
        rows[name] = {
            "own_clearance_leg25_vs_path1_prim9_mm": [bracket.lo, bracket.hi],
            "run_drc_passed": report.passed,
            "run_drc_violation_count": report.violation_count,
            "run_drc_violations_with_leg25": hits,
            "run_drc_reports_leg25_vs_path1_prim9": any("path:1/prim:9" in h["objects"] for h in hits),
        }
    return rows


def main(argv: list[str] | None = None) -> int:
    """Print the spot table and the red-capable check for D08."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    record = check_example(EXAMPLES / f"{D08}.embodic.json", None)
    shapes, labels = record["_shapes"], record["_labels"]
    out = {"spots": {}, "red_check": red_check(record), "rule5_mutant": rule5_mutant(record)}
    for name, row in out["rule5_mutant"].items():
        print("rule 5 mutant,", name, json.dumps(row))
    for name, (x, y) in SPOTS.items():
        out["spots"][name] = spot_distances(shapes, labels, x, y)
        print(name)
        for slot, row in out["spots"][name].items():
            print(f"  {slot}: {json.dumps(row)}")
    rc = out["red_check"]
    print("red check", json.dumps({k: v for k, v in rc.items() if k != "examples"}))
    print("  sample own boundary pairs", rc["examples"])
    if args.json:
        args.json.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
