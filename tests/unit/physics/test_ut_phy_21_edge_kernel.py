"""UT-PHY-21 (REQ-T-08 b): the EC-05 kernel returns the Phase 1 edge-leakage values on the Phase 1 segment set.

Specification: docs/phase3/engineering/fix_wave_f1.md sections B.4 and B.5. Each case is one radial line over the coil
annulus, clipped to the magnet span, in the field of EQ-05 at z = G, the idealised set of edge_zone_d09.js l.34-56. The
expected values were recomputed from the registry formula alone (scipy quad, rel 1e-14), not read from the kernel. They
say nothing about generated layouts, where the segment set differs (section B.2).
"""

from dataclasses import dataclass

import pytest

from embodic.geometry.primitives import Line, PrimitiveRole
from embodic.model.rotor import ArcMagnet, BlockMagnet, RotorSpec, RotorType
from embodic.physics.emf import edge_leakage_fraction, field_table, integrate_path
from embodic.results import ValidityEffect, load_registry
from embodic.results.traceable import evaluate_validity

pytestmark = [pytest.mark.req("REQ-T-08"), pytest.mark.eqt("EQT-05-EC")]

# The kernel's midpoint chords and 48-step field table read low by 0.025 to 0.070 pp at 0.5 mm and by 0.0011 to 0.0028
# pp at 0.1 mm (the ratio 22 to 25 is the h^2 order of a midpoint rule). 0.1 pp is the REQ-T-08 figure.
TOLERANCE_AT_HALF_MM = 0.001
TOLERANCE_AT_TENTH_MM = 0.00005


@dataclass(frozen=True, slots=True)
class EdgeCase:
    """A rotor, the plane G = z of the field, the radial line and the registry-formula e_edge."""

    name: str
    rotor: RotorSpec
    plane_mm: float
    line_mm: tuple[float, float]
    expected: float


def _rotor(poles: int, magnet: ArcMagnet | BlockMagnet, remanence_t: float) -> RotorSpec:
    return RotorSpec(
        poles=poles,
        rotor_type=RotorType.DOUBLE,
        magnet=magnet,
        remanence_t=remanence_t,
        recoil_permeability=1.05,
        air_gap_mm=1.0,
        back_iron_thickness_mm=5.0,
    )


def _d09_rotor(r_inner_mm: float, r_outer_mm: float) -> RotorSpec:
    return _rotor(
        16, ArcMagnet(pole_arc_ratio=0.8, r_inner_mm=r_inner_mm, r_outer_mm=r_outer_mm, thickness_mm=2.0), 1.33
    )


KERNEL_CASES = (
    EdgeCase(
        "default_12_16",
        _rotor(16, BlockMagnet(width_mm=6.0, length_mm=20.0, r_center_mm=28.0, thickness_mm=2.0), 1.315),
        1.31,
        (18.0, 38.0),
        0.05328140,
    ),
    EdgeCase(
        "O1_D08",
        _rotor(10, ArcMagnet(pole_arc_ratio=0.72, r_inner_mm=15.4, r_outer_mm=43.4, thickness_mm=5.0), 1.38),
        1.4,
        (12.5, 44.0),
        0.04208834,
    ),
    EdgeCase("O2_D09_N8", _d09_rotor(25.0, 46.0), 1.5, (25.2, 47.6), 0.05788521),
)
MAGNET_LENGTH_CASES = (
    EdgeCase("cap, 10 mm magnet", _d09_rotor(30.5, 40.5), 1.5, (30.5, 40.5), 0.12373846),
    EdgeCase("cap, 12 mm magnet", _d09_rotor(29.5, 41.5), 1.5, (29.5, 41.5), 0.10445833),
    EdgeCase("no cap, 15 mm magnet", _d09_rotor(28.0, 43.0), 1.5, (28.0, 43.0), 0.08420015),
)


def _e_edge(case: EdgeCase, max_segment_mm: float) -> float:
    check = load_registry().equation("EQ-05").validity_checks[0]
    decay_mm = float(check.parameters["c_e"]) * case.plane_mm
    table = field_table(case.rotor, case.plane_mm, case.plane_mm, (1,))
    line = Line(
        x1_mm=case.line_mm[0], y1_mm=0.0, x2_mm=case.line_mm[1], y2_mm=0.0, width_mm=0.5, role=PrimitiveRole.SIDE
    )
    field = integrate_path([line], table, case.rotor.poles // 2, max_segment_mm, decay_mm)
    return edge_leakage_fraction([field], float(check.parameters["D_e"]))


@pytest.mark.parametrize("case", KERNEL_CASES + MAGNET_LENGTH_CASES, ids=lambda c: c.name)
@pytest.mark.parametrize(
    ("max_segment_mm", "tolerance"), [(0.5, TOLERANCE_AT_HALF_MM), (0.1, TOLERANCE_AT_TENTH_MM)], ids=["0.5mm", "0.1mm"]
)
def test_edge_leakage_of_the_phase_1_segment_set_matches_the_registry_formula(
    case: EdgeCase, max_segment_mm: float, tolerance: float
) -> None:
    """Catches a wrong decay length, end distance, weight, alpha_p or field plane in the EC-05 kernel.

    Shifts of e_edge (fix_wave_f1.md section B.5): decay length G instead of c_e G +0.47 to +0.67 pp, d to the farther
    magnet end -4.2 to -5.8 pp, a weight without r up to 0.16 pp, alpha_p frozen at the mean radius +0.19 pp on the
    block-magnet case, the field at the magnet face instead of z up to 0.05 pp (seen at 0.1 mm only).
    """
    assert abs(_e_edge(case, max_segment_mm) - case.expected) <= tolerance


@pytest.mark.parametrize(
    ("case", "effect"),
    [
        (MAGNET_LENGTH_CASES[0], ValidityEffect.CAP),
        (MAGNET_LENGTH_CASES[1], ValidityEffect.CAP),
        (MAGNET_LENGTH_CASES[2], ValidityEffect.LIMITATION),
    ],
    ids=lambda p: p.name if isinstance(p, EdgeCase) else p.value,
)
def test_short_magnets_cap_the_badge_and_a_15_mm_magnet_does_not(case: EdgeCase, effect: ValidityEffect) -> None:
    """Catches a threshold not applied at 0.10, and a cap or add-on that does not follow the e_edge of the kernel."""
    check = load_registry().equation("EQ-05").validity_checks[0]
    e_edge = _e_edge(case, 0.5)
    flag = evaluate_validity(check, "EQ-05", e_edge)
    assert flag.effect is effect
    if effect is ValidityEffect.LIMITATION:
        assert flag.one_sided_addon == e_edge
