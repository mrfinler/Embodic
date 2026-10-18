Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# Fix wave F3 rulings (U-S13)

Date 2026-10-18. Main 6319959. Decision D-058. This document rules three small items of wave F4: the `preview-timer`
finding of `screens_coverage.py`, the bounds of the two stack-up helper inputs, and the reading of `fix_wave_f2.md` (b)
rule 4. Each section gives the decision, its sources and an acceptance that Agent 3 can run.

Every claim carries one status label. `verified` means read in the named source or reproduced by running something
here. Two probes of this unit ran with `/home/claude/embodic/.venv/bin/python` on the worktree source. One calls
`stepped_text` with the rules on main and with the proposed helper rules. The other builds the real window offscreen.
Neither is committed. Their output is quoted where a ruling rests on it.

## (a) `preview-timer` takes a row in screens.md section 14a

### Decision

A non-visual object that the UI code gives a literal objectName takes a row in screens.md section 14a, like a widget.
The check stays as it is. `preview-timer` is the single-shot `QTimer` of `QtDebounce` (`src/embodic/ui/views/debounce.py`
l.15 to l.18, `verified` by reading). Its row says that it is not a widget, so it has no accessible name, no style and no
tab stop. An offscreen probe built the real window with `create_shell` and printed (`verified` by running):

```
window: main-window | timer: True | interval: 300 | single shot: True | is a widget: False
```

### Why a row and not a skip in the check

- The name is a contract. `tests/ui/qt_shell/typing_support.py` l.85 finds the timer with
  `window.findChild(QTimer, "preview-timer")` (`verified` by reading). A rename in the code breaks that test, and the row
  puts the name where the screens owner and the check can see it.
- The check reads the source text with a regular expression (`screens_coverage.py` l.35 and l.117 to l.119). It cannot
  tell a `QTimer` from a `QWidget` without building the UI. A skip would need a list of names inside the check, which is
  a second register beside screens.md.
- The row costs one line. This follows the laziness protocol, with one register of names and no change to the check.

### Changes

screens.md section 14a gets one sentence that admits non-visual objects and a table with the `preview-timer` row
(revision 2026-10-18, U-S13).

### Acceptance

| Id | Steps | Pass |
|---|---|---|
| A-1 | From the repository root, run `.venv/bin/python docs/phase2/design/checks/screens_coverage.py`. | Prints "no findings" and exits 0. |

Before the row (`verified` by running in this worktree):

```
193 objectNames, 105 binding pointers, blank-draft required: spiral 37, serpentine 35, wave 35
UI code sets an objectName no screens.md table defines: preview-timer
exit 1
```

After the row (`verified` by running in this worktree):

```
194 objectNames, 105 binding pointers, blank-draft required: spiral 37, serpentine 35, wave 35
no findings
exit 0
```

## (b) Bounds of the two stack-up helper inputs

### Decision

| Input | Sign | Low | High | Step (Shift: ten steps) | Source of the bounds |
|---|---|---|---|---|---|
| `param-copper-weight` | POSITIVE | 0.25 oz | 10 oz | 0.5 oz (5 oz) | The field it derives |
| `param-board-thickness` | POSITIVE | 0.2 mm | 10 mm | 0.1 mm (1 mm) | Xcoil |

`low` and `high` include their ends, as for every field (`fix_wave_f2.md` (b), "Arithmetic and bounds"). Rules 1 to 4 of
that section apply unchanged, with rule 4 as section (c) below reads it.

Copper weight. The generator writes `/stackup/layers/*/thickness_mm#copper`, whose `Limits` are
`_lim(POS, 0.25 * MM_PER_COPPER_OZ, 10 * MM_PER_COPPER_OZ)` (`src/embodic/model/fields.py` l.215 to l.217, `verified` by
reading). In the unit the form shows, that is 0.25 oz to 10 oz. Dividing the limits by `MM_PER_COPPER_OZ` (0.0348) gives
0.25 and 10.0 exactly (`verified` by running). Xcoil uses the same range for both of its copper inputs,
`num('copperOzOuter', 0.25, 10); num('copperOzInner', 0.25, 10);` (`/home/claude/serpentine/src/engine.js` l.126,
`verified` by reading).

Board thickness. The derived fields give no fixed bound. The dielectric thickness is POSITIVE with no range
(`fields.py` l.218), and "the board is thicker than its copper" (D-053a, `src/embodic/model/validate.py` l.377 to l.391)
depends on the copper count and weight (`verified` by reading). The bounds therefore come from Xcoil,
`num('boardThickness', 0.2, 10);` (`engine.js` l.127, `verified` by reading). In Xcoil, `num` reports a value outside
the range as `RANGE` and clamps it (`engine.js` l.112 to l.118), which is the meaning of `Limits` here (`fields.py` l.57).
The D-053a relation stays a message at commit in `param-board-thickness-error`. A step does not stop at it, because a
step never writes a message (`fix_wave_f2.md` (b)).

D-030 gives no bound for either input. It names the trace width, the clearance and the turn count
(`docs/decision_log.md` l.36, `verified` by reading).

The steps now have a source as well. Xcoil gives `step: 0.5` for both copper inputs and `step: 0.1` for the board
thickness (`/home/claude/serpentine/src/ui.js` l.102 to l.104, `verified` by reading). These equal the steps that
`fix_wave_f2.md` (b) set as `assumption`, so their status becomes `verified` by reading.

### Changes for Agent 3

