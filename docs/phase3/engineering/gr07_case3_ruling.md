Prepared by: Agent 2 (Motor Design Expert), model: claude-opus-5-5

# GR-07 case 3: embodic refuses a board thinner than its copper (U-E15, DEF-U-M6h-01)

Date 2026-10-17. Worktree base main 7d34543. Every number below comes from
`docs/phase3/engineering/checks/gr07_case3_probe.py` unless another source is named. Run it from the repository root:

```
PYTHONPATH=src /home/claude/embodic/.venv/bin/python docs/phase3/engineering/checks/gr07_case3_probe.py
```

## Ruling

Option (a). embodic refuses 8 copper layers of 2 oz on a 0.4 mm board with a validation ERROR. embodic does not
follow Xcoil (option c), and it does not grow the board (option b). Status: `inferred` (a reasoned engineering ruling
from the facts below, which are `verified` by reading or by running the probe).

The rule: the even stack-up generator accepts its inputs only when the board thickness B exceeds the copper total,
B > n × t, for n copper layers of thickness t. Each even dielectric is (B − n × t) / (n − 1), or B − t for one layer
(`src/embodic/model/stackup.py` l.84 and l.89, l.77), so the rule is the same as "every dielectric is thicker than 0".

## Why the design cannot be built

- The copper alone is 8 × 0.0696 mm = 0.5568 mm, which is 0.1568 mm more than the 0.4 mm board (`verified`, probe
  line "B - n*t mm" = −0.1568). 2 oz is 2 × 0.0348 mm (`src/embodic/units.py` l.21, Xcoil `engine.js` l.14). The
  brief's "8 × 0.07 mm = 0.56 mm" is the same figure rounded.
- Copper layers are separated by dielectric layers of non-zero thickness in every real stack-up in the corpus: prepreg
  0.07 mm and laminate 0.13 mm and 0.15 mm (D01 p.4 Table 4, EV-22, `docs/phase1/evidence/evidence_register.md` l.64,
  `verified` there), and 71 µm prepreg with a 100 µm core in the repository record
  (`docs/phase1/engineering/existing_logic_review.md` l.21). These are examples, not minimum thicknesses.
- A dielectric of 0 mm puts copper on copper, so neighbouring layers touch and are electrically joined (`inferred`; no
  corpus source states it). Xcoil's own layer capacitance cannot evaluate a 0 mm gap: it replaces the distance with
  1 µm (`engine.js` l.1184, `d = Math.max(1e-6, e.t * 1e-3)`, `verified` by reading).
- The manufacturable minimum dielectric is `unresolved`. No PCB fabrication standard is in the corpus, and IPC-2221 is
  cited only second-hand (gap G5, `docs/phase1/evidence/evidence_gaps.md` l.74; UD-23). The rule above uses only the physical floor of 0 mm. It is not
  a fabrication rule, and a board that passes it can still be unbuildable at a given fabricator.

The verdict depends only on the sign of B − n × t. Eight layers fit in 0.4 mm only when t < 0.05 mm, which is
1.437 oz (probe). The question whether 1 oz is 34.8 µm or 35 µm therefore cannot change this ruling.

## Why not option (c), follow Xcoil

Xcoil `stackupFor` keeps the input board thickness (l.1177) and spaces the layer centres 0.0472 mm apart (l.1170),
less than the 0.0696 mm copper thickness. Each layer overlaps its neighbour by 0.0224 mm (probe, "pitch - t mm").
Xcoil then clamps each gap to 0 (l.1174 to l.1175), so its entry list sums to 0.5568 mm while it reports 0.4 mm. The
probe shows that this inconsistency appears only when B − n × t ≤ 0: on the ten case-1 fixtures the entry sum equals
the board thickness within 4.44e-16 mm, and on the thin case it differs by 0.1568 mm. Xcoil's input check bounds the
board thickness to 0.2 to 10 mm (l.127) and has no rule on the copper total (`verified` by reading every
`boardThickness` use in `engine.js`).

embodic cannot hold that state. REQ-F-04 requires that the board thickness is the sum of the layers
(`docs/phase2/architecture/requirements.md` l.73), and `Stackup.copper_z_mm()` is an exact cumulative sum
(`stackup.py` l.40 to l.48). Xcoil also carries the overlap downstream, for example into the via barrel length
`hAdj = |z1 − z0|` (`engine.js` l.2209 and l.2470), which here is 0.0472 mm, less than one copper thickness.

## Why not option (b), keep the thicker stack

The helper output is the same unbuildable copper with seven 0 mm dielectrics (probe, "dielectrics [0.0, ...]"). It
also replaces the user's 0.4 mm with 0.5568 mm, which is +39.2 %. The view-model then reads the board thickness back as
the sum of the layers (`src/embodic/ui/viewmodels/session.py` l.485), so the entered value changes without a message
(`inferred` by reading; not run in the UI). The board thickness feeds the via barrel resistance, the stack thickness
and the symmetry plane of the analysis (`docs/phase2/architecture/interfaces.md` l.779, l.2105 and l.2957). Every one
of those results would describe a board that the user did not enter and that cannot be made.

