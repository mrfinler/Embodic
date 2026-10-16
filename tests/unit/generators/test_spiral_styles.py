"""Side and end styles of the spiral generator (spiral_generator_spec.md G2): radial sides, arc and straight ends."""

import dataclasses
import math
from collections.abc import Callable

import pytest
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.drc import run_drc
from embodic.errors import Unbuildable
from embodic.generators import generate_spiral
from embodic.geometry.details import SpiralDetail, TurnClosing
from embodic.geometry.layout import BoardStack, Layout
from embodic.geometry.paths import is_continuous
from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.model.design import DesignParameters
from embodic.model.winding_specs import EndStyle, SideStyle, SpiralWindingSpec
from embodic.results import Registry, load_registry


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _styled(design: DesignParameters, side: SideStyle, end: EndStyle) -> DesignParameters:
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, side_style=side, end_style=end)
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


def _board(design: DesignParameters, registry: Registry) -> Layout:
    stack = generate_spiral(design, registry)
    assert isinstance(stack, BoardStack), stack
    return stack.boards[0]


def _coil0_x(board: Layout) -> tuple[Line | Arc, ...]:
    return next(p for p in board.paths if p.element == 0 and p.layer == board.copper_layers[0]).primitives


def _clean(board: Layout, design: DesignParameters) -> dict[str, float | None]:
    report = run_drc(board, design.drc_rules)
    assert report is not None and report.violation_count == 0, [v.objects for v in report.violations]
    return {s.kind.value: s.least_clearance_mm for s in report.summaries}


EXAMPLES: list[tuple[str, Callable[[], DesignParameters]]] = [("CF-11", default_design), ("D08", d08_design)]


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize(("name", "make"), EXAMPLES)
@pytest.mark.parametrize("end", [EndStyle.ARC, EndStyle.STRAIGHT])
def test_ut_geo_18_end_turns_have_the_style_type_and_paths_stay_continuous(
    name: str, make: Callable[[], DesignParameters], end: EndStyle, registry: Registry
) -> None:
    """UT-GEO-18: arc ends are arcs about the stator centre, straight ends are chords perpendicular to the coil axis.

    Catches a straight end built as an arc (or the reverse), a chord tilted off the perpendicular, or a broken joint.
    """
    design = _styled(make(), SideStyle.PARALLEL, end)
    board = _board(design, registry)
    assert all(is_continuous(p.primitives) for p in board.paths)
    axis = design.winding.coil.first_coil_angle_rad  # type: ignore[union-attr]
    ends = [p for p in _coil0_x(board) if p.role is PrimitiveRole.END_TURN]
    assert ends
    for p in ends:
        if end is EndStyle.ARC:
            assert isinstance(p, Arc) and (p.cx_mm, p.cy_mm) == (0.0, 0.0)
        else:
            assert isinstance(p, Line)
            dx, dy = p.x2_mm - p.x1_mm, p.y2_mm - p.y1_mm
            assert abs(dx * math.cos(axis) + dy * math.sin(axis)) <= 1e-9 * math.hypot(dx, dy)


@pytest.mark.req("REQ-F-05")
@pytest.mark.parametrize(("name", "make"), EXAMPLES)
def test_straight_ends_pass_drc_with_the_tightest_trace_gap_at_s(
    name: str, make: Callable[[], DesignParameters], registry: Registry
) -> None:
    """G2 straight ends step one pitch in x, so neighbouring chords are exactly s apart and nothing is closer."""
    design = _styled(make(), SideStyle.PARALLEL, EndStyle.STRAIGHT)
    least = _clean(_board(design, registry), design)
    assert least["trace_trace"] == pytest.approx(design.winding.coil.clearance_mm, abs=1e-6)  # type: ignore[union-attr]


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize("end", [EndStyle.ARC, EndStyle.STRAIGHT])
def test_radial_sides_lie_on_rays_and_have_no_triangular_turns(end: EndStyle, registry: Registry) -> None:
    """G2 radial sides: every side is on a ray through the stator centre, rays never meet (no triangle, no half turn).

    Catches parallel sides built for a radial request, and a triangle or half closing that radial rays cannot form.
    """
    board = _board(_styled(default_design(), SideStyle.RADIAL, end), registry)
    sides = [p for p in _coil0_x(board) if p.role is PrimitiveRole.SIDE]
    assert sides
    for p in sides:
        assert isinstance(p, Line)
        cross = p.x1_mm * p.y2_mm - p.y1_mm * p.x2_mm
        assert abs(cross) <= 1e-9 * math.hypot(p.x1_mm, p.y1_mm) * math.hypot(p.x2_mm, p.y2_mm)
    detail = board.detail
    assert isinstance(detail, SpiralDetail)
    assert detail.turn_limit.loops_triangular == 0 and detail.turn_limit.closing is TurnClosing.FULL
    assert all(is_continuous(p.primitives) for p in board.paths)


@pytest.mark.req("REQ-F-05")
def test_radial_sides_with_straight_ends_pass_drc(registry: Registry) -> None:
    """G2 and G9: the neighbouring radial sides are max(gap, s) apart at R_i0, so CF-11 radial passes at s."""
    design = _styled(default_design(), SideStyle.RADIAL, EndStyle.STRAIGHT)
    least = _clean(_board(design, registry), design)
    assert least["trace_trace"] == pytest.approx(0.2, abs=1e-6)


@pytest.mark.req("REQ-F-05")
def test_radial_sides_with_arc_ends_pass_drc(registry: Registry) -> None:
    """G2: CF-11 with radial sides and arc ends has no violation (DEF-M2d3-01 was a DRC kernel false crossing)."""
    design = _styled(default_design(), SideStyle.RADIAL, EndStyle.ARC)
    _clean(_board(design, registry), design)


@pytest.mark.req("REQ-F-06")
def test_stadium_ends_are_refused_until_their_jog_is_specified(registry: Registry) -> None:
    """G2 stadium (status not tested): refused with the pointer, because no construction exists for its jog.

    An end arc tangent to both side lines d_t never reaches the previous side line d_t-1, where the jog starts.
    """
    refused = generate_spiral(_styled(default_design(), SideStyle.PARALLEL, EndStyle.STADIUM), registry)
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        ("UNBUILDABLE_UNSUPPORTED_END_STYLE", ("/winding/coil/end_style",))
    ]


@pytest.mark.req("REQ-F-06")
def test_stadium_refusal_does_not_hide_another_unsupported_option(registry: Registry) -> None:
    """Catches the end-style refusal returning alone: stadium ends with two parallel paths report both gaps."""
    design = _styled(default_design(), SideStyle.PARALLEL, EndStyle.STADIUM)
    assert isinstance(design.winding, SpiralWindingSpec)
    design = dataclasses.replace(design, winding=dataclasses.replace(design.winding, parallel_paths=2))
    refused = generate_spiral(design, registry)
    assert isinstance(refused, Unbuildable)
    assert [(i.code, i.pointers) for i in refused.issues] == [
        ("UNBUILDABLE_UNSUPPORTED_END_STYLE", ("/winding/coil/end_style",)),
        ("UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED", ("/winding/parallel_paths",)),
    ]
