"""DEF-M2d3-02: the track length a G9 fillet removes, per corner, against an independent line-arc closed form.

Every corner of the canonical coil joins a side line (offset d from its sector edge, so d from the origin) to an end arc
of radius R about the origin. A fillet of radius r tangent to both has its centre at offset d + r and at R - r (outer
end) or R + r (inner end) from the origin. With beta = asin(offset / distance from the origin) measured from the line:

    outer end:  dL = r (pi/2 + beta_c) - R (beta_c - beta_v) - (sqrt(R^2 - d^2) - sqrt((R - r)^2 - (d + r)^2))
    inner end:  dL = r (pi/2 - beta_c) - R (beta_c - beta_v) - (sqrt((R + r)^2 - (d + r)^2) - sqrt(R^2 - d^2))

As R grows both reduce to the line-line form r (pi - phi) - 2 r cot(phi / 2). G9 makes the corners of one family
concentric, r = rho + k w_d, so the outer corners of CF-11 (w_d 0.7 mm, 10 turns) take radii up to 6.8 mm and remove
far more than a 0.5 mm fillet would; the 12.7 % CF-11 loss of DEF-M2d3-02 is this construction, not a stray trim.
"""

import dataclasses
import math
from collections.abc import Callable

import pytest
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.generators import generate_spiral
from embodic.generators.spiral.fillets import Corner, CornerKind, corners
from embodic.generators.spiral.turns import (
    Closing,
    CoilFrame,
    FullClosing,
    Point,
    closing_for,
    left_side_tops,
    loop_turns,
    max_closing,
)
from embodic.geometry.details import SpiralDetail
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.results import Registry, load_registry

CASES = [("CF-11", default_design, 0.5), ("D08", d08_design, 1.0)]


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _closed_form_mm(r_arc: float, d: float, r: float, outer: bool) -> float:
    beta_v = math.asin(d / r_arc)
    if outer:
        beta_c = math.asin((d + r) / (r_arc - r))
        line = math.sqrt(r_arc * r_arc - d * d) - math.sqrt((r_arc - r) ** 2 - (d + r) ** 2)
        return r * (math.pi / 2 + beta_c) - r_arc * (beta_c - beta_v) - line
    beta_c = math.asin((d + r) / (r_arc + r))
    line = math.sqrt((r_arc + r) ** 2 - (d + r) ** 2) - math.sqrt(r_arc * r_arc - d * d)
    return r * (math.pi / 2 - beta_c) - r_arc * (beta_c - beta_v) - line


def _arc_mm(r_arc: float, a: Point, b: Point) -> float:
    return r_arc * abs(math.remainder(math.atan2(a[1], a[0]) - math.atan2(b[1], b[0]), 2 * math.pi))


def _measured_mm(corner: Corner, vertex: Point, r_arc: float, arc_first: bool) -> float:
    """Fillet length minus what it trims from the arc and the line it joins at ``vertex``."""
    assert corner.fillet is not None
    on_arc, on_line = (corner.end_in, corner.start_out) if arc_first else (corner.start_out, corner.end_in)
    trimmed = _arc_mm(r_arc, vertex, on_arc) + math.dist(vertex, on_line)
    return corner.fillet.r_mm * abs(corner.fillet.sweep_rad) - trimmed


def _frame_closing(design: DesignParameters) -> tuple[CoilFrame, Closing]:
    """Return the frame and the closing generate_spiral builds for ``design``."""
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = design.winding.coil
    frame = CoilFrame.of(coil, design.vias.pad_mm)
    loops = loop_turns(frame)[0]
    closing = max_closing(frame, loops) if coil.turns is None else closing_for(frame, loops, coil.turns)
    assert closing is not None
    return frame, closing


def _corner_rows(design: DesignParameters, rho: float) -> list[tuple[CornerKind, int, float, float]]:
    """(kind, turn, measured dL, closed-form dL) for every filleted corner of the canonical coil."""
    frame, closing = _frame_closing(design)
    filleted = corners(frame, closing, rho)
    assert filleted is not None
    vertex: dict[tuple[CornerKind, int], Point] = {}
    for turn, top in zip(closing.turns, left_side_tops(closing), strict=True):
        vertex |= {(CornerKind.B, turn.index): turn.b, (CornerKind.C, turn.index): turn.c}
        vertex |= {(CornerKind.D, turn.index): turn.d, (CornerKind.J, turn.index): top}
    if not isinstance(closing, FullClosing):
        vertex[(CornerKind.B, closing.half.index)] = closing.half.b
    rows = []
    for (kind, t), corner in filleted.items():
        outer = kind in (CornerKind.B, CornerKind.J)
        r_arc = frame.outer_radius_mm(t + 1 if kind is CornerKind.J else t) if outer else frame.inner_radius_mm(t)
        assert corner.fillet is not None
        expected = _closed_form_mm(r_arc, frame.offset_mm(t), corner.fillet.r_mm, outer)
        measured = _measured_mm(corner, vertex[(kind, t)], r_arc, arc_first=kind in (CornerKind.B, CornerKind.D))
        rows.append((kind, t, measured, expected))
    return rows


def _with_rho(design: DesignParameters, rho: float) -> DesignParameters:
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, corner_radius_mm=rho)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


def _track_mm(design: DesignParameters, registry: Registry) -> float:
    stack = generate_spiral(design, registry)
    assert isinstance(stack, BoardStack)
    detail = stack.boards[0].detail
    assert isinstance(detail, SpiralDetail)
    return detail.track_length_per_coil_layer_mm["X"]


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize(("name", "make", "rho"), CASES)
def test_def_m2d3_02_each_fillet_removes_the_closed_form_length(
    name: str, make: Callable[[], DesignParameters], rho: float
) -> None:
    """Per corner, fillet minus trims equals the line-arc closed form within 1e-9 mm.

    Catches a fillet that trims the wrong primitive or trims past its tangent point (the trimmed length changes).
    """
    rows = _corner_rows(make(), rho)
    assert rows
    for kind, t, measured, expected in rows:
        assert measured == pytest.approx(expected, abs=1e-9), (kind, t)


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize(("name", "make", "rho"), CASES)
def test_def_m2d3_02_track_length_changes_only_at_the_corners(
    name: str, make: Callable[[], DesignParameters], rho: float, registry: Registry
) -> None:
    """The generated filleted track equals the sharp track plus the corner closed forms within 1e-9 mm.

    Catches fillets applied twice, a stub, jog or lead trimmed as well, or a closing with fewer turns when filleted.
    """
    design = make()
    sharp_mm = _track_mm(_with_rho(design, 0.0), registry)
    filleted_mm = _track_mm(_with_rho(design, rho), registry)
    closed_form_mm = sum(expected for *_, expected in _corner_rows(design, rho))
    assert filleted_mm == pytest.approx(sharp_mm + closed_form_mm, abs=1e-9)


@pytest.mark.req("REQ-F-06")
def test_def_m2d3_02_closed_form_tends_to_the_line_line_form() -> None:
    """For r_arc much larger than r the line-arc form reaches r (pi - phi) - 2 r cot(phi / 2) at phi = pi / 2."""
    r = 0.5
    line_line = r * (math.pi / 2) - 2 * r
    assert _closed_form_mm(1e7, 0.0, r, outer=True) == pytest.approx(line_line, abs=1e-6)
    assert _closed_form_mm(1e7, 0.0, r, outer=False) == pytest.approx(line_line, abs=1e-6)
    assert line_line == pytest.approx(-0.2146, abs=1e-4)
