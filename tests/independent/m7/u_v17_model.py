"""U-V17: Agent 4's M1 model under interfaces.md section 7 as revised on 2026-10-20 (U-D25, D-078).

usage: PYTHONPATH=src python tests/independent/m7/u_v17_model.py [--old-rev REV] [--json FILE] [--skip-sweep]

Three measurements, own side only (``m1/drc_universe.py``, ``m1/brute_clearance.py``, ``m3/drc_m3.py``):

- sweep: each board of the five packaged examples through the product's dump writer, M1's reader and the brute pair
  sweep under the model's exemptions, against the pairs ``run_drc`` of this checkout reports. With ``--old-rev`` the
  model of that revision runs on the same items, and the exemptions it has and the new model lacks are counted by the
  old rule label.
- mutant: U-V16's DEF-UV16-01 mutant (D08, leg 25 widened to 0.8 mm; control start moved 0.001 mm) through the model.
- cases: the Q3 pad case and the DEF-UD25-01 leading taper, through the model and through ``run_drc`` of this checkout.
"""

import argparse
import dataclasses
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
for sub in ("m1", "m3"):
    sys.path.insert(0, str(REPO / "tests" / "independent" / sub))
sys.path.insert(0, str(HERE))

from board_dump_reader import parse_board_dump  # noqa: E402
from brute_clearance import Verdict, clearance_bracket  # noqa: E402
from drc_m3 import universe  # noqa: E402
from drc_universe import Cls, Item, contract_exemptions, sweep  # noqa: E402
from embodic_adapter import pair_violations, to_layout, uniform_rules  # noqa: E402
from records import Line, disc  # noqa: E402
from u_v16_spots import _leg_mutant  # noqa: E402
from v3_10_own_models import RULE_FIELD  # noqa: E402

from embodic.api import compute_project  # noqa: E402
from embodic.drc import run_drc  # noqa: E402
from embodic.io.board_dump import dump_layout, encode_board_dump  # noqa: E402

EXAMPLES = REPO / "resources" / "examples"
D08 = "spiral_12c10p_d08"


def _old_model(rev: str):
    """Import ``m1/drc_universe.py`` as it stood at ``rev`` (git show), beside the current one."""
    text = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{rev}:tests/independent/m1/drc_universe.py"],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    path = Path(tempfile.mkdtemp()) / "drc_universe_old.py"
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("drc_universe_old", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _items(layout, case_id: str) -> list[Item]:
    return universe(parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id=case_id)))))


def _brute(items: list[Item], layers: int, rules, exempt) -> tuple[dict[frozenset[str], str], int]:
    found = sweep(items, range(layers), lambda kind: getattr(rules, RULE_FIELD[kind]), exempt)
    brute = {frozenset((r.a, r.b)): r.kind for r in found if r.verdict is Verdict.VIOLATION}
    return brute, sum(r.verdict is Verdict.UNDECIDED for r in found)


def _against_old(old, items: list[Item], interconnect: frozenset[int], exempt) -> dict:
    """Exemptions the old model has and the new one lacks, by old rule and by whether a sweep can check the pair."""
    before = old.contract_exemptions([dataclasses.replace(it, cls=old.Cls(it.cls)) for it in items], interconnect)
    layer = {it.label: it.layer for it in items}

    def shared(pair: frozenset[str]) -> str:
        a, b = (layer[x] for x in pair)
        return "same layer" if None in (a, b) or a == b else "cross layer"

    return {
        "dropped_by_old_rule": dict(Counter(f"{before[p].name}, {shared(p)}" for p in before.keys() - exempt.keys())),
        "added_by_new_rule": dict(Counter(exempt[p].name for p in exempt.keys() - before.keys())),
    }


def sweep_examples(old, run_sweep: bool) -> list[dict]:
    """One row per board of the five packaged examples."""
    rows = []
    for example in sorted(EXAMPLES.glob("*.embodic.json")):
        outcome = compute_project(example)
        rules = outcome.design.drc_rules
        for k, (layout, report) in enumerate(zip(outcome.boards.boards, outcome.drc, strict=True)):
            items = _items(layout, f"board{k}")
            interconnect = frozenset(layout.circuit.interconnect_path_ids)
            exempt = contract_exemptions(items, interconnect)
            row = {"example": example.name.removesuffix(".embodic.json"), "board": k,
                   "exempt_pairs": len(exempt), "by_rule": dict(Counter(r.name for r in exempt.values()))}  # fmt: skip
            if old is not None:
                row |= _against_old(old, items, interconnect, exempt)
            if run_sweep:
                start = time.perf_counter()
                brute, undecided = _brute(items, len(layout.copper_layers), rules, exempt)
                engine = {frozenset(v.objects) for v in report.violations if v.kind.value in RULE_FIELD}
                row |= {
                    "brute_violations": len(brute),
                    "undecided": undecided,
                    "engine_total": report.violation_count,
                    "engine_pairs": len(engine),
                    "brute_only": sorted(sorted(p) for p in brute.keys() - engine)[:10],
                    "engine_only": sorted(sorted(p) for p in engine - brute.keys())[:10],
                    "sets_equal": brute.keys() == engine and undecided == 0,
                    "sweep_s": round(time.perf_counter() - start, 1),
                }
            print(json.dumps(row), flush=True)
            rows.append(row)
    return rows


