"""AX-01, AX-09 and the contrast part of AX-08: WCAG 2.2 contrast of every theme colour pair the app draws.

Usage: python tools/contrast_check.py    (prints one line per pair, exits 1 when any pair is below its minimum)

Colours come from resources/themes/light.json and dark.json through embodic.ui.theme.load_theme. The pair list is
Agent 1's ``contrast_pairs`` in resources/themes/tokens.json (which token is drawn on which) plus the pairs the shell
adds: toolstrip icons on their backgrounds (AX-09), the focus ring on the canvas and on a checked button (AX-03), and
phase letters on the canvas and the board fill. Formula: WCAG 2.2 relative luminance and contrast ratio
(https://www.w3.org/TR/WCAG22/#dfn-relative-luminance, SC 1.4.3 and 1.4.11). Agent 1's recorded ratio is compared with
the computed one wherever both used the same colours. The palette validator part of AX-08 (colour-vision distances,
greyscale ladder) is Agent 1's result in docs/phase2/design/design_spec.md sections 3.2 and 3.4; it is cited, not rerun.
"""

import json
import re
import sys
from dataclasses import dataclass

from embodic.paths import resource_root
from embodic.ui.theme import ThemeTokens, load_theme

TEXT_MIN = 4.5
GRAPHIC_MIN = 3.0
RECORDED_TOLERANCE = 0.01  # Agent 1 rounded ratios to two decimals

# The shell's own pairs: (fg token, bg token, minimum, kind, why). Icons use text-1: tokens.json icon_color.normal.
SHELL_PAIRS = (
    ("text-1", "surface", GRAPHIC_MIN, "icon", "AX-09 toolstrip icon on the toolstrip"),
    ("text-1", "surface-sunken", GRAPHIC_MIN, "icon", "AX-09 toolstrip icon on a hovered button"),
    ("text-1", "surface-selected", GRAPHIC_MIN, "icon", "AX-09 toolstrip icon on a checked button"),
    ("focus-ring", "canvas", GRAPHIC_MIN, "non-text", "AX-03 focus ring on the geometry canvas"),
    ("focus-ring", "surface-selected", GRAPHIC_MIN, "non-text", "AX-03 focus ring on a checked button"),
    ("text-1", "canvas", TEXT_MIN, "text", "phase letters on the canvas"),
    ("text-1", "board-fill", TEXT_MIN, "text", "phase letters on the board fill"),
)
_COLOUR_ATTRIBUTE = re.compile(r'(?:stroke|fill|color)\s*=\s*"([^"]+)"')


@dataclass(frozen=True)
class Pair:
    """One foreground colour drawn on one background in one theme."""

    theme: str
    fg: str
    bg: str
    fg_hex: str
    bg_hex: str
    minimum: float
    kind: str
    source: str
    recorded: float | None


def relative_luminance(hex_colour: str) -> float:
    """Return the WCAG relative luminance of a #rrggbb colour."""
    channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Return the WCAG contrast ratio of two colours (1 to 21)."""
    lighter, darker = sorted((relative_luminance(fg_hex), relative_luminance(bg_hex)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def token_hex(tokens: ThemeTokens, token: str) -> str:
    """Return a token's colour from a theme file: a chrome token, or phase-x / phase-x-grey."""
    if token.startswith("phase-"):
        letter, _, grey = token.removeprefix("phase-").partition("-")
        style = next(s for s in tokens.phases if s.phase.value.lower() == letter)
        return style.grey_hex if grey else style.colour_hex
    return tokens.colours[token]


def pairs() -> list[Pair]:
    """Return every pair to check, in both themes."""
    declared = json.loads((resource_root() / "themes" / "tokens.json").read_text(encoding="utf-8"))["contrast_pairs"]
    themes = {name: load_theme(name) for name in ("light", "dark")}
    found = []
    for row in declared:
        tokens = themes[row["theme"]]
        fg_hex, bg_hex = token_hex(tokens, row["fg"]), token_hex(tokens, row["bg"])
        same = (fg_hex, bg_hex) == (row["fg_hex"].lower(), row["bg_hex"].lower())
        recorded = float(row["ratio"]) if same else None
        minimum = float(row["min"])
        found.append(
            Pair(row["theme"], row["fg"], row["bg"], fg_hex, bg_hex, minimum, row["kind"], "tokens.json", recorded)
        )
    for name, tokens in themes.items():
        for fg, bg, minimum, kind, why in SHELL_PAIRS:
            found.append(Pair(name, fg, bg, token_hex(tokens, fg), token_hex(tokens, bg), minimum, kind, why, None))
    return found


def icons_not_in_current_colour() -> list[str]:
    """Return 'file: value' for every icon colour that is not currentColor or none (it would not follow the theme)."""
    bad = []
    for path in sorted((resource_root() / "icons").glob("*.svg")):
        for value in _COLOUR_ATTRIBUTE.findall(path.read_text(encoding="utf-8")):
            if value not in ("currentColor", "none"):
                bad.append(f"{path.name}: {value}")
    return bad


def main() -> int:
    """Print every pair with its ratio and verdict; return 0 when all pass."""
    failures = 0
    for p in pairs():
        ratio = contrast_ratio(p.fg_hex, p.bg_hex)
        verdict = "exempt" if p.minimum == 0 else ("PASS" if ratio >= p.minimum else "FAIL")
        drift = p.recorded is not None and abs(ratio - p.recorded) > RECORDED_TOLERANCE
        failures += verdict == "FAIL" or drift
        note = f" recorded {p.recorded:.2f} DIFFERS" if drift else ""
        print(
            f"{verdict:6} {p.theme:5} {p.fg:16} on {p.bg:16} {p.fg_hex} / {p.bg_hex} {ratio:6.2f}:1 "
            f"(min {p.minimum:.1f}, {p.kind}; {p.source}){note}"
        )
    bad_icons = icons_not_in_current_colour()
    for line in bad_icons:
        print(f"FAIL   icon colour not themable: {line}")
    failures += len(bad_icons)
    print(f"{failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
