"""Series via fan clearances by brute force: M1's certified pair sweep over a series-group spiral board.

Run: python tests/independent/m2/series_fan_brute.py  (prints violations and the least copper clearance per case)

The board comes from the public API (build_layout), goes through embodic's board-dump writer and is read back by
Agent 4's own reader (tests/independent/m1/board_dump_reader.py). Exemptions are the contract's (drc_universe.py).
Edges and holes get rule 0: this instrument checks the fan's copper, not the outline.
"""

import dataclasses
import json
import sys
from pathlib import Path

M1 = Path(__file__).resolve().parents[1] / "m1"
sys.path.insert(0, str(M1))

from board_dump_reader import BoardDump, parse_board_dump  # noqa: E402
from drc_universe import Cls, Item, PairResult, contract_exemptions, sweep  # noqa: E402
from records import disc  # noqa: E402

EXAMPLES = {"CF-11": ("spiral_12c16p_default", 0.2), "D08": ("spiral_12c10p_d08", 0.8)}
COPPER_KINDS = {"trace_trace", "trace_via", "via_via", "pad_trace", "pad_pad"}


def own_universe(dump: BoardDump) -> list[Item]:
    """Traces, vias and pads of a parsed dump as M1 items; the outline is left out (rule 0 would never fire)."""
    items = [
        Item(f"path:{p.object}/prim:{p.seq}", Cls.TRACE, p.prim, p.layer, p.net, p.object, p.seq,
             corner=p.kind in ("fillet", "taper"))
        for p in dump.primitives
    ]  # fmt: skip
    items += [Item(f"via:{v.id}", Cls.VIA, disc(v.x, v.y, v.pad), None, v.net) for v in dump.vias]
    for pad in dump.raw["pads"]:
        assert pad["shape"] == "round", "only round pads are modelled"
        items.append(Item(f"pad:{pad['id']}", Cls.PAD, disc(pad["x"], pad["y"], pad["w"]), pad["layer"], pad["net"]))
    return items


def series_board(name: str, groups: int):
    """Return the BoardStack or Unbuildable of an example on 2k layers, k series groups of one pair."""
    from embodic.generators import build_layout
    from embodic.io.examples import load_example
    from embodic.model.layers import LayerConfig, LayerPair
    from embodic.model.stackup import generate_even_stackup
    from embodic.results import load_registry

    _, base = load_example(EXAMPLES[name][0])
    pairs = tuple(LayerPair(index=i, layer_in=f"L{2 * i + 1}", layer_out=f"L{2 * i + 2}") for i in range(groups))
    winding = dataclasses.replace(
        base.winding,
        layers=LayerConfig(pairs=pairs, series_groups=tuple((i,) for i in range(groups))),
        coil=dataclasses.replace(base.winding.coil, turns=None),
    )
    design = dataclasses.replace(base, stackup=generate_even_stackup(2 * groups, 0.0348, 1.6), winding=winding)
    return build_layout(design, load_registry())


def brute(name: str, groups: int, reach_mm: float = 0.05) -> tuple[list[PairResult], float]:
    """Return (violations, least copper clearance lower bound) of the series board by the certified sweep."""
    from embodic.io.board_dump import dump_layout, encode_board_dump

    stack = series_board(name, groups)
    layout = stack.boards[0]
    dump = parse_board_dump(json.loads(encode_board_dump(dump_layout(layout, case_id=f"{name}-k{groups}"))))
    items = own_universe(dump)
    rule = EXAMPLES[name][1]
    exempt = contract_exemptions(items, frozenset(layout.circuit.interconnect_path_ids))
    results = sweep(
        items,
        dump.layers,
        lambda kind: rule if kind in COPPER_KINDS else 0.0,
        exempt,
        reach_mm=reach_mm,
        decide=False,
    )
    copper = [r for r in results if r.kind in COPPER_KINDS]
    least = min((r.clearance.lo for r in copper), default=float("inf"))
    return [r for r in copper if r.verdict.name == "VIOLATION"], least


if __name__ == "__main__":
    for case in ("CF-11", "D08"):
        for k in (2, 3):
            found, least = brute(case, k)
            print(f"{case} k={k}: violations {len(found)}, least copper clearance lo {least:.6f} mm")
            for r in found[:5]:
                print("   ", r.a, r.b, r.kind, r.layer, r.clearance)
