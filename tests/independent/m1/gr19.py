"""GR-19 layouts through embodic's mapper and board dump, read back by Agent 4's reader, checked by Agent 4's sweep.

Run ``python tests/independent/m1/gr19.py`` from the repository root to print the per-layout violation table.

Two universes come from each dump. ``as_mapped`` keeps every net the dump states, as ``run_drc`` sees them.
``intended`` gives each via the net of the copper of its own phase (Xcoil via ``phase`` read from the raw layout), so a
mapper that renames via nets (DEF-M1c-01) cannot also move the expected exemptions. Interconnect path ids come from
``Layout.circuit.interconnect_path_ids``.

U-M1b's mapper makes one CopperPath per Xcoil object. Xcoil's star item holds the neutral ring and its stubs in one
``ic`` object that is not a chain (interfaces.md section 7, D-035b), while a CopperPath is one continuous chain
(section 5). ``split_interconnect_chains`` therefore hands the mapper one ``ic`` object per continuous chain, as
embodic's own serpentine and wave ports split the star item (DEF-M1V-03).
"""

import importlib.util
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from board_dump_reader import BoardDump, parse_board_dump
from brute_clearance import Verdict
from continuity import chains, first_gap
from drc_universe import Cls, Item, PairResult, Rule, contract_exemptions, sweep
from records import Arc, Line, Prim, disc

REPO = Path(__file__).resolve().parents[3]
FIXTURES = REPO / "tests" / "golden" / "data" / "m1_layout"
MAPPER = REPO / "tests" / "golden" / "m1_layout" / "xcoil_map.py"
PHASE_NET = ("PHASE_A", "PHASE_B", "PHASE_C")


def load_cases() -> dict[str, Any]:
    """Return case id -> Xcoil raw layout for every GR-19 fixture."""
    out = {}
    for path in sorted(FIXTURES.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        out[doc["case_id"]] = doc["calls"][0]["output"]
    return out


def load_mapper() -> Any:
    """Import U-M1b's GR-19 mapper module from its file (it lives in the golden tests, not in the package)."""
    spec = importlib.util.spec_from_file_location("gr19_xcoil_map", MAPPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _centreline(rec: dict[str, Any]) -> Prim:
    """Xcoil record to a zero-width primitive: an outline edge, or the geometry of a copper record."""
    if rec["type"] == "line":
        return Line(rec["x1"], rec["y1"], rec["x2"], rec["y2"], 0.0)
    return Arc(rec["cx"], rec["cy"], rec["r"], rec["a1"], rec["a2"] - rec["a1"], 0.0)


def _split(obj: dict[str, Any]) -> list[dict[str, Any]]:
    if obj["kind"] != "ic":
        return [obj]
    runs = chains([_centreline(rec) for rec in obj["prims"]])
    return [{**obj, "prims": obj["prims"][run.start : run.stop]} for run in runs]


def split_interconnect_chains(raw: dict[str, Any]) -> dict[str, Any]:
    """Return ``raw`` with each ``ic`` object replaced by one object per chain; joints wider than CONTINUITY_TOL_MM cut.

    Primitive order, every other object and every other field stay as Xcoil returned them.
    """
    layers = [{**layer, "objs": [o for obj in layer["objs"] for o in _split(obj)]} for layer in raw["layers"]]
    return {**raw, "layers": layers}


def universe(dump: BoardDump, raw: dict[str, Any], *, intended: bool) -> list[Item]:
    """Build the item list of one board from a parsed dump; ``intended`` re-derives via nets from the raw phases."""
    items = [
        Item(f"path:{p.object}/prim:{p.seq}", Cls.TRACE, p.prim, p.layer, p.net, p.object, p.seq,
             corner=p.kind in ("fillet", "taper"))
        for p in dump.primitives
    ]  # fmt: skip
    for v, raw_via in zip(dump.vias, raw["vias"], strict=True):
        net = PHASE_NET[raw_via["phase"]] if intended else v.net
        items.append(Item(f"via:{v.id}", Cls.VIA, disc(v.x, v.y, v.pad), None, net))
    for pad in dump.raw["pads"]:
        assert pad["shape"] == "round", "only round pads are modelled"
        layer = None if pad["layer"] is None else pad["layer"]
        items.append(Item(f"pad:{pad['id']}", Cls.PAD, disc(pad["x"], pad["y"], pad["w"]), layer, pad["net"]))
    outline = dump.raw["outline"]
    loops = [("outer", outline["board"])] + [(f"cutout{c}", loop) for c, loop in enumerate(outline["cutouts"])]
    for name, loop in loops:
        items += [Item(f"edge:{name}/prim:{k}", Cls.EDGE, _centreline(r), None) for k, r in enumerate(loop)]
    items += [Item(f"hole:{i}", Cls.HOLE, disc(h["x"], h["y"], h["dia"]), None) for i, h in enumerate(outline["holes"])]
    return items


@dataclass(frozen=True, slots=True)
class Board:
    """One GR-19 case: raw Xcoil output, the Layout of its split form, the dump, universes, interconnect ids."""

    case_id: str
    raw: dict[str, Any]
    layout: Any
    dump: BoardDump
    as_mapped: list[Item]
    intended: list[Item]
    interconnect: frozenset[int]


def boards() -> list[Board]:
    """Map, dump, encode and re-read every GR-19 case through the public writer and Agent 4's reader."""
    mapper = load_mapper()
    from embodic.io.board_dump import dump_layout, encode_board_dump

    out = []
    for case_id, raw in load_cases().items():
        layout = mapper.layout_from_xcoil(split_interconnect_chains(raw))
        dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id=case_id))))
        out.append(
            Board(case_id, raw, layout, dump, universe(dump, raw, intended=False), universe(dump, raw, intended=True),
                  frozenset(layout.circuit.interconnect_path_ids))
        )  # fmt: skip
    return out


