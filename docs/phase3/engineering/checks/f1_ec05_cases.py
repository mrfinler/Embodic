"""Fix wave F1 item B (REQ-T-08 b, UT-PHY-21): EC-05 values derived from the registry formula (U-E17, Agent 2).

Run from the repository root: PYTHONPATH=src python3 docs/phase3/engineering/checks/f1_ec05_cases.py

The expected values come from the registry text alone (resources/evidence/equations.v1.json): EQ-05 B_z,1 in its
cosh/sinh form, EQ-04 alpha_p(r) for block magnets, and EC-05 e_edge = sum w D_e exp(-d / (c_e G)) / sum w with
w = |B_z,1 r dr|. The segment set is the Phase 1 one (docs/phase1/engineering/checks/edge_zone_d09.js l.34-37 and
l.50-56): one radial line over the coil annulus clipped to the magnet span, at z = G. scipy.integrate.quad gives the
converged integral; the 4000-point midpoint sum repeats the Phase 1 arithmetic. embodic is imported only for the
cross-check of what its kernel returns on the same line (integrate_path, edge_leakage_fraction).
"""

import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import quad

from embodic.geometry.primitives import Line, PrimitiveRole
from embodic.model.rotor import ArcMagnet, BlockMagnet, RotorSpec, RotorType
from embodic.physics.emf import edge_leakage_fraction, field_table, integrate_path

ROOT = Path(__file__).resolve().parents[4]
EQ = {e["id"]: e for e in json.loads((ROOT / "resources/evidence/equations.v1.json").read_text())["equations"]}
EC05 = EQ["EQ-05"]["validity_checks"][0]
D_E, C_E = EC05["parameters"]["D_e"], EC05["parameters"]["c_e"]


def bz1(r: float, z: float, g: float, p: int, br: float, mu_r: float, lm: float, alpha: float) -> float:
    """EQ-05, n = 1: K_1 cosh(u (G - z)) / (cosh(u G) + mu_r coth(u l_m) sinh(u G)), u = p / r."""
    u = p / r
    k1 = 4 * br / math.pi * math.sin(math.pi * alpha / 2)
    return k1 * math.cosh(u * (g - z)) / (math.cosh(u * g) + mu_r / math.tanh(u * lm) * math.sinh(u * g))


def block_alpha(width: float, p: int):
    """EQ-04: alpha_p(r) = 2 p asin(w_PM / (2 r)) / pi."""
    return lambda r: 2 * p * math.asin(width / (2 * r)) / math.pi


CASES = {
    "default_12_16": dict(r_a=18.0, r_b=38.0, coil=(18.0, 38.0), p=8, br=1.315, mu_r=1.05, lm=2.0, g=1.31,
                          alpha=block_alpha(6.0, 8), block=(6.0, 20.0, 28.0)),
    "O1_D08": dict(r_a=15.4, r_b=43.4, coil=(12.5, 44.0), p=5, br=1.38, mu_r=1.05, lm=5.0, g=1.4,
                   alpha=lambda r: 0.72, block=None),
    "O2_D09_N8": dict(r_a=25.0, r_b=46.0, coil=(25.2, 47.6), p=8, br=1.33, mu_r=1.05, lm=2.0, g=1.5,
                      alpha=lambda r: 0.8, block=None),
}  # fmt: skip


def weight(c: dict, r: float) -> float:
    """EC-05 weight |B_z,1 r| at z = G."""
    return abs(bz1(r, c["g"], c["g"], c["p"], c["br"], c["mu_r"], c["lm"], c["alpha"](r))) * r


def e_edge_quad(c: dict) -> tuple[float, float]:
    """Converged e_edge and the larger relative error estimate of the two integrals."""
    a, b = max(c["r_a"], c["coil"][0]), min(c["r_b"], c["coil"][1])
    lam = C_E * c["g"]
    num = quad(lambda r: weight(c, r) * math.exp(-min(r - c["r_a"], c["r_b"] - r) / lam), a, b,
               points=[(c["r_a"] + c["r_b"]) / 2], epsabs=0, epsrel=1e-13, limit=500)  # fmt: skip
    den = quad(lambda r: weight(c, r), a, b, epsabs=0, epsrel=1e-13, limit=500)
    return D_E * num[0] / den[0], max(num[1] / num[0], den[1] / den[0])


def e_edge_midpoint(c: dict, n: int) -> float:
    """Phase 1 arithmetic: n-point midpoint sums (edge_zone_d09.js l.50-54)."""
    a, b = max(c["r_a"], c["coil"][0]), min(c["r_b"], c["coil"][1])
    lam = C_E * c["g"]
    r = a + (b - a) * (np.arange(n) + 0.5) / n
    w = np.array([weight(c, x) for x in r])
    d = np.minimum(r - c["r_a"], c["r_b"] - r)
    return float(D_E * np.sum(w * np.exp(-d / lam)) / np.sum(w))


