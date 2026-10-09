Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# M4 screenshot checklist

Date 2026-10-09, revised 2026-10-09 (U-S4d: S35 for `screens.md` section 6.1), revised 2026-10-09 (U-S4e: S36 to S38;
every capture registers the bundled fonts first, `design_spec.md` 4). The user asked to see a screenshot of every screen before M4 acceptance. This file lists each shot:
the screen and state, the example to load, the theme, the window size, what the shot must show, and the objectName
that has keyboard focus when the shot is taken. Section numbers are those of `screens.md` v2.1; "shell" rows cover the
window parts that U-M4b builds and that `screens.md` describes through `design_spec.md` sections 3, 5 and 6.

How to take a shot (assumption until U-M4e writes the verify skill):

- Window size is the client area: 960 x 540 (minimum, two panes) or 1280 x 800 (three panes, `design_spec.md` section 5).
- "L, D" means one shot per theme. A row with two sizes needs one shot per size.
- File name: `shots/<ID>_<theme>_<width>x<height>.png`, for example `shots/S04_dark_1280x800.png`.
- Examples are the packaged files in `resources/examples/`. "Blank" means File > New with no example.
- Producer: U-M4b can take the row now (shell, geometry view, toolstrip, theme). U-M4c (design flow) and U-M4d
  (results and export) rows wait for those units. Owners of `dlg-guide` and `dlg-tests` are not named in the M4 split;
  U-M4d is assumed (`assumption`).