def violations(results: list[PairResult]) -> dict[frozenset[str], PairResult]:
    """Return the violating pairs of a sweep."""
    return {frozenset((r.a, r.b)): r for r in results if r.verdict is Verdict.VIOLATION}


WAIVER = frozenset({Rule.INTERCONNECT_END, Rule.INTERCONNECT_TAP})


def classify(board: Board, engine: dict[frozenset[str], tuple[str, float]], rule_mm: float) -> Counter[str]:
    """Count every engine and brute violation by class; ``OTHER`` classes are disagreements with the contract."""
    exempt = contract_exemptions(board.intended, board.interconnect)
    mine = violations(sweep(board.intended, range(len(board.dump.layers)), lambda kind: rule_mm, exempt))
    classes: Counter[str] = Counter()
    for key, (kind, measured) in engine.items():
        if key in mine:
            near = "near-rule" if measured > rule_mm - 1e-3 else "overlap" if measured < 0 else "intrusion"
            classes[f"{kind}: real D-006 ({near}), both report"] += 1
        elif key in exempt:
            classes[f"{kind}: engine reports, contract exempts by {exempt[key]} (OTHER)"] += 1
        else:
            classes[f"{kind}: engine only, brute clean (OTHER)"] += 1
    for key, result in mine.items():
        if key not in engine:
            classes[f"{result.kind}: brute only, engine exempts (OTHER)"] += 1
    return classes


def object_gaps_mm(raw: dict[str, Any]) -> dict[int, float]:
    """Xcoil object index (U-M1b's path id) -> its first joint gap, for every object that is not one chain."""
    objs = [obj for layer in raw["layers"] for obj in layer["objs"]]
    gaps = {i: first_gap([_centreline(rec) for rec in obj["prims"]]) for i, obj in enumerate(objs)}
    return {i: round(gap.distance_mm, 6) for i, gap in gaps.items() if gap is not None}


def main() -> int:
    """Print the per-layout violation table, then what U-M1b's unsplit mapping gives instead."""
    from embodic_adapter import pair_violations, uniform_rules

    from embodic.drc import run_drc

    mapper = load_mapper()
    for board in boards():
        rule = board.raw["params"]["clearance"]
        report = run_drc(board.layout, uniform_rules(rule))
        assert report is not None
        print(f"{board.case_id}: run_drc violation_count={report.violation_count}, paths={len(board.layout.paths)}")
        for name, count in sorted(classify(board, pair_violations(report), rule).items()):
            print(f"  {count:5d}  {name}")
        unsplit = mapper.layout_from_xcoil(board.raw)
        unsplit_report = run_drc(unsplit, uniform_rules(rule))
        assert unsplit_report is not None
        gaps = object_gaps_mm(board.raw)
        on_gapped = sorted(
            sorted(key) for key in pair_violations(unsplit_report)
            if any(label.startswith("path:") and int(label[5:].split("/")[0]) in gaps for label in key)
        )  # fmt: skip
        print(f"  U-M1b unsplit: paths={len(unsplit.paths)}, gaps {gaps}, run_drc violation_count="
              f"{unsplit_report.violation_count}, pairs on a gapped object {on_gapped}")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
