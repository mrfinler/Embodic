"""DEF-M2e3-01 re-measured: mapped GR-19 layouts with Xcoil's own phase members instead of `_series_circuit`.

Run: python tests/independent/m2/def_m2e3_01.py  (prints embodic phase R against Xcoil phaseRtrace per case)

Xcoil's members, read in engine.js (read-only): sector `computeSector` l.2471-2475, one element per coil layer (X and
Y in series, layer pairs in parallel), rings and legs go to the phase `extraR`; wave l.2211-2214, one element per
track, copies on layers of the same type in parallel, via barrels in `extraR`; links are `Rlink` (l.2061).
`phaseRtrace` excludes every `extraR`. Both GR-19 cases have one layer pair, so every element has one member.
"""

import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tests" / "golden")]

MEMBER_KINDS = {"layout-sector-default": {"coil"}, "layout-wave-turns-2": {"track"}}
ANALYSIS = {"layout-sector-default": "analysis-sector-default", "layout-wave-turns-2": "analysis-wave-turns-2"}


def xcoil_circuit(raw, layout, kinds):
    """Phase circuits whose one-member groups are the paths of Xcoil element objects, in Xcoil object order."""
    from embodic.geometry.circuit import Member, ParallelGroup, PhaseCircuit
    from embodic.model.vocabulary import Phase

    objects = [obj for layer in raw["layers"] for obj in layer["objs"]]
    assert len(objects) == len(layout.paths), "the mapper makes one path per Xcoil object"
    phases = []
    for index, phase in enumerate((Phase.A, Phase.B, Phase.C)):
        groups = tuple(
            ParallelGroup(members=(Member(path_ids=(path.id,), via_ids=()),))
            for obj, path in zip(objects, layout.paths, strict=True)
            if obj["kind"] in kinds and obj.get("phase") == index
        )
        phases.append(PhaseCircuit(phase=phase, groups=groups, terminal_net=f"PHASE_{phase.value}"))
    return dataclasses.replace(layout.circuit, phases=tuple(phases))


def measure() -> dict[str, dict[str, list[float]]]:
    """Return per case embodic phase R (operating) with Xcoil's members and with `_series_circuit`, and Xcoil's."""
    from m1_layout.xcoil_map import layout_from_xcoil
    from m2_physics import test_analyse_layouts as harness

    from embodic.geometry.layout import BoardStack
    from embodic.physics import analyse
    from embodic.results import load_registry

    registry = load_registry()
    out = {}
    for case, kinds in MEMBER_KINDS.items():
        raw = harness._raw(case)
        layout = layout_from_xcoil(raw)
        thickness = raw["params"]["boardThickness"]
        rows = {}
        for name, circuit in (("xcoil_members", xcoil_circuit(raw, layout, kinds)), ("series", None)):
            board = dataclasses.replace(layout, circuit=circuit) if circuit else harness._stack(raw).boards[0]
            stack = BoardStack(boards=(board,), board_thickness_mm=thickness, board_gap_mm=0.0)
            result = analyse(harness._design(raw), stack, {}, registry)
            rows[name] = [p.resistance_operating_ohm.value for p in result.phases]
        golden = json.loads((ROOT / "tests/golden/data/physics" / f"{ANALYSIS[case]}.json").read_text())
        rows["xcoil_rtrace"] = golden["calls"][0]["output"]["phaseRtrace"]
        out[case] = rows
    return out


if __name__ == "__main__":
    for case, rows in measure().items():
        x = rows["xcoil_rtrace"]
        for name in ("xcoil_members", "series"):
            gaps = [r / ref - 1.0 for r, ref in zip(rows[name], x, strict=True)]
            print(
                f"{case} {name}: R {[f'{r:.6f}' for r in rows[name]]} vs Xcoil {[f'{r:.6f}' for r in x]}, "
                f"rel {[f'{g:+.3e}' for g in gaps]}"
            )
