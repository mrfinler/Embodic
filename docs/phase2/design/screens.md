Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5; section 14a row `ts-section-board` and rulings i, j: claude-sonnet-5-5 (U-S4f)

# embodic screens v2.3 (Phase 2, PySide6)

Date 2026-10-08, revised 2026-10-12 (U-S4h): `compare-scroll` declared in section 10. Revised 2026-10-09 (U-S4f): `ts-section-board` declared in 14a; rulings i and j of
`m4_review_2.md` section 5 applied to sections 4 and 5 (screw buttons, last table column). Revised 2026-10-09 (U-S4e): rulings a, c, d and g of `m4_review_2.md` applied to sections 4, 5, 6,
7, 14a and 16 (`pair-list`, the screw fields, the card grid, the DRC columns, 26 declared names, example titles).
Revised 2026-10-09 (U-S4d): rulings of `m4_review.md` applied to the conventions and sections 1, 2,
3, 4, 5, 6.1 (new) and 14a (new). Read with `design_spec.md` (tokens, toolstrip, hooks, keyboard map). v2 applied rows R1 to R14 of
`docs/phase2/architecture/screen_model_reconciliation.md` to sections 1 to 5, 6 and 7. v2.1 (U-S4c) follows the model
after U-M2a-fix and U-M2a-fix2 and decisions D-024, D-025d and D-031:

- Section 16 is regenerated. `/phases` is optional for every topology (DEF-1).
- Section 4 shows `param-stack-mode` and `param-board-gap` (D-016 fields exist now) and specifies how the layer pairs
  follow the copper count (D-024). Section 4.1 proposes the board picker for one board per phase (`assumption`).
- Section 5 adds `param-screw-hole-diameter` (D-031a).
- Section 15 drops the requests that U-M2a-fix closed.

Sections 8 to 14 are unchanged from v1.

Conventions for every table:

- The binding key is the model pointer of `src/embodic/model/fields.py` `FIELDS`. `FieldSpec.widget_id` is the only
  join between a widget and a field (interfaces.md §2.3); the keys here are for readers and equal the model pointer.
  A field of one union member is written as the pointer and the member in words, for example
  `/outline/board/radius_mm` (circle); the model keys it `radius_mm#circle`. List items use `*`.
- "view model" in the binding column marks a helper widget. It has no `FieldSpec` and writes the named pointers
  through the session view-model as one undoable edit.
- Each objectName is defined in exactly one table row. Other mentions are references.
- Numeric fields are `QLineEdit` with a parser in the view model, or `QDoubleSpinBox` with `NoButtons`. Up and Down
  step by `FieldSpec.step`, Shift steps ten times, Enter and Tab commit, Esc reverts, the wheel does nothing without
  focus. Segments and combo boxes move with the arrow keys; Space selects. Units sit in a `QLabel[class="unit"]` named
  `<id>-unit` and are part of the accessible description. Angles show in degrees; the model stores radians (`*_rad`).
- Start values (D-014, D-019). "required" fields start empty with a placeholder that shows only the unit, never a
  number, and a "Required" hint. "default" fields start at `FieldSpec.neutral_value` with a `default` chip. screens.md
  does not copy the values; the field table is the source.
- Every input has a provenance chip `<id>-prov` (`QLabel[class="prov-chip"]`): `user`, `example`, `default` or
  `measured`. "property" fields (`FieldKind.PROPERTY`) offer "Mark as measured" in the context menu, which asks for the
  source (D-007). Design fields do not offer it (`INVALID_MEASURED_DESIGN_FIELD`).
- Messages (R14). The UI shows the catalogue text of the issue code (`embodic.errors.MESSAGES`) with `{limit}` and
  `{unit}` filled. The generic limit codes apply to every numeric field and are not repeated in the tables:
  `INVALID_NON_POSITIVE`, `INVALID_NEGATIVE`, `INVALID_NOT_INTEGER`, `INVALID_CHOICE`, `RANGE_BELOW_SUPPORTED`,
  `RANGE_ABOVE_SUPPORTED`. A quoted text without a code is a proposal to the unit that owns the rule.
- Validation runs on commit. The message goes in `<id>-error` (`QLabel[class="field-error"]`), the field gets
  `invalid=true`, and the Checks list gets the same text. An INFO issue shows as a hint under the field, not an error.
  A WARNING issue shows in `<id>-error` with `state=warn`, the `check-warn` icon and the word "Warning" before the
  text. The field does not get `invalid=true`, and compute still runs.
- Layout of a field row (U-S4d g2). The label sits above the control for every field, choice fields included. The
  row reserves the unit column and the chip column even when they are empty, so control edges align and nothing moves
  when a chip appears or goes. Chips are 20 px tall and centred on the control.
- Choice fields with two or three options may be a `QComboBox` or a segment (U-M4c builds combo boxes). Either one
  takes the field's objectName.
- Hidden vs disabled. A field that does not apply to the active topology or option is hidden with its label, unit and
  chip (`setVisible(False)` on the row). A field blocked by a sibling option in the same group is disabled and its hint
  names the option ("Not used with straight ends").

## 1. New design

Opens at start and on File > New (D-014). Modal `QDialog#dlg-new-design`, 560 x 400 px minimum (assumption). The
dialog names the design and fixes its topology. Every value is entered in the inspector afterwards, so each widget has
one home.

| objectName | Qt widget | Binding key | Rule |
|---|---|---|---|
| `param-design-name` | QLineEdit "Design name"; initial focus | `/name` | `INVALID_EMPTY_TEXT` |
| `param-topology` | Button group of three QToolButtons (exclusive, `ToolButtonTextUnderIcon`, 24 px `topology-*` icon, `border-control` boundary when unchecked): `param-topology-spiral`, `param-topology-serpentine`, `param-topology-wave` | view model: `DesignDraft.topology` | Proposal: "Choose a topology." |
| `example-picker` | QComboBox, first item "No example (blank)" | none (loads an example) | Enter loads after confirmation if the inspector holds user values |
| `btn-create-design` | QPushButton[class="primary"] "Create design" | command | Enabled when the name is valid and a topology is chosen (R11); Enter |
| `btn-cancel-new` | QPushButton "Cancel" | command | Esc |

State rules:

- **Create design** opens the draft in the inspector. A blank draft has its required fields empty and its optional
  fields at their default; an example fills every field with `example` chips and the window title reads
  "<name> (from example <example name>)". Editing a field turns its chip to `user`.
- The topology fixes the constant `/winding/kind` (interfaces.md §2.3). It is not a field and has no provenance chip.
- Nothing computes until `parse_draft` returns `DesignParameters` (REQ-F-36, UI-24).

### 1.1 Required-field bar (inspector header)

