"""UT-GEO-21 (REQ-F-24, D-031a): screw holes from the entered hole diameter and their edge, pitch and copper keep-outs.

The model's ScrewPattern gains `hole_diameter_mm` in U-M2-fix; until it merges these tests use `_Pattern`, a local
stand-in with the D-031a field names. Every diameter here is an example value, not a fastener-table value. The board is
the CF-11 example (12-gon 93 mm across flats, bore 12.5 mm, copper 18 to 38 mm, edge and hole clearance 0.3 mm).
"""

import dataclasses
import math

import pytest
from tests.unit.generators.default_example import default_design

from embodic.drc import run_drc
from embodic.generators import generate_spiral
from embodic.generators.fasteners import keep_out_issues
from embodic.geometry.fasteners import place_holes
from embodic.geometry.layout import BoardStack, Layout
from embodic.model.outline import ScrewFit
from embodic.results import load_registry


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class _Pattern:
    size: str
    fit: ScrewFit
    count: int
    pitch_radius_mm: float
    hole_diameter_mm: float
    angle_offset_rad: float = 0.0


@pytest.fixture(scope="module")
def board() -> Layout:
    """Return the CF-11 example board."""
    stack = generate_spiral(default_design(), load_registry())
    assert isinstance(stack, BoardStack)
    return stack.boards[0]


@pytest.mark.req("REQ-F-24")
@pytest.mark.parametrize("fit", list(ScrewFit))
@pytest.mark.parametrize(("size", "diameter_mm"), [("M2.5", 2.9), ("M3", 3.4), ("M4", 4.6)])
def test_ut_geo_21_holes_sit_on_the_pitch_circle_with_the_entered_diameter(
    size: str, diameter_mm: float, fit: ScrewFit
) -> None:
    """Hole j at offset + 2 pi j / count on the pitch radius, diameter exactly as entered for every size and fit.

    Catches a diameter looked up from size and fit (D-031a: they only label the hole) or holes spread over pi.
    """
    pattern = _Pattern(size=size, fit=fit, count=5, pitch_radius_mm=44.5, hole_diameter_mm=diameter_mm,
                       angle_offset_rad=0.3)  # fmt: skip
    holes = [p.hole for p in place_holes((pattern,))]
    assert len(holes) == 5
    for j, hole in enumerate(holes):
        assert math.hypot(hole.x_mm, hole.y_mm) == pytest.approx(44.5, abs=1e-9)
        assert math.remainder(math.atan2(hole.y_mm, hole.x_mm) - 0.3 - 2 * math.pi * j / 5, 2 * math.pi) == (
            pytest.approx(0.0, abs=1e-12)
        )
        assert hole.diameter_mm == diameter_mm
        assert hole.label == f"{size} {fit.value}"


def _codes(board: Layout, pattern: _Pattern) -> list[tuple[str, tuple[str, ...]]]:
    issues = keep_out_issues(place_holes((pattern,)), board.outline, default_design().drc_rules)
    return [(i.code, i.pointers) for i in issues]


_POINTERS = ("/outline/screws/0/pitch_radius_mm", "/outline/screws/0/hole_diameter_mm")


@pytest.mark.req("REQ-F-24")
@pytest.mark.parametrize(
    ("pitch_radius_mm", "angle_offset_rad", "kept_out"),
    [
        (15.25, 0.0, False),  # 1.75 mm from the bore
        (12.5 + 0.3 + 1.0, 0.0, False),  # exactly the 0.3 mm rule: no violation (D-006, no slack)
        (12.5 + 0.3 + 1.0 - 2e-6, 0.0, True),  # below rule - epsilon
        (5.0, 0.0, True),  # inside the bore: the positive distance to its edge must not pass
        (46.0, math.pi / 12, True),  # 0.5 mm beyond the flat of the 12-gon
    ],
)
def test_ut_geo_21_edge_keep_out(
    board: Layout, pitch_radius_mm: float, angle_offset_rad: float, kept_out: bool
) -> None:
    """A 2 mm hole (example) closer than 0.3 mm to the bore or the board edge, or off the board, is reported."""
    pattern = _Pattern(size="M2", fit=ScrewFit.NORMAL, count=1, pitch_radius_mm=pitch_radius_mm, hole_diameter_mm=2.0,
                       angle_offset_rad=angle_offset_rad)  # fmt: skip
    expected = [("UNBUILDABLE_SCREW_HOLE_EDGE", _POINTERS)] if kept_out else []
    assert _codes(board, pattern) == expected


@pytest.mark.req("REQ-F-24")
@pytest.mark.parametrize(("count", "kept_out"), [(40, False), (48, True)])
def test_ut_geo_21_pitch_keep_out(board: Layout, count: int, kept_out: bool) -> None:
    """2 mm holes on r 15.25 mm: 40 leave a 0.393 mm web, 48 leave -0.005 mm (below the 0.3 mm rule)."""
    pattern = _Pattern(size="M2", fit=ScrewFit.NORMAL, count=count, pitch_radius_mm=15.25, hole_diameter_mm=2.0)
    expected = [("UNBUILDABLE_SCREW_HOLE_PITCH", _POINTERS)] if kept_out else []
    assert _codes(board, pattern) == expected


@pytest.mark.req("REQ-F-24")
@pytest.mark.parametrize(("pitch_radius_mm", "on_copper"), [(15.25, False), (18.5, True)])
def test_ut_geo_21_copper_keep_out_is_the_drc_copper_hole_check(
    board: Layout, pitch_radius_mm: float, on_copper: bool
) -> None:
    """Holes placed on the outline reach the DRC: on the coils (r 18.5 mm) COPPER_HOLE fires, clear of them it does not.

    Catches holes that never reach `BoardOutline.holes`, so copper under a screw would pass.
    """
    pattern = _Pattern(size="M2", fit=ScrewFit.NORMAL, count=6, pitch_radius_mm=pitch_radius_mm, hole_diameter_mm=2.0)
    holes = tuple(p.hole for p in place_holes((pattern,)))
    drilled = dataclasses.replace(board, outline=dataclasses.replace(board.outline, holes=holes))
    report = run_drc(drilled, default_design().drc_rules)
    assert report is not None
    hits = [v for v in report.violations if v.kind.value == "copper_hole"]
    assert bool(hits) is on_copper
    assert report.violation_count == len(hits)
