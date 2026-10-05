Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# embodic screens v2 (Phase 2, PySide6)

Date 2026-10-05. Read with `design_spec.md` (tokens, toolstrip, hooks, keyboard map). v2 applies rows R1 to R14 of
`docs/phase2/architecture/screen_model_reconciliation.md` to sections 1 to 5, 6 and 7. Sections 8 to 14 are unchanged
from v1.

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
| `param-topology` | 3 x QToolButton (exclusive, large icons): Spiral, Serpentine, Wave | view model: `DesignDraft.topology` | Proposal: "Choose a topology." |
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
| `new-required-count` | QLabel[class="hint"] | view model: number of `DraftIncomplete.missing` | "38 required fields left" (example count). Hidden once the draft parses. |
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
| `phase-pattern-string` | QLabel[class="unit"], read-only, selectable | result `winding.assignment` | spiral | none | none |
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
| `param-stack-mode` | QComboBox "Stack mode"; hidden (R8) | none yet (D-016 contract change) | serpentine | none | none |
| `param-layer-order` | "Layer order", QComboBox Grouped, Interleaved | `/winding/layer_order` | serpentine | default | none |
| `param-board-gap` | "Board gap", mm; hidden (R8) | none yet (D-016 contract change) | serpentine | none | none |
| `param-via-drill` | "Via drill", mm | `/vias/drill_mm` | spiral, serpentine, wave | required | `INVALID_VIA_RING` |
| `param-via-pad` | "Via pad", mm | `/vias/pad_mm` | spiral, serpentine, wave | required | `INVALID_VIA_RING` |
| `param-vias-per-transition` | "Vias per transition" | `/vias/vias_per_transition` | spiral, serpentine, wave | default | none |
| `param-via-plating` | "Via plating", µm | `/vias/plating_um` | spiral, serpentine, wave | required, property | none |
| `layer-list` | QTableView: layer, kind, group, rotation, joins via, copper µm, show; Space toggles "show" | `/stackup/layers`, `/stackup/layers/*/kind`, `/stackup/layers/*/name`, `/stackup/layers/*/thickness_mm`, `/stackup/layers/*/material`, `/winding/layers/pairs`, `/winding/layers/pairs/*/index`, `/winding/layers/pairs/*/layer_in`, `/winding/layers/pairs/*/layer_out`, `/winding/layers/pairs/*/phases`, `/winding/layers/series_groups` | spiral, serpentine, wave | required | `INVALID_STACKUP_NO_COPPER`, `INVALID_LAYER_NAME_DUPLICATE`, `INVALID_PAIR_LAYER_UNKNOWN`, `INVALID_PAIR_LAYER_SAME`, `INVALID_PAIR_INDEX_DUPLICATE`, `INVALID_SERIES_GROUPS` |

State rules:

- Stack-up generator (R3). `param-layer-count` or `param-wave-layers`, `param-copper-weight` and
  `param-board-thickness` are its inputs. Once all three hold a value, the view-model calls
  `generate_even_stackup(copper_count, copper_thickness_mm, board_thickness_mm)`, with the copper weight converted by
  `copper_oz_to_mm`, and writes `/stackup/layers` as one undoable edit. `layer-list` edits the result. Proposal: after
  a manual `layer-list` edit, a generator input change asks "Replace the edited stack-up?" before it writes.
- For serpentine the copper count must equal phases times layers per phase (UT-GEN-03), so `param-layer-count` offers
  only that value.
- The pair columns of `layer-list` (rotation, group, joins via) show for spiral only. The group column edits
  `/winding/layers/series_groups`. Proposal to U-M4c: for spiral, the generator edit also writes one pair per two
  consecutive copper layers, all in series, so a blank design does not start with an empty pair list (open question).
- Rotation mode (R4) reads the current pair rotations. None writes 0 to every pair. Alternate writes pi/Q to every
  second pair, Q being the coil count (option M3, UT-GEO-11). Custom shows `param-pair-rotation`, which edits the pair
  selected in `layer-list`; the other modes hide it.
