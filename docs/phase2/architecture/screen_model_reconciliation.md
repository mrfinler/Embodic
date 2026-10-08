Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5

# Screens and design model: which side changes (2026-10-05, U-D2)

For Agent 1 (owner of `docs/phase2/design/screens.md`), Agent 3 in U-M4c (forms and session), and the Agent 3 worker
of the U-M2a fix round (`work_breakdown.md` §7). U-M2a reported that screens.md v1 and the merged field table disagree.
This file decides each disagreement once. Nobody edits the other side's files: each row names the side that changes.

## How to see the current differences

Run `python3 docs/phase2/architecture/checks/screen_model_diff.py`. It reads screens.md and imports the merged
`embodic.model` from `src/`, then prints three lists: widgets without fields, binding keys that differ from the model
pointer, and required pointers of a blank draft that no widget can fill. On main a138975 it printed 14 widgets without
fields, 17 differing keys, and 10 orphan required pointers for spiral and serpentine and 11 for wave (`verified (run)`,
2026-10-05).

When both sides have applied this table, the script prints nothing in lists 2 and 3. List 1 then holds only the
view-model helpers of rows R3 and R4 (`param-topology`, `param-layer-count`, `param-wave-layers`,
`param-copper-weight`, `param-board-thickness`, `param-rotation-mode`) and, until the D-016 contract change,
`param-stack-mode` and `param-board-gap`.

Revision 2026-10-08 (U-D4). On main c7fff3a with the screens.md working copy that Agent 1 is revising in U-S4c, the
script prints seven widgets in list 1 and nothing in lists 2 and 3 (`verified (run)`, 2026-10-08). List 1 holds the
six view-model helpers of R2 to R4 and `param-screw-hole-diameter`, which waits for its FIELDS row (R16).
`param-stack-mode` and `param-board-gap` have their rows since the U-M2a fix round, and `param-screw-fit` is gone (R15).

## Binding rule

`FieldSpec.widget_id` is the only join between a widget and a field (interfaces.md §2.3). U-M4c binds through it and
never parses the binding keys in screens.md. The keys in screens.md stay for readers and must equal the model pointer.
screens.md already says that Agent 6 owns the final pointer and the objectName stays.

## Decisions

