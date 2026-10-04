Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# embodic screens v1 (Phase 2, PySide6)

Date 2026-10-04. Read with `design_spec.md` (tokens, toolstrip, hooks, keyboard map). Each screen lists its widgets with
`objectName`, Qt widget, binding key, validation message and keyboard behaviour, then its state rules.

Conventions for every table:

- Binding keys are JSON pointers into `DesignParameters` (Phase 1 `screen_to_view_map.md`) or a result key into
  `ComputeOutcome`. Pointers for serpentine and wave fields are derived from Xcoil field names (`ui.js:16-139`) and are
  `assumption` until Agent 6's `docs/phase2/architecture/interfaces.md` names the model fields. Agent 6 owns the final
  pointer; the `objectName` stays.
- Numeric fields are `QLineEdit` with a `QDoubleValidator`-style parser in the view model, or `QDoubleSpinBox` with
  `NoButtons`. Either way: Up and Down step, Shift steps ten times, Enter and Tab commit, Esc reverts, the wheel does
  nothing without focus. Units sit in a `QLabel[class="unit"]` named `<id>-unit` and are part of the accessible
  description (`setAccessibleDescription`).
- Every input has a provenance chip `<id>-prov` (`QLabel[class="prov-chip"]`): `user`, `example`, `default` or
  `measured`. "Mark as measured" lives in the field's context menu and asks for the source (D-007).
- Validation runs on commit. The message goes in `<id>-error` (`QLabel[class="field-error"]`), the field gets
  `invalid=true`, and the Checks list gets the same text. Messages name the limit and the unit.
- Hidden vs disabled. A field that does not apply to the active topology or option is hidden with its label, unit and
  chip (`setVisible(False)` on the row). A field blocked by a sibling option in the same group is disabled and its hint
  names the option ("Not used with straight ends").

## 1. New design

Opens at start and on File > New (D-014). Modal `QDialog#dlg-new-design`, 720 x 520 px minimum. Nothing computes until
**Create design** succeeds.

| objectName | Qt widget | Binding key | Validation message | Keyboard |
|---|---|---|---|---|
| `param-design-name` | QLineEdit | `/name` | "Enter a design name." | Initial focus |
| `param-topology` | 3 x QToolButton (exclusive, large icons) | `/winding/topology` | "Choose a topology." | Arrow keys move, Space selects |
| `param-poles` | QLineEdit | `/rotor/poles` | "Poles must be an even number of 2 or more." | numeric field |
| `param-coil-count` | QLineEdit (spiral only) | `/winding/coil/count` | "Coil count must be a multiple of 3." | numeric field |
| `param-r-inner` | QLineEdit, mm | `/winding/r_inner_mm` | "Inner radius must be smaller than the outer radius." | numeric field |
| `param-r-outer` | QLineEdit, mm | `/winding/r_outer_mm` | "Outer radius must be larger than the inner radius." | numeric field |
| `param-layer-count` | QComboBox 2, 4, 6, 8 | `/stackup/copper_layers` | "Choose the number of copper layers." | Arrow keys |
| `param-trace-width` | QLineEdit, mm | `/winding/coil/trace_width_mm` | "Trace width must be at least the board minimum ({min} mm)." | numeric field |
| `param-clearance` | QLineEdit, mm, label "Trace spacing" | `/winding/coil/clearance_mm` | "Trace spacing must be at least the board minimum ({min} mm)." | numeric field |
| `param-speed` | QLineEdit, rpm | `/operating/speed_rpm` | "Enter the operating speed." | numeric field |
| `param-current` | QLineEdit, A rms | `/operating/current_a_rms` | "Enter the phase current." | numeric field |
| `example-picker` | QComboBox, first item "No example (blank)" | none (loads a preset) | none | Arrow keys; Enter loads after confirmation if fields are filled |
| `new-required-count` | QLabel[class="hint"] | view model | "3 required fields left" | none |
| `btn-create-design` | QPushButton[class="primary"] | command | Disabled until every required field is valid; tooltip lists the missing fields | Enter when enabled |
| `btn-cancel-new` | QPushButton | command | none | Esc |

State rules:

- Required fields start empty with a placeholder that shows only the unit, never a number. Required fields carry a
  "Required" hint until filled.
- Loading an example fills the fields with `example` chips and the dialog title reads "New design from example: <name>".
  Editing a field turns its chip to `user`.
