"""Board outline from the outline inputs: board edge and bore as closed loops of width-0 primitives (REQ-F-09)."""

import math

from embodic.geometry.fasteners import place_holes
from embodic.geometry.layout import BoardOutline
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.outline import CircleOutline, OutlineSpec, PolygonOutline

# Xcoil outlinePrims (engine.js l.1057) keeps a corner arc from reaching the flats: radius at most 0.999 apothem.
_MAX_CORNER_PER_APOTHEM = 0.999
_MIN_CORNER_MM = 1e-9


def _circle_loop(shape: CircleOutline) -> tuple[Primitive, ...]:
    return tuple(
        Arc(cx_mm=0.0, cy_mm=0.0, r_mm=shape.radius_mm, start_rad=start, sweep_rad=math.pi, width_mm=0.0,
            role=PrimitiveRole.OUTLINE)
        for start in (0.0, math.pi)
    )  # fmt: skip


def _polygon_loop(shape: PolygonOutline) -> tuple[Primitive, ...]:
    """Regular polygon as lines; a corner radius adds one arc tangent to the two edges at each vertex.

    The loop runs counter-clockwise, corner arc k then edge k, the order of Xcoil's outlinePrims (engine.js l.1055).
    """
    # Vertex k at rotation + pi/n + 2 pi k/n, so rotation 0 puts a flat across the +x axis (`assumption`).
    n, half_rad = shape.sides, math.pi / shape.sides
    apothem_mm = shape.across_flats_mm / 2
    circum_mm = apothem_mm / math.cos(half_rad)
    corner_mm = max(0.0, min(shape.corner_radius_mm, apothem_mm * _MAX_CORNER_PER_APOTHEM))
    rounded = corner_mm > _MIN_CORNER_MM
    tangent_mm = corner_mm * math.tan(half_rad) if rounded else 0.0
    arc_centre_mm = circum_mm - corner_mm / math.cos(half_rad)
    angles = [shape.rotation_rad + half_rad + 2 * math.pi * k / n for k in range(n)]
    points = [(circum_mm * math.cos(a), circum_mm * math.sin(a)) for a in angles]
    loop: list[Primitive] = []
    for angle, a, b in zip(angles, points, points[1:] + points[:1], strict=True):
        if rounded:
            loop.append(
                Arc(cx_mm=arc_centre_mm * math.cos(angle), cy_mm=arc_centre_mm * math.sin(angle), r_mm=corner_mm,
                    start_rad=angle - half_rad, sweep_rad=2 * half_rad, width_mm=0.0, role=PrimitiveRole.OUTLINE)
            )  # fmt: skip
        edge_mm = math.hypot(b[0] - a[0], b[1] - a[1])
        ux, uy = (b[0] - a[0]) / edge_mm, (b[1] - a[1]) / edge_mm
        loop.append(
            Line(x1_mm=a[0] + ux * tangent_mm, y1_mm=a[1] + uy * tangent_mm,
                 x2_mm=b[0] - ux * tangent_mm, y2_mm=b[1] - uy * tangent_mm, width_mm=0.0,
                 role=PrimitiveRole.OUTLINE)
        )  # fmt: skip
    return tuple(loop)


def _loop(shape: CircleOutline | PolygonOutline) -> tuple[Primitive, ...]:
    return _circle_loop(shape) if isinstance(shape, CircleOutline) else _polygon_loop(shape)


def build_outline(spec: OutlineSpec, envelope_mm: tuple[float, float]) -> BoardOutline:
    """Board edge, bore loop and the screw holes of every pattern; a polygon corner radius is built as arcs."""
    del envelope_mm  # interfaces.md section 5 signature; the copper envelope does not shape the outline yet
    cutouts = () if spec.bore is None else (_loop(spec.bore),)
    holes = tuple(placed.hole for placed in place_holes(spec.screws))
    return BoardOutline(outer=_loop(spec.board), cutouts=cutouts, holes=holes)