- `param-stack-mode` and `param-board-gap` stay hidden until the D-016 fields exist in the contract (R8). Then
  `param-board-gap` shows only when the stack mode is "stacked boards".
- The field check `INVALID_VIA_RING` compares the via pad with the drill. The DRC check `DRC_ANNULAR_RING` compares
  pad minus drill with twice `param-min-ring` and reports in the DRC table. A design can pass the first and fail the
  second (R13).
- Rotation of layer groups shows as solid and dashed footprints on the canvas.

## 5. Board and rotor (`tab-board`)

One `QGroupBox` per group, in this order. Every row applies to all three topologies.

| objectName | Group | Label and Qt widget | Binding key | Start | Messages |
|---|---|---|---|---|---|
| `param-outline-shape` | Outline | "Outline", segment Circle, Polygon | `/outline/board/shape` | required | none |
| `param-outline-sides` | Outline | "Sides", QComboBox 4 to 16 | `/outline/board/sides` (polygon) | required | none |
| `param-outline-size` | Outline | "Board radius" (circle), "Across flats" (polygon), mm | `/outline/board/radius_mm` (circle), `/outline/board/across_flats_mm` (polygon) | required | DRC `DRC_COPPER_EDGE` |
| `param-outline-rotation` | Outline | "Rotation", degrees | `/outline/board/rotation_rad` (polygon) | default | none |
| `param-corner-radius-board` | Outline | "Corner radius", mm | `/outline/board/corner_radius_mm` (polygon) | default | none |
| `param-bore` | Outline | "Centre bore": segment None, Circle, Polygon, then radius, or sides, across flats, corner radius and rotation | `/outline/bore`, `/outline/bore/shape`, `/outline/bore/radius_mm`, `/outline/bore/sides`, `/outline/bore/across_flats_mm`, `/outline/bore/corner_radius_mm`, `/outline/bore/rotation_rad` | required | none |
| `screw-table` | Fasteners | QTableView: size, fit, count, pitch radius (mm), angle offset (degrees); one row per screw pattern | `/outline/screws`, `/outline/screws/*/size`, `/outline/screws/*/fit`, `/outline/screws/*/count`, `/outline/screws/*/pitch_radius_mm`, `/outline/screws/*/angle_offset_rad` | default (no patterns) | DRC `DRC_COPPER_HOLE` |
| `btn-screw-add` | Fasteners | QToolButton "Add pattern" | command | none | none |
| `btn-screw-remove` | Fasteners | QToolButton "Remove pattern" | command | none | none |
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
`stale=true` and the stamp "Last valid results". Keys from Phase 1 stay: `r-phase`, `ke`, `kt`, `ls`, `dt`, `j`.

## 7. DRC (`tab-drc`)

| objectName | Qt widget | Binding key | Behaviour |
|---|---|---|---|
| `drc-summary` | QLabel[class="check-state"] with `check-pass` or `check-fail` icon | `drc.passed`, `drc.violation_count` | "DRC: 2 failures, 1 warning" |
| `drc-table` | QTableView: severity icon, rule code, message, measured, required, layer | `drc.violations` | Rows with `state=fail` get a 4 px fail border. Enter or double-click = Locate. |
| `btn-drc-locate` | QPushButton | selected row | Zooms the canvas to `at_mm`, dims copper to 35 %, draws the ink marker |
| `drc-rule-note` | QLabel[class="hint"] | static | "A violation is reported when clearance < rule − 1e-6 mm (D-006)." |

The message column shows the catalogue text of the violation's `DRC_*` code (R14). The ANNULAR_RING row is where the
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
| `btn-set-reference` | QPushButton | "Set current design as reference"; replaces the stored reference after confirmation |
| `compare-table` | QTableView: quantity, reference, current, delta, unit | Delta as sign plus glyph (▲, ▼); words "better" or "worse" only when Engineering defines the preferred direction. No red or green. Integers without decimals. |
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