- `src/embodic/ui/viewmodels/stepping.py` l.82 to l.86: give both rules `sign=Sign.POSITIVE` and the bounds above. Take
  the copper weight bounds from `FIELD_BY_KEY["/stackup/layers/*/thickness_mm#copper"].limits` divided by
  `MM_PER_COPPER_OZ`, so the two cannot drift apart. Write the board thickness bounds as constants that cite
  `engine.js` l.127. Replace the comment "Neither has limits".
- `tests/unit/ui/session/test_stepping.py` l.127: `test_a_field_without_limits_steps_without_bounds` says the two
  stack-up inputs have no limits. Keep the case for a rule without limits, drop the claim about the inputs, and add rows
  B-1 to B-9.

### Acceptance (Qt-free, `stepped_text` with `STACKUP_INPUT_RULES`)

The expected texts follow from the rules above. The probe gave each of them for `StepRule` values built with these bounds
(`verified` by running). The rules on main do not have the bounds yet.

| Id | Input | Text, steps | Pass |
|---|---|---|---|
| B-1 | `param-copper-weight` | "0.5", -1 | "0.25" |
| B-2 | `param-copper-weight` | "0.25", -1 | unchanged (None) |
| B-3 | `param-copper-weight` | "9.8", +1 | "10" |
| B-4 | `param-copper-weight` | "0.1", +1 | "0.6" |
| B-5 | `param-copper-weight` | "12", +1, then "12", -1 | unchanged, then "10" |
| B-6 | `param-board-thickness` | "0.25", -1 | "0.2" |
| B-7 | `param-board-thickness` | "0.1", -1, then "0.1", +1 | unchanged, then "0.2" |
| B-8 | `param-board-thickness` | "9.95", +10 | "10" |
| B-9 | `param-board-thickness` | "12", -1 | "10" |

## (c) A step from outside the range that lands in range shows the stepped number

### Decision

U-M8f's reading is correct. A number outside the range that one step brings into range shows the stepped number: with
`param-air-gap` (POSITIVE, `low` 0.05, step 0.05), 0.01 and Up give 0.06, not 0.05. This corrects the wording of
`fix_wave_f2.md` (b) rule 4, not its intent.

### Why

- The rules are tried in order, and rule 1 has no exception for a number that starts outside the range. Rule 4 covers
  the case that rule 3 would freeze, a step toward the range that stays outside. Row S-7 of `fix_wave_f2.md` shows it:
  60 and Down give 50 (`param-air-gap`, `high` 50).
- Experience first. The key moves by the step that the shortcut list shows, which was the default of `fix_wave_f2.md`
  Q2. A jump to the bound would move 0.01 by 0.04, a number the user never chose. The bound appears only when the step
  alone cannot reach the range.

### Corrected rule 4

This text replaces rule 4 of `fix_wave_f2.md` (b). Rules 1 to 3 stay as written.

4. A number already outside the range. Rule 1 applies first, so a step that lands in range shows the stepped number. A
   step toward the range that stays outside shows the nearest valid bound. A step away from the range does not change
   the number. If the field has no valid bound on that side, as for POSITIVE with no `low`, the field changes only when
   the step lands in range.

No numeric field has a range narrower than ten of its steps (`verified` by running over `FIELDS`), so a step from
outside never jumps over the whole range, and "nearest valid bound" names one number.

Main already does this. `_move` tries the stepped number first (`src/embodic/ui/viewmodels/stepping.py` l.71 to l.79),
and `tests/unit/ui/session/test_stepping.py` l.115 to l.117 asserts 0.01 and Up give 0.06 (`verified` by reading). The
probe gave these texts on main (`verified` by running):

```
air gap '0.01' +1 -> '0.06'
air gap '0.01' +10 -> '0.51'
air gap '60' +1 -> None
air gap '60' -1 -> '50'
r_inner '-1' +1 -> None
r_inner '-1' +10 -> '4'
```

### Acceptance (offscreen, Qt test, as S-1 to S-12 of `fix_wave_f2.md` (b))

| Id | Steps | Pass |
|---|---|---|
| S-13 | Type "0.01" into `param-air-gap`, press Up. Type "0.01" again, press Shift+Up. | "0.06", then "0.51". |
| S-14 | Type "-1" into `param-r-inner` (spiral, POSITIVE, no `low`, step 0.5), press Up, then Shift+Up. | "-1" after Up, "4" after Shift+Up. |

## Defects found

| Id | Severity | Defect | Reproduce | Status |
|---|---|---|---|---|
| DEF-US13-01 | minor | Down in a stack-up helper input goes below zero: copper weight 0.2 oz gives -0.3 oz, board thickness 0.05 mm gives -0.05 mm. What a commit of such a value shows is `not tested`. | `stepped_text(STACKUP_INPUT_RULES["param-copper-weight"], "0.2", -1)` on main 6319959 returns "-0.3"; the board thickness rule with "0.05" returns "-0.05". | `verified` by running. Fixed by (b). |

## Requests to other owners (through Fable)

- Agent 3 builds the (b) changes and runs B-1 to B-9, S-13 and S-14.
- `fix_wave_f2.md` is outside this unit's scope. Fable may add a pointer under its rule 4 to section (c) of this
  document. screens.md conventions already point here.

## Open questions for Fable

- Q1. Should a commit of a board thickness outside 0.2 mm to 10 mm show a message in `param-board-thickness-error`, as
  Xcoil reports `RANGE` (`engine.js` l.116)? Default used: no. The bounds apply to stepping only, and a commit is checked
  by D-053a alone. A copper weight outside 0.25 oz to 10 oz reaches the copper `Limits` after the generator runs; which
  message the form then shows is `not tested`.
