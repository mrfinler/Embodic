# Keyboard and target size

## Sub-features

AX-02 keyboard-only scenario, AX-04 target size (24 x 24 px; check box and radio click rectangles 32 px), UI-09
scaling at 100, 150 and 200 %, the focus ring of every checklist Focus cell.

## How to get to it (user POV)

Tab moves through the window; Space or Enter activates; arrow keys move between tabs; F5 recomputes; Ctrl+E exports.

## Driving it with pytest-qt

`support.press` sends a key to `QApplication.focusWidget()`; `support.tab_until` presses Tab until a predicate holds.
After a dialog closes, re-activate the main window (offscreen Qt does not). AX-04 walks the screens and lists every
undersized target; open defects are strict xfails `DEF-M4e2-01` to `03`. UI-09 runs the capture lever in a new
process per `QT_SCALE_FACTOR`.

## Gotchas

`QT_SCALE_FACTOR` must be set before the QApplication exists, hence the subprocess. Clipped text at 150 % and 200 % is
`not tested` by a machine; Agent 1 reviews `build/verify/<timestamp>/scaling/`.