| objectName | Qt widget | Binding key | Rule |
|---|---|---|---|
| `new-required-count` | QLabel[class="hint"] | view model: number of controls in the missing list | "38 required fields left" (example count). Hidden once the draft parses. |
| `btn-first-missing` | QPushButton "Go to first missing field" | command | Opens the tab and focuses the widget of the first missing pointer (`FieldSpec.widget_id`). For `/stackup/layers` it focuses the first empty stack-up generator input. |

## 2. Coil (inspector tab `tab-coil`)

| objectName | Label and Qt widget | Binding key | Topology | Start | Messages |
|---|---|---|---|---|---|
| `param-r-inner` | "Inner radius", mm | `/winding/coil/r_inner_mm` (spiral), `/winding/r_inner_mm` | spiral, serpentine, wave | required | `INVALID_ORDER`, `INVALID_RADIAL_SPAN` |
| `param-r-outer` | "Outer radius", mm | `/winding/coil/r_outer_mm` (spiral), `/winding/r_outer_mm` | spiral, serpentine, wave | required | `INVALID_ORDER`, `INVALID_RADIAL_SPAN` |
| `param-turns` | "Turns per coil" (spiral), "Turns per layer" (serpentine), "Slots per phase belt" (wave) | `/winding/coil/turns` (spiral), `/winding/turns` | spiral, serpentine, wave | spiral: default, empty means "Maximum"; others: required | `RANGE_TOO_MANY_TRACES` |
| `param-trace-width` | "Trace width", mm | `/winding/coil/trace_width_mm` (spiral), `/winding/trace_width_mm` | spiral, serpentine, wave | required | DRC `DRC_MIN_WIDTH` |
| `param-clearance` | "Trace spacing", mm | `/winding/coil/clearance_mm` (spiral), `/winding/clearance_mm` | spiral, serpentine, wave | required | DRC `DRC_TRACE_TRACE` |
| `param-corner-radius` | "Corner radius" (spiral), "Fillet radius" (serpentine, wave), mm | `/winding/coil/corner_radius_mm` (spiral), `/winding/fillet_radius_mm` | spiral, serpentine, wave | default | none |
| `param-first-coil-angle` | "First coil angle" (spiral), "Start angle" (serpentine), degrees | `/winding/coil/first_coil_angle_rad` (spiral), `/winding/start_angle_rad` | spiral, serpentine | default | none |
| `param-poles` | "Poles" | `/rotor/poles` | spiral, serpentine, wave | required | `INVALID_POLE_COUNT_ODD` |
| `param-coil-count` | "Coils"; balance hint in `hint-combination` | `/winding/coil/coil_count` | spiral | required | Proposal: "Coil count must be a multiple of 3." |
| `param-side-style` | 2 x QToolButton segment: Radial, Parallel | `/winding/coil/side_style` | spiral | default | none |
| `param-end-style` | 3 x QToolButton segment: Arc, Straight, Stadium | `/winding/coil/end_style` | spiral | default | none |
| `param-coil-gap` | "Coil gap", mm | `/winding/coil/coil_gap_mm` | spiral | required | `RANGE_COIL_GAP_BELOW_CLEARANCE` (INFO, hint with the trace spacing as Suggestion; R12) |
| `param-x-inward-sense` | 2 x QToolButton segment: CW, CCW | `/winding/coil/x_inward_sense` | spiral | default | none |
| `param-strands` | "Strands" | `/winding/strands` | serpentine | default | `RANGE_TOO_MANY_TRACES` |
| `param-active-style` | QComboBox "Active conductors": Radial, Parallel | `/winding/side_style` | serpentine | default | none |
| `param-fillet-max` | QCheckBox "Maximum fillet (semicircular U-turn)" | `/winding/fillet_max` | serpentine | default | none |
| `param-wave-style` | QComboBox "Wave style": Involute, Jog, Chord, Overlap | `/winding/wave_style` | wave | default | none |
| `param-bus-width` | "Bus width", mm | `/winding/bus_width_mm` | wave | required | none |

State rules: `param-corner-radius` is disabled with the hint "Not used with straight ends" when `param-end-style` is
Straight; it is hidden for serpentine when `param-fillet-max` is checked. A coil gap below the trace spacing is valid:
the generator uses the trace spacing, and the INFO hint says so (R12). The coil figure ("Coil detail" or "Ring") sits
on the canvas, not in the tab.

## 3. Phases (`tab-phases`)

| objectName | Label and Qt widget | Binding key | Topology | Start | Messages |
|---|---|---|---|---|---|
| `param-phase-count` | "Phases", segment 1, 2, 3 | `/phases` | serpentine, wave | default (R9) | none |
| `param-connection` | "Connection", mirrors the toolstrip Connection buttons: Star, Delta, Open | `/connection/topology` | spiral, serpentine, wave | default | none |
| `param-phase-assign-mode` | "Assignment", segment Auto, Manual | `/winding/assignment` | spiral | default | none |
| `param-phase-sequence` | "Phase sequence", segment A-B-C, A-C-B; hint "Swapping B and C reverses rotation." | `/winding/phase_sequence` | spiral | default | none |
| `phase-pattern-string` | QLabel[class="unit"], read-only, selectable, caption "Coil pattern", hint "Upper case +, lower case −." | result `winding.assignment` | spiral | none | none |
| `phase-balance-status` | QLabel[class="check-state"] | result `winding.balance` | spiral | none | "Not balanced: choose 12, 18 or 24 coils" (example values from the engine) |
| `phase-table` | QTableView: coil, phase, polarity; F2 edits in manual mode | `/winding/assignment/*/coil_index`, `/winding/assignment/*/phase`, `/winding/assignment/*/polarity` | spiral | none | Proposal: "Each phase needs the same number of coils." |
| `param-terminal-location` | "Terminals": segment Outer, Inner (serpentine); QLabel "Outer rim", read-only (spiral, wave) | `/winding/terminal_side` | serpentine | default | none |
| `param-ring-width` | "Interconnect ring width", mm | `/connection/ring_width_mm` | spiral, serpentine, wave | required | none |
| `param-terminal-pad` | "Terminal pad diameter", mm | `/connection/terminal_pad_mm` | spiral, serpentine, wave | required | `INVALID_TERMINAL_PAD_RING` |
| `param-terminal-drill` | "Terminal drill", mm; hint "0 mm makes a surface-mount pad." | `/connection/terminal_drill_mm` | spiral, serpentine, wave | required | `INVALID_TERMINAL_PAD_RING` |

State rules:

- Spiral hides `param-phase-count`: spiral coils are 3-phase (`INVALID_SPIRAL_PHASES`).
- Auto writes `null` to `/winding/assignment` (star of slots) and fills `phase-table` from result
  `winding.assignment`, read-only. Manual writes the list, starting from the current auto pattern, and makes the phase
  and polarity columns editable. The columns stay visible in auto mode because the user needs the assignment.
- The open connection shows six terminal rows; star shows U, V, W, N; delta U, V, W.

## 4. Layers (`tab-layers`)

