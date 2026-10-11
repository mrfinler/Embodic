# Open a design and edit it

## Sub-features

Empty session (`empty-state`), Examples gallery (`dlg-examples`, `examples-list`, `btn-load-example`), New design
(`dlg-new-design`, `param-design-name`, `param-topology-*`, `example-picker`, `btn-create-design`), inspector tabs
(`tab-coil`, `tab-phases`, `tab-layers`, `tab-board`), provenance chips (`<widget_id>-prov`), required-field bar
(`btn-first-missing`), screw patterns (`screw-table`, `btn-screw-add`, `btn-screw-remove`).

## How to get to it (user POV)

Start the app: the centre offers New design and Examples. Pick an example or create a design, then type into a field
of the inspector and press Enter. The chip next to the field turns from "example" to "user".

## Driving it with pytest-qt

`test_walkthroughs.py` `_open_design` clicks `btn-empty-examples` or `btn-empty-new`; `support.type_value` opens the
field's tab, selects all, types and presses Enter. Prove it with the design document: `flatten(design_document(
window.session.current_outcome().design))[pointer]` equals the typed value, and every edited chip reads "user".

## Gotchas

A typed value equal to the example's value turns the chip back to "example" (UI-22), so type values no example holds.
A stretched QCheckBox toggles only on its indicator and text, at its left end. `spiral_12c16p_default` and
`spiral_12c14p` have no screw pattern; `wave_16p_example` has one.
