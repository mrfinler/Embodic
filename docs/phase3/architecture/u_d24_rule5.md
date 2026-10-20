Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# U-D24: rule 5 and the rule 2 tap are per primitive (DEF-UV16-01, D-078)

Unit U-D24, 2026-10-20, on main 14c8b7a (worktree `/home/claude/wt/U-D24`, branch `unit/U-D24`). The contract text is
in `docs/phase2/architecture/interfaces.md` §7 (rule 2, rule 5, the revision note of 2026-10-20, the net test and the
test table) and in `docs/phase2/architecture/test_plan.md` §5.1 UT-DRC-04. This file gives the reasons, the measured
effect, the case geometry and the questions for Fable. No code or test of the product changed.

Status words follow standing order 12. `verified` means read at the named line on main 14c8b7a, or reproduced by
running the named script on this Linux container (CPython 3.11, the dev venv of `/home/claude/embodic`, `PYTHONPATH=src`
from the worktree). Nothing here ran on Windows.

| Item | Ruling in one line |
|---|---|
| 1. Rule 5 | An end group is exempt only from the landing group of the primitive its end point lies on. An end point on another path's end point is a rule 3 node. |
| 2. Rule 2 tap (D-022c) | Same blind spot. Narrowed to per primitive: the tap is rule 2b with the net test waived for an interconnect path. |
| 3. Examples | 0, 0, 0, 0 and 186 violations stay (`verified` by running). No pair surfaces. GR-19 stays 0, 0, 186. |
| 4. Cases | UT-DRC-04 2d restated, 2e and 2f new; 5a to 5e and 5h kept, 5f and 5g inverted, 5i to 5l new. |
| 5. For Fable | Q1 to Q5 in section 6. Q1 (the sharp-corner cost) and Q2 (finding F-1) need a decision. |

## 1. Rule 5

### The defect, traced to its first wrong decision

DEF-UV16-01 is a symptom of one rule. Rule 5 (D-035b) said the end group "is exempt from every primitive of that other
path". The joint that D-035b needed was a strand or stub end on a bus or ring, but the rule exempted the whole bus. The
end-point reading of U-D8 (D-037a) then made every path end that meets another path's end a rule 5 case, so the whole
path was exempt there too. `_junctions` does what the text said (`items.py` l.284-287: `np.isin(owner, trunks)`), and
Agent 4's `_tees` does the same (`drc_universe.py` l.236-241, `_pairs(e.group, paths[pid])`). Both readings are
`verified` by reading on main 14c8b7a. The root cause is in the contract, so the fix is in the contract (standing
order 11).

The same shape appears in a second clause, the D-022c tap (section 2). No other clause of §7 exempts a whole path:
rule 2 and rule 3 name end groups, rule 2b names primitives, rule 4 names a via and a pad (`verified` by reading §7).

### The new clause

When the end point of a path lies within `COINCIDENCE_MM` of the centreline of a primitive of another same-net path on
its layer, the end group is exempt from the landing group of that primitive, and from nothing else of that path.

- The landing group of a main primitive is the primitive with the fillets and tapers that belong to it.
- The landing group of a fillet or taper is the fillet or taper, the main primitives it belongs to, and the other
  fillets and tapers between those main primitives.
- At the other path's end point, the landing group lies inside that path's end group. Rule 3 already exempts end group
  against end group there, so rule 5 adds nothing. This is Agent 4's reading in the DEF-UV16-01 row.

The landing group is the extent that an end group has at a path end. An end group meets the other path at one point,
and the copper that must overlap there is the primitive under that point with its own corner pieces. This is the
brief's proposal, adopted.

In the engine's slots (a main takes 2 x main index, a fillet or taper 2 x main index + 1 of the main before it,
`items.py` l.48), the landing group is every primitive of the other path whose slot lies within 1 of the slot of a hit
primitive. `_path_ends` already uses that test for an end group (`items.py` l.181).

### Readings measured side by side

`u_d24_probe.py` (section 7) replaced `_junctions` with each reading and ran `run_drc` on the five packaged examples
and the three GR-19 layouts (`verified` by running, 83 s wall time). `u_d24_cases.py` ran the hand-built cases.

