"""Own star of slots and winding factor of tooth-wound coils, written from EQ-08 text and EV-90, not from embodic.

Coil k sits at mechanical angle 2*pi*k/Q, so its EMF phasor is at p*360*k/Q electrical degrees (p pole pairs,
Alberti and Bianchi EV-90 slide 5). Belts are half-open 60 degree sectors [b*60 - 30, b*60 + 30) in the order
A+, C-, B+, A-, C+, B- (equation_specification.md EQ-08, ABC sequence). Angles are exact Fractions, so a phasor on a
belt edge is an exact tie.

Fundamental pitch factor of a coil spanning one slot pitch: k_p,n = |sin(n p pi / Q)| (pitch factor
sin(n * span_electrical / 2) with span_electrical = p * 2 pi / Q). k_w = k_d * k_p.
"""

import cmath
import math
from fractions import Fraction

BELT_ORDER = (("A", 1), ("C", -1), ("B", 1), ("A", -1), ("C", 1), ("B", -1))


def phasor_deg(k: int, coil_count: int, poles: int) -> Fraction:
    """Return the exact electrical angle of coil k in degrees, reduced to [0, 360)."""
    return Fraction(360 * k * (poles // 2), coil_count) % 360


def star_of_slots(coil_count: int, poles: int) -> list[tuple[str, int]]:
    """(phase, polarity) of every coil in index order."""
    out = []
    for k in range(coil_count):
        belt = math.floor((phasor_deg(k, coil_count, poles) + 30) / 60) % 6
        out.append(BELT_ORDER[belt])
    return out


def distribution_factor(coil_count: int, poles: int, harmonic: int = 1) -> float:
    """Return k_d,n of phase A from the signed phasors of its coils."""
    total = 0j
    count = 0
    for k, (phase, sign) in enumerate(star_of_slots(coil_count, poles)):
        if phase == "A":
            total += sign * cmath.exp(1j * math.radians(float(harmonic * phasor_deg(k, coil_count, poles) % 360)))
            count += 1
    return abs(total) / count


def tooth_pitch_factor(coil_count: int, poles: int, harmonic: int = 1) -> float:
    """Return k_p,n of a coil spanning one slot pitch."""
    return abs(math.sin(harmonic * (poles // 2) * math.pi / coil_count))


def winding_factor(coil_count: int, poles: int, harmonic: int = 1) -> float:
    """Return k_w,n = k_d,n * k_p,n."""
    return distribution_factor(coil_count, poles, harmonic) * tooth_pitch_factor(coil_count, poles, harmonic)