- Fields for the other topologies are hidden. Switching topology keeps values already typed in shared fields.
- Optional fields (cooling, drive, materials) are not in this dialog. They start at documented defaults with `default`
  chips in the inspector and count in "n assumptions" (open question Q4 in `design_spec.md`).

## 2. Coil (inspector tab `tab-coil`)

Shared group "Annulus and copper": `param-r-inner`, `param-r-outer`, `param-turns`, `param-trace-width`,
`param-clearance`, `param-corner-radius`, `param-first-coil-angle` (degrees in the UI, radians in the model), `param-poles`.
The label of `param-turns` changes with topology: "Turns per coil" (spiral), "Turns per layer" (serpentine), "Slots
per phase belt" (wave).

| objectName | Qt widget | Binding key | Topology | Validation message | Keyboard |
|---|---|---|---|---|---|
| `param-coil-count` | QLineEdit | `/winding/coil/count` | spiral | "Coil count must be a multiple of 3." Balance hint in `hint-combination` | numeric field |
| `param-side-style` | 2 x QToolButton segment | `/winding/coil/side_style` | spiral | none | Arrow keys |
| `param-end-style` | 3 x QToolButton segment | `/winding/coil/end_style` | spiral | none | Arrow keys |
| `param-coil-gap` | QLineEdit, mm | `/winding/coil/gap_mm` | spiral | "Gap must be at least the trace spacing." | numeric field |
| `param-x-inward-sense` | 2 x QToolButton segment | `/winding/coil/x_inward_sense` | spiral | none | Arrow keys |
| `param-strands` | QLineEdit | `/winding/serpentine/strands` (assumption) | serpentine | "Strands must be 1 or more." | numeric field |
| `param-active-style` | QComboBox | `/winding/serpentine/active_style` (assumption) | serpentine | none | Arrow keys |
| `param-fillet-max` | QCheckBox "Maximum fillet (semicircular U-turn)" | `/winding/serpentine/fillet_max` (assumption) | serpentine | none | Space |
| `param-wave-style` | QComboBox | `/winding/wave/style` (assumption) | wave | none | Arrow keys |

State rules: `param-corner-radius` is disabled with the hint "Not used with straight ends" when `param-end-style` is
straight; it is hidden for serpentine when `param-fillet-max` is checked. The coil figure ("Coil detail" or "Ring")
sits on the canvas, not in the tab.

## 3. Phases (`tab-phases`)

| objectName | Qt widget | Binding key | Validation message | Keyboard |
|---|---|---|---|---|
| `param-connection` | mirrors toolstrip Connection buttons | `/connection/kind` | none | Arrow keys |
| `param-phase-assign-mode` | segment auto, manual | `/connection/assign_mode` | none | Arrow keys |
| `param-phase-sequence` | segment A-B-C, A-C-B | `/connection/sequence` | Hint "Swapping B and C reverses rotation." | Arrow keys |
| `phase-pattern-string` | QLabel[class="unit"] (read-only) | `winding.assignment` | none | Selectable text |
| `phase-balance-status` | QLabel[class="check-state"] | `winding.balance` | "Not balanced: choose 12, 18 or 24 coils" (example values from the engine) | none |
| `phase-table` | QTableView | `winding.assignment` | Manual mode: "Each phase needs the same number of coils." | Arrow keys; F2 edits phase or polarity in manual mode |
| `param-terminal-location` | QLabel (read-only "Outer rim") | `/connection/terminal_location` | none | none |

State rules: manual-mode columns are read-only in auto mode (not hidden: the user needs the assignment). The open
connection shows six terminal rows; star shows U, V, W, N; delta U, V, W.

## 4. Layers (`tab-layers`)

