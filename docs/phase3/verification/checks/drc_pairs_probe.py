"""DEF-UV10-01: the DRC pairs of one example near the broad-phase cutoff, and the items whose piece count is a tie.

    python -I docs/phase3/verification/checks/drc_pairs_probe.py --out <file.json>

Run it with the Python of the environment under test. It computes one packaged example (default wave_16p_example)
through `compute_project` and replays the pair loop of `run_drc` on that layout with the engine's own functions
(`_pieces`, `candidate_pairs`, `_check`), so it reads the floats the product computes on this machine.

Per item pair, over all piece pairs p, q of the two items: `slack_mm` is the least of
|mid_p - mid_q| - (span_p + span_q + rule_mm + 1e-9), the value the `near` test of `candidate_pairs` compares with 0
(kept when <= 0); `bound_mm` is the least of |mid_p - mid_q| - span_p - span_q, a lower bound of the clearance;
`clearance_mm` is the narrow-phase value. An exhaustive pass measures every pair of each layer group and reports the
least clearance of the pairs the broad phase leaves out. `split_edge` lists the items whose piece count
ceil(length / PIECE_MM) sits within 1e-12 of an integer, and for each one the pairs that the other rounding adds to or
removes from the check (its row is moved across the integer by 1e-13 relative inside `_pieces` only).

With `--against` (default: reference/drc_pairs_linux_0.0.6.json.gz beside this folder, when it names the same embodic
source and example), it names every pair whose verdict, presence or piece count differs from that file, and every
split-edge item whose piece count differs. Exit 0 when the replay reproduces `pairs_checked` and no left-out pair
violates its rule, 1 otherwise.
"""

import argparse
import gzip
import json
import os
import platform
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

import numpy as np

import embodic
from embodic.api import compute_project
from embodic.drc import engine
from embodic.drc.items import EVERY_LAYER, build_items, exempt_pairs
from embodic.drc.report import DRC_EPSILON_MM
from embodic.drc.symmetry import rotation_maps
from embodic.paths import resource_root
from embodic.results.registry import package_source_sha256

NEAR_MM = 0.05
TIE = 1e-12
DEFAULT_AGAINST = Path(__file__).parents[1] / "reference" / "drc_pairs_linux_0.0.6.json.gz"


def read_json(path: Path) -> dict:
    """Read a probe record, gzip-compressed when the name ends in .gz."""
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def cpu_features() -> list[str]:
    """NumPy's enabled CPU features, which pick the SIMD kernels."""
    try:
        from numpy._core._multiarray_umath import __cpu_features__
    except ImportError:
        return []
    return sorted(name for name, on in __cpu_features__.items() if on)


def piece_ratio(items) -> np.ndarray:
    """Return the value that `_pieces` rounds up to the piece count of each item."""
    rows, arc = items.rows, items.is_arc
    sweep_rad = np.abs(rows[:, 4])
    dx_mm, dy_mm = rows[:, 2] - rows[:, 0], rows[:, 3] - rows[:, 1]
    length_mm = np.where(arc, rows[:, 2] * sweep_rad, np.sqrt(dx_mm * dx_mm + dy_mm * dy_mm))
    return np.maximum(length_mm / engine.PIECE_MM, np.where(arc, sweep_rad / engine._ARC_PIECE_RAD, 0.0))


def piece_measures(items, sel, rule_mm, a, b):
    """Per item pair (a[i], b[i]): least slack, least bound, whether the engine keeps it, and the piece counts."""
    mid, reach_mm, owner = engine._pieces(items, sel)
    span_mm = reach_mm + items.half_width_mm[owner]
    cell_mm = 2 * float(span_mm.max()) + rule_mm + 1e-9
    cells = np.floor(mid / cell_mm)
    first = np.searchsorted(owner, np.arange(len(items)), side="left")
    count = np.searchsorted(owner, np.arange(len(items)), side="right") - first
    na, nb = count[a], count[b]
    per_pair = na * nb
    pair_of = np.repeat(np.arange(len(a)), per_pair)
    k = np.arange(int(per_pair.sum())) - np.repeat(np.cumsum(per_pair) - per_pair, per_pair)
    pa = first[a][pair_of] + k // nb[pair_of]
    pb = first[b][pair_of] + k % nb[pair_of]
    gap = mid[pa] - mid[pb]
    lhs = np.sqrt((gap * gap).sum(axis=1))
    rhs = span_mm[pa] + span_mm[pb] + rule_mm + 1e-9
    adjacent = (np.abs(cells[pa] - cells[pb]) <= 1).all(axis=1)
    slack, bound = np.full(len(a), np.inf), np.full(len(a), np.inf)
    kept = np.zeros(len(a), dtype=bool)
    np.minimum.at(slack, pair_of, lhs - rhs)
    np.minimum.at(bound, pair_of, lhs - span_mm[pa] - span_mm[pb])
    np.logical_or.at(kept, pair_of, (lhs <= rhs) & adjacent)
    group = {"items": len(sel), "pieces": len(owner), "cell_mm": cell_mm, "cell_mm_hex": cell_mm.hex()}
    return slack, bound, kept, na, nb, group


