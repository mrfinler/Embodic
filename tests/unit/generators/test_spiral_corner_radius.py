"""A spiral design with a board corner radius builds the rounded outline (REQ-F-09; build_outline rounds it)."""

import dataclasses
import math

import pytest
from tests.unit.generators.default_example import default_design

from embodic.generators import build_layout
from embodic.geometry.layout import BoardStack
from embodic.geometry.primitives import Arc
from embodic.model.design import DesignParameters
from embodic.model.outline import PolygonOutline
from embodic.physics.analyse import board_area_mm2
from embodic.results import load_registry

pytestmark = pytest.mark.req("REQ-F-09")
CORNER_RADIUS_MM = 5.0


def _with_corner_radius(corner_radius_mm: float) -> DesignParameters:
    design = default_design()
    board = design.outline.board
    assert isinstance(board, PolygonOutline)
    rounded = dataclasses.replace(board, corner_radius_mm=corner_radius_mm)
    return dataclasses.replace(design, outline=dataclasses.replace(design.outline, board=rounded))


def _build(design: DesignParameters):
    stack = build_layout(design, load_registry())
    assert isinstance(stack, BoardStack), stack
    return stack.boards[0]


def test_a_spiral_design_with_a_corner_radius_builds_one_arc_per_polygon_corner() -> None:
    """Defect caught: the spiral generator refusing /outline/board/corner_radius_mm, or building the corners sharp."""
    sides = _with_corner_radius(0.0).outline.board.sides
    sharp, rounded = _build(_with_corner_radius(0.0)), _build(_with_corner_radius(CORNER_RADIUS_MM))
    assert [p for p in sharp.outline.outer if isinstance(p, Arc)] == []
    arcs = [p for p in rounded.outline.outer if isinstance(p, Arc)]
    assert len(arcs) == sides
    assert {p.r_mm for p in arcs} == {CORNER_RADIUS_MM}


def test_the_rounded_board_loses_the_closed_form_corner_area() -> None:
    """Defect caught: an arc of the wrong radius or sweep at a corner.

    Each of n corners cuts r^2 (tan(pi/n) - pi/n) from a regular n-gon: the kite of the vertex, the two tangent points
    and the arc centre, minus the sector of the arc.
    """
    n = _with_corner_radius(0.0).outline.board.sides
    cut_mm2 = n * CORNER_RADIUS_MM**2 * (math.tan(math.pi / n) - math.pi / n)
    sharp, rounded = _build(_with_corner_radius(0.0)), _build(_with_corner_radius(CORNER_RADIUS_MM))
    assert board_area_mm2(sharp) - board_area_mm2(rounded) == pytest.approx(cut_mm2, rel=1e-9)