| objectName | Label and Qt widget | Binding key | Topology | Start | Messages |
|---|---|---|---|---|---|
| `param-layer-count` | "Copper layers", QComboBox 2, 4, 6, 8 | view model: stack-up generator writes `/stackup/layers` | spiral, serpentine | empty | none |
| `param-wave-layers` | "Copper layers", QComboBox 2, "4 (2 in parallel)", "6 (3 in parallel)", "8 (4 in parallel)" | view model: stack-up generator writes `/stackup/layers` | wave | empty | none |
| `param-pair-connection` | "Layer pairs", segment Series, Parallel; parallel hint "Circulating current if layer EMFs differ (EQ-07)." | `/winding/pair_connection` | serpentine | default | `INVALID_SERIES_PAIRS_EXCEED_POLE_PAIRS` |
| `param-rotation-mode` | "Pair rotation", segment None, Alternate, Custom | view model: writes `/winding/layers/pairs/*/rotation_rad` | spiral | none | none |
| `param-pair-rotation` | "Rotation of the selected pair", degrees | `/winding/layers/pairs/*/rotation_rad` | spiral | default | none |
| `param-layers-per-phase` | "Layers per phase" | `/winding/layers_per_phase` | serpentine | required | `INVALID_LAYERS_PER_PHASE` |
| `param-stack-mode` | "Boards", segment "Single board", "One board per phase" | `/winding/stack_mode` | serpentine | default | `INVALID_SERPENTINE_COPPER_COUNT` |
| `param-layer-order` | "Layer order", QComboBox Grouped, Interleaved | `/winding/layer_order` | serpentine | default | none |
| `param-board-gap` | "Gap between boards", mm | `/winding/board_gap_mm` | serpentine | default | none |
| `param-via-drill` | "Via drill", mm | `/vias/drill_mm` | spiral, serpentine, wave | required | `INVALID_VIA_RING` |
| `param-via-pad` | "Via pad", mm | `/vias/pad_mm` | spiral, serpentine, wave | required | `INVALID_VIA_RING` |
| `param-vias-per-transition` | "Vias per transition" | `/vias/vias_per_transition` | spiral, serpentine, wave | default | none |
| `param-via-plating` | "Via plating", µm | `/vias/plating_um` | spiral, serpentine, wave | required, property | none |
| `layer-list` | QTableView of the stack-up: Layer, Kind, Thickness (µm). Kind reads "Copper" or "Dielectric" in full, never elided. Columns size to their content and the last one takes the remaining width, so the header has no empty cell; no sideways scroll at 300 px (U-S4e ruling c, U-S4f ruling j). Layer visibility stays with the canvas toggles (U-S4d g1). Delete removes the selected layer row | `/stackup/layers`, `/stackup/layers/*/kind`, `/stackup/layers/*/name`, `/stackup/layers/*/thickness_mm`, `/stackup/layers/*/material` | spiral, serpentine, wave | required | `INVALID_STACKUP_NO_COPPER`, `INVALID_LAYER_NAME_DUPLICATE`, `RANGE_SPIRAL_COPPER_COUNT_ODD` (WARNING), `INVALID_SERPENTINE_COPPER_COUNT` |
| `pair-list` | QTableView of the layer pairs under `layer-list`, caption "Layer pairs": Pair (the number, "1" is index 0), Layers ("L1, L2"), Rotation (°) with the provenance chip in the cell. One row per pair the copper count makes; a deleted pair keeps its row dimmed with "No coil" in the Rotation cell. The row tooltip names the vias ("Pair 1 joins L1 and L2 through vias."); the row context menu sets the series group. The chip is `prov-chip` with its `provenance` property, as in the form rows. The last column takes the remaining width (U-S4f ruling j). Delete removes the selected pair (U-S4e ruling c) | `/winding/layers/pairs`, `/winding/layers/pairs/*/index`, `/winding/layers/pairs/*/layer_in`, `/winding/layers/pairs/*/layer_out`, `/winding/layers/pairs/*/phases`, `/winding/layers/series_groups` | spiral | required | `INVALID_PAIR_LAYER_UNKNOWN`, `INVALID_PAIR_LAYER_SAME`, `INVALID_PAIR_INDEX_DUPLICATE`, `INVALID_SERIES_GROUPS` |
| `layer-pairs-notice` | QFrame[class="notice"] under `pair-list`: one sentence and an **Undo** button | derived: what `derive_layer_pairs` changed in the last edit | spiral | hidden | none |

State rules:

- Stack-up generator (R3). `param-layer-count` or `param-wave-layers`, `param-copper-weight` and
  `param-board-thickness` are its inputs. Once all three hold a value, the view-model calls
  `generate_even_stackup(copper_count, copper_thickness_mm, board_thickness_mm)`, with the copper weight converted by
  `copper_oz_to_mm`, and writes `/stackup/layers` as one undoable edit. `layer-list` edits the result. Proposal: after
  a manual `layer-list` edit, a generator input change asks "Replace the edited stack-up?" before it writes.
- Serpentine copper count (UT-GEN-03, D-031e). On a single board the copper count equals phases times layers per
  phase. With one board per phase the stack-up describes one board, so the count equals layers per phase
  (`INVALID_SERPENTINE_COPPER_COUNT`). `param-layer-count` offers only the value that applies. Today the model checks
  the count only for one board per phase (`validate.py` `_serpentine_layers`, `verified` by reading).
- `pair-list` shows for spiral only. Its Pair column shows the pair index plus one ("1" is index 0). The row context
  menu "Series group" edits `/winding/layers/series_groups`. Pairs are their own rows because a pair spans two copper
  layers: in one table with the stack-up, each pair showed twice and Delete on a layer row removed a pair, not the
  layer (U-S4e ruling c).
- Rotation mode (R4) reads the current pair rotations. None writes 0 to every pair. Alternate writes pi/Q to every
  second pair, Q being the coil count (option M3, UT-GEO-11). Custom shows `param-pair-rotation`, which edits the pair
  selected in `pair-list`; the other modes hide it.
- The field check `INVALID_VIA_RING` compares the via pad with the drill. The DRC check `DRC_ANNULAR_RING` compares
  pad minus drill with twice `param-min-ring` and reports in the DRC table. A design can pass the first and fail the
  second (R13).
- Rotation of layer groups shows as solid and dashed footprints on the canvas.

Layer pairs follow the copper count (spiral, D-024, D-025d):

- Every edit that changes the number of copper layers calls `derive_layer_pairs(draft)` and writes its result in the
  same undoable edit. These edits are a stack-up generator write, an added or removed copper row in `layer-list`, and
  a loaded project file. Pair k joins copper layers 2k and 2k + 1 in stack order. A blank spiral design therefore shows
  its pairs as soon as the three stack-up generator inputs hold values.
- A new pair starts with its rotation at the documented default and a `default` chip in the rotation cell, in its own
  series group.
