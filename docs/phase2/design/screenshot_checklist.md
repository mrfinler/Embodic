Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5; U-S4f revision: claude-sonnet-5-5 (U-S4f); U-S4g revision: claude-opus-5-5

# M4 screenshot checklist

Date 2026-10-09, revised 2026-10-09 (U-S4d: S35 for `screens.md` section 6.1), revised 2026-10-09 (U-S4e: S36 to S38),
revised 2026-10-09 (U-S4f: final list for U-M4e-2, a lever column, rules for fonts and focus, S39 to S41),
revised 2026-10-12 (U-S4g: S33 moves to M5, rule Popups, cells of S17, S20, S27 and S40; review in `m4_review_2.md` section 7). The user asked
to see a screenshot of every screen before M4 acceptance. This file lists each shot: the screen and state, the example to
load, the theme, the window size, what the shot must show, the objectName that has keyboard focus when the shot is
taken, and the lever on main that takes it. Section numbers are those of `screens.md` v2.3. "Shell" rows cover the
window parts that `screens.md` describes through `design_spec.md` sections 3, 5 and 6. U-M4e-2 takes every row.

How to take a shot:

- Window size is the client area: 960 x 540 (minimum, two panes) or 1280 x 800 (three panes, `design_spec.md` section 5).
- "L, D" means one shot per theme. A row with two sizes needs one shot per size.
- File name: `shots/<ID>_<theme>_<width>x<height>.png`, for example `shots/S04_dark_1280x800.png`.
- Examples are the packaged files in `resources/examples/`. "Blank" means File > New with no example. A lever that
  loads D08 where the row names another example is a lever to change, not a substitute; the file name carries the
  example id.
- Fonts. Every lever starts Qt through `qt_application()` (`src/embodic/ui/app.py`), which calls `register_fonts`, so
  a shot renders in the bundled Inter Regular, Inter SemiBold and JetBrains Mono. A lever that builds its own
  `QApplication` renders in the fallback font and its shots do not count. `grep -n "qt_application()" <lever>` shows
  the call; the six levers of the table below all have it (`verified` by running grep, 2026-10-09).
- Focus. Before the grab the lever calls `setFocus()` on the widget of the Focus column and lets the window process
  events, so the 2 px ring of UX-AC-11 shows on that widget. The eight U-M4e-1 shots all show the ring on the toolstrip
  Home tab, so none met their Focus cell (`verified` by looking).
- Popups. A tooltip or an open combo list is a top-level window that `QWidget.grab()` leaves out: S09 and S18 of the
  U-M4e-2 set show neither (`verified` by looking). The lever paints each visible popup into the window image at its
  position before it saves the file.
- Numbers. A shot that makes a numeric claim (pane widths, canvas share, text contrast) is read with
  `docs/phase2/design/checks/shot_measure.py`, not by eye. A shot that cannot show a claim, such as U+00A0 between
  number and unit, leaves that claim `not tested`.
- Rows whose Lever cell starts with "none" have no lever on main: S01, S02, S03, S05, S08, S09, S10, S12, S14, S21, S23, S24, S31, S33, S34, S41 (16 rows). U-M4e-2 adds
  one lever function for each next to the existing ones, in the same folder, started through `qt_application()`.