| Reading of rule 5 | D08 mutant (leg 25, 0.700 mm from `path:1/prim:9`) | Case 5k (T 0.1 mm before a fillet) | Examples |
|---|---|---|---|
| Whole path, end points included (main 14c8b7a) | passes: blind | exempt | 0, 0, 0, 0, 186 |
| Landing group (adopted) | reported at 0.700 mm | exempt | 0, 0, 0, 0, 186 |
| Landing group, hits at trunk end points left to rule 3 | reported at 0.700 mm | exempt | same pairs as the adopted reading on all eight layouts |
| Landing primitive with its rule 1 neighbours (slot within 2) | passes: blind | exempt | 0, 0, 0, 0, 186 |
| Landing primitive alone | reported at 0.700 mm | reported at -0.100 mm: a designed joint | 0, 0, 0, 0, 186 |

The rule 1 neighbour reading fails on the defect itself. `path:1/prim:9` is the main primitive before the stub
`path:1/prim:10` that leg 25 starts on, one main index away. The landing primitive alone reports a branch whose copper
overlaps the fillet beside its landing point. The adopted reading and the variant that leaves trunk end points to rule
3 exempt the same pairs on every layout measured, so the contract states one rule and notes that rule 3 covers the end
point.

### What it costs

A T that lands near a sharp corner of the other path, with no fillet, is now reported against the next main primitive.
Product case 5f is that geometry: the end point lies 0.05 mm before the corner, and the pair is reported at -0.150 mm
(`verified` by running). Rules 2 and 3 already report a sharp corner behind an end group in the same way, and rule 2b
reports a via near a sharp corner of a same-net path in the same way (D-037a). No packaged example or GR-19 layout has
such a T: the adopted reading surfaces no pair on any of the eight (section 3). The DRC is the guard against generator
mistakes (D-078 c). A wrong report is visible and a missed one is not, so the narrow rule is the safer default. Fable
decides (Q1).

## 2. The rule 2 tap (D-022c)

The tap had the same blind spot. `_taps` exempts a via from every primitive of an interconnect path when any primitive
passes within `pad_mm / 2` of it (`items.py` l.267-268, `tapped_rings`). An interconnect lead that ends on a via is also
a tap there, because its end primitive passes over the via. So every lead was exempt from the whole of each via it ends
on. On the wave board this exempts the second primitive of each lead from the terminal via the lead starts on:
`path:93/prim:1` from via 2, `path:94/prim:1` from via 34 and `path:95/prim:1` from via 18, each 0.200 mm at the
0.2 mm rule (`verified` by running). A generator change that moved one of them inward would pass `run_drc`.

Ruling: narrow it. The tap is a via and each primitive of an interconnect path whose centreline passes within
`pad_mm / 2` of the via centre, whatever the nets and the via role. It is rule 2b with the net test waived for an
interconnect path, so §7 now has one tap test and one waiver instead of two tap clauses of different reach.

D-022c chose the whole path in answer to DEF-M1c3-01. That defect needed an exemption for a mid-path tap at all, since
rules 2 and 3 covered only path ends (`tests/independent/README.md` l.160, `verified` by reading). It did not need the
whole path. D-037a narrowed rule 2b after a measured harm (828 extra pairs on D08) and kept the tap whole-path, and its
text gives no reason for the tap (`docs/decision_log.md` l.43, `verified` by reading). The measurement here shows that
narrowing costs nothing on the shipped boards: the tap stops exempting 0, 0, 0, 0 and 3 pairs on the five examples and
1 pair on GR-19 sector (1.600 mm), and no pair is reported.

The cost has the shape of rule 5's. A via that taps an interconnect path mid-primitive near a sharp corner is reported
against the primitive past the corner when that primitive's centreline lies more than `pad_mm / 2` from the via centre.
Rule 2b has carried that cost since D-037a.

## 3. Effect on the boards

`verified` by running `u_d24_probe.py --gr19` on main 14c8b7a with `_junctions` and `_taps` replaced. The violation
counts are the same with and without the symmetry shortcut. "Dropped" counts the pairs that lose their exemption.
"Least margin" is the least clearance among them minus the rule.