- A pair that still exists after the edit keeps every value the user gave it (rotation, phases, group) and its
  `user` chips.
- When the count falls, the pairs past the new count go, with their group entries.
- `layer-pairs-notice` names what the edit changed, for example "Layer pairs: 3. Pair 3 added with the default
  rotation." or "Layer pairs: 1. Pair 2 removed: the stack-up has 2 copper layers." **Undo** reverts the whole edit,
  the copper count included (UX-AC-12). The notice hides at the next edit.
- Delete on a selected `pair-list` row removes that pair, not its copper layers. The row stays, dimmed, with "No coil"
  in the Rotation cell, and `layer-pairs-notice` reads "Pair 2 removed. It returns with default values when the copper layer count
  changes." The count is the structure, so a later count change derives the pair again (Fable ruling on U-M2a-fix2).
  Today this fails for a pair that is not the last one: `derive_layer_pairs` keys the surviving pairs by list
  position, so the pairs after the deleted one shift and the next derivation repeats an index
  (`checks/pair_delete_probe.py` exits 1, `verified` by running on 2026-10-08; DEF-S4c-01).
- An odd copper count leaves the last copper layer without a pair. `pair-list` has no row for it, its `layer-list` row
  tooltip reads "No coil: this copper layer has no partner.", and `layer-list-error` shows the WARNING text of `RANGE_SPIRAL_COPPER_COUNT_ODD`: "Spiral coils use copper layers in
  pairs; with an odd count one copper layer carries no coil." Compute still runs. `param-layer-count` offers only even
  counts, so an odd count comes from a `layer-list` edit or a loaded file.
- After a count change, rotation mode reads the rotations again. A new pair at the default rotation can turn Alternate
  into Custom; choosing Alternate again applies it to every pair.

Stack mode (serpentine, D-016):

- "One board per phase" builds one board per phase, each with the stack-up in `layer-list` (interfaces.md §2.2).
  The board picker of section 4.1 appears.
- `param-board-gap` is disabled with the hint "Used only with one board per phase." while the mode is "Single board".
  `param-layer-order` is disabled with the hint "Not used with one board per phase: each board holds one phase." while
  the mode is "One board per phase" (Xcoil `ui.js` l.236 and `engine.js` l.681, cited in interfaces.md §2.2).
- With one board per phase no board carries a star or delta interconnect (interfaces.md §5). Proposal for a hint under
  `param-connection`: "One board per phase: connect the phases between the boards."

### 4.1 Board picker for one board per phase (`assumption` until U-M4c tests it)

A serpentine design with `/winding/stack_mode` = `one_board_per_phase` produces a `BoardStack` of one `Layout` per
board, board k holding phase k (interfaces.md §5). The user needs to see the whole stack and each board. One control
does both.

| objectName | Qt widget | Binding key | Topology | Start | Messages |
|---|---|---|---|---|---|
| `board-picker` | QComboBox in the toolstrip View section, caption "Board": "All boards", "Board A", "Board B", "Board C" (one item per phase) | control: canvas view state, not a design value | serpentine | "All boards" | none |

- Place. The View section of the toolstrip, beside the canvas toggles, because the choice changes what the canvas
  draws and nothing in the design. It is not in the inspector: the inspector holds design values with provenance
  chips, and a view choice there would look like one.
- Visibility. Shown only while the design has more than one board. It is hidden for spiral, wave and single-board
  serpentine designs, because it never applies there (P3). The items follow `/phases` before the first compute.
- Default "All boards". The canvas draws every board's copper over one outline, each phase in its colour, line style
  and coil-eye hatch (design_spec.md section 3.3). The picture matches the single-board view of the same winding, so
  switching the stack mode does not change what the user sees first. "Board A" draws board A only.
- Names. Boards carry the letter of the phase they hold, as the exports do (`_board` plus the phase letter,
  interfaces.md §5). The UI does not show Xcoil's `B1:` prefix, because "B1" reads as phase B.
- Never colour alone (D-011). Each item names its letter. A phase-colour swatch beside an item repeats the letter and
  turns grey in greyscale mode.
- Keyboard. Page Up and Page Down on the focused canvas select the previous or next item. Layer solo (`[` and `]`)
  works inside the selected board, or on every board for "All boards".
- DRC. `drc-summary` counts the whole stack and then each board: "DRC: 2 failures, 0 warnings. Board A pass, Board B
  2 failures, Board C pass." `drc-table` gains a "Board" column and lists every board whatever the picker shows, so a
  failure is never hidden by a view choice. **Locate** sets the picker to the row's board, then zooms.
- Results. The picker does not change results. Physics reads every board of the stack (`analyse`, interfaces.md §5),
  and phase results are per phase as before. `st-counts` reads "3 boards, 2 copper layers each" (example values).
- Export. The picker does not change exports. SVG and DXF write one file per board, and `export-result` lists each
  file (interfaces.md §5).

## 5. Board and rotor (`tab-board`)

One `QGroupBox` per group, in this order. Every row applies to all three topologies.

