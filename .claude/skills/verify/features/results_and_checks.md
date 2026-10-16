# Results, DRC and charts

## Sub-features

Results cards (`res-<key>-value`, `-eq`, `-asm`, `-how-toggle`, `-how`), status filters (`results-filter-*`), DRC tab
(`tab-drc`, `drc-summary`, `drc-table`, `btn-drc-locate`), rail cards (`rail-inputs`, `rail-drc`), charts
(`chart-backemf`, `chart-torque-speed`), Compare (`btn-set-reference`, `compare-table`), status bar (`st-drc`).

## How to get to it (user POV)

After a compute the Results tab shows cards; "How was this computed" opens the derivation; the DRC tab lists
failures with Clearance and Required; Locate zooms the canvas to the marker.

## Driving it with pytest-qt

`run_action(qtbot, window, "act-compute")` recomputes; click `res-r-phase-how-toggle` and assert `res-r-phase-how`
is visible; select `tab-drc` in `results-tabs` and read `drc-summary` ("DRC: ..."). For failures, type a spacing
rule above the copper's (`param-min-space` 3 on `spiral_12c16p_default`), as capture row S25 does.

## Gotchas

At 960 x 540 the rail becomes the Key results tab and the canvas the Drawing tab (compact height under 620 px).
`wave_16p_example` has 186 DRC failures, so its export asks for confirmation (`dlg-export-confirm`).