| Layout | Violations, main | Violations, U-D24 | Rule 5 pairs dropped | Tap pairs dropped | Least margin of a dropped pair |
|---|---|---|---|---|---|
| serpentine_16p_example | 0 | 0 | 1506 | 0 | -1.0e-14 mm (`path:7/prim:188`, `path:8/prim:0`) |
| spiral_12c10p_d08 | 0 | 0 | 120 | 0 | -4.7e-15 mm (`path:10/prim:1`, `path:48/prim:0`) |
| spiral_12c14p | 0 | 0 | 492 | 0 | -7.1e-15 mm |
| spiral_12c16p_default | 0 | 0 | 492 | 0 | -7.1e-15 mm |
| wave_16p_example | 186 | 186 (same set) | 0 | 3 | +1.8e-15 mm (`path:95/prim:1`, via 18) |
| GR-19 sector | 0 | 0 | 396 | 1 | -4.3e-15 mm |
| GR-19 serpentine | 0 | 0 | 1506 | 0 | -1.0e-14 mm |
| GR-19 wave | 186 | 186 (same set) | 0 | 3 | +1.8e-15 mm |

Every dropped pair sits at the rule or above it. The least margin is far inside D-006's 1e-6 mm, so none is a
violation. The generator places these gaps at the clearance exactly, as U-V16 found. The D08, spiral_12c14p and
spiral_12c16p_default counts equal U-V16's rule 5 counts (120, 492, 492). On the serpentine example U-V16 counted 1512
rule 5 pairs that are not designed joints, and 1506 are dropped here. The adopted reading keeps 19 rule 5 pairs there:
13 touching joints and 6 end-group pairs at 16.520 mm (`verified` by running a scratch listing). That the 6 are the
difference is `inferred`, since U-V16's joint test was not rerun. On the wave example the one designed T of U-V16 stays
exempt (0 rule 5 pairs dropped).

The D08 mutant of U-V16 (leg 25 widened to 0.8 mm) passes `run_drc` on main and is reported at 0.700 mm under the new
rule. Its control (start moved 0.001 mm) is reported at 0.701 mm under both (`verified` by running).

## 4. Case geometry for Agent 3

The helpers are those of `tests/unit/drc/layouts.py`: `RULES` (trace and via rule 0.2 mm), `line` and `arc` 0.2 mm
wide, `via` with `pad_mm` 0.6 and net `A` unless given. Every expected result below is `verified` by running
`u_d24_cases.py` under the U-D24 reading, and the "main" column under main 14c8b7a.

| Case | Layout | Expected, U-D24 | Main 14c8b7a |
|---|---|---|---|
| 5i | coil `path(0, [line(-5, 0, 0, 0), line(0, 0, 0, 2)])`, via 0 at (0, 2) role TERMINAL, leg `path(1, [line(0, 2, -5, 0.39)])`, all net A | exactly `trace_trace` (`path:0/prim:0`, `path:1/prim:0`) at 0.19 | none: blind |
| 5j | 5i with the leg ending at (-5, 0.41) | none | none |
| 5k | trunk `path(0, [line(-5, 0, 4.5, 0), fillet arc(4.5, 0.5, 0.5, -pi/2, pi/2), line(5, 0.5, 5, 5)])`, branch `path(1, [line(4.4, -4, 4.4, 0)])` | none | none |
| 5l | trunk `path(0, [line(-5, 0, 5, 0), line(5, 0, 5, -2), line(5, -2, x, -2)])`, branch `path(1, [line(0, 0, 0, -4)])`; x = 0.39, then 0.41 | x = 0.39: exactly (`path:0/prim:2`, `path:1/prim:0`) at 0.19; x = 0.41: none | none for both: blind |
| 2e | `path(0, [line(-5, 0, 0, 0), line(0, 0, 0, 5)], net="N")` as interconnect, `via(0, -0.2, 0, net="PHASE_A")` | none | none |
| 2f | `path(0, [line(-5, 0, 5, 0), line(5, 0, 5, h), line(5, h, -5, h)], net="N")` as interconnect, `via(0, 0, 0, net="PHASE_A")`; h = 0.59, then 0.61 | h = 0.59: exactly `trace_via` (`path:0/prim:2`, `via:0`) at 0.19; h = 0.61: none | none for both: blind |
| 5f (inverts) | as on main | `trace_trace` (`path:0/prim:1`, `path:1/prim:0`) at -0.15 | none |
| 5g (inverts) | as on main, both parametrisations | `trace_trace` (`path:0/prim:1`, `path:1/prim:0`) at 0.0 | none |

