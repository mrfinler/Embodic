"""Item 4: OR-01 reproduced with an own EQ-05/EQ-06 implementation on the subject's D08 layout.

Measured on 24b33f2: own 0.0308780 V s/rad, embodic 0.0308768 (-3.8e-5 relative). An own 48-step linear table
accounts for 1.4e-5 of it; 2.5e-5 is unexplained (README, open question). The chord step moves own Ke by 2e-7.
Defect caught: a field, z or phase-sum change in embodic that moves Ke_LL by more than 1e-4 relative.
"""

import or01
import pytest

pytestmark = pytest.mark.req("REQ-F-11")

EMBODIC_VS_OWN_REL = 1e-4  # 2.6 x the measured gap; the 48-step table alone gives 1.4e-5
D08_BAND = 0.08  # D08 p.98, OR-01 band lower edge (test_plan.md section 4)


def test_or01_ke_line_peak_agrees_with_own_field_and_d08_measurement() -> None:
    """Embodic Ke_LL within 1e-4 of the own value; the own value inside D08's 8 % band."""
    got = or01.run()
    assert abs(got["embodic_vs_own_rel"]) <= EMBODIC_VS_OWN_REL, got
    assert abs(got["own_vs_measured_rel"]) <= D08_BAND, got


def test_subject_copper_z_matches_own_two_layer_faces() -> None:
    """Copper z plus air gap equals the own foil z from the magnet face (a z or gap offset error)."""
    got = or01.run()
    for layer, z in got["subject_copper_z_mm"].items():
        assert z + got["air_gap_mm"] == pytest.approx(got["own_z_from_magnet_mm"][layer], abs=1e-12)
