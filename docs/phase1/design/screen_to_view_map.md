Prepared by: Agent 1 — UX/UI Expert Designer — model: claude-opus-5-5

# Screen ↔ element ids ↔ engine data (reconciliation round, 2026-10-04)

Purpose: let Agent 6 bind each of my screens to the architecture views (`architecture/architecture_draft.md` §10) and data
models (§7). Inputs are JSON pointers into `DesignParameters` (§7.1); outputs are fields of `ComputeOutcome` (§7.8) —
`winding: WindingPlan`, `layout: Layout`, `drc: DrcReport`, `analysis: AnalysisResult` — each result a `Traceable`
(value, unit, status, eq_ids, assumptions, inputs, validity, tolerance). Element ids follow the canonical rule of
architecture §19, **accepted** (mockups re-rendered with them). Status: bindings are `inferred` from the architecture
draft as read on 2026-10-04; items marked **gap** have no matching model field yet.

## 0. Id changes accepted from architecture §19

| Old mockup id | Canonical id | Model field |
|---|---|---|
| `param-pole-count` | `param-poles` | `/rotor/poles` |
| `param-coil-sides` | `param-side-style` | `/winding/coil/side_style` |
| `param-coil-ends` | `param-end-style` | `/winding/coil/end_style` |
| `param-fillet-radius` | `param-corner-radius` | `/winding/coil/corner_radius_mm` |
| `param-trace-spacing` | `param-clearance` (label stays “Trace spacing”) | `/winding/coil/clearance_mm` |
| `param-spiral-sense` | `param-x-inward-sense` (label “Spiral sense on layer X”) | `/winding/coil/x_inward_sense` |
| `param-start-angle` | `param-first-coil-angle` (UI in degrees) | `/winding/coil/first_coil_angle_rad` |
| `param-terminal-side` | `param-terminal-location` | `/connection/terminal_location` |

## 1. Shell — mockups 01 (variant A) and 07 (variant B, pure greyscale) → `main_window`, `geometry_view`, `results_rail`

| Element ids | Needs from the engine |
|---|---|
| `#doc-name`, `#doc-state` | `DesignParameters.name`; dirty flag from `design_vm` (not engine) |
| `#step-nav`, `#step-<coil…export>` state text | per-step issue counts: `ComputeOutcome.issues` grouped by the step that owns each `pointers[]` entry; DRC fail count → Results step |
| `#engine-state`, `#st-compute` | `versions` (`VersionInfo`), `timings_s`, busy state from `workers.py` |
| `#st-drc` | `drc.passed`, `drc.violation_count`, warning count from `issues` (severity warning) |
| `#st-counts` | `len(stackup.copper_layers())`, `coil_count`, via count from `Layout` / `ViaPlan` |
| `#fig-canvas` | `layout` (copper paths per layer/phase/width run, vias, pads, outline, holes), labels from `winding.assignment` (coil_index, phase, polarity), DRC markers from `drc.violations[].at_mm`; stamp from `versions` + `design_hash` (REQ-T-14) |
| `#fig-layer-chips` | copper layer names from `stackup` |
| `#rail-drc`, `#btn-drc-locate` | first `drc.violations` entry (kind, layer, measured_mm, required_mm, at_mm), `drc.summaries[].pairs_checked` |
| `#res-r-phase` | `analysis.resistance_phase_operating` |
| `#res-ke` | `analysis.ke_phase` |
| `#res-kt` | `analysis.kt_per_line_a_rms` |
| `#res-ls` | `analysis.inductance_estimate` (EQ-14 → `unresolved`, label “estimate”) |
| `#res-dt` | `analysis.temperature_rise` |
| each `#res-*` child | `-value` = `value` formatted per REQ-L-07, `-unit` = `unit`, badge = `status` (trust level of the calculation per D-007 — not lowered by defaults), `-eq` = `eq_ids`, `-asm` tag “n assumptions” = `assumptions` plus `inputs` whose `source` is `default`, listed in the expandable tag |

