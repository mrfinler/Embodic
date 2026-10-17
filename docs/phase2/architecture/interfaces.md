Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# embodic Phase 2 interfaces (build contract v1, 2026-10-04)

This file is the binding interface contract for Phase 2. It is written as Python stubs: every `python` block parses with
`ast.parse`, and all blocks run in order as one module (`checks/check_contract.py`). Bodies are `...`. Phase 1 types that
survive unchanged are restated here only where Phase 2 code must match them; the rationale stays in
`docs/phase1/architecture/architecture_draft.md` §7 and §8.

Revision 2026-10-04 (U-D1, corrections from the W0 pilot): §1 replaces `round_half_away_from_zero` with `js_round` and
`quantise` (JS `Math.round` semantics, DEF-M1a-02), adds the U-M1a conversions and `MM_PER_COPPER_OZ`, and splits the
issue catalogue per owning unit. §2.4 adds `default` provenance (D-019). §9.1 states how a blank-origin file stores
it. §9.2 ratifies the U-M1d number encoding and says what the Node dumper emits for GR-19.

Revision 2026-10-05 (U-D2, corrections from the W1 and W2 reports; the merged code on main a138975 was read for every
item): §1 adds the five units of DEF-M2a-01. §2.1 adds `validate_drc_rules`. §2.3 restates `FieldSpec` as merged and
names the constants that are not fields. §5 restates `Layout` with its derived hash, adds `Segment`, `discretise_path`,
`Transform`, the Xcoil distance and grid ports, and fixes the continuity tolerance at 1e-6 mm. §7 rewrites the
exemptions, fixes the clearance rule per check kind, ratifies the pad-to-pad rule and states what `measured_min_mm`
covers. §9.1 decides that the project file stores degrees. §9.2 removes the PCB-tool layer key, names the circuit phase
key and states the interim `write_board_dump` signature. §13 records D-016 and the board dump v2 needs.

Revision 2026-10-05 (U-D3, decisions D-016 and D-022, defect DEF-M1V-04): §2.2 adds `StackMode`,
`SerpentineWindingSpec.stack_mode` and `board_gap_mm` with their FIELDS rows. §5 adds `BoardStack`, one `Layout` per
board. §6, §8 and §10 take or return a `BoardStack`, and `ComputeOutcome.drc` holds one report per board. §7 narrows
the fillet exemption and adds the interconnect net waiver, with test cases per rule. §9.2 describes the board dump
`board_dump.py` writes today and its two differences from Phase 1 §7.5. §13 point 1 is closed.

Revision 2026-10-08 (U-D4, decisions D-022c, D-025, D-026 and D-031; the merged code on main c7fff3a was read for
every item): §1 adds `Unit.N_M_PER_SQRT_W` for U-M2e-4. §2.1 adds `ScrewPattern.hole_diameter_mm` (D-031a). §2.2
states the `first_coil_angle_rad` range (D-031c) and adds two FIELDS rows. §3 adds `ke_line_peak_v_s_per_rad` as
implemented and the U-M2e-4 loss-sum fields (D-031f). §4 ratifies `plan_issues` and the winding issue codes (D-031d).
§5 adds `TurnClosing` and `TurnLimit.closing` (D-031b), restates `Layout.detail` and `Layout.derived` as implemented,
and specifies the interconnect classification U-M2e-4 builds (D-031f). §7 folds D-022c into rules 2 and 3. §8
restates `embodic.physics` as merged (D-025a, D-026c, D-031f) and gives EQ-20 `phases` and `connection`. §9.1 lists the
fields added since the first draft of v1 and the schema version rule for U-M2f. §13 closes point 2, opens point 5 and
lists in point 6 the code on main that contradicts these lines, as defect rows for its owners.

Revision 2026-10-08 (U-D5, decisions D-032a, D-033b, D-033d and D-033e; the merged code on main e1536b8 was read for
every item): §4 adopts t mod a = 0 with `Feasibility.allows_parallel_paths`, renames the code to
`UNBUILDABLE_PARALLEL_PATHS_NOT_DIVISOR` and marks `Feasibility.max_parallel_paths` for removal. §5 states the via roles
of a series coil (2k + 1 vias). §6 lists the spiral generator's Unbuildable codes with the `TURNS_EXCEED_LIMIT` cause
value and the series via fan of spec G6 (U-E6). §13 closes point 5.

Revision 2026-10-08 (U-D6, the U-M2e-4 and U-M2f reports; the merged code on main a336531 was read or run for every
item): §3 states that `motor_constant_n_m_per_sqrt_w` stays in the contract and that U-M2-fix3 adds it with its unit.
§9.1 answers the three open questions of U-M2f: the provenance of a design whose origin is not packaged, unknown keys,
and what PR-12 means by "set back to default". §13 closes the PENDING list of point 2 and adds two defect rows.

Revision 2026-10-09 (U-D8, decisions D-035 to D-037; the code on main 8a297a0 was read for every item): §2.2 names
the copper-count rule of each port and corrects the XD-WAVE text. §5 closes the wave warning case. §6 lists the port
warnings in `BoardStack.issues`. §7 adds rule 2b, per primitive (D-037a), and the rule 5 end-point reading. §13 adds
point 7 (M3 items closed) and point 8 (the per-phase stack limitation of D-037b).

Revision 2026-10-09 (U-D9, claude-sonnet-5-5, D-038; the code on main 3acb044 was read for every item): §2.2 and §13
point 7 give XD-WAVE-001 and XD-WAVE-002 their status and close the via-length question (D-038b, D-038c). §3 adds the
module `embodic.results.labels` (D-038e). §9.3 states the engine version, the DRC behaviour of the PDF report, what
`write_bundle` returns, and which import of `PhaseRenderMode` is canonical (D-038d). §11 widens the
`ThemeTokens.colours` comment to the status tokens (D-038a) and names the theme generator.

Revision 2026-10-09 (U-D10, claude-sonnet-5-5, D-039 and D-040; the code on main fd190c1 was read for every item): §3 adds
`QUANTITY_SYMBOLS` and `quantity_title` and records D-040. §5 adds the shared drawing data `embodic.geometry.marks` and
`embodic.geometry.labels`. §6 adds the shared input guard `unusable_sizes` and the two codes of DEF-M3b-03. §9.1 adds
`ExampleInfo.display_note`. §9.3 adds the PDF writer's `TrueTypeFont` and `MissingGlyphError` and the drawing rules of
D-039 c. §11 adds `register_fonts`, the results rail rule below 1280 px and `ResultRow.title`. §13 adds point 9.

Revision 2026-10-09 (U-D11, claude-sonnet-5-5, D-040 and D-041a; the code on main 9776555 was read for every item, after
U-M4c-4 and U-M4e-1 merged): §3 counts 25 symbols in `QUANTITY_SYMBOLS` and states the per-module allowance of LG-01
(D-040 a and c). §5 restates `LabelAnchor.forced`, `place_labels` with `copper`, and `copper_spots`. §6 records that the
spiral generator calls `unusable_sizes`. §9.1 states that `example.title` is free English display text (D-041a). §9.3
replaces the variable Inter file by the two static faces, adds the colophon line and the U+00A0 unit joiner. §11 adds the
board picker, the vertical split of `centre-split` with `layout/canvas_share`, the start widths, `pair-list`, the screw
fields, the DRC columns with the Board column, and corrects the font and rail text of the U-D10 revision. §13 closes three
rows of point 9 and adds point 10.

Revision 2026-10-11 (U-D12, claude-sonnet-5-5, D-040 c, D-041a, D-041b; the code on main 4fda98d was read for every item, after
U-M4e-1b and U-M4e-2 merged). §3 states that `UNIT_SPACE` is the U+00A0 literal and that LG-01 admits it in
`results/formatting.py` only. §9.1 closes the state paragraph of U-D11 (schema pattern removed, five titles set) and adds
D-041b, the design name that equals the title, with the five moved design hashes. §9.3 moves the colophon to the end of
the PDF (ruling f). §11 adds the screw push buttons (ruling i), the stretched last column (ruling j) and the provenance
property of the pair-list chip (F2). §13 closes the open rows of point 10 and adds point 11.

Revision 2026-10-12 (U-D13, claude-opus-5-5, D-007, D-023, D-034, D-042a; the code on main 7b9b4c9 was read for every
item, and `checks/selftest_probe.py` ran every self-test check against it). §3 corrects the `passed_tests` comment, adds
`Registry.tests_passed` as implemented and `Registry.evidence_build_id`. The new §3.1 is the contract for the evidence
of passing tests: the file `resources/evidence/passed_tests.v1.json`, its writer `tools/record_passed_tests.py`, the
`eqt` test marker, the staleness rule and the badge changes. §12 adds `embodic-cli selftest`. The new §14 is the
contract for `embodic.selftest` and the Tests dialog. §13 adds point 12.

Revision 2026-10-17 (U-D17, claude-sonnet-5-5, D-051; the code on main 0547f20 was read for every item, and
`docs/phase3/architecture/v3_contract_rulings.md` supplies the detail that D-051 leaves out). The new §3.2 states the
`checks` ruling that a requirement row needs before the audit calls it `verified` (D-051e), and the release trace gate
with its manual-record input. §4 renames the two winding issue codes to `…_ASYMMETRIC_…` (D-051b). §5 states that
`layout_hash` and `stack_hash` are same-platform identities (D-051f). §7 renames `DrcViolation.measured_mm` to
`clearance_mm` and `DrcCheckSummary.measured_min_mm` to `least_clearance_mm` (D-051a), and fixes the order of
`DrcReport.violations` (D-051f). §10 adds `format` and `format_version` 2 to the outcome JSON, with the key map from
version 1 (D-051a). §11 and §14 follow the rename. §13 adds point 14.

Revision 2026-10-17 (U-D20, claude-opus-5-5, D-055; the code on main e68d5ff was read for every item). The new §1.1
lists the 78 issue codes that `src` defines or emits and that this file did not name, with category, severity,
pointers, condition, `value`, `limit` and source line, and `checks/issue_code_coverage.py` finds the next one. §9.1
adds `engine_version` and `registry_version` to the project file, raises its format version to 2 and gives the load
rule for a v1 file (DEF-UM7d-01, REQ-T-07).

Revision 2026-10-17 (U-D21, claude-sonnet-5-5, D-056; main b977621 read for every item). §1.1 no longer names the issue
code for a topology with no generator, because no code path returns it (D-056e). §9.1 states that
`tools/sync_registry.py` regenerates the example project files after a registry change (D-056b). `checks/check_contract.py`
runs `checks/issue_code_coverage.py` (D-056d).

## 0. Rules for every public boundary

- Lengths are millimetres (`_mm`), angles radians (`_rad`) inside the core, temperature °C (`_degc`), current A (`_a`),
  voltage V (`_v`), resistance Ω (`_ohm`), field T (`_t`), power W (`_w`), temperature rise K (`_k`). Degrees exist only in
  the project file (`_deg`) and UI widgets.
- Data crossing a module seam is a frozen, slotted, keyword-only dataclass or a `StrEnum`. Closed choices are enums or
  tagged unions, never free strings or flag pairs.
- Functions are pure unless the docstring says otherwise. User input never raises. A failure the user can cause returns a
  value (`Unbuildable`, `DraftIncomplete`, issue tuples). Exceptions mean programming errors.
- Status vocabulary, badge rule and assumed-inputs tag follow D-007 and ADR-0003 unchanged.
- The core (`embodic.*` except `embodic.ui.views`, `embodic.ui.app`, `embodic.ui.workers`) imports no Qt
  (`package_layout.md` §3).

Deltas against the Phase 1 sketch (`architecture_draft.md` §7, §8):

| Area | Phase 1 | Phase 2 contract | Reason |
|---|---|---|---|
| KiCad | `io.kicad_items`, `.kicad_pcb` writer, plugin, `IMPORTED_KICAD` sources, nm conversion | removed | D-009 |
| Generators | `WindingGenerator` protocol with spiral only; serpentine/wave as `dict` placeholders | `generate_spiral/serpentine/wave(DesignParameters) -> Layout or Unbuildable`; full serpentine and wave specs | D-013, ADR-0012 |
| Winding plan | `plan_winding()` stage before geometry for every topology | spiral-only (`plan_spiral_winding`); each generator owns its phase plan and emits the shared `Circuit` | serpentine/wave assign phases per layer or per track, not by star of slots |
| Provenance | `default / user / imported_kicad / migrated / measured`, stored per field | `user / example / default / measured` as a tagged union, derived from the origin (example or blank) and the measurement list | D-014, D-007, D-019 |
| Design entry | app opens on the default design | blank `DesignDraft`; `parse_draft()` returns `DesignParameters` only when every required field is present | D-014 |
| Outline | one class with optional fields per shape | `CircleOutline` or `PolygonOutline` | shape-dependent fields cannot be half set |
| Materials | `MaterialConstant` inputs carrying a free `status` string | registry constants; optional user overrides as `PropertyValue` | constants and their EV status live in the registry |
| EC-05 | `ValidityFlag(metric, one_sided_addon)` | adds `metric_bound`, `calibration_status`, `transfer_status`, `threshold_status` | closes DEF-23 |
| View-models | Qt view-models | Qt-free view-models in `embodic.ui.viewmodels` behind `Observable` | testable without a display |
| Exports | SVG, DXF full/outline/holes, `.kicad_pcb`, JSON/CSV results, PDF | SVG, DXF complete/outline/screws, project JSON, PDF report, README, bundle ZIP | D-009 |

## 1. `embodic.units` and `embodic.errors`

```python
from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from fractions import Fraction
from pathlib import Path
from typing import ClassVar, Generic, Literal, Protocol, TypeAlias, TypeVar

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


class Unit(StrEnum):
    """Closed unit vocabulary of every Traceable. The value is the canonical code; `display()` gives the UI form."""

    MM = "mm"
    MM2 = "mm2"
    M = "m"
    UM = "um"  # display "µm"; via plating (DEF-M2a-01)
    RAD = "rad"
    T = "T"
    V = "V"
    V_S_PER_RAD = "V_s_per_rad"
    N_M_PER_A = "N_m_per_A"
    RPM_PER_V = "rpm_per_V"
    OHM = "ohm"
    OHM_M = "ohm_m"  # display "Ω·m"; resistivity
    H = "H"
    W = "W"
    W_PER_M2_K = "W_per_m2_K"  # display "W/(m²·K)"; convection coefficient
    A = "A"
    A_PER_MM2 = "A_per_mm2"
    K = "K"
    PER_K = "per_K"  # display "1/K"; temperature coefficient
    DEGC = "degC"
    G = "g"
    G_PER_CM3 = "g_per_cm3"  # display "g/cm³"; density
    N_M = "N_m"
    N_M_PER_SQRT_W = "N_m_per_sqrt_W"  # display "N·m/√W"; motor constant K_m (EQ-26), revision 2026-10-08 (U-D4)
    RPM = "rpm"
    HZ = "Hz"
    ONE = "one"
    COUNT = "count"

    def display(self) -> str: ...


MM_PER_COPPER_OZ: float = 0.0348  # status assumption; Xcoil engine.js l.14 OZ_TO_MM


def deg_to_rad(angle_deg: float) -> float: ...
def rad_to_deg(angle_rad: float) -> float: ...
def mm_to_m(length_mm: float) -> float: ...
def rpm_to_rad_per_s(speed_rpm: float) -> float: ...
def copper_oz_to_mm(copper_oz: float) -> float: ...
def mm2_to_mil2(area_mm2: float) -> float: ...
def mil2_to_mm2(area_mil2: float) -> float: ...
def js_round(value: float) -> float:
    """ECMAScript Math.round: the nearest integer, ties toward +inf (js_round(-2.5) == -2.0). Never returns -0.0."""
def quantise(value: float, scale: float) -> float:
    """Xcoil fmt(): js_round(value * scale) / scale, multiplied by scale, not divided by a step. Never returns -0.0.

    Writers that emit fixed decimals use scale = 1e5 (0.00001 mm). Built-in round() is banned on coordinates (MT-06).
    """


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(StrEnum):
    INVALID = "invalid"
    MISSING = "missing"  # new-design flow: a required field has no value yet (D-014)
    UNSUPPORTED_RANGE = "unsupported_range"
    UNBUILDABLE = "unbuildable"
    DRC = "drc"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True, kw_only=True)
class Suggestion:
    """The engine proposes, never applies (REQ-F-23)."""

    pointer: str
    proposed_value: float | int | str
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationIssue:
    code: str  # stable UPPER_SNAKE code with category prefix, e.g. "RANGE_SKIN_DEPTH"
    category: IssueCategory
    severity: Severity
    message: str  # English sentence from the message catalogue
    pointers: tuple[str, ...]  # JSON pointers into the design
    value: float | int | str | None = None
    limit: float | int | str | None = None
    hint: str = ""
    eq_ids: tuple[str, ...] = ()
    suggestion: Suggestion | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Unbuildable:
    """Returned instead of a Layout when valid input cannot produce copper."""

    issues: tuple[ValidationIssue, ...]  # at least one ERROR with category UNBUILDABLE


MESSAGES: Mapping[str, str]  # merged from every module of embodic.errors.catalogue; a duplicate code fails the import


def message_for(code: str) -> str:
    """English message template for an issue code; raises KeyError for an unknown code (programming error)."""
```

Revision 2026-10-04 (U-D1). Four changes to this section.

Rounding (DEF-M1a-02). Phase 1 `architecture_draft.md` §6 U6 says JS `Math.round` rounds half away from zero. It does
not: ECMAScript `Math.round` rounds ties toward +∞. `node -e` printed `3 -2 1 0 -1 0 0` for `Math.round` of 2.5, -2.5,
0.5, -0.5, -1.5, 0.49999999999999994 and -0.49999999999999994 (`verified (run)`, Node v22.22.2, 2026-10-04; Agent 3
measured the same values in Phase 1 `calculation_flow_and_port_notes.md` §2.1). Half away from zero gives -3, -1 and -2
for the three negative ties. Xcoil's `fmt()` (`engine.js` l.2762) is
`(Math.round(v * 1e5) / 1e5).toString()` with `"-0"` replaced by `"0"`. A port with half away from zero would therefore
write a different last digit for every negative coordinate that sits exactly on a half quantum (for example
`fmt(-0.000025)` is `-0.00002` in Xcoil and would be `-0.00003`). Decision: embodic's quantiser uses JS semantics, so
SVG and DXF numbers match Xcoil's exports digit for digit. `round_half_away_from_zero` (U-M1a) is replaced by `js_round`
and `quantise`. The obvious port `math.floor(x + 0.5)` is wrong as well: it returns 1 for 0.49999999999999994, where
`Math.round` returns 0 (`verified (run)`, same session). `js_round` takes `n = floor(x)` and adds 1 when `x - n >= 0.5`.
The subtraction cannot move a value across 0.5 for any finite double (`inferred` from Sterbenz's lemma; UT-UNI-01 tests
the ties). `-0.000025 * 1e5` is exactly -2.5 in both Python and Node (`verified (run)`), so the example above is a true
tie. The Phase 1 file is outside Agent 6's Phase 2 write scope; this section supersedes its U6 sentence.

Number text in writers. The quantised value alone does not give Xcoil's text. JS `Number.prototype.toString` writes
`0.00001` and `0`, while Python `repr` writes `1e-05` and `0.0` (`verified (run)` on the values above). Writers that must
match Xcoil format numbers like JS `toString`; U-M4a owns that formatter (UT-EXP-01, UT-EXP-02).

Copper weight. `MM_PER_COPPER_OZ = 0.0348` stays `assumption`. Xcoil `engine.js` l.14 is
`var OZ_TO_MM = 0.0348; // 1 oz/ft^2 copper = 34.8 um` (`verified` by reading, 2026-10-04). That is a copy of Xcoil's
value, not a standard. Agent 5's evidence register has no IPC-4562 entry, so no standard backs the nominal thickness yet.

Issue catalogue. `MESSAGES` is the merge of one module per owning unit under `embodic.errors.catalogue`
(`work_breakdown.md` §4). Each module exports `MESSAGES: Mapping[str, str]`. `embodic/errors/__init__.py` finds the
modules with `pkgutil.iter_modules`, so a new module needs no edit to a shared file. A code defined twice raises at
import, which fails every test run.

Revision 2026-10-05 (U-D2). DEF-M2a-01: `Unit` had no member for via plating, convection coefficient, resistivity,
temperature coefficient or density, so U-M2a left those fields without a unit. The five members above are the names
U-M1z implements (commit `eb7a2f1` on branch `unit/U-M1z`, read on 2026-10-05, not yet merged). The field table gives
`/vias/plating_um`, `/operating/convection_h_w_m2k` and the material override values these units in the U-M2a fix round
(`work_breakdown.md` §5).

### 1.1 Issue codes by emitting module (revision 2026-10-17, U-D20; D-055)

This section lists every issue code that `src` defines or emits and that no other section of this file names. The code
on main e68d5ff was read for every row, and each Source cell gives the line that holds the code literal. The lever
`checks/issue_code_coverage.py` lists the codes of the catalogue modules and the code literals of `src/embodic`, and
prints each one that this file does not name. Run it after a unit adds a code. On main e68d5ff it found 78 codes
before this section and 0 after it (`verified (run)`, 2026-10-17). `INVALID_HARMONIC_FUNDAMENTAL`, which the U-D20 brief
names, was already in §2.2 (revision U-D15, `verified` by reading).

Common fields. `message` is the catalogue text, formatted with `limit` and `unit` where the template names them.
`hint` is `""` for every code below except the DRC kind codes. `eq_ids` is `()` for every code below. A pointer
written `<i>` or `<k>` is a list index.

Field checks and cross-field rules of `validate_design` (`src/embodic/model/validate.py`). The helper `issue()` (l.37)
takes the category from the prefix: `INVALID_` gives INVALID and `RANGE_` gives UNSUPPORTED_RANGE. The severity is
ERROR unless the row says otherwise. `check_value` runs per field in the order type, empty text, sign, range, and stops
at the first hit, so a value that fails the sign check never also gets a `RANGE_` code.

| Code | Category, severity | Pointers | Fires when | `value`, `limit`, `suggestion` | Source |
|---|---|---|---|---|---|
| `INVALID_NOT_INTEGER` | INVALID, ERROR | the field | an INT field holds a finite number that is not an integer | the number; none; none | l.97 |
| `INVALID_TYPE` | INVALID, ERROR | the field | the value does not have the field's value type, and the field is not a CHOICE | the value if it is a number or text, else None; none; none | l.98 |
| `INVALID_CHOICE` | INVALID, ERROR | the field | a CHOICE field holds a value outside `FieldSpec.choices` | as `INVALID_TYPE` | l.98 |
| `INVALID_EMPTY_TEXT` | INVALID, ERROR | the field | a TEXT field holds only white space | none | l.101 |
| `INVALID_NON_POSITIVE` | INVALID, ERROR | the field | `Limits.sign` is POSITIVE and the number is not above 0 | the number; 0 with the field unit; none | l.114 |
| `INVALID_NEGATIVE` | INVALID, ERROR | the field | `Limits.sign` is NON_NEGATIVE and the number is below 0 | the number; 0 with the field unit; none | l.117 |
| `RANGE_BELOW_SUPPORTED` | UNSUPPORTED_RANGE, ERROR | the field | the number is below `Limits.low` | the number; `Limits.low` with the field unit; proposes `Limits.low` | l.126 |
| `RANGE_ABOVE_SUPPORTED` | UNSUPPORTED_RANGE, ERROR | the field | the number is above `Limits.high` | the number; `Limits.high` with the field unit; proposes `Limits.high` | l.135 |
| `INVALID_POLE_COUNT_ODD` | INVALID, ERROR | `/rotor/poles` | the pole count is odd | the count; none; proposes the count + 1 | l.145 |
| `INVALID_ORDER` | INVALID, ERROR | spiral: `/winding/coil/r_inner_mm`, `/winding/coil/r_outer_mm`; serpentine and wave: `/winding/r_inner_mm`, `/winding/r_outer_mm` | the outer radius is not above the inner radius | none | l.152, l.156 |
| `INVALID_RADIAL_SPAN` | INVALID, ERROR | `/winding/r_inner_mm`, `/winding/r_outer_mm` | serpentine or wave: the outer radius is above the inner radius but not above inner + `RADIAL_SPAN_MIN_MM` (0.5 mm, Xcoil R_ORDER) | the outer radius; 0.5; none | l.158 |
| `INVALID_MAGNET_ORDER` | INVALID, ERROR | `/rotor/magnet/r_inner_mm`, `/rotor/magnet/r_outer_mm` | an arc magnet whose outer radius is not above its inner radius | none | l.164 |
| `INVALID_MAGNET_CROSSES_AXIS` | INVALID, ERROR | `/rotor/magnet/r_center_mm`, `/rotor/magnet/length_mm` | a block magnet whose radial span starts at or below radius 0 | none | l.179 |
| `INVALID_MAGNET_WIDER_THAN_RADIUS` | INVALID, ERROR | `/rotor/magnet/r_center_mm`, `/rotor/magnet/length_mm`, `/rotor/magnet/width_mm` | a block magnet whose span starts below half its width (EQ-04 takes asin(w / 2r)) | the span's inner radius; half the width in mm; none | l.184 |
| `RANGE_MAGNET_OUTSIDE_WINDING` | UNSUPPORTED_RANGE, ERROR | `/rotor/magnet` | the winding span is valid and the magnet's radial span does not overlap it (DEF-M2f-01) | the magnet's inner radius; the winding's outer radius in mm; none | l.189 |
| `INVALID_LAYERS_PER_PHASE` | INVALID, ERROR | `/winding/layers_per_phase` | serpentine: the count is odd and not 1 | the count; none; proposes the count + 1 | l.203 |
| `INVALID_SERIES_PAIRS_EXCEED_POLE_PAIRS` | INVALID, ERROR | `/winding/layers_per_phase`, `/winding/pair_connection`, `/rotor/poles` | serpentine with series pairs: the pair count exceeds poles // 2 | the pair count; poles // 2; none | l.207 |
| `RANGE_TOO_MANY_TRACES` | UNSUPPORTED_RANGE, ERROR | `/winding/turns`, `/winding/strands` | serpentine: turns × strands above `TRACES_MAX` (400, Xcoil TOO_MANY) | the product; 400; none | l.215 |
| `INVALID_VIA_RING` | INVALID, ERROR | `/vias/drill_mm`, `/vias/pad_mm` | the via pad is below drill + `VIA_RING_MIN_MM` (0.1 mm) | the pad; 0.1; none | l.233 |
| `INVALID_TERMINAL_PAD_RING` | INVALID, ERROR | `/connection/terminal_drill_mm`, `/connection/terminal_pad_mm` | the terminal drill is above 0 and the pad is below drill + `TERMINAL_RING_MIN_MM` (0.3 mm) | the pad; 0.3; none | l.237 |
| `INVALID_SPIRAL_PHASES` | INVALID, ERROR | `/phases` | spiral: the phase count is not 3 | the count; 3; none | l.245 |
| `RANGE_COIL_GAP_BELOW_CLEARANCE` | UNSUPPORTED_RANGE, INFO | `/winding/coil/coil_gap_mm`, `/winding/coil/clearance_mm` | spiral: the coil gap is below the clearance | the gap; the clearance; proposes the clearance | l.254 |
| `INVALID_END_WIDTH_BELOW_TRACE` | INVALID, ERROR | `/winding/coil/end_width_outer_mm` or `/winding/coil/end_width_inner_mm`, and `/winding/coil/trace_width_mm` | spiral: an end width is set and is below the trace width; one issue per end | the end width; the trace width; none | l.267 |
| `RANGE_SPIRAL_COPPER_COUNT_ODD` | UNSUPPORTED_RANGE, WARNING | `/stackup/layers` | spiral: the copper layer count is odd | the count; none; none | l.274 |
| `INVALID_PAIR_LAYER_UNKNOWN` | INVALID, ERROR | `/winding/layers/pairs/<i>/layer_in` or `/winding/layers/pairs/<i>/layer_out` | spiral: the pair names a layer that is not a copper layer of the stack-up; one issue per side | the name; none; none | l.281 |
| `INVALID_PAIR_LAYER_SAME` | INVALID, ERROR | `/winding/layers/pairs/<i>/layer_in`, `/winding/layers/pairs/<i>/layer_out` | spiral: both sides name one layer | the name; none; none | l.283 |
| `INVALID_PAIR_INDEX_DUPLICATE` | INVALID, ERROR | `/winding/layers/pairs/<i>/index` | spiral: the index occurs more than once; one issue per pair that holds it | the index; none; none | l.285 |
| `INVALID_SERIES_GROUPS` | INVALID, ERROR | `/winding/layers/series_groups` | spiral: the sorted group members differ from the sorted pair indices | none | l.288 |
| `INVALID_STACKUP_NO_COPPER` | INVALID, ERROR | `/stackup/layers` | the stack-up has no copper layer | none | l.294 |
| `INVALID_LAYER_NAME_DUPLICATE` | INVALID, ERROR | `/stackup/layers/<i>/name` | a layer repeats the name of an earlier layer; one issue per repeat | the name; none; none | l.298 |
| `RANGE_WINDING_BELOW_AMBIENT` | UNSUPPORTED_RANGE, ERROR | `/operating/winding_temperature_degc`, `/operating/ambient_temperature_degc` | the winding temperature is below the ambient temperature | the winding temperature; the ambient temperature in °C; none | l.344 |

Supported ranges outside the field table. `SUPPORTED_RANGES` (`validate.py` l.304-328) holds bounds that `FIELDS` does
not hold. `_supported_ranges` (l.331) applies them through `_check_limits` with the field's own unit, so they give
`RANGE_BELOW_SUPPORTED` and `RANGE_ABOVE_SUPPORTED` as in the table above. The comment above the table marks each value
an `assumption` unless a source is named, and gives the U-M2-fix3 timing of CF-11 as the reason. `OUTLINE_MAX_MM` is
2000.0, the arc-magnet radius maximum of the field table (l.303).

| Pointer pattern | Low | High | Reason in the code |
|---|---|---|---|
| `/analysis/max_segment_mm` | 0.1 | none | physics cuts each path into length / max_segment chords |
| `/drc_rules/trace_clearance_mm`, `/drc_rules/via_clearance_mm`, `/drc_rules/edge_clearance_mm`, `/drc_rules/hole_clearance_mm` | none | 5.0 | the DRC broad phase keeps every pair closer than the rule |
| `/vias/plating_um` | 1.0 | none | none given |
| `/rotor/magnet/width_mm`, `/rotor/magnet/length_mm` | 0.1 | 100.0 | Xcoil magnet sizes 0.1 to 100 mm |
| `/rotor/magnet/r_center_mm` | 0.5 | 2000.0 | follows the arc radii |
| `/winding/coil/r_inner_mm`, `/winding/coil/r_outer_mm`, `/outline/board/radius_mm`, `/outline/board/across_flats_mm`, `/outline/bore/radius_mm`, `/outline/bore/across_flats_mm` | none | 2000.0 | `OUTLINE_MAX_MM` |
| `/outline/screws/*/pitch_radius_mm` | none | 2000.0 | DEF-M7a-01: a pitch radius of 1e30 mm overflowed the DRC |
| `/outline/screws/*/hole_diameter_mm` | none | 4000.0 | 2 × `OUTLINE_MAX_MM` |

Other model codes.

| Code | Category, severity | Pointers | Fires when | `value`, `limit` | Source |
|---|---|---|---|---|---|
| `INVALID_STACKUP_COPPER_EXCEEDS_BOARD` | INVALID, ERROR | `/stackup/layers` | `even_stackup_issues(copper_count, copper_thickness_mm, board_thickness_mm)` finds a board thickness not above the copper total n × t (D-053a). `validate_design` does not run it: its only caller is the stack-up generator of `ui/viewmodels/session.py` l.926 | the board thickness; the copper total in mm | `validate.py` l.385 |
| `INVALID_LIST_SHAPE` | INVALID, ERROR | the list | `parse_draft`: `resolve` reports the list as malformed (missing or extra entries) | none | `model/draft.py` l.74 |
| `INVALID_DRC_RULE_NOT_FINITE`, `INVALID_DRC_RULE_NEGATIVE` | INVALID, ERROR | `/drc_rules/<field>` | `validate_drc_rules`: the rule is not finite, or it is finite and below 0 | the rule; 0.0 | `model/drc_rules.py` l.30 |

Generator refusals. Each generator returns these in `Unbuildable.issues`, with category UNBUILDABLE, severity ERROR
and `value` None unless the row says otherwise. Every generator runs `design_keep_out_issues` before it builds
(`generators/spiral/generate.py` l.144, `serpentine/generate.py` l.118, `wave/generate.py` l.80).

| Code | Generator | Pointers | Fires when | `limit` | Source |
|---|---|---|---|---|---|
| `UNBUILDABLE_SCREW_HOLE_EDGE` | all | `/outline/screws/<k>/pitch_radius_mm` and `/outline/screws/<k>/hole_diameter_mm` for each pattern k that breaks the rule | a hole's gap to the board edge or a cutout violates `edge_clearance_mm` by the D-006 test | none | `generators/fasteners.py` l.40 |
| `UNBUILDABLE_SCREW_HOLE_PITCH` | all | the same form, for both patterns of each pair | the gap between two holes violates `edge_clearance_mm` (the web rule is an `assumption`, module docstring) | none | `fasteners.py` l.40 |
| `UNBUILDABLE_ZERO_TURNS` | spiral | `/winding/coil/turns` | `max_closing` finds no closing for the centre vias | none | `spiral/generate.py` l.396 |
| `UNBUILDABLE_INTERCONNECT_CROSSING` | spiral | `/connection/topology` | the interconnect is drawn, the topology is not `open`, and `plan_links` returns None | none | `spiral/generate.py` l.415 |
| `UNBUILDABLE_PHASE_CHAIN_UNROUTABLE` | spiral | `/connection/ring_width_mm` | `chain_coils` returns None for a phase | none | `spiral/generate.py` l.489 |
| `UNBUILDABLE_SERPENTINE_OPTION_NOT_IMPLEMENTED` | serpentine | `/vias/vias_per_transition` | `vias_per_transition` is not 1 (D-054d) | none | `serpentine/generate.py` l.120 |
| `UNBUILDABLE_SERPENTINE_R_TOO_SMALL` | serpentine | `/winding/r_inner_mm`, `/winding/turns`, `/winding/strands` | `plan_stack` returns a `CanonFailure` whose first reason is `BuildFailure.R_TOO_SMALL` | none | `serpentine/generate.py` l.126 builds the code as f"UNBUILDABLE_SERPENTINE_{reason.value}"; pointers l.64 |
| `UNBUILDABLE_SERPENTINE_ACUTE_CORNER` | serpentine | `/winding/turns`, `/winding/corner_style`, `/winding/r_inner_mm` | the same, first reason `ACUTE_CORNER` | none | l.126; l.65 |
| `UNBUILDABLE_SERPENTINE_BUNDLE_TOO_WIDE` | serpentine | `/winding/turns`, `/winding/strands`, `/winding/r_inner_mm` | the same, first reason `BUNDLE_TOO_WIDE` | none | l.126; l.66 |
| `UNBUILDABLE_SERPENTINE_GEOMETRY` | serpentine | `/winding/r_outer_mm`, `/winding/fillet_radius_mm` | the same, first reason `GEOMETRY` (`serpentine/canonical.py` l.237, l.261) | none | l.126; l.67 |
| `UNBUILDABLE_WAVE_OPTION_NOT_IMPLEMENTED` | wave | `/vias/vias_per_transition` | `vias_per_transition` is not 1 (D-054d) | none | `wave/generate.py` l.82 |
| `UNBUILDABLE_WAVE_MIN_POLES` | wave | `/rotor/poles` | `derive_wave`: more than one phase and fewer than 2 pole pairs (`wave/derive.py` l.315) | none | `wave/generate.py` l.34 |
| `UNBUILDABLE_WAVE_SLOT_PITCH` | wave | `/winding/turns` | `derive_wave`: the slot chord at the inner radius is below trace width + clearance - 1e-9 mm (`derive.py` l.317); or the chord style finds an inner via radius not above 0.5 mm or a gap that does not fit (l.212) | `max_wave_turns(params)`, or None when it is 0 | `wave/generate.py` l.35, l.102 |
| `UNBUILDABLE_WAVE_OUTER_TIGHT` | wave | `/winding/end_width_outer_mm` | jog: no outer via radius keeps the pitch (`derive.py` l.268); involute: the outer spacing is below the need - 1e-9 mm (l.301) | none | `wave/generate.py` l.36 |
| `UNBUILDABLE_WAVE_INNER_TIGHT` | wave | `/winding/turns` | jog, overlap or involute: the inner end turns do not fit (`derive.py` l.271, l.286, l.298) | as `UNBUILDABLE_WAVE_SLOT_PITCH` | `wave/generate.py` l.37, l.102 |
| `UNBUILDABLE_WAVE_LINK_ROOM` | wave | `/winding/r_inner_mm` | involute, jog or chord: the group links leave less than 0.5 mm inside the inner via ring, or `build_wave` reports no link room | none | `wave/generate.py` l.183 |
| `UNBUILDABLE_WAVE_INTERCONNECT_CROSSING` | wave | `/connection/topology` | the interconnect is wanted and `build_interconnect` reports it unroutable | none | `wave/generate.py` l.198 |

`derive_wave` can return `UNBUILDABLE_WAVE_MIN_POLES` and `UNBUILDABLE_WAVE_SLOT_PITCH` together (l.314-320). Every
other wave refusal and every serpentine refusal is one issue: `_refusal` reports only the first reason of a
`CanonFailure` (`serpentine/generate.py` l.125). `build_layout` indexes `GENERATORS`, which has all three topologies
(`generators/__init__.py` l.25-27), so no path refuses a topology.

Revision 2026-10-17 (U-D21; D-056e). The catalogue still holds one code for that refusal, and this file no longer names
it. `checks/issue_code_coverage.py` finds no literal of it outside the catalogue (`verified (run)`, main b977621), and its
message says that only spiral coils can be built (`errors/catalogue/generators.py` l.6, `verified` by reading), which is
false. D-056e removes the code, and unit U-M8e removes it from `src`. Until that unit merges, `checks/issue_code_coverage.py`
and `checks/check_contract.py` report the code as absent from this file. Do not add its name here to silence the report.

Project file, compute facade, exporters and command line. None of these codes has a pointer unless the row says so.

| Code | Category, severity | Pointers | Fires when | `value`, `limit`, `hint` | Source |
|---|---|---|---|---|---|
| `INVALID_PROJECT_NOT_FOUND` | INVALID, ERROR | none | `load_project`: reading the file raises FileNotFoundError | the path as text | `io/project.py` l.263 |
| `INFO_PROVENANCE_EXAMPLE_MISMATCH` | INVALID, INFO | the file pointer of the field | a stored `example` entry disagrees with the derivation from the packaged example (UT-IO-07) | the stored provenance word | `io/project.py` l.253. The category is INVALID because `IssueCategory` has no INFO member (l.69) |
| `MISSING_DESIGN_INCOMPLETE` | MISSING, ERROR | the file pointers of the missing fields | `compute_project` loads a `LoadedDraft` | none | `api.py` l.317 |
| `UNBUILDABLE_EXPORT_NO_LAYOUT` | UNBUILDABLE, ERROR | none | `exportable_boards`: the outcome has no boards; `ExportRefused.reason` is `no_layout` | none | `io/exporters.py` l.157 |
| `INVALID_EXPORT_NO_SCREW_HOLES` | INVALID, ERROR | none | `no_screws()`; `ExportRefused.reason` is `no_screws` (§9.3) | none | `io/exporters.py` l.166 |
| `INVALID_CLI_USAGE` | INVALID, ERROR | none | argparse reports a usage error; the process exits with `ExitCode.VALIDATION_ERRORS` | the argparse message | `cli/commands.py` l.290 |
| `INVALID_CLI_OUTPUT_UNWRITABLE` | INVALID, ERROR | none | the output path is a folder, or its parent folder does not exist | the path as text | `cli/commands.py` l.113 |
| `RANGE_NON_FINITE_RESULT` | UNSUPPORTED_RANGE, WARNING | none | a result carries the validity flag of this code (`physics/analyse.py` l.83) | the result's quantity name | `api.py` l.140-148 |
| `DRC_TRACE_TRACE`, `DRC_TRACE_VIA`, `DRC_VIA_VIA`, `DRC_PAD_TRACE`, `DRC_PAD_PAD`, `DRC_COPPER_EDGE`, `DRC_COPPER_HOLE`, `DRC_MIN_WIDTH`, `DRC_MIN_DRILL`, `DRC_ANNULAR_RING` | DRC, ERROR | none | `_drc_failures`: one issue per failed `DrcCheckKind` of each board, after `DRC_EXPORT_NOT_CONFIRMED`. The code is `DrcCheckKind.issue_code`, f"DRC_{name}" (§7) | `least_clearance_mm`; `required_mm`; "board <n>" | `io/exporters.py` l.141-147; `drc/report.py` l.33 |
| `INTERNAL_VALIDATE_FAILED`, `INTERNAL_GEOMETRY_FAILED`, `INTERNAL_DRC_FAILED`, `INTERNAL_PHYSICS_FAILED` | INTERNAL, ERROR | none | a pipeline stage raised; the code is f"INTERNAL_{stage.name}_FAILED" over `Stage` (`outcome.py` l.15) | the traceback | `api.py` l.151-160 |
| `INTERNAL_CLI_FAILED` | INTERNAL, ERROR | none | a command raised | the traceback | `cli/commands.py` l.354 |
| `INTERNAL_REGISTRY_EQUATION_UNSOURCED` | INTERNAL, WARNING | `/equations/<id>/sources` | an equation cites no evidence ID | the equation ID | `results/registry.py` l.301 |
| `INTERNAL_REGISTRY_EVIDENCE_MISSING` | INTERNAL, WARNING | `/equations/<id>/sources` | an equation cites an evidence ID the register lacks; one issue per ID | the evidence ID | `registry.py` l.303 |
| `INTERNAL_REGISTRY_UNIT_UNKNOWN` | INTERNAL, WARNING | `/equations/<id>/constants` | a constant's unit is outside `Unit`; the constant is not loaded | the unit text | `registry.py` l.423 |
| `INTERNAL_REGISTRY_FIELD_UNTYPED` | INTERNAL, WARNING | `/equations/<id>/validity_checks/<check>` | a DEF-23 field is missing or written as prose; one issue per field | the field name | `registry.py` l.449 |

The four registry codes go to `Registry.issues` (`registry.py` l.312) and never reach `ComputeOutcome.issues`
(`inferred` from a grep of `api.py`, which reads no `registry.issues`). `INTERNAL_INTERCONNECT_UNCLASSIFIED` is not a
`ValidationIssue`. It is the code of the `ValidityFlag` `UNCLASSIFIED_INTERCONNECT` (`physics/analyse.py` l.84-89,
EQ-23, effect CAP).

## 2. `embodic.model`: design inputs, draft, provenance

### 2.1 Shared vocabulary and sub-models

```python
class TopologyKind(StrEnum):
    SPIRAL = "spiral"
    SERPENTINE = "serpentine"
    WAVE = "wave"


class Phase(StrEnum):
    A = "A"
    B = "B"
    C = "C"


PhaseCount: TypeAlias = Literal[1, 2, 3]  # spiral accepts 3 only (validator); serpentine and wave keep Xcoil's 1/2/3


class RotorType(StrEnum):
    DOUBLE = "double"
    SINGLE_YOKE = "single_yoke"
    SINGLE_OPEN = "single_open"


@dataclass(frozen=True, slots=True, kw_only=True)
class ArcMagnet:
    kind: Literal["arc"] = "arc"
    pole_arc_ratio: float
    r_inner_mm: float
    r_outer_mm: float
    thickness_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockMagnet:
    kind: Literal["block"] = "block"
    width_mm: float
    length_mm: float
    r_center_mm: float
    thickness_mm: float


MagnetGeometry: TypeAlias = ArcMagnet | BlockMagnet


@dataclass(frozen=True, slots=True, kw_only=True)
class RotorSpec:
    poles: int  # 2p, even
    rotor_type: RotorType
    magnet: MagnetGeometry
    remanence_t: float  # property input
    recoil_permeability: float  # property input
    air_gap_mm: float  # per side, magnet face to board surface
    back_iron_thickness_mm: float
    magnet_offset_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class CopperLayer:
    kind: Literal["copper"] = "copper"
    name: str  # unique, e.g. "L1"
    thickness_mm: float  # property input (finished copper)


@dataclass(frozen=True, slots=True, kw_only=True)
class DielectricLayer:
    kind: Literal["dielectric"] = "dielectric"
    name: str
    thickness_mm: float
    material: str


StackLayer: TypeAlias = CopperLayer | DielectricLayer


@dataclass(frozen=True, slots=True, kw_only=True)
class Stackup:
    layers: tuple[StackLayer, ...]  # top to bottom, always explicit (REQ-F-04)

    def copper_layers(self) -> tuple[CopperLayer, ...]: ...
    def copper_z_mm(self) -> dict[str, float]:
        """Centre z of each copper layer from the top surface; exact cumulative sum (math.fsum)."""
    def board_thickness_mm(self) -> float: ...


def generate_even_stackup(copper_count: int, copper_thickness_mm: float, board_thickness_mm: float,
                          material: str = "FR-4") -> Stackup:
    """Helper only; its output is an ordinary Stackup (GR-07 compares it with Xcoil stackupFor auto mode)."""


class ViaSpan(StrEnum):
    THROUGH = "through"  # Phase 2 builds through vias only (D-015)


@dataclass(frozen=True, slots=True, kw_only=True)
class ViaSpec:
    drill_mm: float
    pad_mm: float
    plating_um: float  # property input (EQ-11)
    vias_per_transition: int = 1


class ConnectionTopology(StrEnum):
    STAR = "star"
    DELTA = "delta"
    OPEN = "open"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSpec:
    topology: ConnectionTopology = ConnectionTopology.STAR  # D-015 default
    draw_interconnect: bool = True
    ring_width_mm: float
    terminal_pad_mm: float
    terminal_drill_mm: float  # 0 = SMD pad
    neutral_pad: bool = False


class ScrewFit(StrEnum):
    CLOSE = "close"
    NORMAL = "normal"
    LOOSE = "loose"


@dataclass(frozen=True, slots=True, kw_only=True)
class ScrewPattern:
    """Clearance holes of one fastener pattern (REQ-F-24). Revision 2026-10-08 (U-D4, D-031a): the user enters the hole
    diameter; `size` and `fit` label the holes and pick no value. ISO 273 values ship only as labelled example values
    once Agent 5 cites the source (U-S3b)."""

    size: str  # e.g. "M3"
    fit: ScrewFit
    count: int
    pitch_radius_mm: float
    hole_diameter_mm: float  # required whenever a pattern exists; no default (D-031a)
    angle_offset_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class CircleOutline:
    shape: Literal["circle"] = "circle"
    radius_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class PolygonOutline:
    shape: Literal["polygon"] = "polygon"
    sides: int
    across_flats_mm: float
    corner_radius_mm: float = 0.0
    rotation_rad: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class OutlineSpec:
    board: CircleOutline | PolygonOutline
    bore: CircleOutline | PolygonOutline | None
    screws: tuple[ScrewPattern, ...] = ()


class Modulation(StrEnum):
    SVPWM = "svpwm"
    SPWM = "spwm"
    SIX_STEP = "six_step"


@dataclass(frozen=True, slots=True, kw_only=True)
class OperatingPoint:
    speed_rpm: float
    line_current_rms_a: float
    winding_temperature_degc: float
    ambient_temperature_degc: float
    convection_h_w_m2k: float  # property input (EQ-17 source disagreement)
    dc_link_v: float | None = None  # None: no torque-speed estimate (EQ-20)
    modulation: Modulation = Modulation.SVPWM


@dataclass(frozen=True, slots=True, kw_only=True)
class PropertyValue:
    """A user override of a registry constant. Without an override the registry constant and its EV status apply."""

    value: float
    unit: Unit


@dataclass(frozen=True, slots=True, kw_only=True)
class MaterialOverrides:
    copper_resistivity_20c_ohm_m: PropertyValue | None = None
    copper_temp_coeff_per_k: PropertyValue | None = None
    copper_density_g_per_cm3: PropertyValue | None = None
    laminate_density_g_per_cm3: PropertyValue | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisOptions:
    harmonics: tuple[int, ...] = (1, 3, 5, 7, 9, 11, 13)  # starts with 1, odd and positive (§2.2, revision 2026-10-13)
    max_segment_mm: float = 0.5
    edge_correction: Literal["off"] = "off"  # EC-05 optional correction stays off in Phase 2


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcRules:
    trace_clearance_mm: float
    via_clearance_mm: float
    edge_clearance_mm: float
    hole_clearance_mm: float
    min_trace_width_mm: float
    min_drill_mm: float
    min_annular_ring_mm: float


def validate_drc_rules(rules: DrcRules, pointer: str = "/drc_rules") -> tuple[ValidationIssue, ...]:
    """One INVALID issue per rule that is not a finite number >= 0 (INVALID_DRC_RULE_NOT_FINITE or _NEGATIVE).

    A NaN or negative rule would make every comparison pass, so callers run this before run_drc (U-M1c addition)."""
```

### 2.2 Winding specs, one per topology

The spiral spec keeps the Phase 1 fields (`architecture_draft.md` §7.1, Agent 2 `answers_to_agents.md` §3.2). Serpentine
and wave specs carry exactly the inputs Xcoil's builders read (`/home/claude/serpentine/src/engine.js` l.163-753 for
serpentine, l.1449-2230 for wave; `verified` by reading the parameter references on 2026-10-04), renamed to embodic
conventions. The golden harness maps each field to its Xcoil name (`tools/golden/param_map/<topology>.json`, units U-M3a and U-M3b).

```python
class SideStyle(StrEnum):
    RADIAL = "radial"
    PARALLEL = "parallel"


class EndStyle(StrEnum):
    ARC = "arc"
    STRAIGHT = "straight"
    STADIUM = "stadium"


class InnerTurnMode(StrEnum):
    FIXED = "fixed"
    MOVING = "moving"


class Sense(StrEnum):
    CW = "cw"
    CCW = "ccw"


class LeadStyle(StrEnum):
    RADIAL_THEN_ARC = "radial_then_arc"
    STRAIGHT = "straight"


class PhaseSequence(StrEnum):
    ABC = "abc"
    ACB = "acb"


class PairConnection(StrEnum):
    SERIES = "series"
    PARALLEL = "parallel"


@dataclass(frozen=True, slots=True, kw_only=True)
class LayerPair:
    index: int
    layer_in: str  # copper layer name of X (spiral in)
    layer_out: str  # copper layer name of Y (spiral out, mirrored)
    rotation_rad: float = 0.0  # option M3
    phases: tuple[Phase, ...] | None = None  # None = all phases (FSCW); one phase = option M4


@dataclass(frozen=True, slots=True, kw_only=True)
class LayerConfig:
    pairs: tuple[LayerPair, ...]
    series_groups: tuple[tuple[int, ...], ...]  # inner tuples in parallel, groups in series (EQ-07)


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignmentInput:
    coil_index: int
    phase: Phase
    polarity: Literal[1, -1]


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralCoilSpec:
    coil_count: int
    r_inner_mm: float  # copper-edge radius
    r_outer_mm: float  # copper-edge radius
    trace_width_mm: float
    clearance_mm: float
    coil_gap_mm: float
    turns: int | None = None  # None = maximum feasible
    side_style: SideStyle = SideStyle.PARALLEL
    end_style: EndStyle = EndStyle.ARC
    inner_turn_mode: InnerTurnMode = InnerTurnMode.MOVING
    corner_radius_mm: float = 0.0
    end_width_outer_mm: float | None = None
    end_width_inner_mm: float | None = None
    first_coil_angle_rad: float = math.pi / 2  # any finite value; the generator normalises it modulo 2*pi (D-031c)
    x_inward_sense: Sense = Sense.CW
    lead_style: LeadStyle = LeadStyle.RADIAL_THEN_ARC
    terminal_offset_mm: float | None = None
    min_side_length_mm: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralWindingSpec:
    kind: Literal["spiral"] = "spiral"
    coil: SpiralCoilSpec
    layers: LayerConfig
    assignment: tuple[CoilAssignmentInput, ...] | None = None  # None = star of slots
    phase_sequence: PhaseSequence = PhaseSequence.ABC
    parallel_paths: int = 1


class CornerStyle(StrEnum):
    ROUND = "round"
    SHARP = "sharp"


class TerminalSide(StrEnum):
    OUTER = "outer"
    INNER = "inner"


class LayerOrder(StrEnum):
    GROUPED = "grouped"
    INTERLEAVED = "interleaved"


class StackMode(StrEnum):  # revision 2026-10-05 (U-D3, D-016)
    SINGLE = "single"  # Xcoil stackMode 'single': all phases on one board
    ONE_BOARD_PER_PHASE = "one_board_per_phase"  # Xcoil stackMode 'perPhase'


@dataclass(frozen=True, slots=True, kw_only=True)
class SerpentineWindingSpec:
    """Xcoil 'serpentine': one phase per layer group, on one board or on one board per phase (D-016)."""

    kind: Literal["serpentine"] = "serpentine"
    r_inner_mm: float  # Xcoil rIn
    r_outer_mm: float  # Xcoil rOut
    turns: int  # Xcoil turns (traces per pole)
    strands: int = 1  # Xcoil strands
    trace_width_mm: float  # Xcoil traceWidth
    clearance_mm: float  # Xcoil clearance
    end_width_outer_mm: float | None = None  # Xcoil endWidthOuter (0 there = None here)
    end_width_inner_mm: float | None = None  # Xcoil endWidthInner
    side_style: SideStyle = SideStyle.PARALLEL  # Xcoil style
    corner_style: CornerStyle = CornerStyle.ROUND  # Xcoil cornerStyle
    fillet_radius_mm: float = 0.4  # Xcoil filletRadius
    fillet_max: bool = False  # Xcoil filletMax
    terminal_side: TerminalSide = TerminalSide.OUTER  # Xcoil terminalSide
    start_angle_rad: float = 0.0  # Xcoil startAngleDeg
    layers_per_phase: int  # Xcoil layersPerPhase: 1 or even
    pair_connection: PairConnection = PairConnection.SERIES  # Xcoil pairConnection
    layer_order: LayerOrder = LayerOrder.GROUPED  # Xcoil layerOrder; ignored for ONE_BOARD_PER_PHASE (l.681)
    stack_mode: StackMode = StackMode.SINGLE  # Xcoil stackMode (l.37)
    board_gap_mm: float = 0.1  # Xcoil boardGap (l.54); no effect for SINGLE (l.689, l.695)


class WaveStyle(StrEnum):
    INVOLUTE = "involute"
    JOG = "jog"
    CHORD = "chord"
    OVERLAP = "overlap"


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveWindingSpec:
    """Xcoil 'wave': all phases on every layer, via-stitched T/B track pairs."""

    kind: Literal["wave"] = "wave"
    r_inner_mm: float
    r_outer_mm: float
    turns: int  # Xcoil turns (tracks per phase and pole pair)
    trace_width_mm: float
    clearance_mm: float
    end_width_outer_mm: float | None = None
    end_width_inner_mm: float | None = None
    corner_style: CornerStyle = CornerStyle.ROUND
    fillet_radius_mm: float = 0.4
    wave_style: WaveStyle = WaveStyle.INVOLUTE  # Xcoil waveStyle
    bus_width_mm: float  # Xcoil busWidth, the links between layers; the interconnect uses /connection/ring_width_mm


WindingSpec: TypeAlias = SpiralWindingSpec | SerpentineWindingSpec | WaveWindingSpec


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignParameters:
    """A complete design. Only parse_draft() and load_project() construct it from user data."""

    schema_version: Literal[1] = 1
    name: str
    phases: PhaseCount
    rotor: RotorSpec
    winding: WindingSpec
    stackup: Stackup
    vias: ViaSpec
    connection: ConnectionSpec
    outline: OutlineSpec
    operating: OperatingPoint
    materials: MaterialOverrides = MaterialOverrides()
    analysis: AnalysisOptions = AnalysisOptions()
    drc_rules: DrcRules

    @property
    def topology(self) -> TopologyKind: ...


def validate_design(design: DesignParameters) -> tuple[ValidationIssue, ...]:
    """Single-field ranges and cross-field relations (INVALID, UNSUPPORTED_RANGE). Winding and geometry feasibility are
    the generators' job (UNBUILDABLE)."""
```

Revision 2026-10-05 (U-D3, D-016): one board per phase. `SerpentineWindingSpec` gains `stack_mode` and
`board_gap_mm`. The defaults reproduce today's single board: with `StackMode.SINGLE` Xcoil places every layer on board
0 and the gap term `(nBoards - 1) * boardGap` is 0 (`engine.js` l.687-695; `verified` by reading, 2026-10-05). The gap
default 0.1 mm is Xcoil's default (l.54), so the golden parameter map needs no special case. What Xcoil does with
`stackMode = 'perPhase'`, each point `verified` by reading `/home/claude/serpentine/src/engine.js` on 2026-10-05:

- One board per phase: `nBoards = phases` and board k carries phase k (l.687, l.691). Layers are grouped by phase
  whatever `layerOrder` says (l.681).
- Every board uses one board's stack-up with `layersPerPhase` copper layers (`stackupFor(p, perBoard)`, l.686-688).
  The design's `stackup` therefore describes one board in this mode (UT-GEN-03).
- Board k's copper sits at `z = k * (boardThickness + boardGap) + zLocal`, and the stator is
  `nBoards * boardThickness + (nBoards - 1) * boardGap` thick (l.689, l.695). The serpentine analysis takes the
  symmetry plane from that stator thickness (l.869-872) and the link-via length from `statorThickness / nBoards`
  (l.969).
- Layer names carry a board prefix `B<k+1>:` when there is more than one board (l.706).
- The bus level offset that keeps vias of different phases apart is 0, because no two phases share a board (l.186).
- DRC skips a via against a layer of another board and a via pair on two boards (l.779, l.819).
- No on-board star or delta interconnect is built. When the interconnect is requested for three phases in star or
  delta, Xcoil warns `INTERCONNECT_EXTERNAL`: "One board per phase: make the ... connection between boards
  externally" (`wantIc`, l.2525-2535). The analysis still applies the
  chosen connection (`tests.js` l.468).
- Xcoil offers the option for serpentine only (`ui.js` l.54 and l.107, `only: 's'`); wave layouts always report one
  board (l.1940, l.2192).

Validation adds two relations for `one_board_per_phase` (UT-GEN-03): the copper layer count of `stackup` equals
`layers_per_phase`, and `board_gap_mm` follows Xcoil's clamp range 0 to 10 mm (l.127). `layer_order` and
`board_gap_mm` are temporarily inapplicable in the modes where Xcoil disables them (`ui.js` l.236), which REQ-F-32
covers through `FieldSpec.topologies` plus the applicability rule of the form (U-M4c).

FIELDS rows that the U-M2a fix round adds to `src/embodic/model/fields.py` `_ROWS` (widget ids from screens.md §4;
limits and step from Xcoil `normalizeParams` l.127 and `ui.js` l.107):

| Pointer | Kind | Unit | Required | Default (neutral value) | Group | Widget id | Limits | Step | Topologies |
|---|---|---|---|---|---|---|---|---|---|
| `/winding/stack_mode` | design | none | no | `"single"` | LAYERS | `param-stack-mode` | choices `single`, `one_board_per_phase` | none | serpentine |
| `/winding/board_gap_mm` | design | mm | no | 0.1 | LAYERS | `param-board-gap` | `Limits(sign=NON_NEGATIVE, low=0, high=10)` | 0.05 | serpentine |

Both are design fields, so they can never be marked measured, and a blank serpentine draft starts them at their
neutral values with the `default` chip (D-019). The screens.md binding keys `/winding/serpentine/stack_mode` and
`/winding/serpentine/board_gap_mm` are labels only; the UI binds through `widget_id` (§2.3).

Revision 2026-10-08 (U-D4, D-031a, D-031c and D-031e). FIELDS rows that U-M2d-3 adds or confirms in
`src/embodic/model/fields.py` `_ROWS`. The first row is new. The second row states the range of the row that exists on
main c7fff3a, which has no limits (`verified` by reading `fields.py` l.122).

| Pointer | Kind | Unit | Required | Default (neutral value) | Group | Widget id | Limits | Step | Topologies |
|---|---|---|---|---|---|---|---|---|---|
| `/outline/screws/*/hole_diameter_mm` | design | mm | yes, once the pattern exists | none | FASTENERS | `param-screw-hole-diameter` | `Limits(sign=POSITIVE)` | none | all |
| `/winding/coil/first_coil_angle_rad` | design | rad | no | pi / 2 | COIL | `param-first-coil-angle` | `Limits()`: any finite value | none | spiral |

- Hole diameter. The decision fixes kind, unit, requirement, default and widget. `POSITIVE` is an `assumption`: it
  matches the sign of `/vias/drill_mm` (`fields.py` l.167), and a hole of diameter 0 or less cannot be drilled. No
  supported range is set until Agent 5 cites a fastener table. The board outline takes its `Hole.diameter_mm` from this value (§5,
  `build_outline`). `size` and `fit` stay labels.
- First coil angle. The model accepts any finite value and stores it as typed, so the project file keeps what the user
  entered (§9.1). The spiral generator reduces it modulo 2 pi before it places coil 0. A negative angle is therefore
  buildable. The generator on main refuses it (§13 point 6, DEF-U-D4-01).
- Copper count per stack mode (D-031e, UT-GEN-03). `validate_design` checks, for a serpentine design, that the
  copper layer count of `stackup` equals `phases * layers_per_phase` for `StackMode.SINGLE` (Xcoil
  `stackupFor(p, perBoard)`, `engine.js` l.686-688) and `layers_per_phase` for `StackMode.ONE_BOARD_PER_PHASE`, else
  `INVALID_SERPENTINE_COPPER_COUNT` with the three pointers. Main checks only the second mode (§13 point 6,
  DEF-U-D4-02).

Revision 2026-10-08 (U-D7, D-035e; U-M3b report Q1, Q2 and Q4; `src/embodic/generators/wave/generate.py`,
`src/embodic/physics/analyse.py` and `resources/examples/wave_16p_example.embodic.json` on main 4aec992 and
`/home/claude/serpentine/src/engine.js`, `verified` by reading). Three wave decisions:

- No start angle in Phase 2. `WaveWindingSpec` gets no `start_angle_rad`. PR-14 rotates the wave through the private
  seam `generate_wave_rotated(design, registry, start_angle_deg)` (`generate.py` l.181), and `generate_wave` calls it with 0.
- Two width fields. Xcoil's single `busWidth` sizes both the links between layers and the interconnect (U-M3b Q2,
  `engine.js` l.1673 and l.1226). embodic keeps two fields: `/winding/bus_width_mm` sizes the links and
  `/connection/ring_width_mm` sizes the interconnect (`generate.py` l.85 and l.158). The wave example sets both to
  1.0 mm, Xcoil's default `busWidth` (`engine.js` l.44).
- Via length from the layer span. embodic computes a wave via's barrel resistance over the board thickness that a
  through via spans (`analyse.py` l.181). Xcoil uses the spacing of the first two copper layers, `hAdj` (l.2048). The
  embodic length is the physical one. The phase resistance of the wave example is 0.27 % higher than Xcoil's for this
  reason alone (U-M3b Q4, `inferred` from its report). U-M3-fix records the difference as an XD-WAVE entry in
  `tests/golden/expected_diffs/wave.toml`, which holds no entry on main 4aec992.

Wave copper count (D-035e, as D-031e did for the serpentine). On main the wave generator refuses an odd copper count
or a count below 2 with `UNBUILDABLE_WAVE_LAYER_COUNT` on `/stackup/layers`, and `validate_design` has no wave rule
(U-M3b deviations). U-M3-fix moves the rule into `validate_design`. The INVALID code it reports is U-M3-fix's to name.

Revision 2026-10-09 (U-D8, D-031e, D-035e, D-037d; main 8a297a0, `verified` by reading). Copper count per topology:

| Topology | `validate_design` (INVALID, ERROR) | Generator refusal (UNBUILDABLE) |
|---|---|---|
| wave | `INVALID_WAVE_COPPER_COUNT` on `/stackup/layers` when the copper count is below 2, odd, or above `WAVE_LAYERS_MAX` = 16 (`model/validate.py` l.31, l.210-215; text in `errors/catalogue/wave.py` l.24) | `UNBUILDABLE_WAVE_LAYER_COUNT`, same condition (`generators/wave/generate.py` l.218-220) |
| serpentine | `INVALID_SERPENTINE_COPPER_COUNT` on `/stackup/layers`, `/winding/layers_per_phase` and `/winding/stack_mode` when the count differs from `layers_per_phase` (one board per phase) or `phases * layers_per_phase` (single) (`model/validate.py` l.196-200; text in `errors/catalogue/model.py` l.38) | `UNBUILDABLE_SERPENTINE_COPPER_COUNT` when the count differs from the planned layers per board (`generators/serpentine/generate.py` l.385-387) |

`validate_design` runs both rules from `CROSS_FIELD_RULES` (`model/validate.py` l.343-356). The serpentine row also
closes DEF-U-D4-02 (§13 point 7).

Revision 2026-10-09 (U-D8, D-035e, D-036e, D-037d; corrected by U-D9 with D-038b and D-038c;
`tests/golden/expected_diffs/wave.toml` and `tests/golden/m3_wave/test_gr22_results.py` on main 3acb044, `verified` by
reading). XD-WAVE text. `wave.toml` holds two entries.

- XD-WAVE-001 (`wave.toml` l.12) covers the overlap wave with a star connection. embodic counts the three tap stubs as
  phase link copper, and Xcoil sets its link sum to zero (`engine.js` l.2172). Its status is `verified` (U-E8,
  `docs/phase2/engineering/open_positions_m3.md` §1a): the stubs are the only copper between each minus terminal and
  the star ring, so each carries I_line, and Xcoil's zero is an omission.
- XD-WAVE-002 (`wave.toml` l.21) covers the overlap wave with a delta connection, case
  `wave-analysis-overlap-l2-m3-p16-t2-delta`. embodic counts the three line leads at I_line^2 x R and gets
  1.962909e-03 W. That value is an upper bound, and Xcoil reports 0 W because its overlap path leaves `icR` null
  (`engine.js` l.2154). Its status is `inferred`. The true value is `unresolved` until the spec names the external
  closure point (U-E8, `open_positions_m3.md` §1b).
- `test_gr22_interconnect_loss_matches_xcoil_for_star_and_delta` (`test_gr22_results.py` l.154) applies both entries.
  `test_gr22_overlap_difference_is_the_uncounted_copper_and_nothing_else` (l.168) reclassifies the uncounted copper as
  carrying no current and then finds embodic equal to Xcoil, so no other copper differs.
- The via-length difference above has no XD-WAVE entry. D-038b corrects D-035e: no entry is owed.
  `test_gr22_phase_resistance_differs_from_xcoil_only_by_the_via_barrel_length` (`test_gr22_results.py` l.124) removes
  the barrel length at function level and compares.

Revision 2026-10-13 (U-D15, claude-sonnet-5-5; D-046 and the U-M5h report; `src/embodic/model/validate.py`,
`src/embodic/errors/catalogue/model.py`, `src/embodic/physics/analyse.py` and `src/embodic/api.py` on main 5e74acc,
`verified` by reading unless a line says otherwise). The harmonic list, `/analysis/harmonics`. The list starts with
harmonic 1, and every entry is odd and at least 1. `validate_design` reports two codes:

| Code | Category, severity | Pointer | Fires when | Message | Source |
|---|---|---|---|---|---|
| `INVALID_HARMONIC_FUNDAMENTAL` | INVALID, ERROR | `/analysis/harmonics` | the list is empty, or its first entry is not 1 | "The harmonic list must start with the fundamental, harmonic 1." | `validate.py` l.339-340; `catalogue/model.py` l.64 |
| `INVALID_HARMONIC` | INVALID, ERROR | `/analysis/harmonics/<position>`, one per bad entry | an entry is below 1 or is even; `value` holds the entry | "Harmonic orders must be odd and positive." | `validate.py` l.341-343; `catalogue/model.py` l.63 |

The two rules are independent. `(2, 1)` raises both codes, `(3, 1)` raises only the first, and `(1, 2)` raises only the
second.

- Where the rule comes from. §8 says "Harmonic 1 is index 0" for `CircuitSolution.phase_emf_phasor_v_s_per_rad`.
  `analyse` reads `emf[phase][0]` as the fundamental for `ke_ph` and `emf_angle_ph` (`physics/analyse.py` l.298-299),
  and EQ-18 divides the THD sum by Ke_1 (`equation_specification.md` l.388). U-M5h found that `_harmonics` checked only
  the odd and positive entries, so no rule held index 0 to harmonic 1 (its report).
- What a bad list did before the rule. `()` raised IndexError in physics, found by the release run on 10c6411 in the
  nightly profile (comment at `test_pipeline_properties.py` l.94). `(3, 5)` raised KeyError. `(3, 1)` returned the
  constant of n = 3 as Ke with no issue. These come from the U-M5h report and the docstring at `test_validate.py`
  l.33. They were not re-run here, so they are `inferred`.
- The stop. `issue()` makes every issue an ERROR unless the caller says otherwise (`validate.py` l.45), and `compute`
  returns after the validate stage when any issue is an ERROR, before geometry, DRC and physics (`api.py` l.270-283).
  `analyse` does not check the list itself: a grep of `analyse.py` finds `harmonics` only in lines that compute with
  it (l.249 to l.381). A caller that bypasses `compute` has to validate first.
- Registration. `_harmonics` (`validate.py` l.337-343) is in `CROSS_FIELD_RULES` (l.346-359). The range l.343-356 given
  for that tuple under "Copper count per topology" above was true on main 8a297a0 and has moved.
- Tests. `test_a_harmonic_list_that_does_not_start_with_the_fundamental_is_an_error` (`tests/unit/model/test_validate.py`
  l.32) expects exactly one issue, `INVALID_HARMONIC_FUNDAMENTAL` with the pointer `/analysis/harmonics`, for `()`,
  `(3, 5)` and `(3, 1)`. The test at l.40 accepts `(1,)` and `(1, 3, 5, 7, 9, 11, 13)`. PR-05 pins the empty list
  (`test_plan.md` §5.2). No test names `INVALID_HARMONIC` or passes an even or a negative entry (a grep of `tests`), so
  that rule is `not tested`.

### 2.3 Field table, draft and the new-design flow (ADR-0010)

One table drives required-field checks, form generation, units shown next to inputs, applicability (REQ-F-32) and the
field kind that decides whether an input can be marked measured.

```python
class FieldKind(StrEnum):
    DESIGN = "design"  # geometry, layer configuration, operating point
    PROPERTY = "property"  # B_r, mu_r, finished copper thickness, plating, h, material overrides


JsonValue: TypeAlias = "None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]"
Choice: TypeAlias = str | int


class ValueType(StrEnum):  # embodic.model.schema; GROUP and LIST leaves exist while their container is None or []
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    TEXT = "text"
    CHOICE = "choice"
    INT_LIST = "int_list"
    INT_GROUPS = "int_groups"
    CHOICE_LIST = "choice_list"
    GROUP = "group"
    LIST = "list"


class FieldGroup(StrEnum):  # form group, in form order (screens.md sections 1 to 5)
    DESIGN = "design"
    COIL = "coil"
    PHASES = "phases"
    LAYERS = "layers"
    OUTLINE = "outline"
    FASTENERS = "fasteners"
    STACKUP = "stackup"
    ROTOR = "rotor"
    OPERATING = "operating"
    DRIVE = "drive"
    COOLING = "cooling"
    MATERIALS = "materials"
    ANALYSIS = "analysis"
    MANUFACTURING = "manufacturing"


class Sign(StrEnum):  # physical validity; breaking it is INVALID
    ANY = "any"
    POSITIVE = "positive"
    NON_NEGATIVE = "non_negative"


@dataclass(frozen=True, slots=True, kw_only=True)
class Limits:
    """`sign` is validity (INVALID); `low` to `high` is the supported range (UNSUPPORTED_RANGE, Xcoil clamps to it)."""

    sign: Sign = Sign.ANY
    low: float | None = None
    high: float | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class FieldSpec:
    pointer: str  # JSON pointer into the "design" object, list items as "/stackup/layers/*/thickness_mm"
    kind: FieldKind
    unit: Unit | None  # None for enums, names and booleans
    required: bool  # required while its container exists; a blank draft leaves it empty
    topologies: frozenset[TopologyKind]  # where the field applies
    neutral_value: JsonValue = None  # optional fields only; written into a blank design (ADR-0010 decision 2)
    value_type: ValueType
    choices: tuple[Choice, ...] = ()
    nullable: bool = False
    variant: Choice | None = None  # tagged-union member owning the field ("circle", "arc", ...); None if all have it
    group: FieldGroup
    widget_id: str | None  # objectName in screens.md; the join key between form and model
    limits: Limits = Limits()
    step: float | None = None  # Up and Down increment in the form


FIELDS: tuple[FieldSpec, ...]  # every field of every topology; built at import from the type hints plus one row each


def field_specs(topology: TopologyKind) -> tuple[FieldSpec, ...]: ...
def field_for(pointer: str, values: Mapping[str, JsonValue]) -> FieldSpec:
    """The field of a concrete pointer; the sibling `kind` or `shape` value in `values` picks the union member."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignDraft:
    """What the form edits. Values may be missing; nothing is computed from a draft (D-014)."""

    topology: TopologyKind
    values: Mapping[str, JsonValue]  # pointer -> value; absent pointer = missing


@dataclass(frozen=True, slots=True, kw_only=True)
class DraftIncomplete:
    missing: tuple[str, ...]  # pointers of required fields without a value, in form order
    issues: tuple[ValidationIssue, ...]  # INVALID issues of the fields that do have values


def blank_draft(topology: TopologyKind) -> DesignDraft:
    """Required fields absent; optional fields at their neutral value."""


def parse_draft(draft: DesignDraft) -> DesignParameters | DraftIncomplete: ...


def draft_from_design(design: DesignParameters) -> DesignDraft: ...
```

Revision 2026-10-05 (U-D2, U-M2a report). The names `field_specs`, `parse_draft` and `validate_design` stay as written.
U-M2a's additions are ratified and restated above.

- `FieldSpec` gains `value_type`, `choices`, `nullable`, `variant`, `group`, `widget_id`, `limits` and `step`. The
  type hints decide `required`, `neutral_value`, `value_type`, `choices` and `topologies`; one row per field adds the
  rest (`src/embodic/model/fields.py` `_ROWS`). The import fails when a leaf has no row or a row has no leaf, so the
  table cannot drift from the dataclasses.
- `widget_id` is the only join between a form widget and a field. The UI binds through it, never through the binding
  keys written in screens.md (`screen_model_reconciliation.md`).
- `embodic.model.schema` is a new module: one walk over the dataclass annotations gives the leaves, JSON conversion
  (`to_json`, `from_json`, `design_from_json`) and pointer helpers (`flatten`, `unflatten`, `field_key`, `pattern_of`).
- A field of one tagged-union member is keyed `<pointer>#<tag>` (for example `/outline/board/radius_mm#circle`).

Constants are not fields. `/schema_version` (`Literal[1]`), `/winding/kind` (the topology tag) and
`/analysis/edge_correction` (`Literal["off"]`) are one-value literals. They appear in the project file and in
`design_hash`, but not in `FIELDS`, a draft or the provenance map. `DesignDraft.topology` sets `/winding/kind`.

### 2.4 Provenance (D-007, D-014, D-019)

Provenance is derived, not typed by hand. A design has one origin: an example, or a blank design. The first matching
rule gives a field's provenance.

1. `measured` for a property field the user marked with a named source.
2. `example` while the value equals the value in the origin example.
3. `default` while the design has a blank origin and the value equals the field's `FieldSpec.neutral_value` (the
   documented default of an optional field, D-019). Required fields have no neutral value, so they never get `default`.
4. `user` otherwise.

Re-entering the current value changes nothing. Setting a changed field back to the origin's value makes it `example` or
`default` again (value-based, keystroke independent, consistent with Phase 1 PR-12 and DEF-21).

Revision 2026-10-04 (U-D1): `DEFAULT` and `DefaultValue` added and rule 3 written, per D-019 (provenance values `user`,
`example`, `default`, `measured`). `EXAMPLE` was already present. D-019's "`InputSource` gains `example`" is met by
`InputRef.provenance` (§3), which uses this enum.

```python
class Provenance(StrEnum):
    USER = "user"
    EXAMPLE = "example"
    DEFAULT = "default"
    MEASURED = "measured"


@dataclass(frozen=True, slots=True, kw_only=True)
class UserValue:
    provenance: Literal[Provenance.USER] = Provenance.USER


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleValue:
    provenance: Literal[Provenance.EXAMPLE] = Provenance.EXAMPLE
    example_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DefaultValue:
    provenance: Literal[Provenance.DEFAULT] = Provenance.DEFAULT


@dataclass(frozen=True, slots=True, kw_only=True)
class MeasuredValue:
    provenance: Literal[Provenance.MEASURED] = Provenance.MEASURED
    source: str  # datasheet, coupon or LCR record; never empty (mark_measured refuses an empty source)


FieldProvenance: TypeAlias = UserValue | ExampleValue | DefaultValue | MeasuredValue
ProvenanceMap: TypeAlias = Mapping[str, FieldProvenance]  # concrete pointers ("/stackup/layers/0/thickness_mm")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleRef:
    example_id: str  # file stem in resources/examples
    example_sha256: str  # of the example's canonical design JSON


@dataclass(frozen=True, slots=True, kw_only=True)
class Measurement:
    pointer: str
    source: str


def derive_provenance(design: DesignParameters, origin: tuple[ExampleRef, DesignParameters] | None,
                      measurements: Sequence[Measurement]) -> dict[str, FieldProvenance]:
    """origin None means a blank design: rule 3 compares with field_specs(design.topology) neutral values."""


def mark_measured(design: DesignParameters, measurements: Sequence[Measurement], pointer: str,
                  source: str) -> tuple[Measurement, ...] | ValidationIssue:
    """Refuses (INVALID_MEASURED_SOURCE_EMPTY, INVALID_MEASURED_DESIGN_FIELD) instead of raising."""


def drop_stale_measurements(old: DesignParameters, new: DesignParameters,
                            measurements: Sequence[Measurement]) -> tuple[Measurement, ...]:
    """A measurement no longer applies once its field's value changes."""
```

## 3. `embodic.results`: Traceable, registry, analysis result

`Status`, the weakest-link order, `Assumption`, `AssumedInput`, `Tolerance` and `Traceable` keep their Phase 1 meaning.
`InputRef.provenance` now uses `Provenance`. `ValidityFlag` gains the DEF-23 fields.

```python
T = TypeVar("T")


class Status(StrEnum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    ASSUMPTION = "assumption"
    UNRESOLVED = "unresolved"
    NOT_TESTED = "not tested"


STATUS_ORDER_WEAKEST_FIRST: tuple[Status, ...] = (
    Status.UNRESOLVED, Status.NOT_TESTED, Status.ASSUMPTION, Status.INFERRED, Status.VERIFIED,
)


class GateVerdict(StrEnum):
    REUSE = "reuse"
    REUSE_WITH_CHANGE = "reuse with change"
    REPLACE = "replace"
    ADD = "add"
    CANNOT_VERIFY_YET = "cannot verify yet"


@dataclass(frozen=True, slots=True, kw_only=True)
class Assumption:
    id: str
    text: str
    status: Status
    source_ref: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class InputRef:
    pointer: str  # JSON pointer or "result:<quantity>" or "constant:<name>"
    value: float | int | str
    unit: Unit | None
    provenance: Provenance | None  # None for result references and registry constants
    kind: FieldKind | None
    label: Status | None  # ASSUMPTION for unmeasured property inputs; constant's EV status for registry constants


@dataclass(frozen=True, slots=True, kw_only=True)
class AssumedInput:
    item: str
    value_text: str
    reason: Literal["example", "unmeasured_property", "registry_constant", "equation_assumption"]
    label: Status
    dominant: bool


class ValidityEffect(StrEnum):
    CAP = "cap"  # badge capped at unresolved
    LIMITATION = "limitation"  # badge unchanged; limitation listed, optional one-sided tolerance add-on


class MetricBound(StrEnum):
    ESTIMATE = "estimate"
    LOWER_BOUND = "lower_bound"  # true value is at least the metric (EC-05: |B| proxy for B_z, DEF-23 a)
    UPPER_BOUND = "upper_bound"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidityFlag:
    code: str  # "RANGE_SKIN_DEPTH", "EC-05"
    message: str
    eq_id: str
    effect: ValidityEffect
    metric: float | None = None
    metric_bound: MetricBound = MetricBound.ESTIMATE
    one_sided_addon: float | None = None
    calibration_status: Status | None = None  # EC-05: inferred (one D09 case)
    transfer_status: Status | None = None  # EC-05: assumption (calibration applied to this rotor)
    threshold_status: Status | None = None  # EC-05: assumption (10 % cap)


@dataclass(frozen=True, slots=True, kw_only=True)
class Tolerance:
    relative: float | None
    absolute: float | None
    against: str
    source_ref: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Traceable(Generic[T]):
    quantity: str
    value: T
    unit: Unit
    eq_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    kind_tag: Literal["computed", "input", "derived", "count"] = "computed"
    assumptions: tuple[Assumption, ...] = ()
    inputs: tuple[InputRef, ...] = ()
    assumed_inputs: tuple[AssumedInput, ...] = ()
    validity: tuple[ValidityFlag, ...] = ()
    tolerance: Tolerance | None = None
    status: Status
    status_reasons: tuple[str, ...] = ()
    label: str | None = None  # "estimate" / "guideline (unverified)"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidityCheckSpec:
    """Registry `validity_checks` entry (Agent 2 owns the content). DEF-23 adds the four status/bound fields."""

    id: str
    name: str
    metric: str
    parameters: Mapping[str, float | str]
    basis: str
    rule: str
    threshold: float
    metric_bound: MetricBound
    calibration_status: Status
    transfer_status: Status
    threshold_status: Status
    independent_oracles: tuple[str, ...]  # e.g. ("OR-01",)
    dependent_oracles: tuple[str, ...]  # share the calibration source, e.g. ("OR-07", "OR-08")


@dataclass(frozen=True, slots=True, kw_only=True)
class RegistryConstant:
    name: str
    value: float
    unit: Unit
    source: str | None  # EV-ID
    status: Status


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationEntry:
    id: str
    name: str
    formula: str
    gate: GateVerdict
    status: Status  # evidence status of the equation
    sources: tuple[str, ...]
    tolerance: Tolerance | None
    dominant_assumptions: tuple[str, ...]
    validity_checks: tuple[ValidityCheckSpec, ...]
    tests: tuple[str, ...]
    implementation: str | None
    constants: tuple[RegistryConstant, ...]
    label: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceEntry:
    id: str
    claim: str
    document: str
    location: str
    status: Status


@dataclass(frozen=True, slots=True, kw_only=True)
class Registry:
    version: str
    equations: Mapping[str, EquationEntry]
    evidence: Mapping[str, EvidenceEntry]
    passed_tests: frozenset[str]  # registry test IDs (EQT-nn-kind) that passed in this build (§3.1); empty without evidence
    issues: tuple[ValidationIssue, ...] = ()
    evidence_build_id: str | None = None  # PassedTestsEvidence.build_id when the evidence applies (§3.1), else None

    def equation(self, eq_id: str) -> EquationEntry: ...
    def constant(self, name: str) -> RegistryConstant: ...
    def tests_passed(self, eq_id: str) -> bool:
        """True when the equation links at least one test and every linked test is in passed_tests (registry.py l.143)."""
    def test_state(self, eq_id: str) -> Status:
        """NOT_TESTED until every linked test passed in this build, else the equation status."""


def load_registry(root: Path | None = None) -> Registry:
    """Reads resources/evidence/equations.v1.json and evidence.v1.json (packaged copies, tools/sync_registry.py), then
    passed_tests.v1.json when it exists and applies (§3.1). A missing, unreadable, malformed or stale evidence file gives
    an empty passed_tests and evidence_build_id None; it never raises and adds no issue."""


def combine_status(*statuses: Status) -> Status: ...


def traced(quantity: str, value: T, unit: Unit, *, eq_ids: Sequence[str], inputs: Sequence[InputRef],
           registry: Registry, validity: Sequence[ValidityFlag] = (), kind_tag: Literal["computed", "input", "derived",
           "count"] = "computed") -> Traceable[T]:
    """Badge = weakest(equation status, test state, validity cap). Inputs build the tag only (D-007)."""


def format_value(t: Traceable[float], *, significant: int = 3) -> str:
    """Locale-independent, SI prefixes, U+2212 minus, U+00A0 before the unit (REQ-L-07, U-S4e ruling e1)."""
```

Result containers. Phase 1 `AnalysisResult` fields are kept; topology-specific geometry values move to the generator's
detail record (§6).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class LayerResult:
    layer: str
    z_mm: Traceable[float]
    b1_peak_mid_radius_t: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseResult:
    phase: Phase
    ke_peak_v_s_per_rad: Traceable[float]
    resistance_20c_ohm: Traceable[float]
    resistance_operating_ohm: Traceable[float]
    circulating_loss_w: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class TorqueSpeedEstimate:
    speed_rpm: Traceable[tuple[float, ...]]
    torque_n_m: Traceable[tuple[float, ...]]
    power_w: Traceable[tuple[float, ...]]
    no_load_speed_rpm: Traceable[float]
    base_speed_rpm: Traceable[float]


@dataclass(frozen=True, slots=True, kw_only=True)
class AnalysisResult:
    ke_phase_v_s_per_rad: Traceable[float]  # EQ-06, EQ-09
    ke_line_v_s_per_rad: Traceable[float]  # EQ-09
    ke_line_peak_v_s_per_rad: Traceable[float]  # EQ-18, EQ-09: peak of the line waveform per mech. rad/s (U-M2e-3)
    kt_n_m_per_a: Traceable[float]  # EQ-09
    kv_rpm_per_v: Traceable[float]  # EQ-09
    winding_factor_1: Traceable[float]  # EQ-08 (spiral); kind_tag "derived" from the generator for serpentine/wave
    resistance_phase_20c_ohm: Traceable[float]  # EQ-10, EQ-11
    resistance_phase_operating_ohm: Traceable[float]
    resistance_line_ohm: Traceable[float]
    emf_phase_rms_v: Traceable[float]
    torque_n_m: Traceable[float]
    loss_copper_w: Traceable[float]
    loss_eddy_w: Traceable[float]  # EQ-12
    loss_circulating_w: Traceable[float]  # EQ-07
    loss_delta_circulating_w: Traceable[float]  # EQ-19
    loss_interconnect_w: Traceable[float]  # EQ-23 P_ic; U-M2e-4 (D-031f)
    loss_total_w: Traceable[float]  # EQ-26 P_Cu + P_eddy + P_circ + P_delta,circ + P_ic; U-M2e-4
    output_power_w: Traceable[float]  # EQ-26 P_out = T * omega_m; U-M2e-4
    efficiency: Traceable[float]  # EQ-26 P_out / (P_out + P_loss), electromagnetic only; U-M2e-4
    motor_constant_n_m_per_sqrt_w: Traceable[float]  # EQ-26 K_m = T / sqrt(P_Cu); U-M2e-4
    thd_phase: Traceable[float]  # EQ-18
    thd_line: Traceable[float]
    current_density_a_per_mm2: Traceable[float]  # EQ-22
    skin_depth_mm: Traceable[float]  # EQ-13
    inductance_estimate_h: Traceable[float]  # EQ-14, badge unresolved, label "estimate"
    ipc_guideline_current_a: Traceable[float]  # EQ-15, badge unresolved, label "guideline (unverified)"
    mass_copper_g: Traceable[float]  # EQ-16
    mass_laminate_g: Traceable[float]
    temperature_rise_k: Traceable[float]  # EQ-17
    edge_leakage_fraction: Traceable[float]  # EC-05 metric e_edge; status assumption (transfer, DEF-23)
    layers: tuple[LayerResult, ...]
    phases: tuple[PhaseResult, ...]
    emf_waveform_v: Traceable[tuple[float, ...]]  # EQ-18, one electrical period
    torque_speed: TorqueSpeedEstimate | None  # EQ-20; None without dc_link_v
    registry_version: str
```

Revision 2026-10-08 (U-D4, D-031f). `ke_line_peak_v_s_per_rad` is on main (`src/embodic/results/analysis_result.py`,
U-M2e-3); OR-01 compares it with D08's measured peak (D-030). The five loss-sum fields are the U-M2e-4 contract; §8
says how `analyse` computes them. Their values follow Xcoil `applyConnection` (`engine.js` l.1419-1434; `verified` by
reading, 2026-10-08): the open connection has no interconnect loss, the efficiency is 0 without output power, and
`motor_constant_n_m_per_sqrt_w` is 0 when the copper loss or the phase current is 0, as Xcoil reports it. Each field
cites its EQ-ID, so its badge follows the registry status of EQ-23 and EQ-26 and the inputs it depends on (D-007).

Revision 2026-10-08 (U-D6, DEF-M2e4-01). `motor_constant_n_m_per_sqrt_w` stays in `AnalysisResult` with the unit
`Unit.N_M_PER_SQRT_W` of §1. Main a336531 has neither: the field is absent from
`src/embodic/results/analysis_result.py` and the unit from `src/embodic/units.py` (`verified` by reading, 2026-10-08).
The kernel `motor_constant_n_m_per_sqrt_w` is on main (`src/embodic/physics/circuit.py` l.195). U-M2-fix3 adds the unit
and fills the field from that kernel. The other four loss-sum fields are on main.

Revision 2026-10-09 (U-D9, D-038e; `src/embodic/results/labels.py` on main 3acb044, `verified` by reading and by
running). The module `embodic.results.labels` holds the English display label of every `AnalysisResult` field. Before it
existed, the Key results table of the PDF report printed raw field names (U-M4a report, Fable's finding ii).

```python
QUANTITY_LABELS: Mapping[str, str]  # AnalysisResult field name -> English label, e.g. "ke_line_peak_v_s_per_rad" -> "Line back-EMF constant, peak"
```

- The keys are the 35 `AnalysisResult` field names, one label each and no extra key
  (`test_every_analysis_result_field_has_exactly_one_label`, `tests/unit/results/test_labels.py` l.15). The labels are
  distinct English text without underscores (l.20).
- The mapping is read-only (`MappingProxyType`, `labels.py` l.10), and `embodic.results` exports it (`__init__.py` l.5).
- The labels follow the equation titles of `equation_specification.md`. The two labels that the summary strip of the
  shell shows have the same text as `shell.sum-ke.label` and `shell.sum-r-phase.label` in `embodic.ui.strings.shell`
  (`test_labels.py` l.27).
- Readers. The PDF report prints these labels in its Key results table (through `quantity_title`, `io/report.py` l.119). The results view-model of
  §11 reads the same mapping for `ResultRow.label`, so the rail, the cards and the PDF name a quantity alike and UI
  strings do not repeat the labels. No code builds `ResultRow` on main 3acb044; U-M4d does.

Revision 2026-10-09 (U-D10, D-039 e, D-040; `src/embodic/results/labels.py` and `tests/unit/results/test_labels.py` on
main fd190c1, `verified` by reading). Card and report titles carry the symbol that the equation specification writes
(U-M4d-fix).

```python
QUANTITY_SYMBOLS: Mapping[str, str]  # AnalysisResult field name -> symbol exactly as equation_specification.md writes it


def quantity_title(quantity: str) -> str:
    """The label, then the symbol when one is stated, for example "Copper loss P_Cu"."""
```

- `QUANTITY_SYMBOLS` sits beside `QUANTITY_LABELS` (`labels.py` l.10 and l.53) and holds 25 symbols on main 9776555
  (`verified` by running `len(QUANTITY_SYMBOLS)`; 21 on main fd190c1, plus the four Greek ones below). Each entry
  carries the specification line in a comment, for example `Ke_ph` (l.219) and `R_ph` (l.422). A field with no stated
  symbol has no entry: the peak line constant, the rms phase EMF, THD (an abbreviation) and the IPC current (the bare "I"
  of EQ-15), as the comment at l.50 says. The mapping is read-only.
- `quantity_title` (l.84) returns the label alone for a field without a symbol. The results view-model reads it for
  `ResultRow.title` (§11, `ui/viewmodels/results.py` l.77) and the PDF Key results table prints it (`io/report.py`
  l.119). `embodic.results` exports only `QUANTITY_LABELS`, so callers import the other two names from
  `embodic.results.labels`.
- `test_symbols_belong_to_labelled_fields` (`test_labels.py` l.42) keeps every symbol key a labelled field.
  `test_every_symbol_is_written_in_the_equation_specification` (l.47) searches the specification for each symbol, so
  an invented symbol fails.

Revision 2026-10-09 (U-D11, D-040 a and c; `src/embodic/results/labels.py`, `results/formatting.py` and
`tests/static/test_lg_language.py` on main 9776555, `verified` by reading and by running `test_labels.py`,
`test_lg_language.py`, `test_registry.py` and `test_formatting.py`: 65 passed). U-M4c-4 (b) built D-040 a. The Greek symbols and the U+00A0 joiner are the two uses of one
per-module allowance in LG-01.

- The four held-back symbols are in. `efficiency` is "η" (specification l.509), `skin_depth_mm` is "δ" (l.326),
  `temperature_rise_k` is "ΔT" (l.373) and `loss_delta_circulating_w` is "P_δ,circ" (l.509) (`labels.py` l.71, l.74,
  l.75 and l.69). No other symbol of the mapping has a letter outside ASCII.
- LG-01 stays strict outside the one module (D-040 a). `ALLOWED_SYMBOLS` (`tests/static/test_lg_language.py` l.9) is
  unchanged: `°µΩ²³·−×±≤≥√`. `MODULE_SYMBOLS` (l.12) maps a module name to the extra characters that module may hold in
  a string literal, and today has one entry: `embodic.results.labels` admits η, δ and Δ. `is_allowed_in_english_text`
  (l.20) takes the module name as its second argument. ρ is not admitted, and no symbol of the mapping uses it, which
  closes the question U-D10 left open.
- `test_lg01_admits_the_spec_greek_letters_in_the_label_module_only` (l.81) plants the four symbols in
  `embodic.results.labels`, where only a stray ω is reported, and in `embodic.errors`, where U+0394, U+03B4 and U+03B7
  are reported.
- U+00A0 between a number and its unit (D-040 c, U-S4e ruling e1). `format_quantity` joins them with `UNIT_SPACE`
  (`results/formatting.py` l.22, used by `_with_unit`, l.76). Every other place that writes a value and its unit
  imports the same constant: the PDF report (`io/report.py` l.63, l.65, l.134, l.165), the SVG layer label
  (`svg_writer.py` l.134), the results view-model (`ui/viewmodels/results.py` l.51, l.134, l.136, l.446), the DRC table
  (`ui/views/checks_view.py` l.172) and the cursor readout (`ui/views/main_window.py` l.675). A number and its unit
  never part at a line end.
- `UNIT_SPACE` is the U+00A0 literal on main 4fda98d (`results/formatting.py` l.22, with `# noqa: RUF001`). U-M4e-1b
  replaced `chr(0x00A0)` by the character after LG-01 admitted it (revision 2026-10-11, U-D12, D-040 c, which
  `docs/decision_log.md` l.46 records). `MODULE_SYMBOLS` (`tests/static/test_lg_language.py` l.13) has two entries,
  `embodic.results.labels` for η, δ and Δ and `embodic.results.formatting` for U+00A0. Every other module still reports
  U+00A0 as a non-English character. `test_lg01_admits_the_no_break_space_in_the_formatting_module_only` (l.96) plants
  the character in `embodic.results.formatting`, where it passes, and in `embodic.errors`, where the message names U+00A0.
- The unit tests expect the character: the `CASES` of `tests/unit/results/test_formatting.py` write `"1.00\u00a0kΩ"`,
  `"500\u00a0mΩ"` and the like, and `test_formatting_engineering_text` (l.44) compares against them.

### 3.1 Evidence of passing tests (revision 2026-10-12, U-D13; D-007, D-023, D-034)

The gap. `parse_registry` builds every `Registry` with `passed_tests=frozenset()` (`results/registry.py` l.185), and
`load_registry` (l.157) returns that registry unchanged. `Registry.tests_passed` (l.143) is therefore False for every
equation, `_link` passes False into `ChainLink.tests_passed` (`results/traceable.py` l.231 to l.234), and `derive_badge` adds
`not tested` for every link (`results/status.py` l.118 to l.120). Every computed result of an installed build reads
`not tested`, and the equation guide shows `not tested` in its "Test state in this build" row
(`ui/viewmodels/results.py` l.734). All of this is `verified` by reading main 7b9b4c9.

What a registry test ID is. The registry links test IDs of the form `EQT-<nn>-<kind>` to each equation
(`resources/evidence/equations.v1.json`, 63 distinct IDs over 30 equations, `verified` by counting; the kinds GR, CFxx, O1, O2, EC and UTk are defined in
`docs/phase2/engineering/equation_specification.md` l.27). No pytest test named an EQT ID on main 7b9b4c9 (`verified` by
grep. In `tests/` the string occurred only in `tests/unit/results/test_registry.py`, which checks the ID format). U-M5o has
since placed the markers (§13 point 12). A pytest
node ID and a registry test ID are different things, so the build needs a declared link between them before any
evidence can exist.

The link. A test that realises a registry test ID carries the marker `@pytest.mark.eqt("EQT-05-CF01", ...)`.
`tests/conftest.py` registers the marker beside `req` and `eq` (`MARKERS`, l.10), and `ReqReport` writes a sorted `"eqt"`
list into each record of `build/req_report.json` (l.53 to l.58). `tools/trace_matrix.py` reads only `nodeid`, `req` and
`outcome` (`parse_report`, l.56), so the extra key changes nothing there. U-M5o places the markers (`work_breakdown.md`
§8), and Agent 2 reviews the mapping. A registry test ID that no test carries never passes, so its equation keeps the
badge `not tested`, which is what D-007 asks for an untested equation.

The file. `resources/evidence/passed_tests.v1.json` is a build product. It is git-ignored and never committed. The wheel
carries it as `embodic/_resources/evidence/passed_tests.v1.json`, because hatchling's `force-include` copies a
git-ignored file under `resources/` (`verified` by building a wheel and an sdist from a scratch copy of main 7b9b4c9 with
the file present and its path in `.gitignore`, U-D13). The sdist leaves it out (same build), so a wheel built from the
sdist reads `not tested`. That is correct, because no gate ran on that build. The file is one JSON object with sorted
keys:

| Key | Type | Value |
|---|---|---|
| `format` | string | `"embodic.passed-tests"` |
| `format_version` | integer | `1` |
| `build_id` | string | `<embodic_version>+g<first 12 hex digits of git_commit>.<generated_utc as YYYYMMDDThhmmssZ>` |
| `embodic_version` | string | `embodic.__version__` of the tested tree (`src/embodic/__init__.py` l.3) |
| `registry_version` | string | `Registry.version` of the tested tree (`v1+<12 hex>.<12 hex>`, `registry.py` l.165) |
| `source_sha256` | string | `package_source_sha256` of `src/embodic` (below), 64 hex digits |
| `git_commit` | string | the 40 hex digits of `git rev-parse HEAD` |
| `git_dirty` | boolean | true when `git status --porcelain` prints anything |
| `python`, `numpy` | string | `platform.python_version()` and `numpy.__version__` of the gate run (as in `VersionInfo`) |
| `platform` | string | `platform.platform()`. Never `platform.node()`, a user name or a home path (standing order 7) |
| `generated_utc` | string | ISO 8601 UTC time ending in `Z` |
| `gate_profile` | string | `"release"`, the only profile that writes the file |
| `passed_tests` | array of strings | the sorted registry test IDs that passed |
| `realised_by` | object | for each ID in `passed_tests`, the sorted pytest node IDs that carried it |

The writer. `tools/record_passed_tests.py` (new, U-M5b) is pure functions and one `main`:

```python
# tools/record_passed_tests.py (U-M5b): reads the REQ report of one gate run and writes the evidence file or nothing.

@dataclass(frozen=True, slots=True, kw_only=True)
class ReportRecord:
    nodeid: str
    outcome: str  # "passed", "failed", "skipped" or "not run" (tests/conftest.py ReqReport)
    eqt: tuple[str, ...]


def passed_registry_tests(records: Sequence[ReportRecord], registry_test_ids: frozenset[str]
                          ) -> tuple[frozenset[str], Mapping[str, tuple[str, ...]]]:
    """An ID passes when at least one record carries it and every record that carries it has outcome "passed".
    A skipped, xfailed (the report says "skipped"), failed or not-run record keeps its IDs out. Raises ValueError for an
    eqt ID that registry_test_ids does not hold, because a typo would otherwise never match and hide."""


def record_main(argv: Sequence[str] | None = None) -> int:
    """record_passed_tests.py --report build/req_report.json --profile release --out resources/evidence/passed_tests.v1.json
    Exit 1 and write nothing when the profile is not release, the report is missing, any record has outcome "failed",
    or an eqt ID is unknown. Otherwise write the file with the keys above and print one line: how many registry test
    IDs passed, of how many, and how many no test carries."""
```

Who runs it. `python tools/ci.py --profile release` deletes `resources/evidence/passed_tests.v1.json` before its first
gate, so a red run never leaves the file of an earlier build. It then runs every gate as today. When every gate passed,
it runs the record step as one more gate, "passed-test evidence (TR-05)", followed by the PK-10 step, which builds the
wheel and checks the file inside it (`test_plan.md` §5.7). The commit and nightly profiles neither write nor delete the
file. The report path stays `build/req_report.json` (`tools/ci.py` `gates_for`, l.50 and l.53).

The reader. `embodic.results.registry` gains the names below. `load_registry` calls them after `parse_registry`.
`parse_registry` stays pure and unchanged, so the fixtures of `tests/unit/results/registries.py` keep working.

```python
PASSED_TESTS_FILE = "passed_tests.v1.json"
PASSED_TESTS_FORMAT = "embodic.passed-tests"


@dataclass(frozen=True, slots=True, kw_only=True)
class PassedTestsEvidence:
    build_id: str
    embodic_version: str
    registry_version: str
    source_sha256: str
    git_commit: str
    git_dirty: bool
    python: str
    numpy: str
    platform: str
    generated_utc: str
    gate_profile: str
    passed_tests: frozenset[str]
    realised_by: Mapping[str, tuple[str, ...]]


def parse_passed_tests(document: object) -> PassedTestsEvidence | None:
    """The boundary parser: None for a wrong format or version, a missing key or a value of the wrong type. Never raises."""


def package_source_sha256(package_dir: Path) -> str | None:
    """One SHA-256 over every *.py below package_dir outside __pycache__, taken in the sorted order of the relative POSIX
    path strings. For each file it takes in the UTF-8 bytes of that path, one NUL byte, and the raw 32-byte digest of the
    file's bytes (the digest itself, not its hex text). Returns the 64 hex digits of the outer digest, or None when the
    folder holds no .py file (a frozen build). The 168 files of src/embodic hash in 5 to 16 ms on this container
    (checks/selftest_probe.py, U-D13). See the revision of 2026-10-13 below for the checked rule."""


def evidence_applies(evidence: PassedTestsEvidence, *, embodic_version: str, registry_version: str,
                     source_sha256: str | None) -> bool:
    """False (stale) when embodic_version or registry_version differs from the evidence, or when source_sha256 is not
    None and differs. A frozen build passes None and skips only the source comparison."""
```

Staleness. The U-D13 brief defines stale as a different embodic version or registry version. That rule alone lets a
source checkout keep the file of its last release run while a developer edits the physics code under the same version,
and the badges would then claim that tests passed for code no test ran. The source hash closes that gap. A wheel
installs the same `.py` files that the gate tested (PK-03 compares their hashes), so an unmodified install always
applies. A PyInstaller one-folder build holds compiled modules and no `.py` files (`inferred` from PyInstaller's
layout; U-M5c confirms), so it compares the two versions only.

What changes on screen. With an evidence file that applies, `Registry.tests_passed(eq_id)` is True for exactly the
equations whose every linked EQT ID is in `passed_tests`. For those equations:

1. `ChainLink.tests_passed` is True, so `derive_badge` stops adding `not tested` for that link. The badge becomes the
   weakest of the chain's evidence statuses and the validity cap, as D-007 states. A result whose chain is EQ-10 alone
   reads `verified`, the registry status of EQ-10. A result whose chain holds EQ-05 reads at most `inferred`. A chain that
   holds a `cannot verify yet` equation stays `unresolved`.
2. `Registry.test_state(eq_id)` returns the registry status of the equation (`verified`, `inferred`, `assumption` or
   `unresolved`), not always `verified`, and the guide row "Test state in this build" shows it.
3. `Registry.evidence_build_id` holds the build ID that the Tests dialog shows (§14).

Nothing else changes. A result with an empty chain (`input`, `derived`, `count`) stays `not tested` (`status.py` l.109).
The "n assumed inputs" tag (D-023), the provenance chips, the validity flags, labels such as "estimate", DRC and every
number stay as they are. A source checkout without the file behaves exactly as main 7b9b4c9 does. Tests: UT-RES-08
(reader), UT-RES-09 (badge change), TR-05 (writer) and PK-10 (wheel), in `test_plan.md` §5.7.

Revision 2026-10-13 (U-D14, claude-sonnet-5-5; D-045f; `src/embodic/results/registry.py`, `tools/record_passed_tests.py`
and `tools/ci.py` on main 6243163, `verified` by reading unless the text says it ran). Three points.

The source hash, exactly. `package_source_sha256` (`registry.py` l.228-243) builds one SHA-256 object, then walks the
`*.py` files below `package_dir` whose relative path has no `__pycache__` part, sorted by the relative POSIX path as a
Python string. For each file it feeds the object, in this order:

1. the UTF-8 bytes of the relative POSIX path,
2. one NUL byte,
3. `hashlib.sha256(file bytes).digest()`, the raw 32 bytes of that file's own digest.

The result is the `hexdigest()` of the outer object, 64 lowercase hex digits. The U-M5b report describes the hash as "adds
each file's raw 32-byte digest", which leaves out steps 1 and 2. The code is the rule, so the path and the NUL byte
count. `checks/source_hash_rule.py` applies the three steps in a separate loop and compares the result with the function
(`verified` by running `PYTHONPATH=src python3 docs/phase2/architecture/checks/source_hash_rule.py`, exit 0). On the 179
files of `src/embodic` on main 76f054b both give `01a6880473b6813d6e870776e3727805b0ab2a0e1962c3826ced30a09591c9b4`
(`verified` by running the check again there). Two misreadings give other values, so the wording matters. The hex text of
each file digest gives `2cbba600dd5be4c8f745552370d60bf00259881ab9a404af56d78ddb6ffbac55`. Leaving out the path and the
NUL byte gives `9aea9c6e87a9c8408761c4b9988e47004a7e7576234a7a22943d7b54edfe6734`. A renamed file changes the hash
although its bytes stay the same. The value is a measurement of that tree, not a constant to pin: the same function gave
`ae8cc9643477ef9221a7f7ed59fe8eec82309a7ca94bcd8f291ce7bfef33e0e4` on main 6243163, before the sources changed.

The profile key. The evidence file's key is `gate_profile`, in the table above, in `PassedTestsEvidence.gate_profile`
(`registry.py` l.178 and l.193) and in the writer (`tools/record_passed_tests.py` l.88). The command-line flag of the
writer is `--profile`; the JSON key is not `profile`. The value is `"release"`.

A leftover evidence file (D-045f, DEF-U-M5b-01). A release run writes the file into the working tree, and the file
stays there after the run. A later gate in the same tree must not read it. Behaviour the contract fixes:

- A commit gate, a nightly gate and a plain pytest session never read a leftover evidence file. In those runs
  `load_registry()` returns the registry as if no file existed: `passed_tests` is empty and `evidence_build_id` is None.
- A test that needs evidence builds its own file in a temporary folder and passes that folder as `root`, as UT-RES-08
  and UT-RES-09 already do. No test depends on the file of an earlier release run.
- D-045f changes no other rule of §3.1. An installed wheel reads the file it carries, and the staleness rule above still
  applies.

Which mechanism achieves this was U-M5e's choice, and D-046e records it: the test side meets D-045f, and the product
gains no test-only switch. State on main 76f054b, `verified` by reading the files named and by running the two tests
below. `load_registry` still reads `passed_tests.v1.json` whenever it exists and applies (`registry.py` l.270-291), so a
product run keeps the rule above. `tests/conftest.py` (`pytest_configure` l.42, `_load_registry_without_build_evidence`,
l.59-71) copies `resources/evidence` without `PASSED_TESTS_FILE` into a temporary folder, points `registry.resource_root`
at it for the whole session and deletes the copy in `pytest_unconfigure`. The packaging fixture `build_wheel`
(`tests/packaging/support.py` l.30-44) builds the wheel from a copy of the build inputs that leaves the file out, so
only the release profile's own wheel carries it (PK-10). Two tests pin the behaviour. They have no ID in `test_plan.md`
§5.7 yet, and this unit invents none:

- `test_d045f_evidence_a_release_run_left_in_the_tree_never_reaches_the_test_session`
  (`tests/unit/results/test_evidence.py` l.202) plants a file in `resources/evidence` that applies to this tree
  and lists no test. It checks that `load_registry(resource_root())` reads the file (`evidence_build_id` is set) while
  `load_registry()` gives `evidence_build_id` None and an empty `passed_tests`. `1 passed` (`verified` by running it).
- `test_pk03_the_session_wheel_leaves_out_evidence_a_release_run_left_in_the_tree`
  (`tests/packaging/test_pk03_reproducible_wheel.py` l.67) plants a file and checks that the wheel built by
  `build_wheel` has `embodic/_resources/evidence/equations.v1.json` and not `passed_tests.v1.json`. `1 passed`
  (`verified` by running it).

`tools/ci.py` names the file only for the release profile (`EVIDENCE`, l.27, and `evidence_gates`, l.86-93). Outside a
pytest session, `load_registry()` keeps reading the file whenever it applies, which is the product behaviour above.

### 3.2 Requirement status and the release trace gate (revision 2026-10-17, U-D17; D-051e)

Scope. This section governs the project's audit tooling. Nothing under `src/embodic` changes. D-051e (`docs/decision_log.md`
l.57) rules two points. A requirement row counts `verified` only with Agent 4's `checks` ruling for that row, tied to the
source hash of each test it cites (DEF-UV8-07). The release profile passes `tools/trace_matrix.py
--fail-untested-through` from the 0.0.2 gate on, with a manual-record input for rows only a person can check. The data
shapes below follow `docs/phase3/architecture/v3_contract_rulings.md` §4 and §2. D-051e does not spell them out, and the
parts marked as proposed wait for Fable.

What the audit does on main 0547f20 (`verified` by reading). `docs/phase3/verification/checks/req_audit.py` marks a row
`verified` when every planned test ID of the row has `gate`, `name`, `file`, `eqt` or `record` evidence and no ID needs
another machine (docstring l.21-24, `audit` l.138-160). A `name` match means that a passing test carrying the row's REQ
marker has the ID in its name. The script states that it does not read whether a test checks the acceptance (l.24).
Agent 4 read one sampled test for each of the 50 must rows that the audit called `verified` and found that 6 check the
acceptance, 32 check part of it and 12 check none of it (`tests/independent/m7/records/V3-01.md` l.68). Standing order 2
defines `verified` as read in the source or reproduced by running something, and a name match is neither.

The acceptance ruling. Agent 4 owns the ruling file, `req_audit.py` and `verification_plan.md`. The example path of
v3_contract_rulings.md §4 is `tests/independent/m7/acceptance_rulings.json`, and Agent 4 may choose another path and
record it here. The file holds one `AcceptanceRuling` per row, with these keys.

| Key | Type | Value |
|---|---|---|
| `req_id` | string | the row, for example `"REQ-F-36"` |
| `ruling` | string | `"checks"`, `"partial"` or `"does not check"`, the words of V3-01 |
| `clauses` | list | one entry per clause of the row's Acceptance cell, quoted in `text`, each with a list `evidence` |
| `clauses[].evidence[]` | object | `kind` (`"test"`, `"gate"` or `"record"`), `ref` (a pytest node ID, a gate name or a record path), `line` (integer) and `sha256` (the hash of the cited source) |
| `missing` | list | the clauses that no evidence asserts; empty for `checks` |
| `reviewer`, `base_commit` | string | the role that read the evidence (not a person's name, standing order 7) and the commit it read |

The hash covers the source text, encoded as UTF-8. For a test it is the function's source segment
(`ast.get_source_segment`). For a gate it is the `Gate(...)` entry in `tools/ci.py`. For a record it is the whole file.

The rule. A live row is `verified` only when all three hold.

1. Every planned test ID of the row has passing evidence, as today.
2. The row has an `AcceptanceRuling` with `ruling` equal to `"checks"`.
3. Every evidence entry of that ruling is current. Its hash equals the hash of the same source in the audited tree, and a
   cited test passed in the audited run.

A row that meets 1 but not 2 or 3 is `partial`. A ruling with a hash that no longer matches counts as absent, and the
audit lists it as stale. A cited test carries the REQ marker of the row. Every other status rule of `req_audit.py` stays,
including `withdrawn` for withdrawn rows. One ruling covers one row and cites every test the row needs together. The hash
covers the function body only, so a change to a fixture or a helper does not make a ruling stale, and the audit's header
states that limit (`inferred`).

TR-01 stays a floor. `tools/trace_matrix.py` answers whether a test exists, and its output never says `verified`.
`req_audit.py` answers whether the acceptance is checked.

Release trace gate (D-051e). From the 0.0.2 release gate on, the release profile of `tools/ci.py` passes
`--fail-untested-through M5` to `tools/trace_matrix.py`. D-051e names the flag. The value `M5` is the proposal of
v3_contract_rulings.md §2 point 1, because it covers every milestone, and Fable confirms it. With the flag, the script
exits 1 when a live must row of milestone M5 or earlier has no passing test and no manual record that passed
(`find_untested`, `tools/trace_matrix.py` l.88-97, flag at l.106). On main 0547f20 no profile passes the flag
(`tools/ci.py` l.74-82).

- `Profile` (`tools/ci.py` l.33-39) gains `untested_through: str | None`. The release profile sets `"M5"`, and the commit
  and nightly profiles set `None`.
- `gates_for` adds the flag when the field is set. It names the gate "trace matrix (TR-01, TR-02)" in that case and
  "trace matrix (TR-02)" otherwise (name at l.75). `req_audit.py` reads the PASS lines of the gate log as `gate`
  evidence (`gate_ids`, l.110), so a gate name that claims TR-01 without enforcing it gives false evidence.
- The commit and nightly profiles skip `tests/performance` and `tests/packaging` (`RELEASE_ONLY_TEST_DIRS`, l.28), and the
  commit profile also deselects `slow` tests (l.43). A row whose only tests sit in those folders has no passing test
  there. REQ-N-05 is such a row (v3_contract_rulings.md §2 point 2).

Manual records (proposed; Fable confirms the location and the format). `tools/trace_matrix.py` gains `--manual-records
PATH`. The file is one JSON list with one object per record.

| Key | Type | Value |
|---|---|---|
| `req` | string | the REQ ID that the record covers; a row of `requirements.md` |
| `test_id` | string | the planned test ID that the person ran, for example `"PK-06"` |
| `record` | string | the repository-relative POSIX path of the record file; the file exists |
| `embodic_version` | string | the version of the build that the person tested |
| `result` | string | `"passed"` or `"failed"` |

- TR-01 counts a record with `result` equal to `"passed"` as a test for its `req`. The Phase 1 text of TR-01 already
  allows "a manual test record" (`docs/phase1/architecture/test_plan_draft.md` l.393).
- The script exits 1 and prints the record when its `result` is neither value, its `req` is unknown or its `record`
  path does not exist. A typo then cannot hide a gap, as `record_passed_tests.py` refuses an unknown eqt ID (§3.1).
- The summary line prints the number of counted records after the test counts, as "manual: 1". Nobody then reads a
  manual record as an automated test.
- The index file is `docs/phase3/verification/manual_records.json`. Agent 4 owns it and the release profile passes its
  path. It holds `[]` until a person has recorded a check. Without this input REQ-N-07 cannot pass, because its acceptance
  needs a person on a clean Windows machine (`requirements.md`, REQ-N-07).
- The record files are Markdown. Agent 4's records stay under `tests/independent/<milestone>/records/`, where
  `req_audit.py` already reads three (`RECORDS`, l.58-62). A campaign record that Fable writes stays under
  `docs/phase3/fable/`. A record names the build (the version, and the wheel's SHA-256 when a wheel exists), each step
  with the output the person saw, and the verdict. It holds no account name (standing order 7).

`embodic_version` does not decide whether a record counts. Whether a record of an earlier build satisfies TR-01 for the
0.0.2 gate is open (§13 point 14). D-051e puts a coverage step in Phase 5, so this contract adds no coverage gate.

## 4. `embodic.winding`: spiral phase plan

Used by the spiral generator only. Exact integer arithmetic (EQ-08 `replace`).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class Feasibility:
    coils: int
    poles: int
    phases: int
    q: Fraction
    periodicity: int  # t = gcd(Q, p)
    balanced: bool
    max_parallel_paths: int  # always = periodicity; marked for removal (revision 2026-10-08 (U-D5))

    def allows_parallel_paths(self, paths: int) -> bool:
        """True when `paths` divides the periodicity t (D-032a; `inferred` until a source lands)."""


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignment:
    coil_index: int
    phasor_index: int
    phase: Phase
    polarity: Literal[1, -1]


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralWindingPlan:
    """Phase plan of one layer pair; with one phase per pair it is the template every pair repeats. No issues field
    (D-031d): warnings come from plan_issues."""

    feasibility: Feasibility
    assignment: tuple[CoilAssignment, ...]
    pattern: str  # "AabBCcaABbcC", upper = +, lower = -
    winding_factors: Mapping[int, Traceable[float]]  # harmonic order -> k_w,n; orders PLAN_HARMONICS = (1, 3, 5, 7)


def check_feasibility(coil_count: int, poles: int, phases: int = 3, *, phase_per_pair: bool = False) -> Feasibility: ...
def balanced_coil_counts(poles: int, phases: int = 3, max_coils: int = 96) -> tuple[int, ...]: ...
def assign_phases(coil_count: int, poles: int, phases: int = 3,
                  sequence: PhaseSequence = PhaseSequence.ABC) -> tuple[CoilAssignment, ...]: ...
def compute_winding_factors(assignment: Sequence[CoilAssignment], poles: int, coil_count: int,
                            spans_rad: Sequence[float], harmonics: Sequence[int],
                            registry: Registry) -> dict[int, Traceable[float]]: ...
def plan_spiral_winding(design: DesignParameters, spec: SpiralWindingSpec,
                        registry: Registry) -> SpiralWindingPlan | Unbuildable: ...
def plan_issues(plan: SpiralWindingPlan, design: DesignParameters) -> tuple[ValidationIssue, ...]:
    """Warnings a buildable plan carries: delta with k_w3 not zero, an asymmetric manual assignment (D-031d, D-051b)."""
```

Revision 2026-10-08 (U-D4, D-031d; `src/embodic/winding/plan.py` and `src/embodic/errors/catalogue/winding.py` on main
c7fff3a, `verified` by reading). `plan_spiral_winding` returns `Unbuildable` for a design it cannot plan, and
`plan_issues` returns the warnings of a plan it can build. The plan carries no `issues` field, so a plan stays a pure
value that the generator copies into `SpiralDetail.plan` and the warnings are computed where the design is at hand. The
compute facade (U-M2f) adds `plan_issues(detail.plan, design)` to the outcome's issues for every spiral board; until
then no production code calls it.

Issue codes of `embodic.winding`. The catalogue has no `WND_` prefix, so the codes use the shared prefixes, and the
prefix sets category and severity (`plan.py` `_KIND_BY_PREFIX`). Every issue cites EQ-08.

| Code | Returned by | Category, severity | Pointers | `value`, `limit` |
|---|---|---|---|---|
| `UNBUILDABLE_ASYMMETRIC_WINDING` | `plan_spiral_winding`, star of slots only (renamed 2026-10-17, U-D17, D-051b) | UNBUILDABLE, ERROR | `/winding/coil/coil_count`, `/rotor/poles` | none |
| `UNBUILDABLE_ASSIGNMENT_COVERAGE` | `plan_spiral_winding`, manual assignment that does not list coils 0 to Q - 1 once | UNBUILDABLE, ERROR | `/winding/assignment` | none |
| `UNBUILDABLE_PARALLEL_PATHS_NOT_DIVISOR` | `plan_spiral_winding`, `not feasibility.allows_parallel_paths(parallel_paths)` (revision 2026-10-08 (U-D5), D-032a, D-033d) | UNBUILDABLE, ERROR | `/winding/parallel_paths` | requested paths, `periodicity` |
| `RANGE_DELTA_TRIPLEN` | `plan_issues`, delta with k_w3 > 1e-9 | UNSUPPORTED_RANGE, WARNING | `/connection/topology` | k_w3, 0 |
| `RANGE_MANUAL_ASSIGNMENT_ASYMMETRIC` | `plan_issues`, manual assignment not symmetric (renamed 2026-10-17, U-D17, D-051b) | UNSUPPORTED_RANGE, WARNING | `/winding/assignment` | spread (max - min) / max of the fundamental phase EMF magnitudes |

A manual assignment is accepted even when it is asymmetric; only the star of slots refuses an asymmetric coil and pole
count. The plan's winding factors use the outermost-turn span 2 pi / Q (A2-TOP §2.2). The generator passes the real
turn spans to `compute_winding_factors` when it needs the turn-averaged values. Agent 2 answered the two engineering
questions of U-M2c (D-025e) in `docs/phase2/engineering/equation_specification.md` l.207-214, both `inferred` with no
textbook source yet: one phase per layer pair is self-consistent when 2p/Q is odd, and the parallel path count a must
divide t.

Revision 2026-10-17 (U-D17, D-051b; `src/embodic/errors/catalogue/winding.py` l.6 and l.16 and `src/embodic/winding/plan.py`
l.58 and l.96 on main 0547f20, `verified` by grep). The codes were `UNBUILDABLE_UNBALANCED_WINDING` and
`RANGE_MANUAL_ASSIGNMENT_UNBALANCED`. D-051b renames them to the same meaning. Category, severity, pointers and `value`
stay as the table says. The reason is the user's rule that no text claims balance from geometry (standing order 2): the
check tests a property of the winding pattern, not of a motor. Code that names the old codes changes in the same wave
(`src/embodic/ui/viewmodels/session.py` l.617, `tests/unit/winding/test_plan.py` l.86 and l.171). Agent 3 owns that
change. `Feasibility.balanced` and `balanced_coil_counts` keep their names, because D-051b does not name them (§13 point
14).

Revision 2026-10-08 (U-D5, D-032a, D-033d; `src/embodic/winding/feasibility.py` and `plan.py` on main e1536b8,
`verified` by reading). D-032a adopts the second answer: a design plans only when t mod a = 0, and the rule stays
`inferred` until a source lands. `plan_spiral_winding` asks `Feasibility.allows_parallel_paths` and puts t in the
issue's `limit`. `max_parallel_paths` is marked for removal. It always equals `periodicity`, its name describes the
replaced rule a <= t, and since D-032a no production code reads it (one assertion in
`tests/unit/winding/test_star_of_slots.py` l.128 does). The next unit that writes `src/embodic/winding/**` deletes the
field and that assertion. Fable schedules it; until then the stub names the field as main has it.

## 5. `embodic.geometry`: primitives, electrical element list, Layout

`Layout` is the one shape every generator produces and every consumer (DRC, physics, exporters, UI, board dump) reads.
No consumer imports a generator: the layer order of contract C1 (`package_layout.md` §3) puts `embodic.generators`
above `io`, `outcome`, `physics` and `drc`. The generator-specific records live in `embodic.geometry.details`, so
`Layout.detail` is typed without an upward import.

```python
from dataclasses import field


class PrimitiveRole(StrEnum):
    SIDE = "side"
    END_TURN = "end_turn"
    LEAD = "lead"
    FILLET = "fillet"
    TAPER = "taper"
    LEG = "leg"
    RING = "ring"
    STUB = "stub"
    BUS = "bus"
    LINK = "link"
    OUTLINE = "outline"


@dataclass(frozen=True, slots=True, kw_only=True)
class Line:
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    width_mm: float  # 0 for outline geometry
    role: PrimitiveRole

    def start_point(self) -> tuple[float, float]: ...
    def end_point(self) -> tuple[float, float]: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class Arc:
    cx_mm: float
    cy_mm: float
    r_mm: float
    start_rad: float
    sweep_rad: float  # signed, positive = counter-clockwise, y up
    width_mm: float
    role: PrimitiveRole

    def start_point(self) -> tuple[float, float]: ...
    def mid_point(self) -> tuple[float, float]: ...
    def end_point(self) -> tuple[float, float]: ...


Primitive: TypeAlias = Line | Arc


@dataclass(frozen=True, slots=True, kw_only=True)
class CopperPath:
    """Continuous chain on one copper layer, ordered in current direction."""

    id: int
    layer: str
    net: str
    primitives: tuple[Primitive, ...]
    phase: Phase | None  # None for neutral and interconnect copper
    element: int | None  # coil index (spiral), track or strand index (serpentine, wave)
    polarity: Literal[1, -1, 0]


class ViaRole(StrEnum):
    CENTRE = "centre"
    TRANSFER = "transfer"
    TERMINAL = "terminal"
    RING = "ring"
    STITCH = "stitch"


@dataclass(frozen=True, slots=True, kw_only=True)
class Via:
    id: int
    x_mm: float
    y_mm: float
    drill_mm: float
    pad_mm: float
    role: ViaRole
    span: ViaSpan
    layer_from: str
    layer_to: str
    net: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Pad:
    id: int
    x_mm: float
    y_mm: float
    shape: Literal["round", "square", "oblong", "rect"]
    width_mm: float
    height_mm: float
    rotation_rad: float
    drill_mm: float  # 0 = SMD
    layer: str | None  # SMD layer; None = all copper layers
    net: str
    label: str  # "U", "V", "W", "N"


@dataclass(frozen=True, slots=True, kw_only=True)
class Hole:
    x_mm: float
    y_mm: float
    diameter_mm: float
    label: str  # e.g. "M3 normal"


@dataclass(frozen=True, slots=True, kw_only=True)
class BoardOutline:
    outer: tuple[Primitive, ...]  # closed loop, width 0
    cutouts: tuple[tuple[Primitive, ...], ...]  # bore and other closed loops
    holes: tuple[Hole, ...]  # screw clearance holes (DXF "screws")


@dataclass(frozen=True, slots=True, kw_only=True)
class Member:
    """One conductive route between two group nodes, in current direction (electrical element list)."""

    path_ids: tuple[int, ...]
    via_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ParallelGroup:
    members: tuple[Member, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseCircuit:
    phase: Phase
    groups: tuple[ParallelGroup, ...]  # in series
    terminal_net: str


@dataclass(frozen=True, slots=True, kw_only=True)
class LineLead:
    """Interconnect copper from a phase end to its line pad; carries the line current (Xcoil lineStub)."""

    kind: Literal["line_lead"] = "line_lead"
    path_id: int
    phase: Phase


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseLink:
    """Interconnect copper in series with one phase branch: a star tap stub or a whole delta link (Xcoil link)."""

    kind: Literal["phase_link"] = "phase_link"
    path_id: int
    phase: Phase


@dataclass(frozen=True, slots=True, kw_only=True)
class NeutralRing:
    """Star-point ring; the copper between two consecutive taps carries one line current (Xcoil neutralRing)."""

    kind: Literal["neutral_ring"] = "neutral_ring"
    path_id: int
    tap_via_ids: tuple[int, ...]  # tap vias in ring order; the first and the last sit at the ring ends


@dataclass(frozen=True, slots=True, kw_only=True)
class NeutralLead:
    """Interconnect copper from the star point to the neutral pad; no current in a balanced star (Xcoil l.1313)."""

    kind: Literal["neutral_lead"] = "neutral_lead"
    path_id: int


InterconnectRole: TypeAlias = LineLead | PhaseLink | NeutralRing | NeutralLead


@dataclass(frozen=True, slots=True, kw_only=True)
class Circuit:
    phases: tuple[PhaseCircuit, ...]
    topology: ConnectionTopology
    interconnect_path_ids: tuple[int, ...]
    interconnect_roles: tuple[InterconnectRole, ...] = ()  # U-M2e-4 (D-031f); empty, or one role per interconnect id

    def __post_init__(self) -> None:
        """Raises ValueError when interconnect_roles is not empty and its path ids are not interconnect_path_ids, each
        exactly once."""


@dataclass(frozen=True, slots=True, kw_only=True)
class RotationalSymmetry:
    """Lets DRC check one period plus neighbours (PR-02 proves equality with the full check)."""

    order: int  # copper of `periodic_path_ids` repeats every 2*pi/order
    periodic_path_ids: tuple[int, ...]
    canonical_path_ids: tuple[int, ...]  # one period, the reference set


@dataclass(frozen=True, slots=True, kw_only=True)
class LayoutArrays:
    """Per-layer NumPy view for DRC and physics. Rows map back through path_index and prim_index."""

    lines: Mapping[str, FloatArray]  # (N, 5): x1, y1, x2, y2, width
    arcs: Mapping[str, FloatArray]  # (M, 6): cx, cy, r, start, sweep, width
    path_index: Mapping[str, NDArray[np.int64]]
    prim_index: Mapping[str, NDArray[np.int64]]
    vias: FloatArray  # (K, 4): x, y, pad, drill


# embodic.geometry.details: generator-specific records carried by Layout.detail


class TurnLimitReason(StrEnum):
    RADIAL = "radial"
    LATERAL = "lateral"
    EYE = "eye"
    USER = "user"


class TurnClosing(StrEnum):  # revision 2026-10-08 (U-D4, D-031b); spiral_generator_spec.md G5
    FULL = "full"  # N full turns; a lead arc at r_v joins the last left side to the centre via
    HALF = "half"  # N - 1 full turns and a closing half turn whose right side ends on the centre via


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnLimit:
    """Turn bounds of one spiral coil (spiral_generator_spec.md G3 and G5)."""

    radial_bound: float  # D08 eq. 3.24, information only
    loops_trapezoidal: int
    loops_triangular: int
    eye_limit: int | None
    limiting_reason: TurnLimitReason
    closing: TurnClosing  # how the built coil reaches its centre via (D-031b)


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralDetail:
    kind: Literal["spiral"] = "spiral"
    plan: SpiralWindingPlan
    turns_achieved: int
    turn_limit: TurnLimit
    track_length_per_coil_layer_mm: Mapping[str, float]  # "X", "Y"


@dataclass(frozen=True, slots=True, kw_only=True)
class SerpentineDetail:
    kind: Literal["serpentine"] = "serpentine"
    max_turns_that_fit: int  # Xcoil F-10
    layer_phase: Mapping[str, Phase]  # one phase per copper layer
    canonical_frame_rad: float


@dataclass(frozen=True, slots=True, kw_only=True)
class WaveDetail:
    kind: Literal["wave"] = "wave"
    tracks_per_layer: int
    stitch_vias_per_stack: int


TopologyDetail: TypeAlias = SpiralDetail | SerpentineDetail | WaveDetail


@dataclass(frozen=True, slots=True, kw_only=True)
class Layout:
    topology: TopologyKind
    copper_layers: tuple[str, ...]
    copper_z_mm: Mapping[str, float]
    paths: tuple[CopperPath, ...]
    vias: tuple[Via, ...]
    pads: tuple[Pad, ...]
    outline: BoardOutline
    circuit: Circuit
    symmetry: RotationalSymmetry | None
    envelope_mm: tuple[float, float]  # r_min_cu, r_max_cu
    detail: TopologyDetail | None = None  # generator-specific record; None only for hand-built test layouts
    derived: tuple[Traceable[float], ...] = ()  # feasibility-rail values; () only for hand-built test layouts
    layout_hash: str = field(init=False)  # "sha256:<hex>"; never passed in; a same-platform identity (D-051f)

    def __post_init__(self) -> None:
        """Sets layout_hash = compute_layout_hash(paths, vias, pads, outline), so no Layout carries a foreign hash."""

    def arrays(self) -> LayoutArrays: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class BoardStack:
    """The boards a design produces (D-016; revision 2026-10-05, U-D3). One Layout per board, in phase order for
    StackMode.ONE_BOARD_PER_PHASE; exactly one board for every other design."""

    boards: tuple[Layout, ...]  # never empty; board k of a per-phase stack holds only phase k
    board_thickness_mm: float  # one board, = design.stackup.board_thickness_mm()
    board_gap_mm: float  # 0.0 when len(boards) == 1
    issues: tuple[ValidationIssue, ...] = ()  # WARNING and INFO only; revision 2026-10-08 (U-D7, D-035a)
    stack_hash: str = field(init=False)  # "sha256:<hex>" over the boards' layout_hash values in order and the gap; a same-platform identity (D-051f)

    def __post_init__(self) -> None:
        """Sets stack_hash. Raises ValueError for no board, or a gap other than 0.0 on a one-board stack."""

    @property
    def stack_thickness_mm(self) -> float:
        """n * board_thickness_mm + (n - 1) * board_gap_mm (Xcoil statorThickness, engine.js l.689)."""


COINCIDENCE_MM: float = 1e-6  # embodic.geometry.paths; the one continuity tolerance (REQ-N-21, UT-GEO-01, IT-21)


def joint_gaps_mm(prims: Sequence[Primitive]) -> tuple[float, ...]: ...
def is_continuous(prims: Sequence[Primitive], tolerance_mm: float = COINCIDENCE_MM) -> bool: ...
def hypot_mm(dx: float, dy: float) -> float:
    """Xcoil's own hypot, sqrt(dx*dx + dy*dy) (engine.js l.77). Faithful ports use it, not math.hypot."""
def primitive_length_mm(p: Primitive) -> float: ...
def path_length_mm(prims: Sequence[Primitive]) -> float:
    """Xcoil primsLength: a left-to-right sum, so the last bit matches Xcoil."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Segment:
    """One chord of a discretised chain (Xcoil keys x1, y1, x2, y2, s, len, w, kind, pi)."""

    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float
    s_mm: float  # path position of the chord midpoint
    length_mm: float  # primitive length / piece count, not the chord length
    width_mm: float
    role: PrimitiveRole
    prim_index: int


def discretise_path(prims: Sequence[Primitive], max_segment_mm: float = 0.5,
                    max_angle_rad: float = 5 * math.pi / 180, max_sagitta_mm: float = 0.001) -> tuple[Segment, ...]:
    """Chords of a chain with their path positions; port of Xcoil discretize with its three limits (GR-17)."""
def discretise(p: Primitive, max_segment_mm: float, max_angle_rad: float = 5 * math.pi / 180,
               max_sagitta_mm: float = 0.001) -> FloatArray:
    """Polyline points (K, 2) of one primitive: the chord end points of discretise_path."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Transform:
    """Mirror about the line through the origin at mirror_axis_rad (when set), then rotate (Xcoil tf and thetaG)."""

    rotation_rad: float = 0.0
    mirror_axis_rad: float | None = None


def transform(prims: Sequence[Primitive], tf: Transform) -> tuple[Primitive, ...]:
    """Xcoil tfPrim on every primitive, in polar form as Xcoil computes it."""
def reverse_path(prims: Sequence[Primitive]) -> tuple[Primitive, ...]: ...
def rotate(prims: Sequence[Primitive], angle_rad: float) -> tuple[Primitive, ...]: ...
def mirror(prims: Sequence[Primitive], axis_angle_rad: float) -> tuple[Primitive, ...]: ...
def build_outline(spec: OutlineSpec, envelope_mm: tuple[float, float]) -> BoardOutline: ...
def compute_layout_hash(paths: Sequence[CopperPath], vias: Sequence[Via], pads: Sequence[Pad],
                        outline: BoardOutline) -> str:
    """SHA-256 of the sorted-key JSON of the copper and the outline, shortest round-trip floats (D-051f: a same-platform
    identity, because one ulp in one float changes the digest)."""


# embodic.geometry.distance and embodic.geometry.grid: Xcoil ptSegDist, segSegDist, makeGrid, gridQuery (l.563-596)
class Chord(Protocol):
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class ChordGrid:
    cell_mm: float
    cells: Mapping[tuple[int, int], tuple[int, ...]]  # chords binned by midpoint, in Xcoil's first-use order


def point_segment_distance_mm(px_mm: float, py_mm: float, s: Chord) -> float: ...
def segment_segment_distance_mm(a: Chord, b: Chord) -> float: ...
def make_grid(chords: Sequence[Chord], cell_mm: float) -> ChordGrid: ...
def grid_query(grid: ChordGrid, x_mm: float, y_mm: float, radius_mm: float) -> tuple[int, ...]: ...
```

Revision 2026-10-05 (U-D2, U-M1b and U-V1 reports).

- `Layout` computes `layout_hash` in `__post_init__` from its own copper (`src/embodic/geometry/layout.py`). A caller
  cannot pass a hash, so a Layout cannot carry the hash of other copper. `derived` and `detail` arrive with U-M2d, as
  planned.
- `Segment`, `discretise_path`, `Transform`, `transform`, `hypot_mm` and `path_length_mm` are U-M1b additions. Physics
  (U-M2e) integrates over `discretise_path` chords, and the serpentine and wave ports (U-M3a, U-M3b) need `Transform`
  and `hypot_mm` to reproduce Xcoil bit for bit.
- The Xcoil distance and grid ports live in `embodic.geometry.distance` and `embodic.geometry.grid`, not in `drc`.
  The DRC uses its own exact kernels (§7) and imports neither. Generators that port Xcoil code which calls
  `segSegDist` or `gridQuery` import them from `geometry`.
- Continuity tolerance. `COINCIDENCE_MM = 1e-6` mm is the only continuity tolerance: UT-GEO-01, REQ-F-01, REQ-N-21,
  the DRC node rule in §7 and Agent 4's IT-21 use it. Xcoil's own GEO-01 test uses the same bound
  (`/home/claude/serpentine/TEST_PLAN.md` l.41, `src/tests.js` l.36; `verified` by reading, 2026-10-05). The 1e-9 mm
  in Phase 1 port notes §6 and in `tests/independent/m1/continuity.py` (`CONTINUITY_TOL_MM`) is stricter than the
  requirement, so a gap between 1e-9 mm and 1e-6 mm would be reported there and accepted here. Agent 4 aligns the
  instrument to 1e-6 mm and may log the largest gap as information (request through Fable). The mirror and centre-via
  criteria of REQ-F-01 (1e-9 mm) are separate checks and stay.

Revision 2026-10-05 (U-D3, D-016): board stack. A `Layout` stays one board. A design that produces several boards
(serpentine `StackMode.ONE_BOARD_PER_PHASE`) produces a `BoardStack` with one `Layout` per board, and so does every
other design, with one board. Board k of a per-phase stack holds phase k's copper, vias and outline, and a `Circuit`
with one `PhaseCircuit` and no interconnect paths or pads (Xcoil builds none, `engine.js` l.2525-2535). Each board's
`copper_z_mm` is in the stack frame: board k adds `k * (board_thickness_mm + board_gap_mm)` to the single-board z
(l.695). Layer names are the stack-up names on every board; two boards may repeat a name, so no consumer merges
layer-keyed maps across boards. Xcoil's `B<k+1>:` prefix (l.706) is a display label for the UI and exports only.

Why one Layout per board and not a board index on paths, vias and pads. Copper on two boards never touches: Xcoil
skips every pair across boards (l.779, l.819). With a board index, every pair loop in DRC, its broad phase, the
symmetry shortcut and each exemption rule would need a board-equality test, and one missed test reports a phantom
violation or checks a via against copper it does not pierce. `ViaSpan.THROUGH` would also stop meaning "every copper
layer of the Layout". One Layout per board makes the separation structural: `run_drc`, `layout_hash`, the outline and
the board dump keep their one-board meaning and need no change. The cost sits in two places that must see the whole
stack anyway: the facade loops over boards, and physics reads every board plus `stack_thickness_mm`, as Xcoil's
analysis reads `statorThickness` (l.869-872, l.969).

How each consumer reads a stack:

| Consumer | Contract |
|---|---|
| `build_layout`, `Generator.generate` (§6) | return `BoardStack | Unbuildable` for every topology; spiral and wave return one board |
| `run_drc` (§7) | unchanged, one board per call; `compute` calls it once per board, and `ComputeOutcome.drc` holds one report per board in board order |
| `analyse` (§8) | takes the `BoardStack`; reads `paths`, `vias`, `circuit` and `copper_z_mm` of every board and uses `stack_thickness_mm` for the EQ-05 symmetry plane where Xcoil uses `statorThickness` (l.869-872) and `stack_thickness_mm / len(boards)` for the series-link via length (EQ-11, l.969); phase results are per phase as before |
| board dump (§9.2) | v1 stays one board per file; a stack of n boards writes n dumps whose `case_id` ends in `-board<k>`, k from 0 |
| exporters (§9.3) | SVG and DXF write one file per board when the stack has more than one, suffixed `_board` plus the phase letter (Xcoil `ui-main.js` l.31); the PDF report and README describe the whole stack and its thickness (Xcoil `report.js` l.292) |
| UI geometry view (§11) | shows one board of the stack at a time; how the user picks the board is Agent 1's screens.md decision (request through Fable) |

Revision 2026-10-08 (U-D7, D-035a; U-M3a report Q1; `src/embodic/geometry/layout.py` and `src/embodic/outcome.py` on
main 4aec992, `verified` by reading). Warning channel. A generator that builds a stack can still have something to tell
the user. `BoardStack.issues` carries those findings, with severity WARNING or INFO. A finding with severity ERROR stays
in `Unbuildable` and no stack is built. The first user is the serpentine port. Xcoil warns `INTERCONNECT_EXTERNAL` when
a one-board-per-phase stack or a single layer per phase cannot route the star or delta connection on the board
(`engine.js` l.2535). U-M3-fix adds the catalogue code and the serpentine port emits it. Xcoil's overlap wave raises
the same code when it has one terminal per rim (l.2190); the U-M3-fix brief does not name the wave port, so that case
is `unresolved`. The compute facade merges `BoardStack.issues` into `ComputeOutcome.issues` (§10, U-M3-fix brief).
`stack_hash` keeps its inputs, the boards' `layout_hash` values and the gap, because an issue is not copper. On main
4aec992 `BoardStack` has no `issues` field yet (`layout.py` l.120-145).
Revision 2026-10-09 (U-D8, D-036d; main 8a297a0, `verified` by reading). Closed. `BoardStack.issues` exists
(`geometry/layout.py` l.130) and refuses an ERROR (l.139-140). The wave case is no longer `unresolved`: both ports
emit their warning through it (§6, revision U-D8).

Revision 2026-10-17 (U-D17, D-051f; `src/embodic/geometry/hashing.py` l.27-33, `geometry/layout.py` l.141-143 and
`src/embodic/api.py` l.195, l.296, l.339-340 on main 0547f20, `verified` by reading). `layout_hash` and `stack_hash` are
same-platform identities. `compute_layout_hash` hashes the sorted-key JSON of the copper and the outline with shortest
round-trip floats, and `stack_hash` hashes the boards' `layout_hash` values and `board_gap_mm`. A float that differs by
one ulp gives another digest, and D-051f records that float bytes differ by an ulp across maths libraries. The same
design can therefore give two `layout_hash` values on Windows and on Linux. REQ-N-04 promises byte identity on one
platform only. The contract follows from that.

- Two equal hashes mean equal copper on one platform, one Python and one NumPy build. Two unequal hashes from two
  platforms say nothing about the copper.
- The stage caches of `compute` key on both hashes (`api.py` l.195 and l.296). A cache lives in one process, so the
  rule costs it nothing.
- The outcome JSON carries both hashes at `/boards/stack_hash` and `/boards/layout_hashes` (`api.py` l.339-340). A
  cross-platform comparison leaves those pointers out and compares `/design_hash` exactly (`test_plan.md` §5.7, PK-04).
  `design_hash` hashes the design only (§9.1), so no computed float enters it.
- The determinism claim of `Generator` below holds on one platform.

Revision 2026-10-08 (U-D4, D-031b, D-031f; `src/embodic/geometry/layout.py`, `details.py` and
`src/embodic/generators/spiral/derived.py` on main c7fff3a, `verified` by reading).

Closing of the last turn. `TurnLimit.closing` records which G5 closing the generator built. The type lives in
`embodic.geometry.details`, so `Layout.detail` stays typed without an upward import (contract C1). The spiral
generator's own `ClosingKind` (`generators/spiral/turns.py`) has the same two values; U-M2d-3 adds the field and maps
or replaces the private enum. The field is derived from the design, so the project file does not store it (§9.1).

`Layout.detail` and `Layout.derived` as implemented. Both have defaults, so a test can build a `Layout` by hand without
a generator record. Every generator sets both on every board it returns. A consumer that reads `detail` handles `None`
as "no generator record" (the UI shows no topology panel). The spiral generator fills `derived` with five values, in
this order; each is a `Traceable[float]` with no EQ-ID whose inputs are the coil pointers of `derived.py`:

| `quantity` | Unit | `kind_tag` | Value |
|---|---|---|---|
| `turns_per_coil_per_layer` | one | count | turns built |
| `turn_limit_per_coil_per_layer` | one | count | turns that fit (G3, G5) |
| `track_length_per_coil_layer_mm` | mm | derived | track length of one coil on one layer |
| `copper_r_min_mm` | mm | derived | `envelope_mm[0]` |
| `copper_r_max_mm` | mm | derived | `envelope_mm[1]` |

Interconnect classification (D-031f, built by U-M2e-4). Physics needs to know which current each interconnect path
carries to compute the line-to-line resistance and P_ic of EQ-23. Xcoil keeps that as three per-phase sums,
`lineStub`, `link` and `neutralRing` (`interconnectResistance`, `engine.js` l.1361-1372; `verified` by reading,
2026-10-08). The net names cannot carry it: a star tap stub has net `N` but belongs to one phase. So the generator,
which knows the role of each path when it builds it, records one `InterconnectRole` per interconnect path in
`Circuit.interconnect_roles`:

| Role | Xcoil term | Current (EQ-23) | Which paths (spiral, `generators/spiral/interconnect.py`) |
|---|---|---|---|
| `LineLead(phase)` | `lineStub[k]`, items with `line` (l.1364) | line current | lead from the phase start to its `U`, `V` or `W` pad |
| `PhaseLink(phase)` | `link[k]`, `tapOf` items and stubs with `tap` (l.1365-1368); delta link `D<k>` (l.1366) | star: line current; delta: phase current | star tap stub of that phase; the whole delta link of net `D<k>`, in series with phase k (Xcoil l.1366, l.1425) |
| `NeutralRing(tap_via_ids)` | `neutralRing` segments (l.1369-1370) | one line current per segment | star-point ring of net `N`; segment k joins tap k and tap k + 1 |
| `NeutralLead` | the `neutralPad` item (l.1313), counted in no sum | none in a balanced star | lead from the star point to the `N` pad |

Rules:

- The data shape is a tagged union, so a ring cannot carry a phase and a lead cannot lack one. `interconnect_path_ids`
  stays, because DRC (§7) and the hand-built layouts of tests and Agent 4's instruments read it. `Circuit.__post_init__`
  keeps the two fields consistent when the roles are given.
- Every generator that builds interconnect copper fills `interconnect_roles` (UT-GEN-01). An empty tuple with
  interconnect paths present means the layout was built by hand; `analyse` then reports `loss_interconnect_w` with
  status `unresolved` and the reason "interconnect copper not classified", and adds no interconnect resistance.
- Physics reads only the roles and the copper; it never infers a role from a net name or a primitive role.
- The serpentine and wave ports (U-M3a, U-M3b) fill the same records from Xcoil's `ic.items` and wave links (l.1687).
  The mapped Xcoil layouts of `tests/golden/m1_layout/xcoil_map.py` take them from Xcoil's items too (DEF-M2e3-01 is
  the related circuit-mapping defect, Agent 4, U-V2).

Revision 2026-10-08 (U-D5, D-033b; `docs/phase2/engineering/spiral_generator_spec.md` G6 via plan, U-E6). Via roles of
one spiral coil with k series groups (`LayerConfig.series_groups`), each placed v times per transition: k `CENTRE`
vias, k - 1 `TRANSFER` vias and 2 `TERMINAL` vias, so 2k + 1 per coil and Q·v·(2k + 1) per board. A `TERMINAL` via is
also the stitch via of an end group with more than one pair. Each `ParallelGroup` of a `PhaseCircuit` is one series
group, and its members enter at ring via g and leave at ring via g + 1. The generator on main e1536b8 places these
vias; whether the fan between them passes DRC is §6.

Revision 2026-10-09 (U-D10, D-039 c and d; `src/embodic/geometry/marks.py` and `labels.py` on main fd190c1, `verified`
by reading and by running both on the D08 example). Shared drawing data. The canvas, the SVG writer and the PDF report
draw the same coil marks and the same labels from two modules of `embodic.geometry`, so a drawing on screen and a drawing
in a file cannot differ (m4_review.md ruling a 3). Both modules are pure and import no Qt. `geometry` imports nothing
from `io` or `ui` (contract C1).

```python
# embodic.geometry.marks (U-M4f)
EYE_MARGIN: float  # 0.85: the eye disc keeps this fraction of the free radius around its centre


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilMark:
    layer: str
    phase: Phase
    number: int  # 1, 2, ... within the phase, in element order
    polarity: int  # +1, -1, or 0 for a coil without polarity
    label: str  # "A1+", "B2-" with the ASCII hyphen; the text a drawing prints is LabelAnchor.text
    cx_mm: float
    cy_mm: float
    eye_radius_mm: float  # 0.0 = label only, no eye fill


def point_primitive_distance_mm(x_mm: float, y_mm: float, p: Primitive) -> float: ...
def coil_marks(layout: Layout) -> Iterator[CoilMark]: ...
def top_layer_of_each_phase(layout: Layout) -> dict[Phase, str]: ...
def hatch_chords(cx_mm: float, cy_mm: float, r_mm: float, angle_deg: float,
                 spacing_mm: float) -> list[tuple[tuple[float, float], tuple[float, float]]]: ...
def eye_marks(layout: Layout) -> tuple[CoilMark, ...]: ...


# embodic.geometry.labels (U-M4f)
MINUS: str  # U+2212, the width of "+" unlike the hyphen
GAP_PX: float  # 2.0
SERPENTINE_QUADRANTS: int  # 4
LEADER_STEPS: int  # 8
SPOT_PITCH_MM: float  # 1.0, spacing of the copper spots a moved label may take


@dataclass(frozen=True, slots=True, kw_only=True)
class LabelAnchor:
    phase: Phase
    text: str  # spiral "A1+", "A2−"; wave "A+" per belt; serpentine "A"
    x_mm: float
    y_mm: float
    forced: bool  # the first of its phase and sign: always placed, inside the view (U-S4e ruling h)


@dataclass(frozen=True, slots=True, kw_only=True)
class Viewport:
    x_min_mm: float
    y_min_mm: float
    x_max_mm: float
    y_max_mm: float
    px_per_mm: float


@dataclass(frozen=True, slots=True, kw_only=True)
class Box:
    x_min_mm: float
    y_min_mm: float
    x_max_mm: float
    y_max_mm: float

    def grown(self, by_mm: float) -> Box: ...
    def meets(self, other: Box) -> bool: ...
    def inside(self, view: Viewport) -> bool: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class PlacedLabel:
    phase: Phase
    text: str
    x_mm: float  # the label centre
    y_mm: float
    leader: tuple[tuple[float, float], tuple[float, float]] | None  # (anchor, label centre), board mm


TextSize: TypeAlias = Callable[[str], tuple[float, float]]  # text -> (width, height) in viewport pixels


CopperSpots: TypeAlias = Mapping[Phase, Sequence[tuple[float, float]]]  # points on each phase's copper, board mm


def label_anchors(layout: Layout) -> tuple[LabelAnchor, ...]: ...
def copper_spots(layout: Layout) -> dict[Phase, tuple[tuple[float, float], ...]]: ...
def pad_boxes(layout: Layout) -> tuple[Box, ...]: ...
def place_labels(anchors: Iterable[LabelAnchor], *, view: Viewport, text_size: TextSize,
                 obstacles: Sequence[Box], ring_outer_mm: float,
                 copper: CopperSpots | None = None) -> tuple[PlacedLabel, ...]: ...
```

Coil marks (`geometry/marks.py`).

- `CoilMark` (l.23) is one coil on one layer. `coil_marks` (l.94) yields one per coil per copper layer, layer by layer,
  then by (phase, element, polarity). The D08 example gives 24 marks, which is 12 coils on 2 layers.
- The number counts the coils of one phase in element order from 1 (`_coil_number`, l.85). It restarts in each phase,
  so D08 has A1 to A4, B1 to B4 and C1 to C4.
- `CoilMark.label` is the phase letter, the number and the sign, with the ASCII hyphen for minus (l.106). The labels
  module writes the sign with `MINUS` (U+2212). No code under `src/embodic` reads `CoilMark.label` on main fd190c1
  (`verified` by grep), so the hyphen text reaches no drawing.
- Only a spiral coil has an eye disc. Its radius is `EYE_MARGIN` (l.18) times the free radius around the eye centre,
  so a fill never touches a trace edge. A wave or serpentine mark sits at the start of its first primitive and has
  radius 0.0 (label only).
- `top_layer_of_each_phase` (l.124) gives, per phase, the first copper layer in stack order that carries that phase. A
  drawing names and fills each phase on that layer. A spiral or wave board names all three phases on its top layer. A
  serpentine board with one phase per layer pair names each phase on the upper layer of its own pair.
- `eye_marks` (l.154) returns the marks with an eye disc on the top layer of their phase, which is the set a drawing
  fills (12 for D08). `hatch_chords` (l.139) returns parallel chords of a disc at an angle and a spacing, each ending
  on the circle.

Labels (`geometry/labels.py`). `label_anchors` (l.187) returns the labels of one board in priority order: the forced
labels first, then the rest in index order. A label is forced when it is the first of its phase and sign (U-S4e ruling
h, UX-AC-27). Each label sits on the top layer of its phase. Text and count follow the topology (D-039 d).

| Topology | Text | Count | `forced` | Anchor |
|---|---|---|---|---|
| spiral | `A1+`, `A2−` | one per coil on the top layer of its phase (`_spiral`, l.103) | the lowest-numbered coil of each phase and sign: six for D08, `A1+`, `B1−`, `C1+`, `A2−`, `B2+` and `C2−` | the eye centre |
| wave | `A+`, `A−` | one per belt, a run of radial sides next to each other with the same phase and polarity; a belt that crosses angle 0 is one belt (`_wave`, l.134) | the first belt of each phase and sign, in path order: six for the wave example | the middle side of the belt |
| serpentine | `A` | `SERPENTINE_QUADRANTS` (l.21) per phase (`_serpentine`, l.165) | quadrant 0 of each phase: three for the serpentine example (a serpentine label has no sign) | the outermost end turn nearest the middle of the 90 degree quadrant |

U-M4c-3 forced the first label of each phase only. The belts of a wave alternate sign, so every "−" belt could be
skipped and the fit view read "+" on every label (m4_review_2.md, finding R3). One forced label per phase and sign
fixes that. `label_anchors` gives 12 anchors for the D08 example, 48 for the wave example and 12 for the serpentine
example (`verified` by running it on the three examples of main 9776555).

- `place_labels` (l.313) takes the anchors in priority order, a `Viewport`, a `text_size` callback, the obstacles,
  `ring_outer_mm` and, new in U-M4e-1, `copper`. `copper` maps a phase to points on its copper and defaults to None
  (`CopperSpots`, l.196). It returns the `PlacedLabel` values that show, and every one lies inside the view. `pad_boxes`
  (l.221) gives one box per terminal pad, the obstacles the files pass. `copper_spots` (l.210) gives points
  `SPOT_PITCH_MM` (l.23) apart along each phase's copper on the layer it is labelled on.
- A label that is not forced is skipped when its box, grown by `GAP_PX` (l.20), meets a placed label, an obstacle or
  the viewport edge. Boxes are measured in viewport pixels, so the gap holds at every zoom.
- A forced label always places, by the first rule that fits (`_Placer.place_forced`, l.287). (1) On its anchor, when
  the box is free. (2) When the anchor lies in the view, on the first free spot of `LEADER_STEPS` (l.22) spots outside
  `ring_outer_mm` along the direction of the anchor, each one label height further out; `PlacedLabel.leader` then holds
  the line from the anchor to the label centre, and both ends lie in the view. (3) On the free `copper` spot of its
  phase in the view that is nearest the anchor. (4) On the anchor itself, when it lies in the view and no spot is free, even if its box then meets another label.
  A forced label with its anchor outside the view and no free `copper` spot in the view is not placed.
- Last, `name_unlabelled` (l.302) gives every phase that has a `copper` spot in the view but no label one label, on the
  free spot nearest the view centre, with the text of its nearest anchor. This closes the open question of the
  U-M4c-3 report: a zoomed view can no longer show a phase with copper and no label, and a leader no longer ends beyond
  the view edge. "In the view" means inside the `Viewport` shrunk by the 2 px gap on every edge (`_Placer.in_view`,
  l.266).
- Coordinates are board millimetres with y up. The caller chooses the scale and the text measure:

| Caller | Scale | Where |
|---|---|---|
| SVG writer | 1:1 on the page, 96 CSS px per 25.4 mm; Inter advance widths; no `copper` | `_board_labels`, `io/svg_writer.py` l.232 |
| PDF report | one point per viewport pixel at the page scale; Inter advance widths; no `copper` | `_labels`, `io/report.py` l.261 |
| Canvas | the zoom of the view, placed again after every zoom, pan and resize step; passes the `copper` of the boards it shows | `place_in_view`, called at `ui/views/geometry_view.py` l.310 |

- `place_in_view` (`ui/viewmodels/outcome.py` l.298) is the canvas's own step on top of `place_labels`. It sets
  `forced` again for the view: the forced label of each phase and sign is the first anchor of that group that lies in the
  view (`_group`, l.292, reads the phase and the sign from the text; a serpentine label has none). A group with no
  anchor in the view keeps its own forced label, which `place_labels` then moves onto the copper of the phase in the
  view. The canvas gets the `copper` from `BoardMarks.copper` (l.79), which `board_marks` (l.256) fills with
  `copper_spots`. A skipped label still shows in the hover tooltip of its copper. This is view-model behaviour (§11) and
  not part of `embodic.geometry`.
- Fit zoom survives a resize. `GeometryView` keeps `_fitted` (`geometry_view.py` l.159): true until the user zooms or
  pans, and `resizeEvent` (l.428) then fits again before it places the labels (U-S4e ruling h).
- Tests. `tests/unit/geometry/marks/test_labels.py` pins the text, the order of the forced labels (l.55), the 2 px gap
  and the pad and edge skips (l.101 and l.110), the leader (l.117), a forced label whose leader would leave the view
  (l.139), a forced label whose anchor is out of the view (l.150), the label for every phase in view (l.158) and
  `copper_spots` (l.169). `tests/ui/qt_shell/test_canvas_labels.py` pins no overlap at fit zoom and 3x
  (`test_ux_ac_27_labels_never_overlap_and_name_every_phase_at_fit_zoom_and_3x`, l.77), both signs of every wave phase
  at fit zoom (l.201), a label for every phase with copper in view and leaders inside the view at 4x zoom on three corners of the D08 and
  wave examples (l.211), and the fit kept through a resize (l.231).


## 6. `embodic.generators`: plug-in interface (ADR-0012)

```python
class Generator(Protocol):
    """A topology generator. Pure; never raises for user input; deterministic on one platform (same design -> same
    stack_hash; D-051f)."""

    kind: ClassVar[TopologyKind]

    def generate(self, design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable: ...


def generate_spiral(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Requires design.winding to be SpiralWindingSpec (TypeError otherwise: a dispatch bug, not user input). One board."""


def generate_serpentine(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Faithful port of Xcoil buildCanonical/buildLayout, one board or one board per phase (D-016). Golden GR-20."""


def generate_wave(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Faithful port of Xcoil buildWave/buildWaveOverlap. One board. Layout-level golden regression GR-21."""


GENERATORS: Mapping[TopologyKind, Callable[[DesignParameters, Registry], BoardStack | Unbuildable]] = {
    TopologyKind.SPIRAL: generate_spiral,
    TopologyKind.SERPENTINE: generate_serpentine,
    TopologyKind.WAVE: generate_wave,
}


def build_layout(design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
    """Dispatch on design.topology through GENERATORS. Adding a topology = one module + one table entry."""
```

Revision 2026-10-05 (U-D3, D-016): every generator returns a `BoardStack` (§5). The names `build_layout` and
`generate_*` stay, because no code calls them yet (U-M2d writes them) and the rename would touch ADR-0012 and
package_layout.md for no behavioural gain.

Revision 2026-10-08 (U-D5, D-033b, D-033e; `src/embodic/generators/spiral/generate.py` and
`src/embodic/errors/catalogue/generators.py` on main e1536b8, `verified` by reading). Unbuildable codes of
`generate_spiral` that D-032 and D-033 touch. Category UNBUILDABLE, severity ERROR for all. The catalogue holds one
text per code.

| Code | Returned when | Pointers | `value`, `limit` |
|---|---|---|---|
| `UNBUILDABLE_TURNS_EXCEED_LIMIT` | the requested turns exceed `MAX_TURNS_PER_LAYER` or the turns that fit, or the turns that fit exceed `MAX_TURNS_PER_LAYER` | `/winding/coil/turns` | `value` is the `TurnsExceedCause`: `user_cap` (the requested count is too high; `limit` is `MAX_TURNS_PER_LAYER` or the turns that fit, l.139 and l.399) or `loop_rule` (more turns fit than `MAX_TURNS_PER_LAYER`, whatever was requested; `limit` is `MAX_TURNS_PER_LAYER`, l.391 and l.396) |
| `UNBUILDABLE_UNSUPPORTED_END_STYLE` | `end_style` is `stadium` (D-032f; U-E6 left the stadium closing unspecified) | `/winding/coil/end_style` | none |
| `UNBUILDABLE_SERIES_VIA_FAN_DRC` | k > 1 series groups and the built board reports any DRC violation (D-020, D-033b) | `/winding/layers/series_groups` | none |
| `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` | among other options, layer pairs at more than one rotation | `/winding/layers/pairs` | none |

Series layer pairs. Main builds them with the v1.0 terminal fan, which fails DRC on CF-11 (DEF-M2d4-02), so every
series design returns `UNBUILDABLE_SERIES_VIA_FAN_DRC`. D-033b calls this the honest state. Its decision text names the
code `UNBUILDABLE_SERIES_FAN_DRC`; the code on main and in spec G6 is `UNBUILDABLE_SERIES_VIA_FAN_DRC`, and this
contract uses that name. Spec G6 (revision U-E6) replaces the fan: pitch c_f = max(pad, w, bw) + s, Δa = asin(c_f/r_T),
radial stubs for fan levels 1 and up, and the same refusal when 2r_T sin a_(L-1) < c_f or the board DRC reports a
violation. Agent 2 measured the construction DRC-clean on CF-11 and D08 for k = 2 and 3 (`series_fan_check.py`,
construction `inferred`). U-M2d-5 implements it, and the DRC check before return stays.

Pairs rotated against each other. Spec G6 forbids layer pairs of one winding at two rotations (`inferred`, U-E6) and
proposes `UNBUILDABLE_PAIRS_ROTATED_APART` with pointer `/winding/layers/pairs`. U-M2d-5 adds it to the catalogue.
Until then main returns `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED` with the same pointer.

Revision 2026-10-08 (U-D7, D-035; U-M3a, U-M3b and U-M3-wire reports; `src/embodic/generators/__init__.py` on main
4aec992, `verified` by reading). Both ports are merged. `GENERATORS` maps `SERPENTINE` to `generate_serpentine` and
`WAVE` to `generate_wave`, and `src/embodic/generators/stubs.py` no longer exists. The ports differ from Xcoil's layout
in these points, each recorded in the unit's report:

| Port | Difference from Xcoil | Why |
|---|---|---|
| serpentine | the star ring is cut at the middle tap, which adds one arc | the ring is a chain of primitives; the board stays DRC-clean (U-M3a) |
| serpentine | each tap stub is its own path | a path is one chain; the stub end meets the ring under §7 rule 5 |
| serpentine | the bus paths are members of the phase circuit | physics and the circuit then see every phase conductor (`inferred`; the report states no reason) |
| serpentine | the outline comes from the design inputs; an N pad exists only when `neutral_pad` is set | embodic takes the outline and the pads from `OutlineSpec` and `ConnectionSpec` (`inferred`) |
| wave | the star item is split into one ring path and one path per stub (D-035b; U-M3-fix does it) | Xcoil holds them in one path that is not a chain (l.1284-1289, l.2169), and DRC reported it overlapping itself (U-M3b Q3) |
| wave | vias carry the roles STITCH and TERMINAL; polarity is the belt sign | U-M3b lists both as deviations without a reason (`unresolved`) |
| wave | the via barrel length is the board thickness | §2.2, revision U-D7 |

Revision 2026-10-09 (U-D8, D-035a, D-036d; `src/embodic/generators/serpentine/generate.py`,
`src/embodic/generators/wave/generate.py`, `src/embodic/errors/catalogue/serpentine.py` and `wave.py` on main 8a297a0,
`verified` by reading). Warnings that a port returns in `BoardStack.issues` (§5). Each has category UNSUPPORTED_RANGE
and severity WARNING, and `compute` merges it into `ComputeOutcome.issues` (`api.py` l.287 and l.290, §10). Xcoil raises `INTERCONNECT_EXTERNAL`
for all three cases.

| Port | Code | Emitted when | Pointers | Source |
|---|---|---|---|---|
| serpentine | `RANGE_SERPENTINE_INTERCONNECT_BOARDS` | the interconnect is wanted (`draw_interconnect`, three phases, topology not `open`), none is built, and `stack_mode` is not `single` | `/connection/draw_interconnect`, `/winding/stack_mode` | `_external_interconnect`, `serpentine/generate.py` l.165-187 (Xcoil l.2535) |
| serpentine | `RANGE_SERPENTINE_INTERCONNECT_LAYER` | the same, with `stack_mode` `single` | `/connection/draw_interconnect`, `/winding/layers_per_phase` | the same function |
| wave | `RANGE_WAVE_INTERCONNECT_EXTERNAL` | the style is overlap, the interconnect is wanted, and the topology is delta | `/connection/draw_interconnect`, `/connection/topology` | `_external_interconnect`, `wave/generate.py` l.103-125 (D-036d) |

Xcoil's overlap branch `else if (wantIc)` (l.2190) follows `if (wantIc || conn === 'open')` and never runs. The wave
condition is the one its message states (`wave/generate.py` l.104-108 docstring; U-M3-fix2 report, `inferred`).

Revision 2026-10-09 (U-D10, D-030, DEF-M3b-03; `generators/base.py`, `generators/wave/generate.py`,
`generators/wave/involute.py`, `generators/serpentine/generate.py` and both catalogue modules on main fd190c1,
`verified` by reading and by running the new tests). The wave and serpentine ports refuse the inputs D-030 bounds
before they build any geometry (U-M3-fix3).

```python
def unusable_sizes(positive: Mapping[str, float], trace_pointer: str, width_mm: float, rules: DrcRules) -> list[str]:
    """Pointers of sizes no geometry can be built from (D-030), so a generator refuses before it builds anything."""
```

- Defect. On main 3d70170 the merged gate failed the wave fuzz test with `ZeroDivisionError` in `biarc` for a denormal
  width (w = 1.175494351e-38 with both end points equal). The draw depended on Hypothesis: a rerun with an empty
  database passed, and only the explicit `@example` reproduced it. The serpentine port had no fuzz test, and the new one found a
  `ZeroDivisionError` in `serpentine/frame.py` with zero poles (U-M3-fix3 report, `verified` there by reproduction).
- `unusable_sizes` (`generators/base.py` l.26) returns the pointer of every entry of `positive` that is not finite and
  above 0. It also returns `trace_pointer` when the width is not finite, not above 0, or below
  `DrcRules.min_trace_width_mm` by the D-006 test (`violates`, `drc/report.py` l.54). A width exactly at the minimum is
  accepted.
- `_out_of_range` of the wave port (`wave/generate.py` l.63) and of the serpentine port (`serpentine/generate.py`
  l.95) call it. Since U-M4c-4 (d) the spiral generator calls it too: `_out_of_range` (`spiral/generate.py` l.101)
  passes its positive sizes and `coil.trace_width_mm` at l.112. The inline copy is gone, and the behaviour and the
  codes are unchanged (revision 2026-10-09, U-D11: `tests/unit/generators/test_spiral_bounds.py` and
  `test_generator_interface.py` pass, 29 passed on main 9776555).

| Code | Port | Returned when | Pointers | Source |
|---|---|---|---|---|
| `UNBUILDABLE_WAVE_INPUT_OUT_OF_RANGE` | wave | `_out_of_range` finds a pointer: an unusable size, an outer radius not above the inner, a negative fillet, turns outside 1 to `MAX_TURNS` (200), poles outside 2 to `MAX_POLES` (200) or odd, or poles × phases × turns above `MAX_SLOTS` (2400) | the pointers found | `wave/generate.py` l.218; `catalogue/wave.py` l.27 |
| `UNBUILDABLE_WAVE_END_TURN_DEGENERATE` | wave | `biarc` raises `DegenerateBiarcError` where Xcoil divides by zero: the two end points coincide, or the tangents are equal (c at most 1e-12) and the chord is perpendicular to them (`wave/involute.py` l.18 and l.82-83) | `/winding/r_inner_mm`, `/winding/turns` | `wave/generate.py` l.228-229; `catalogue/wave.py` l.28 |
| `UNBUILDABLE_SERPENTINE_INPUT_OUT_OF_RANGE` | serpentine | `_out_of_range` finds a pointer: an unusable size, an outer radius not above the inner, a negative fillet, a start angle that is not finite, turns or strands below 1, turns × strands above `TRACES_MAX` (400), poles below 2, or layers per phase below 1 | the pointers found | `serpentine/generate.py` l.415-416; `catalogue/serpentine.py` l.22 |

- The tests. The wave fuzz test is `test_fuzzed_inputs_give_a_stack_or_unbuildable_never_an_exception`
  (`tests/unit/generators/wave/test_wave_generate.py` l.321). Its explicit `@example` for the denormal case (l.306)
  stays, so Hypothesis replays the case without a database. The serpentine fuzz test has the same name in
  `tests/unit/generators/serpentine/test_serpentine_inputs.py` (l.88), with the same explicit `@example` (l.73). Both
  are UT-GEN-01 for their port (test_plan.md §5.1).
- Open (U-M3-fix3 report). D-030 bounds the trace width only. A tiny positive clearance, pad or end width still
  reaches the degenerate end turn, and the wave port then returns `UNBUILDABLE_WAVE_END_TURN_DEGENERATE`. A DRC lower
  bound for clearance and pad would refuse earlier. Whether to add one is Agent 2's and Agent 6's call (§13 point 9).


## 7. `embodic.drc`

Rule D-006: violation when the clearance < rule - `DRC_EPSILON_MM`. The clearance is the distance that the kernels
compute from the generated geometry, and the word "measured" is not used for it (D-051a, revision 2026-10-17, U-D17).
Turns of one spiral share a net and still keep
clearance. Connectivity exempts exactly the pairs below (revision 2026-10-05, U-M1c report; implemented in
`src/embodic/drc/items.py` `exempt_pairs` and `src/embodic/drc/engine.py` `_check`). Every other pair is checked,
including same-net pairs. `run_drc` checks one board; a board stack (§5, D-016) is checked board by board, so copper
of two boards never forms a pair (Xcoil skips other-board pairs, `engine.js` l.779 and l.819).

Revision 2026-10-05 (U-D3, D-022). Rule 1 is narrowed (D-022 b, DEF-M1V-01) and rules 2 and 3 gain one net waiver
(D-022 a, DEF-M1z-01). Agent 3 implements both in the U-M1c fix round. Nothing else in this section changed.
Revision 2026-10-08 (U-D4, D-022c): rule 2 gains the tap clause and the waiver loses its terminal-via qualifier; see
the note after the rule list.
Revision 2026-10-09 (U-D8, D-036a, D-037a): rule 2 gains the same-net tap (rule 2b), and rule 5 states that the other
path's centreline includes its end points. See the note after the rule list.
Revision 2026-10-13 (U-D14, claude-sonnet-5-5, D-045g): no GR-19 pair depends on that end-point clause any more, because
both GR-19 DRC readings now cut each Xcoil `ic` object into continuous chains (D-046f keeps the physics mapping whole).
The rule text stays. See the note after the rule list.

1. Neighbours in one path. Each primitive that is not a fillet or a taper is a main primitive and starts a new main
   index (Xcoil `mi`, `engine.js` `drcObjects` l.1697). A fillet or taper belongs to the main primitive it follows and
   to the main primitive it precedes; at a path end it has only one of them. Two primitives of one path are exempt in
   exactly these cases:
   - two main primitives whose main indices differ by at most 1;
   - a fillet or taper and a main primitive it belongs to;
   - a fillet or taper and another fillet or taper that belongs to one of those two main primitives.

   A fillet is therefore not exempt from the main primitive two steps back (DEF-M1V-01). Xcoil applies the plain
   `abs(a.mi - b.mi) <= 1` test, and only to `cornerOk` objects (l.1697, l.1705). Xcoil's wider exemption of pairs
   closer than `1.6 * (wMax + s)` along the path (l.1700, l.1705) is not adopted (`tests/independent/README.md`, known
   limits).
2. A path end on a land. A via and the end group of a path whose end point lies within `pad_mm / 2` of the via
   centre. A pad and the end group of a path whose end point lies inside the pad outline, when the pad is on the
   path's layer or on all layers. The end group is the terminating main primitive with its fillets and tapers.
   Tap (D-022c): a via and every primitive of an interconnect path when the via centre lies within `pad_mm / 2` of
   that path's centreline, at an end or mid-path.
   Same-net tap, rule 2b (revision 2026-10-09 (U-D8), D-036a as D-037a rules it): a via and each primitive of a path
   of the via's net whose centreline passes within `pad_mm / 2` of the via centre. The exemption is per primitive, not
   per path: every other primitive of that path stays checked against the via. Rule 2b names vias, not pads. The tap
   clause above stays whole-path for interconnect paths (D-022c).
3. Path ends meeting at a node. The end groups of two different paths on one layer whose end points lie on one via,
   on one pad, or within `COINCIDENCE_MM` of each other.
4. A pad and a via whose centre lies inside the pad.
5. A T-junction (revision 2026-10-08 (U-D7), D-035b). The end group of a path whose end point lies within
   `COINCIDENCE_MM` of the centreline of another path of the same net is exempt from every primitive of that other
   path. The centreline includes its two end points (revision 2026-10-09 (U-D8), D-037a). An end point that lies on
   the other path's end point therefore also exempts its end group from every primitive of that path, not only from
   that path's end group under rule 3.

Revision 2026-10-08 (U-D7, D-035b; U-M3a report Q2, U-M3b report Q3). Xcoil joins copper mid-path in three places:
the serpentine strand bus (`engine.js` l.485), the serpentine star-ring taps (l.1289) and the wave star item, which
holds the ring and its stubs in one path that is not a chain (l.1284-1289, l.2169). Rules 1 to 4 do not cover a path
end that meets another path between its ends, so D-006 reported each joint as a violation. U-M3a measured 7 serpentine
cases with more than one strand that fail DRC for this reason. Rule 5 covers the bus and the taps. The wave port splits
the star item into one ring path and one path per stub, as the serpentine port already does (§6), so its stubs meet
the ring under rule 5. Rule 5 has no interconnect waiver: D-035b names same-net paths only. U-M3-fix implements it in
`src/embodic/drc/items.py`.

Revision 2026-10-08 (U-D4, D-022c; `src/embodic/drc/items.py` `exempt_pairs` and `_taps` on main c7fff3a, `verified`
by reading). The star-point ring is tapped by vias mid-path (DEF-M1c3-01, Xcoil sector layout), so the tap clause of
rule 2 exempts the via from the whole interconnect path, not only from the primitive it lies on. D-022c also replaces
the terminal-via qualifier of the D-022 a waiver for interconnect paths. Rule 1 reads as D-022c confirms: a fillet or
taper is exempt from the main primitive it follows, the one it precedes, and their fillets and tapers. The engine
implements the three cases as one test on slots, `abs(slot_a - slot_b) <= 2`, where a main primitive takes slot
2 x main index and a fillet or taper takes 2 x main index + 1 of the main before it (`items.py` l.48, `engine.py`
l.195).

Revision 2026-10-09 (U-D8, D-036a, D-037a; `src/embodic/drc/items.py` on main 8a297a0, `verified` by reading and by
the UT-DRC-04 tests named below). Rule 2b. The serpentine strand bus carries a terminal via of its own net mid-bus, so
rules 1 to 5 reported the via against the bus it sits on (U-M3-fix report). D-036a exempted the via from the whole
path. D-037a narrows that to each primitive whose centreline passes within `pad_mm / 2` of the via centre, because the
whole-path reading exempted 828 extra pairs on the D08 spiral and hid true trace-to-via clearances. `_taps`
(`items.py` l.253-269) tests each primitive of a non-interconnect path of the via's net on its own and tests an
interconnect path as a whole (D-022c). The decision text and the code agree. The strand sides that pass within 0.109 mm
of such a via stay reported (D-036a, faithful port).

Revision 2026-10-09 (U-D8, D-037a; U-V3b report; `tests/independent/README.md` on main 8a297a0, `verified` by
reading). Rule 5 reading. `_junctions` (`items.py` l.272-287) measures the distance from a path end to the centreline of
every primitive of the other same-net paths on its layer, end points included, and exempts the end group from every
primitive of each path within `COINCIDENCE_MM`. Agent 4's independent model reads rule 5 the same way. While an Xcoil
`ic` object was mapped as one path, one pair on each of the serpentine and wave GR-19 layouts depended on that reading.
The start of path 16 (wave: 193) was the end of path 15 (wave: 192) and also lay on its primitive 2, both net `N`. Only
rule 5 exempted that primitive, and `run_drc` exempted it too. Those path numbers belong to the unsplit mapping, which
the next revision replaces.

Revision 2026-10-13 (U-D14, claude-sonnet-5-5, D-037a, D-045g; U-V1c and U-M5o reports; `tests/independent/README.md`
l.91-98 and `src/embodic/drc/items.py` l.272-287 on main 6243163, and `tests/golden/m1_layout/xcoil_map.py` l.75-135 on
main 76f054b, `verified` by reading; the violation counts `verified` by running
`PYTHONPATH=src python3 tests/golden/m1_drc/time_gr19_layouts.py --runs 1`). No GR-19 pair depends on the end-point
clause of rule 5 any more.

- Both GR-19 DRC readings cut each Xcoil `ic` object at every joint wider than `COINCIDENCE_MM`. Agent 4's harness does
  it with `split_interconnect_chains` (U-V1c). The product tests do it with `split_ic_chains`
  (`tests/golden/m1_layout/xcoil_map.py`), and `layout_from_xcoil(split_ic_chains(raw))` is the GR-19 DRC reading. Every
  star path is then one primitive, so a stub that meets the end of another path falls under rule 3, not rule 5.
- `layout_from_xcoil` itself does not split (revision 2026-10-13, U-D14, D-046f). It keeps one path per Xcoil object,
  which is Xcoil's circuit member, because the physics goldens and Agent 4's DEF-M2e3-01 test pin that mapping
  (`test_gr19_physics_mapping_keeps_one_path_per_xcoil_object`, `tests/golden/m1_layout/test_gr19_layouts.py` l.55).
  The first version of the cut (U-M5o) sat inside `layout_from_xcoil`, and Fable's gate on 3e765f2 showed it breaking
  the physics goldens (D-046, sources).
- One pair per layout still needs rule 5, and it needs the T-junction clause, not the end-point reading. The neutral stub
  path 16 (wave: 193) ends on the ring path 18 (wave: 195) between the ring's ends, both net `N` (README l.92-94).
  `run_drc` exempts it too.
- Agent 4 ran a scratch copy of `_tees` (`tests/independent/m1/drc_universe.py` l.236) that skips a hit at the other
  path's end points. The split mapping gave 0 extra violations. The unsplit mapping gave exactly `path:15/prim:2` and
  `path:192/prim:2` (README l.95-98, read, not rerun).
- `run_drc` on the three GR-19 layouts of the product reading (`layout_from_xcoil(split_ic_chains(raw))`) reports sector
  0, serpentine 0 and wave 186 violations (wave: 6 `trace_trace` and 180 `trace_via`). The counts did not change with
  D-046f (`verified` by running the command above again on main 76f054b). Before the split the same layouts gave 0, 3
  and 190 (U-M5o report, read, not rerun).
- The clause stays in the contract and in `_junctions`. No UT-DRC-04 case covers the end-point reading on main 76f054b:
  cases 5a to 5d put the end point in the middle of the trunk (`tests/independent/m1/test_exemption_model.py`
  l.99-125). The two M3 wave boards that need rule 5 (README l.287) were not re-measured. U-M5f adds cases 5e and 5f for
  the end-point reading (Fable's ruling of 2026-10-13). Until that merge the reading is `not tested` by a dedicated case.

Net test. Rules 2 to 5 (rule 5 added 2026-10-08, U-D7) apply only when both objects carry the same net, with one waiver (D-022 a, as revised by
D-022c). Rules 2 and 3 also apply, whatever the net names and the via role, when one object is an interconnect path
(its id is in `Circuit.interconnect_path_ids`; nets `N`, `U`, `V`, `W`, `D...`):

- rule 2: an interconnect path's end group and any via or pad its end point lies on;
- rule 2, tap: an interconnect path and any via whose centre lies within `pad_mm / 2` of its centreline;
- rule 3: an interconnect path's end group and the end group of another path, when both end points lie on one via or
  one pad.

A lead or star-point link that ends on a phase via, or a ring that a via taps, is an intended joint, not a short. The
waiver does not reach rule 4, a via on a path that is not an interconnect, or a node of coincident end points with no
via or pad; those keep the net test. Net names do not change: phase copper and vias carry `PHASE_A`, `PHASE_B` and
`PHASE_C`, and interconnects keep their circuit net. Xcoil's single `WINDING` net is not adopted, because it would also
exempt another phase's path end that lands on a via by mistake. Rule 1 needs no net test, because a path has one net.

Tests per rule (test_plan.md §5.1 UT-DRC-04, amended 2026-10-05). Every rule has one case that must be exempt and one
near miss that must be reported. PR-01 and PR-13 check the exemption set as a whole against Agent 4's brute-force
checker, and `tests/independent/m1/test_drc_agreement.py` `test_fillet_is_not_exempt_from_the_main_primitive_two_steps_back`
is the independent check of rule 1.

| Rule | Test cases |
|---|---|
| 1, main pairs | UT-DRC-04 cases 1a (adjacent mains exempt) and 1b (mains two apart, same net, reported) |
| 1, fillets and tapers | UT-DRC-04 cases 1c (corner fillet exempt from both mains) and 1d (fillet against the main two steps back reported, the DEF-M1V-01 hairpin) |
| 2 | UT-DRC-04 cases 2a (end on its via or pad exempt) and 2b (foreign via reported) |
| 2, waiver | UT-DRC-04 case 2c (interconnect end on a terminal, centre or transfer via of another net, and on a pad of another net, exempt), near miss 2b |
| 2, tap | UT-DRC-04 case 2d (vias of any net and role tapping an interconnect ring mid-path and at its ends exempt from every primitive of the ring; the same ring as a phase path of another net reported) |
| 2b, same-net tap (revision 2026-10-09, U-D8) | the four rule 2b tests of UT-DRC-04 in test_plan.md §5.1 (via on a line and on an arc exempt; the same via on another net reported; 0.01 mm outside the band reported; a far primitive of the tapped path still checked). D-036a's "rule 2b" is not UT-DRC-04 case 2b, which is the foreign-via near miss of rule 2 |
| 3 | UT-DRC-04 cases 3a (same-net ends at one via, pad or coincident point exempt) and 3b (different-net ends at a coincident point without a land reported) |
| 3, waiver | UT-DRC-04 case 3c (interconnect end and phase path end on one via of any role, or one pad, exempt), near miss 3b |
| 4 | UT-DRC-04 cases 4a (same-net via inside a pad exempt) and 4b (other-net via inside a pad reported) |
| 5 (revision 2026-10-08, U-D7) | UT-DRC-04 cases 5a (end point on the middle of a same-net line exempt from that path), 5b (end point on the middle of a same-net arc exempt), 5c (the same T with the two paths on different nets reported) and 5d (the same-net end point 0.01 mm short of the centreline reported). The end-point reading (revision 2026-10-09, U-D8) has no UT-DRC-04 case on main 76f054b. GR-19 in `tests/independent/m1/test_gr19_drc.py` covered it only while an Xcoil `ic` object was one path. Since the split (revision 2026-10-13, U-D14; U-V1c, D-045g, D-046f) no GR-19 pair depends on it. U-M5f adds cases 5e (a same-net path's end point on the other path's end point region, exempt) and 5f (the same geometry on different nets, reported) next to 5a to 5d. Until they merge the reading is `not tested`; this contract does not claim that they pass (see the note after the rule list) |

```python
DRC_EPSILON_MM: float = 1e-6


class DrcCheckKind(StrEnum):
    TRACE_TRACE = "trace_trace"
    TRACE_VIA = "trace_via"
    VIA_VIA = "via_via"
    PAD_TRACE = "pad_trace"
    PAD_PAD = "pad_pad"
    COPPER_EDGE = "copper_edge"
    COPPER_HOLE = "copper_hole"
    MIN_WIDTH = "min_width"
    MIN_DRILL = "min_drill"
    ANNULAR_RING = "annular_ring"

    @property
    def issue_code(self) -> str:
        """Catalogue code of the kind, f"DRC_{name}" (DRC_TRACE_TRACE ...); U-M1c addition."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcViolation:
    kind: DrcCheckKind
    layer: str | None
    clearance_mm: float  # was measured_mm (D-051a)
    required_mm: float
    at_mm: tuple[float, float]
    objects: tuple[str, ...]  # "path:17/prim:4", "via:33"


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcCheckSummary:
    kind: DrcCheckKind
    least_clearance_mm: float | None  # was measured_min_mm (D-051a)
    required_mm: float
    pairs_checked: int


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcReport:
    passed: bool
    summaries: tuple[DrcCheckSummary, ...]
    violations: tuple[DrcViolation, ...]  # first 1000 in canonical order (kind, layer, objects), D-051f
    violation_count: int
    method: Literal["grid+exact", "symmetric+grid+exact"]
    epsilon_mm: float = DRC_EPSILON_MM


class CancelToken:
    """Cooperative cancellation, checked between stages and inside chunked kernels. Thread-safe flag."""

    def cancel(self) -> None: ...

    @property
    def cancelled(self) -> bool: ...


def run_drc(layout: Layout, rules: DrcRules, *, use_symmetry: bool = True,
            cancel: CancelToken | None = None) -> DrcReport | None:
    """None only when cancelled. The violations come in the canonical order (kind, layer, objects), D-051f."""


def min_distance_line_line(a: FloatArray, b: FloatArray) -> FloatArray: ...
def min_distance_line_arc(a: FloatArray, b: FloatArray) -> FloatArray: ...
def min_distance_arc_arc(a: FloatArray, b: FloatArray) -> FloatArray: ...
```

Clearance rule per check kind (decided 2026-10-05, U-D2; `REQUIRED_MM` in `src/embodic/drc/report.py`). A pair that
contains a via uses `via_clearance_mm`, and so does a pair of two pads. Trace to trace and pad to trace use
`trace_clearance_mm`.

| Kind | Pair | Rule field |
|---|---|---|
| TRACE_TRACE | trace and trace | `trace_clearance_mm` |
| PAD_TRACE | pad and trace | `trace_clearance_mm` |
| TRACE_VIA | trace and via | `via_clearance_mm` |
| VIA_VIA | via and via | `via_clearance_mm` |
| PAD_PAD | pad and pad, pad and via | `via_clearance_mm` |
| COPPER_EDGE | trace, via or pad and a board edge or cutout | `edge_clearance_mm` |
| COPPER_HOLE | trace, via or pad and a screw hole | `hole_clearance_mm` |
| MIN_WIDTH, MIN_DRILL, ANNULAR_RING | one object | `min_trace_width_mm`, `min_drill_mm`, `min_annular_ring_mm` |

The split is an `assumption`. Xcoil compares every pair with one clearance `p.clearance` (`engine.js` `runDrc`
l.756-775; `verified` by reading, 2026-10-05), and no fabrication source for separate values is cited yet. Golden runs
set both clearances to Xcoil's value, so the split cannot change a golden verdict. The comment above `REQUIRED_MM` does
not mention TRACE_VIA; the table is the authority.

Pad to pad and pad to via (ratified). The clearance is the centre distance minus the circumscribed radius of each land
(Xcoil `padRadius` and `padsClearance`, `engine.js` l.1818). The result is exact for round lands and smaller than the
true clearance for square, rectangular and oblong pads, so it never under-reports. It can report a pair whose true
clearance passes. PR-01's no-false-positive clause excludes these pairs (test_plan.md §5.2).

What `DrcCheckSummary` covers. `least_clearance_mm` is the least clearance over the pairs the narrow phase computed.
The broad phase keeps every pair that can lie closer than the largest pair rule plus `DRC_EPSILON_MM` (`verified` by
reading `candidate_pairs` in `src/embodic/drc/engine.py`; UT-DRC-08 compares it with an exhaustive check), so below that
bound the value is the true minimum of that kind. Above it, the value is an upper bound of the true minimum and the true
minimum still exceeds the bound, so no verdict depends on it. `None` means no pair of that kind came within the bound.
`pairs_checked` counts the pairs the narrow phase computed and depends on `use_symmetry`. Golden comparisons of summary
values apply only below the bound. For MIN_WIDTH, MIN_DRILL and ANNULAR_RING the summary covers every object.

Revision 2026-10-17 (U-D17, D-051a and D-051f; `src/embodic/drc/report.py` l.54-56, l.68 and l.79 and
`src/embodic/drc/engine.py` l.325, l.336, l.348, l.352 and l.356 on main 0547f20, `verified` by reading).

Names. `DrcViolation.measured_mm` is now `clearance_mm`, and `DrcCheckSummary.measured_min_mm` is now
`least_clearance_mm`. The engine computes each value from the generated geometry (`engine.py` l.336), and `measured`
stays reserved for an input with a named source (D-007). Each new key sits beside `required_mm`, so the object says
which value is which. Callers change in the same wave, and no alias property stays. The older revision notes of this
file keep the old names, because they record what the contract said on their date.

Order. `run_drc` returns `DrcReport.violations` sorted by the key (kind, layer, objects) of D-051f. Main 0547f20 sorts by
`(v.measured_mm - v.required_mm, v.kind, v.objects)` (`engine.py` l.356), the least margin first. D-051f gives the
reason for the change: on Windows the same 186 wave violations came out in another order (DEF-W-01).

- `kind` compares as the string value of the `DrcCheckKind` member, a `StrEnum`, as the key at `engine.py` l.356 does.
- `layer` is `None` for a check that holds on every layer. `None` sorts before every layer name (proposed; Fable
  confirms). Layer names compare in code-point order.
- `objects` compares as a tuple of strings in code-point order. The string `path:17/prim:4` sorts before `path:2/prim:1`.
- `violations` keeps the first 1000 entries of this order, and `violation_count` is the full count. The entries kept are
  no longer the 1000 with the least margin (§13 point 14).

## 8. `embodic.physics`

Kernels return plain floats or arrays and cite their EQ-ID in the docstring; only `analyse()` wraps values into
`Traceable`. Argument lists follow the Phase 1 registry variables; Agent 2's `docs/phase2/engineering/equation_registry.json`
is the authority for formulas. A kernel signature change after M2 starts is a contract change (Fable approves).

Revision 2026-10-08 (U-D4, D-025a, D-026c and D-031f). The block below is `src/embodic/physics/__init__.py` on main
c7fff3a as merged by U-M2e, U-M2e-2 and U-M2e-3, signature by signature (`verified` by running `inspect.signature` on
every public name, 2026-10-08), plus the U-M2e-4 changes marked in comments. Kernels that U-M2e-2 split or replaced:
`flux_linkage_harmonics` became `field_table` and `integrate_path` with the `PathField` record; `eddy_loss_w` and
`edge_leakage_fraction` read `PathField` values instead of `LayoutArrays`.

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class CircuitSolution:
    """Per-phase EMF phasors of every analysed harmonic (EQ-18 needs all of them), resistance and circulating loss."""

    phase_emf_phasor_v_s_per_rad: Mapping[Phase, NDArray[np.complex128]]  # one entry per harmonic, design order
    phase_resistance_ohm: Mapping[Phase, float]
    circulating_loss_w: Mapping[Phase, float]


@dataclass(frozen=True, slots=True, kw_only=True)
class MotorConstants:
    ke_line_v_s_per_rad: float
    kt_n_m_per_a: float  # per line ampere rms
    kv_rpm_per_v: float


@dataclass(frozen=True, slots=True, kw_only=True)
class MassBreakdown:
    copper_g: float
    laminate_g: float


@dataclass(frozen=True, slots=True, kw_only=True)
class FieldTable:
    """Peak B_z and B_t of every harmonic on FIELD_TABLE_STEPS + 1 radii of the magnet span, at one copper z."""

    r_inner_mm: float
    r_outer_mm: float
    harmonics: tuple[int, ...]
    bz_t: FloatArray  # (harmonics, steps + 1)
    bt_t: FloatArray

    def at(self, radius_mm: float) -> tuple[FloatArray, FloatArray]: ...  # Xcoil `look`


@dataclass(frozen=True, slots=True, kw_only=True)
class PathField:
    """What one copper path collects from the rotor field, per harmonic (EQ-06, EQ-12, EC-05)."""

    flux_linkage_t_mm2: NDArray[np.complex128]  # sum B_z,n r_m dr exp(-j n p theta_m), T*mm^2
    eddy_bz_sum: FloatArray  # sum L frac B_z,n^2 w^3 in T^2 mm^4
    eddy_bt_sum: FloatArray  # sum L frac B_t,n^2 w in T^2 mm^2
    edge_weight: float  # sum |B_z,1 r_m dr| inside the span (EC-05 w)
    edge_weighted: float  # sum w exp(-d / (c_e G)), without the D_e factor


class PhysicsCancelToken(Protocol):
    """Published as embodic.physics.analyse.CancelToken: anything with a `cancelled` flag, such as the DRC token (§7).
    Physics may not import drc (MT-01). Named PhysicsCancelToken here only because one stub module holds both."""

    @property
    def cancelled(self) -> bool: ...


def pole_arc_ratio_block(width_mm: float, radius_mm: FloatArray, poles: int) -> FloatArray: ...  # EQ-04
def symmetry_plane_mm(rotor: RotorSpec, board_thickness_mm: float) -> float: ...  # EQ-05 G; analyse passes the stack
def field_harmonic(n: int, radius_mm: FloatArray, z_mm: FloatArray, rotor: RotorSpec, symmetry_plane_mm: float,
                   alpha_p: FloatArray) -> tuple[FloatArray, FloatArray]: ...  # EQ-05, (Bz, Bt) peak in T
def field_table(rotor: RotorSpec, symmetry_plane_mm: float, z_from_magnet_mm: float,
                harmonics: Sequence[int]) -> FieldTable: ...  # EQ-05 on Xcoil's NR = 48 radii
def integrate_path(prims: Sequence[Primitive], table: FieldTable, pole_pairs: int, max_segment_mm: float,
                   edge_decay_mm: float) -> PathField: ...  # EQ-06, EQ-12 sums, EC-05 weights
def edge_leakage_fraction(fields: Sequence[PathField], amplitude: float) -> float: ...  # EC-05 e_edge
def solve_phase_circuit(circuit: Circuit, path_flux_linkage_t_mm2: Mapping[int, NDArray[np.complex128]],
                        path_r_ohm: Mapping[int, float], via_r_ohm: Mapping[int, float],
                        mechanical_speed_rad_per_s: float) -> CircuitSolution: ...  # EQ-07
def phase_constants(ke_phase_v_s_per_rad: float, topology: ConnectionTopology, phases: int,
                    poles: int) -> MotorConstants: ...  # EQ-09
def copper_resistivity_ohm_m(temperature_degc: float, rho20_ohm_m: float, alpha_per_k: float) -> float: ...  # EQ-10
def path_resistance_ohm(arrays: LayoutArrays, layer_thickness_mm: Mapping[str, float],
                        resistivity_ohm_m: float) -> FloatArray: ...  # EQ-10; D-025a name
def via_resistance_ohm(drill_mm: float, plating_um: float, length_mm: float, resistivity_ohm_m: float,
                       count: int) -> float: ...  # EQ-11
def eddy_loss_w(field: PathField, harmonics: Sequence[int], thickness_mm: float, electrical_speed_rad_per_s: float,
                resistivity_ohm_m: float) -> float: ...  # EQ-12, one path
def skin_depth_mm(frequency_hz: float, resistivity_ohm_m: float) -> float: ...  # EQ-13
def inductance_estimate_h(series_turns: float, winding_factor_1: float, r_outer_mm: float, r_inner_mm: float,
                          pole_pairs: int, effective_gap_mm: float) -> float: ...  # EQ-14 (estimate)
def ipc2221_current_a(cross_section_mm2: float, temperature_rise_k: float, internal: bool) -> float: ...  # EQ-15
def mass_g(layer_copper_area_mm2: Mapping[str, float], layer_thickness_mm: Mapping[str, float],
           board_area_mm2: float, board_thickness_mm: float, copper_density_g_per_cm3: float,
           laminate_density_g_per_cm3: float) -> MassBreakdown: ...  # EQ-16; D-025a and D-026c names
def temperature_rise_k(loss_w: float, board_area_mm2: float, convection_h_w_m2k: float) -> float: ...  # EQ-17
def emf_waveform_v(phasors_v: Mapping[int, complex], samples: int = 181) -> FloatArray: ...  # EQ-18, Xcoil 181 samples
def line_waveforms_v(phase_waveforms_v: Sequence[FloatArray],
                     topology: ConnectionTopology) -> tuple[FloatArray, ...]: ...  # EQ-18 line waveforms
def thd(harmonic_amplitudes: Mapping[int, float]) -> float: ...  # EQ-18; inf for a zero fundamental (D-025c)
def delta_circulating_loss_w(phase_emf_v: Sequence[NDArray[np.complex128]],
                             loop_resistance_ohm: float) -> float: ...  # EQ-19
def line_resistance_ohm(phase_r_ohm: Sequence[float], topology: ConnectionTopology,
                        line_stub_ohm: Sequence[float] = (0.0, 0.0, 0.0), link_ohm: Sequence[float] = (0.0, 0.0, 0.0),
                        neutral_ring_ohm: Sequence[float] = ()) -> float: ...  # EQ-23
def efficiency(output_w: float, loss_w: float) -> float: ...  # EQ-26; 0 without output
def loss_budget_current_a(copper_loss_w: float, phases: int, phase_resistance_ohm: float) -> float: ...  # EQ-21
def current_density_a_per_mm2(phase_current_a: float, parallel_paths: int, width_mm: float,
                              thickness_mm: float) -> float: ...  # EQ-22

# Drive helpers (EQ-20, Xcoil inverterVoltage and driveAnalysis, engine.js l.2679-2725). U-M2e-4 adds `connection`
# and `phases`; main c7fff3a has neither and fixes the envelope at three phases (drive.py PHASES = 3).
def inverter_phase_voltage_v(dc_link_v: float, modulation: Modulation,
                             connection: ConnectionTopology) -> float: ...  # open: full bridge per phase (l.2681)
def no_load_speed_rpm(ke_v_s_per_rad: float, dc_link_v: float, modulation: Modulation,
                      connection: ConnectionTopology) -> float: ...
def base_speed_rpm(speed_rpm: FloatArray, torque_n_m: FloatArray) -> float: ...
def torque_speed_envelope(resistance_ohm: float, inductance_h: float, ke_v_s_per_rad: float, dc_link_v: float,
                          modulation: Modulation, current_limit_a: float, poles: int, points: int, *, phases: int,
                          connection: ConnectionTopology) -> tuple[FloatArray, FloatArray]: ...  # EQ-20 (estimate)


def analyse(design: DesignParameters, boards: BoardStack, provenance: ProvenanceMap, registry: Registry,
            *, cancel: PhysicsCancelToken | None = None) -> AnalysisResult | None:
    """Topology-agnostic: reads paths, vias, circuit and copper_z_mm of every board and boards.stack_thickness_mm only
    (revision 2026-10-05, U-D3, D-016). None only when cancelled."""
```

What the merged names mean (D-031f, adopted as implemented):

- `layer_thickness_mm` and `layer_copper_area_mm2` replace `thickness_mm_by_layer` and `copper_area_mm2_by_layer`
  (D-025a, D-026c): the unit suffix ends the name, as MT-05 requires.
- `CircuitSolution.phase_emf_phasor_v_s_per_rad` holds every analysed harmonic, in the order of
  `design.analysis.harmonics`, because EQ-18 builds the waveform from all of them. Harmonic 1 is index 0. Revision
  2026-10-13 (U-D15): `validate_design` enforces this with the ERROR `INVALID_HARMONIC_FUNDAMENTAL` on
  `/analysis/harmonics` (§2.2, same date), so `compute` passes `analyse` neither an empty list nor one that starts with
  another order.
- `solve_phase_circuit` takes per-path flux linkage in T·mm² and the mechanical speed, so it can return the
  circulating loss in W. Path and via resistances are keyed by id.
- The cancel token in physics is a `Protocol` with one read-only `cancelled` property, because MT-01 forbids
  `embodic.physics` to import `embodic.drc`. The DRC `CancelToken` of §7 satisfies it.
- `ke_line_peak_v_s_per_rad` (§3) is the peak of the synthesised line waveform per mechanical rad/s.
- `inverter_phase_voltage_v`, `no_load_speed_rpm` and `base_speed_rpm` are U-M2e-3 additions; the envelope uses them.
- `analyse` integrates the eddy loss over every copper path, the interconnect included (D-029), and adds no
  interconnect resistance to the phase or line values today.

U-M2e-4 (D-031f). Data shape first: `Circuit.interconnect_roles` (§5) is the input; the five result fields of §3 are
the output. Steps, each from Xcoil `applyConnection` (`engine.js` l.1398-1436; `verified` by reading, 2026-10-08):

1. Resistance of every classified path at 20 °C and at the winding temperature with `path_resistance_ohm`. For a
   `NeutralRing`, the copper between tap k and tap k + 1 is one segment, as Xcoil `interconnectResistance` l.1369-1370
   computes it from the tap angles.
2. Per-phase sums `line_stub_ohm` (LineLead), `link_ohm` (PhaseLink) and `neutral_ring_ohm` (segments) passed to
   `line_resistance_ohm` for `resistance_line_ohm` (EQ-23, l.1419-1429).
3. `loss_interconnect_w` (EQ-23): star I_line² (Σ stub + Σ link + Σ ring); delta I_line² Σ stub + I_ph² Σ link; open 0
   (l.1422-1429).
4. The delta circulating loss uses the loop resistance Σ R_k + Σ link_k (l.1411), so the delta links count.
5. `loss_total_w` = P_Cu + P_eddy + P_circ + P_delta,circ + P_ic; `output_power_w` = T ω_m; `efficiency` from
   `efficiency()`; `motor_constant_n_m_per_sqrt_w` = T / sqrt(P_Cu) when P_Cu > 0 and I_ph > 0, else 0 (EQ-26,
   l.1430-1434). The unit is `Unit.N_M_PER_SQRT_W` (§1).
6. EQ-20 for every phase count: `analyse` calls `torque_speed_envelope` with `phases=design.phases` and the connection
   it analyses (open whenever `design.phases != 3`, as Xcoil l.1399). Inside, the open connection uses the phase
   resistance, Ke1 / sqrt 2, the full-bridge voltage and m phases; star and delta use the three-phase star equivalent
   (Xcoil l.2689-2694). `torque_speed` stays `None` only without `dc_link_v` or with Ke1 = 0.

Golden cases come from Xcoil's `an.pInterconnect`, `an.lossTotal`, `an.efficiency`, `an.motorConstant` and
`an.rLineLine` on star and delta layouts, and from `driveAnalysis` for a two-phase and a one-phase design.

## 9. `embodic.io`: project file v1, examples, board dump, exporters

### 9.1 Project file schema v1

File name `<name>.embodic.json`, UTF-8 JSON. Top level (values are examples, `assumption`):

```json
{
  "format": "embodic-project",
  "schema_version": 1,
  "app_version": "0.2.0",
  "saved_utc": "2026-10-04T12:00:00Z",
  "design_hash": "sha256:...",
  "origin_example": {"example_id": "spiral_12c16p_default", "example_sha256": "sha256:..."},
  "design": {
    "name": "my stator",
    "phases": 3,
    "rotor": {"poles": 16, "rotor_type": "double", "remanence_t": 1.3, "recoil_permeability": 1.05,
              "air_gap_mm": 1.0, "back_iron_thickness_mm": 3.0, "magnet_offset_deg": 0.0,
              "magnet": {"kind": "block", "width_mm": 6.0, "length_mm": 20.0, "r_center_mm": 28.0, "thickness_mm": 2.0}},
    "winding": {"kind": "spiral", "coil": {"coil_count": 12, "r_inner_mm": 18.0, "r_outer_mm": 38.0, "...": "..."},
                "layers": {"pairs": [{"index": 0, "layer_in": "L1", "layer_out": "L2", "rotation_deg": 0.0, "phases": null}],
                           "series_groups": [[0]]},
                "assignment": null, "phase_sequence": "abc", "parallel_paths": 1},
    "stackup": {"layers": [{"kind": "copper", "name": "L1", "thickness_mm": 0.0348},
                           {"kind": "dielectric", "name": "D1", "thickness_mm": 0.071, "material": "FR-4"}]},
    "vias": {"drill_mm": 0.3, "pad_mm": 0.5, "plating_um": 25.0, "vias_per_transition": 1},
    "connection": {"topology": "star", "draw_interconnect": true, "ring_width_mm": 1.0, "terminal_pad_mm": 2.4,
                   "terminal_drill_mm": 1.2, "neutral_pad": false},
    "outline": {"board": {"shape": "polygon", "sides": 12, "across_flats_mm": 93.0, "corner_radius_mm": 0.0,
                          "rotation_deg": 0.0},
                "bore": {"shape": "circle", "radius_mm": 12.5}, "screws": []},
    "operating": {"speed_rpm": 1000.0, "line_current_rms_a": 1.0, "winding_temperature_degc": 60.0,
                  "ambient_temperature_degc": 20.0, "convection_h_w_m2k": 10.0, "dc_link_v": null, "modulation": "svpwm"},
    "materials": {},
    "analysis": {"harmonics": [1, 3, 5, 7, 9, 11, 13], "max_segment_mm": 0.5, "edge_correction": "off"},
    "drc_rules": {"trace_clearance_mm": 0.2, "...": "..."}
  },
  "provenance": {
    "/rotor/remanence_t": {"provenance": "measured", "source": "magnet datasheet rev C, grade N42"},
    "/rotor/poles": {"provenance": "example", "example_id": "spiral_12c16p_default"},
    "/winding/coil/trace_width_mm": {"provenance": "user"}
  },
  "ui": {"theme": "system", "phase_render_mode": "colour", "view": {"zoom": 1.0}}
}
```

Rules:
- `provenance` lists every concrete pointer of the design. `save_project` writes `derive_provenance()` output; on load the
  stored map is checked against the derivation when the referenced example is packaged with the same SHA-256, and
  replaced by the derivation without the example otherwise (`INFO_EXAMPLE_NOT_PACKAGED`; revision 2026-10-08, U-D6,
  question 1 below). A `measured` entry without `source`, or on a design field, is
  `INVALID_PROVENANCE`. A file with no `origin_example` stores `{"provenance": "default"}` for optional fields still at
  their neutral value (§2.4 rule 3; revision 2026-10-04, D-019).
- `design_hash` = SHA-256 over the canonical JSON of `design` only (sorted keys, no whitespace, shortest round-trip float
  `repr`, UTF-8). `origin_example`, `provenance` and `ui` do not change the hash.
- Integer `schema_version`; migrations `migrate_v<n>_to_v<n+1>` run in sequence with `INFO_MIGRATED`; newer versions are
  refused (`INVALID_SCHEMA_VERSION_NEWER`). Phase 1 drafts never shipped a v1 file, so no Phase 1 migration exists.
- The published JSON Schema `src/embodic/io/schema/project.v1.schema.json` (Draft 2020-12) is validated against every
  example and fixture in tests (UT-IO-03); the runtime loader is hand-written and typed.

Revision 2026-10-08 (U-D4). Fields added to `design` since this section was first written, and what the file stores:

| Pointer in the file | Added by | Stored as | Note |
|---|---|---|---|
| `/winding/stack_mode` | D-016 (U-D3) | `"single"` or `"one_board_per_phase"` | serpentine only |
| `/winding/board_gap_mm` | D-016 (U-D3) | mm | serpentine only; no effect for `single` |
| `/outline/screws/{k}/hole_diameter_mm` | D-031a | mm | required in every pattern; the example above has no pattern |
| `/winding/coil/first_coil_angle_deg` | range only (D-031c) | degrees as typed, any finite value | the file keeps the user's value; only the generator reduces it modulo 360 degrees |

Derived values are not stored: `TurnLimit.closing` (D-031b), `Layout.derived` and every other generator output come
from the design, so the file holds no copy that could disagree with it. The spiral layer-pair list stays stored,
because the user may edit it after D-024 derives it.

Schema version rule for U-M2f. No project file has been written yet, so v1 is the `design` shape of `FIELDS` when
U-M2f merges, including the four rows above, and no migration exists for them. After that merge, any change that makes
a v1 reader read a file differently or refuse it increments `schema_version` and adds `migrate_v<n>_to_v<n+1>`: an
added, removed or renamed key, a changed unit, or a changed meaning. A migration sets a new key only to the value that
reproduces the old file's behaviour; when no such value exists, the key stays empty and the file loads as a
`LoadedDraft` (D-014: no invented input). U-M2f's JSON Schema test (UT-IO-03) pins the shape, so such a change fails
the test until the version and the migration exist.

Revision 2026-10-08 (U-D6). U-M2f's three open questions, answered from §2.4, the schema version rule above and
ADR-0010. Each `verified (run)` line below names the function that was run on main a336531 and its input.

1. Provenance when the origin is not packaged. `origin` is a packaged example, or every field is `measured` where a
   measurement names it and `user` everywhere else. Neither `ProjectFile` nor
   `LoadedDraft` gains a field for a stored map. The file keeps `origin_example` unchanged, so an app that packages
   that SHA-256 derives `example` again. `default` does not apply either, because §2.4 rule 3 needs a blank origin and
   this design has one that is not blank. The reason is that provenance is derived from values (§2.4). Rule 2 needs the
   example's values, which the app does not have, so a stored map could not follow the first edit and would disagree
   with the values. Badges never read provenance. Every unmeasured property input stays in the assumed-inputs tag, so
   only design inputs leave it, and a design input is exact for the geometry it builds (ADR-0010 decision 6). Main
   a336531 instead derives as for a blank origin: the D08 example with a changed `example_sha256` gives 56 `user` and
   30 `default` entries (`verified (run)`, `project_provenance`, 2026-10-08). §13 row DEF-U-D6-01 tracks it.
2. Unknown keys. The loader refuses what the schema refuses: a key that `project.v1.schema.json` does not allow
   gives `INVALID_PROJECT_FILE` with the key's pointer, and the file does not load. The schema refuses a top-level
   `extra_top` and a nested `design/rotor/polez` (`verified (run)`, `jsonschema` `Draft202012Validator` on
   `spiral_12c10p_d08.embodic.json`, 2026-10-08). `ui` stays free-form, and a `provenance` pointer is checked as
   today. The reasons are three. Under the schema version rule every legitimate key change raises
   `schema_version`, so an unknown key in a v1 file comes from a hand edit or a writer defect, never from a newer
   app. Ignoring it drops a value the
   user typed: a misspelt optional key loads its neutral value with no message, which D-014 forbids. And UT-IO-03
   validates files against the schema, so a loader that opens what the schema refuses makes the schema wrong about
   the files the app opens. Main a336531 loads `design/rotor/polez` and a top-level `extra_top` with no issue
   (`verified (run)`, `parse_project` on `spiral_12c10p_d08.embodic.json`, 2026-10-08). §13 row DEF-U-D6-02 tracks it.
3. PR-12 "set back to default". "Default" is the origin's value of the field: the example's value when the origin is an
   example, and `FieldSpec.neutral_value` when the origin is blank (§2.4 rules 2 and 3). Take design D0, change one
   field to another value (D1), then type the origin's value again (D2). PR-12 then requires four things.
   `design_hash(D2) == design_hash(D0) != design_hash(D1)`. The field's provenance in D2 equals its provenance in D0
   (`example` or `default`). The assumed-inputs tag of D2 equals the tag of D0, so the field rejoins the tag when its
   provenance is `example` or its kind is property; a design field back at its neutral value stays out (ADR-0010
   decision 6). Every badge of D2 equals the badge computed with every pointer `user`. Phase 1's "the hash changes"
   (DEF-21) compares D2 with D1, not with D0.

Angles (decided 2026-10-05, U-D2, U-M2a report). The file stores degrees under `_deg` names, as §0 says and as the
example above shows. The model stores radians under `_rad` names (`src/embodic/model/fields.py`). `embodic.io` converts
value and name together at the boundary: every field whose `unit` is `Unit.RAD` maps `<stem>_rad` to `<stem>_deg`, and
the file's provenance map uses the file names. The map comes from `FIELDS`, not from a hand list. U-M2f owns the
converter with `embodic.units.deg_to_rad` and `rad_to_deg`. `canonical_json` writes the file form, so `design_hash`
hashes the degrees the file stores.

The reasons for degrees are readability (`15.0`, not `0.2617993877991494`) and Xcoil, whose parameters are degrees
(`startAngleDeg`, `outlineRotationDeg`, `engine.js` l.31 and l.57). `checks/angle_round_trip.py` measured the cost on
the 72,001 values from -360 to 360 in steps of 0.01 and on 200,000 random values (`verified (run)`, CPython 3.11.15,
2026-10-05):

- Save, load, save changed no saved value in either set, so REQ-F-15's byte-identical round trip and the hash hold.
- The first save of a typed value prints a longer decimal for 8,496 of the 72,001 grid values. For example, -359.7
  typed in the UI is saved as -359.70000000000005. That is cosmetic, and the next round trip keeps it unchanged.
- `math.radians(d)` differs from Xcoil's `d * Math.PI / 180` (`engine.js` l.171, l.1507) by 1 ulp for 20,170 of the
  grid values. The units module keeps `math.radians`: the difference is far inside the 1e-6 mm path tolerance of
  GR-20 and GR-21, and Xcoil's expressions would print a longer decimal on first save twice as often (17,734 values).

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectFile:
    design: DesignParameters
    origin: ExampleRef | None
    measurements: tuple[Measurement, ...]
    ui_state: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedDraft:
    """A project file whose design is incomplete (saved mid-entry). Loads into the new-design form."""

    draft: DesignDraft
    origin: ExampleRef | None
    measurements: tuple[Measurement, ...]
    ui_state: Mapping[str, JsonValue]


def load_project(path: Path) -> tuple[ProjectFile | LoadedDraft | None, tuple[ValidationIssue, ...]]: ...
def save_project(path: Path, project: ProjectFile | LoadedDraft, *, saved_utc: str | None = None) -> str:
    """Writes atomically (temp file + os.replace). Returns the design hash ('' for a draft).

    `saved_utc` is the text of the file's `saved_utc` key. None reads the clock to the whole second (revision
    2026-10-13, U-D15)."""
def canonical_json(design: DesignParameters) -> bytes: ...
def design_hash(design: DesignParameters) -> str: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ExampleInfo:
    example_id: str
    title: str  # free English display text (D-041a), for example "Spiral, 12 coils, 16 poles"; no fixed word is required
    topology: TopologyKind
    source_note: str  # e.g. "Agent 2 default 12/16 (assumption)", "D08 thesis configuration (oracle O1)"; provenance, never shown
    display_note: str  # what the gallery shows: no other program's name and no repository path (UX-AC-03)


def list_examples() -> tuple[ExampleInfo, ...]: ...
def load_example(example_id: str) -> tuple[ExampleRef, DesignParameters]: ...
```

Revision 2026-10-09 (U-D10, ruling g 4, UX-AC-03; `src/embodic/io/examples.py` on main fd190c1, `verified` by reading).
`ExampleInfo` has a fifth field, `display_note`. The Examples gallery shows `display_note` and never `source_note`. The
`source_note` keeps the provenance in the example file (for example "D08 thesis configuration (oracle O1)"), and it may
name another program or a repository path. `display_note` may not (UX-AC-03). `list_examples` takes it from the table
`DISPLAY_NOTES` (`examples.py` l.20), which has one entry per packaged example id, and a missing id raises `KeyError`.
Titles still come from the example files (`title` is `meta["title"]`); the serpentine example title names the reference
program, and a strict xfail records it (test_plan.md §5.6). Closed on main 4fda98d (revision 2026-10-11, U-D12, see below).

Revision 2026-10-09 (U-D11, D-041a (Fable, 2026-10-09) and ruling g of `docs/phase2/design/m4_review_2.md`;
`src/embodic/io/examples.py`, `resources/examples/*.embodic.json` and
`src/embodic/io/schema/project.v1.schema.json` on main 9776555, `verified` by reading). The title of an example.

- The rule. `example.title` of a project file is free English display text. The schema does not require the word
  "Example" in it, and the loader requires no fixed word. The provenance chip `example` and the Examples gallery
  heading carry the label (D-014, UX-AC-03), so a title does not repeat it. A title may not name another program or a
  repository path (UX-AC-03). `ExampleInfo.title` is that text and `ExampleInfo.display_note` is the note the gallery
  shows beside it.
- The titles. Ruling g fixes five values and edits them in the example files, not in a `display_title` table:
  "Spiral, 12 coils, 16 poles" (`spiral_12c16p_default`), "Spiral, 12 coils, 14 poles" (`spiral_12c14p`), "Spiral, 12
  coils, 10 poles (D08)" (`spiral_12c10p_d08`), "Serpentine, 16 poles" (`serpentine_16p_example`) and "Wave, 16
  poles, involute" (`wave_16p_example`). The ruling lists the five titles without ids; the pairing with the ids is
  `inferred` from the old titles in the files. The wave title drops "2 turns" because the field reads "Slots per phase
  belt".
- State on main 4fda98d (revision 2026-10-11, U-D12, `verified` by reading the schema and the five `example` objects). U-M4e-1b
  removed the pattern: `example.title` is `{"type": "string"}` with no `pattern` (`project.v1.schema.json` l.1015), and the
  five files carry the titles above, regenerated through the example builders. The titles are the `title` of each file's
  `example` object. A title change does not change the design hash, because the hash covers the design and not the
  `example` object (U-M4e-1b asserted it with the hashes before and after: 42b7027464, 546ef05451, 709ea86cd9,
  3fa7f90783 and 294f2a10ca, for the 16-pole spiral, the 14-pole spiral, D08, the serpentine and the wave; `verified` by
  `git grep` in the example files at 1b5c581).
- Where the word was required. Only the published schema requires it. The loader knows the keys of the `example`
  object (`_EXAMPLE_KEYS`, `io/project.py` l.62) and checks no content, and `_parse` (`io/examples.py` l.52) reads
  `document["example"]` and parses the design. Removing the pattern therefore changes the schema and its tests, not the
  loader (`inferred` from a grep for "Example" in `io/project.py` and `io/examples.py`). `source_note` keeps
  provenance such as engine line numbers and is never shown (`DISPLAY_NOTES`, l.20; `list_examples`, l.64).

Revision 2026-10-11 (U-D12, D-041b (Fable, 2026-10-09); `src/embodic/io/examples.py`, `resources/examples/*.embodic.json` and
`tests/unit/embodic_io/project/test_examples.py` on main 4fda98d, `verified` by reading and by running the tests named).
The design name of an example.

- The rule. The design `/name` of each packaged example equals its display title. The window title and the export stem
  show the name, so "Xcoil" and "Example" leave it too (D-041b). `test_d_041b_each_example_design_is_named_by_its_display_title`
  (`test_examples.py` l.52) asserts `load_example(id)[1].name == title` for the five ids.
- The hashes moved. `/name` is inside the design hash, so U-M4e-2 changed all five (D-041b): `sha256:ac4fab5d…`
  (`spiral_12c16p_default`), `sha256:4a199702…` (`spiral_12c14p`), `sha256:327919a0…` (`spiral_12c10p_d08`),
  `sha256:8ec4c234…` (`serpentine_16p_example`) and `sha256:3131a619…` (`wave_16p_example`). `EXAMPLE_HASHES`
  (`test_examples.py` l.34) holds the full values, and `test_ut_io_08_the_packaged_design_hashes_are_pinned` (l.58)
  compares them with `ExampleRef.example_sha256` of `load_example`. A unit that changes an example design edits that
  table, because a saved project keeps the hash as its `origin_example`. The ten-digit values of the bullet above
  are the hashes before D-041b.
- What did not change. A name is not an engineering value: OR-01 and every golden are unaffected. The only keys that
  changed in the five files are `/name` and the hash fields (U-M4e-2 report). Provenance stays in `source_note`, which the
  gallery never shows (`display_note` does).

Revision 2026-10-13 (U-D15, claude-sonnet-5-5; D-046 and the U-M5h report; `src/embodic/io/project.py`,
`src/embodic/selftest/catalogue.py` and `tests/unit/embodic_io/project/test_project.py` on main 5e74acc, `verified` by
reading). `save_project` takes the keyword `saved_utc`. U-M5h reported that the stub above differed from the code. This
note and the stub are the contract row.

- The signature. The stub is the signature of `project.py` l.171, copied without change. The keyword is optional and
  keyword-only, so every earlier call stays valid. Without it, `_utc_now()` (l.138-139) formats the current UTC time to
  the whole second as `%Y-%m-%dT%H:%M:%SZ`. A stamp that the caller passes is written as given, without a check
  (l.181-182), and the schema only types the key as a string (`project.v1.schema.json` l.1082).
- Why the keyword exists. `saved_utc` is a key of the file, but neither `ProjectFile` nor `LoadedDraft` has a field
  for it, and `load_project` does not return it (a grep of `project.py` finds the name only at l.52, l.143, l.157 and
  l.171-182). The second save of a save, load, save round trip therefore reads the clock again. When the two reads fall
  in different seconds, the two files differ in that one key and REQ-F-15's byte-identical round trip fails. One stamp
  passed to both saves removes the second read. U-M5h reproduced the failure with a red test (its report; not re-run
  here, `inferred`).
- Who passes it. A caller that compares two saves byte for byte passes one stamp to both. `UT-IO-01` does not need to,
  because its autouse fixture replaces `_utc_now` with a fixed time (`test_project.py` l.35-37).
  `test_ut_io_01_saved_utc_reads_the_clock_unless_the_caller_passes_a_stamp` (l.80) pins both behaviours: no keyword
  gives the clock, and a passed stamp reaches the file. The self-test `ST-IO-ROUNDTRIP` runs in an installed build
  without that fixture, so `_roundtrip` passes `ROUNDTRIP_SAVED_UTC = "2026-10-08T12:00:00Z"` to both saves
  (`catalogue.py` l.43, l.191 and l.194), the time of the fixture. `checks/selftest_probe.py` copied the old save pair
  and has the same fix (U-D15).
- No product save passes it. The two product calls of `save_project` (`ui/viewmodels/outcome.py` l.157 and
  `ui/viewmodels/session.py` l.709) omit the keyword, so a user's Save writes the clock. Only the self-test above passes
  it. Two callers of `project_document`, which requires the keyword (`project.py` l.142-144), pass the export time:
  `write_bundle` (`io/bundle.py` l.44) and the JSON project export (`ui/viewmodels/export.py` l.260-264). A grep of
  `src` for `save_project(` and `saved_utc` finds no other call.

Revision 2026-10-17 (U-D20, claude-opus-5-5; D-055, DEF-UM7d-01, REQ-T-07; `src/embodic/io/project.py`,
`io/migrations.py`, `io/exporters.py`, `io/examples.py`, `results/registry.py`, `api.py` and
`io/schema/project.v1.schema.json` on main e68d5ff, `verified` by reading unless a line says otherwise). The project file
gets the engine version and the registry version, and its format version becomes 2.

- The defect. REQ-T-07 lists the project JSON among the files that carry the engine version and the registry version.
  `project_document` writes `app_version`, `saved_utc` and `design_hash` and neither of the two (`project.py` l.142-163).
  The strict xfail `test_t07_project_json_holds_the_engine_version_and_the_registry_version`
  (`tests/unit/embodic_io/exporters/test_stamp_fields.py` l.53) records it.
- Names and place. Two top-level keys, `engine_version` and `registry_version`, beside `app_version`. The names are
  those of `ExportMetadata` and `metadata_fields` (`exporters.py` l.47-48 and l.103-104), so one name finds the value
  in every export. `app_version` keeps its name. `encode_project` sorts the keys (`project.py` l.166-168), so the place in
  the text is alphabetical and does not depend on the order in `project_document`.
- Values. `engine_version` is `embodic.__version__`. There is no separate engine (D-038d), and `export_metadata` sets
  `engine_version` from `versions.embodic` (`exporters.py` l.91). `registry_version` is `Registry.version`, the text
  `v1+<12 hex>.<12 hex>` built from the manifest copy hashes of the two registry files (`registry.py` l.282). It is the
  value of `VersionInfo.registry` (`api.py` l.220) and of the evidence file's `registry_version` (§3.1).
- Signatures. `project_document` stays pure and the caller supplies the value. `save_project` loads the packaged
  registry when the caller passes none, as it reads the clock when the caller passes no `saved_utc`. The cost of that
  load per save is `not tested`.

```python
def project_document(
    project: ProjectFile | LoadedDraft, provenance: ProvenanceMap, *, saved_utc: str, registry_version: str
) -> dict[str, JsonValue]:
    """The file's JSON data; `engine_version` is embodic.__version__ (D-038d; revision 2026-10-17, U-D20)."""


def save_project(
    path: Path, project: ProjectFile | LoadedDraft, *, saved_utc: str | None = None, registry_version: str | None = None
) -> str:
    """Writes atomically and returns the design hash ('' for a draft). `registry_version` None writes
    `embodic.results.load_registry().version` (revision 2026-10-17, U-D20)."""
```

- Callers. `write_bundle` (`io/bundle.py` l.44) and the JSON project export (`ui/viewmodels/export.py` l.260) call
  `project_document` with `outcome.versions.registry` of the outcome they write. The example builders under `tests`
  that call `project_document` (`make_examples.py` l.92 and the serpentine and wave `make_example.py`) pass
  `load_registry().version`. A caller of `save_project` may omit the keyword.
- Format version. `PROJECT_SCHEMA_VERSION` becomes 2 (`io/migrations.py` l.13) and `MIGRATIONS[1]` is
  `migrate_v1_to_v2`. The schema version rule above requires it, because a key is added and a v1 reader refuses the
  file: `_unknown_keys` refuses a top-level key outside `TOP_LEVEL_KEYS` (`project.py` l.273-275), and
  `project.v1.schema.json` has `"additionalProperties": false` at the top level. With the bump, embodic 0.0.1 reports
  `INVALID_SCHEMA_VERSION_NEWER` for a new file, not `INVALID_PROJECT_FILE` at `/engine_version`.
  `VersionInfo.schema` and `/versions/schema` of the outcome JSON become 2 (`api.py` l.219). The §10 bullet "The
  project file schema stays at 1" (revision U-D17) was true for D-051 and is superseded here. The outcome JSON's own
  `format_version` stays 2, because none of its keys changes.
- Schema files. `tests/unit/embodic_io/project/make_schema.py` also writes `project.v2.schema.json`: `schema_version`
  const 2, and `engine_version` and `registry_version` typed `string` and not required, as `app_version` is.
  `project.v1.schema.json` stays unchanged for v1 files. UT-IO-03 validates each file against the schema that its
  `schema_version` names. The PK-03 member list (`tests/packaging/test_pk03_reproducible_wheel.py` l.38) gains the new
  file.
- Load rule for a file without the keys. `migrate_v1_to_v2` returns the document with `engine_version` and
  `registry_version` set to null. A v1 writer recorded neither value, and the rule above forbids an invented one. The
  loader reads neither key into `ProjectFile` or `LoadedDraft`, as it reads neither `app_version` nor `saved_utc`, so
  a v1 file loads with the same design, provenance and issues as before, plus `INFO_MIGRATED` with `value` 1 and
  `limit` 2 (`migrations.py` l.48). `_unknown_keys` checks the key set of the file's own version before `migrate` runs
  (today it runs after, `project.py` l.314-317), so a v1 file that holds either key gives `INVALID_PROJECT_FILE` with
  that key's pointer, as the v1 schema does (question 2 above).
- Packaged examples. `load_example` reads only the `design` and `example` objects (`io/examples.py` l.52-61), so it
  runs no migration and loads a v1 or a v2 file alike. The five files become v2 all the same, because their builders
  call `project_document` and three tests assert that a rerun gives the same bytes (`test_examples.py` l.112,
  `test_serpentine_example.py` l.30 and `test_wave_example.py` l.43). The unit reruns the builders. The five files
  already hold `app_version` "0.0.1" (`verified` by grep), so a version bump already forces a rerun, and after this
  change a registry sync forces one too. Their design hashes do not change (the design hash bullet below).
- Round trip. Save, load, save stays byte-identical (REQ-F-15). Both saves run in one build, so `engine_version` is the
  same constant, and `registry_version` is the same packaged value or the one value that the caller passes to both, as
  with `saved_utc`. The second save of a loaded v1 file writes a v2 file. That is the migration, not a round trip.
- Design hash. `design_hash` covers `design` only (rule above; `project.py` l.150 hashes `project.design`). The two keys
  change no design hash, no `EXAMPLE_HASHES` pin (UT-IO-08) and no stored `origin_example`.

Revision 2026-10-17 (U-D21, claude-sonnet-5-5; D-056b; `tools/sync_registry.py` on main b977621 read). The packaged
examples depend on the registry, because each holds `registry_version`, and a registry change alters that value.

- Contract. `tools/sync_registry.py` regenerates the five example project files under `resources/examples/`
  (`serpentine_16p_example`, `spiral_12c10p_d08`, `spiral_12c14p`, `spiral_12c16p_default`, `wave_16p_example`) after every
  registry change. `tools/sync_registry.py --check` reports an example that differs from what the regeneration gives, as
  it reports a registry copy or the manifest that differs. A registry change alters `registry_version` in the files. It
  alters no design hash (bullet above).
- State. Not built on main b977621. `SOURCES` lists the two registry files only (l.40-43), and `sync()` writes the two
  copies and the manifest (l.85-91) (`verified` by reading). U-M8e builds the regeneration and regenerates the five files.

### 9.2 Board dump (Agent 3 format, frozen here as v1)

Agent 4's independent checks and the golden harness read `embodic.board-dump` v1. `BOARD_DUMP_SCHEMA` in
`src/embodic/io/board_dump.py` lists every key with its meaning, so a second reader needs nothing else.

Revision 2026-10-05 (U-D3, DEF-M1V-04). This section describes the file that `src/embodic/io/board_dump.py`
`dump_layout` writes today (`verified` by reading l.33-188, 2026-10-05). The earlier text said v1 had no field changes
against `docs/phase1/software/calculation_flow_and_port_notes.md` §7.5. It has two, both in what embodic writes:

1. `layers[]` has no PCB-tool layer-name key. Phase 1 §7.5 lists `kicad_name`; MT-07 forbids the tool's name in
   shipped files (D-009), so the writer never writes the key (`_layer_record`, l.133-135; DEF-M1b-02). A layer record
   is `{index, name, z, copper_t, role, pair, phase}`.
2. `vias[].phase` is always null. Phase 1 §7.5 gives every via its phase index; embodic's `Via` has a `net` and no
   phase field, and `_via_record` writes `"phase": None` (l.97-112). A reader takes a via's phase from its net
   (`PHASE_A`, `PHASE_B`, `PHASE_C`) or from the circuit that lists it.

The rest of the file follows Phase 1 §7.5 key for key:

- Each `circuits[]` record names its phase in the key `phase`, an integer with the encoding of `primitives[].phase`
  (0 = A, 1 = B, 2 = C). Phase 1 §7.5 said "per phase" without naming the key (DEF-V1-02); naming it is not a change.
- Null until a Layout carries the value: `params`, `params_sha256` and `drc`; layer `copper_t`, `role`, `pair` and
  `phase`; object `kind`; circuit `terminals` as `{plus: null, minus: null}`. Object `touch_vias` is `[]` and via
  `label` is `""`. A reader treats null as "not provided", never as zero.
- The writer's signatures today are `dump_layout(layout, *, case_id)` and `write_board_dump(layout, path, *,
  case_id)`. U-M2f adds the keyword `design` shown in the block below, to fill `params` and `params_sha256`
  (`work_breakdown.md` §1). `drc` stays null until §13 point 4 fixes its shape for per-kind rules.
- A board stack (§5) writes one dump per board.

Number encoding, shared by board dumps and golden fixtures (revision 2026-10-04, U-M1d deviations ratified):

- Infinity and NaN are written as `{"$f": "inf"}`, `{"$f": "-inf"}` and `{"$f": "nan"}`. JSON has no literal for
  them, and Python's `json` would otherwise write the non-standard `Infinity`.
- Negative zero is written `-0.0`. A reader that sees `-0` gets the integer 0 and loses the sign, and the sign changes
  `atan2` results (`tools/golden/README.md`, case `tfpoint-negative-x-signed-zero`).
- Comparators treat `-0.0` and `0.0` as equal (test_plan.md §3). The sign is kept for functions that read it, not for
  value comparison.

Xcoil's side of GR-19. The Node dumper does not write board dumps. For each Xcoil topology it writes the raw layout
that Xcoil's builder returns (see test_plan.md §3, "Layout dumps"). The mapping from that raw layout to
`embodic.board-dump` v1 is Python code owned by U-M1b, so the mapping is tested where the reader lives.

```python
BOARD_DUMP_SCHEMA: Mapping[str, str]  # key -> meaning, for writers and second readers


def dump_layout(layout: Layout, *, case_id: str, design: DesignParameters | None = None) -> dict[str, JsonValue]:
    """Board dump as plain JSON data. `design` arrives with U-M2f; without it params and params_sha256 are null."""
def encode_board_dump(dump: Mapping[str, JsonValue]) -> str:
    """Canonical text: sorted keys, one-space indent, tagged non-finite numbers, trailing newline."""
def decode_board_dump(text: str) -> dict[str, JsonValue]:
    """Parses and decodes non-finite tags; a bare NaN or Infinity token or another format raises ValueError."""
def write_board_dump(layout: Layout, path: Path, *, case_id: str, design: DesignParameters | None = None) -> None: ...
def read_board_dump(path: Path) -> Mapping[str, JsonValue]:
    """Returns the parsed JSON with non-finite numbers decoded ({"$f": "inf"} -> math.inf)."""
```

### 9.3 Exporters (D-009 list)

```python
class ExportKind(StrEnum):
    SVG = "svg"
    DXF_COMPLETE = "dxf_complete"
    DXF_OUTLINE = "dxf_outline"  # board outline and bore only
    DXF_SCREWS = "dxf_screws"  # screw clearance holes only
    PROJECT_JSON = "project_json"
    PDF_REPORT = "pdf_report"
    README = "readme"


class PhaseRenderMode(StrEnum):
    COLOUR = "colour"  # red / blue / green plus labels and line style (D-011)
    GREYSCALE_HATCH = "greyscale_hatch"  # lightness + hatch + labels (REQ-N-23)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportMetadata:
    embodic_version: str
    engine_version: str  # the embodic version string: there is no separate engine (D-038d)
    registry_version: str
    design_hash: str
    generated_utc: str
    drc_passed: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportSummary:
    kind: ExportKind
    path: Path
    lines: int
    arcs: int
    circles: int
    vias: int
    pads: int
    holes: int
    pages: int  # PDF only, else 0


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportRefused:
    reason: Literal["drc_errors_not_confirmed", "no_layout", "no_screws"]
    issues: tuple[ValidationIssue, ...]


def write_svg(outcome: ComputeOutcome, path: Path, *, mode: PhaseRenderMode = PhaseRenderMode.COLOUR,
              allow_drc_errors: bool = False) -> ExportSummary | ExportRefused: ...
def write_dxf(outcome: ComputeOutcome, path: Path, part: Literal["complete", "outline", "screws"],
              *, allow_drc_errors: bool = False) -> ExportSummary | ExportRefused: ...
def write_report_pdf(outcome: ComputeOutcome, path: Path, *,
                     mode: PhaseRenderMode = PhaseRenderMode.GREYSCALE_HATCH) -> ExportSummary | ExportRefused:
    """Own dependency-free writer (port of Xcoil report.js, team's own code). Every value with unit and status.
    Refuses only without a layout. A failed DRC never refuses: the report documents it (D-038d)."""
def write_readme(outcome: ComputeOutcome, files: Sequence[ExportSummary], path: Path) -> ExportSummary:
    """Plain-text README.txt describing every exported file, units, frame and the estimate caveats (Xcoil ui-main.js l.37)."""
def write_bundle(outcome: ComputeOutcome, kinds: Sequence[ExportKind], path: Path, *,
                 allow_drc_errors: bool = False) -> tuple[ExportSummary, ...] | ExportRefused:
    """ZIP of the selected exports plus README.txt (stdlib zipfile). Returns the first refusal and then writes no ZIP.
    The summaries name each member by its path inside the ZIP, for example Path("motor_report.pdf")."""
```

Revision 2026-10-09 (U-D9, D-038d; `src/embodic/io` on main 3acb044, `verified` by reading and by running each case
below on the packaged examples). What the exporters do, as the code implements it:

- Engine version. `ExportMetadata.engine_version` is the embodic version string (`export_metadata`, `io/exporters.py`
  l.82-92: `engine_version=versions.embodic`). There is no separate engine. The Python and NumPy versions stay in
  `VersionInfo` (`outcome.py` l.25-32) and are not part of the stamp. The D08 example gives `0.0.1` for both fields.
  `test_dxf.py` l.118 and `test_svg.py` l.77 pin the equality.
- PDF report and DRC. `write_report_pdf` never refuses for a failed DRC. It asks `exportable_boards` with
  `allow_drc_errors=True` (`io/report.py` l.304), prints the DRC result in the report (`_drc`, l.127) and stamps
  `drc_passed` in the metadata. Its only refusal is `no_layout`. The wave example, with 186 violations, writes a four-page
  PDF without confirmation.
- Bundle and DRC. `write_bundle` still applies the DRC gate to the whole bundle (`io/bundle.py` l.76-78). A bundle of the
  PDF report alone, for the wave example without `allow_drc_errors`, returns `drc_errors_not_confirmed`.
- Bundle and `no_screws`. `write_dxf(part="screws")` returns `no_screws()` when the boards have no screw holes
  (`io/dxf_writer.py` l.171). `write_bundle` returns that refusal from the first selected writer that refuses
  (`io/bundle.py` l.86) and writes no ZIP. Asking for `ExportKind.DXF_SCREWS` on the D08 example gives
  `ExportRefused(reason="no_screws")` and no file. `test_ut_exp_05_bundle_refuses_screws_on_a_board_without_holes`
  (`test_report_readme_bundle.py` l.202) pins it.
- Bundle member paths. The returned summaries name each member by its path inside the ZIP (`io/bundle.py` l.92). A
  bundle named `m.zip` of SVG and PDF returns `m.svg`, `m_report.pdf` and `README.txt`, and the archive holds the same
  names. The temporary folder in which the writers worked never appears. `test_ut_exp_05_bundle_holds_selected_files_and_readme`
  (`test_report_readme_bundle.py` l.188) pins it.
- `PhaseRenderMode`. The enum is defined in `embodic.io.exporters` (l.35) and that import is canonical. The view-model
  module `embodic.ui.viewmodels.appearance` re-exports the same object (l.5), and `geometry_view.py` l.46 imports it
  from there. §11 uses it through `AppearanceViewModel`. The four import contracts hold with this import (`lint-imports`
  reports 4 kept on main 3acb044). `test_phase_render_mode.py` l.25 shows that the view-model hands the writers their
  own enum member.

Revision 2026-10-09 (U-D10, D-039 b and c; `src/embodic/io/pdf_writer.py`, `svg_writer.py` and `report.py` on main
fd190c1, `verified` by reading and by running the writers on the D08 example). The PDF report embeds the bundled fonts,
and both drawing writers draw labels, eye fills and a legend from the shared data of §5.

```python
# embodic.io.pdf_writer (U-M4f)
@dataclass(frozen=True, slots=True, kw_only=True)
class TrueTypeFont:
    postscript_name: str
    data: bytes  # the whole font file, embedded as FontFile2
    units_per_em: int
    advances: tuple[int, ...]  # advance width of each glyph id, font units
    glyph_of: Mapping[int, int]  # code point -> glyph id
    bbox: tuple[int, int, int, int]
    ascent: int
    descent: int
    cap_height: int

    def width_pt(self, text: str, size: float) -> float: ...
    def missing(self, text: str) -> str:
        """The characters of text the font has no glyph for, each once, in order."""


def parse_truetype(data: bytes) -> TrueTypeFont: ...
def bundled_font(relative: str) -> TrueTypeFont:
    """A file of resources/fonts, parsed once per process."""


class MissingGlyphError(Exception):
    issue: ValidationIssue  # INVALID_EXPORT_GLYPH_MISSING, ERROR; value = "U+0E01 ..."; hint = font name and text

    def __init__(self, font: TrueTypeFont, missing: str, text: str) -> None: ...
```

- Embedding (D-039 b). Each font is a `Type0` font with the `Identity-H` encoding and a `CIDFontType2` descendant. Its
  `FontFile2` is the whole TrueType file, with no subsetting (`_embed`, `pdf_writer.py` l.223). Widths come from `hmtx`,
  glyph ids from the font's own `cmap`, and a `ToUnicode` CMap lets a reader extract the text. `PdfDocument.glyphs`
  (l.271) writes each text as a hex string of glyph ids. Revision 2026-10-09 (U-D11, U-S4e ruling e2): the document
  holds three files, `SANS_FILE` (`Inter/Inter-Regular.ttf`, font name `F1`), `SEMIBOLD_FILE`
  (`Inter/Inter-SemiBold.ttf`, `F3`) and `MONO_FILE` (`JetBrainsMono/JetBrainsMono-Regular.ttf`, `F2`), l.22-25. They
  are read through `embodic.paths.resource_root` and registered in `PdfDocument.fonts` (l.254). The variable Inter
  file is gone from `resources/fonts` (`verified` by listing the folder).
- The parser. `parse_truetype` (l.120) reads `head`, `hhea`, `maxp`, `hmtx`, `cmap` (formats 4 and 12, format 12
  first), `OS/2` and `name` with `struct`. The module imports the standard library and `embodic` only: `python -X
  importtime -c "import embodic.io.pdf_writer"` loads no third-party module and not numpy. fontTools (MIT, test side
  only) is the oracle of `test_reader_maps_every_code_point_and_width_as_fonttools_does`
  (`tests/unit/embodic_io/exporters/test_pdf_fonts.py` l.19).
- Bold is a real face. Revision 2026-10-09 (U-D11, ruling e2): `PdfDocument.text` and the table rows set `bold` text in
  Inter SemiBold (`PdfDocument.text` l.286, which picks `SEMIBOLD` for `bold`). The stroke trick of the earlier text
  (`BOLD_STROKE`, text render mode 2) is deleted. Run on main 9776555, the D08 report lists three font resources,
  `Inter-Regular`, `JetBrainsMono-Regular` and `Inter-SemiBold`
  (`test_ruling_e2_report_headings_use_the_semibold_file_and_no_faux_bold`,
  `test_report_readme_bundle.py` l.95).
- A missing glyph stops the export. `TrueTypeFont.missing` (l.51) lists the characters the font lacks, and `glyphs`
  raises `MissingGlyphError` (l.148, raised l.275) before it writes anything for that text. The error carries a
  `ValidationIssue` with code `INVALID_EXPORT_GLYPH_MISSING` (`catalogue/exporters.py` l.11). A character is never
  dropped or replaced (D-039 b, ruling g 7). `test_ut_exp_03_a_character_without_a_glyph_fails_instead_of_vanishing`
  (`test_report_readme_bundle.py` l.145) feeds U+0E01 and reads the code and the value `U+0E01`.
- The error is an exception, not a returned refusal. No code catches it (`verified` by grep: only `pdf_writer.py`
  names it), so `write_report_pdf` raises it where its signature promises `ExportSummary | ExportRefused`. The report's
  own texts hold characters the bundled fonts cover, which the D08 run confirms. Whether the writer should return an
  `ExportRefused` with a new reason is open (§13 point 9).

Drawing rules (D-039 c, REQ-N-14, REQ-N-23, UX-AC-05). A greyscale or print export names every phase without its
colour. The SVG writer and the PDF report apply the same rules in both render modes:

- Labels. Every label that `place_labels` places at the page scale is drawn over a paper-coloured halo. The SVG holds a
  `<text class="coil-label-halo">` with a `#ffffff` stroke of `LABEL_HALO_MM` (0.5) under each
  `<text class="coil-label">` of `LABEL_MM` (2.2) (`_labels`, `svg_writer.py` l.243). The halo is a separate text
  because QSvgRenderer ignores `paint-order` (U-M4f report). A leader is a line of `LEADER_MM` (0.15). The PDF draws the
  halo and the label with `PdfDocument.haloed_text` (l.317), `LABEL_PT` 6.5 and `LABEL_HALO_PT` 1.6 (`report.py` l.50-51).
- Eye fills. Phase A gets a tint of 10 percent (`EYE_TINT`). Phase B gets a hatch at 45 degrees and phase C at 135
  degrees (`PhaseInk.hatch_deg`, `exporters.py` l.176), with 0.4 mm between lines at 1:1 (`HATCH_PITCH_MM`). The fill
  is clipped to the eye disc, by `clipPath` in the SVG (`_eye`, l.201) and by a `W n` clip in the PDF (`_eye`, `report.py`
  l.210 and l.218). Only the top layer of each phase is filled (`eye_marks`, §5).
- Copper is solid. No element of a drawing has a dash pattern, copper and legend bars included
  (`test_drawings_never_dash_copper_or_legend_bars`, `test_svg.py` l.152;
  `test_report_drawing_labels_every_coil_and_never_dashes`, `test_report_readme_bundle.py` l.127).
- Legend. Each phase has a solid copper bar in its ink, an eye swatch with the same tint or hatch, and the text "Phase
  A" (`_legend`, `svg_writer.py` l.271; `report.py` l.287).
- Footer. The SVG width is the larger of the drawing and the footer text, so the stamp is never clipped
  (`svg_document`, l.305; `test_footer_fits_inside_the_drawing`, `test_svg.py` l.161).
- Colophon (revision 2026-10-09, U-D11; U-S4e ruling f, design_spec.md §4; moved by U-M4e-2, revision 2026-10-11,
  U-D12). `write_report_pdf` ends the PDF with one line, `COLOPHON` (`report.py` l.56): "Set in Inter and JetBrains
  Mono, SIL Open Font License 1.1." The writer draws the Inputs table, then every board drawing, and then the line with
  `doc.row(MARGIN, [(MARGIN, COLOPHON)])` (l.318). It is the last line of the last page, after the drawing pages. There is
  no per-page footer. U-M4e-1 had put it after the Inputs table and before the drawings, following design_spec.md §4
  ("after the last table"). Ruling f says the line "ends the PDF", and U-M4e-2 moved it (commit 92754c0).
  `test_ruling_f_one_colophon_line_ends_the_whole_report_and_no_page_has_a_footer` (`test_report_readme_bundle.py` l.113)
  pins it: the line occurs once, "Board 1 drawing" occurs before it, and it is the last line of the last page.
  The question of U-D11 whether it should move behind the drawing pages is closed. design_spec.md §4 still says "after
  the last table", and `docs/phase2/design` is Agent 1's file (`unresolved` whether Agent 1 amends it).
- Number and unit (U-S4e ruling e1). Every value the report prints joins its number and unit with `UNIT_SPACE` (§3),
  so pypdf extracts U+00A0 between them.
- Run on main fd190c1 and rerun on main 9776555 (U-D11, same counts): the greyscale D08 SVG holds 12 `coil-label` texts, 12 `coil-label-halo` texts, 12 clipped `eye`
  groups (plus 3 `legend-eye` swatches) and no `stroke-dasharray`. The D08 report extracts as text with `A2−`, `502\u00a0mΩ`, `434\u00a0mΩ` and `1.34\u00a0µH`, where `\u00a0` is the
  U+00A0 of `UNIT_SPACE` (§3), and the colophon line sits on page 3 of the four pages (`verified` by running
  `write_report_pdf` on the D08 example on main 9776555 and extracting each page with pypdf). On main 4fda98d the same run
  gives four pages and the colophon as the last line of page 4 (`verified` by running it, 2026-10-11).
- No test asserts the halo: a search of `tests` for "halo" finds nothing. Fable rasterised the greyscale D08 SVG and saw
  the labels with their halos, the eye swatches and an intact footer (U-M4f report, Fable's notes). The halo is
  `verified` by reading and by that look, `not tested` by code.

## 10. `embodic.outcome` and `embodic.api`: the compute facade

`VersionInfo`, `ComputeOptions` and `ComputeOutcome` live in `embodic.outcome` so that `embodic.io` can take an outcome
without importing `embodic.api` (layer rule, `package_layout.md` §3); `embodic.api` re-exports them.

```python
# embodic.outcome


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionInfo:
    embodic: str
    schema: int
    registry: str
    python: str
    numpy: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeOptions:
    run_drc: bool = True
    use_symmetry: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class ComputeOutcome:
    design: DesignParameters
    design_hash: str
    provenance: ProvenanceMap
    issues: tuple[ValidationIssue, ...]
    boards: BoardStack | None  # revision 2026-10-05 (U-D3, D-016): was `layout: Layout | None`
    drc: tuple[DrcReport, ...] | None  # one report per board, in board order
    analysis: AnalysisResult | None
    timings_s: Mapping[str, float]
    versions: VersionInfo

    @property
    def ok(self) -> bool:
        """No ERROR issue and the DRC of every board passed."""


# embodic.api


class StageCache:
    """Per-stage LRU (8 entries per stage). Keys: SHA-256 of the stage inputs (Phase 1 §8.1 table, with 'winding' merged
    into 'geometry'). One instance per worker thread; never shared between threads (no lock needed)."""

    def get(self, stage: Literal["geometry", "drc", "physics"], key: str) -> object | None: ...
    def put(self, stage: Literal["geometry", "drc", "physics"], key: str, value: object) -> None: ...


def compute(design: DesignParameters, provenance: ProvenanceMap, *, options: ComputeOptions = ComputeOptions(),
            cache: StageCache | None = None, cancel: CancelToken | None = None,
            registry: Registry | None = None) -> ComputeOutcome | None:
    """validate -> build_layout -> run_drc per board -> analyse. Physics runs even with DRC violations. None only when
    cancelled."""


def compute_project(path: Path) -> ComputeOutcome | tuple[ValidationIssue, ...]:
    """Load + compute. Returns the issues when the file is missing, unreadable or holds an incomplete draft."""


def outcome_to_json(outcome: ComputeOutcome) -> dict[str, JsonValue]:
    """Results JSON of embodic-cli compute --json; non-finite numbers encoded as {"$f": "inf"}. The top level holds
    "format": "embodic.outcome" and "format_version": 2 (D-051a, revision 2026-10-17, U-D17)."""


def version_info() -> VersionInfo: ...
```

Revision 2026-10-17 (U-D17, D-051a; `src/embodic/api.py` l.331-352 and `src/embodic/cli/commands.py` l.150 on main
0547f20, `verified` by reading, and by grep for a reader in `src` and `tools`).

The document names its shape. `outcome_to_json` adds `"format": "embodic.outcome"` and `"format_version": 2` at the top
level, next to `design`, `design_hash`, `provenance`, `issues`, `ok`, `boards`, `drc`, `analysis` and `versions`. A
document without `format` is version 1, the shape that embodic 0.0.1 writes. The evidence file (§3.1) and the board dump
(§9.2) already carry both keys. The outcome JSON was the one machine-written document that could not say which shape it
had, and a key rename is the first change that needs it.

What version 2 changes. D-051a renames two keys, and D-051f fixes the order of one list. Every other key keeps its name
and meaning.

| Version 1 pointer | Version 2 pointer |
|---|---|
| `/drc/<b>/violations/<i>/measured_mm` | `/drc/<b>/violations/<i>/clearance_mm` |
| `/drc/<b>/summaries/<i>/measured_min_mm` | `/drc/<b>/summaries/<i>/least_clearance_mm` |

In the pointers, `<b>` is the board index in `drc` and `<i>` is the list index. The list at `/drc/<b>/violations` is in
the canonical order of §7 in version 2, and in the least-margin-first order of main 0547f20 in version 1. A script that
reads the violation at one index therefore reads another violation in a version 2 file. The `measured` value at
`/provenance` is an input provenance and keeps its name (D-007).

- The project file schema stays at 1. The rule of §9.1 covers the project file, and the project file holds no DRC value.
  A bump to 2 would make embodic 0.0.1 refuse every 0.0.2 project file with `INVALID_SCHEMA_VERSION_NEWER`, although the
  content of those files did not change. `VersionInfo.schema` at `/versions/schema` is that project schema and stays 1.
- The product has no version 1 reader. `outcome_to_json` is called by `cli/commands.py` l.150 and by tests, and
  `src/embodic` and `tools` read no outcome JSON. The key map above is the whole migration for an outside script. Whether
  the user has such a script is `unresolved`.
- PK-04 compares two outcome folders only when their source hashes are equal
  (`docs/phase3/verification/checks/pk04_compare.py` l.53-56), so a 0.0.1
  file and a 0.0.2 file never meet there. A 0.0.2 build writes new Linux references in any case.
- `/boards/stack_hash` and `/boards/layout_hashes` are same-platform identities (§5, D-051f).

## 11. `embodic.ui`: theme, toolstrip and view-model contracts

View-models live in `embodic.ui.viewmodels` and import no Qt (import contracts C2 and C3). Qt views subscribe through
`Observable` and call view-model commands; the worker in `embodic.ui.workers` runs `compute` off the GUI thread with a
`CancelToken` per request (latest wins, REQ-N-02).

```python
class ThemeName(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseStyle:
    phase: Phase
    colour_hex: str  # red / blue / green per theme (D-011), from resources/themes/<theme>.json
    grey_hex: str  # greyscale ladder value
    hatch_deg: Literal[0, 45, 135]  # 0 = no hatch; hatch only inside the coil eye (REQ-N-23)
    dash: Literal["solid", "dash", "dot"]
    label: str  # "A", "B", "C"


@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeTokens:
    name: Literal["light", "dark"]
    colours: Mapping[str, str]  # chrome tokens (white / grey / black, REQ-L-04) plus status-pass, status-fail and
    # status-warn, the three semantic status tokens (D-038a)
    phases: tuple[PhaseStyle, PhaseStyle, PhaseStyle]
    focus_ring_px: int
    control_height_px: int


def load_theme(name: Literal["light", "dark"]) -> ThemeTokens:
    """Reads resources/themes/<name>.json, which tools/design/build_themes.py generates from resources/themes/tokens.json
    (the one source). Raises on a missing chrome token: the build ships both themes."""


def resolve_theme(choice: ThemeName, os_prefers_dark: bool) -> Literal["light", "dark"]: ...


class ToolstripTab(StrEnum):
    HOME = "home"
    DESIGN = "design"
    ANALYSIS = "analysis"
    EXPORT = "export"
    VIEW = "view"


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolstripAction:
    id: str  # also the Qt objectName and the string-catalogue key prefix
    tab: ToolstripTab
    icon: str  # file stem in resources/icons, monochrome SVG drawn with currentColor
    shortcut: str | None
    command: str  # name of a view-model command, resolved at startup (unknown name = startup error)
    group: str  # toolstrip group label key


TOOLSTRIP: tuple[ToolstripAction, ...] = (
    ToolstripAction(id="act-new", tab=ToolstripTab.HOME, icon="new", shortcut="Ctrl+N", command="new_design", group="file"),
    ToolstripAction(id="act-open", tab=ToolstripTab.HOME, icon="open", shortcut="Ctrl+O", command="open_project", group="file"),
    ToolstripAction(id="act-save", tab=ToolstripTab.HOME, icon="save", shortcut="Ctrl+S", command="save_project", group="file"),
    ToolstripAction(id="act-examples", tab=ToolstripTab.HOME, icon="examples", shortcut=None, command="show_examples", group="file"),
    ToolstripAction(id="act-undo", tab=ToolstripTab.HOME, icon="undo", shortcut="Ctrl+Z", command="undo", group="edit"),
    ToolstripAction(id="act-redo", tab=ToolstripTab.HOME, icon="redo", shortcut="Ctrl+Y", command="redo", group="edit"),
    ToolstripAction(id="act-topo-spiral", tab=ToolstripTab.DESIGN, icon="topology-spiral", shortcut=None, command="set_topology_spiral", group="topology"),
    ToolstripAction(id="act-topo-serpentine", tab=ToolstripTab.DESIGN, icon="topology-serpentine", shortcut=None, command="set_topology_serpentine", group="topology"),
    ToolstripAction(id="act-topo-wave", tab=ToolstripTab.DESIGN, icon="topology-wave", shortcut=None, command="set_topology_wave", group="topology"),
    ToolstripAction(id="act-conn-star", tab=ToolstripTab.DESIGN, icon="connection-star", shortcut=None, command="set_connection_star", group="connection"),
    ToolstripAction(id="act-conn-delta", tab=ToolstripTab.DESIGN, icon="connection-delta", shortcut=None, command="set_connection_delta", group="connection"),
    ToolstripAction(id="act-compute", tab=ToolstripTab.ANALYSIS, icon="compute", shortcut="F5", command="compute_now", group="run"),
    ToolstripAction(id="act-drc", tab=ToolstripTab.ANALYSIS, icon="drc", shortcut=None, command="show_checks", group="run"),
    ToolstripAction(id="act-equations", tab=ToolstripTab.ANALYSIS, icon="equations", shortcut=None, command="show_equations", group="reference"),
    ToolstripAction(id="act-export-svg", tab=ToolstripTab.EXPORT, icon="export-svg", shortcut=None, command="export_svg", group="drawings"),
    ToolstripAction(id="act-export-dxf", tab=ToolstripTab.EXPORT, icon="export-dxf", shortcut=None, command="export_dxf", group="drawings"),
    ToolstripAction(id="act-export-pdf", tab=ToolstripTab.EXPORT, icon="export-pdf", shortcut=None, command="export_pdf", group="report"),
    ToolstripAction(id="act-export-all", tab=ToolstripTab.EXPORT, icon="export-all", shortcut="Ctrl+E", command="export_bundle", group="report"),
    ToolstripAction(id="act-theme", tab=ToolstripTab.VIEW, icon="theme", shortcut=None, command="cycle_theme", group="appearance"),
    ToolstripAction(id="act-greyscale", tab=ToolstripTab.VIEW, icon="greyscale", shortcut=None, command="toggle_phase_render_mode", group="appearance"),
    ToolstripAction(id="act-fit", tab=ToolstripTab.VIEW, icon="zoom-fit", shortcut="F", command="fit_view", group="view"),
    ToolstripAction(id="act-tests", tab=ToolstripTab.VIEW, icon="check-pass", shortcut=None, command="show_tests", group="help"),
)


class Observable(Generic[T]):
    """Minimal pure-Python observable value for view-models; Qt views subscribe, tests call value directly."""

    @property
    def value(self) -> T: ...
    def subscribe(self, callback: Callable[[T], None]) -> Callable[[], None]: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionEmpty:
    """App start: no design open. The New design dialog and the Examples gallery are offered (D-014)."""

    state: Literal["empty"] = "empty"


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionDrafting:
    """Required fields missing: form editable, nothing computed, results area shows the missing list."""

    state: Literal["drafting"] = "drafting"
    draft: DesignDraft
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionComputed:
    """A complete design. `outcome` is None while the first compute runs; `stale` marks a kept last valid layout."""

    state: Literal["computed"] = "computed"
    design: DesignParameters
    provenance: ProvenanceMap
    outcome: ComputeOutcome | None
    stale: bool
    computing: bool


SessionState: TypeAlias = SessionEmpty | SessionDrafting | SessionComputed


class DesignSessionViewModel(Protocol):
    """State machine of one open design. Every command returns at once; computes run in the worker."""

    state: Observable[SessionState]
    can_undo: Observable[bool]
    can_redo: Observable[bool]

    def new_design(self, topology: TopologyKind) -> None: ...
    def load_example(self, example_id: str) -> None: ...
    def open_project(self, path: Path) -> tuple[ValidationIssue, ...]: ...
    def save_project(self, path: Path) -> str: ...
    def edit(self, pointer: str, value: JsonValue) -> None:
        """Re-entering the current value is a no-op (no undo entry, no recompute, PR-12)."""
    def mark_measured(self, pointer: str, source: str) -> ValidationIssue | None: ...
    def apply_suggestion(self, suggestion: Suggestion) -> None:
        """Applies with an inline notice 'Changed from X to Y: reason' and an Undo entry (REQ-F-23)."""
    def undo(self) -> None: ...
    def redo(self) -> None: ...
    def compute_now(self) -> None: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ResultRow:
    """One displayed number (REQ-T-01): everything the row and its 'How was this computed' disclosure need."""

    quantity: str
    label: str
    title: str  # the label, then the symbol the equation specification states (QUANTITY_SYMBOLS, §3)
    value_text: str
    unit_text: str
    status: Status
    assumed_count: int
    eq_ids: tuple[str, ...]
    estimate_label: str | None
    traceable: Traceable[float]


class ResultsViewModel(Protocol):
    rows: Observable[tuple[ResultRow, ...]]
    status_filter: Observable[frozenset[Status]]

    def set_status_filter(self, statuses: frozenset[Status]) -> None: ...
    def copy_trace(self, quantity: str) -> str: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportPreflight:
    drc_passed: bool
    failures: tuple[DrcViolation, ...]
    needs_confirmation: bool  # True when the DRC failed or did not run; which selections ask is stated below (REQ-F-33)


class ExportViewModel(Protocol):
    def preflight(self) -> ExportPreflight: ...
    def export(self, kinds: Sequence[ExportKind], folder: Path, *,
               confirmed_drc_errors: bool) -> tuple[ExportSummary, ...] | ExportRefused: ...


class AppearanceViewModel(Protocol):
    theme: Observable[ThemeName]
    phase_render_mode: Observable[PhaseRenderMode]
    canvas_share: float  # fraction of the centre pane the canvas takes (U-S4e ruling b)

    def cycle_theme(self) -> None: ...
    def toggle_phase_render_mode(self) -> None: ...
    def set_canvas_share(self, canvas_px: int, results_px: int) -> None:
        """Remember the split a drag left as the fraction canvas / (canvas + results)."""
```

Revision 2026-10-13 (U-D14, claude-sonnet-5-5; D-046a, D-045e, D-038d; `src/embodic/ui/viewmodels/export.py` l.72-74,
l.120-122 and l.206-219 on main 76f054b, `verified` by reading). `needs_confirmation` says only that the DRC failed or did
not run. Whether `dlg-export-confirm` opens depends on the selection. The view model keeps `UNGATED`, the set of the
PDF report, the README and the JSON project file. `needs_drc_confirmation(preflight, formats)` is `needs_confirmation`
and the selection holds a format outside `UNGATED`, so only the SVG, the three DXF files and the ZIP bundle ask. A
selection inside `UNGATED` runs without the dialog and without `confirmed_drc_errors` (`run`, l.218). The PDF report and
the README document the DRC state, and the project file is the design itself, not a fabrication drawing (D-046a). The
bundle keeps the gate when it is chosen, because `write_bundle` refuses the whole archive (§9.3). The CLI has no project
format (`DOCUMENTS = {pdf, readme}`, `src/embodic/cli/commands.py`), so the `--format` list of §12 does not change. Tests,
`verified` by running `pytest tests/ui/qt_results/test_charts_compare_guide_export.py -k "export_dialog or
export_confirmation"` (`4 passed`): `test_export_dialog_on_a_failed_drc_writes_the_report_and_readme_and_refuses_the_drawings`
(l.198) and `test_export_dialog_on_a_failed_drc_writes_the_project_file_without_the_confirmation` (l.230, `Catches a
project file that waits for the confirmation meant for drawings`).

Revision 2026-10-13 (U-D14, claude-sonnet-5-5, D-045c; `src/embodic/ui/toolstrip.py` l.144-146, `ui/strings/shell.py` l.23 and
l.71-72 and `ui/views/main_window.py` l.207 and l.340 on main 6243163, `verified` by reading; the count `verified` by
importing the module: `PYTHONPATH=src python3 -c "from embodic.ui.toolstrip import TOOLSTRIP; print(len(TOOLSTRIP))"`
printed 22). The Tests dialog opens from the toolstrip action `act-tests`, the last row of `TOOLSTRIP` above.

| Field | Value |
|---|---|
| `id` | `act-tests`, also the Qt object name and the prefix of the string keys `act-tests.label` ("Self-tests") and `act-tests.tooltip` |
| `tab`, `group` | View tab, group `help` (`toolstrip.group-help.label` is "Help") |
| `icon` | `check-pass` (`resources/icons/check-pass.svg` exists) |
| `shortcut` | None |
| `command` | `show_tests`, which `MainWindow.show_tests` implements. It creates the Tests dialog (`dlg-tests`) on first use and shows it. A run never touches the results or their badges (D-045d, §14) |

`TOOLSTRIP` holds 22 actions: Home 6, Design 5, Analysis 3, Export 4 and View 4 (`verified` by running the same import
with a count per `tab`). Before D-045c it held 21. UI-25 (`test_plan.md` §5.3) covers the new row with the others,
because its tests loop over `TOOLSTRIP` (`tests/ui/qt_shell/test_toolstrip_and_start.py` l.48 and l.64-72, `7 passed`
when run on main 6243163).

Revision 2026-10-09 (U-D9, D-038a; `src/embodic/ui/theme.py`, `tools/design/build_themes.py` and
`resources/themes/*.json` on main 3acb044, `verified` by reading and by running). Theme tokens and the theme generator:

- `ThemeTokens.colours` holds 20 tokens per theme: the 17 chrome tokens (grey only, REQ-L-04; `CHROME_TOKENS`,
  `theme.py` l.18) and the three semantic status tokens `status-pass`, `status-fail` and `status-warn` (D-038a). The
  status tokens are the only chromatic entries. REQ-L-04's rule of white, grey and black names the chrome tokens. The
  six `phase-*` colours live in `phases`, not in `colours`.
- The status tokens are keys of `colours`, not fields of `ThemeTokens`. `parse_theme` (`theme.py` l.106) requires only
  `CHROME_TOKENS`, so a theme file without a status token still loads (17 colours, run on `light.json`).
  `tools/design/check_theme_tokens.py` requires all 20 (`STATUS_TOKENS`, l.26). `token_hex` in `tools/contrast_check.py`
  (l.67) looks up the contrast pairs of `tokens.json` in `colours`, and some pairs name a status token. A theme file
  without them therefore raised `KeyError: 'status-pass'` in `tests/unit/ui/shell/test_contrast_check.py` on main
  bcc6749 (U-M4r-fix report).
- `load_theme` (`theme.py` l.126) reads `resources/themes/<name>.json`. `tools/design/build_themes.py` writes that file
  (`theme_tokens`, l.64) with the QSS and the glyphs from `resources/themes/tokens.json`, the one source of colours.
  Running the generator twice leaves `git status` clean.

Revision 2026-10-09 (U-D10, D-039 a and e; `src/embodic/ui/fonts.py`, `ui/views/main_window.py`, `ui/viewmodels/results.py`
and `ui/strings/shell.py` on main fd190c1, `verified` by reading and by running `tests/ui/qt_shell/test_fonts.py` and
`test_rail_layout.py`, which pass). Fonts and the results rail.

```python
# embodic.ui.fonts (U-M4f; static Inter files from U-M4e-1). Imports no Qt (contract C2): the app passes Qt's loader and the application in.
INTER: str  # "Inter": the typographic family of the two static files; Qt registers SemiBold as its 600 style
JETBRAINS_MONO: str  # "JetBrains Mono"
UI_FALLBACKS: tuple[str, ...]  # ("Segoe UI",), then the platform sans
MONO_FALLBACKS: tuple[str, ...]  # ("Cascadia Mono", "Consolas", "monospace")
BODY_PX: int  # 13
FONT_FILES: Mapping[str, tuple[str, ...]]  # family -> files relative to resources/fonts


def font_file(relative: str) -> Path: ...
def register_fonts(add_font: Callable[[str], int], application: FontApplication[F]) -> None:
    """Load every bundled file and make Inter 13 px the application font. RuntimeError when Qt cannot load a file."""
```

- `register_fonts` (`fonts.py` l.57) loads the four files of `FONT_FILES` (l.19) through the loader it receives: Inter
  Regular, Inter SemiBold, JetBrains Mono Regular and JetBrains Mono Medium. It sets the application font to Inter at 13
  px with Segoe UI after it, and names the substitutes for JetBrains Mono. A file Qt cannot load raises `RuntimeError`,
  because the install is broken. No font is fetched at run time (D-039 a). The files, their licences and their SHA-256
  values are in `resources/fonts/FONTS.md`. Revision 2026-10-09 (U-D11, U-M4e-1): `qt_application` (`ui/app.py` l.184)
  creates the `QApplication` when none exists and calls `register_fonts` (l.192) on it. `main` (l.197) calls it at l.203, and every
  screenshot lever under `tests/ui` start Qt there, and `tests/ui/conftest.py` registers the fonts in a session fixture,
  so the app, the captures and the UI tests all render in the fonts the user sees.
- The Inter weights are real faces (revision 2026-10-09, U-D11; U-S4e ruling e2). Qt ignores the `wght` axis of a
  variable file (U-M4f report, `inferred`), so weight 600 rendered at body weight with the variable Inter file. Main 9776555
  bundles `Inter/Inter-Regular.ttf` (400) and `Inter/Inter-SemiBold.ttf` (600) of the Inter v4.1 release and no variable
  file. `INTER` is "Inter" (`fonts.py` l.13). The SHA-256 values in `FONTS.md` equal `sha256sum` of the files
  (`verified` by running it, 2026-10-09). `test_ruling_e2_weight_600_resolves_to_the_bundled_semibold_face`
  (`tests/ui/qt_shell/test_fonts.py` l.35) checks that Qt resolves 600 to the SemiBold face. The PDF embeds the same two
  files (§9.3).
- The results rail (D-039 e, UX-AC-21). From 1280 px window width (`THREE_PANE_FROM_PX`, `main_window.py` l.101) the
  rail is the third pane of the splitter, 360 px wide (`RAIL_PX`, l.103), inside a `QScrollArea` named `rail-scroll`
  (l.256). Below 1280 px the same widget is the first tab after the drawing in `results-tabs`, titled by the string
  `shell.results-rail.title`, "Key results" (`strings/shell.py` l.81). `_place_rail` (l.755) moves it on every
  `resizeEvent` (l.784), so the rail never appears in both places. The inspector is 300 px in the two-pane layout and 340
  px in the three-pane layout (`INSPECTOR_PX`, l.102). The rail shows an "Inputs" card and a "DRC" card with glyphs in
  place of the earlier "Design" card (D-039 e; `results_rail.py` l.1, `strings/results.py` l.15). Tests:
  `test_ux_ac_21_from_1280_px_the_rail_is_the_third_pane_inside_a_scroll_area`
  (`tests/ui/qt_shell/test_rail_layout.py` l.43) and its three siblings at l.56, l.70 and l.86.
- `ResultRow` gains `title: str`, the label followed by the specification symbol (§3, `quantity_title`). The stub of
  this section lists the field.
- The two known gaps of the U-M4d-fix report are closed on main 9776555 (revision 2026-10-09, U-D11). The Results card
  grid takes its column count from the scroll area beside its scroll bar, and the DRC table has the column set below
  (both in the next block). `INSPECTOR_PX` and `RAIL_PX` are unchanged by U-M4e-1; the start widths of 340 px and 360 px
  at 1280 px came from removing a second set of side margins, not from new constants (next block).

Revision 2026-10-09 (U-D11, claude-sonnet-5-5; `src/embodic/ui` and `tests/ui` on main 9776555 read for every item).
U-S4e rulings b to h and the board picker of screens.md §4.1, as U-M4c-4 and U-M4e-1 built them. The test modules named
below were run on main 9776555 with `QT_QPA_PLATFORM=offscreen`; the report of U-D11 quotes the results.

```python
# embodic.ui.viewmodels.appearance (U-M4e-1)
CANVAS_SHARE: float  # 0.6: the canvas gets 60 percent of the centre pane by default
CANVAS_MIN_PX: int  # 240
RESULTS_MIN_PX: int  # 180
COMPACT_BELOW_PX: int  # 620: under this window height the canvas becomes the first results tab


class AppearanceStore(Protocol):
    def load_theme(self) -> str | None: ...
    def save_theme(self, value: str) -> None: ...
    def load_canvas_share(self) -> float | None:
        """The stored canvas fraction (0 to 1), or None when nothing readable is stored."""
    def save_canvas_share(self, value: float) -> None: ...


def split_sizes(total_px: int, share: float) -> tuple[int, int]:
    """Canvas and results heights of a centre pane total_px tall, both held to their minimums."""


# embodic.ui.viewmodels.outcome (U-M4c-4): the board picker state
class OutcomeViewModel(Protocol):
    board: Observable[int | None]  # None is "All boards"; k is the board of phase letter k

    def select_board(self, index: int | None) -> None:
        """An index at or above the board count, and any index of a one-board design, give None."""
    def step_board(self, delta: int) -> None:
        """Page Up (-1) and Page Down (+1): "All boards", then board A, B, C; stops at both ends."""
    def step_layer_solo(self, delta: int) -> None:
        """[ (-1) and ] (+1): solo the previous or next layer of the drawn boards; all layers lie between."""
```

Board picker (screens.md §4.1, U-M4c-4 a).

- `board-picker` is a `QComboBox` (`ToolstripBar.board_picker`, `ui/views/toolstrip_bar.py` l.191) with the caption
  "Board" (`toolstrip.group-board.label`, `strings/shell.py` l.22), inside the frame `ts-section-board` (l.187) of the
  View tab. It is not a `ToolstripAction`. `TOOLSTRIP` is unchanged by the picker: a picker has no command. It held the 21 actions then (`verified` by
  counting the rows in `ui/toolstrip.py`), and holds the 22 actions above since D-045c added `act-tests` (revision 2026-10-13,
  U-D14). The bar emits `board_selected` (l.94) with
  the index or None, and the window connects it to `OutcomeViewModel.select_board` (`main_window.py` l.172).
- Items. "All boards" (data None) and one "Board A", "Board B" or "Board C" per board (`strings/shell.py` l.23-24).
  Each item has a swatch (`board_swatch`, l.48) that repeats the letter and turns grey in greyscale mode, so colour is
  never the only cue (D-011). `show_boards` (l.204) rebuilds the items when the letters, the theme or the render mode
  change, and hides `ts-section-board` when the design has one board.
- Which designs. `board_letters` (`ui/viewmodels/outcome.py` l.338) returns the first phases, one per board, when the
  scene holds more than one board and () otherwise. Board k of a per-phase stack holds phase k (§5). The picker
  therefore shows for a serpentine design built as one board per phase, and never for a spiral or wave design, whose
  stack holds one board. `scene_of_board` (l.346) gives the scene of one board, with its marks, or the whole scene for
  None.
- The state. `OutcomeViewModel.board` (l.144) starts at None. `select_board` is l.195 and `step_board` is l.200. A new
  result with fewer boards than the choice resets it to None (`on_ready`, l.177).
- Keys. `GeometryView.board_step` (`geometry_view.py` l.142) fires for Page Up (-1) and Page Down (+1), `layer_step`
  (l.143) for `[` and `]`. The window connects both to the view-model (`main_window.py` l.170-171). Layer solo works
  inside the board the picker shows, or on every board for "All boards" (`step_layer_solo`, `outcome.py` l.208).
- Results and exports ignore the picker (screens.md §4.1). `counts_text` (`outcome.py` l.372) is the `st-counts` text:
  a stack reads in the form of `shell.st-counts.stack` (`strings/shell.py` l.106): "{boards} boards, {layers} copper
  layers each, {phases} phases, {vias} vias". A spiral names its coils and a serpentine or wave names its phases
  (U-S4e ruling h).
- Tests. `tests/ui/qt_design/test_board_picker.py`: hidden for spiral, wave and single-board serpentine (l.60); items of
  the per-phase serpentine (l.72); selecting Board B leaves only its copper in the scene (l.86); Page Down and Page Up
  (l.101); `[` and `]` (l.114); the swatch in colour and in greyscale (l.136, l.149); Locate sets the picker (l.162);
  `st-counts` of a stack (l.213). `tests/unit/ui/shell/test_outcome_viewmodel.py` pins the view-model alone (l.213 to
  l.264).

Vertical layout (U-S4e ruling b, UX-AC-21).

- `centre-split` is a vertical `QSplitter` (`main_window.py` l.223) with the canvas page above `results-tabs`. The
  canvas gets `CANVAS_SHARE` of the pane by default (`appearance.py` l.9), at least `CANVAS_MIN_PX` (l.10), and the
  results keep at least `RESULTS_MIN_PX` (l.11). `split_sizes` (l.37) computes the two heights. Neither pane collapses.
- The window sets the sizes on every resize of the splitter (`eventFilter`, `main_window.py` l.777), so the size hint of
  a results tab never moves the split. Before this rule the canvas was 112 px tall at 960 x 540 and 124 px at 1280 x 800
  (m4_review_2.md, R13 and R14).
- Under `COMPACT_BELOW_PX` (620 px) of window height the canvas page becomes the first tab of `results-tabs`, titled
  "Drawing" (`shell.drawing.title`, `strings/shell.py` l.82), and returns to the split when the window grows
  (`_place_canvas`, `main_window.py` l.766). `_show_drawing` (l.290) brings it forward after Locate and after a design
  opens (`DesignSession.opened`, `session.py` l.666).
- The share is stored per user as a fraction, not in pixels, under the QSettings key `layout/canvas_share`
  (`CANVAS_SHARE_KEY`, `ui/app.py` l.38). `AppearanceViewModel.set_canvas_share` (`appearance.py` l.61) stores
  canvas / (canvas + results) when a drag ends (`splitterMoved`, `main_window.py` l.231). The view-model reads a stored
  value between 0 and 1 at start and takes `CANVAS_SHARE` otherwise (l.54). `QSettingsStore.load_canvas_share` and
  `save_canvas_share` (`app.py` l.60 and l.67) implement the store, and an unreadable value gives None.
- Tests. `tests/ui/qt_shell/test_centre_split.py`: 60 percent at 1280 x 800 (l.20), the "Drawing" tab under 620 px
  (l.33), the canvas back in the split (l.50), a dragged share stored and restored (l.61).
  `tests/unit/ui/shell/test_appearance_and_strings.py`: `split_sizes` within both minimums (l.96) and the stored
  fraction (l.102).

Start widths (U-S4e ruling c).

- At 1280 px the inspector starts at 340 px and the rail at 360 px. The constants are unchanged: `INSPECTOR_PX`
  (300, 340) and `RAIL_PX` 360 (`main_window.py` l.102-103). The panes measured 327 and 347 px because the filter row of
  the Results tab carried a second set of side margins, whose minimum width forced the centre pane to 598 px. U-M4e-1
  removed those margins (commit 14ae65e, `ui/views/results_view.py`). `test_ruling_c_at_1280_px_the_panes_start_at_340_and_360_px`
  (`tests/ui/qt_shell/test_rail_layout.py` l.98) pins both widths.
- The inspector tab bar fits the 300 px inspector in Inter: the tabs take 8 px of padding a side
  (`main_window.py` l.203-204, ruling h; the comment there names the ruling). `test_ruling_h_the_inspector_tab_bar_fits_the_300_px_inspector_in_inter`
  (`test_rail_layout.py` l.108) pins it.

Layers tab and Board tab (U-S4e ruling c).

- A pair spans two layers, so it has its own table. `layer-list` holds Layer, Kind and Thickness (`LAYER_COLUMNS`,
  `ui/views/layer_panel.py` l.43). `pair-list` holds Pair, Layers and Rotation (`PAIR_COLUMNS`, l.44). Kind shows in
  full, and both tables fit the 300 px inspector without sideways scroll.
- `pair-list` carries the pair commands. The Delete key removes the selected pair, not its copper layers
  (`delete_selected_pair`, l.172, calling `DesignSession.delete_pair`, `session.py` l.742). A row menu puts the selected
  pair in a series group (`_series_menu`, l.181, calling `DesignSession.set_series_group`, `session.py` l.758). A pair
  the copper count makes stays listed after Delete as a dimmed row and returns when the count changes (`PairSlot` l.50,
  `pair_slots` l.59, D-032b), and the notice `pair-list.removed` says so.
- Pointers and widgets (`model/fields.py`, widget id strings only). `/winding/layers/pairs`, its `index`, `layer_in`,
  `layer_out` and `phases` leaves, and `/winding/layers/series_groups` have `widget_id` `pair-list` (l.160 to l.166).
  `/winding/layers/pairs/*/rotation_rad` keeps `param-pair-rotation` (l.164), the field that edits the pair selected in
  `pair-list` (`ROTATION_WIDGET`, `layer_panel.py` l.46). `tab_of_widget` (`session.py` l.367) maps `pair-list` to
  `tab-layers`. No FIELDS pointer is new.
- `screw-table` has three columns, Size, Count and Pitch radius (`SCREW_COLUMNS`, `board_rotor_panel.py` l.37). The other
  leaves of the selected pattern are fields beside `param-screw-hole-diameter` (l.204, D-031a): `param-screw-fit` for
  `/outline/screws/*/fit` (l.201) and `param-screw-angle-offset` for `/outline/screws/*/angle_offset_rad` (l.206).
- Tests. `tests/ui/qt_design/test_pair_list.py` (rows with layers, vias and the rotation chip l.32, Delete l.41, series
  menu l.61, rotation field l.76), `test_ruling_g.py` (l.53 and l.64, the 300 px fit),
  `test_inspector_widgets.py` l.112 (the screw table) and `tests/unit/model/test_fields.py` (l.113 and l.128, the
  pointer bindings).

DRC table and result cards (U-S4e ruling d, DEF-1 and DEF-2).

- Columns. `COLUMNS` (`ui/views/checks_view.py` l.43) is glyph, Board, Message, Clearance, Required, Layer (the fourth
  column read "Measured" until revision 2026-10-17, U-D17, D-051a). The glyph
  column is `GLYPH_PX` (24) wide, and Message takes the width the others leave, at least `MESSAGE_MIN_PX` (l.49, 200)
  on two lines. A table too narrow for that scrolls. The rule code and the severity word moved to the row tooltip and the
  accessible text (`row_description`, l.208). `test_ruling_d_drc_table_shows_glyph_message_measured_required_layer_without_sideways_scroll`
  (`tests/ui/qt_results/test_results_and_checks.py` l.155) pins the set, and the Clearance and Required cells hold the
  number only (l.172). The test name keeps the old word until Agent 3 renames it with the column.
- The word "clearance" in the window (revision 2026-10-17, U-D17, D-051a). Main 0547f20 says "measured" at these places
  (`verified` by grep): the column id `measured` and the string `drc.column.measured` "Measured\n(mm)"
  (`ui/views/checks_view.py` l.43, l.181, `ui/strings/results.py` l.85), the row description "Measured {measured}"
  (`strings/results.py` l.87), `DrcRow.measured_text` (`ui/viewmodels/results.py` l.310), the export confirmation row
  "{measured} measured, {required} required" (`ui/strings/export.py` l.45) and the PDF column "Least measured"
  (`io/report.py` l.137). D-051a gives all of them "clearance" or "least clearance", and the id, the field and the
  format keys follow the new word. Agent 1 writes the strings and Agent 3 changes the code
  (`docs/phase3/architecture/v3_contract_rulings.md` §1, edit table). The chip "measured" and the command "Mark as
  measured..." of the inspector (`ui/strings/design.py`) stay, because they name an input provenance with a named
  source (D-007).
- The Board column. `DrcRow.board_text` (`ui/viewmodels/results.py` l.271) holds the phase letter of the failure's
  board and "" for a one-board design. `DrcTable.boards` (l.284) lists the letters when the design has more than one
  board, and the view hides the column otherwise (`checks_view.py` l.187). `drc_table` (l.298) lists the violations of
  every board whatever the picker shows. `drc-summary` appends one verdict per board, for example "Board A pass, Board B
  2 failures" (`_board_verdict`, l.291, string `drc.summary.boards`). Locate sets the picker to the row's board, then the
  drawing, then zooms (`MainWindow._locate`, `main_window.py` l.284). Tests: `test_checks_charts_compare_guide.py` l.52
  and l.69, `test_board_picker.py` l.162, l.184 and l.202.
- Card grid. The Results tab takes its column count from the scroll area beside its scroll bar (`_columns_that_fit`,
  `ui/views/results_view.py` l.340) with cards at least `CARD_MIN_WIDTH_PX` (l.54, 280) wide and `CARD_GAP_PX` (l.55,
  8) apart. `test_no_result_card_is_cut_off_at_the_right_of_the_grid` (`tests/ui/qt_results/test_results_grid.py` l.20)
  checks that no card passes the viewport at 1280 x 800 and 1600 x 900.

Open (F21). `act-open` (`TOOLSTRIP`, unchanged) is enabled. The command name `open_project` resolves in
`MainWindow._commands` (`main_window.py` l.182) to `open_project_dialog` (l.696), which asks for a file and calls
`open_project_file` (l.702) and then `DesignSession.open_project` (`session.py` l.686). A file that does not load
shows its reasons in a message box and changes nothing. `test_f21_open_loads_a_saved_d08_file_into_the_inspector_and_computes_it`
(`tests/ui/qt_shell/test_open_project.py` l.25) and `test_f21_a_file_that_does_not_load_says_why_and_keeps_the_open_design`
(l.43) pin both cases. The session stub above keeps `open_project(path)`.

Gallery selection and window title are screens.md matters (ruling h): a selected gallery item draws title and note in
`text-inverse` (`ExamplesGallery._ink_selection`, `ui/views/examples_gallery.py` l.89), pinned by
`test_ruling_h_the_selected_example_draws_title_and_note_in_text_inverse` (`test_ruling_g.py` l.151).

Revision 2026-10-11 (U-D12, claude-sonnet-5-5; `src/embodic/ui` on main 4fda98d read for every item). Three view changes of
U-M4e-2 (`m4_review_2.md` §6) and one deletion. The tests that pin them are in `tests/ui/qt_e2e/test_review_2_fixes.py`
(`test_plan.md` §5.3.1).

- Ruling i (F3). `btn-screw-add` and `btn-screw-remove` are `QPushButton`, no longer `QToolButton`
  (`board_rotor_panel.py` l.109 and l.113). They use the push-button style with a boundary of 3:1 against the pane
  (UX-AC-08). `test_ruling_i_the_screw_buttons_are_push_buttons_with_a_3_to_1_boundary` (l.45) grabs both buttons and
  measures the contrast.
- Ruling j (F1). The last column of `layer-list`, `pair-list` and `screw-table` takes the remaining width, so no header
  cell is empty. The call is `horizontalHeader().setStretchLastSection(True)` in `_fill` (`layer_panel.py` l.330, which
  fills `layer-list` and `pair-list`), again for `pair-list` after its rotation cells are set (l.287), and for
  `screw-table` (`board_rotor_panel.py` l.209). `test_ruling_j_the_last_column_takes_the_remaining_width_so_no_header_cell_is_empty`
  (l.65) asserts `header.length() >= viewport.width()` at 1280 x 800 and 960 x 540.
- F2. The rotation chip of a `pair-list` row carries the dynamic property `provenance` beside `class` = `prov-chip`
  (`_value_with_chip`, `layer_panel.py` l.333, third argument; `setProperty` at l.342). The QSS rule
  `QLabel[class="prov-chip"][provenance="example"]` (`tools/design/theme_template.qss` l.109) draws the dashed example
  chip, and a chip without the property drew the solid default. `test_f2_the_pair_list_rotation_chip_carries_its_provenance_for_the_dashed_example_rule`
  (l.27) loads `spiral_12c14p` and reads `{("example", "example")}` over the chips of its pair rows.
- The string `shell.sum.assumptions` is deleted (`strings/shell.py`). No code read it (U-M4e-2 report).
  `OutcomeReady.summary` stays, because `tests/unit/ui/shell/test_outcome_viewmodel.py` l.108 reads it. §13 point 11
  carries its deletion.
- Target sizes. The EQ chip, the assumption tag, the check box click rectangle and the scroll bar are below the AX-04
  size on main 4fda98d (`test_plan.md` §5.6). §11 states no size for them yet, because the rulings are Agent 1's
  (U-S4g) and the change is Agent 3's (U-M4e-3).

## 12. `embodic.cli`

```python
class ExitCode(IntEnum):
    OK = 0
    VALIDATION_ERRORS = 1  # also: incomplete draft, unreadable file
    DRC_ERRORS = 2
    INTERNAL_ERROR = 3


def main(argv: Sequence[str] | None = None) -> int:
    """embodic-cli compute <project.embodic.json> [--json OUT] [--no-drc] [--timings]
    embodic-cli validate <project.embodic.json>
    embodic-cli export <project.embodic.json> --format {svg,dxf,dxf-outline,dxf-screws,pdf,readme,bundle} -o PATH
                [--allow-drc-errors]
    embodic-cli selftest [--json OUT]      (revision 2026-10-12, U-D13; §14)
    The desktop app entry point is `embodic` (embodic.ui.app:main)."""
```

`embodic-cli selftest` (U-M5d, after U-M5a merges) runs `run_selftests(SELFTESTS)` of §14 and prints one line per
check, with the verdict word, the check ID, the duration and, for a failure, the message. The last line is the summary of
screens.md §13 ("45 tests: 45 passed, 0 failed"). The exit code is `ExitCode.OK` when `SelfTestReport.ok`, else
`ExitCode.VALIDATION_ERRORS` (value 1). The enum keeps its four members, so the U-M5a code needs no change. A check
that raises is a failed check, not exit code 3. `--json OUT` writes `selftest_to_json(report)`. Ctrl+C cancels through
the `CancelToken`, prints the summary with the remaining checks as `not run`, and exits 1. Test: UT-CLI-03.

`embodic-cli export` and the DRC verdict (revision 2026-10-13, U-D14, claude-sonnet-5-5; D-045e, D-038d;
`src/embodic/cli/commands.py` l.189-241 on main 6243163, `verified` by reading, and by running each command below on
`resources/examples/wave_16p_example.embodic.json`, which fails its DRC with 186 violations). The PDF report and the README
document the DRC state, so they never wait for the confirmation of REQ-F-33. The drawings and the bundle do.

| `--format` | Design fails the DRC | Output | Exit |
|---|---|---|---|
| `pdf`, `readme` | The file is written. `--allow-drc-errors` changes nothing | `Wrote <path>`, then `Design rule check: FAILED, 186 violations` | 0 |
| `svg`, `dxf`, `dxf-outline`, `dxf-screws`, `bundle` | Nothing is written | on stderr: `DRC_EXPORT_NOT_CONFIRMED` with the violation count, one issue per failing check kind (`DRC_TRACE_TRACE` and `DRC_TRACE_VIA` here) and `DRC_CLI_EXPORT_REFUSED`, which names `--allow-drc-errors` | 2 |
| the same five, with `--allow-drc-errors` | The file is written | `Wrote <path>`, then the warning `DRC_CLI_EXPORT_FORCED` with `value: 186` on stderr | 0 |

When the DRC passes, `pdf` and `readme` print only the `Wrote` line and the other formats print no warning. The report
itself prints the DRC result (§9.3). A refusal for another reason, `no_layout` or `no_screws`, exits 1 (`REFUSAL_EXIT`,
`commands.py` l.199-203). `bundle` holds the drawings, the project JSON and the PDF report (`_bundle`, l.179-185), and
`write_bundle` applies the gate to the whole archive (§9.3, revision U-D9), so the bundle keeps the refusal.

What ran. The commands on the wave example printed the exit codes `pdf` 0, `readme` 0, `svg` 2, `dxf` 2, `bundle` 2 and
`svg --allow-drc-errors` 0. `dxf-outline`, `dxf-screws` and the flag on `dxf` and `bundle` use the same code path
(`commands.py` l.189-192 and l.232-238). This unit read that path and did not run those cases by hand. The tests are in
`tests/unit/cli/test_export_command.py`: `test_a_failed_drc_refuses_drawings_and_the_bundle_without_confirmation` (all
five gated formats), `test_d_045e_the_pdf_report_of_a_failed_drc_is_written_and_prints_the_drc_result`,
`test_d_045e_the_readme_of_a_failed_drc_is_written_without_confirmation` and
`test_allow_drc_errors_writes_the_file_and_warns`. The module gives `48 passed` (`verified` by running it again on main
76f054b, 90 s). The line numbers above hold on main 76f054b (`verified` by reading). The CLI has no project format
(`DOCUMENTS` and `WRITERS` list `svg`, `dxf`, `dxf-outline`, `dxf-screws`, `pdf`, `readme` and `bundle`), so D-046a, which
lets the GUI export dialog write the JSON project file without `dlg-export-confirm`, leaves this table and the
`--format` list as they are. The `bundle` row still refuses, because the archive holds the drawings. The GUI dialog has
two tests of its own (§11, revision note after `ExportViewModel`).

## 13. Open interface points

1. Closed 2026-10-05 (U-D3, D-016). `SerpentineWindingSpec` has `stack_mode` and `board_gap_mm` with their FIELDS rows
   (§2.2), and a design's boards are a `BoardStack` of one `Layout` per board (§5). U-M2a's fix round adds the fields
   and rows; U-M2d builds the stack type into the generator interface; U-M3a builds the per-phase serpentine.
2. Closed 2026-10-08 (U-D4, D-031f). §8 restates the kernel argument lists as merged; `checks/physics_signatures.py`
   compares every public name of `embodic.physics` with its stub and lists the three EQ-20 drive changes U-M2e-4
   still owes. Revision 2026-10-08 (U-D6, DEF-M2e4-02): U-M2e-4 merged them, so the PENDING list is empty and the
   check passes on main a336531 with 33 names compared.
3. Whether Xcoil's serpentine analysis path (`engine.js` `analyze`, l.880-1017) and the generic element path
   (`analyzeElements`, l.1846) give the same EMF for the same copper is `unresolved`; GR-22 measures it (test_plan.md).
4. Board dump v2 (added 2026-10-05, U-M1b report). v1 cannot say three things: a Member with several paths (v1 writes
   one `members[]` entry per path, so the grouping of paths into one route is lost), the polarity of a path (the
   GR-19 mapper writes `polarity=0` because Xcoil does not return it), and the DRC record for per-kind rules (v1 `drc`
   has one `rule.clearance`). Agent 4's readers and the golden harness need all three before M3 compares ported
   boards. Agent 6 specifies v2 with Agent 4 before U-V3; until then embodic writes v1. Revision 2026-10-08 (U-D4):
   v2 also needs `Circuit.interconnect_roles` (§5), so Agent 4's readers can check P_ic.
5. Closed 2026-10-08 (U-D5, D-032a). Agent 2's `inferred` answer that the parallel path count must divide t
   (`equation_specification.md` l.213-214) is the rule, and `plan_spiral_winding` on main e1536b8 applies it (§4).
6. Code on main c7fff3a that contradicts a contract line (revision 2026-10-08, U-D4). Each row names the owner and
   how to reproduce it. The text above states the decision, not the code.

| ID | Owner | Contract line | Main c7fff3a | Reproduce | Closes in |
|---|---|---|---|---|---|
| DEF-U-D4-01 | Agent 3 | §2.2: `first_coil_angle_rad` accepts any finite value (D-031c) | `generate_spiral` refuses a negative angle: `_out_of_range` lists it among the non-negative inputs (`generators/spiral/generate.py` l.98-103) | `default_design()` of `tests/unit/generators/default_example.py` with `first_coil_angle_rad=-0.1` gives `Unbuildable` `UNBUILDABLE_SPIRAL_INPUT_OUT_OF_RANGE` at `/winding/coil/first_coil_angle_rad`; 7.0 builds (`verified (run)`, 2026-10-08) | U-M2d-3 (in its brief) |
| DEF-U-D4-02 | Agent 3 | §2.2 and UT-GEN-03: copper count = phases x layers per phase for `stack_mode` `single` (D-031e) | `validate_design` checks only `one_board_per_phase` (`model/validate.py` l.170) | `serpentine_design()` of `tests/unit/model/designs.py` with `layers_per_phase=1` (3 phases, 6 copper layers): `single` gives no issue, `one_board_per_phase` gives `INVALID_SERPENTINE_COPPER_COUNT` (`verified (run)`, 2026-10-08) | no unit yet: needs `src/embodic/model/validate.py` and `tests/unit/boundary/test_bv_design.py`, which U-M2a-fix named as the blocker; neither is in U-M2d-3's scope |
| DEF-U-D4-03 | Agent 3 | §2.1 `ScrewPattern.hole_diameter_mm` (D-031a); §5 `TurnLimit.closing` (D-031b) | neither field exists (`model/outline.py`, `geometry/details.py`) | read the two dataclasses | U-M2d-3 (in its brief) |
| DEF-U-D4-04 | Agent 3 | §8 EQ-20 drive helpers take `connection`, the envelope `phases` and `connection`; §3 loss-sum fields; §5 `Circuit.interconnect_roles` (D-031f) | `drive.py` fixes `PHASES = 3`; `analyse` gives `torque_speed=None` for other phase counts and adds no interconnect resistance (`physics/analyse.py` l.334, l.432) | `checks/physics_signatures.py` lists the three drive names as PENDING | U-M2e-4 (§8 of work_breakdown.md) |
| DEF-U-D6-01 | Agent 3 | §9.1 question 1: an origin that is not packaged gives `measured` or `user`, never `default` | `project_provenance` passes `None` to `derive_provenance` for such an origin, which reads it as a blank origin (`io/project.py` l.99-111) | parse `resources/examples/spiral_12c10p_d08.embodic.json`, build a `ProjectFile` of its design with `ExampleRef(example_id="spiral_12c10p_d08", example_sha256="sha256:other")`, call `project_provenance`: 56 `user`, 30 `default` (`verified (run)`, main a336531) | no unit yet: `src/embodic/io/project.py` is in no running brief |
| DEF-U-D6-02 | Agent 3 | §9.1 question 2: a key the schema refuses gives `INVALID_PROJECT_FILE` | `parse_project` ignores unknown keys (`io/project.py` l.244-283) | add `"polez": 99` to `design.rotor`, or `"extra_top": 1` at the top level, of the same file and call `parse_project`: `ProjectFile`, no issue (`verified (run)`, main a336531) | no unit yet: same file |

Revision 2026-10-08 (U-D6). The rows above name main c7fff3a; the two U-D6 rows name main a336531. DEF-U-D4-04 is
closed on main a336531 except for `motor_constant_n_m_per_sqrt_w` (DEF-M2e4-01, §3) and the spiral generator's
`Circuit.interconnect_roles` (`inferred` from the U-M2e-4 report and the passing signature check). U-M2-fix3 owns
both.
7. M3 items closed (revision 2026-10-09, U-D8; main 8a297a0, `verified` by reading unless the row says otherwise;
   the XD-WAVE row corrected by U-D9 on main 3acb044).

| Item | Closed by | State on main 8a297a0 |
|---|---|---|
| §2.2: the INVALID code of the wave copper-count rule is U-M3-fix's to name | D-035e, D-037d | `INVALID_WAVE_COPPER_COUNT` in `validate_design` (§2.2, revision U-D8) |
| §5: the wave case of `INTERCONNECT_EXTERNAL` is `unresolved`; `BoardStack` has no `issues` field | D-035a, D-036d | `RANGE_WAVE_INTERCONNECT_EXTERNAL` through `BoardStack.issues` (§6, revision U-D8) |
| §7: rule 2b text and the rule 5 end-point reading | D-036a, D-037a | `_taps` and `_junctions` in `drc/items.py` (§7, revision U-D8) |
| §2.2: U-M3-fix records the via-length difference as an XD-WAVE entry | D-035e, D-036e, D-038b | No entry is owed (D-038b corrects D-035e). `test_gr22_phase_resistance_differs_from_xcoil_only_by_the_via_barrel_length` (`test_gr22_results.py` l.124) removes the barrel length at function level and compares. `wave.toml` on main 3acb044 holds XD-WAVE-001 (overlap star, `verified`) and XD-WAVE-002 (overlap delta, `inferred`; §2.2) |
| DEF-U-D4-02 (point 6): `validate_design` checks only `one_board_per_phase` | D-032c (U-M2-fix, work_breakdown.md §8) | both stack modes checked (`model/validate.py` l.196-200) |

8. Recorded limitation (revision 2026-10-09, U-D8, D-037b): "per-phase stack: interconnect between boards not
   modelled; Ke/P_ic status `unresolved`". The serpentine example built one board per phase gives three boards, each
   DRC-clean, and the `RANGE_SERPENTINE_INTERCONNECT_BOARDS` warning (§6). Its Ke is finite (0.0707654 V·s/rad,
   Fable's acceptance probe), and D-037b states that this is not a claim of accuracy. The status here is the decision's
   label. Whether the `Traceable` status fields of that outcome say `unresolved` is not checked by U-D8 (`unresolved`).

9. Open points after the M4-3 and M4-4 units (revision 2026-10-09, U-D10; main fd190c1, `verified` by reading unless the
   row says otherwise).

| Item | State on main fd190c1 | Owner |
|---|---|---|
| A glyph the report font lacks: exception or refusal (§9.3) | `MissingGlyphError` propagates out of `write_report_pdf`. `ExportRefused.reason` has no value for it. U-M4f asked whether to add `"missing_glyph"` and could not, because `io/exporters.py` was outside its scope | Fable decides; the change is an `io` unit's |
| Greek symbols in result titles (§3, D-040) | Closed by U-M4c-4 (b), U-D11: 25 symbols in `QUANTITY_SYMBOLS` on main 9776555, the four Greek ones among them. D-040 is still not in `decision_log.md`, which ends at D-039 (`verified` by reading, U-D11) | Fable records D-040 |
| Lower DRC bounds for clearance, pad and end width in the wave and serpentine guards (§6) | D-030 gives a bound for the trace width only. A tiny positive clearance, pad or end width reaches `UNBUILDABLE_WAVE_END_TURN_DEGENERATE`. A serpentine of 400 traces took up to 16 s (U-M3-fix3 report, measured there) | Agent 2 and Agent 6 for the bound; the 16 s goes to the Phase 5 performance list (Fable's note on the report) |
| Spiral generator still has its own input guard (§6) | Closed by U-M4c-4 (d), U-D11: `_out_of_range` calls `unusable_sizes` (`generators/spiral/generate.py` l.112) | none |
| Label anchors are fixed at fit zoom (§5) | Closed by U-S4e ruling h and U-M4e-1, U-D11: forced labels per phase and sign, `place_in_view`, the copper fallback and `name_unlabelled` (§5). The U-M4c-3 question is answered | none |
| `CoilMark.label` keeps the ASCII hyphen while `LabelAnchor.text` uses U+2212 (§5) | no code reads `CoilMark.label`. Whether to delete the field or switch it to `MINUS` is not decided (`unresolved`) | Agent 3, with the next `geometry` unit |

10. Open points after U-M4c-4 and U-M4e-1 (revision 2026-10-09, U-D11; main 9776555, `verified` by reading unless the
    row says otherwise).

| Item | State on main 9776555 | Owner |
|---|---|---|
| D-040 and D-041a are not in `decision_log.md` | The log ends at D-039 (`docs/decision_log.md`, read). D-040 a and b are in the store's `decisions.tsv` (2026-10-09T11:40Z). D-040 c and D-041a are in the briefs of U-M4e-1b and U-D11 only. This file cites D-041a as "D-041a (Fable, 2026-10-09)" | Fable records them |
| LG-01 admits U+00A0 only after U-M4e-1b (§3) | `MODULE_SYMBOLS` has one entry, `embodic.results.labels`. `UNIT_SPACE` is `chr(0x00A0)` | U-M4e-1b |
| Example titles (§9.1) | The schema pattern `"Example"` and the five old titles are still on main. Two strict xfails record the Xcoil title (test_plan.md §5.6) | U-M4e-1b |
| REQ-F-38 says examples are labelled "Example" wherever they appear, and its acceptance says "Gallery titles contain "Example"" (`requirements.md` l.89) | D-041a and ruling g remove the word from titles. The chip `example` and the gallery intro text ("Loaded values are marked "example"", `dlg-examples.intro`, `strings/design.py` l.187) still carry the label. Whether REQ-F-38 and its acceptance change, or the gallery needs a visible tag, is not decided here (`unresolved`). U-D11 left `requirements.md` unchanged | Fable with Agent 1 |
| Colophon position (§9.3) | The line sits after the Inputs table, on page 3 of 4 for D08, and the drawing page follows. Ruling f says "ends the PDF" (`unresolved`) | U-M4e-1b (c), Agent 1 |
| `CoilMark.label` keeps the ASCII hyphen (§5) | No code under `src/embodic` reads it (`verified` by grep). Delete or switch to `MINUS` is not decided | Agent 3, with the next `geometry` unit |
| A missing glyph raises out of `write_report_pdf` (§9.3) | Unchanged: only `pdf_writer.py` names `MissingGlyphError` (`verified` by grep) | Fable decides |
| EV-106 names the variable file | Agent 5 updates it (U-S5b, in flight). The files and hashes are in `resources/fonts/FONTS.md` | U-S5b |

11. Open points after U-M4e-1b and U-M4e-2 (revision 2026-10-11, U-D12; main 4fda98d, `verified` by reading unless the
    row says otherwise).

| Item | State on main 4fda98d | Owner |
|---|---|---|
| D-040 and D-041a are not in `decision_log.md` (point 10) | Closed. The log holds D-040 (l.46) and D-041 (l.47). It holds no D-042 (`verified` by grep). The store calls D-042 a draft: the Tests dialog is M5 work (`reports/U-M4e-2.md`, `briefs/U-S4g.md`). Its content is `unresolved` until Fable records it | Fable records D-042 |
| LG-01 admits U+00A0 only after U-M4e-1b (§3) | Closed. `MODULE_SYMBOLS` has the entry `embodic.results.formatting`, and `UNIT_SPACE` is the literal | none |
| Example titles (§9.1) | Closed. The schema pattern is gone, the five titles are set, and the two UX-AC-03 marks are removed (`test_plan.md` §5.6). D-041b moved the five design hashes (§9.1) | none |
| REQ-F-38 (point 10) | The acceptance text is amended (`requirements.md`, D-041a). The statement still says examples are labelled "Example" wherever they appear, while the window title and the export stem now show the display title without the word (D-041b). Whether the statement names the chip and the gallery heading instead is `unresolved` | Fable with Agent 1 |
| Colophon position (§9.3) | Closed. The line is the last line of the last page (ruling f). design_spec.md §4 (l.198) and `m4_review_2.md` l.149 still say "after the last table" | Agent 1 amends design_spec.md or leaves it (`unresolved`) |
| EV-106 names the variable file | Closed by U-S5b (merge a1e08e3; commit e89cb2f "EV-106 and the font record describe the static Inter files") | none |
| `CoilMark.label` keeps the ASCII hyphen; a missing glyph raises out of `write_report_pdf` | Not rechecked on main 4fda98d. The U-D11 rows stand | Agent 3; Fable decides |
| DEF-M4e2-01 to DEF-M4e2-03: the EQ chip and assumption tag are 22 px tall, check box click rectangles 20 px, scroll bars 12 px wide | Four strict xfails (`test_plan.md` §5.6). Agent 1 rules fix or exception per defect in U-S4g, including whether WCAG's spacing exception applies to scroll bars | Agent 1 (U-S4g), Agent 3 fixes (U-M4e-3) |
| `OutcomeReady.summary` (`ui/viewmodels/outcome.py` l.104) and the test that reads it (`tests/unit/ui/shell/test_outcome_viewmodel.py` l.108) | Kept by U-M4e-2, because that test was outside its scope. Fable's note on the report sends the deletion to U-M4e-3 | Agent 3 (U-M4e-3) |
| The layer bar showed "L1 L2 L1 L2" once after several rows shared one window | `unresolved`. U-M4e-2 did not reproduce it in a fresh window (its report). U-V4 tries to reproduce it | Agent 4 (U-V4) |
| S33, the Tests dialog (`tests-table`) | Not in this build, so row S33 of the checklist is not captured and the verify skill lists it as `not tested`. M5 carries the dialog (D-042 draft): it needs the `passed_tests` evidence packaged into `resources/evidence` and a test bundle in the wheel (D-034, `briefs/U-S4g.md`) | M5 (`work_breakdown.md` §8) |
| Text clipping at 150 and 200 percent (UI-09), keyboard input in the native file dialog (AX-02) | `not tested` by a machine (`test_plan.md` §5.3.1) | Agent 1 reviews the grabs |

12. Open points after U-D13 (revision 2026-10-12; main 7b9b4c9, `verified` by reading unless the row says otherwise).

| Item | State | Owner |
|---|---|---|
| S33, the Tests dialog (point 11) | The contract is §14. D-042a (`docs/decision_log.md` l.48) asks for "a test bundle in the wheel". The wheel ships no pytest tests (`package_layout.md` §5.2), so the bundle is the self-test catalogue of §14, which needs only the package. Fable records that reading or rules otherwise | Fable |
| The entry point that opens `dlg-tests` | screens.md §13 says no toolstrip button, menu item or shortcut opens the dialog until it ships. Agent 1 names the entry (action ID, icon stem, label, shortcut) and, if wanted, a label that shows `Registry.evidence_build_id`, in screens.md §13 and §14a, before U-M5d starts. `checks/screens_coverage.py` fails on an objectName that no table defines | Agent 1, through Fable |
| The CI matrix | `.github/workflows/ci.yml` runs Python 3.11 and 3.12 only and installs `.[dev]`, so no Qt test runs in CI. REQ-N-05 names 3.11 to 3.13 (PK-01) | U-M5b |
| The `eqt` markers | U-M5o placed them, and D-046c fixes the rule: a test carries a registry ID only when it checks that ID's acceptance criterion as written. On main 76f054b `grep -rn "pytest.mark.eqt" tests --include=*.py` finds 48 lines (`verified`). How many of the 63 registry IDs they carry is `unresolved`: the U-M5o report counts 42, and a count by this unit that reads the arguments of every `pytest.mark.eqt(...)` call finds 37. The two are not reconciled, and U-M5f recounts. Revision 2026-10-13 (U-D15, claude-sonnet-5-5; main 5e74acc): U-M5f recounted. 54 of the 63 registry IDs are carried by tests (U-M5f report). This unit's static count agrees (`verified` by reading: `equation_registry.json` holds 63 IDs, and 54 appear as whole-string constants in `tests/`, which covers the markers and the parametrised `EQT_GR_BY_FN` tables). The 9 others are `EQT-14-GR`, `EQT-14-O2`, `EQT-16-GR`, `EQT-17-GR`, `EQT-19-GR`, `EQT-22-GR`, `EQT-27-GR`, `EQT-28-GR` and `EQT-29-GR`, the nine rows marked Phase 3 in `docs/phase2/engineering/eqt_map_review.md` l.229-241. The count reads test files and not the markers pytest collects, so the `--req-report` count is `not tested` here. Carried is not passed. The rule of §3.1 admits an ID only when every test that carries it passed, and the release evidence (`passed_tests.v1.json`) lists the passed ones. Which of the 54 pass is `unresolved` until a release run has written that file for a build. EQT-05-O2 and EQT-06-O2 cannot pass while OR-07 is the strict xfail F-OR07 (`test_plan.md` §5.6) | U-M5f recounted (done); the passed list comes from the release run |
| embodic's own licence | No `LICENSE` file. `package_layout.md` §5.2 reserves the place and says "pending the user's choice". This contract chooses nothing | the user |

13. Open points after U-D14 (revision 2026-10-13, claude-sonnet-5-5; main 6243163, and main 76f054b where a row says so
    or where D-046 changed the file; `verified` by reading unless the row says otherwise).

| Item | State | Owner |
|---|---|---|
| S33, the Tests dialog, and the "test bundle" of D-042a (points 11 and 12) | Closed by D-045d. The bundle is the self-test catalogue of §14, and a self-test result never moves a result badge | none |
| The entry point that opens `dlg-tests` (point 12) | Closed by D-045c. `act-tests` is the last row of `TOOLSTRIP` (§11), and `docs/phase2/design/screens.md` l.424 names the same entry | none |
| DEF-M4e2-01 to DEF-M4e2-03 (point 11) | Closed. No `xfail` mark is left in `tests/ui/qt_e2e/test_ax04_target_size.py`, and the file gives `4 passed` (`verified` by running it, 41 s). `test_plan.md` §5.6 lists the one strict xfail that remains | none |
| `embodic-cli export` and a failed DRC | Stated in §12 (D-045e): the PDF report and the README are written, the drawings and the bundle are refused with exit 2 unless `--allow-drc-errors`. The GUI dialog follows D-045e and D-046a (§11): the PDF report, the README and the JSON project file are written without `dlg-export-confirm`, and the SVG, the three DXF files and the bundle ask. Two dialog tests cover it and pass (`verified` by running them on main 76f054b). The CLI has no project format | none |
| The rule 5 end-point reading (point 7, row "§7") | No GR-19 pair depends on it since U-V1c and the GR-19 DRC reading of D-046f (§7, revision 2026-10-13). No UT-DRC-04 case covers it on main 76f054b. U-M5f adds cases 5e and 5f | U-M5f |
| A leftover evidence file (D-045f, §3.1) | Closed by D-046e. The test side implements it (`tests/conftest.py` session copy, `build_wheel` copy) and the product has no switch. Two tests pin it and pass on main 76f054b. `test_plan.md` §5.7 names them and gives them no ID | Fable decides whether they get an ID |
| The PyInstaller folder (stretch, D-015; `package_layout.md` §5.1 and §5.2) | A Linux smoke of the spec only (D-046h). Build exit 0, 444 files, the Qt libraries are separate files, no `.py` file, `licenses/` and `source/embodic-0.0.1.tar.gz` present. Open: the sdist is 18.8 MB (a trimmed sdist is a question for Fable and the user); PyInstaller warns that `libxcb-cursor.so.0` is not resolved on Linux; PK-05 on Windows is `not tested`; the written offer for the Qt and PySide6 source and embodic's `LICENSE` are user decisions; Qt's third-party notices are `unresolved` | Fable, the user |
| `SelfTestWorker` location (§14) | Closed by D-046g. The class is in `ui/workers.py`, `create_shell` composes it and passes `selftests=` to `MainWindow` (main 76f054b, `verified` by reading). The `getattr` in `selftest/runner.py` is gone | none |

14. Open points after U-D17 (revision 2026-10-17, claude-sonnet-5-5; D-051; main 0547f20, `verified` by reading unless the
    row says otherwise). Each row is a point that D-051 or the brief of U-D17 does not settle.

| Item | State | Owner |
|---|---|---|
| Where `None` sorts in the violation order (§7) | D-051f names the key (kind, layer, objects) and not the place of a `None` layer. §7 proposes `None` first | Fable decides |
| Which 1000 violations the report keeps (§7) | The key of D-051f replaces the margin key, so the report keeps the first 1000 in canonical order, not the 1000 with the least margin. The DRC table reads the list in order (`ui/viewmodels/results.py` l.352), and so does the export dialog (`ui/viewmodels/export.py` l.149). Whether a least-margin view is wanted is `unresolved` | Fable decides, then Agent 1 and Agent 3 |
| Names with "balanced" that D-051b does not list (§4) | `Feasibility.balanced` (`src/embodic/winding/feasibility.py` l.19), `balanced_coil_counts` (l.49) and `is_balanced` (`src/embodic/winding/star_of_slots.py` l.61) keep their names. D-051b renames two issue codes, the copy and the text of option M4. The option M4 text is in no file of this folder (`verified` by grep for "Q = 2p" and "2p rule") | Fable decides |
| The milestone argument of `--fail-untested-through` (§3.2) | D-051e names the flag. `M5` is the proposal of v3_contract_rulings.md §2 point 1 | Fable confirms |
| The manual-record index and its format (§3.2) | Proposed: `docs/phase3/verification/manual_records.json`, five keys per record. D-051e asks for the input and fixes neither | Fable confirms; Agent 4 owns the file |
| A manual record of an earlier build (§3.2) | The script counts a `passed` record whatever its `embodic_version`. If Fable wants a 0.0.2 walkthrough for REQ-N-07, the 0.0.2 gate cannot pass before the Windows campaign (v3_contract_rulings.md, open question 2) | Fable decides |
| Two record inputs for Agent 4 (§3.2) | `req_audit.py` holds its own `RECORDS` dict (l.58-62), and the index above lists records for TR-01. Whether the audit reads the index is not settled | Agent 4 |
| The six rows that the flag fails (§3.2) | On the 0.0.1 release report they are REQ-N-07, REQ-N-10, REQ-T-10, REQ-T-11, REQ-L-03 and REQ-L-05 (v3_contract_rulings.md §2, reproduced there). LG-03 to LG-06 have no row in `test_plan.md` §5.4 yet, and D-051 does not ask for them. The 0.0.2 gate cannot pass until each row has a passing test or a `passed` manual record | Fable decides who writes the rows |
| REQ-N-10 acceptance (`requirements.md`) | It says "matrix generator lists 0 untested live REQs", and TR-01 checks only must rows (`tools/trace_matrix.py` l.95). v3_contract_rulings.md §2 point 6 proposes "0 untested live must REQs". D-051 does not rule on it, so the row is unchanged | Fable decides |
| PK-04 array definition and scale (`test_plan.md` §5.7) | D-051f says an array compares at 1e-9 relative to "its own largest magnitude". §5.7 reads that as the largest absolute value over both arrays, and reads an array as a JSON list of numbers. Another reading of either word changes which element pairs fail | Fable confirms |
| `pk04_compare.py` (Agent 4's file) | It compares each float pair against the larger magnitude of the pair (docstring l.6) and compares hash strings exactly (l.28-29). PK-04 as `test_plan.md` §5.7 now states it needs the array rule and the excluded pointers | Agent 4, through Fable |

## 14. `embodic.selftest`: self-tests for an installed build (revision 2026-10-12, U-D13; D-042a, screens.md §13)

The installed wheel carries no pytest tests and no pytest (`package_layout.md` §5.2). The self-test is a small runner in
pure Python over a fixed catalogue of checks that need only the package and its resources. Each check computes one value
through the public functions and compares it with an expected value and tolerance copied from a named pytest test.
The Tests dialog and `embodic-cli selftest` both run it.

```python
# embodic.selftest (U-M5d). Layer: below embodic.ui and embodic.cli, above embodic.api (package_layout.md §3, C1).

class SelfTestGroup(StrEnum):
    CLOSED_FORM = "closed form"  # CF cases of oracle_cases.json and the spiral worked examples
    EXAMPLES = "examples"  # the five packaged examples compute, with their pinned design hashes
    DRC = "drc"
    EXPORT = "export"


class SelfTestVerdict(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not run"  # cancelled before the check started


SelfTestValue: TypeAlias = "float | int | bool | str | tuple[str, ...]"


@dataclass(frozen=True, slots=True, kw_only=True)
class SelfTestCheck:
    id: str  # "ST-CF01"; unique; the Tests table and the CLI show it
    group: SelfTestGroup
    title: str  # English, one line
    source_test: str  # pytest node ID whose assertion gives expected, rel_tol and abs_tol
    expected: SelfTestValue
    unit: str  # display unit of a float value ("T", "ohm", "mm"), "" otherwise
    measure: Callable[[Path], SelfTestValue]  # receives an empty scratch folder; writes nowhere else
    rel_tol: float = 0.0
    abs_tol: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class SelfTestResult:
    check_id: str
    group: SelfTestGroup
    title: str
    verdict: SelfTestVerdict
    observed: SelfTestValue | None  # None when not run, or when measure raised
    expected: SelfTestValue
    duration_s: float
    message: str  # "" when passed; else expected, observed and tolerance, or the exception type and text


@dataclass(frozen=True, slots=True, kw_only=True)
class SelfTestReport:
    results: tuple[SelfTestResult, ...]  # one per check, in catalogue order
    versions: VersionInfo
    evidence_build_id: str | None  # load_registry().evidence_build_id (§3.1), shown, never changed by a run
    cancelled: bool

    @property
    def ok(self) -> bool:
        """Every result passed: no failure and nothing not run."""


SELFTESTS: tuple[SelfTestCheck, ...] = ()  # the 45 checks of the table below, in that order


def agrees(observed: SelfTestValue, expected: SelfTestValue, *, rel_tol: float, abs_tol: float) -> bool:
    """A float or int against a float expectation: |observed - expected| <= max(abs_tol, rel_tol * |expected|).
    Anything else: equality."""


def run_selftests(checks: Sequence[SelfTestCheck] = SELFTESTS, *, cancel: CancelToken | None = None,
                  on_result: Callable[[SelfTestResult], None] | None = None) -> SelfTestReport:
    """Run the checks in order, each with its own temporary folder that is deleted afterwards. A check that raises is
    FAILED with the exception type and message, and the run goes on. After cancel, every check not yet started is
    NOT_RUN. on_result is called once per result, from the running thread. Imports no Qt and no pytest."""


def selftest_to_json(report: SelfTestReport) -> dict[str, JsonValue]:
    """Versions, evidence_build_id, cancelled and one object per result; floats in the encoding of §9.2."""
```

The catalogue. Each expected value below was computed by `checks/selftest_probe.py` on main 7b9b4c9 through the same
public functions, and all 45 checks pass (`verified` by running it twice, U-D13: "45 checks, 0 failed"; 9.5 s and 18.0 s of
wall time on this 2-CPU container, which other units share, so the time is no budget).
The catalogue holds the values as literals, because the wheel carries neither `docs/` nor `tests/`.

| IDs | Group | Measures | Expected, tolerance | Source test |
|---|---|---|---|---|
| ST-CF01 | closed form | `field_harmonic` B_z1 of the CF-01 rotor at r = 1e5 mm, z = 0 | 1.162077823241657 T, rel. 1e-9 | `tests/unit/physics/test_kernels.py::test_cf01_field_fundamental_equals_the_1d_magnetic_circuit` |
| ST-CF04-R20, ST-CF04-R60, ST-CF04-ARC | closed form | `path_resistance_ohm` of a 1000 mm line and a 90 degree arc of r 30 mm, 0.5 mm by 34.8 µm, at 20 and 60 °C | 0.9908620689655171, 1.1466255862068966 and 0.04669327494874277 ohm, rel. 1e-12 | `test_kernels.py::test_cf04_track_resistance_at_20_and_60_degc` |
| ST-CF04-VIA | closed form | `via_resistance_ohm(0.3, 25.0, 1.6, rho20, 1)` | 0.001277202792190775 ohm, rel. 1e-12 | `test_kernels.py::test_cf04_and_ut_phy_11_via_barrel_resistance` |
| ST-CF06-KE, ST-CF06-KT-STAR, ST-CF06-KT-DELTA | closed form | `phase_constants(0.01, STAR or DELTA, 3, 10)` | 0.017320508075688773 V·s/rad, 0.021213203435596423 and 0.01224744871391589 N·m/A, rel. 1e-12 | `test_kernels.py::test_cf06_star_and_delta_constants` |
| ST-CF06-RLL-STAR, ST-CF06-RLL-DELTA | closed form | `line_resistance_ohm([1.0, 1.1, 1.2], STAR or DELTA)` | 2.2 and 0.731313131 ohm, rel. 1e-9 | `tests/unit/physics/test_closed_forms_m2e2.py::test_eq23_cf06_star_and_delta` |
| ST-CF09-<Q>-<poles>-PATTERN, 9 checks | closed form | the pattern string of `assign_phases(Q, poles)` for each CF-09 row: (12, 10), (12, 14), (12, 16), (18, 16), (24, 14), (24, 22), (24, 26), (9, 8), (15, 16) | the row's `pattern`, exact | `tests/unit/winding/test_star_of_slots.py::test_cf09_patterns_and_balance` |
| ST-CF09-<Q>-<poles>-KD1, 9 checks | closed form | `distribution_factor(assign_phases(Q, poles), 1, Q)` for the same rows | the row's `kd1`, abs. 1e-9 | `tests/unit/winding/test_winding_factors.py::test_ut_wnd_05_cf09_distribution_factor` |
| ST-CF11-LENGTH, ST-CF11-TURNS | closed form | the computed `spiral_12c16p_default` board: `SpiralDetail.track_length_per_coil_layer_mm["X"]`, `turns_achieved` | 415.4808 mm abs. 5e-5; 10 exact | `tests/unit/generators/test_spiral_generate.py::test_default_track_length_matches_cf11` |
| ST-CF10-LENGTH | closed form | the same for `spiral_12c10p_d08` | 160.2750 mm, abs. 5e-5 | `test_spiral_generate.py::test_d08_builds_three_turns_with_the_half_closing` |
| ST-EX-<example_id>-HASH, 5 checks | examples | `compute(...).design_hash` of each packaged example | the pinned `EXAMPLE_HASHES` value, exact | `tests/unit/embodic_io/project/test_examples.py::test_ut_io_08_the_packaged_design_hashes_are_pinned` |
| ST-EX-<example_id>-COMPUTES, 5 checks | examples | the outcome has an analysis and no ERROR issue | True | `test_examples.py::test_ut_io_08_example_validates_and_computes_drc_clean` (three spirals), `tests/unit/generators/serpentine/test_serpentine_example.py::test_the_example_validates_and_computes_drc_clean`, `tests/unit/ui/results/test_rail_cards.py::test_drc_card_of_the_wave_example_counts_186_failures` |
| ST-DRC-DEFAULT-CLEAN, ST-DRC-DEFAULT-TRACE | drc | the DRC report of `spiral_12c16p_default`: `violation_count`, the `trace_trace` `least_clearance_mm` (was `measured_min_mm` until revision 2026-10-17, U-D17, D-051a; the check reads it at `selftest/catalogue.py` l.181) | 0 exact; 0.2 mm abs. 1e-6 | `test_spiral_generate.py::test_default_example_passes_drc` |
| ST-IO-ROUNDTRIP | export | save, load and save `spiral_12c16p_default` with `ui_state={"zoom": 1.5}` in the scratch folder, both saves with `saved_utc="2026-10-08T12:00:00Z"` (revision 2026-10-13, U-D15; §9.1) | the two files are byte-identical | `tests/unit/embodic_io/project/test_project.py::test_ut_io_01_save_load_save_is_byte_identical` |
| ST-EXP-BUNDLE | export | `write_bundle` of SVG, DXF complete, DXF outline, PDF report and project JSON to `motor.zip` with `allow_drc_errors=True` | members `README.txt`, `motor.dxf`, `motor.embodic.json`, `motor.svg`, `motor_outline.dxf`, `motor_report.pdf` | `tests/unit/embodic_io/exporters/test_report_readme_bundle.py::test_ut_exp_05_bundle_holds_selected_files_and_readme` |

Revision 2026-10-13 (U-D15, claude-sonnet-5-5; main 5e74acc). `ST-IO-ROUNDTRIP` passes one `saved_utc` to both saves
(`selftest/catalogue.py` l.43, l.191 and l.194; §9.1), as U-M5h fixed it, and `checks/selftest_probe.py` now does the
same (`ROUNDTRIP_SAVED_UTC`). The probe on main 5e74acc printed "45 checks, 0 failed, 8.7 s for all checks" and
exited 0 (`verified` by running it once at low priority beside Fable's release gate; the time is no budget). One run
cannot show that the flake is gone, because the old pair failed only when its two clock reads fell in different
seconds (U-M5h report). The fix removes the second read (`project.py` l.181), and absence of the flake over repeated
runs is `not tested`.

CF-02, CF-03, CF-05, CF-07 and CF-08 have no product test that asserts their expected value on main 7b9b4c9 (`verified`
by grep for the case IDs and the values in `tests/unit`). They join the catalogue when U-M5o adds those tests, with the
new test as the source. The catalogue grows only from a named passing test, never from a value typed here.

Drift. UT-SLF-02 keeps the literals true. It compares the CF-09 rows with `docs/phase2/engineering/oracle_cases.json`,
the hashes with `EXAMPLE_HASHES` of `test_examples.py` (l.34), and checks that every `source_test` names a function that
exists in its file. A unit that changes a source value edits the catalogue in the same commit.

The Tests dialog (screens.md §13). `embodic.ui.viewmodels.selftest.SelfTestViewModel` is Qt-free: `rows`
(`Observable[tuple[SelfTestResult, ...]]`), `summary` (`Observable[str]`), `running` (`Observable[bool]`), `run()` and
`stop()`. `embodic.ui.workers.SelfTestWorker` (see the note below) runs `run_selftests` on the `QThreadPool` with a fresh `CancelToken`
and posts each `on_result` to the GUI thread. `embodic.ui.views.tests_dialog.TestsDialog` (`dlg-tests`) shows
`btn-tests-run`, the `tests-table` columns of screens.md §13 (test ID, group, result icon with the verdict word,
duration, message) and `tests-summary` ("45 tests: 45 passed, 0 failed"; after a cancel, "45 tests: 12 passed, 0
failed, 33 not run"). Esc and **Stop** call `stop()`. The window stays responsive while checks run. Strings live in a new
`embodic/ui/strings/selftest.py`. Test: UI-35.

Where `SelfTestWorker` lives (revision 2026-10-13, U-D14, claude-sonnet-5-5; D-046g; `src/embodic/ui/workers.py`,
`ui/app.py`, `ui/views/main_window.py`, `ui/views/tests_dialog.py` and `selftest/runner.py` on main 76f054b, `verified` by
reading and by grep). The class is in `src/embodic/ui/workers.py` l.87, next to `ComputeWorker` (`package_layout.md` §1).
`create_shell` composes it (`ui/app.py` l.122 builds `SelfTestWorker()`, l.133 passes it to `MainWindow` as `selftests=`
and l.138 makes the window its Qt parent). D-046g keeps contract C3.
`MainWindow.__init__` takes it as `selftests: WaitingRunner` (`main_window.py` l.139 and l.143) and hands it to the dialog
(l.344). `WaitingRunner` is a `Protocol` in `tests_dialog.py` l.34 (the dialog waits on the runner when it closes), so
the view imports no worker. A grep for `SelfTestWorker` in `src` finds `workers.py`, `app.py` and a docstring in
`tests_dialog.py`. The `getattr` on `load_registry()` that U-M5d left in `selftest/runner.py` is gone:
`run_selftests` reads `evidence_build_id=load_registry().evidence_build_id` (l.103), and `grep -n getattr` on the file
finds nothing. Test: `tests/ui/qt_results/test_tests_dialog.py` builds `workers.SelfTestWorker(window)` (l.56) and gives
`6 passed` (`verified` by running it, 24 s). This note replaces the earlier target marking.

Why a self-test result never moves a badge. The badge rule is a pure function of the registry and the design (D-007,
`derive_badge`), and the registry's test state comes from the build's evidence (§3.1). A self-test run does not feed it,
for three reasons. First, the catalogue is 45 checks, and the registry links 63 test IDs, most of them golden and oracle
tests that need Xcoil fixtures and literature data the wheel does not carry, so a passing run cannot stand for the
registry's tests. Second, a badge that changed when a user pressed Run would differ between two machines, and before and
after the click, for the same file. That breaks determinism (REQ-N-04) and the D-007 rule that only calculation trust
sets a badge. Third, a self-test answers a different question, whether this installation reproduces the build's numbers.
A failure there is a defect in the installation (a broken NumPy, a damaged resource), which the dialog and the CLI
report as a failure, not a lower evidence status. Tests: UT-SLF-01 to UT-SLF-03, UT-CLI-03, UI-35, PK-11.