def filtered(items, a, b, drop_every, maps):
    """Apply the pair filter of run_drc between candidate_pairs and _check."""
    if drop_every:
        mixed = (items.layer[a] != EVERY_LAYER) | (items.layer[b] != EVERY_LAYER)
        a, b = a[mixed], b[mixed]
    if maps is not None:
        redundant = maps.periodic[a] & maps.periodic[b] & ~maps.canonical[a] & ~maps.canonical[b]
        a, b = a[~redundant], b[~redundant]
    return a, b


def every_pair(items, layout, sel, drop_every, maps, exempt, layer):
    """Every pair (a < b) of one layer group under the run_drc filter, measured in chunks."""
    i, j = np.triu_indices(len(sel), k=1)
    a, b = filtered(items, sel[i], sel[j], drop_every, maps)
    step = 1 << 18
    return [
        engine._check(items, layout, a[s : s + step], b[s : s + step], exempt, layer) for s in range(0, len(a), step)
    ]


def trace_pairs_checked(layout, rules, items, flip: int | None, target: float) -> tuple[int, int, set]:
    """Run run_drc with one item's row moved to piece ratio `target` inside _pieces; return count, violations, pairs."""
    original_pieces, original_check = engine._pieces, engine._check
    seen: set[tuple[str, str, float]] = set()

    def pieces(items_, sel):
        if flip is None or flip not in sel:
            return original_pieces(items_, sel)
        rows = items_.rows.copy()
        scale = target / float(piece_ratio(items_)[flip])
        if items_.is_arc[flip]:
            rows[flip, 4] *= scale
        else:
            rows[flip, 2:4] = rows[flip, 0:2] + (rows[flip, 2:4] - rows[flip, 0:2]) * scale
        return original_pieces(replace(items_, rows=rows), sel)

    def check(items_, layout_, a, b, exempt, layer):
        m = original_check(items_, layout_, a, b, exempt, layer)
        trace = m.kind == engine.PAIR_KINDS.index(engine.DrcCheckKind.TRACE_TRACE)
        seen.update(
            (*sorted((items.labels[x], items.labels[y])), float(c))
            for x, y, c in zip(m.a[trace].tolist(), m.b[trace].tolist(), m.clearance_mm[trace].tolist(), strict=True)
        )
        return m

    engine._pieces, engine._check = pieces, check
    try:
        report = engine.run_drc(layout, rules)
    finally:
        engine._pieces, engine._check = original_pieces, original_check
    count = next(s.pairs_checked for s in report.summaries if s.kind is engine.DrcCheckKind.TRACE_TRACE)
    return count, report.violation_count, seen


def split_edge(layout, rules, items) -> list[dict]:
    """Items whose piece count is a rounding tie, with the trace_trace pairs the other rounding adds or removes."""
    ratio = piece_ratio(items)
    nearest = np.round(ratio)
    ties = np.flatnonzero((np.abs(ratio - nearest) < TIE) & (ratio > 0.5) & (ratio != nearest))
    _, _, base = trace_pairs_checked(layout, rules, items, None, 0.0)
    out = []
    for i in ties.tolist():
        other = nearest[i] - 1e-13 * nearest[i] if ratio[i] > nearest[i] else nearest[i] + 1e-13 * nearest[i]
        count, violations, seen = trace_pairs_checked(layout, rules, items, i, float(other))
        out.append(
            {
                "item": items.labels[i],
                "ratio": float(ratio[i]),
                "ratio_hex": float(ratio[i]).hex(),
                "pieces": int(np.ceil(ratio[i])),
                "other_rounding": {
                    "trace_trace_pairs_checked": count,
                    "violations": violations,
                    "added": [list(p) for p in sorted(seen - base)],
                    "removed": [list(p) for p in sorted(base - seen)],
                },
            }
        )
    return out


