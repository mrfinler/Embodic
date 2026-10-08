"""Item 2c: EC-05 edge-leakage metric and its grading, own e_edge against compute() on the D08 example.

Own metric from the registry text (equation_registry.json EC-05): e_edge = D_e sum w exp(-d / (c_e G)) / sum w,
w = abs(B_z1 r_m dr), d = min(r_m - r_A, r_B - r_m), D_e 0.47, c_e 0.9; own field and 0.05 mm chords (own_emf.py).
Rule: e_edge > 0.10 caps the badge at unresolved. Measured on 24b33f2: own 0.017406 vs 0.017380 (base) and 0.27472 vs
0.27418 (magnet span 28 to 31 mm), 0.14 % and 0.20 %; the 48-step table and 0.5 mm chords of embodic give the gap.
Defects caught: a wrong decay length or amplitude, d measured from the wrong edge, a cap that never fires.
"""

import dataclasses

import numpy as np
import own_emf
import pytest

from embodic.api import compute
from embodic.io.examples import load_example
from embodic.results import Status

pytestmark = pytest.mark.req("REQ-F-11")

D_E, C_E = 0.47, 0.9
REL = 0.01  # 5 x the measured gap


def _own_e_edge(design, boards) -> float:
    rot = design.rotor
    g = boards.stack_thickness_mm / 2 + rot.air_gap_mm  # EQ-05 G of a double rotor, (t + 2 g) / 2
    field = own_emf.Field(
        rot.poles,
        rot.remanence_t,
        rot.recoil_permeability,
        rot.magnet.thickness_mm,
        g,
        rot.magnet.pole_arc_ratio,
        rot.magnet.r_inner_mm,
        rot.magnet.r_outer_mm,
    )
    num = den = 0.0
    for layout in boards.boards:
        for path in layout.paths:
            z = layout.copper_z_mm[path.layer] + rot.air_gap_mm
            for prim in path.primitives:
                pts = own_emf.chord_points(prim, 0.05)
                r = np.hypot(pts[:, 0], pts[:, 1])
                c1, c2 = np.clip(r[:-1], field.r_a_mm, field.r_b_mm), np.clip(r[1:], field.r_a_mm, field.r_b_mm)
                keep = c2 != c1
                rm = (c1 + c2)[keep] / 2
                w = np.abs(field.bz(1, rm, z) * rm * (c2 - c1)[keep])
                d = np.minimum(rm - field.r_a_mm, field.r_b_mm - rm)
                num += float(np.sum(w * np.exp(-d / (C_E * g))))
                den += float(np.sum(w))
    return D_E * num / den


def _variant(r_inner: float | None):
    _, design = load_example("spiral_12c10p_d08")
    if r_inner is not None:
        magnet = dataclasses.replace(design.rotor.magnet, r_inner_mm=r_inner, r_outer_mm=r_inner + 3.0)
        design = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, magnet=magnet))
    outcome = compute(design, {})
    assert outcome is not None and outcome.analysis is not None
    return design, outcome


@pytest.mark.parametrize(("r_inner", "capped"), [(None, False), (28.0, True)])
def test_edge_leakage_matches_own_metric_and_caps_the_badge_above_ten_percent(r_inner, capped: bool) -> None:
    """e_edge within 1 % of the own metric; Ke_LL is unresolved with the EC-05 reason exactly when e_edge > 0.10."""
    design, outcome = _variant(r_inner)
    got = outcome.analysis.edge_leakage_fraction.value
    assert got == pytest.approx(_own_e_edge(design, outcome.boards), rel=REL)
    assert (got > 0.10) is capped
    ke = outcome.analysis.ke_line_peak_v_s_per_rad
    has_reason = any("EC-05" in reason for reason in ke.status_reasons)
    assert has_reason is capped
    if capped:
        assert ke.status is Status.UNRESOLVED