In 5k the branch end lies 0.1 mm before the fillet, so its copper overlaps the fillet by 0.1 mm. The reading that
exempts the landing primitive alone reports that pair at -0.100 mm. In 2e the via centre lies 0.2 mm from the second
line's centreline, inside the 0.3 mm band, so an implementation that exempts only the nearest primitive reports the
pair at -0.200 mm (`inferred` from the geometry, not run).

The two UT-DRC-04 items that invert are `test_ut_drc_04_junction_end_group_is_exempt_from_the_whole_trunk_path` (5f)
and `test_ut_drc_04_path_end_on_an_end_point_of_a_same_net_path_is_exempt_from_every_primitive_of_it` (5g). With the
U-D24 reading in place, `pytest tests/unit/drc/test_run_drc.py -k ut_drc_04` gives 3 failed (those two, one of them
twice by parametrisation) and 27 passed (`verified` by running, with the plugin `u_d24_reading.py` of section 7).

## 5. What changes in code and models (for the implementing units)

- Agent 3, `src/embodic/drc/items.py`. `_junctions` exempts the end group from the landing group of each hit primitive,
  not from the whole path. `_taps` drops the whole-path step (`tapped_rings`), so `exempt = within` for every
  candidate. The `exempt_pairs` docstring follows. `tests/unit/drc/test_run_drc.py` gains 2e, 2f and 5i to 5l, and
  5f and 5g change their expected results.
- Agent 4, `tests/independent/m1/drc_universe.py`. `_tees` pairs the end group with the landing group of each hit,
  and `_interconnect_taps` pairs a via with each primitive it taps, as `_via_taps` does without the net test.
  `contract_exemptions`' docstring follows.
- Not run under the U-D24 reading: `tests/unit/property/t_junctions.py` (PR-13), `tests/independent/m1/test_drc_agreement.py`,
  `tests/independent/m1/test_gr19_drc.py` and the golden helpers that import the exemption functions. A combined run
  hit its 580 s timeout on this 2-CPU machine beside the release gate and gave no result (`not tested`). PR-13 and
  the agreement tests compare the product with Agent 4's model, so they agree again only when both units land.

## 6. Questions for Fable

- Q1 (decision). Accept the sharp-corner cost of section 1: a T that lands near a sharp corner, and a tap via near a
  sharp corner of an interconnect path, are reported against the primitive past the corner. Recommendation: accept.
  Nothing shipped is affected (section 3), and a fillet at the corner removes the report.
- Q2 (decision, finding F-1). A path that starts with a fillet or taper is wider under rule 1 in the engine than in the
  contract. `main_indices` gives the leading corner piece main index 0, so its slot is 1 (`items.py` l.108-115 and
  l.133), and `abs(slot) <= 2` exempts it from main primitive 1. Rule 1 says that a fillet or taper at a path end belongs
  to one main primitive only. `verified` by running: a path of a leading taper `line(0, 0, 1, 0)`, then
  `line(1, 0, 1, 0.3)` and `line(1, 0.3, 0, 0.3)` passes `run_drc`, and the same path with a side in place of the taper
  reports `path:0/prim:0` and `path:0/prim:2` at 0.100 mm. No path of the five examples or the GR-19 layouts starts
  with a fillet or taper (`verified` by running), so it is latent. A slot test for the landing group inherits the same
  gap. Proposed fix: a leading fillet or taper takes slot -1. Fable logs the row and names the owner.