def probe(example: str) -> dict:
    """Compute the example and replay its DRC pair loop; return the record written to --out."""
    outcome = compute_project(resource_root() / "examples" / f"{example}.embodic.json")
    if isinstance(outcome, tuple) or outcome.boards is None or outcome.drc is None:
        raise SystemExit(f"{example}: compute gave no boards or no DRC report")
    layout, report, rules = outcome.boards.boards[0], outcome.drc[0], outcome.design.drc_rules
    items, first_item = build_items(layout)
    exempt = exempt_pairs(layout, items, first_item)
    maps = rotation_maps(layout, items, first_item, exempt) if report.method.startswith("symmetric") else None
    required_mm = engine._required(rules)
    rule_mm = float(required_mm.max()) + DRC_EPSILON_MM
    kinds = [k.value for k in engine.PAIR_KINDS]

    rows, groups, replay = [], [], Counter()
    left_out = {k: {"pairs": 0, "least_clearance_mm": None, "violations": 0} for k in kinds}
    least_gap_mm = np.inf
    for layer, sel, drop_every in engine._layer_groups(items, layout):
        wide = engine._check(
            items,
            layout,
            *filtered(items, *engine.candidate_pairs(items, sel, rule_mm + NEAR_MM), drop_every, maps),
            exempt,
            layer,
        )
        slack, bound, kept, na, nb, group = piece_measures(items, sel, rule_mm, wide.a, wide.b)
        used = engine._check(
            items,
            layout,
            *filtered(items, *engine.candidate_pairs(items, sel, rule_mm), drop_every, maps),
            exempt,
            layer,
        )
        replay.update(kinds[k] for k in used.kind.tolist())
        used_keys = set(zip(used.a.tolist(), used.b.tolist(), strict=True))
        replayed = {
            key
            for key, keep in zip(zip(wide.a.tolist(), wide.b.tolist(), strict=True), kept.tolist(), strict=True)
            if keep
        }
        group.update(layer=layer, engine_pairs=len(used_keys), replay_matches=replayed == used_keys)
        groups.append(group)
        if len(bound):
            least_gap_mm = min(least_gap_mm, float((wide.clearance_mm - bound).min()))
        for i in range(len(wide.a)):
            a, b = int(wide.a[i]), int(wide.b[i])
            rows.append(
                {
                    "kind": kinds[int(wide.kind[i])],
                    "layer": layer,
                    "objects": sorted((items.labels[a], items.labels[b])),
                    "kept": bool(kept[i]),
                    "slack_mm": float(slack[i]),
                    "slack_hex": float(slack[i]).hex(),
                    "bound_mm": float(bound[i]),
                    "clearance_mm": float(wide.clearance_mm[i]),
                    "pieces": [int(na[i]), int(nb[i])]
                    if items.labels[a] < items.labels[b]
                    else [int(nb[i]), int(na[i])],
                }
            )
        codes = used.a * len(items) + used.b
        for m in every_pair(items, layout, sel, drop_every, maps, exempt, layer):
            out = ~np.isin(m.a * len(items) + m.b, codes)
            for k in np.unique(m.kind[out]).tolist():
                on = out & (m.kind == k)
                entry = left_out[kinds[k]]
                entry["pairs"] += int(on.sum())
                least = float(m.clearance_mm[on].min())
                if entry["least_clearance_mm"] is None or least < entry["least_clearance_mm"]:
                    entry["least_clearance_mm"] = least
                entry["violations"] += int((m.clearance_mm[on] < required_mm[k] - DRC_EPSILON_MM).sum())
    rows.sort(key=lambda r: (r["kind"], str(r["layer"]), r["objects"]))
    summaries = {s.kind.value: s.pairs_checked for s in report.summaries if s.kind.value in kinds}
    return {
        "probe": "drc_pairs_probe.py",
        "example": example,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "numpy_cpu_features": cpu_features(),
        "npy_disable_cpu_features": os.environ.get("NPY_DISABLE_CPU_FEATURES"),
        "embodic": embodic.__version__,
        "embodic_source_sha256": package_source_sha256(Path(embodic.__file__).parent),
        "drc_method": report.method,
        "violation_count": report.violation_count,
        "rule_mm": rule_mm,
        "rule_mm_hex": rule_mm.hex(),
        "required_mm": dict(zip(kinds, required_mm.tolist(), strict=True)),
        "epsilon_mm": DRC_EPSILON_MM,
        "pairs_checked": summaries,
        "replayed_pairs_checked": {k: replay.get(k, 0) for k in summaries},
        "groups": groups,
        "least_clearance_minus_bound_mm": least_gap_mm,
        "left_out": left_out,
        "closest_to_cutoff": sorted(rows, key=lambda r: abs(r["slack_mm"]))[:6],
        "split_edge": split_edge(layout, rules, items),
        "pairs": rows,
    }