| objectName | Group | Label and Qt widget | Binding key | Start | Messages |
|---|---|---|---|---|---|
| `param-outline-shape` | Outline | "Outline", segment Circle, Polygon | `/outline/board/shape` | required | none |
| `param-outline-sides` | Outline | "Sides", QComboBox 4 to 16 | `/outline/board/sides` (polygon) | required | none |
| `param-outline-size` | Outline | "Board radius" (circle), "Across flats" (polygon), mm | `/outline/board/radius_mm` (circle), `/outline/board/across_flats_mm` (polygon) | required | DRC `DRC_COPPER_EDGE` |
| `param-outline-rotation` | Outline | "Rotation", degrees | `/outline/board/rotation_rad` (polygon) | default | none |
| `param-corner-radius-board` | Outline | "Corner radius", mm | `/outline/board/corner_radius_mm` (polygon) | default | none |
| `param-bore` | Outline | "Centre bore": None, Circle, Polygon | `/outline/bore`, `/outline/bore/shape` | required | none |
| `param-bore-radius` | Outline | "Bore radius", mm | `/outline/bore/radius_mm` (circle) | required | none |
| `param-bore-sides` | Outline | "Bore sides" | `/outline/bore/sides` (polygon) | required | none |
| `param-bore-across-flats` | Outline | "Bore across flats", mm | `/outline/bore/across_flats_mm` (polygon) | required | none |
| `param-bore-corner-radius` | Outline | "Bore corner radius", mm | `/outline/bore/corner_radius_mm` (polygon) | default | none |
| `param-bore-rotation` | Outline | "Bore rotation", degrees | `/outline/bore/rotation_rad` (polygon) | default | none |
| `screw-table` | Fasteners | QTableView: Size, Count, Pitch radius (mm); one row per screw pattern. Columns size to their content and the last one takes the remaining width; no sideways scroll at 300 px (U-S4e ruling c, U-S4f ruling j) | `/outline/screws`, `/outline/screws/*/size`, `/outline/screws/*/count`, `/outline/screws/*/pitch_radius_mm` | default (no patterns) | DRC `DRC_COPPER_HOLE` |
| `param-screw-fit` | Fasteners | "Fit of the selected pattern", QComboBox | `/outline/screws/*/fit` | default | none |
| `param-screw-hole-diameter` | Fasteners | "Hole diameter of the selected pattern", mm | `/outline/screws/*/hole_diameter_mm` | required when a pattern exists, no default (D-031a) | none |
| `param-screw-angle-offset` | Fasteners | "Angle offset of the selected pattern", degrees | `/outline/screws/*/angle_offset_rad` | default | none |
| `btn-screw-add` | Fasteners | QPushButton "Add pattern", secondary boundary like `btn-drc-locate` (U-S4f ruling i) | command | none | none |
| `btn-screw-remove` | Fasteners | QPushButton "Remove pattern", secondary boundary (U-S4f ruling i) | command | none | none |
| `param-copper-weight` | Stack-up and manufacturing | "Copper weight", oz | view model: stack-up generator writes `/stackup/layers` | empty | none |
| `param-board-thickness` | Stack-up and manufacturing | "Board thickness", mm | view model: stack-up generator writes `/stackup/layers` | empty | none |
| `param-min-trace` | Stack-up and manufacturing | "Minimum trace width", mm | `/drc_rules/min_trace_width_mm` | required | DRC `DRC_MIN_WIDTH` |
| `param-min-space` | Stack-up and manufacturing | "Trace clearance (trace to trace, pad to trace)", mm | `/drc_rules/trace_clearance_mm` | required | DRC `DRC_TRACE_TRACE`, `DRC_PAD_TRACE` |
| `param-min-via-space` | Stack-up and manufacturing | "Via clearance (to traces, vias and pads; pad to pad)", mm | `/drc_rules/via_clearance_mm` | required | DRC `DRC_TRACE_VIA`, `DRC_VIA_VIA`, `DRC_PAD_PAD` |
| `param-min-edge` | Stack-up and manufacturing | "Copper to board edge", mm | `/drc_rules/edge_clearance_mm` | required | DRC `DRC_COPPER_EDGE` |
| `param-min-hole-space` | Stack-up and manufacturing | "Copper to screw hole", mm | `/drc_rules/hole_clearance_mm` | required | DRC `DRC_COPPER_HOLE` |
| `param-min-via` | Stack-up and manufacturing | "Minimum drill", mm | `/drc_rules/min_drill_mm` | required | DRC `DRC_MIN_DRILL` |
| `param-min-ring` | Stack-up and manufacturing | "Minimum annular ring", mm | `/drc_rules/min_annular_ring_mm` | required | DRC `DRC_ANNULAR_RING` |
| `param-rotor-kind` | Rotor and magnets | "Rotor", QComboBox Double, Single with yoke, Single open | `/rotor/rotor_type` | required | none |
| `param-magnet-shape` | Rotor and magnets | "Magnet shape", segment Arc, Block | `/rotor/magnet/kind` | required | none |
| `param-magnet-arc-ratio` | Rotor and magnets | "Pole arc ratio" | `/rotor/magnet/pole_arc_ratio` (arc) | required | none |
| `param-magnet-r-inner` | Rotor and magnets | "Magnet inner radius", mm | `/rotor/magnet/r_inner_mm` (arc) | required | `INVALID_MAGNET_ORDER` |
| `param-magnet-r-outer` | Rotor and magnets | "Magnet outer radius", mm | `/rotor/magnet/r_outer_mm` (arc) | required | `INVALID_MAGNET_ORDER` |
| `param-magnet-width` | Rotor and magnets | "Magnet width", mm | `/rotor/magnet/width_mm` (block) | required | none |
| `param-magnet-length` | Rotor and magnets | "Magnet length", mm | `/rotor/magnet/length_mm` (block) | required | none |
| `param-magnet-r-center` | Rotor and magnets | "Magnet centre radius", mm | `/rotor/magnet/r_center_mm` (block) | required | none |
| `param-magnet-thickness` | Rotor and magnets | "Magnet thickness", mm | `/rotor/magnet/thickness_mm` (arc, block) | required | none |
| `param-magnet-br` | Rotor and magnets | "Remanence B_r", T | `/rotor/remanence_t` | required, property | none |
| `param-magnet-mur` | Rotor and magnets | "Recoil permeability mu_r" | `/rotor/recoil_permeability` | required, property | none |
| `param-air-gap` | Rotor and magnets | "Air gap per side", mm | `/rotor/air_gap_mm` | required | none |
| `param-back-iron` | Rotor and magnets | "Back-iron thickness", mm | `/rotor/back_iron_thickness_mm` | required | none |
| `param-speed` | Operating point | "Speed", rpm | `/operating/speed_rpm` | required | none |
| `param-current` | Operating point | "Line current (rms)", A | `/operating/line_current_rms_a` | required | Proposal for the missing hint: "Enter the line current." |
| `param-copper-temp` | Operating point | "Winding temperature", °C | `/operating/winding_temperature_degc` | required | none |
| `param-dc-link` | Drive | "DC-link voltage", V | `/operating/dc_link_v` | default, empty means no torque-speed estimate | none |
| `param-modulation` | Drive | "Modulation", QComboBox SVPWM, SPWM, Six-step | `/operating/modulation` | default | none |
| `param-h-conv` | Cooling | "Convection coefficient h", W/(m²·K) | `/operating/convection_h_w_m2k` | required, property | none |
| `param-ambient` | Cooling | "Ambient temperature", °C | `/operating/ambient_temperature_degc` | required | none |

State rules:

- `param-outline-sides`, `param-outline-rotation` and `param-corner-radius-board` are hidden for a circular outline.
  The bore fields follow the bore segment the same way; None writes `null` to `/outline/bore`.
- The arc rows of the magnet show for Arc, the block rows for Block.
- `screw-table` starts with no rows. Each new row starts with its required cells empty. An example ported from the
  two Xcoil rings has two rows (R6).
- `param-screw-fit`, `param-screw-hole-diameter` and `param-screw-angle-offset` edit the pattern selected in
  `screw-table`, as `param-pair-rotation` does for pairs. They are fields and not table cells because each needs the
  unit label, the provenance chip, the hint and the error label, and a cell carries none of them; six cells also
  needed 315 px where the 300 px inspector leaves about 240 (U-S4e ruling c, measured with `tools/design/layout_probe.py`).
  They hide while the table has no rows. A new pattern starts with the hole diameter empty and "Required". **Go to first missing field** selects
  the row and focuses the field. The UI fills no ISO 273 value; such values ship only as labelled example values once
  Agent 5 cites the source (D-031a, U-S3b).
