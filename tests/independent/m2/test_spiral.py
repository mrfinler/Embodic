"""Item 3: the spiral generator against own_spiral.py (own construction from spiral_generator_spec.md).

Subject: build_layout on the packaged CF-11 (12/16 default) and D08 (12/10) examples. Defects caught: a turn radius
off by a pitch, a wrong closing choice or via radius, a broken or reversed path, a layer Y that is not the mirror of
X, and fillet radii that are not concentric (a constant radius changes the CF-11 length by -7.76 mm, not -52.84 mm).
"""

import dataclasses
import itertools
import math
from functools import cache

import own_spiral
import pytest

from embodic.generators import build_layout
from embodic.geometry.layout import Layout, ViaRole
from embodic.geometry.primitives import Arc, PrimitiveRole
from embodic.io.examples import load_example
from embodic.results import load_registry

OWN = {
    "spiral_12c16p_default": own_spiral.Coil(12, 18.0, 38.0, 0.5, 0.2, 0.2, 0.6, None),
    "spiral_12c10p_d08": own_spiral.Coil(12, 11.47, 45.03, 2.06, 0.8, 0.8, 0.6, 3),
}
EXPECTED_PLAN = {"spiral_12c16p_default": (10, "full"), "spiral_12c10p_d08": (3, "half")}  # spec worked examples


@cache
def _layout(example_id: str, corner_radius_mm: float = 0.0) -> Layout:
    _, design = load_example(example_id)
    coil = dataclasses.replace(design.winding.coil, corner_radius_mm=corner_radius_mm)
    stack = build_layout(
        dataclasses.replace(design, winding=dataclasses.replace(design.winding, coil=coil)), load_registry()
    )
    return stack.boards[0]


def _ends(prim: object) -> tuple[tuple[float, float], tuple[float, float]]:
    if isinstance(prim, Arc):
        a, b = prim.start_rad, prim.start_rad + prim.sweep_rad
        return (
            (prim.cx_mm + prim.r_mm * math.cos(a), prim.cy_mm + prim.r_mm * math.sin(a)),
            (prim.cx_mm + prim.r_mm * math.cos(b), prim.cy_mm + prim.r_mm * math.sin(b)),
        )
    return (prim.x1_mm, prim.y1_mm), (prim.x2_mm, prim.y2_mm)


def _length(prim: object) -> float:
    if isinstance(prim, Arc):
        return prim.r_mm * abs(prim.sweep_rad)
    return math.hypot(prim.x2_mm - prim.x1_mm, prim.y2_mm - prim.y1_mm)


def _coil_paths(layout: Layout, element: int):
    return sorted((p for p in layout.paths if p.element == element and p.phase is not None), key=lambda p: p.layer)


def test_own_plan_matches_the_spec_worked_examples() -> None:
    """The own construction gives N 10 full (CF-11) and N 3 half (D08), as the worked examples state."""
    assert {k: c.plan()[:2] for k, c in OWN.items()} == EXPECTED_PLAN


@pytest.mark.parametrize("example_id", list(OWN))
def test_end_arc_radii_of_every_turn_match_own_construction(example_id: str) -> None:
    """Every coil-layer's end arcs about the origin, in path order, equal own R_out,t and r_end,t within 1e-9 mm."""
    own = OWN[example_id].end_radii()
    layout = _layout(example_id)
    ends = [
        [x.r_mm for x in p.primitives if isinstance(x, Arc) and x.role is PrimitiveRole.END_TURN] for p in layout.paths
    ]
    coil_layers = [(p, radii) for p, radii in zip(layout.paths, ends, strict=True) if radii]
    assert len(coil_layers) == OWN[example_id].q * len(layout.copper_layers)
    for path, radii in coil_layers:
        if radii[-1] == max(radii):  # path walked from the centre via outward (layer Y or a negative coil)
            radii.reverse()
        assert radii == pytest.approx(own, abs=1e-9), (path.id, path.layer)


@pytest.mark.parametrize("example_id", list(OWN))
def test_centre_vias_sit_on_each_coil_centre_line_at_own_radius(example_id: str) -> None:
    """One centre via per coil at r_v (cos theta_k, sin theta_k), theta_k = theta_0 + 2 pi k / Q, within 1e-9 mm."""
    _, design = load_example(example_id)
    coil = design.winding.coil
    r_v = OWN[example_id].plan()[2]
    own = [
        (r_v * math.cos(a), r_v * math.sin(a))
        for a in (coil.first_coil_angle_rad + 2 * math.pi * k / coil.coil_count for k in range(coil.coil_count))
    ]
    got = [(v.x_mm, v.y_mm) for v in _layout(example_id).vias if v.role is ViaRole.CENTRE]
    assert len(got) == len(own)
    for x, y in own:
        assert min(math.hypot(x - gx, y - gy) for gx, gy in got) <= 1e-9


@pytest.mark.parametrize("example_id", list(OWN))
def test_every_path_is_continuous_within_1e_6(example_id: str) -> None:
    """End of primitive i to start of i + 1 is at most 1e-6 mm on every path (REQ-N-21 COINCIDENCE_MM)."""
    for path in _layout(example_id).paths:
        ends = [_ends(x) for x in path.primitives]
        gaps = [math.dist(a[1], b[0]) for a, b in itertools.pairwise(ends)]
        assert max(gaps, default=0.0) <= 1e-6, (path.id, max(gaps))


@pytest.mark.parametrize("example_id", list(OWN))
def test_layer_y_is_the_reversed_mirror_of_layer_x_about_the_coil_centre_line(example_id: str) -> None:
    """Reflect X about the coil axis and reverse it: every non-stub primitive lands on Y within 1e-9 mm."""
    _, design = load_example(example_id)
    coil = design.winding.coil
    layout = _layout(example_id)
    for k in range(coil.coil_count):
        x_path, y_path = _coil_paths(layout, k)
        axis = coil.first_coil_angle_rad + 2 * math.pi * k / coil.coil_count
        c, s = math.cos(2 * axis), math.sin(2 * axis)

        def mirror(p: tuple[float, float], c: float = c, s: float = s) -> tuple[float, float]:
            return (c * p[0] + s * p[1], s * p[0] - c * p[1])

        xs = [_ends(x) for x in x_path.primitives if x.role is not PrimitiveRole.STUB]
        ys = [_ends(y) for y in y_path.primitives if y.role is not PrimitiveRole.STUB][::-1]
        assert len(xs) == len(ys)
        for (a0, a1), (b0, b1) in zip(xs, ys, strict=True):
            assert max(math.dist(mirror(a0), b1), math.dist(mirror(a1), b0)) <= 1e-9, k


def test_fillet_length_change_matches_the_g9_closed_form_on_cf11() -> None:
    """Coil-layer length with rho 0.5 mm minus without equals own sum over the B, C, D, J corners within 1e-9 mm."""
    plain, filleted = (_coil_paths(_layout("spiral_12c16p_default", r), 0)[0] for r in (0.0, 0.5))
    change = math.fsum(map(_length, filleted.primitives)) - math.fsum(map(_length, plain.primitives))
    assert change == pytest.approx(own_spiral.fillet_total(OWN["spiral_12c16p_default"], 0.5), abs=1e-9)
