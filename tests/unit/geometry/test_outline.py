"""build_outline: a polygon corner radius becomes tangent arcs, clamped like Xcoil's outlinePrims (D-056h)."""

import math

import pytest

from embodic.geometry.outline import build_outline
from embodic.geometry.primitives import Arc, Line, Primitive
from embodic.model.outline import CircleOutline, OutlineSpec, PolygonOutline

pytestmark = pytest.mark.req("REQ-F-09")

CLOSURE_MM = 1e-9


def _outer(shape: PolygonOutline) -> tuple[Primitive, ...]:
    return build_outline(OutlineSpec(board=shape, bore=None), (0.0, 0.0)).outer


def _chain_gaps_mm(loop: tuple[Primitive, ...]) -> list[float]:
    """Distance from the end of each primitive to the start of the next one, the last to the first."""
    return [math.dist(a.end_point(), b.start_point()) for a, b in zip(loop, loop[1:] + loop[:1], strict=True)]


@pytest.mark.parametrize("sides", [4, 6, 8, 12, 16])
@pytest.mark.parametrize("corner_radius_mm", [0.0, 2.0, 7.5, 500.0])
@pytest.mark.parametrize("rotation_rad", [0.0, 0.3, -2.5])
def test_polygon_loop_is_closed_and_chained_for_any_corner_radius(
    sides: int, corner_radius_mm: float, rotation_rad: float
) -> None:
    """Catches a corner arc with the wrong centre or tangent length: the edge would not meet the arc (DXF gap)."""
    loop = _outer(
        PolygonOutline(sides=sides, across_flats_mm=60.0, corner_radius_mm=corner_radius_mm, rotation_rad=rotation_rad)
    )
    assert max(_chain_gaps_mm(loop)) < CLOSURE_MM


@pytest.mark.parametrize("sides", [4, 8, 16])
def test_sharp_polygon_has_one_line_per_side_and_no_arc(sides: int) -> None:
    """Catches an arc of radius 0 added at every vertex of an unrounded polygon."""
    loop = _outer(PolygonOutline(sides=sides, across_flats_mm=60.0))
    assert [type(p) for p in loop] == [Line] * sides


@pytest.mark.parametrize("sides", [4, 8, 16])
def test_rounded_polygon_has_one_counter_clockwise_arc_per_corner(sides: int) -> None:
    """Catches a missing corner and an arc that sweeps the long way round or clockwise."""
    loop = _outer(PolygonOutline(sides=sides, across_flats_mm=60.0, corner_radius_mm=3.0))
    arcs = [p for p in loop if isinstance(p, Arc)]
    assert len(arcs) == len(loop) // 2 == sides
    for arc in arcs:
        assert arc.r_mm == 3.0
        assert arc.sweep_rad == pytest.approx(2 * math.pi / sides, rel=1e-12)  # exterior angle at the corner


def test_corner_radius_larger_than_the_apothem_is_clamped_to_0_999_apothem() -> None:
    """Catches a radius that passes the flats (arcs of 500 mm) or a clamp at the whole apothem (edges of 0 mm)."""
    loop = _outer(PolygonOutline(sides=8, across_flats_mm=100.0, corner_radius_mm=500.0))
    arcs = [p for p in loop if isinstance(p, Arc)]
    assert len(arcs) == 8
    assert all(a.r_mm == pytest.approx(0.999 * 50.0, rel=1e-12) for a in arcs)
    lines = [p for p in loop if isinstance(p, Line)]
    straight_mm = 2 * (50.0 - 0.999 * 50.0) * math.tan(math.pi / 8)  # what is left of an edge between two arcs
    assert all(
        math.dist(line.start_point(), line.end_point()) == pytest.approx(straight_mm, rel=1e-6) for line in lines
    )


def test_bore_polygon_gets_its_corner_radius_too() -> None:
    """Catches a corner radius applied to the board edge only."""
    spec = OutlineSpec(
        board=CircleOutline(radius_mm=50.0),
        bore=PolygonOutline(sides=6, across_flats_mm=20.0, corner_radius_mm=2.0),
    )
    (bore,) = build_outline(spec, (0.0, 0.0)).cutouts
    assert sum(isinstance(p, Arc) for p in bore) == 6