Variant B (07) uses the same bindings; only the theme differs (`tokens.json` → `light_pure_greyscale_variant`).

## 2. Step 1 Coil — mockup 02 → `coil_panel`, `geometry_view` (coil detail ↔ ring)

| Element ids | Input pointer | Output used |
|---|---|---|
| `#param-coil-count`, `#param-poles` | `/winding/coil/coil_count`, `/rotor/poles` | `winding.feasibility` (balanced, q, periodicity, max_parallel_paths); coils per phase = Q / 3 |
| `#hint-combination` | — | `feasibility.balanced`, `winding.winding_factors[1]` (EQ-08) |
| balanced-count buttons | — | **gap**: list of balanced Q for the current 2p (a `Suggestion` list or helper `balanced_coil_counts(poles)` in `embodic.winding`) |
| `#param-side-style`, `#param-end-style`, `#param-corner-radius` | `/winding/coil/side_style`, `end_style`, `corner_radius_mm` | issue when the radius is reduced (never silent) |
| `#param-turns` (+ `-notice`) | `/winding/coil/turns` | `Suggestion` (pointer `/winding/coil/turns`, proposed_value, reason) → inline notice + Undo (REQ-F-23) |
| `#param-trace-width`, `#param-clearance` (+ `-error`) | `trace_width_mm`, `clearance_mm` | `ValidationIssue` with matching `pointers` → error text; DRC rule limits from `/drc_rules/min_trace_width_mm`, `trace_clearance_mm` |
| `#param-x-inward-sense` | `/winding/coil/x_inward_sense` | — |
| `#param-r-inner`, `#param-r-outer`, `#param-coil-gap`, `#param-first-coil-angle` | `r_inner_mm`, `r_outer_mm`, `coil_gap_mm`, `first_coil_angle_rad` | — |
| Advanced: end widths, inner turn mode | `end_width_outer_mm`, `end_width_inner_mm`, `inner_turn_mode` | — |
| Feasibility rail rows | — | **gap**: derived geometry `Traceable`s are not in `AnalysisResult`: radial turn bound (EQ-02), constructive limit (`SpiralArtwork.turn_limit`, §10.1), coil pitch and pole pitch at r_i / r_o (EQ-01), track length per coil per layer (EQ-03). Proposal: `Layout.derived: GeometryDerived` with these as `Traceable`. |
| `#fig-canvas` (coil detail) | — | one coil's `CopperPath` set + dimension values (from the inputs) |

## 3. Step 2 Phases — mockup 03 frame A → `phase_panel`, phase ring in `geometry_view`

| Element ids | Input pointer | Output used |
|---|---|---|
| `#param-connection` | `/connection/topology` | issue `RANGE_DELTA_TRIPLEN` (EQ-19) with `winding_factors[3]` |
| `#param-phase-assign-mode` | `/winding/assignment` (null = automatic) | — |
| `#param-phase-sequence` | `/winding/phase_sequence` | — |
| `#phase-pattern-string`, `#phase-balance-status` | — | `winding.pattern`, `feasibility.balanced`, `winding_factors[1]`, `[3]` |
| `#phase-table` rows (`#coil-<n>-phase`, `-polarity`, `-direction`) | manual mode writes `/winding/assignment/coils/*` (`phase`, `polarity`) | `winding.assignment[]` (coil_index, phasor_index, phase, polarity); mechanical angle = `first_coil_angle` + n·360°/Q; EMF angle from `phasor_index` |
| phasor star | — | `winding.assignment[].phasor_index` |
| `#param-terminal-location` | `/connection/terminal_location` (P2: `outer` only — inner option hidden, see review notes) | — |
| `#param-terminal-u|v|w|n` | **gap**: no terminal-name field in `ConnectionSpec`; names exist only as KiCad net names (`kicad` section). Proposal: drop from Phases, keep in Export. | — |
| `#phase-ring` | — | `layout` + `winding.assignment` + polarity → circulation arrows |

## 4. Step 3 Layers — mockup 03 frame B → `layer_panel`