| # | Item | screens.md v1 | Merged model | Decision | Who changes |
|---|---|---|---|---|---|
| R1 | Binding keys | 17 keys differ (script list 2), for example `/winding/coil/count`, `/connection/kind`, `/operating/current_a_rms`, `/winding/serpentine/strands` | `/winding/coil/coil_count`, `/connection/topology`, `/operating/line_current_rms_a`, `/winding/strands` | The model pointer wins. `param-current` is the line current (rms): label "Line current (rms)", message "Enter the line current." `param-phase-assign-mode` writes `/winding/assignment`: auto is `null`, manual is the list. `param-pair-rotation` edits `/winding/layers/pairs/*/rotation_rad`, shown in degrees | Agent 1 |
| R2 | Topology picker | `param-topology` bound to `/winding/topology` | `/winding/kind` is a constant, not a field (interfaces.md §2.3) | `param-topology` sets `DesignDraft.topology`, which fixes `/winding/kind` | Agent 1 (key text); U-M4c |
| R3 | Layer count, copper weight, board thickness | `param-layer-count`, `param-wave-layers`, `param-copper-weight`, `param-board-thickness` bound to `/stackup/copper_layers` and others | The stack-up is an explicit layer list (REQ-F-04); no count field | These widgets are inputs of a stack-up generator in the session view-model. It calls `generate_even_stackup(copper_count, copper_thickness_mm, board_thickness_mm)` (copper weight through `copper_oz_to_mm`) and writes `/stackup/layers` as one undoable edit. `layer-list` edits the result. For serpentine the count must equal phases times layers per phase (UT-GEN-03), so the view-model offers only that value | Agent 1 (describe as generator inputs); U-M4c |
| R4 | Rotation mode | `param-rotation-mode` (none, alternate, custom) for spiral and wave | per-pair `rotation_rad` on spiral layer pairs; wave has no layer pairs | View-model helper for spiral only: none writes 0, alternate writes pi/Q on every second pair (option M3, UT-GEO-11), custom shows `param-pair-rotation`. Remove wave from its topology column | Agent 1; U-M4c |
| R5 | Terminal location | `param-terminal-location`, read-only "Outer rim" | serpentine `/winding/terminal_side` (outer, inner) has no widget; spiral and wave have no field | For serpentine the widget becomes an editable segment bound to `/winding/terminal_side`. For spiral and wave it stays read-only | Agent 1; U-M2a fix round (widget id in the field table) |
| R6 | Screw patterns | fixed outer and inner rings: `param-screw-count-*`, `param-screw-circle-*`, `param-screw-fit` | `/outline/screws` is a list of patterns (size, fit, count, pitch radius, angle offset) | The list stays. One pattern table `screw-table` replaces the four ring widgets; fit becomes a column. Xcoil's two rings are two rows | Agent 1; U-M2a fix round (widget ids) |
| R7 | Current limit | `param-current-limit` in Drive | no field | Remove it in Phase 2. EQ-20 reads V_dc, modulation, R, L_s and Ke only (`docs/phase2/engineering/equation_specification.md` EQ-20), so no calculation would read it | Agent 1 |
| R8 | Multi-board serpentine | `param-stack-mode`, `param-board-gap` | `/winding/stack_mode`, `/winding/board_gap_mm` (interfaces.md §2.2, added 2026-10-05 by U-D3; §13 point 1 closed) | Keep the widgets. The U-M2a fix round adds the two FIELDS rows with these widget ids; U-M3a implements the per-phase stack | U-M2a fix round; U-M3a |
| R9 | Required fields without a widget | none for 10 required pointers (11 for wave) | required in every blank draft (script list 3) | `/phases` becomes optional with neutral value 3, and serpentine and wave show a new `param-phase-count` (1, 2, 3); spiral hides it. New widgets for the rest: `param-ring-width`, `param-terminal-pad`, `param-terminal-drill` (Phases); `param-via-plating` in µm, a property field with chip and "Mark as measured" (Layers); `param-back-iron` (Rotor and magnets); `param-bus-width` (Coil, wave); `param-min-via-space`, `param-min-edge`, `param-min-hole-space`, `param-min-ring` (Stack-up and manufacturing, labelled per the clearance table in interfaces.md §7). Agent 1 may rename these objectNames before the fix round runs; the field table follows screens.md | Agent 1 (widgets); U-M2a fix round (`phases` default, widget ids) |
| R10 | Defaults for physical inputs | B_r, mu_r and h start at documented defaults with `default` chips; cooling is optional | B_r, mu_r, h, ambient and winding temperature are required (ADR-0010 decision 2) | The model stands. D-014 says the user enters every design parameter, and a default B_r would be a physical assumption inside Ke. These fields start empty with the "Required" hint; the property fields keep "Mark as measured". Of the groups screens.md §1 calls optional, only drive (`dc_link_v`, modulation) and material overrides are | Agent 1 |
| R11 | When "Create design" enables | disabled until every required field is valid | a blank spiral draft has 38 required pointers, most of them outside the dialog | Create design needs a valid name and topology. It opens the draft in the inspector. Compute starts once `parse_draft` returns `DesignParameters` (REQ-F-36, UI-24); `new-required-count` and "Go to first missing field" lead the user there | Agent 1; U-M4c |
| R12 | Coil gap | error "Gap must be at least the trace spacing." | no rule; Agent 2's generator uses max(gap, s) (`spiral_generator_spec.md` l.31, l.147) | Agent 2's semantics stand: a gap below s is valid and the generator uses s. The model adds an INFO issue `RANGE_COIL_GAP_BELOW_CLEARANCE` with a Suggestion of s, shown as a hint, not an error | Agent 1 (drop the error); U-M2a fix round (issue and message) |
| R13 | Via ring | "Pad must be larger than drill + 2 x annular ring." | `INVALID_VIA_RING`: pad at least drill + 0.1 mm (Xcoil `VIA_RING`, `engine.js` l.145) | Two checks at two levels, both kept. The field shows the catalogue text of `INVALID_VIA_RING`. The relation pad - drill >= 2 x `min_annular_ring_mm` is the DRC check ANNULAR_RING and appears in the DRC table. A design can pass the field check and fail DRC; that is intended | Agent 1 (message) |
| R14 | Message texts | each row proposes a text | `embodic.errors.MESSAGES` | The UI shows the catalogue text of the issue. A screens.md text without an issue code is a proposal to the unit that owns the rule | Agent 1; owning units |
| R15 | Screw fit widget (DEF-2, U-M2a-fix report) | `param-screw-fit` named only in the §15 prose, so script list 1 reported it | `/outline/screws/*/fit` has `widget_id` `screw-table` (R6) | Revision 2026-10-08 (U-D4): R6 stands. Fit is a column of `screw-table`, and no `param-screw-fit` widget exists. The prose mention goes; the script then has nothing to report. Closed in the U-S4c working copy, which no longer names it | Agent 1 (U-S4c) |
| R16 | Hole diameter (D-031a) | `param-screw-hole-diameter` edits the pattern selected in `screw-table` | no field on main c7fff3a | Revision 2026-10-08 (U-D4): new FIELDS row `/outline/screws/*/hole_diameter_mm`, design, mm, required once the pattern exists, no default, `widget_id` `param-screw-hole-diameter` (interfaces.md §2.2). `size` and `fit` stay labels and pick no diameter. Example values come only from a cited table (U-S3b) | U-M2d-3 (field row); Agent 1 (widget, done in U-S4c) |

## What does not change

The objectNames, groups, keyboard behaviour and state rules of screens.md stay, except where a row above says
otherwise. The model keeps its pointers, required set and units, except for the U-M2a fix round items named in R5, R6,
R9 and R12 and the U-M2d-3 field of R16.