- Rotor and magnets shows the pole count of `param-poles` read-only.
- B_r, mu_r and h start empty like every required field (R10, D-014): a default B_r would be a physical assumption
  inside Ke. Of the optional groups only Drive is in the form.
- The clearance split per check kind is an `assumption` (interfaces.md §7). Xcoil uses one clearance for every pair.
- Fields without a widget keep their neutral value: `/winding/coil/inner_turn_mode`, the end-turn widths,
  `/winding/coil/lead_style`, `/winding/coil/terminal_offset_mm`, `/winding/coil/min_side_length_mm`,
  `/winding/corner_style`, `/winding/parallel_paths`, `/connection/draw_interconnect`, `/connection/neutral_pad`,
  `/rotor/magnet_offset_rad`, `/analysis/*` and the material overrides (registry constants apply, D-023).

## 6. Results (`tab-results` in `results-tabs`; key rows in `results-rail`)

Result card `QFrame[class="result-card"]` named `res-card-<key>`:

| Part | objectName | Widget | Rule |
|---|---|---|---|
| Title and symbol | `res-<key>-title` | QLabel | "Phase resistance R_ph" |
| Value | `res-<key>-value` | QLabel[class="result-value"] | 3 significant figures; integers for counts; minus sign U+2212 |
| Unit | `res-<key>-unit` | QLabel[class="result-unit"] | Always present; "–" with accessible text "dimensionless" |
| Trust badge | `res-<key>-badge` | QLabel[class="badge"][status=...] with `status-*` icon | Exactly one; from data, never hard-coded (D-007). `unresolved` reads "estimate". |
| EQ-ID | `res-<key>-eq` | QLabel[class="eq-chip"], link | Opens the equation register at that entry; or tag `input`, `derived`, `count` |
| Assumptions | `res-<key>-asm` | QToolButton[class="asm-tag"] | "n assumptions"; toggles the list; "0 assumptions" shown plainly |
| How was this computed | `res-<key>-how` | collapsible QFrame toggled by a QToolButton | Equation, inputs (value, unit, provenance), assumptions, limitations, validation state, sources, **Copy trace** |

State rules: until `parse_draft` returns `DesignParameters` the tab shows one sentence "Results appear when every
required field is valid." and the button `btn-results-first-missing` "Go to first missing field", which runs the
command of `btn-first-missing` (R11). While computing, values dim to 60 % after 300 ms and the status bar
reads "Updating"; previous values stay until new ones arrive. Invalid input keeps the last valid results dimmed with
`stale=true` and the stamp "Last valid results". Card grid (U-S4e ruling d): columns = the largest n with
n x 280 px + (n − 1) x 8 px within the viewport width after the vertical scroll bar; cards share the width equally and
reflow on resize. The grid never scrolls sideways and never places a card past the viewport edge. Keys from Phase 1 stay: `r-phase`, `ke`, `kt`, `ls`, `dt`, `j`.

### 6.1 Status cards of the results rail (U-S4d e)

Until `tab-drc` exists the rail heads with two status cards, each with a `check-*` glyph and a word, never colour alone.

| objectName | Qt widget | Binding key | Rule |
|---|---|---|---|
| `rail-inputs` | QFrame[class="result-card"] with QLabel[class="check-state"] | session issues | "Inputs": `check-pass` "No input issues" or `check-fail` "3 input issues" (example count) |
| `rail-drc` | QFrame[class="result-card"] with QLabel[class="check-state"] | `drc.passed`, `drc.violation_count` | "DRC": `check-pass` "Passed", `check-fail` "186 failures" (example count) or "Not run". A link opens `tab-drc` once it exists. |

The card that read "Design: Problems found" goes: it merged two states, and beside "No issues." it read as a
contradiction. `issues-list` takes the title "Input issues" and the empty text "No input issues.".

## 7. DRC (`tab-drc`)

| objectName | Qt widget | Binding key | Behaviour |
|---|---|---|---|
| `drc-summary` | QLabel[class="check-state"] with `check-pass` or `check-fail` icon | `drc.passed`, `drc.violation_count` | "DRC: 2 failures, 1 warning" |
| `drc-table` | QTableView: severity glyph (24 px, no word), Message, Measured (mm), Required (mm), Layer | `drc.violations` | Rows with `state=fail` get a 4 px fail border. Enter or double-click = Locate. The rule code and the severity word go to the row tooltip and the accessible description ("Error. DRC_TRACE_VIA. A trace is closer to a via than the via clearance rule. Measured 0.199965 mm, required 0.2 mm, layer L1."); Ctrl+C copies the row with the code. No row-number column. |
| `btn-drc-locate` | QPushButton | selected row | Zooms the canvas to `at_mm`, dims copper to 35 %, draws the ink marker |
| `drc-rule-note` | QLabel[class="hint"] | static | "A violation is reported when clearance < rule − 1e-6 mm (D-006)." |

The message column shows the catalogue text of the violation's `DRC_*` code (R14). Column budget (U-S4e ruling d):
the glyph column is 24 px; Measured, Required and Layer size to their content, numbers right-aligned in JetBrains Mono
with the unit in the header only; Message stretches, holds at least 200 px and wraps to two lines. The fixed columns
need about 250 px, so the table never scrolls sideways in a centre pane of 480 px or more, which every window from
960 px wide gives. The glyph shape (`check-fail`, `check-warn`) and the fail border carry the severity without colour. The ANNULAR_RING row is where the
relation pad minus drill of at least twice the minimum annular ring appears (R13).

## 8. Back-EMF (`tab-back-emf`) and 9. Torque-speed (`tab-torque-speed`)

| objectName | Qt widget | Rule |
|---|---|---|
| `chart-backemf` | QChartView or custom QWidget | One unit per y axis (V). Phases A, B, C in phase colours with solid, dashed, dotted lines, legend and direct end labels. Crosshair tooltip by mouse and by Left and Right keys when focused. |
| `chart-backemf-table` | QTableView in a collapsible "Data table" | Same samples as the chart |
| `chart-backemf-meta` | badge + EQ chip + assumptions tag | As a result card |
| `chart-torque-speed`, `chart-power-speed` | two charts sharing the x axis (rpm) | Never two y units on one chart; small multiples instead |
| `chart-*-table`, `chart-*-meta` | as above | as above |

Empty state: "Charts appear after the first compute." Charts never show efficiency without its status (P1).

## 10. Compare (`tab-compare`)

| objectName | Qt widget | Rule |
|---|---|---|
| `compare-scroll` | QScrollArea | The one vertical scroll of the Compare page: table at the height of its rows, then the charts; no sideways bar (U-M4e-3c, recorded U-S4h) |
| `btn-set-reference` | QPushButton | "Set current design as reference"; replaces the stored reference after confirmation |
| `compare-table` | QTableView: quantity, reference, current, delta | Delta as sign plus glyph (▲, ▼); words "better" or "worse" only when Engineering defines the preferred direction. No red or green. Integers without decimals. |
| `compare-chart` | small multiples, one unit each | Reference dashed grey, current solid ink |