def d08_mutant() -> dict:
    """DEF-UV16-01: the model's leg 25 pairs (U-V16: 0.700 mm from coil turn path:1/prim:9 at the 0.8 mm rule)."""
    outcome = compute_project(EXAMPLES / f"{D08}.embodic.json")
    layout, rules = outcome.boards.boards[0], outcome.design.drc_rules
    out = {}
    for name, shift in (("joint kept", 0.0), ("control: start 0.001 mm off the coil end", 0.001)):
        mutant = _leg_mutant(layout, 25, 0.8, shift)
        items = _items(mutant, "d08-mutant")
        exempt = contract_exemptions(items, frozenset(mutant.circuit.interconnect_path_ids))
        brute, undecided = _brute(items, len(mutant.copper_layers), rules, exempt)
        prim = {it.label: it.prim for it in items}
        leg = {}
        for pair in sorted(sorted(p) for p in brute if "path:25/prim:0" in p):
            b = clearance_bracket(prim[pair[0]], prim[pair[1]], tol=1e-9)
            leg[" / ".join(pair)] = [round(b.lo, 9), round(b.hi, 9)]
        product = run_drc(mutant, rules, use_symmetry=False)
        out[name] = {
            "model_violations": len(brute),
            "undecided": undecided,
            "model_leg25_pairs_mm": leg,
            "model_reports_path1_prim9": "path:1/prim:9 / path:25/prim:0" in leg,
            "run_drc_this_checkout_passed": product.passed,
            "run_drc_this_checkout_leg25": sorted(
                [list(v.objects), round(v.clearance_mm, 6)] for v in product.violations if "path:25/prim:0" in v.objects
            ),
        }
        print(name, json.dumps(out[name]), flush=True)
    return out


def _trace(path: int, seq: int, prim: Line, net: str, corner: bool = False) -> Item:
    return Item(f"path:{path}/prim:{seq}", Cls.TRACE, prim, 0, net, path, seq, corner=corner)


def _both(items: list[Item], interconnect: tuple[int, ...]) -> dict:
    """Model sweep and run_drc of this checkout on one hand-built board, 0.2 mm rule."""
    exempt = contract_exemptions(items, interconnect)
    mine = sweep(items, [0], lambda kind: 0.2, exempt, decide=False, tol=1e-9)
    layout = to_layout(items, 1)
    layout = dataclasses.replace(
        layout, circuit=dataclasses.replace(layout.circuit, interconnect_path_ids=tuple(interconnect))
    )
    report = run_drc(layout, uniform_rules(0.2), use_symmetry=False)
    return {
        "model": sorted([r.a, r.b, r.kind, round(r.clearance.lo, 6)] for r in mine if r.verdict is Verdict.VIOLATION),
        "model_rules": {" / ".join(sorted(p)): r.name for p, r in exempt.items() if "path:0/prim:0" in p},
        "run_drc_this_checkout": sorted([*sorted(k), v[0], round(v[1], 6)] for k, v in pair_violations(report).items()),
    }


def cases() -> dict:
    """Q3 (a pad on an interconnect centreline) and DEF-UD25-01 (a path that starts with a taper)."""
    w = 0.2
    out = {}
    for net in ("N", "PHASE_A"):
        items = [_trace(0, 0, Line(-5, 0, 5, 0, w), "N"), Item("pad:0", Cls.PAD, disc(0, 0, 0.6), 0, net)]
        out[f"Q3 pad of net {net} centred mid-path on an N interconnect"] = _both(items, (0,))
    prims = [Line(0, 0, 1, 0, w), Line(1, 0, 1, 0.3, w), Line(1, 0.3, 0, 0.3, w)]
    for name, corner in (("DEF-UD25-01 leading taper", True), ("DEF-UD25-01 control, side in place", False)):
        items = [_trace(0, k, p, "A", corner=corner and k == 0) for k, p in enumerate(prims)]
        out[name] = _both(items, ())
    for name, row in out.items():
        print(name, json.dumps(row), flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    """Print and optionally write the cases, the D08 mutant and the example rows."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--old-rev")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--skip-sweep", action="store_true")
    args = parser.parse_args(argv)
    old = _old_model(args.old_rev) if args.old_rev else None
    out = {"cases": cases(), "d08_mutant": d08_mutant(), "examples": sweep_examples(old, not args.skip_sweep)}
    if args.json:
        args.json.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