- Q3 (for Agent 4). `_interconnect_taps` runs over every land, pads included (`drc_universe.py` l.45 `_LANDS`, l.280-288),
  while §7 and `_taps` name vias only. That the model is wider than the contract for a pad on an interconnect
  centreline is `inferred` by reading, not run.
- Q4 (text outside this unit's sections). `test_plan.md` §5 l.300 and `interfaces.md` §13 point 13 still say that U-M5f
  adds cases 5e and 5f for the end-point reading. Both are dated notes, and the U-D24 notes supersede them. This unit
  did not add a line to the revision list at the top of `test_plan.md`, because U-S16 edits that file in parallel and
  this unit's write scope there is the UT-DRC-04 row.
- Q5 (release). D-078 c fixes this before the next release. The contract change alone changes no verdict on the five
  examples, so the 0.0.4 notes need no DRC count change if Agent 3's code matches section 3.

## 7. The levers

Run from a worktree root on main 14c8b7a with the dev venv, for example
`PYTHONPATH=src:<dir of the scripts> python <dir>/u_d24_probe.py --gr19`. The scripts replace functions of
`embodic.drc.items` in memory only. They are a measurement for this ruling, not tests.

`u_d24_probe.py`, the readings, the board sweep and the D08 mutant:

```python
"""U-D24 probe: run_drc under narrowed rule 5 and rule 2 tap readings (scratch measurement, not a test).

Usage, from a worktree root with the dev venv:  PYTHONPATH=src python u_d24_probe.py [--gr19]

For each packaged example (and with --gr19 the three GR-19 Xcoil layouts in the product DRC reading) it reports, per
reading, the violation count, the violations that are new against the contract reading of main 14c8b7a, and the pairs
whose exemption the reading drops, with the least clearance among them against the rule. The readings replace
``_junctions`` or ``_taps`` in ``embodic.drc.items``; ``exempt_pairs`` and the engine are unchanged.
"""

import argparse
import dataclasses
import math
import sys
from pathlib import Path

import numpy as np

from embodic.api import compute_project
from embodic.drc import engine as E
from embodic.drc import items as I
from embodic.drc.engine import run_drc
from embodic.geometry.paths import COINCIDENCE_MM

ROOT = Path.cwd()
ORIGINAL_JUNCTIONS, ORIGINAL_TAPS = I._junctions, I._taps


def junctions_window(window: int | None, skip_trunk_ends: bool):
    """Rule 5 per primitive: each trunk primitive the end lies on, with the trunk primitives whose slot is within
    ``window`` of it (None: only the hit primitives). ``skip_trunk_ends`` drops hits at the trunk's own end points."""

    def _junctions(layout, items, first_item, ends):
        groups = {}
        for path in layout.paths:
            groups.setdefault((path.layer, path.net), []).append(path)
        for (layer, net), paths in groups.items():
            if len(paths) < 2:
                continue
            trace = np.concatenate([np.arange(first_item[p.id], first_item[p.id] + len(p.primitives)) for p in paths])
            owner = items.path[trace]
            path_end_points = {
                p.id: (p.primitives[0].start_point(), p.primitives[-1].end_point()) for p in paths if p.primitives
            }
            for e in (e for e in ends if e.path.layer == layer and e.path.net == net):
                distance_mm = I._centreline_distance_mm(items, trace, *e.point)
                hit = (distance_mm <= COINCIDENCE_MM) & (owner != e.path.id)
                if skip_trunk_ends:
                    at_end = np.array(
                        [any(math.dist(e.point, q) <= COINCIDENCE_MM for q in path_end_points[int(o)]) for o in owner]
                    )
                    hit &= ~at_end
                exempt = np.zeros(len(trace), dtype=bool)
                for k in np.flatnonzero(hit):
                    same = owner == owner[k]
                    if window is None:
                        exempt[k] = True
                    else:
                        exempt |= same & (np.abs(items.slot[trace] - items.slot[trace[k]]) <= window)
                yield from ((i, int(j)) for j in trace[exempt] for i in e.group)

    return _junctions


def taps_per_primitive(layout, items, interconnects, via_base):
    """Rule 2 tap per primitive: rule 2b with the net test waived for interconnect paths."""
    traces = np.flatnonzero(items.item_class == I.ItemClass.TRACE)
    net_of = {path.id: path.net for path in layout.paths}
    trace_net = np.array([net_of[int(i)] for i in items.path[traces]])
    interconnect = np.isin(items.path[traces], list(interconnects))
    for v, via in enumerate(layout.vias):
        candidates = traces[interconnect | (trace_net == via.net)]
        within = I._centreline_distance_mm(items, candidates, via.x_mm, via.y_mm) <= via.pad_mm / 2
        yield from ((via_base + v, int(i)) for i in candidates[within])


READINGS = {
    "contract 14c8b7a": (ORIGINAL_JUNCTIONS, ORIGINAL_TAPS),
    "r5 window 1 (main with its fillets and tapers)": (junctions_window(1, False), ORIGINAL_TAPS),
    "r5 window 1, trunk end points to rule 3": (junctions_window(1, True), ORIGINAL_TAPS),
    "r5 window 2 (rule 1 neighbours)": (junctions_window(2, False), ORIGINAL_TAPS),
    "r5 hit primitive only": (junctions_window(None, False), ORIGINAL_TAPS),
    "tap per primitive": (ORIGINAL_JUNCTIONS, taps_per_primitive),
    "r5 window 1 + tap per primitive": (junctions_window(1, False), taps_per_primitive),
}


def _use(reading: str) -> None:
    I._junctions, I._taps = READINGS[reading]


def _exempt(layout):
    items, first = I.build_items(layout)
    return items, set(I.exempt_pairs(layout, items, first).tolist())


def _lost_pairs(layout, rules, items, keys):
    """Clearance of each pair whose exemption a reading drops, minus its rule (only pairs a check applies to)."""
    n = len(items)
    a = np.array([k // n for k in keys], dtype=np.int64)
    b = np.array([k % n for k in keys], dtype=np.int64)
    same_layer = (items.layer[a] == items.layer[b]) | (items.layer[a] == I.EVERY_LAYER) | (
        items.layer[b] == I.EVERY_LAYER
    )
    kind = E._KIND_TABLE[items.item_class[a], items.item_class[b]]
    keep = same_layer & (kind != E._NO_KIND)
    a, b, kind = a[keep], b[keep], kind[keep]
    if len(a) == 0:
        return []
    clearance, _ = E._measure(items, layout, a, b, kind)
    required = E._required(rules)[kind]
    rows = sorted(zip(clearance - required, a, b, clearance, strict=True))
    return [(items.labels[i], items.labels[j], float(c), float(m)) for m, i, j, c in rows]


def probe(name: str, layouts, rules, show: int) -> None:
    print(f"== {name}")
    for board, layout in enumerate(layouts):
        _use("contract 14c8b7a")
        items, base_exempt = _exempt(layout)
        base = run_drc(layout, rules)
        base_set = {v.objects for v in base.violations}
        for reading in READINGS:
            _use(reading)
            _, exempt = _exempt(layout)
            report = run_drc(layout, rules)
            plain = run_drc(layout, rules, use_symmetry=False)
            new = sorted({v.objects for v in report.violations} - base_set)
            gone = sorted(base_set - {v.objects for v in report.violations})
            lost = _lost_pairs(layout, rules, items, sorted(base_exempt - exempt))
            least = f"least margin {lost[0][3]:+.3e} mm ({lost[0][0]} / {lost[0][1]}, clearance {lost[0][2]:.6f})" if lost else ""
            print(
                f"  board {board} | {reading}: violations {report.violation_count} (no symmetry {plain.violation_count});"
                f" new {len(new)}, gone {len(gone)}; exemptions dropped {len(base_exempt - exempt)},"
                f" checkable {len(lost)}; {least}"
            )
            for row in new[:show]:
                hit = next(v for v in report.violations if v.objects == row)
                print(f"      NEW {row} clearance {hit.clearance_mm:.6f} rule {hit.required_mm}")
            if reading.startswith("tap") or reading.endswith("tap per primitive"):
                for row in lost[:show]:
                    print(f"      dropped {row[0]} / {row[1]} clearance {row[2]:.6f} margin {row[3]:+.3e}")
    _use("contract 14c8b7a")


def leg_mutant(layout, leg_id: int, width_mm: float, start_shift_mm: float):
    """U-V16's DEF-UV16-01 mutant (u_v16_spots.py ``_leg_mutant``), reproduced."""
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gr19", action="store_true")
    parser.add_argument("--show", type=int, default=8)
    args = parser.parse_args()
    examples = sorted((ROOT / "resources" / "examples").glob("*.embodic.json"))
    for path in examples:
        outcome = compute_project(path)
        probe(path.name.split(".")[0], list(outcome.boards.boards), outcome.design.drc_rules, args.show)
        if path.name.startswith("spiral_12c10p_d08"):
            layout, rules = outcome.boards.boards[0], outcome.design.drc_rules
            for reading in ("contract 14c8b7a", "r5 window 1 (main with its fillets and tapers)"):
                _use(reading)
                for shift in (0.0, 0.001):
                    report = run_drc(leg_mutant(layout, 25, 0.8, shift), rules, use_symmetry=False)
                    hits = [(v.objects, round(v.clearance_mm, 6)) for v in report.violations if "path:25/prim:0" in v.objects]
                    print(f"  DEF-UV16-01 mutant | {reading} | start shift {shift}: passed {report.passed}, leg 25 hits {hits}")
            _use("contract 14c8b7a")
    if args.gr19:
        sys.path.insert(0, str(ROOT / "tests" / "golden"))
        from harness import load_area
        from m1_layout.xcoil_map import layout_from_xcoil, split_ic_chains

        from embodic.model.drc_rules import DrcRules

        for case_name, case in load_area("m1_layout").items():
            raw = case.calls[0].output
            c = raw["params"]["clearance"]
            rules = DrcRules(
                trace_clearance_mm=c, via_clearance_mm=c, edge_clearance_mm=c, hole_clearance_mm=c,
                min_trace_width_mm=0.1, min_drill_mm=0.2, min_annular_ring_mm=0.1,
            )  # fmt: skip
            probe(f"GR-19 {case_name}", [layout_from_xcoil(split_ic_chains(raw))], rules, args.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`u_d24_cases.py`, the hand-built cases of section 4 under four readings:

```python
"""U-D24: the proposed UT-DRC-04 cases under the contract of 14c8b7a and under the U-D24 reading (scratch check).

Usage, from a worktree root:  PYTHONPATH=src python u_d24_cases.py
"""

import math
import sys
from dataclasses import replace
from itertools import pairwise
from pathlib import Path

sys.path.insert(0, "tests/unit/drc")
sys.path.insert(0, str(Path(__file__).parent))

from layouts import RULES, arc, layout, line, path, via  # noqa: E402
from u_d24_probe import READINGS, _use  # noqa: E402

from embodic.drc import run_drc  # noqa: E402
from embodic.geometry.layout import ViaRole  # noqa: E402
from embodic.geometry.primitives import PrimitiveRole  # noqa: E402

NEW = "r5 window 1 + tap per primitive"
STRICT = "r5 hit primitive only"
W2 = "r5 window 2 (rule 1 neighbours)"


def coil_end_and_leg(inside: bool):
    """5i/5j: a coil's turn and stub end on via 0; a leg starts there and runs back past the turn."""
    y = 0.39 if inside else 0.41
    coil = path(0, [line(-5, 0, 0, 0), line(0, 0, 0, 2)], net="A")
    leg = path(1, [line(0, 2, -5, y)], net="A")
    return layout(paths=[coil, leg], vias=[via(0, 0, 2, net="A", role=ViaRole.TERMINAL)])


def tee_by_a_fillet():
    """5k: a branch lands on main0 0.1 mm before the corner fillet; its copper overlaps the fillet."""
    fillet = replace(arc(4.5, 0.5, 0.5, -math.pi / 2, math.pi / 2), role=PrimitiveRole.FILLET)
    trunk = path(0, [line(-5, 0, 4.5, 0), fillet, line(5, 0.5, 5, 5)], net="A")
    branch = path(1, [line(4.4, -4, 4.4, 0)], net="A")
    return layout(paths=[trunk, branch])


def tee_on_a_u_turn(inside: bool):
    """5l: a branch on the middle of main0; the trunk turns back and main2 ends beside the branch."""
    x = 0.39 if inside else 0.41
    trunk = path(0, [line(-5, 0, 5, 0), line(5, 0, 5, -2), line(5, -2, x, -2)], net="A")
    branch = path(1, [line(0, 0, 0, -4)], net="A")
    return layout(paths=[trunk, branch])


def tap_near_a_vertex():
    """2e: an N interconnect with a corner; a PHASE_A via on main0 0.2 mm before it, inside pad/2 of both lines."""
    ring = path(0, [line(-5, 0, 0, 0), line(0, 0, 0, 5)], net="N")
    return layout(paths=[ring], vias=[via(0, -0.2, 0, net="PHASE_A")], interconnects=[0])


def tap_on_a_u_turn(inside: bool):
    """2f: an N interconnect U-turn tapped mid-main0 by a PHASE_A via; main2 returns past the via."""
    h = 0.59 if inside else 0.61
    ring = path(0, [line(-5, 0, 5, 0), line(5, 0, 5, h), line(5, h, -5, h)], net="N")
    return layout(paths=[ring], vias=[via(0, 0, 0, net="PHASE_A")], interconnects=[0])


_HOOK = [(0.0, 0.0), (0.0, 2.0), (4.0, 2.0), (4.0, 5.0)]


def hook(net: str, at_start: bool):
    """5g/5h on main: test_run_drc.py ``_hook_and_branch``."""
    points = _HOOK if at_start else _HOOK[::-1]
    trunk = path(0, [line(*a, *b) for a, b in pairwise(points)], net="A")
    return layout(paths=[trunk, path(1, [line(0.5, 1.8, 0.0, 0.0)], net=net)])


def sharp_corner():
    """5f on main: test_run_drc.py ``test_ut_drc_04_junction_end_group_is_exempt_from_the_whole_trunk_path``."""
    trunk = path(0, [line(-5, 0, 0, 0), line(0, 0, 0, -5)], net="A")
    return layout(paths=[trunk, path(1, [line(-0.05, 4, -0.05, 0)], net="A")])


CASES = {
    "5i coil end, leg 0.01 inside the rule of the turn": coil_end_and_leg(True),
    "5j coil end, leg 0.01 outside (the designed joint)": coil_end_and_leg(False),
    "5k mid-path T by a fillet": tee_by_a_fillet(),
    "5l mid-path T, return main 0.01 inside": tee_on_a_u_turn(True),
    "5l control, return main 0.01 outside": tee_on_a_u_turn(False),
    "2e tap 0.2 mm before a vertex": tap_near_a_vertex(),
    "2f tap, return main 0.01 inside": tap_on_a_u_turn(True),
    "2f control, return main 0.01 outside": tap_on_a_u_turn(False),
    "5f (main) T 0.05 before a sharp corner": sharp_corner(),
    "5g (main) hook, trunk start": hook("A", True),
    "5g (main) hook, trunk end": hook("A", False),
    "5h (main) hook, other net, trunk start": hook("B", True),
}

for name, board in CASES.items():
    print(name)
    for reading in ("contract 14c8b7a", NEW, STRICT, W2):
        _use(reading)
        report = run_drc(board, RULES)
        rows = sorted((v.kind.value, v.objects, round(v.clearance_mm, 6)) for v in report.violations)
        print(f"   {reading:34s} {rows}")
_use("contract 14c8b7a")
```

`u_d24_reading.py`, a pytest plugin (`-p u_d24_reading`) that puts the U-D24 reading in place before collection:

```python
"""pytest plugin: replace rule 5 and the rule 2 tap with the U-D24 reading before any test runs (scratch only)."""
from embodic.drc import items
from u_d24_probe import junctions_window, taps_per_primitive

items._junctions = junctions_window(1, False)
items._taps = taps_per_primitive
```