Empty state: "No reference stored. Set the current design as the reference to compare later versions."

## 11. Export (`dlg-export`)

Opened by any toolstrip Export button with that format preselected.

| objectName | Qt widget | Rule |
|---|---|---|
| `export-format-svg`, `export-format-dxf-complete`, `export-format-dxf-outline`, `export-format-dxf-screws`, `export-format-json`, `export-format-pdf`, `export-format-readme` | QCheckBox each | All checked for "All files"; README needs at least one other format |
| `export-folder` | QLineEdit + QToolButton "Browse" | "Choose a folder you can write to." |
| `export-checklist` | QListWidget with check icons | Engine stamp, DRC result, stale state, number of assumptions |
| `btn-export-run` | QPushButton[class="primary"] | With DRC failures opens `dlg-export-confirm` listing them; focus on Cancel |
| `export-result` | QLabel + "Open folder" button | Lists written files; never claims a file it did not write |

Every exported file carries the embodic version, engine version and parameter hash. Paths shown use the real folder;
documentation uses `%USERPROFILE%` placeholders.

## 12. Guide and reference (`dlg-guide`)

Non-modal window with a left `QTreeView#guide-toc` (Guide topics, Equation register, Status labels, Keyboard shortcuts)
and a `QTextBrowser#guide-body`. Equation entries show EQ-ID, formula, sources with page, status. F1 opens it at the topic
of the focused field (field `whatsThis` holds the topic id).

## 13. Tests (`dlg-tests`)

Milestone M5 (U-S4g ruling l, D-042 draft). The dialog needs the bundled test set and the packaged `passed_tests`
evidence in the wheel (D-034). Entry point (D-045c, U-M5d): the toolstrip View tab, group "Help", `act-tests`
"Self-tests" with icon `check-pass`, command `show_tests`.

| objectName | Qt widget | Rule |
|---|---|---|
| `btn-tests-run` | QPushButton[class="primary"] | Runs the bundled self-tests in a worker; Esc or **Stop** cancels |
| `tests-table` | QTableView: test id, group, result icon, duration, message | Pass, fail, not run; no colour without the icon and word |
| `tests-summary` | QLabel | "131 tests: 129 passed, 2 failed" (example numbers) |

## 14. Status bar (`statusbar`)

`st-compute` (Ready, Updating, Error), `st-drc` (link to `tab-drc`), `st-counts` (layers; coils for spiral, phases for
serpentine and wave, U-S4e ruling h; vias), `st-units` (mm),
`st-cursor` (x, y in mm, mono). The status bar announces "Results updated, DRC: 1 failure" at most once per second through
`QAccessible` (assumption: Agent 3 checks NVDA on Windows).

## 14a. Names set in code (U-S4d c)

Shell and dialog parts that U-M4b and U-M4c named. `checks/screens_coverage.py` fails when the UI code sets a literal
objectName that no table defines.

| objectName | Part | Status |
|---|---|---|
| `dlg-new-design` | New design dialog (section 1) | ratified |
| `issues-list` | QListWidget of the input issues in the rail (section 6.1) | ratified |
| `fig-stale` | Stamp "Last valid drawing" on the canvas | ratified |
| `dlg-examples` | Examples gallery dialog | ratified |
| `examples-list` | Its list; items `example-<id>`. Titles follow U-S4e ruling g ("Spiral, 12 coils, 16 poles"); a selected item draws title and note in `text-inverse` | ratified |
| `dlg-recovery` | Recovery offer after an unclean exit (UI-21) | ratified |
| `btn-recover`, `btn-discard-recovery` | Its two buttons | declared |
| `btn-load-example`, `btn-cancel-examples` | Examples gallery buttons | declared |
| `menu-examples` | Examples menu of the toolstrip | declared |
| `dlg-error` | Engine error dialog (UI-12) | declared |
| `main-window`, `work-area`, `centre` | Window, splitter and centre pane | declared |
| `empty-state`, `btn-empty-new`, `btn-empty-examples` | Empty session with New design and Examples (UI-23) | declared |
| `required-bar` | Container of `new-required-count` and `btn-first-missing` | declared |
| `results-rail-empty` | Rail sentence before the first compute | declared |
| `layer-toggles` | Canvas layer checkboxes, one `layer-<name>` each | declared |
| `toolstrip-tabs` | Tab bar of the toolstrip; sections `ts-section-<group>` | declared |
| `design-notice`, `design-notice-text`, `btn-notice-undo`, `btn-apply-suggestion` | Inline notice "Changed from X to Y" with Undo and a suggestion button (UX-AC-12) | declared |
| `param-topology-hint` | Hint under the topology buttons | declared |
| `tab-board-group-fasteners` | Fasteners group box; group boxes are `<tab>-group-<group>` | declared |

Names that U-M4c-3, U-M4d and U-M4d-fix set (U-S4e ruling a). Each is declared with the part it names; none needed a
rename.

| objectName | Part | Status |
|---|---|---|
| `centre-split` | Vertical splitter of the canvas page and `results-tabs` (design_spec 5, U-S4e ruling b) | declared |
| `rail-scroll` | Scroll area of `results-rail`; it is the "Key results" tab below 1280 px | declared |
| `btn-rail-drc` | "DRC" button on the `rail-drc` card; opens `tab-drc` (section 6.1) | declared |
| `results-empty` | Sentence of `tab-results` before the draft parses (section 6) | declared |
| `btn-results-first-missing` | Its "Go to first missing field" button (section 6) | declared |
| `results-scroll` | Scroll area of the result card grid (section 6) | declared |
| `results-stale` | Stamp "Last valid results" (section 6) | declared |
| `drc-summary-icon` | `check-*` glyph of `drc-summary` | declared |
| `drc-truncated` | Hint under `drc-table` when the list is cut | declared |
| `compare-caption`, `compare-empty` | Caption and empty sentence of `tab-compare` (section 10) | declared |
| `dlg-compare-confirm`, `btn-compare-replace` | Confirmation before `btn-set-reference` replaces the reference, and its Replace button | declared |
| `dlg-export-confirm` | Export confirmation with DRC failures (section 11, UX-AC-18) | declared |
| `export-confirm-list`, `btn-export-confirm-cancel`, `btn-export-confirm-run` | Its failure list, Cancel (initial focus) and Export anyway | declared |
| `btn-export-browse` | Browse button of `export-folder` | declared |
| `export-problem` | Hint in `dlg-export` when the export cannot run | declared |
| `btn-export-open-folder`, `btn-export-close` | Open folder and Close of `export-result` | declared |
| `guide-toc`, `guide-body` | Topic tree and body of `dlg-guide` (section 12) | declared |
| `layer-pairs-notice-text`, `btn-layer-pairs-undo` | Sentence and Undo of `layer-pairs-notice` (section 4) | declared |
| `param-rotation-mode-row` | Row container of `param-rotation-mode` | declared |