def e_edge_kernel(c: dict, max_segment_mm: float) -> float:
    """Cross-check only: embodic integrate_path on one radial line, field table at z = G."""
    if c["block"]:
        width, length, centre = c["block"]
        magnet = BlockMagnet(width_mm=width, length_mm=length, r_center_mm=centre, thickness_mm=c["lm"])
    else:
        magnet = ArcMagnet(pole_arc_ratio=c["alpha"](0.0), r_inner_mm=c["r_a"], r_outer_mm=c["r_b"],
                           thickness_mm=c["lm"])  # fmt: skip
    rotor = RotorSpec(poles=2 * c["p"], rotor_type=RotorType.DOUBLE, magnet=magnet, remanence_t=c["br"],
                      recoil_permeability=c["mu_r"], air_gap_mm=1.0, back_iron_thickness_mm=5.0)  # fmt: skip
    table = field_table(rotor, c["g"], c["g"], (1,))
    line = Line(x1_mm=c["coil"][0], y1_mm=0.0, x2_mm=c["coil"][1], y2_mm=0.0, width_mm=0.5, role=PrimitiveRole.SIDE)
    field = integrate_path([line], table, c["p"], max_segment_mm, C_E * c["g"])
    return edge_leakage_fraction([field], D_E)


def variant_e_edge(c: dict, lam: float, z: float, with_r: bool, near_end: bool) -> float:
    """e_edge of case c with one ingredient of the EC-05 metric changed."""
    a, b = max(c["r_a"], c["coil"][0]), min(c["r_b"], c["coil"][1])
    pick = min if near_end else max

    def w(r: float) -> float:
        f = abs(bz1(r, z, c["g"], c["p"], c["br"], c["mu_r"], c["lm"], c["alpha"](r)))
        return f * r if with_r else f

    num = quad(lambda r: w(r) * math.exp(-pick(r - c["r_a"], c["r_b"] - r) / lam), a, b, limit=500)[0]
    return D_E * num / quad(w, a, b, limit=500)[0]


def mean_alpha(c: dict):
    """alpha_p frozen at the mean magnet radius."""
    a = c["alpha"]((c["r_a"] + c["r_b"]) / 2)
    return lambda r: a


def defect_shifts() -> None:
    """Shift of e_edge (pp) under each defect UT-PHY-21 must catch at 0.1 pp."""
    variants = {
        "decay length G instead of c_e G (c_e 1.0)": lambda c: variant_e_edge(c, c["g"], c["g"], True, True),
        "d to the farther magnet end": lambda c: variant_e_edge(c, C_E * c["g"], c["g"], True, False),
        "weight without r": lambda c: variant_e_edge(c, C_E * c["g"], c["g"], False, True),
        "z = 0 (magnet face) instead of G": lambda c: variant_e_edge(c, C_E * c["g"], 0.0, True, True),
        "alpha_p at the mean radius (block)": lambda c: variant_e_edge(
            {**c, "alpha": mean_alpha(c)}, C_E * c["g"], c["g"], True, True
        ),
    }
    for label, run in variants.items():
        shifts = ", ".join(f"{k} {100 * (run(c) - e_edge_quad(c)[0]):+.4f}" for k, c in CASES.items())
        print(f"defect '{label}': {shifts} pp")


CAP_CASES = {
    f"D09 rotor, magnet radial length {length} mm": dict(
        r_a=35.5 - length / 2, r_b=35.5 + length / 2, coil=(35.5 - length / 2, 35.5 + length / 2), p=8, br=1.33,
        mu_r=1.05, lm=2.0, g=1.5, alpha=lambda r: 0.8, block=None)
    for length in (10.0, 12.0, 15.0)
}  # fmt: skip


if __name__ == "__main__":
    print(f"registry EC-05: D_e {D_E}, c_e {C_E}, threshold {EC05['threshold']}, consequences {EC05['consequences']}")
    for name, c in {**CASES, **CAP_CASES}.items():
        q, err = e_edge_quad(c)
        mid = e_edge_midpoint(c, 4000)
        k05, k01 = e_edge_kernel(c, 0.5), e_edge_kernel(c, 0.1)
        print(f"{name}: quad {100 * q:.6f} % (rel err est {err:.1e}); midpoint 4000 {100 * mid:.6f} %; "
              f"embodic kernel 0.5 mm {100 * k05:.6f} % (diff {100 * (k05 - q):+.5f} pp), "
              f"0.1 mm {100 * k01:.6f} % (diff {100 * (k01 - q):+.5f} pp)")  # fmt: skip
    defect_shifts()
