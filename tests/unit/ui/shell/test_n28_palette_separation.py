"""REQ-N-28 (V3-01 gap N-28): phase colours and grey steps stay distinguishable in both theme files.

The instrument is Agent 1's palette validator (dataviz `validate_palette`, design_spec.md section 3.2), re-implemented
here because the repository does not ship it: OKLab distance times 100, Machado, Oliveira and Fernandes (2009)
severity-1.0 simulation. Limits come from the spec: normal vision at least 15 (hard gate, section 3.2), protan and
deutan at least 8 (the validator target, section 3.2; tritan is reported there, not gated), grey ladder monotone with
adjacent OKLCH lightness steps of at least 0.06 (section 3.4).
"""

import json
import math
from collections.abc import Sequence
from itertools import combinations, pairwise

import pytest

from embodic.paths import resource_root

pytestmark = pytest.mark.req("REQ-N-28")

NORMAL_FLOOR = 15.0
CVD_TARGET = 8.0
LADDER_MIN_DL = 0.06
MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}
# design_spec.md section 3.2, "Phase colours": the hex values the table below was computed from.
SPEC_COLOURS = {
    "light": {"A": "#941328", "B": "#0032e2", "C": "#579f03"},
    "dark": {"A": "#c43b10", "B": "#005bfc", "C": "#0eb16a"},
}
# design_spec.md section 3.2, "Colour-blind simulation per pair": normal, protan, deutan, tritan (OKLab dE x 100).
SPEC_TABLE = {
    ("light", "A", "B"): (36.2, 30.8, 30.8, 27.4),
    ("light", "A", "C"): (34.9, 32.9, 19.9, 30.7),
    ("light", "B", "C"): (44.0, 38.3, 39.3, 16.4),
    ("dark", "A", "B"): (39.7, 34.0, 35.4, 32.6),
    ("dark", "A", "C"): (31.8, 25.1, 12.2, 36.2),
    ("dark", "B", "C"): (35.5, 32.4, 31.9, 12.5),
}


def _linear(hex_colour: str) -> tuple[float, ...]:
    channels = (int(hex_colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)


def _oklab(rgb: Sequence[float]) -> tuple[float, float, float]:
    r, g, b = rgb
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)  # noqa: E741
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def delta_e(a: str, b: str, vision: str | None = None) -> float:
    """Return the OKLab distance times 100 between two colours, optionally as a dichromat sees them."""

    def seen(hex_colour: str) -> tuple[float, ...]:
        rgb = _linear(hex_colour)
        if vision is None:
            return rgb
        rows = MACHADO[vision]
        return tuple(max(0.0, min(1.0, sum(w * c for w, c in zip(row, rgb, strict=True)))) for row in rows)

    return 100 * math.dist(_oklab(seen(a)), _oklab(seen(b)))


def lightness(hex_colour: str) -> float:
    """Return OKLCH lightness."""
    return _oklab(_linear(hex_colour))[0]


def separation_findings(phases: list[dict[str, object]]) -> list[str]:
    """Return one message per phase pair or grey step that is too close, for the `phases` list of a theme file."""
    findings = []
    colours = {str(p["phase"]): str(p["colour_hex"]) for p in phases}
    for (a, ca), (b, cb) in combinations(colours.items(), 2):
        normal = delta_e(ca, cb)
        if normal < NORMAL_FLOOR:
            findings.append(f"phases {a}-{b}: normal vision dE {normal:.1f} < {NORMAL_FLOOR:g}")
        for vision in ("protan", "deutan"):
            seen = delta_e(ca, cb, vision)
            if seen < CVD_TARGET:
                findings.append(f"phases {a}-{b}: {vision} dE {seen:.1f} < {CVD_TARGET:g}")
    steps = [(str(p["phase"]), lightness(str(p["grey_hex"]))) for p in phases]
    levels = [level for _, level in steps]
    if levels != sorted(levels) and levels != sorted(levels, reverse=True):
        findings.append(f"grey ladder is not monotone: {[(n, round(level, 3)) for n, level in steps]}")
    for (a, la), (b, lb) in pairwise(steps):
        if abs(la - lb) < LADDER_MIN_DL:
            findings.append(f"grey steps {a}-{b}: dL {abs(la - lb):.3f} < {LADDER_MIN_DL:g}")
    return findings


def theme_phases(theme: str) -> list[dict[str, object]]:
    """Return the `phases` list of a packaged theme file."""
    return json.loads((resource_root() / "themes" / f"{theme}.json").read_text(encoding="utf-8"))["phases"]


def with_colour(phases: list[dict[str, object]], phase: str, key: str, hex_colour: str) -> list[dict[str, object]]:
    """Return a copy of ``phases`` where one phase has another colour or grey."""
    return [{**p, key: hex_colour} if p["phase"] == phase else dict(p) for p in phases]


@pytest.mark.parametrize(("theme", "first", "second"), sorted(SPEC_TABLE))
def test_n28_the_instrument_reproduces_the_published_table(theme: str, first: str, second: str) -> None:
    """Catches a validator port that disagrees with design_spec.md section 3.2, which would make every verdict moot."""
    colours = SPEC_COLOURS[theme]
    measured = tuple(
        delta_e(colours[first], colours[second], vision) for vision in (None, "protan", "deutan", "tritan")
    )
    assert measured == pytest.approx(SPEC_TABLE[(theme, first, second)], abs=0.06)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_n28_every_phase_pair_and_grey_step_of_a_shipped_theme_is_separated(theme: str) -> None:
    """Catches a theme edit that keeps 3:1 on the canvas but makes two phases or two grey steps indistinguishable."""
    assert separation_findings(theme_phases(theme)) == []


def test_n28_two_phases_of_close_colour_are_reported() -> None:
    """Catches a checker that passes any palette whose colours are all dark enough for 3:1 on a white canvas."""
    close = with_colour(theme_phases("light"), "B", "colour_hex", "#a01328")
    findings = separation_findings(close)
    assert any(f.startswith("phases A-B: normal vision") for f in findings)
    assert any(f.startswith("phases A-B: deutan") for f in findings)


def test_n28_a_red_green_pair_that_collapses_for_deutan_readers_is_reported() -> None:
    """Catches a checker that tests normal vision only; the weakest published pair is red-green under deutan."""
    collapse = with_colour(theme_phases("dark"), "C", "colour_hex", "#8a8a10")
    findings = separation_findings(collapse)
    assert any("deutan" in f and "A-C" in f for f in findings)


def test_n28_two_grey_steps_closer_than_a_lightness_step_are_reported() -> None:
    """Catches a ladder edit that leaves B and C 0.03 apart, which the 3:1 contrast check never sees."""
    ladder = with_colour(theme_phases("light"), "C", "grey_hex", "#6a6a6a")
    findings = separation_findings(ladder)
    assert any(f.startswith("grey steps B-C") for f in findings)


def test_n28_a_ladder_that_changes_direction_is_reported() -> None:
    """Catches a ladder where B is lighter than both A and C: every step may be wide and the ladder still not a ramp."""
    broken = with_colour(theme_phases("light"), "B", "grey_hex", "#c0c0c0")
    assert any("not monotone" in f for f in separation_findings(broken))
