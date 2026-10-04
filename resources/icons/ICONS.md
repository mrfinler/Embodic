Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# embodic icon set

49 original monochrome icons drawn for embodic. Licence: project-owned (same licence as embodic). No third-party icon set or icon font is used.

Drawing rules: 24 px grid (`viewBox="0 0 24 24"`), 20 px live area (2 px margin), 1.5 px stroke, round caps and joins, `stroke="currentColor"`, `fill="none"`; small solid marks (nodes, magnets, vector handles) use `fill="currentColor"`. At 16 px the loader replaces `stroke-width="1.5"` with `stroke-width="2"` (renders 1.33 px). Qt does not resolve `currentColor` from the widget palette: the loader replaces `currentColor` with the theme's `icon_color` (tokens.json) for each QIcon mode. Rationale and contact sheet: `docs/phase2/design/design_spec.md` section 7.

Contact sheet: `_contact_sheet.png` (rendered with Qt's own QSvgRenderer at 24 px and 16 px, light and dark).

| Icon | Group | Meaning | Used where |
|---|---|---|---|
| `new.svg` | File | Create a blank design | Toolstrip File > New (Ctrl+N) |
| `open.svg` | File | Open a project file | Toolstrip File > Open (Ctrl+O) |
| `save.svg` | File | Save the project file | Toolstrip File > Save (Ctrl+S) |
| `save-as.svg` | File | Save the project under a new name | Toolstrip File > Save as (Ctrl+Shift+S) |
| `examples.svg` | File | Load a team example parameter set | Toolstrip File > Examples; New design screen |
| `undo.svg` | File | Undo the last change | Quick-access bar (Ctrl+Z) |
| `redo.svg` | File | Redo | Quick-access bar (Ctrl+Shift+Z, Ctrl+Y) |
| `phases.svg` | Design | Phase assignment and connection | Toolstrip Design > Phases; inspector tab Phases |
| `layers.svg` | Design | Copper layers, layer groups, series or parallel | Toolstrip Design > Layers; inspector tab Layers |
| `board.svg` | Design | Board outline and bore; outline DXF | Toolstrip Design > Board; Export > DXF menu > Outline |
| `screws.svg` | Design | Fastener holes; screws DXF | Board & rotor > Fasteners; Export > DXF menu > Screws |
| `rotor.svg` | Design | Rotor and magnets | Toolstrip Design > Rotor; View > Magnets toggle |
| `topology-spiral.svg` | Topology | Spiral coils (concentrated planar spirals) | Toolstrip Topology > Spiral; Coil tab icon when spiral is active |
| `topology-serpentine.svg` | Topology | Serpentine winding (one phase per layer pair) | Toolstrip Topology > Serpentine; Coil tab icon when serpentine is active |
| `topology-wave.svg` | Topology | Interleaved wave winding | Toolstrip Topology > Wave; Coil tab icon when wave is active |
| `connection-star.svg` | Connection | Star connection with neutral | Toolstrip Connection > Star |
| `connection-delta.svg` | Connection | Delta connection | Toolstrip Connection > Delta |
| `connection-open.svg` | Connection | Open phases (six terminals) | Toolstrip Connection > Open |
| `zoom-in.svg` | View | Zoom in | Toolstrip View > Zoom in (+ on the canvas, Ctrl+=) |
| `zoom-out.svg` | View | Zoom out | Toolstrip View > Zoom out (- on the canvas, Ctrl+-) |
| `zoom-fit.svg` | View | Fit the drawing to the view | Toolstrip View > Fit (0 on the canvas, Ctrl+0) |
| `terminals.svg` | View | Zoom to the terminal pads | Toolstrip View > Terminals |
| `labels.svg` | View | Show coil and terminal labels | Toolstrip View > Labels toggle (L on the canvas) |
| `current-flow.svg` | View | Show the direction of positive current | Toolstrip View > Current toggle |
| `theme-light.svg` | View | Switch to the light theme | Toolstrip View > Theme (shown while dark is active) |
| `theme-dark.svg` | View | Switch to the dark theme | Toolstrip View > Theme (shown while light is active) |
| `greyscale.svg` | View | Greyscale and hatching accessibility mode | Toolstrip View > Greyscale toggle (G on the canvas) |
| `export-svg.svg` | Export | Export every layer as SVG | Toolstrip Export > SVG |
| `export-dxf.svg` | Export | Export DXF (complete, outline or screws) | Toolstrip Export > DXF (split button) |
| `report.svg` | Export | Export the PDF design report | Toolstrip Export > Report |
| `export-all.svg` | Export | Export all files and the README into one folder | Toolstrip Export > All files |
| `results.svg` | Verify | Results with traceability | Toolstrip Verify > Results; results tab Summary |
| `drc.svg` | Verify | Design rule check (clearances) | Toolstrip Verify > DRC; results tab DRC |
| `back-emf.svg` | Verify | Back-EMF waveform | Toolstrip Verify > Back-EMF; results tab Back-EMF |
| `torque-speed.svg` | Verify | Torque-speed characteristic | Toolstrip Verify > Torque-speed; results tab Torque-speed |
| `compare.svg` | Verify | Compare with the reference design | Toolstrip Verify > Compare; results tab Compare |
| `tests.svg` | Verify | Run the built-in self-tests | Toolstrip Verify > Tests |
| `guide.svg` | Help | Design guide | Toolstrip Help > Guide (F1) |
| `equations.svg` | Help | Equation register and references | Toolstrip Help > Equations |
| `shortcuts.svg` | Help | Keyboard shortcuts | Toolstrip Help > Shortcuts (Ctrl+/) |
| `settings.svg` | Help | Settings (theme, units, defaults) | Toolstrip Help > Settings (Ctrl+,) |
| `status-verified.svg` | Status | Badge glyph: verified | Result badges, Tests table |
| `status-inferred.svg` | Status | Badge glyph: inferred | Result badges |
| `status-assumption.svg` | Status | Badge glyph: assumption | Input chips, result badges |
| `status-unresolved.svg` | Status | Badge glyph: unresolved (estimate) | Result badges |
| `status-not-tested.svg` | Status | Badge glyph: not tested | Result badges, Tests table |
| `check-pass.svg` | Status | Check passed | DRC list, checks, status bar |
| `check-fail.svg` | Status | Check failed | DRC list, canvas DRC marker, status bar, field errors |
| `check-warn.svg` | Status | Warning | DRC list, checks, inline notices |

The Coil inspector tab has no icon of its own: it shows the icon of the active topology (`topology-spiral`, `topology-serpentine` or `topology-wave`).