| objectName | Qt widget | Rule |
|---|---|---|
| `btn-tests-run` | QPushButton[class="primary"] | Runs the bundled self-tests in a worker; Esc or **Stop** cancels |
| `tests-table` | QTableView: test id, group, result icon, duration, message | Pass, fail, not run; no colour without the icon and word |
| `tests-summary` | QLabel | "131 tests: 129 passed, 2 failed" (example numbers) |

## 14. Status bar (`statusbar`)

`st-compute` (Ready, Updating, Error), `st-drc` (link to `tab-drc`), `st-counts` (layers, coils, vias), `st-units` (mm),
`st-cursor` (x, y in mm, mono). The status bar announces "Results updated, DRC: 1 failure" at most once per second through
`QAccessible` (assumption: Agent 3 checks NVDA on Windows).

## 15. Requests to other owners

screens.md v2 names these changes; each owner applies them through Fable.

| To | Request | Row |
|---|---|---|
| U-M2a fix round (`fields.py`) | Set `widget_id` for the new widgets: `param-phase-count` (`/phases`), `param-bus-width`, `param-ring-width`, `param-terminal-pad`, `param-terminal-drill`, `param-terminal-location` (`/winding/terminal_side`), `param-via-plating`, `param-back-iron`, `param-min-via-space`, `param-min-edge`, `param-min-hole-space`, `param-min-ring` | R5, R9 |
| U-M2a fix round (`fields.py`) | Set `widget_id` `screw-table` for `/outline/screws` and every `/outline/screws/*` leaf; `param-screw-fit` no longer exists | R6 |
| U-M2a fix round (`fields.py`) | Set `widget_id` for the magnet geometry, which is required once a magnet shape is chosen: `param-magnet-arc-ratio`, `param-magnet-r-inner`, `param-magnet-r-outer` (arc), `param-magnet-width`, `param-magnet-length`, `param-magnet-r-center` (block). No row of the reconciliation covers them, because `screen_model_diff.py` reads only blank drafts | none |
| U-M2a fix round (model) | `/phases` optional with neutral value 3; issue `RANGE_COIL_GAP_BELOW_CLEARANCE` (INFO, Suggestion of the trace spacing) | R9, R12 |
| U-M4c | Stack-up generator, rotation mode helper, required-field bar and the spiral pair proposal of section 4 | R3, R4, R11 |
| Owners of the rules | The quoted proposals in sections 1 to 5 have no issue code yet | R14 |

## 16. Required pointers of a blank draft and their widgets

Generated by `docs/phase2/design/checks/screens_coverage.py --table` from the tables above and `parse_draft(blank_draft)`;
the same script fails when this table drifts. A cell names the widget that fills the pointer for that topology.

| Pointer | spiral | serpentine | wave |
|---|---|---|---|
| `/name` | `param-design-name` | `param-design-name` | `param-design-name` |
| `/phases` | none (R9: optional, neutral 3) | `param-phase-count` | `param-phase-count` |
| `/winding/coil/coil_count` | `param-coil-count` | not required | not required |
| `/winding/coil/r_inner_mm` | `param-r-inner` | not required | not required |
| `/winding/coil/r_outer_mm` | `param-r-outer` | not required | not required |
| `/winding/coil/trace_width_mm` | `param-trace-width` | not required | not required |
| `/winding/coil/clearance_mm` | `param-clearance` | not required | not required |
| `/winding/coil/coil_gap_mm` | `param-coil-gap` | not required | not required |
| `/connection/ring_width_mm` | `param-ring-width` | `param-ring-width` | `param-ring-width` |
| `/connection/terminal_pad_mm` | `param-terminal-pad` | `param-terminal-pad` | `param-terminal-pad` |
| `/connection/terminal_drill_mm` | `param-terminal-drill` | `param-terminal-drill` | `param-terminal-drill` |
| `/winding/layers/pairs` | `layer-list` | not required | not required |
| `/winding/layers/series_groups` | `layer-list` | not required | not required |
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
