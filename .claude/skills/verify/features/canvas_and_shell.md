# Canvas and shell

## Sub-features

Toolstrip tabs and actions (`toolstrip-tabs`, `act-*`), canvas (`fig-canvas`, legend, labels, greyscale through
`act-greyscale`), layer toggles (`layer-L1`, `layer-L2`), board picker (`board-picker`), centre split and the Drawing
tab, error dialog (`dlg-error`), status bar (`statusbar`).

## How to get to it (user POV)

Load any example: the canvas draws the coils in phase colours with a label per coil; the View tab holds Theme,
Greyscale and Fit.

## Driving it with pytest-qt

Capture rows S02 to S10, S36, S38 and S41 in `capture_acceptance.py`; `support.run_action` clicks a toolstrip action
after opening its tab. The canvas zooms with `window.canvas.zoom_by(3)` and fits with `window.canvas.fit_view()`.

## Gotchas

A toolstrip button on a hidden tab is not visible, so open its tab first. Offscreen Qt draws no tooltip (S09).
