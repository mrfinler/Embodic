"""WCAG 2.x contrast of every text and background pair in design_spec.md appendix A.

Usage, from the repository root::

    python tools/design/contrast.py

Reads ``resources/themes/tokens.json`` > ``themes.<theme>.color``, prints the appendix A table and exits 1 when a pair
is below its minimum (4.5:1 text, 3:1 non-text, WCAG 2.2 SC 1.4.3 and 1.4.11). ``build_themes.py`` imports ``PAIRS``
and ``contrast_rows`` to write ``tokens.json`` > ``contrast_pairs``.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOKENS = REPO / "resources" / "themes" / "tokens.json"

_SURFACES = ("surface", "bg-app", "surface-sunken", "surface-selected")
PAIRS: tuple[tuple[str, str, float, str], ...] = (
    *((t, b, 4.5, "text") for t in ("text-1", "text-2", "text-3") for b in _SURFACES),
    ("text-inverse", "surface-inverse", 4.5, "text"),
    *(
        (s, b, 4.5, "text")
        for s in ("status-pass", "status-fail", "status-warn")
        for b in ("surface", "surface-sunken")
    ),
    *(
        (c, b, 3.0, "non-text")
        for c in ("border-control", "focus-ring")
        for b in ("surface", "bg-app", "surface-sunken")
    ),
    *(
        (p, b, 3.0, "non-text")
        for p in ("phase-a", "phase-b", "phase-c", "phase-a-grey", "phase-b-grey", "phase-c-grey")
        for b in ("canvas", "board-fill")
    ),
    ("text-disabled", "surface", 0.0, "exempt (disabled, SC 1.4.3)"),
)


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    """Return the WCAG 2.x relative luminance of a ``#rrggbb`` colour."""
    h = hex_colour.lstrip("#")
    r, g, b = (_linear(int(h[i : i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: str, bg: str) -> float:
    """Return the contrast ratio of two ``#rrggbb`` colours, 1.0 to 21.0."""
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def contrast_rows(colours: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    """Return one row per theme and pair of ``PAIRS``, in the order ``tokens.json`` stores them."""
    rows: list[dict[str, object]] = []
    for theme, c in colours.items():
        for fg, bg, need, kind in PAIRS:
            r = ratio(c[fg], c[bg])
            rows.append(
                {
                    "theme": theme,
                    "fg": fg,
                    "bg": bg,
                    "fg_hex": c[fg],
                    "bg_hex": c[bg],
                    "ratio": round(r, 2),
                    "min": need,
                    "kind": kind,
                    "pass": r >= need,
                }
            )
    return rows


def main() -> int:
    """Print the appendix A table; return 1 when a pair fails."""
    themes = json.loads(TOKENS.read_text(encoding="utf-8"))["themes"]
    rows = contrast_rows({name: t["color"] for name, t in themes.items()})
    print("| Theme | Foreground | Background | Ratio | Min | Result |\n|---|---|---|---|---|---|")
    for r in rows:
        print(
            f"| {r['theme']} | `{r['fg']}` {r['fg_hex']} | `{r['bg']}` {r['bg_hex']} | {r['ratio']:.2f}:1 | "
            f"{r['min']:g} | {'pass' if r['pass'] else 'FAIL'} |"
        )
    fails = [r for r in rows if not r["pass"]]
    print(f"\npairs: {len(rows)}, fails: {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
