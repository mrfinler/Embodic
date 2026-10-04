"""Hypothesis strategies for primitive chains that are continuous by construction."""

import math

from hypothesis import strategies as st

from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole

coordinate_mm = st.floats(-60.0, 60.0, allow_nan=False)
angle_rad = st.floats(-4 * math.pi, 4 * math.pi, allow_nan=False)


@st.composite
def chains(draw: st.DrawFn, max_size: int = 8) -> tuple[Primitive, ...]:
    """Draw a chain whose primitive i + 1 starts exactly where primitive i ends (an arc's centre is placed for it)."""
    x_mm, y_mm = draw(coordinate_mm), draw(coordinate_mm)
    prims: list[Primitive] = []
    for _ in range(draw(st.integers(1, max_size))):
        heading_rad = draw(angle_rad)
        if draw(st.booleans()):
            step_mm = draw(st.floats(0.01, 20.0))
            x2_mm, y2_mm = x_mm + step_mm * math.cos(heading_rad), y_mm + step_mm * math.sin(heading_rad)
            prims.append(Line(x1_mm=x_mm, y1_mm=y_mm, x2_mm=x2_mm, y2_mm=y2_mm, width_mm=0.2, role=PrimitiveRole.SIDE))
            x_mm, y_mm = x2_mm, y2_mm
        else:
            r_mm = draw(st.floats(0.05, 30.0))
            arc = Arc(
                cx_mm=x_mm - r_mm * math.cos(heading_rad),
                cy_mm=y_mm - r_mm * math.sin(heading_rad),
                r_mm=r_mm,
                start_rad=heading_rad,
                sweep_rad=draw(st.floats(-2 * math.pi, 2 * math.pi).filter(lambda a: abs(a) > 1e-3)),
                width_mm=0.2,
                role=PrimitiveRole.FILLET,
            )
            prims.append(arc)
            x_mm, y_mm = arc.end_point()
    return tuple(prims)
