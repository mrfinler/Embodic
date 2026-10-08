"""Item 2 (U-V3): brute-force DRC of every ported board against ``run_drc``; prints the class table.

Each board goes through embodic's dump writer and Agent 4's M1 reader, then the M1 certified pair sweep under the
interfaces.md section 7 exemptions as D-022, D-022c, D-035b (rule 5) and D-036a with D-037a (rule 2b) amend them
(``drc_universe.contract_exemptions``).
"""

import json
import sys
import time
from collections import Counter
from dataclasses import dataclass
from functools import cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1"))

from board_dump_reader import BoardDump, parse_board_dump
from brute_clearance import Verdict
from cases import xcoil_dumps
from drc_universe import Cls, Item, contract_exemptions, sweep
from embodic_adapter import pair_violations, uniform_rules
from records import Arc, Line, Prim, disc
from subject import stack_for

from embodic.drc import run_drc
from embodic.io.board_dump import dump_layout, encode_board_dump


def _outline_prim(rec: dict) -> Prim:
    if rec["type"] == "line":
        return Line(rec["x1"], rec["y1"], rec["x2"], rec["y2"], 0.0)
    return Arc(rec["cx"], rec["cy"], rec["r"], rec["a1"], rec["a2"] - rec["a1"], 0.0)


def universe(dump: BoardDump) -> list[Item]:
    """Every copper and keep-out item of one parsed dump, with the nets the dump states."""
    items = [
        Item(f"path:{p.object}/prim:{p.seq}", Cls.TRACE, p.prim, p.layer, p.net, p.object, p.seq,
             corner=p.kind in ("fillet", "taper"))
        for p in dump.primitives
    ]  # fmt: skip
    items += [Item(f"via:{v.id}", Cls.VIA, disc(v.x, v.y, v.pad), None, v.net) for v in dump.vias]
    for pad in dump.raw["pads"]:
        assert pad["shape"] == "round", "only round pads are modelled"
        items.append(Item(f"pad:{pad['id']}", Cls.PAD, disc(pad["x"], pad["y"], pad["w"]), pad["layer"], pad["net"]))
    outline = dump.raw["outline"]
    loops = [("outer", outline["board"])] + [(f"cutout{c}", loop) for c, loop in enumerate(outline["cutouts"])]
    for name, loop in loops:
        items += [Item(f"edge:{name}/prim:{k}", Cls.EDGE, _outline_prim(r), None) for k, r in enumerate(loop)]
    items += [Item(f"hole:{i}", Cls.HOLE, disc(h["x"], h["y"], h["dia"]), None) for i, h in enumerate(outline["holes"])]
    return items


@dataclass(frozen=True, slots=True)
class BoardDrc:
    """Engine and brute violation sets of one board and their classes."""

    board_id: str
    engine: dict[frozenset[str], tuple[str, float]]
    brute: dict[frozenset[str], str]
    exempt_by_contract: dict[frozenset[str], str]
    seconds: float

    def classes(self) -> Counter[str]:
        """Count every engine and brute violation by agreement class."""
        out: Counter[str] = Counter()
        for key, (kind, measured) in self.engine.items():
            if key in self.brute:
                out[f"{kind}: both report ({'overlap' if measured < 0 else 'near rule'})"] += 1
            elif key in self.exempt_by_contract:
                out[f"{kind}: engine only, contract exempts by {self.exempt_by_contract[key]}"] += 1
            else:
                out[f"{kind}: engine only, brute clean"] += 1
        for key, kind in self.brute.items():
            if key not in self.engine:
                out[f"{kind}: brute only"] += 1
        return out


@cache
def board_drc(case_id: str) -> tuple[BoardDrc, ...]:
    """Run both checks on every board of one case at Xcoil's clearance."""
    rule = xcoil_dumps()[case_id]["params"]["clearance"]
    stack = stack_for(case_id)
    out = []
    for k, layout in enumerate(stack.boards):
        board_id = case_id if len(stack.boards) == 1 else f"{case_id}-board{k}"
        t = time.perf_counter()
        dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id=board_id))))
        items = universe(dump)
        exempt = contract_exemptions(items, frozenset(layout.circuit.interconnect_path_ids))
        found = sweep(items, range(len(dump.layers)), lambda kind: rule, exempt)
        brute = {frozenset((r.a, r.b)): r.kind for r in found if r.verdict is Verdict.VIOLATION}
        undecided = [r for r in found if r.verdict is Verdict.UNDECIDED]
        assert not undecided, f"{board_id}: {len(undecided)} undecided pairs"
        report = run_drc(layout, uniform_rules(rule))
        assert report is not None
        out.append(BoardDrc(board_id, pair_violations(report), brute, dict(exempt), time.perf_counter() - t))
    return tuple(out)


def main() -> None:
    """Print each board's engine count, brute count and classes."""
    for case_id in xcoil_dumps():
        for b in board_drc(case_id):
            print(f"{b.board_id}: engine {len(b.engine)} brute {len(b.brute)} ({b.seconds:.1f} s)")
            for name, n in sorted(b.classes().items()):
                print(f"    {n:5d}  {name}")


if __name__ == "__main__":
    main()
