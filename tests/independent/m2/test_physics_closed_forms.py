"""Item 2: EQ-05 magnetic-circuit limit and EQ-06 flux linkage of one sector loop, against closed forms.

EQ-05 at z = 0 with u = n p / r -> 0: coth(u l_m) -> 1 / (u l_m) and sinh(u G) -> u G, so
B_z,n -> K_n l_m / (l_m + mu_r G), the 1-D magnetic circuit of a magnet of thickness l_m in series with an air
length G (equation_specification.md EQ-05 formula; reference CF-01 = 1.162077823 T).

EQ-06 on a loop with radial legs at -sigma/2 and +sigma/2 in a uniform injected B_1: the outgoing leg collects
B_1 (r_b^2 - r_a^2) / 2 e^{+j p sigma / 2}, the return leg the negative at e^{-j p sigma / 2}, so
Ke_1 = B_1 (r_b^2 - r_a^2) sin(p sigma / 2) * 1e-6 V s/rad (CF-02's closed form, derived here again).
"""

import math

import numpy as np
import pytest

from embodic.geometry.primitives import Arc, Line, PrimitiveRole
from embodic.model.rotor import ArcMagnet, RotorSpec, RotorType
from embodic.physics import field_harmonic, integrate_path
from embodic.physics.emf import FIELD_TABLE_STEPS, FieldTable

pytestmark = pytest.mark.req("REQ-F-11")


def _rotor(poles: int, alpha: float) -> RotorSpec:
    return RotorSpec(
        poles=poles,
        rotor_type=RotorType.DOUBLE,
        magnet=ArcMagnet(pole_arc_ratio=alpha, r_inner_mm=10.0, r_outer_mm=30.0, thickness_mm=3.0),
        remanence_t=1.3,
        recoil_permeability=1.05,
        air_gap_mm=0.5,
        back_iron_thickness_mm=5.0,
    )


def _magnetic_circuit_peak(n: int, rotor: RotorSpec, g_mm: float) -> float:
    l_m = rotor.magnet.thickness_mm
    k_n = 4 * rotor.remanence_t / (n * math.pi) * math.sin(n * math.pi * rotor.magnet.pole_arc_ratio / 2)
    return k_n * l_m / (l_m + rotor.recoil_permeability * g_mm)


@pytest.mark.parametrize("n", [1, 3, 5])
def test_eq05_at_the_magnet_face_tends_to_the_magnetic_circuit_limit(n: int) -> None:
    """At u -> 0 the harmonic equals K_n l_m / (l_m + mu_r G) (a wrong denominator or z origin)."""
    rotor = _rotor(poles=2, alpha=0.85)
    g = 1.1
    bz, _ = field_harmonic(n, np.array([1e7]), np.array([0.0]), rotor, g, np.array([0.85]))
    assert float(bz[0]) == pytest.approx(_magnetic_circuit_peak(n, rotor, g), rel=1e-9)


def test_eq05_limit_reproduces_cf01() -> None:
    """The own limit reproduces the registry's CF-01 1-D value (an instrument defect)."""
    assert _magnetic_circuit_peak(1, _rotor(2, 0.85), 1.1) == pytest.approx(1.162077823, abs=1e-9)


def test_eq05_approaches_the_limit_from_below_as_the_pole_pitch_grows() -> None:
    """The 2-D field rises monotonically to the 1-D limit as r grows (a sign error in u)."""
    rotor = _rotor(poles=2, alpha=0.85)
    limit = _magnetic_circuit_peak(1, rotor, 1.1)
    gaps = [
        limit - float(field_harmonic(1, np.array([r]), np.array([0.0]), rotor, 1.1, np.array([0.85]))[0][0])
        for r in (10.0, 100.0, 1000.0)
    ]
    assert 0 < gaps[2] < gaps[1] < gaps[0]


def _sector_loop(r_lo: float, r_hi: float, sigma: float, width: float) -> list[Line | Arc]:
    a, b = -sigma / 2, sigma / 2
    return [
        Line(
            x1_mm=r_lo * math.cos(a),
            y1_mm=r_lo * math.sin(a),
            x2_mm=r_hi * math.cos(a),
            y2_mm=r_hi * math.sin(a),
            width_mm=width,
            role=PrimitiveRole.SIDE,
        ),
        Arc(cx_mm=0.0, cy_mm=0.0, r_mm=r_hi, start_rad=a, sweep_rad=sigma, width_mm=width, role=PrimitiveRole.END_TURN),
        Line(
            x1_mm=r_hi * math.cos(b),
            y1_mm=r_hi * math.sin(b),
            x2_mm=r_lo * math.cos(b),
            y2_mm=r_lo * math.sin(b),
            width_mm=width,
            role=PrimitiveRole.SIDE,
        ),
        Arc(
            cx_mm=0.0, cy_mm=0.0, r_mm=r_lo, start_rad=b, sweep_rad=-sigma, width_mm=width, role=PrimitiveRole.END_TURN
        ),
    ]


@pytest.mark.parametrize(("pole_pairs", "sigma"), [(5, math.radians(30)), (8, math.radians(22.5)), (4, 0.6)])
def test_eq06_sector_loop_in_a_uniform_field_matches_the_closed_form(pole_pairs: int, sigma: float) -> None:
    """Flux linkage of a sector loop equals B_1 (r_b^2 - r_a^2) sin(p sigma / 2) (dr sign, clip or angle errors)."""
    r_a, r_b, b1 = 12.0, 28.0, 0.8
    table = FieldTable(
        r_inner_mm=r_a,
        r_outer_mm=r_b,
        harmonics=(1,),
        bz_t=np.full((1, FIELD_TABLE_STEPS + 1), b1),
        bt_t=np.zeros((1, FIELD_TABLE_STEPS + 1)),
    )
    got = integrate_path(_sector_loop(8.0, 32.0, sigma, 0.3), table, pole_pairs, 0.5, 1.0)
    ke = abs(got.flux_linkage_t_mm2[0]) * 1e-6
    assert ke == pytest.approx(b1 * (r_b**2 - r_a**2) * math.sin(pole_pairs * sigma / 2) * 1e-6, rel=1e-12)