Name that U-M4c-4 set (U-S4f; principle model-the-domain, one row per name). It names a part, so no rename.

| objectName | Part | Status |
|---|---|---|
| `ts-section-board` | Frame in the toolstrip View tab that holds `board-picker` and its "Board" caption (section 4.1). Built by hand, not from a `TOOLSTRIP` group, because a combo box is not an action. Hidden while the design has one board | declared |

## 15. Requests to other owners

screens.md names these changes; each owner applies them through Fable. U-M2a-fix closed the v2 requests for widget
ids, `/phases` and `RANGE_COIL_GAP_BELOW_CLEARANCE` (`screen_model_diff.py` lists 2 and 3 empty, 2026-10-08).

| To | Request | Row |
|---|---|---|
| Model owner (`fields.py`) | `FieldSpec.widget_id` of `/outline/bore/radius_mm` and the four polygon bore pointers names the section 5 bore widgets (U-S4d c) | U-S4d c |
| U-M2d-3 (model) | The single-board serpentine copper-count check (copper count = phases times layers per phase) | D-031e |
| Model owner (`draft.py`) | DEF-S4c-01: `derive_layer_pairs` must keep a surviving pair by its identity, not its list position, so a deleted middle pair returns and no index repeats. `checks/pair_delete_probe.py` exits 0 when fixed | D-024 |
| U-M4c | Stack-up generator, rotation mode helper and required-field bar | R3, R4, R11 |
| U-M4c | Layer pairs: call `derive_layer_pairs` in the edit that changes the copper count, and `layer-pairs-notice` (section 4) | D-024 |
| U-M4c | Stack mode applicability and the board picker (section 4.1, `assumption`; UX-AC-26) | D-016 |
| Owners of the rules | The quoted proposals in sections 1 to 5 have no issue code yet | R14 |

## 16. Required pointers of a blank draft and their widgets

Generated by `docs/phase2/design/checks/screens_coverage.py --table` from the tables above and `parse_draft(blank_draft)`;
the same script fails when this table drifts. A cell names the widget that fills the pointer for that topology.

| Pointer | spiral | serpentine | wave |
|---|---|---|---|
| `/name` | `param-design-name` | `param-design-name` | `param-design-name` |
| `/winding/coil/coil_count` | `param-coil-count` | not required | not required |
| `/winding/coil/r_inner_mm` | `param-r-inner` | not required | not required |
| `/winding/coil/r_outer_mm` | `param-r-outer` | not required | not required |
| `/winding/coil/trace_width_mm` | `param-trace-width` | not required | not required |
| `/winding/coil/clearance_mm` | `param-clearance` | not required | not required |
| `/winding/coil/coil_gap_mm` | `param-coil-gap` | not required | not required |
| `/connection/ring_width_mm` | `param-ring-width` | `param-ring-width` | `param-ring-width` |
| `/connection/terminal_pad_mm` | `param-terminal-pad` | `param-terminal-pad` | `param-terminal-pad` |
| `/connection/terminal_drill_mm` | `param-terminal-drill` | `param-terminal-drill` | `param-terminal-drill` |
| `/winding/layers/pairs` | `pair-list` | not required | not required |
| `/winding/layers/series_groups` | `pair-list` | not required | not required |
| `/vias/drill_mm` | `param-via-drill` | `param-via-drill` | `param-via-drill` |
| `/vias/pad_mm` | `param-via-pad` | `param-via-pad` | `param-via-pad` |
| `/vias/plating_um` | `param-via-plating` | `param-via-plating` | `param-via-plating` |
| `/outline/board/shape` | `param-outline-shape` | `param-outline-shape` | `param-outline-shape` |
| `/outline/bore/shape` | `param-bore` | `param-bore` | `param-bore` |
| `/stackup/layers` | `param-layer-count`, `layer-list`, `param-copper-weight`, `param-board-thickness` | `param-layer-count`, `layer-list`, `param-copper-weight`, `param-board-thickness` | `param-wave-layers`, `layer-list`, `param-copper-weight`, `param-board-thickness` |
| `/rotor/poles` | `param-poles` | `param-poles` | `param-poles` |
| `/rotor/rotor_type` | `param-rotor-kind` | `param-rotor-kind` | `param-rotor-kind` |
| `/rotor/magnet/kind` | `param-magnet-shape` | `param-magnet-shape` | `param-magnet-shape` |
| `/rotor/remanence_t` | `param-magnet-br` | `param-magnet-br` | `param-magnet-br` |
| `/rotor/recoil_permeability` | `param-magnet-mur` | `param-magnet-mur` | `param-magnet-mur` |
| `/rotor/air_gap_mm` | `param-air-gap` | `param-air-gap` | `param-air-gap` |
| `/rotor/back_iron_thickness_mm` | `param-back-iron` | `param-back-iron` | `param-back-iron` |
| `/operating/speed_rpm` | `param-speed` | `param-speed` | `param-speed` |
| `/operating/line_current_rms_a` | `param-current` | `param-current` | `param-current` |
| `/operating/winding_temperature_degc` | `param-copper-temp` | `param-copper-temp` | `param-copper-temp` |
| `/operating/convection_h_w_m2k` | `param-h-conv` | `param-h-conv` | `param-h-conv` |
| `/operating/ambient_temperature_degc` | `param-ambient` | `param-ambient` | `param-ambient` |
| `/drc_rules/trace_clearance_mm` | `param-min-space` | `param-min-space` | `param-min-space` |
| `/drc_rules/via_clearance_mm` | `param-min-via-space` | `param-min-via-space` | `param-min-via-space` |
| `/drc_rules/edge_clearance_mm` | `param-min-edge` | `param-min-edge` | `param-min-edge` |
| `/drc_rules/hole_clearance_mm` | `param-min-hole-space` | `param-min-hole-space` | `param-min-hole-space` |
| `/drc_rules/min_trace_width_mm` | `param-min-trace` | `param-min-trace` | `param-min-trace` |
| `/drc_rules/min_drill_mm` | `param-min-via` | `param-min-via` | `param-min-via` |
| `/drc_rules/min_annular_ring_mm` | `param-min-ring` | `param-min-ring` | `param-min-ring` |
| `/winding/r_inner_mm` | not required | `param-r-inner` | `param-r-inner` |
| `/winding/r_outer_mm` | not required | `param-r-outer` | `param-r-outer` |
| `/winding/turns` | not required | `param-turns` | `param-turns` |
| `/winding/trace_width_mm` | not required | `param-trace-width` | `param-trace-width` |
| `/winding/clearance_mm` | not required | `param-clearance` | `param-clearance` |
| `/winding/layers_per_phase` | not required | `param-layers-per-phase` | not required |
| `/winding/bus_width_mm` | not required | not required | `param-bus-width` |
