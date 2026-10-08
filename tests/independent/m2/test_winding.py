"""Item 1: embodic's star of slots and k_w against own_winding.py and a published value.

Defects caught: a belt edge that rounds the wrong way, a lost polarity, k_p computed with mechanical instead of
electrical span, k_d averaged over the wrong phase.
"""

import math

import own_winding
import pytest

from embodic.results import load_registry
from embodic.winding import assign_phases, compute_winding_factors

COMBINATIONS = [(12, 16), (12, 10), (12, 14), (9, 8), (24, 22)]
# Emetor glossary "Concentrated winding", Fig. 2: double-layer 10-pole 12-slot winding factor 0.933
# (https://www.emetor.com/glossary/concentrated-winding/, read 2026-10-08). Every tooth wound = double layer.
PUBLISHED_KW1 = {(12, 10): 0.933}


@pytest.mark.parametrize(("coils", "poles"), COMBINATIONS)
def test_phase_and_polarity_of_every_coil_match_own_star_of_slots(coils: int, poles: int) -> None:
    """Every coil's phase and polarity equals the own Fraction-exact star of slots."""
    got = [(c.phase.value.upper(), c.polarity) for c in assign_phases(coils, poles)]
    assert got == own_winding.star_of_slots(coils, poles)


@pytest.mark.parametrize(("coils", "poles"), COMBINATIONS)
@pytest.mark.parametrize("harmonic", [1, 5, 7])
def test_winding_factor_of_one_slot_pitch_coil_matches_kd_times_kp(coils: int, poles: int, harmonic: int) -> None:
    """k_w,n of a one-turn coil spanning one slot pitch equals own k_d,n * k_p,n."""
    kw = compute_winding_factors(
        assign_phases(coils, poles), poles, coils, [2 * math.pi / coils], [harmonic], load_registry()
    )[harmonic].value
    assert kw == pytest.approx(own_winding.winding_factor(coils, poles, harmonic), abs=1e-12)


@pytest.mark.parametrize(("coils", "poles"), list(PUBLISHED_KW1))
def test_fundamental_winding_factor_matches_published_value(coils: int, poles: int) -> None:
    """k_w1 of 12/10 equals the published double-layer 0.933."""
    kw = compute_winding_factors(assign_phases(coils, poles), poles, coils, [2 * math.pi / coils], [1], load_registry())
    assert kw[1].value == pytest.approx(PUBLISHED_KW1[(coils, poles)], abs=5e-4)


def test_own_instrument_reproduces_the_published_value() -> None:
    """The own instrument gives 0.933 for 12/10 (an instrument defect)."""
    assert own_winding.winding_factor(12, 10) == pytest.approx(0.933, abs=5e-4)