The fault is the clamp `max(0.0, dielectric_mm)` in `stackup.py` l.81 and l.91. It turns an infeasible input into a
stack that looks valid. The field table has the same gap for hand-edited lists: a dielectric thickness may be 0
(`src/embodic/model/fields.py` l.216, `NONNEG`), and `validate._stackup` checks only for copper and duplicate names
(`src/embodic/model/validate.py` l.291 to l.298).

## Proposed change (for the code owner, Agent 3; text by Agent 1)

1. New issue code `INVALID_STACKUP_COPPER_EXCEEDS_BOARD`, severity ERROR, category INVALID from its prefix
   (`validate.py` l.34). Condition: B ≤ n × t, with n × t summed by `math.fsum`. Fields: `value` = B, `limit` = n × t,
   `unit` = `Unit.MM`, pointer `/stackup/layers` (the list the generator writes, `docs/phase2/design/screens.md` R3).
   Proposed message, in the style of `INVALID_NON_POSITIVE` (`src/embodic/errors/catalogue/model.py` l.14):
   "Board thickness must exceed the total copper thickness of {limit}{unit}, so that every dielectric layer is
   thicker than 0."
2. `session.set_stackup_input` (`session.py` l.915 to l.927) checks the three inputs before it calls
   `generate_even_stackup`. On the ERROR it writes nothing and shows the issue at `param-board-thickness`.
3. `generate_even_stackup` drops both clamps and raises `ValueError` when B ≤ n × t. That is a programming error
   because the caller checked first, so REQ-F-14 (user input yields issues) still holds.
4. Same fault, other path: the dielectric thickness limit in `fields.py` l.216 becomes `POS`, so a 0 mm dielectric in a
   hand-edited list yields the existing `INVALID_NON_POSITIVE` at its own pointer. No shipped or test JSON design holds
   one: a scan of the JSON files under `resources/` and `tests/` found 9 dielectric layers, none at 0 mm or below
   (`verified` over JSON files; designs built in Python test code were not scanned).

## What GR-07 case 3 asserts after the change

Case 3 stops comparing embodic's values with Xcoil's, because Xcoil's output for this input is not physical. No
expected-difference (XD) entry is needed: the case does not go through `golden_report`. The GR-07 row of
`docs/phase2/architecture/test_plan.md` l.276 states the reason instead.

1. The committed Xcoil fixture `stackupfor-auto-thin-8cu-2oz-0p4mm` stays as the record. The test asserts its
   inconsistency within 1e-12 mm absolute: the sum of its entries minus its `boardThickness` equals 8 × 0.0696 − 0.4,
   and its layer-centre pitch is less than its copper thickness.
2. The input check for (8, 0.0696 mm, 0.4 mm) returns one ERROR `INVALID_STACKUP_COPPER_EXCEEDS_BOARD` with `value`
   0.4 and `limit` equal to `math.fsum([0.0696] * 8)` within 1e-12 mm.
3. At the boundary, B = n × t exactly is refused. B = n × t + 1e-6 mm gives no issue, and the helper's dielectrics
   are all greater than 0 and sum with the copper to B within 1e-12 mm.
4. `generate_even_stackup(8, 0.0696, 0.4)` raises `ValueError`. This assertion fails if a clamp returns.
5. Optional, to pin agreement near the boundary: a new Xcoil fixture of 8 × 2 oz on 0.6 mm (B − n × t = 0.0432 mm)
   compared as in case 1. Case 1 covers margins of 1.0432 mm and more only.

The `INVALID_NON_POSITIVE` rule on a hand-edited 0 mm dielectric is a unit test of the validation module, not part of
GR-07.

## The 2 oz constant matches the registry

Yes (`verified` by reading and by the probe's first line). The registry's EQ-10 text states "1 oz = 34.8 µm
`assumption`" (`docs/phase2/engineering/equation_specification.md` l.237). The same 0.0348 mm per oz is in
`src/embodic/units.py` l.21 (`MM_PER_COPPER_OZ`, status `assumption`), the GR-07 test's `OZ_TO_MM`
(`tests/golden/m2_stackup/test_gr07_even_stackup.py` l.26), the CF case inputs (`oracle_cases.json` l.1134) and
Xcoil `engine.js` l.14. So 2 oz is 0.0696 mm everywhere. The value itself stays an `assumption`: finished copper
thickness depends on the supplier (EQ-10 limitations, `equation_specification.md` l.240). The registry holds the value
only as text; no `constants` row of any equation carries it (registry read in this unit).
