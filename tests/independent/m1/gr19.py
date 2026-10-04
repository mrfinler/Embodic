"""GR-19 layouts through embodic's mapper and board dump, read back by Agent 4's reader, checked by Agent 4's sweep.

Run ``python tests/independent/m1/gr19.py`` from the repository root to print the per-layout violation table.

Two universes come from each dump. ``as_mapped`` keeps every net the dump states, so its exemptions match what
``run_drc`` sees and minima compare like for like. ``intended`` gives each via the net of the copper of its own phase
(Xcoil via ``phase`` read from the raw layout), which is what interfaces.md section 7 means by the via that terminates
a path end. A pair exempt in ``intended`` but reported by ``run_drc`` is a mapper net-name artefact (DEF-M1c-01).
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
from drc_universe import Cls, Item, PairResult, contract_exemptions, extended_exemptions, sweep
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


def _outline_prim(rec: dict[str, Any]) -> Prim:
    if rec["type"] == "line":
        return Line(rec["x1"], rec["y1"], rec["x2"], rec["y2"], 0.0)
    return Arc(rec["cx"], rec["cy"], rec["r"], rec["a1"], rec["a2"] - rec["a1"], 0.0)


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
        items += [Item(f"edge:{name}/prim:{k}", Cls.EDGE, _outline_prim(r), None) for k, r in enumerate(loop)]
    items += [Item(f"hole:{i}", Cls.HOLE, disc(h["x"], h["y"], h["dia"]), None) for i, h in enumerate(outline["holes"])]
    return items


@dataclass(frozen=True, slots=True)
class Board:
    """One GR-19 case: the mapped Layout, its parsed dump and both universes."""

    case_id: str
    raw: dict[str, Any]
    layout: Any
    dump: BoardDump
    as_mapped: list[Item]
    intended: list[Item]


def boards() -> list[Board]:
    """Map, dump, encode and re-read every GR-19 case through the public writer and Agent 4's reader."""
    mapper = load_mapper()
    from embodic.io.board_dump import dump_layout, encode_board_dump

    out = []
    for case_id, raw in load_cases().items():
        layout = mapper.layout_from_xcoil(raw)
        dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id=case_id))))
        out.append(
            Board(case_id, raw, layout, dump, universe(dump, raw, intended=False), universe(dump, raw, intended=True))
        )
    return out


def violations(results: list[PairResult]) -> dict[frozenset[str], PairResult]:
    """Return the violating pairs of a sweep."""
    return {frozenset((r.a, r.b)): r for r in results if r.verdict is Verdict.VIOLATION}


def classify(board: Board, engine: dict[frozenset[str], tuple[str, float]], rule_mm: float) -> Counter[str]:
    """Count every engine and brute violation by class; ``other`` classes are disagreements."""
    layers = range(len(board.dump.layers))
    strict = contract_exemptions(board.intended)
    wide = extended_exemptions(board.intended)
    mine = violations(sweep(board.intended, layers, lambda kind: rule_mm, strict))
    classes: Counter[str] = Counter()
    for key, (kind, measured) in engine.items():
        if key in mine:
            near = "near-rule" if measured > rule_mm - 1e-3 else "overlap" if measured < 0 else "intrusion"
            classes[f"{kind}: real D-006 ({near}), both report"] += 1
        elif key in strict and kind == "trace_via":
            classes["trace_via: DEF-M1c-01 artefact (via net 'A' vs path net 'PHASE_A')"] += 1
        else:
            classes[f"{kind}: engine only, OTHER"] += 1
    for key, result in mine.items():
        if key in engine:
            continue
        rule = "documented extension" if key in wide else "OTHER"
        classes[f"{result.kind}: brute only, engine exempts ({rule})"] += 1
    return classes


def main() -> int:
    """Print the per-layout violation table."""
    from embodic_adapter import pair_violations, uniform_rules

    from embodic.drc import run_drc

    for board in boards():
        rule = board.raw["params"]["clearance"]
        report = run_drc(board.layout, uniform_rules(rule))
        assert report is not None
        print(f"{board.case_id}: run_drc violation_count={report.violation_count}")
        for name, count in sorted(classify(board, pair_violations(report), rule).items()):
            print(f"  {count:5d}  {name}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