| Element ids | Input pointer | Output used |
|---|---|---|
| `#param-layer-count` | derived: number of `CopperLayer` in `/stackup/layers` (regenerates pairs) | — |
| `#param-pair-connection` | `/winding/layers/series_groups` (series = singletons, parallel = one group; custom in Advanced) | `analysis.loss_circulating` (EQ-07); issue `RANGE_PARALLEL_UNEQUAL_Z` |
| `#param-rotation-mode`, `#param-pair-rotation` | `/winding/layers/pairs/*/rotation_rad` | issue `UNBUILDABLE_VIA_DOES_NOT_FIT` (rotated vias need gap ≥ pad + 2 × clearance) |
| `#param-via-drill`, `#param-via-pad`, `#param-vias-per-transition`, plating | `/vias/drill_mm`, `pad_mm`, `vias_per_transition`, `plating_um` | — |
| `#layer-list` / `#layer-<n>` | `/winding/layers/pairs/*` (`layer_in`, `layer_out`), `/stackup/layers/*/thickness_mm` | `stackup.copper_z_mm()`; KiCad layer name by order (§9.3) |
| `#layer-path-diagram` | — | `Circuit` (§7.4) + `ViaPlan` (§7.3): centre/transfer via per transition |
| `#layer-overlay` | — | coil footprints per pair rotated by `rotation_rad` |
| rail rows | — | vias per coil (`ViaPlan`), `analysis.layers[].b1_peak_mid_radius_t` spread (EQ-05), board thickness (`stackup.board_thickness_mm()`, provenance), series turns per phase (**gap**: not in `AnalysisResult`; add as `count` Traceable) |

## 5. Step 4 Board & rotor — no mockup (spec §10.5) → `board_rotor_panel`

Inputs: `/outline/*` (shape, sides, across_flats_mm, radius_mm, corner_radius_mm, rotation_rad, bore_diameter_mm, holes),
`/stackup/*` (+ `source`), `/drc_rules/*` (manufacturing limits), `/rotor/*` (type, magnet, remanence_t,
recoil_permeability, air_gap_mm, back_iron_thickness_mm; poles read-only), `/operating/*` (speed_rpm,
line_current_rms_a, winding_temperature_degc, ambient_temperature_degc, dc_link_v, modulation, convection_h_w_m2k),
`/materials/*` (read-only with source and status), `/analysis/*` (Advanced). Outputs: issues per pointer; provenance per
field (`ProvenanceMap`) for the “default · assumption” marker (REQ-T-06, see review notes).

## 6. Step 5 Results — mockup 04 → `results_view`, `charts`, `status_badge`, `checks_view`

| Section / ids | Output fields |
|---|---|
| `#results-nav` counts | number of `Traceable`s per section; DRC failures |
| `#res-filter-status` | `Traceable.status` of every displayed result |
| Electrical cards `#res-card-<q>` | `ke_phase`, `ke_line`, `kt_per_line_a_rms`, `kv_rpm_per_v`, `resistance_phase_20c`, `resistance_phase_operating` (`r-phase`), `resistance_line`, `emf_phase_rms`, `winding_factor_1`, `utilisation_factor`, `inductance_estimate` (`ls`), `current_density` (`j`), `skin_depth`, `torque` |
| Losses and thermal | `loss_copper`, `loss_eddy`, `loss_circulating`, `loss_delta_circulating`, `temperature_rise` (`dt`), `ipc_guideline_current` (“guideline (unverified)”), `mass_copper`, `mass_laminate` — no efficiency field (good: P1 / REQ-T-11) |
| Back-EMF waveform `#chart-backemf`, `#chart-backemf-table` | `emf_waveform` (samples), `thd_phase`, `thd_line`, `phases[].ke_peak_v_s_per_rad` |
| Torque–speed | **gap**: no torque–speed curve in `AnalysisResult` although `OperatingPoint` has `dc_link_v`/`modulation` (EQ-20, cannot verify yet). Either add `torque_speed: Traceable[curve]` (status unresolved) or remove the section in P2. |
| Stack-up and field | `layers[].z_mm`, `layers[].b1_peak_mid_radius_t`, `phases[].resistance_*`, `phases[].circulating_loss_w` |
| Checks (DRC) | `drc.summaries`, `drc.violations`, `issues` (all categories) |
| Compare | two `ComputeOutcome`s (REQ-F-17, could) |
| “How was this computed” `#<q>-how` | `Traceable.eq_ids` → registry (`equations.v1.json`: name, formula, gate_verdict, tolerance, sources, dominant_assumptions, label), `inputs[]` (pointer, value, unit, source, status), `assumptions[]`, `validity[]`, `tolerance`, `status_reasons[]`, `evidence_ids` → evidence registry; “Copy trace” = serialised Traceable |
| Oracle table | registry `reference_case` / validation results (REQ-T-12) |
| `#btn-export-trace` | all Traceables flattened to CSV |

