Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# U-V4 defect rows (M4, main 4fda98d)

Every reproduce command runs from the worktree root with `QT_QPA_PLATFORM=offscreen PYTHONPATH=src` and the project
virtual environment. A strict xfail names each row that has a test; `--runxfail` shows the disagreement.

| Id | Severity | Finding | Reproduce | Owner |
|---|---|---|---|---|
| DEF-UV4-01 | moderate | The wave SVG names 44 of 48 belts. B− and C− get 6 labels each instead of 8 (16 poles x 3 phases, polarity alternating). Brief 1a and design_spec.md l.126 ask one label per belt; interfaces.md §9.3 draws only the labels `place_labels` keeps at page scale. Status `verified` by running. | `pytest tests/independent/m4/test_exports_svg.py -k wave_has_one --runxfail` | Agent 1 rules (per belt or per placement), then Agent 3 |
| DEF-UV4-02 | minor | The PDF key results print `(dimensionless)`, the results card prints `dimensionless`. Brief 1c asks the same unit text as the UI. `verified`. | `pytest tests/independent/m4/test_ui_behaviour.py -k dimensionless --runxfail` | Agent 1 picks one text, Agent 3 |
| DEF-UV4-03 | minor | The card title "Phase resistance at 20 °C R_ph" joins 20 and °C with a plain space (request 6 asks U+00A0 between every displayed number and unit). The PDF quantity text has the same space. `verified`. | `pytest tests/independent/m4/test_ui_behaviour.py -k titles_join --runxfail` | Agent 3 |
| DEF-UV4-04 | minor | For L_m and the IPC current, the card badge reads "estimate" while the PDF prints the status "unresolved (estimate)" and "unresolved (guideline (unverified))". Brief 1c asks the same status word. design_spec.md P1 says "Estimates say 'estimate'". `verified`. | `pytest tests/independent/m4/test_ui_behaviour.py -k status_word --runxfail` | Agent 1 rules |
| DEF-UV4-05 | moderate | AX-06 proxy: the 5 `QComboBox` inputs and 24 segment buttons have an accessible name equal to their value ("Circle", "Delta"); the field label is in neither name nor description (WCAG 3.3.2, 4.1.2). `verified` through QAccessible; Narrator `not tested`. | `python tests/independent/m4/ax_lever.py names /tmp/ax06.md` then read the `QComboBox` and `QToolButton` rows | Agent 3 |
| DEF-UV4-06 | moderate | AX-06 proxy: `param-screw-angle-offset` and `param-screw-hole-diameter` have empty accessible name and description. `verified`. | same command, rows `param-screw-*` | Agent 3 |
| DEF-UV4-07 | major | AX-06 proxy: no result carries value, unit and status in one accessible name. `res-card-*` names are empty; `res-*-value` names are the bare number (WCAG 4.1.2). `verified`; Narrator `not tested`. | same command, rows `res-*` | Agent 1 (spec text), Agent 3 |

## Not filed as defects

- U-M4e-2 note "layer bar showed L1 L2 L1 L2": not reproduced. One window loading D08, serpentine, wave, D08 shows
  L1 L2 / L1 to L6 / L1 L2 / L1 L2 (`test_layer_bar_reads_each_designs_layers_when_rows_share_one_window`).
- My first zoom check measured label top-left corners in scene units and reported no labels in view at 8x. Text items
  ignore the view transform, so that instrument was wrong. Measured in viewport pixels, every phase in view has a label
  at 1x, 3x and 8x.
- After "One board per phase" on the six-layer serpentine example the compute fails with
  INVALID_SERPENTINE_COPPER_COUNT and `st-counts` keeps the old "6 layers, 3 phases, 9 vias". Whether a failed compute
  should clear the counts is not in the brief (`unresolved`, for Agent 1).
