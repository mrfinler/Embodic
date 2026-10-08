"""Generate the embodic icon set: ``resources/icons/*.svg`` and ``resources/icons/ICONS.md``.

Usage, from the repository root::

    python tools/design/build_icons.py

Every icon is drawn here to design_spec.md section 7 (24 px grid, 1.5 px ``currentColor`` stroke). Running it twice
changes nothing. Then run ``render_sheet.py`` for the contact sheet and ``check_icons.py`` for the rules.
"""

import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "resources" / "icons"
MODEL = "claude-opus-5-5"
HEAD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
)
DOC = '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/>'


def dot(x: float, y: float, r: float = 1.4) -> str:
    """Return a small solid mark (node, handle)."""
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="currentColor" stroke="none"/>'


def ring(x: float, y: float, r: float = 1.6) -> str:
    """Return a small open terminal ring."""
    return f'<circle cx="{x}" cy="{y}" r="{r}"/>'


# name: (group, meaning, used where, body)
ICONS = {
    "new": ("File", "Create a blank design", "Toolstrip File > New (Ctrl+N)", DOC + '<path d="M12 11v6M9 14h6"/>'),
    "open": (
        "File",
        "Open a project file",
        "Toolstrip File > Open (Ctrl+O)",
        '<path d="M3 18V5h6l2 2h7v3"/><path d="M3 18l3-8h15l-3 8z"/>',
    ),
    "save": (
        "File",
        "Save the project file",
        "Toolstrip File > Save (Ctrl+S)",
        '<path d="M5 4h11l3 3v13H5z"/><path d="M8 4v5h7V4"/><path d="M8 20v-6h8v6"/>',
    ),
    "save-as": (
        "File",
        "Save the project under a new name",
        "Toolstrip File > Save as (Ctrl+Shift+S)",
        '<path d="M12 20H5V4h11l3 3v4"/><path d="M8 4v5h7V4"/><path d="M14 21l.6-2.6 5.4-5.4 2 2-5.4 5.4z"/>',
    ),
    "examples": (
        "File",
        "Load a team example parameter set",
        "Toolstrip File > Examples; New design screen",
        '<rect x="3.5" y="3.5" width="7" height="7" rx="1"/><rect x="13.5" y="3.5" width="7" height="7" rx="1"/>'
        '<rect x="3.5" y="13.5" width="7" height="7" rx="1"/><rect x="13.5" y="13.5" width="7" height="7" rx="1"/>',
    ),
    "undo": (
        "File",
        "Undo the last change",
        "Quick-access bar (Ctrl+Z)",
        '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    ),
    "redo": (
        "File",
        "Redo",
        "Quick-access bar (Ctrl+Shift+Z, Ctrl+Y)",
        '<path d="M15 14l5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
    ),
    "phases": (
        "Design",
        "Phase assignment and connection",
        "Toolstrip Design > Phases; inspector tab Phases",
        '<path d="M3 5.5c1.5-2.2 3-2.2 4.5 0s3 2.2 4.5 0 3-2.2 4.5 0 3 2.2 4.5 0"/><path d="M3 12c1.5-2.2 3-2.2 4.5 '
        '0s3 2.2 4.5 0 3-2.2 4.5 0 3 2.2 4.5 0"/><path d="M3 18.5c1.5-2.2 3-2.2 4.5 0s3 2.2 4.5 0 3-2.2 4.5 0 3 2.2 '
        '4.5 0"/>',
    ),
    "layers": (
        "Design",
        "Copper layers, layer groups, series or parallel",
        "Toolstrip Design > Layers; inspector tab Layers",
        '<path d="M12 3.5 21 8l-9 4.5L3 8z"/><path d="M3 12l9 4.5 9-4.5"/><path d="M3 16l9 4.5 9-4.5"/>',
    ),
    "board": (
        "Design",
        "Board outline and bore; outline DXF",
        "Toolstrip Design > Board; Export > DXF menu > Outline",
        '<path d="M8.3 3h7.4L21 8.3v7.4L15.7 21H8.3L3 15.7V8.3z"/><circle cx="12" cy="12" r="3.5"/>',
    ),
    "screws": (
        "Design",
        "Fastener holes; screws DXF",
        "Board & rotor > Fasteners; Export > DXF menu > Screws",
        '<path d="M6.5 3.5h11v3.5h-11z"/><path d="M9.5 7v11l2.5 2.5 2.5-2.5V7"/>'
        '<path d="M9.5 11l5-1.5M9.5 14.5l5-1.5M9.5 18l5-1.5"/>',
    ),
    "rotor": (
        "Design",
        "Rotor and magnets",
        "Toolstrip Design > Rotor; View > Magnets toggle",
        '<path d="M5 3v9a7 7 0 0 0 14 0V3h-4.5v9a2.5 2.5 0 0 1-5 0V3z"/><path d="M5 7h4.5M14.5 7H19"/>',
    ),
    "topology-spiral": (
        "Topology",
        "Spiral coils (concentrated planar spirals)",
        "Toolstrip Topology > Spiral; Coil tab icon when spiral is active",
        '<path d="M3 4h18l-5 16H8L4.6 9.3h12.7l-2.6 7.2H9.3L7.9 12.4H12"/>' + dot(12, 12.4, 1.6),
    ),
    "topology-serpentine": (
        "Topology",
        "Serpentine winding (one phase per layer pair)",
        "Toolstrip Topology > Serpentine; Coil tab icon when serpentine is active",
        '<path d="M3 19V5h4.5v14H12V5h4.5v14H21V5"/>',
    ),
    "topology-wave": (
        "Topology",
        "Interleaved wave winding",
        "Toolstrip Topology > Wave; Coil tab icon when wave is active",
        '<path d="M2.5 16.5h3l3-9h3l3 9h3l3-9h1.5"/>',
    ),
    "connection-star": (
        "Connection",
        "Star connection with neutral",
        "Toolstrip Connection > Star",
        '<path d="M12 12V5.5M12 12l5.6 3.3M12 12l-5.6 3.3"/>'
        + dot(12, 12, 1.8)
        + ring(12, 3.9)
        + ring(19, 16.1)
        + ring(5, 16.1),
    ),
    "connection-delta": (
        "Connection",
        "Delta connection",
        "Toolstrip Connection > Delta",
        '<path d="M10.4 6.6 5.6 15.1M13.6 6.6l4.8 8.5M7.2 18h9.6"/>' + ring(12, 4) + ring(19, 18) + ring(5, 18),
    ),
    "connection-open": (
        "Connection",
        "Open phases (six terminals)",
        "Toolstrip Connection > Open",
        '<path d="M6 6.5v11M12 6.5v11M18 6.5v11"/>' + "".join(ring(x, y) for x in (6, 12, 18) for y in (4.9, 19.1)),
    ),
    "zoom-in": (
        "View",
        "Zoom in",
        "Toolstrip View > Zoom in (+ on the canvas, Ctrl+=)",
        '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.3 15.3 20.5 20.5M10.5 7.5v6M7.5 10.5h6"/>',
    ),
    "zoom-out": (
        "View",
        "Zoom out",
        "Toolstrip View > Zoom out (- on the canvas, Ctrl+-)",
        '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.3 15.3 20.5 20.5M7.5 10.5h6"/>',
    ),
    "zoom-fit": (
        "View",
        "Fit the drawing to the view",
        "Toolstrip View > Fit (0 on the canvas, Ctrl+0)",
        '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/><rect x="8.5" y="8.5" width="7" height="7" rx="1"/>',
    ),
    "terminals": (
        "View",
        "Zoom to the terminal pads",
        "Toolstrip View > Terminals",
        '<path d="M2.5 20.5c6-3 13-3 19 0"/><path d="M5.5 12v6.6M12 12v5.6M18.5 12v6.6"/>'
        '<rect x="3.5" y="6" width="4" height="6" rx=".5"/><rect x="10" y="6" width="4" height="6" rx=".5"/><rect '
        'x="16.5" y="6" width="4" height="6" rx=".5"/>',
    ),
    "labels": (
        "View",
        "Show coil and terminal labels",
        "Toolstrip View > Labels toggle (L on the canvas)",
        '<path d="M3.5 12.5V4h8.5l9 9-8.5 8.5z"/>' + dot(8, 8.5, 1.5),
    ),
    "current-flow": (
        "View",
        "Show the direction of positive current",
        "Toolstrip View > Current toggle",
        '<rect x="4" y="5" width="16" height="14" rx="2.5"/><path d="M10.5 2.8 12.7 5l-2.2 2.2M13.5 16.8 11.3 19l2.2 '
        '2.2"/>',
    ),
    "theme-light": (
        "View",
        "Switch to the light theme",
        "Toolstrip View > Theme (shown while dark is active)",
        '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2'
        'M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    ),
    "theme-dark": (
        "View",
        "Switch to the dark theme",
        "Toolstrip View > Theme (shown while light is active)",
        '<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.8 6.8 0 0 0 10.5 10.5z"/>',
    ),
    "greyscale": (
        "View",
        "Greyscale and hatching accessibility mode",
        "Toolstrip View > Greyscale toggle (G on the canvas)",
        '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17M12 8l6.3-3M12 12.5l8.3-4M12 17l8-3.9"/>',
    ),
    "export-svg": (
        "Export",
        "Export every layer as SVG",
        "Toolstrip Export > SVG",
        DOC
        + '<path d="M9 17.5c0-4 6-2.5 6-6.5"/>'
        + '<rect x="7.8" y="16.3" width="2.4" height="2.4" fill="currentColor" stroke="none"/>'
        + '<rect x="13.8" y="9.8" width="2.4" height="2.4" fill="currentColor" stroke="none"/>',
    ),
    "export-dxf": (
        "Export",
        "Export DXF (complete, outline or screws)",
        "Toolstrip Export > DXF (split button)",
        DOC + '<circle cx="12" cy="14" r="2.6"/><path d="M12 9.5v9M7.5 14h9"/>',
    ),
    "report": (
        "Export",
        "Export the PDF design report",
        "Toolstrip Export > Report",
        DOC + '<path d="M9 18v-2.5M12 18v-6M15 18v-4"/><path d="M9 9h3"/>',
    ),
    "export-all": (
        "Export",
        "Export all files and the README into one folder",
        "Toolstrip Export > All files",
        '<path d="M3 19V5h6l2 2h10v12z"/><path d="M12 10v6.5M9.3 13.8 12 16.5l2.7-2.7"/>',
    ),
    "results": (
        "Verify",
        "Results with traceability",
        "Toolstrip Verify > Results; results tab Summary",
        '<path d="M4 4v16h16"/><path d="M7.5 15l3.5-4.5 3 3 5-6.5"/>',
    ),
    "drc": (
        "Verify",
        "Design rule check (clearances)",
        "Toolstrip Verify > DRC; results tab DRC",
        '<path d="M4.5 4v16M19.5 4v16"/><path d="M8 12h8M10 9.8 7.8 12l2.2 2.2M14 9.8l2.2 2.2-2.2 2.2"/>',
    ),
    "back-emf": (
        "Verify",
        "Back-EMF waveform",
        "Toolstrip Verify > Back-EMF; results tab Back-EMF",
        '<path d="M3 12h18" stroke-dasharray="1.5 2.5"/><path d="M3 12c2.5-8.5 5-8.5 7.5 0s5 8.5 7.5 0c.9-3 2-4.6 '
        '3-4.6"/>',
    ),
    "torque-speed": (
        "Verify",
        "Torque-speed characteristic",
        "Toolstrip Verify > Torque-speed; results tab Torque-speed",
        '<path d="M4 4v16h16"/><path d="M7 7.5l12 9"/><path d="M7 17c3.5-.5 6-3.5 7.5-8"/>',
    ),
    "compare": (
        "Verify",
        "Compare with the reference design",
        "Toolstrip Verify > Compare; results tab Compare",
        '<path d="M4 8h12M13 5l3 3-3 3"/><path d="M20 16H8M11 13l-3 3 3 3"/>',
    ),
    "tests": (
        "Verify",
        "Run the built-in self-tests",
        "Toolstrip Verify > Tests",
        '<path d="M9 3h6M10 3v6.2L4.6 19a1.3 1.3 0 0 0 1.1 2h12.6a1.3 1.3 0 0 0 1.1-2L14 9.2V3"/><path d="M7.2 '
        '15h9.6"/>',
    ),
    "guide": (
        "Help",
        "Design guide",
        "Toolstrip Help > Guide (F1)",
        '<path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5z"/><path '
        'd="M12 6.5v13"/>',
    ),
    "equations": (
        "Help",
        "Equation register and references",
        "Toolstrip Help > Equations",
        '<path d="M3 13h3l3 7 5-16h7"/>',
    ),
    "shortcuts": (
        "Help",
        "Keyboard shortcuts",
        "Toolstrip Help > Shortcuts (Ctrl+/)",
        '<rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6 10h1M9.5 10h1M13 10h1M16.5 10h1M7.5 14h9"/>',
    ),
    "settings": (
        "Help",
        "Settings (theme, units, defaults)",
        "Toolstrip Help > Settings (Ctrl+,)",
        '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    ),
    "status-verified": (
        "Status",
        "Badge glyph: verified",
        "Result badges, Tests table",
        '<path d="M5 12.5 10 17.5 19 7"/>',
    ),
    "status-inferred": (
        "Status",
        "Badge glyph: inferred",
        "Result badges",
        '<path d="M5 9.5c2.3-2 4.7-2 7 0s4.7 2 7 0M5 15c2.3-2 4.7-2 7 0s4.7 2 7 0"/>',
    ),
    "status-assumption": (
        "Status",
        "Badge glyph: assumption",
        "Input chips, result badges",
        '<path d="M12 4l8 8-8 8-8-8z"/>',
    ),
    "status-unresolved": (
        "Status",
        "Badge glyph: unresolved (estimate)",
        "Result badges",
        '<path d="M9 9a3 3 0 1 1 4.5 2.6c-1 .6-1.5 1.3-1.5 2.4v.5"/><path d="M12 18.3v.7"/>',
    ),
    "status-not-tested": (
        "Status",
        "Badge glyph: not tested",
        "Result badges, Tests table",
        '<circle cx="12" cy="12" r="7"/>',
    ),
    "check-pass": (
        "Status",
        "Check passed",
        "DRC list, checks, status bar",
        '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
    ),
    "check-fail": (
        "Status",
        "Check failed",
        "DRC list, canvas DRC marker, status bar, field errors",
        '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
    ),
    "check-warn": (
        "Status",
        "Warning",
        "DRC list, checks, inline notices",
        '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5M12 17.3v.7"/>',
    ),
}


def main() -> int:
    """Write every icon and ICONS.md."""
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (_, _, _, body) in ICONS.items():
        (OUT / f"{name}.svg").write_text(HEAD + body + "</svg>\n", encoding="utf-8")
    lines = [
        f"Prepared by: Agent 1 (UX/UI Expert Designer) - model: {MODEL}",
        "",
        "# embodic icon set",
        "",
        f"{len(ICONS)} original monochrome icons drawn for embodic. Licence: project-owned (same licence as embodic). "
        "No third-party icon set or icon font is used.",
        "",
        'Drawing rules: 24 px grid (`viewBox="0 0 24 24"`), 20 px live area (2 px margin), 1.5 px stroke, round caps '
        "and joins, "
        '`stroke="currentColor"`, `fill="none"`; small solid marks (nodes, magnets, vector handles) use '
        '`fill="currentColor"`. '
        'At 16 px the loader replaces `stroke-width="1.5"` with `stroke-width="2"` (renders 1.33 px). '
        "Qt does not resolve `currentColor` from the widget palette: the loader replaces `currentColor` with the "
        "theme's "
        "`icon_color` (tokens.json) for each QIcon mode. Rationale and contact sheet: "
        "`docs/phase2/design/design_spec.md` section 7.",
        "",
        "Contact sheet: `_contact_sheet.png` (rendered with Qt's own QSvgRenderer at 24 px and 16 px, light and dark).",
        "",
        "| Icon | Group | Meaning | Used where |",
        "|---|---|---|---|",
    ]
    lines += [f"| `{n}.svg` | {g} | {m} | {u} |" for n, (g, m, u, _) in ICONS.items()]
    lines += [
        "",
        "The Coil inspector tab has no icon of its own: it shows the icon of the active topology "
        "(`topology-spiral`, `topology-serpentine` or `topology-wave`).",
        "",
    ]
    (OUT / "ICONS.md").write_text("\n".join(lines), encoding="utf-8")
    print(len(ICONS), "icons written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