def against(mine: dict, theirs: dict) -> dict:
    """Pairs and split-edge items that differ between two probe records, and the slack noise over the common pairs."""

    def key(r):
        return (r["kind"], str(r["layer"]), tuple(r["objects"]))

    a, b = {key(r): r for r in mine["pairs"]}, {key(r): r for r in theirs["pairs"]}
    differs = [
        {"key": list(k), "here": a.get(k), "there": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) is None or b.get(k) is None or (a[k]["kept"], a[k]["pieces"]) != (b[k]["kept"], b[k]["pieces"])
    ]
    split_a = {s["item"]: s for s in mine["split_edge"]}
    split_b = {s["item"]: s for s in theirs["split_edge"]}
    split = [
        {
            "item": n,
            "here": split_a.get(n, {}).get("ratio_hex"),
            "there": split_b.get(n, {}).get("ratio_hex"),
            "pieces_here": split_a.get(n, {}).get("pieces"),
            "pieces_there": split_b.get(n, {}).get("pieces"),
        }
        for n in sorted(set(split_a) | set(split_b))
        if split_a.get(n, {}).get("pieces") != split_b.get(n, {}).get("pieces")
    ]
    common = set(a) & set(b)
    return {
        "file_platform": theirs["platform"],
        "pairs_checked": theirs["pairs_checked"],
        "differs": differs,
        "split_edge_differs": split,
        "largest_slack_difference_mm": max((abs(a[k]["slack_mm"] - b[k]["slack_mm"]) for k in common), default=None),
        "common_pairs": len(common),
    }


def main(argv: list[str] | None = None) -> int:
    """Write the probe record and print its summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--example", default="wave_16p_example")
    parser.add_argument("--against", type=Path, default=DEFAULT_AGAINST)
    args = parser.parse_args(argv)
    record = probe(args.example)
    if args.against.exists() and args.against.resolve() != args.out.resolve():
        theirs = read_json(args.against)
        if (theirs["embodic_source_sha256"], theirs["example"]) == (record["embodic_source_sha256"], args.example):
            record["against"] = against(record, theirs)
        else:
            print(f"not compared with {args.against}: other embodic source or example")
    text = json.dumps(record, separators=(",", ":")) + "\n"
    args.out.write_bytes(gzip.compress(text.encode(), mtime=0) if args.out.suffix == ".gz" else text.encode())

    print(f"{record['platform']} Python {record['python']} NumPy {record['numpy']} embodic {record['embodic']}")
    print(f"pairs_checked {record['pairs_checked']}, violations {record['violation_count']}")
    print(f"replayed      {record['replayed_pairs_checked']}")
    print(f"rule_mm {record['rule_mm']!r}; least clearance - bound {record['least_clearance_minus_bound_mm']:.3e} mm")
    for r in record["closest_to_cutoff"][:2]:
        print(
            f"nearest the cutoff: {r['kind']} {r['layer']} {r['objects']} kept {r['kept']} slack {r['slack_mm']:.3e} mm"
        )
    for kind, entry in record["left_out"].items():
        if entry["pairs"]:
            print(
                f"left out {kind}: {entry['pairs']} pairs, least clearance {entry['least_clearance_mm']:.6f} mm"
                f" (rule {record['required_mm'][kind]}), violations {entry['violations']}"
            )
    for s in record["split_edge"]:
        o = s["other_rounding"]
        print(
            f"split tie {s['item']}: ratio {s['ratio']!r} -> {s['pieces']} pieces; other rounding: trace_trace"
            f" {o['trace_trace_pairs_checked']}, violations {o['violations']},"
            f" added {o['added']}, removed {o['removed']}"
        )
    if "against" in record:
        cmp = record["against"]
        print(
            f"against {cmp['file_platform']}: pairs_checked {cmp['pairs_checked']}; {len(cmp['differs'])} pairs and"
            f" {len(cmp['split_edge_differs'])} split ties differ; largest slack difference"
            f" {cmp['largest_slack_difference_mm']!r} mm over {cmp['common_pairs']} pairs"
        )
        for d in cmp["split_edge_differs"]:
            print(
                f"  split tie differs: {d['item']}: here {d['here']} ({d['pieces_here']} pieces),"
                f" there {d['there']} ({d['pieces_there']} pieces)"
            )
        for d in cmp["differs"]:
            here, there = d["here"] or {}, d["there"] or {}
            print(
                f"  pair differs: {d['key']}: here kept {here.get('kept')} pieces {here.get('pieces')} clearance"
                f" {here.get('clearance_mm')}; there kept {there.get('kept')} pieces {there.get('pieces')}"
            )
    ok = record["replayed_pairs_checked"] == record["pairs_checked"] and all(
        g["replay_matches"] for g in record["groups"]
    )
    ok &= all(e["violations"] == 0 for e in record["left_out"].values())
    print("probe " + ("consistent" if ok else "INCONSISTENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