## 7. Step 6 Export — mockup 05 frame A → `export_view`, `dialogs`

| Element ids | Data |
|---|---|
| `#export-targets` | static list; availability from route state (R1 always, R2/R3 per T2/T3) |
| `#kicad-connection-status`, `#btn-kicad-connect` | not engine: IPC client state (KiCad version, board name, `get_copper_layer_count()`, `get_stackup()`) |
| `#kicad-layer-map`, `#kicad-map-L<n>` | `stackup` (embodic) vs board stack-up; block when the board has fewer copper layers (REQ-K-14) |
| `#param-kicad-origin-x/y`, `#param-kicad-rotation`, group/lock/replace, `#kicad-net-names` | project file `kicad.placement` and net names (not part of the design hash) |
| `#export-checklist` | `versions`, `design_hash`, `drc.passed` + first violation, stack-up warnings, “run KiCad DRC” note |
| `#kicad-preview-counts` | `embodic.io.kicad_items.layout_to_item_specs(layout)` counts (tracks, arcs, vias, pads, outline) |
| `#btn-kicad-place`, `#dlg-place-confirm` | `drc.violations` listed in the dialog (REQ-F-33) |
| `#btn-save-kicad-file`, other file buttons | R1 writer, SVG/DXF/JSON/PDF writers with REQ-T-07 metadata |

## 8. KiCad plugin variant — mockup 05 frame B → `kicad_compact` (compact mode of the standalone app, R3)

Window 880 × 600, **2-D only, no 3-D, no animation**. What survives:

| Tab (`#plg-tab-*`) | Kept | Dropped / collapsed |
|---|---|---|
| Coil | combination, shape, turns, w/s, annulus (same `#param-*` ids) | coil-detail figure (ring preview only), feasibility rail → one-line summary |
| Phases | connection, method, sequence, pattern + balance | coil table and phasor star (behind “Details”), terminal names |
| Layers | layer count (pre-filled from the board), pair connection, pair rotation, vias | section/path diagram and overlay (behind “Details”) |
| Board | outline, manufacturing limits, stack-up **read from the board** (REQ-K-03) | rotor, operating point, drive, cooling collapsed (still editable) |
| Place | connection card, layer map, origin X/Y (`#plg-origin-x/y`), checklist, `#plg-btn-place`, Save file | — |
| (all tabs) | 2-D preview, `#res-r-phase`, `#res-kt`, DRC summary with badges | Results step, charts, compare, PDF report → link “Open in the embodic app” |

Minimum-size mockup of this window: `05b_kicad_window.html` (880 × 600 px, 0 px overflow, Place button visible).

## 9. Phone — mockup 06

Out of scope with the desktop option (REQ-N-15, UD-01 = C-A). Kept only as the reference if C-B1 is chosen; ids equal
the desktop ids.

---

Revision 2026-10-04 (defect fixes): badge/assumptions binding updated for decision D-007 (badge = calculation trust
level; defaults and assumed inputs feed the separate “n assumptions” tag); KiCad window mockup 05b referenced.
