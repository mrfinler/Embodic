"""Theme files, the theme choice and icon recolouring (UI-26, UI-27, AX-08 inputs). Qt-free."""

import copy

import pytest

from embodic.model.vocabulary import Phase
from embodic.ui.theme import CHROME_TOKENS, ThemeName, load_theme, parse_theme, recolour_svg, resolve_theme

# design_spec.md section 3.2 and 3.4 (Agent 1), copied by hand so a token generator bug cannot hide here.
PHASE_COLOURS = {
    "light": {Phase.A: "#941328", Phase.B: "#0032e2", Phase.C: "#579f03"},
    "dark": {Phase.A: "#c43b10", Phase.B: "#005bfc", Phase.C: "#0eb16a"},
}
PHASE_GREYS = {
    "light": {Phase.A: "#262626", Phase.B: "#5e5e5e", Phase.C: "#8a8a8a"},
    "dark": {Phase.A: "#e0e0e0", Phase.B: "#a8a8a8", Phase.C: "#7a7a7a"},
}


@pytest.mark.req("REQ-N-27", "REQ-N-28")
@pytest.mark.parametrize("name", ["light", "dark"])
def test_ui26_both_theme_files_load_with_every_chrome_token_and_the_spec_phase_colours(name):
    """Catches a theme file that lacks a chrome token or swaps a phase colour or hatch angle."""
    tokens = load_theme(name)
    assert tokens.name == name
    assert set(CHROME_TOKENS) <= set(tokens.colours)
    assert {s.phase: s.colour_hex for s in tokens.phases} == PHASE_COLOURS[name]
    assert {s.phase: s.grey_hex for s in tokens.phases} == PHASE_GREYS[name]
    assert [(s.label, s.hatch_deg, s.dash) for s in tokens.phases] == [
        ("A", 0, "solid"),
        ("B", 45, "dash"),
        ("C", 135, "dot"),
    ]
    assert tokens.focus_ring_px >= 2


def _document():
    return {
        "name": "light",
        "colours": {token: "#808080" for token in CHROME_TOKENS},
        "phases": [
            {"phase": p, "colour_hex": "#112233", "grey_hex": "#444444", "hatch_deg": h, "dash": d, "label": p}
            for p, h, d in (("A", 0, "solid"), ("B", 45, "dash"), ("C", 135, "dot"))
        ],
        "focus_ring_px": 2,
        "control_height_px": 32,
    }


@pytest.mark.req("REQ-N-27")
def test_ui26_a_theme_file_missing_a_token_is_refused_by_name():
    """Catches a loader that fills a missing token with a default instead of failing the build."""
    document = _document()
    del document["colours"]["focus-ring"]
    with pytest.raises(KeyError, match="focus-ring"):
        parse_theme(document)


@pytest.mark.req("REQ-N-23")
@pytest.mark.parametrize(
    ("pointer", "bad"),
    [(("phases", 1, "hatch_deg"), 30), (("phases", 2, "dash"), "dashed"), (("colours", "surface"), "white")],
)
def test_ui27_a_hatch_angle_dash_or_colour_outside_the_contract_is_refused(pointer, bad):
    """Catches a loader that accepts a hatch angle other than 0/45/135 or a non-hex colour."""
    document = copy.deepcopy(_document())
    target = document
    for key in pointer[:-1]:
        target = target[key]
    target[pointer[-1]] = bad
    with pytest.raises(ValueError):
        parse_theme(document)


@pytest.mark.req("REQ-N-27")
@pytest.mark.parametrize(
    ("choice", "os_dark", "expected"),
    [
        (ThemeName.LIGHT, True, "light"),
        (ThemeName.DARK, False, "dark"),
        (ThemeName.SYSTEM, True, "dark"),
        (ThemeName.SYSTEM, False, "light"),
    ],
)
def test_ui26_resolve_theme_follows_the_os_only_for_system(choice, os_dark, expected):
    """Catches a resolver that lets the OS override an explicit light or dark choice."""
    assert resolve_theme(choice, os_dark) == expected


@pytest.mark.req("REQ-F-39")
def test_ui25_icon_recolour_writes_the_token_and_thickens_the_stroke_only_at_16px():
    """Catches icons left in currentColor (QtSvg draws them black) or the 16 px stroke rule applied at 24 px."""
    svg = '<svg><path stroke="currentColor" stroke-width="1.5"/></svg>'
    assert recolour_svg(svg, "#f2f2f2", 24) == '<svg><path stroke="#f2f2f2" stroke-width="1.5"/></svg>'
    assert recolour_svg(svg, "#141414", 16) == '<svg><path stroke="#141414" stroke-width="2"/></svg>'
