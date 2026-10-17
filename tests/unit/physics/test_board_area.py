"""EQ-16 and EQ-17 board area: the exact area of the outline loops, not of their 0.5 mm chords (DEF-M7b-01).

Expected values are closed forms written out in docs/phase3/engineering/fix_wave_f1.md section A.4 (T-A3).
"""

import math

import pytest
from tests.unit.drc.layouts import layout

from embodic.geometry.outline import build_outline
from embodic.model.outline import CircleOutline, OutlineSpec, PolygonOutline, ScrewFit, ScrewPattern
from embodic.physics.analyse import board_area_mm2

pytestmark = pytest.mark.req("REQ-F-11")

_M3_PATTERN = ScrewPattern(size="M3", fit=ScrewFit.NORMAL, count=6, pitch_radius_mm=42.0, hole_diameter_mm=3.4)

# (spec, area in mm^2), the values of fix_wave_f1.md section A.4 T-A3.
_CASES = {
    "C1 circle r 57.84": (
        OutlineSpec(board=CircleOutline(radius_mm=57.84), bore=None),
        10510.09015179737,
    ),
    "C2 12-gon, 93 mm across flats": (
        OutlineSpec(board=PolygonOutline(sides=12, across_flats_mm=93.0), bore=None),
        6952.477696010341,
    ),
    "C3 12-gon minus round bore r 12.5 minus 6 holes of 3.4 mm": (
        OutlineSpec(
            board=PolygonOutline(sides=12, across_flats_mm=93.0),
            bore=CircleOutline(radius_mm=12.5),
            screws=(_M3_PATTERN,),
        ),
        6407.128627273689,
    ),
    "C4 circle r 50 minus a hexagonal bore, 20 mm across flats, turned 0.3 rad": (
        OutlineSpec(
            board=CircleOutline(radius_mm=50.0),
            bore=PolygonOutline(sides=6, across_flats_mm=20.0, rotation_rad=0.3),
        ),
        7507.571472460708,
    ),
}


@pytest.mark.parametrize(("spec", "expected_mm2"), _CASES.values(), ids=list(_CASES))
def test_board_area_of_a_built_outline_equals_its_closed_form(spec: OutlineSpec, expected_mm2: float) -> None:
    """Catches the 0.5 mm chord area and a polygon circumradius taken as across flats / 2 (C2).

    The chord area is C1 -1.2e-5, C3 +8.1e-6 and C4 -1.7e-5 relative. A dropped segment term, or a bore or screw
    hole left in the board, also fails C1, C3 or C4.
    """
    outline = build_outline(spec, (0.0, 0.0))
    area = board_area_mm2(layout(outer=outline.outer, cutouts=outline.cutouts, holes=outline.holes))
    assert area == pytest.approx(expected_mm2, rel=1e-12)
    assert math.isfinite(area)


@pytest.mark.parametrize(("sides", "rotation_rad"), [(8, 0.0), (8, 0.3), (12, -2.5), (4, 1.0)])
def test_board_area_of_a_rounded_polygon_equals_its_closed_form(sides: int, rotation_rad: float) -> None:
    """Catches a corner arc on the wrong side of its edges and an area that depends on the polygon's rotation.

    A wrong-side arc moves the area by 2 r_c^2 (tan(pi/n) - pi/n) per corner.
    """
    apothem_mm, corner_mm = 50.0, 5.0
    spec = OutlineSpec(
        board=PolygonOutline(
            sides=sides, across_flats_mm=2 * apothem_mm, corner_radius_mm=corner_mm, rotation_rad=rotation_rad
        ),
        bore=None,
    )
    outline = build_outline(spec, (0.0, 0.0))
    half = math.pi / sides
    expected_mm2 = sides * apothem_mm**2 * math.tan(half) - sides * corner_mm**2 * (math.tan(half) - half)
    assert board_area_mm2(layout(outer=outline.outer)) == pytest.approx(expected_mm2, rel=1e-12)
