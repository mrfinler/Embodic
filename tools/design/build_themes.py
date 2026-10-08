"""Generate every theme file from ``resources/themes/tokens.json``.

Usage, from the repository root::

    python tools/design/build_themes.py

Source: ``tokens.json`` > ``themes.<theme>.color``, ``phase_style``, ``control_height_px`` and ``focus_ring_px``.
Writes ``<theme>.qss`` (from ``tools/design/theme_template.qss``), the indicator glyphs in ``<theme>/``, the
``<theme>.json`` ThemeTokens file of interfaces.md section 11, and the derived ``icon_color`` and ``contrast_pairs``
of ``tokens.json``. Running it twice changes nothing. Exit code 1 when a contrast pair fails.
"""

import json
import re
import sys
from pathlib import Path

from contrast import contrast_rows

REPO = Path(__file__).resolve().parents[2]
THEMES = REPO / "resources" / "themes"
TOKENS = THEMES / "tokens.json"
TEMPLATE = Path(__file__).with_name("theme_template.qss")
MODEL = "claude-opus-5-5"
DASH = {"solid": "solid", "dashed": "dash", "dotted": "dot"}
DATA_PREFIXES = ("phase-", "status-")

GLYPHS = {
    "chevron-down.svg": ('<path d="M3 4.5 6 7.5 9 4.5"/>', "text-2", 12),
    "chevron-down-disabled.svg": ('<path d="M3 4.5 6 7.5 9 4.5"/>', "text-disabled", 12),
    "check.svg": ('<path d="M3.5 8.5 6.5 11.5 12.5 4.5"/>', "text-inverse", 16),
}


def render_qss(theme: str, colours: dict[str, str], focus_ring_px: int) -> str:
    """Return the style sheet of one theme: ``@<token>`` becomes its value, ``@dir`` the theme name."""
    head = (
        f'/* embodic {theme} theme. Generated from resources/themes/tokens.json, theme "{theme}". Do not hand-edit.\n'
        f"   Prepared by: Agent 1 (UX/UI) - model: {MODEL}\n"
        "   Variables: each hex value below is a token; the trailing comment names it. Token table:\n"
        + "".join(f"     @{k:<17} {v}\n" for k, v in colours.items())
        + '   Loader contract: QDir.addSearchPath("theme", <resources/themes>) before setStyleSheet, so\n'
        "   url(theme:<theme>/<glyph>.svg) resolves. Variant hooks are dynamic properties (class, status,\n"
        "   provenance, state, invalid, stale); after changing one call style().unpolish(w); style().polish(w). */\n"
    )
    out = []
    for line in TEMPLATE.read_text(encoding="utf-8").strip().splitlines():
        used: list[str] = []

        def sub(m: re.Match[str], used: list[str] = used) -> str:
            name = m.group(1)
            if name == "dir":
                return theme
            used.append(name)
            return f"{focus_ring_px}px" if name == "focus-ring-px" else colours[name]

        text = re.sub(r"@([a-z0-9-]+)", sub, line)
        if used:
            text += " /* " + ", ".join(dict.fromkeys(used)) + " */"
        out.append(text)
    return head + "\n".join(out) + "\n"


def theme_tokens(theme: str, tokens: dict) -> dict:
    """Return the ThemeTokens of interfaces.md section 11 for one theme.

    ``colours`` holds the chrome tokens only (white, grey and black, REQ-L-04). Phase colours move into ``phases``;
    status colours stay in the QSS because ThemeTokens has no field for them.
    """
    c = tokens["themes"][theme]["color"]
    phases = []
    for phase, style in tokens["phase_style"].items():
        key = f"phase-{phase.lower()}"
        phases.append(
            {
                "phase": phase,
                "colour_hex": c[key],
                "grey_hex": c[f"{key}-grey"],
                "hatch_deg": style["hatch_deg"] or 0,
                "dash": DASH[style["line"]],
                "label": style["label"],
            }
        )
    return {
        "name": theme,
        "colours": {k: v for k, v in c.items() if not k.startswith(DATA_PREFIXES)},
        "phases": phases,
        "focus_ring_px": tokens["focus_ring_px"],
        "control_height_px": tokens["control_height_px"],
    }


def glyph_svg(body: str, colour: str, size: int) -> str:
    """Return one indicator glyph drawn in a fixed theme colour (QSS ``image:`` cannot recolour an SVG)."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'fill="none" stroke="{colour}" stroke-width="1.75" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>\n'
    )


def write_if_changed(path: Path, text: str) -> None:
    """Write ``text`` only when it differs, so a second run leaves file times alone too."""
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def main() -> int:
    """Regenerate every theme file; return 1 when a contrast pair fails."""
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    colours = {name: t["color"] for name, t in tokens["themes"].items()}
    for theme, c in colours.items():
        tokens["themes"][theme]["icon_color"] = {
            "normal": c["text-1"],
            "disabled": c["text-disabled"],
            "checked": c["text-1"],
        }
        write_if_changed(THEMES / f"{theme}.qss", render_qss(theme, c, tokens["focus_ring_px"]))
        write_if_changed(THEMES / f"{theme}.json", json.dumps(theme_tokens(theme, tokens), indent=1) + "\n")
        glyph_dir = THEMES / theme
        glyph_dir.mkdir(exist_ok=True)
        for name, (body, token, size) in GLYPHS.items():
            write_if_changed(glyph_dir / name, glyph_svg(body, c[token], size))
    rows = contrast_rows(colours)
    tokens["contrast_pairs"] = rows
    write_if_changed(TOKENS, json.dumps(tokens, indent=1, ensure_ascii=False) + "\n")
    fails = [r for r in rows if not r["pass"]]
    print(f"themes: {', '.join(colours)}; contrast pairs: {len(rows)}, fails: {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