| objectName | Qt widget | Binding key | Topology | Validation message | Keyboard |
|---|---|---|---|---|---|
| `param-layer-count` | QComboBox 2, 4, 6, 8 | `/stackup/copper_layers` | spiral, serpentine | none | Arrow keys |
| `param-wave-layers` | QComboBox | `/winding/wave/layers` (assumption) | wave | none | Arrow keys |
| `param-pair-connection` | segment series, parallel | `/layers/pair_connection` | all | Parallel hint: "Circulating current if layer EMFs differ (EQ-07)." | Arrow keys |
| `param-rotation-mode` | segment none, alternate, custom | `/layers/rotation_mode` | spiral, wave | none | Arrow keys |
| `param-pair-rotation` | QLineEdit, degrees | `/layers/pair_rotation_deg` | custom rotation only | "Rotation must be between 0 and 360 degrees." | numeric field |
| `param-layers-per-phase` | QLineEdit | `/winding/serpentine/layers_per_phase` (assumption) | serpentine | "Layers per phase must divide the layer count." | numeric field |
| `param-stack-mode` | QComboBox | `/winding/serpentine/stack_mode` (assumption) | serpentine | none | Arrow keys |
| `param-layer-order` | QComboBox | `/winding/serpentine/layer_order` (assumption) | serpentine | none | Arrow keys |
| `param-board-gap` | QLineEdit, mm | `/winding/serpentine/board_gap_mm` (assumption) | serpentine, stacked boards only | "Gap must be 0 mm or more." | numeric field |
| `param-via-drill`, `param-via-pad`, `param-vias-per-transition` | QLineEdit | `/vias/...` | all | "Pad must be larger than drill + 2 x annular ring." | numeric field |
| `layer-list` | QTableView: layer, group, rotation, joins via, copper µm, show | `stackup`, `layout` | all | none | Arrow keys; Space toggles "show" |

State rules: `param-pair-rotation` is hidden unless rotation mode is custom. `param-board-gap` is hidden unless stack mode
is "stacked boards". Rotation of layer groups shows as solid and dashed footprints on the canvas.

## 5. Board and rotor (`tab-board`)

Groups (one `QGroupBox` each): Outline (`param-outline-shape`, `param-outline-sides`, `param-outline-size`,
`param-outline-rotation`, `param-corner-radius-board`, `param-bore`); Fasteners (`param-screw-fit`,
`param-screw-count-outer`, `param-screw-count-inner`, `param-screw-circle-outer`, `param-screw-circle-inner`);
Stack-up and manufacturing (`param-copper-weight`, `param-board-thickness`, `param-min-trace`, `param-min-space`,
`param-min-via`); Rotor and magnets (`param-rotor-kind`, `param-magnet-br`, `param-magnet-mur`, `param-magnet-thickness`,
`param-magnet-shape`, `param-air-gap`, poles read-only from Coil); Operating point (`param-speed`, `param-current`,
`param-copper-temp`); Drive (`param-dc-link`, `param-modulation`, `param-current-limit`); Cooling (`param-h-conv`,
`param-ambient`).

| Rule | Message or behaviour |
|---|---|
| Polygon fields | `param-outline-sides` and `param-corner-radius-board` hidden for a circular outline |
| Inner screws | Inner pattern fields hidden when the inner count is 0 |
| Board vs annulus | "Board outline must clear the outer radius by at least the copper-to-edge rule ({rule} mm)." |
| Material properties | `param-magnet-br`, `param-magnet-mur`, `param-h-conv` start at documented defaults with `default` chips; each counts as an assumption until marked measured with a source |
| Binding keys | `/board/...`, `/fasteners/...`, `/stackup/...`, `/rotor/...`, `/operating/...`, `/drive/...`, `/cooling/...` (Agent 6 names the leaves) |

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

State rules: before the first successful compute the tab shows one sentence "Results appear when every required field is
valid." and a button **Go to first missing field**. While computing, values dim to 60 % after 300 ms and the status bar
reads "Updating"; previous values stay until new ones arrive. Invalid input keeps the last valid results dimmed with
`stale=true` and the stamp "Last valid results". Keys from Phase 1 stay: `r-phase`, `ke`, `kt`, `ls`, `dt`, `j`.

## 7. DRC (`tab-drc`)

| objectName | Qt widget | Binding key | Behaviour |
|---|---|---|---|
| `drc-summary` | QLabel[class="check-state"] with `check-pass` or `check-fail` icon | `drc.passed`, `drc.violation_count` | "DRC: 2 failures, 1 warning" |
| `drc-table` | QTableView: severity icon, rule code, message, measured, required, layer | `drc.violations` | Rows with `state=fail` get a 4 px fail border. Enter or double-click = Locate. |
| `btn-drc-locate` | QPushButton | selected row | Zooms the canvas to `at_mm`, dims copper to 35 %, draws the ink marker |
| `drc-rule-note` | QLabel[class="hint"] | static | "A violation is reported when clearance < rule − 1e-6 mm (D-006)." |

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
