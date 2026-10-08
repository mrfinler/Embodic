"""Theme tokens, their loader and the light / dark / system choice (interfaces.md section 11). Qt-free."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, get_args

from embodic.model.vocabulary import Phase
from embodic.paths import resource_root

ThemeFile = Literal["light", "dark"]
HatchDeg = Literal[0, 45, 135]
Dash = Literal["solid", "dash", "dot"]

# The chrome tokens the shell paints with (design_spec.md section 3.1); a theme file without one is a build error.
CHROME_TOKENS: tuple[str, ...] = (
    "bg-app",
    "surface",
    "surface-sunken",
    "surface-selected",
    "surface-inverse",
    "canvas",
    "board-fill",
    "divider",
    "grid-line",
    "border-control",
    "border-strong",
    "focus-ring",
    "text-1",
    "text-2",
    "text-3",
    "text-disabled",
    "text-inverse",
)

ICON_STROKE_AT_24 = 'stroke-width="1.5"'
ICON_STROKE_AT_16 = 'stroke-width="2"'


class ThemeName(StrEnum):
    """The user's theme choice; SYSTEM follows the operating system."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True, kw_only=True)
class PhaseStyle:
    """How one phase is drawn: colour, greyscale step, coil-eye hatch, chart dash and letter."""

    phase: Phase
    colour_hex: str  # red / blue / green per theme (D-011), from resources/themes/<theme>.json
    grey_hex: str  # greyscale ladder value
    hatch_deg: HatchDeg  # 0 = no hatch; hatch only inside the coil eye (REQ-N-23)
    dash: Dash
    label: str  # "A", "B", "C"


@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeTokens:
    """One theme file, parsed."""

    name: ThemeFile
    colours: Mapping[str, str]  # chrome tokens, white / grey / black only (REQ-L-04)
    phases: tuple[PhaseStyle, PhaseStyle, PhaseStyle]
    focus_ring_px: int
    control_height_px: int

    def phase_style(self, phase: Phase) -> PhaseStyle:
        """Return the style of one phase."""
        return next(style for style in self.phases if style.phase is phase)


def themes_dir() -> Path:
    """Return the folder that holds the theme files, the style sheets and their chrome glyphs."""
    return resource_root() / "themes"


def _hex(value: object, where: str) -> str:
    if not (isinstance(value, str) and len(value) == 7 and value[0] == "#"):
        raise ValueError(f"{where}: expected a #rrggbb colour, got {value!r}")
    int(value[1:], 16)
    return value.lower()


def _choice(value: object, allowed: tuple[Any, ...], where: str) -> Any:
    if value not in allowed:
        raise ValueError(f"{where}: expected one of {allowed}, got {value!r}")
    return value


def _phase_style(raw: Mapping[str, Any], where: str) -> PhaseStyle:
    return PhaseStyle(
        phase=Phase(raw["phase"]),
        colour_hex=_hex(raw["colour_hex"], f"{where}.colour_hex"),
        grey_hex=_hex(raw["grey_hex"], f"{where}.grey_hex"),
        hatch_deg=_choice(raw["hatch_deg"], get_args(HatchDeg), f"{where}.hatch_deg"),
        dash=_choice(raw["dash"], get_args(Dash), f"{where}.dash"),
        label=str(raw["label"]),
    )


def parse_theme(document: Mapping[str, Any]) -> ThemeTokens:
    """Parse one theme file's JSON data; raise ValueError or KeyError naming the first missing or bad token."""
    name = _choice(document["name"], get_args(ThemeFile), "name")
    colours = document["colours"]
    missing = [token for token in CHROME_TOKENS if token not in colours]
    if missing:
        raise KeyError(f"theme {name!r} lacks the chrome tokens {missing}")
    phases = tuple(_phase_style(raw, f"phases[{i}]") for i, raw in enumerate(document["phases"]))
    if tuple(style.phase for style in phases) != tuple(Phase):
        raise ValueError(f"theme {name!r} must list phases A, B, C in order")
    a, b, c = phases
    return ThemeTokens(
        name=name,
        colours={token: _hex(value, f"colours.{token}") for token, value in colours.items()},
        phases=(a, b, c),
        focus_ring_px=int(document["focus_ring_px"]),
        control_height_px=int(document["control_height_px"]),
    )


def load_theme(name: ThemeFile) -> ThemeTokens:
    """Read resources/themes/<name>.json (Agent 1). Raises on a missing token: the build ships both themes."""
    return parse_theme(json.loads((themes_dir() / f"{name}.json").read_text(encoding="utf-8")))


def resolve_theme(choice: ThemeName, os_prefers_dark: bool) -> ThemeFile:
    """Return the theme file a choice shows."""
    if choice is ThemeName.SYSTEM:
        return "dark" if os_prefers_dark else "light"
    return "dark" if choice is ThemeName.DARK else "light"


def recolour_svg(svg: str, colour_hex: str, size_px: int) -> str:
    """Return icon SVG text drawn in one colour; at 16 px and below the stroke thickens (design_spec.md section 7).

    QtSvg does not take ``currentColor`` from the widget palette, so the loader writes the token colour in.
    """
    text = svg.replace("currentColor", colour_hex)
    return text.replace(ICON_STROKE_AT_24, ICON_STROKE_AT_16) if size_px <= 16 else text
