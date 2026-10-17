"""REQ-L-04: UI chrome is white, grey or black in both themes; only phase and status tokens are saturated (D-011)."""

import json
from pathlib import Path

import pytest

THEME_FOLDER = Path(__file__).resolve().parents[4] / "resources" / "themes"
THEMES = ("light", "dark")


def rgb(token: str) -> tuple[int, int, int]:
    """Return the red, green and blue bytes of a #rrggbb token."""
    assert len(token) == 7 and token.startswith("#"), token
    return int(token[1:3], 16), int(token[3:5], 16), int(token[5:7], 16)


def is_grey(token: str) -> bool:
    """Return True for white, grey and black: all three bytes are equal."""
    red, green, blue = rgb(token)
    return red == green == blue


def tokens_of(theme: dict) -> tuple[dict[str, str], dict[str, str]]:
    """Return the chrome tokens and the tokens that may be saturated: status colours and the A, B, C phase colours."""
    colours = theme["colours"]
    allowed = {name: value for name, value in colours.items() if name.startswith("status-")}
    allowed |= {f"phase-{p['phase']}": p["colour_hex"] for p in theme["phases"]}
    chrome = {name: value for name, value in colours.items() if not name.startswith("status-")}
    chrome |= {f"phase-{p['phase']}-grey": p["grey_hex"] for p in theme["phases"]}
    return chrome, allowed


def tinted_chrome(theme: dict) -> list[str]:
    """Return the names of the chrome tokens that are not white, grey or black."""
    return sorted(name for name, value in tokens_of(theme)[0].items() if not is_grey(value))


def theme_file(name: str) -> dict:
    """Read one theme file of resources/themes."""
    return json.loads((THEME_FOLDER / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.req("REQ-L-04")
@pytest.mark.parametrize("name", THEMES)
def test_every_chrome_token_has_equal_red_green_and_blue(name):
    """Catches a tinted chrome colour, for example a blue-grey surface that reads as a fourth accent."""
    assert tinted_chrome(theme_file(name)) == []


@pytest.mark.req("REQ-L-04")
@pytest.mark.parametrize("name", THEMES)
def test_the_only_saturated_colours_are_the_phase_and_the_status_tokens(name):
    """Catches a phase or status token that is grey (no colour to reserve) next to a chrome that is not."""
    chrome, allowed = tokens_of(theme_file(name))
    assert sorted(allowed) == ["phase-A", "phase-B", "phase-C", "status-fail", "status-pass", "status-warn"]
    assert not [n for n, v in allowed.items() if is_grey(v)], "an allowed token is grey, so the allowance is idle"
    assert chrome


@pytest.mark.req("REQ-L-04")
def test_a_planted_tinted_chrome_token_is_found_and_a_planted_grey_one_is_not():
    """Control. Catches a check that cannot fail: #f7f7f8 is one byte off grey, #f7f7f7 is grey."""
    theme = theme_file("light")
    theme["colours"]["surface-tinted"] = "#f7f7f8"
    theme["colours"]["surface-plain"] = "#f7f7f7"
    assert tinted_chrome(theme) == ["surface-tinted"]