| ID | § | Screen and state | Load | Theme | Window | Must be visible | Focus | Producer |
|---|---|---|---|---|---|---|---|---|
| S01 | shell | Empty session at start | nothing | L, D | 960 x 540, 1280 x 800 | Toolstrip, empty centre offering New design and Examples, status bar "Ready" | `toolstrip` | U-M4b |
| S02 | shell | Toolstrip, one shot per tab: Home, Design, Analysis, Export, View | `spiral_12c16p_default` | L | 1280 x 800 | Every `TOOLSTRIP` action of the tab with icon and label; disabled actions greyed | `act-new`, `act-topo-spiral`, `act-compute`, `act-export-svg`, `act-theme` | U-M4b |
| S03 | shell | Toolstrip at minimum width | `spiral_12c16p_default` | L | 960 x 540 | Small buttons collapsed to icons, large buttons keep labels, nothing clipped | `toolstrip` | U-M4b |
| S04 | shell | Geometry view, spiral, colour mode | `spiral_12c16p_default` | L, D | 1280 x 800 | Red, blue, green phases; letter label on every coil; coil-eye tint and hatches; legend; summary strip with badges | `fig-canvas` | U-M4b |
| S05 | shell | Geometry view, greyscale mode (`act-greyscale` on) | `spiral_12c16p_default` | L, D | 1280 x 800 | Grey ladder A dark to C light; 45 and 135 degree eye hatches; labels unchanged | `fig-canvas` | U-M4b |
| S06 | shell | Geometry view, serpentine | `serpentine_16p_example` | L, D | 1280 x 800 | Continuous ribbon per phase, phase colours and labels | `fig-canvas` | U-M4b |
| S07 | shell | Geometry view, wave | `wave_16p_example` | L, D | 1280 x 800 | Interleaved phases on every layer, phase colours and labels | `fig-canvas` | U-M4b |
| S08 | shell | Layer visibility: one copper layer hidden | `spiral_12c14p` | L | 1280 x 800 | Hidden layer absent from the canvas, its toggle unchecked | the layer toggle | U-M4b |
| S09 | shell | Theme tooltip on the Theme action | `spiral_12c16p_default` | L, D | 1280 x 800 | Tooltip "Label (Shortcut). One sentence." in `surface-inverse` | `act-theme` | U-M4b |
| S10 | shell | Engine error dialog (UI-12) | `spiral_12c10p_d08` with the test hook that raises | L | 1280 x 800 | English message, correlation id, project saved note | the dialog's OK button | U-M4b |
| S11 | 1 | New design dialog, blank | Blank | L, D | 960 x 540 | Name field empty, three topology buttons, example picker on "No example (blank)", Create disabled | `param-design-name` | U-M4c |
| S12 | 1 | New design dialog, ready to create | Blank, name typed, Spiral chosen | L | 960 x 540 | Create design enabled as the primary button | `btn-create-design` | U-M4c |
| S13 | 1.1 | Required-field bar on a blank spiral draft | Blank spiral | L, D | 1280 x 800 | "n required fields left", Go to first missing field; results area shows the missing list | `btn-first-missing` | U-M4c |
| S14 | 2 | Coil tab, spiral, with one invalid field | `spiral_12c16p_default`, then an out-of-range inner radius | L, D | 1280 x 800 | Spiral fields, `example` chips, the edited field with `user` chip, 2 px fail border and message | `param-r-inner` | U-M4c |
| S15 | 2 | Coil tab, serpentine and wave (one shot each) | `serpentine_16p_example`, `wave_16p_example` | L | 1280 x 800 | Only the fields of the active topology; hidden rows leave no gap | `param-r-inner` | U-M4c |
| S16 | 3 | Phases tab | `serpentine_16p_example` | L | 1280 x 800 | Phase count segment, connection mirrored from the toolstrip | `param-phase-count` | U-M4c |
| S17 | 4 | Layers tab, spiral layer pairs | `spiral_12c14p` | L, D | 1280 x 800 | Copper layer count, layer-pair list with rotation and `default` chips | `param-layer-count` | U-M4c |
| S18 | 4 | Layers tab, wave | `wave_16p_example` | L | 1280 x 800 | Wave layer combo with the "in parallel" items | `param-wave-layers` | U-M4c |
| S19 | 4.1 | Board picker, one board per phase | `serpentine_16p_example`, Stack mode set to one board per phase | L | 1280 x 800 | Board picker in the View section on "Board B", canvas showing that board only | `board-picker` | U-M4c |
| S20 | 5 | Board and rotor tab | `spiral_12c16p_default` | L, D | 1280 x 800 | One group box per group in `screens.md` section 5 order, scrolled to the fasteners group | `param-screw-hole-diameter` | U-M4c |
| S21 | 6 | Results before the first compute | Blank spiral | L | 1280 x 800 | "Results appear when every required field is valid." and its button | `btn-results-first-missing` | U-M4d |
| S22 | 6 | Results computed, one card expanded | `spiral_12c16p_default` | L, D | 1280 x 800, 960 x 540 | Cards with value, unit, badge, EQ chip, assumptions tag; "How was this computed" open on R_ph; at 960 the rail is the Key results tab | `res-r-phase-how` | U-M4d |
| S23 | 6 | Stale results after an invalid edit | `spiral_12c16p_default`, then an invalid field | L | 1280 x 800 | Dimmed cards with "Last valid results" | `res-r-phase-value` | U-M4d |
| S24 | 7 | DRC pass | `spiral_12c16p_default` | L | 1280 x 800 | Pass summary with `check-pass` icon, rule note | `drc-summary` | U-M4d |
| S25 | 7 | DRC failure located | `spiral_12c16p_default`, trace spacing below the rule | L, D | 1280 x 800 | Fail rows with 4 px border, canvas zoomed to the marker in ink with copper dimmed | `drc-table` | U-M4d |
| S26 | 8 | Back-EMF chart with the data table open | `spiral_12c16p_default` | L, D | 1280 x 800 | Three phase lines (solid, dashed, dotted), legend, end labels, meta badge | `chart-backemf` | U-M4d |
| S27 | 9 | Torque-speed and power-speed charts | `spiral_12c16p_default` | L | 1280 x 800 | Two charts sharing the rpm axis, one y unit each | `chart-torque-speed` | U-M4d |
| S28 | 10 | Compare, empty and with a reference (one shot each) | `spiral_12c16p_default`, then `spiral_12c14p` after Set reference | L | 1280 x 800 | Empty sentence; then the delta table with glyphs and no red or green | `btn-set-reference`, `compare-table` | U-M4d |
| S29 | 11 | Export dialog, All files | `spiral_12c16p_default` | L, D | 1280 x 800 | Seven format boxes checked, folder field, checklist with engine stamp and DRC result | `btn-export-run` | U-M4d |
| S30 | 11 | Export with DRC failures | the S25 design | L | 1280 x 800 | `dlg-export-confirm` listing the failures, focus on Cancel | `dlg-export-confirm` | U-M4d |
| S31 | 11 | Export result | after S29 | L | 1280 x 800 | List of written files and Open folder | `export-result` | U-M4d |
| S32 | 12 | Guide at an equation entry | `spiral_12c16p_default`, F1 on a field | L, D | 1280 x 800 | Topic tree, body with EQ-ID, formula, sources with page, status | `guide-toc` | U-M4d (assumption) |
| S33 | 13 | Tests dialog after a run | nothing | L | 1280 x 800 | Table with result icon and word per test, summary line | `tests-table` | U-M4d (assumption) |
| S34 | 14 | Status bar crop with a DRC failure | the S25 design | L, D | 1280 x 800 | `st-compute`, `st-drc` link, `st-counts`, `st-units`, `st-cursor` | `statusbar` | U-M4b (`st-compute`, `st-units`, `st-cursor`), U-M4d (`st-drc`, `st-counts`) |
| S36 | 4 | Layers tab, spiral, stack-up and layer pairs at two-pane width | `spiral_12c14p` | L | 960 x 540 | `layer-list` with Kind in full, `pair-list` below it with Rotation chips, no sideways scroll | `pair-list` | U-M4e |
| S37 | 7 | DRC failures at three-pane width | `wave_16p_example` | L | 1280 x 800 | Glyph, Message, Measured (mm), Required (mm), Layer all visible, no sideways scroll | `drc-table` | U-M4e |
| S38 | shell | Compact height: canvas as the Drawing tab | `spiral_12c10p_d08` | L, D | 960 x 540 | "Drawing" first tab and current, ring at fit filling the tab, legend not clipped | `fig-canvas` | U-M4e |
| S35 | 6.1 | Rail status cards with DRC failures | `wave_16p_example` | L, D | 1280 x 800, 960 x 540 | "Inputs" with `check-pass` "No input issues", "DRC" with `check-fail` "186 failures", no "Design" card; at 960 the cards sit in the Key results tab, nothing clipped | `rail-drc` | U-M4d |

Rows S01 to S10 are 10 rows and 22 shots; U-M4b can take them once its shell runs. `tools/design/check_checklist.py`
fails when a `screens.md` section 1 to 14 has no row here or a focus objectName is not defined in `screens.md`,
`design_spec.md` or interfaces.md `TOOLSTRIP`.