| ID | § | Screen and state | Load | Theme | Window | Must be visible | Focus | Lever on main |
|---|---|---|---|---|---|---|---|---|
| S01 | shell | Empty session at start | nothing | L, D | 960 x 540, 1280 x 800 | Toolstrip, empty centre offering New design and Examples, status bar "Ready" | `toolstrip` | none; U-M4e-2 adds one |
| S02 | shell | Toolstrip, one shot per tab: Home, Design, Analysis, Export, View | `spiral_12c16p_default` | L | 1280 x 800 | Every `TOOLSTRIP` action of the tab with icon and label; disabled actions greyed | `act-new`, `act-topo-spiral`, `act-compute`, `act-export-svg`, `act-theme` | none; U-M4e-2 adds one |
| S03 | shell | Toolstrip at minimum width | `spiral_12c16p_default` | L | 960 x 540 | Small buttons collapsed to icons, large buttons keep labels, nothing clipped | `toolstrip` | none; `qt_shell/capture_u_m4e.py` shows only the Home tab at 960 |
| S04 | shell | Geometry view, spiral, colour mode | `spiral_12c16p_default` | L, D | 1280 x 800 | Red, blue, green phases; letter label on every coil; coil-eye tint and hatches; legend; summary strip with badges | `fig-canvas` | `qt_design/capture_canvas.py` (D08 and light, dark; load the row's example) |
| S05 | shell | Geometry view, greyscale mode (`act-greyscale` on) | `spiral_12c16p_default` | L, D | 1280 x 800 | Grey ladder A dark to C light; 45 and 135 degree eye hatches; labels unchanged | `fig-canvas` | none; U-M4e-2 adds one |
| S06 | shell | Geometry view, serpentine | `serpentine_16p_example` | L, D | 1280 x 800 | Continuous ribbon per phase, phase colours and labels | `fig-canvas` | `qt_design/capture_canvas.py` |
| S07 | shell | Geometry view, wave: fit zoom, then 3x zoom on phase B copper | `wave_16p_example` | L, D | 1280 x 800 | Fit zoom: labels A+ A− B+ B− C+ C− all in view, leaders inside the view. 3x: a "B" label in view. Phase colours | `fig-canvas` | `qt_design/capture_canvas.py` (fit and 3x zoom) |
| S08 | shell | Layer visibility: one copper layer hidden | `spiral_12c14p` | L | 1280 x 800 | Hidden layer absent from the canvas, its toggle unchecked | the layer toggle | none; U-M4e-2 adds one |
| S09 | shell | Theme tooltip on the Theme action | `spiral_12c16p_default` | L, D | 1280 x 800 | Tooltip "Label (Shortcut). One sentence." in `surface-inverse` | `act-theme` | none; U-M4e-2 adds one |
| S10 | shell | Engine error dialog (UI-12) | `spiral_12c10p_d08` with the test hook that raises | L | 1280 x 800 | English message, correlation id, project saved note | the dialog's OK button | none; U-M4e-2 adds one |
| S11 | 1 | New design dialog, blank | Blank | L, D | 960 x 540 | Name field empty, three topology buttons, example picker on "No example (blank)", Create disabled | `param-design-name` | `qt_design/capture_screens.py` (`new-design_blank_<theme>`; dialog size, not 960 x 540) |
| S12 | 1 | New design dialog, ready to create | Blank, name typed, Spiral chosen | L | 960 x 540 | Create design enabled as the primary button | `btn-create-design` | none; U-M4e-2 adds one |
| S13 | 1.1 | Required-field bar on a blank spiral draft | Blank spiral | L, D | 1280 x 800 | "n required fields left", Go to first missing field; results area shows the missing list | `btn-first-missing` | `qt_design/capture_screens.py` (`inspector-coil_blank-spiral_light`, light only) |
| S14 | 2 | Coil tab, spiral, with one invalid field | `spiral_12c16p_default`, then an out-of-range inner radius | L, D | 1280 x 800 | Spiral fields, `example` chips, the edited field with `user` chip, 2 px fail border and message | `param-r-inner` | none; U-M4e-2 adds one |
| S15 | 2 | Coil tab, serpentine and wave (one shot each) | `serpentine_16p_example`, `wave_16p_example` | L | 1280 x 800 | Only the fields of the active topology; hidden rows leave no gap | `param-r-inner` | `qt_design/capture_screens.py` (`inspector-coil_<serpentine, wave>`) |
| S16 | 3 | Phases tab | `serpentine_16p_example` | L | 1280 x 800 | Phase count segment, connection mirrored from the toolstrip | `param-phase-count` | `qt_design/capture_screens.py` (`inspector-phases_serpentine`) |
| S17 | 4 | Layers tab, spiral layer pairs | `spiral_12c14p` | L, D | 1280 x 800 | Copper layer count, `layer-list`, `pair-list` with rotation and its provenance chip (`example` after an example load), the inspector scrolled until `pair-list` is whole | `param-layer-count` | `qt_design/capture_screens.py` (D08), `qt_shell/capture_u_m4e.py` (12c14p at 960) |
| S18 | 4 | Layers tab, wave | `wave_16p_example` | L | 1280 x 800 | Wave layer combo with the "in parallel" items | `param-wave-layers` | `qt_design/capture_screens.py` (`inspector-layers_wave`) |
| S19 | 4.1 | Board picker, one board per phase | `serpentine_16p_example`, Stack mode set to one board per phase | L | 1280 x 800 | Board picker in the View section on "Board B", canvas showing that board only | `board-picker` | `qt_design/capture_board_picker.py` |
| S20 | 5 | Board and rotor tab | `spiral_12c16p_default`, one fastener pattern added and filled (M3, 6, 45 mm, Clearance, 3.4 mm) so the design stays valid | L, D | 1280 x 800 | One group box per group in `screens.md` section 5 order, scrolled until `screw-table` (three columns), `btn-screw-add` and `btn-screw-remove` (with a boundary), the fit, hole diameter and angle offset fields are all in view | `param-screw-hole-diameter` | `qt_design/capture_screens.py` (`inspector-board_*`), `qt_shell/capture_u_m4e.py` (`board-screws-drc`) |
| S21 | 6 | Results before the first compute | Blank spiral | L | 1280 x 800 | "Results appear when every required field is valid." and its button | `btn-results-first-missing` | none; U-M4e-2 adds one |
| S22 | 6 | Results computed, one card expanded | `spiral_12c16p_default` | L, D | 1280 x 800, 960 x 540 | Cards with value, unit, badge, EQ chip, assumptions tag; "How was this computed" open on R_ph; no card clipped or past the scroll bar; at 960 the rail is the Key results tab and "Drawing" is the first tab | `res-r-phase-how` | `qt_results/capture_screens.py` (`results_d08_<theme>`), `qt_results/capture_rail_screens.py` (960) |
| S23 | 6 | Stale results after an invalid edit | `spiral_12c16p_default`, then an invalid field | L | 1280 x 800 | Dimmed cards with "Last valid results" | `res-r-phase-value` | none; U-M4e-2 adds one |
| S24 | 7 | DRC pass | `spiral_12c16p_default` | L | 1280 x 800 | Pass summary with `check-pass` icon, rule note | `drc-summary` | none; `--smoke --screenshot-dir` shows the passed card only |
| S25 | 7 | DRC failure located | `spiral_12c16p_default`, trace spacing below the rule | L, D | 1280 x 800 | Fail rows with 4 px border, canvas zoomed to the marker in ink with copper dimmed | `drc-table` | `qt_results/capture_screens.py` (`drc_wave_located_light`, light only) |
| S26 | 8 | Back-EMF chart with the data table open | `spiral_12c16p_default` | L, D | 1280 x 800 | Three phase lines (solid, dashed, dotted), legend, end labels, meta badge | `chart-backemf` | `qt_results/capture_screens.py` (`back_emf_d08_<theme>`) |
| S27 | 9 | Torque-speed and power-speed charts | `spiral_12c16p_default`, DC-link voltage set to 24 V (the example leaves it empty, so the tab shows its empty state) | L | 1280 x 800 | Two charts sharing the rpm axis, one y unit each | `chart-torque-speed` | `qt_results/capture_screens.py` (`torque_speed_d08_dc24v_light`) |
| S28 | 10 | Compare, empty and with a reference (one shot each) | `spiral_12c16p_default`, then `spiral_12c14p` after Set reference | L | 1280 x 800 | Empty sentence; then the delta table with glyphs and no red or green | `btn-set-reference`, `compare-table` | `qt_results/capture_screens.py` (`compare_d08_vs_12c14p_light`, second shot only) |
| S29 | 11 | Export dialog, All files | `spiral_12c16p_default` | L, D | 1280 x 800 | Seven format boxes checked, folder field, checklist with engine stamp and DRC result | `btn-export-run` | `qt_results/capture_screens.py` (`export_dialog_wave_light`, light only) |
| S30 | 11 | Export with DRC failures | the S25 design | L | 1280 x 800 | `dlg-export-confirm` listing the failures, focus on Cancel | `dlg-export-confirm` | `qt_results/capture_screens.py` (`export_confirm_wave_light`) |
| S31 | 11 | Export result | after S29 | L | 1280 x 800 | List of written files and Open folder | `export-result` | none; U-M4e-2 adds one |
| S32 | 12 | Guide at an equation entry | `spiral_12c16p_default`, F1 on a field | L, D | 1280 x 800 | Topic tree, body with EQ-ID, formula, sources with page, status | `guide-toc` | `qt_results/capture_screens.py` (`guide_eq18_light`, light only) |
| S33 | 13 | Tests dialog after a run (milestone M5, `m4_review_2.md` ruling l) | nothing | L | 1280 x 800 | Table with result icon and word per test, summary line | `tests-table` | M5; no Tests entry ships before then, so M4 takes no shot |
| S34 | 14 | Status bar crop with a DRC failure | the S25 design | L, D | 1280 x 800 | `st-compute`, `st-drc` link, `st-counts`, `st-units`, `st-cursor` | `statusbar` | none; U-M4e-2 adds one |
| S36 | 4 | Layers tab, spiral, stack-up and layer pairs at two-pane width | `spiral_12c14p` | L | 960 x 540 | `layer-list` with Kind in full, `pair-list` below it with Rotation chips drawn as `prov-chip` (dashed for `example`), neither table with an empty header cell, no sideways scroll | `pair-list` | `qt_shell/capture_u_m4e.py` (`layers-pair-list`) |
| S37 | 7 | DRC failures at three-pane width | `wave_16p_example` | L | 1280 x 800 | Glyph, Message, Measured (mm), Required (mm), Layer all visible, no sideways scroll | `drc-table` | `qt_shell/capture_u_m4e.py` (`board-screws-drc`), `qt_results/capture_rail_screens.py` |
| S38 | shell | Compact height: canvas as the Drawing tab | `spiral_12c10p_d08` | L, D | 960 x 540 | "Drawing" first tab and current, ring at fit filling the tab, legend not clipped | `fig-canvas` | `qt_shell/capture_u_m4e.py` (`drawing-tab-<theme>`) |
| S35 | 6.1 | Rail status cards with DRC failures | `wave_16p_example` | L, D | 1280 x 800, 960 x 540 | "Inputs" with `check-pass` "No input issues", "DRC" with `check-fail` "186 failures", no "Design" card; at 960 the cards sit in the Key results tab, nothing clipped | `rail-drc` | `qt_results/capture_rail_screens.py` (`drc_wave_<size>_light`, light only) |
| S39 | 14a | Examples gallery with one item selected | nothing; open Examples, select the second item | L, D | dialog size | The five titles of ruling g with no "Example", "default", "Xcoil" or institution name; the selected item's title and note readable (4.5:1 or more, `checks/shot_measure.py` reads it) | `examples-list` | `qt_shell/capture_u_m4e.py` (light only) |
| S40 | 11 | PDF report: page 1 and the last text page | `spiral_12c10p_d08` | L | A4 page, 110 dpi | Page 1: µH, mΩ, mV·s/rad, Ω, η, ΔT and A/mm² print, headings in SemiBold. Last page: the colophon line ends the report, after the drawing legend. `pdffonts` output beside the shots lists Inter-Regular, Inter-SemiBold and JetBrainsMono-Regular embedded | none (PDF) | `qt_shell/capture_u_m4e.py` (page 1 only; U-M4e-2 adds the last text page and the `pdffonts` line) |
| S41 | shell | Canvas after a resize | `spiral_12c10p_d08`, loaded at 1280 x 800, then the window resized to 960 x 700 | L | 960 x 700 | The ring fills the canvas within 10 %, legend not clipped, labels unchanged (UX-AC-27) | `fig-canvas` | none; U-M4e-2 adds one |

The checklist has 41 rows; M4 takes 40 of them (S33 is M5). `tools/design/check_checklist.py` fails when a `screens.md` section 1 to 14 has no row
here or a focus objectName is not defined in `screens.md`, `design_spec.md` or interfaces.md `TOOLSTRIP`.
