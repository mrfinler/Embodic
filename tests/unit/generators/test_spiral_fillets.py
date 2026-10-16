"""G9 fillets of the spiral generator on CF-11 and D08 (spiral_generator_spec.md G9; interfaces.md section 7 rule 1)."""

import dataclasses
import math
from collections import defaultdict
from collections.abc import Callable

import pytest
from tests.unit.generators.d08_example import d08_design
from tests.unit.generators.default_example import default_design

from embodic.drc import run_drc
from embodic.generators import generate_spiral
from embodic.geometry.details import SpiralDetail
from embodic.geometry.layout import BoardStack, Layout
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole
from embodic.model.design import DesignParameters
from embodic.model.winding_specs import SpiralWindingSpec
from embodic.results import Registry, load_registry


@pytest.fixture(scope="module")
def registry() -> Registry:
    """Return the shipped equation registry."""
    return load_registry()


def _with_coil(design: DesignParameters, **changes: object) -> DesignParameters:
    assert isinstance(design.winding, SpiralWindingSpec)
    coil = dataclasses.replace(design.winding.coil, **changes)  # type: ignore[arg-type]
    return dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil))


def _board(design: DesignParameters, registry: Registry) -> Layout:
    stack = generate_spiral(design, registry)
    assert isinstance(stack, BoardStack)
    return stack.boards[0]


def _detail(board: Layout) -> SpiralDetail:
    assert isinstance(board.detail, SpiralDetail)
    return board.detail


def _heading(p: Primitive, at_end: bool) -> float:
    if isinstance(p, Line):
        return math.atan2(p.y2_mm - p.y1_mm, p.x2_mm - p.x1_mm)
    angle = p.start_rad + (p.sweep_rad if at_end else 0.0)
    return angle + math.copysign(math.pi / 2, p.sweep_rad)


def _mismatch(a: float, b: float) -> float:
    return abs(math.remainder(a - b, 2 * math.pi))


CASES = [("CF-11", default_design, 0.5), ("D08", d08_design, 1.0)]


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize(("name", "make", "rho"), CASES)
def test_ut_geo_02_fillets_are_tangent_continuous(
    name: str, make: Callable[[], DesignParameters], rho: float, registry: Registry
) -> None:
    """UT-GEO-02: at both ends of every fillet the heading jumps by at most 1e-6 rad (a wrong-side fillet jumps pi)."""
    board = _board(_with_coil(make(), corner_radius_mm=rho), registry)
    assert _detail(board).rho_used_mm == rho
    joints = 0
    for path in board.paths:
        for before, after in zip(path.primitives, path.primitives[1:], strict=False):
            if PrimitiveRole.FILLET in (before.role, after.role):
                assert _mismatch(_heading(before, at_end=True), _heading(after, at_end=False)) <= 1e-6
                assert math.dist(before.end_point(), after.start_point()) <= 1e-6
                joints += 1
    assert joints > 0


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize(("name", "make", "rho"), CASES)
def test_g9_nested_fillets_are_concentric_and_add_one_pitch_per_turn(
    name: str, make: Callable[[], DesignParameters], rho: float, registry: Registry
) -> None:  # fmt: skip
    """G9: fillets sharing a centre have radii rho, rho + w_d, rho + 2 w_d, ...; a fixed radius per corner fails."""
    design = _with_coil(make(), corner_radius_mm=rho)
    coil = design.winding.coil  # type: ignore[union-attr]
    pitch = coil.trace_width_mm + coil.clearance_mm
    board = _board(design, registry)
    coil_x = next(p for p in board.paths if p.element == 0 and p.layer == board.copper_layers[0])
    families: dict[tuple[float, float], list[float]] = defaultdict(list)
    for prim in coil_x.primitives:
        if prim.role is PrimitiveRole.FILLET:
            assert isinstance(prim, Arc)
            families[(round(prim.cx_mm, 6), round(prim.cy_mm, 6))].append(prim.r_mm)
    assert len(families) == 4  # B, C, D and J corner families of G3
    for radii in families.values():
        for k, r_mm in enumerate(sorted(radii)):
            assert r_mm == pytest.approx(rho + k * pitch, abs=1e-9)


@pytest.mark.req("REQ-F-05")
@pytest.mark.parametrize(("name", "make", "rho"), CASES)
def test_filleted_examples_pass_drc_with_the_tightest_gaps_at_s(
    name: str, make: Callable[[], DesignParameters], rho: float, registry: Registry
) -> None:  # fmt: skip
    """G9 and section 7 rule 1: the filleted board has no violation and its tightest trace and via gaps are s."""
    design = _with_coil(make(), corner_radius_mm=rho)
    report = run_drc(_board(design, registry), design.drc_rules)
    assert report is not None and report.violation_count == 0, [v.objects for v in report.violations]
    least = {s.kind.value: s.least_clearance_mm for s in report.summaries}
    s_mm = design.winding.coil.clearance_mm  # type: ignore[union-attr]
    assert least["trace_trace"] == pytest.approx(s_mm, abs=1e-6)
    assert least["trace_via"] == pytest.approx(s_mm, abs=1e-6)


@pytest.mark.req("REQ-F-06")
@pytest.mark.parametrize("rho", [1.0, 3.0, 50.0])
def test_g9_a_radius_that_does_not_fit_shrinks_by_0_7_and_stays_drc_clean(rho: float, registry: Registry) -> None:
    """G9 retry: rho_used is rho * 0.7**k with k <= 12 (or 0, sharp) and the board passes DRC; CF-11 rejects 1.0 mm."""
    design = _with_coil(default_design(), corner_radius_mm=rho)
    board = _board(design, registry)
    used = _detail(board).rho_used_mm
    allowed = [rho * 0.7**k for k in range(13)] + [0.0]
    assert any(used == pytest.approx(a, rel=1e-12, abs=0.0) for a in allowed)
    assert used < rho
    report = run_drc(board, design.drc_rules)
    assert report is not None and report.violation_count == 0


@pytest.mark.req("REQ-F-06")
def test_g9_unequal_end_width_keeps_corners_sharp(registry: Registry) -> None:
    """G9 validity: with w_out != w the end pitch differs from the side pitch, so no corner is filleted."""
    board = _board(_with_coil(default_design(), corner_radius_mm=0.5, end_width_outer_mm=0.6), registry)
    assert _detail(board).rho_used_mm == 0.0
    assert not any(p.role is PrimitiveRole.FILLET for path in board.paths for p in path.primitives)
