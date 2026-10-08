"""Board outline from the outline inputs: board edge and bore as closed loops of width-0 primitives (REQ-F-09)."""

import math

from embodic.geometry.fasteners import place_holes
from embodic.geometry.layout import BoardOutline
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.outline import CircleOutline, OutlineSpec, PolygonOutline


def _loop(shape: CircleOutline | PolygonOutline) -> tuple[Primitive, ...]:
    if isinstance(shape, CircleOutline):
        return tuple(
            Arc(cx_mm=0.0, cy_mm=0.0, r_mm=shape.radius_mm, start_rad=start, sweep_rad=math.pi, width_mm=0.0,
                role=PrimitiveRole.OUTLINE)
            for start in (0.0, math.pi)
        )  # fmt: skip
    # Vertex k at rotation + pi/n + 2 pi k/n, so rotation 0 puts a flat across the +x axis (`assumption`).
    n, circum_mm = shape.sides, shape.across_flats_mm / 2 / math.cos(math.pi / shape.sides)
    angles = [shape.rotation_rad + math.pi / n + 2 * math.pi * k / n for k in range(n)]
    points = [(circum_mm * math.cos(a), circum_mm * math.sin(a)) for a in angles]
    return tuple(
        Line(x1_mm=a[0], y1_mm=a[1], x2_mm=b[0], y2_mm=b[1], width_mm=0.0, role=PrimitiveRole.OUTLINE)
        for a, b in zip(points, points[1:] + points[:1], strict=True)
    )


def build_outline(spec: OutlineSpec, envelope_mm: tuple[float, float]) -> BoardOutline:
    """Board edge, bore loop and the screw holes of every pattern; polygon corner radii are not built yet."""
    del envelope_mm  # interfaces.md section 5 signature; the copper envelope does not shape the outline yet
    cutouts = () if spec.bore is None else (_loop(spec.bore),)
    holes = tuple(placed.hole for placed in place_holes(spec.screws))
    return BoardOutline(outer=_loop(spec.board), cutouts=cutouts, holes=holes)
