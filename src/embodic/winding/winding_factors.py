"""Distribution, turn-averaged pitch and winding factors of concentrated spiral coils (EQ-08).

k_d,n = |sum_{k in A} s_k e^{j n alpha_k}| / N_A; k_p,avg,n = (1/N) sum_t |sin(n p sigma_t / 2)| (D15 eq. 6, EV-59);
k_w,n = k_d,n · k_p,avg,n. The phasor angle n·alpha_k is reduced in integers before any trigonometry.
"""

import cmath
import math
from collections.abc import Sequence

from embodic.model.vocabulary import Phase
from embodic.results import InputRef, Registry, Traceable, traced
from embodic.units import Unit
from embodic.winding.star_of_slots import CoilAssignment


def distribution_factor(assignment: Sequence[CoilAssignment], harmonic: int, coil_count: int) -> float:
    """Return k_d,n of phase A; 0.0 when no coil carries phase A."""
    coils = [c for c in assignment if c.phase is Phase.A]
    if not coils:
        return 0.0
    phasor_sum = sum(
        c.polarity * cmath.exp(2j * math.pi * (harmonic * c.phasor_index % coil_count) / coil_count) for c in coils
    )
    return abs(phasor_sum) / len(coils)


def turn_averaged_pitch_factor(harmonic: int, poles: int, spans_rad: Sequence[float]) -> float:
    """Return (1/N) sum_t |sin(n p sigma_t / 2)| over the turn spans sigma_t (mechanical radians)."""
    if not spans_rad:
        raise ValueError("at least one turn span is needed")
    p = poles // 2
    return math.fsum(abs(math.sin(harmonic * p * sigma / 2)) for sigma in spans_rad) / len(spans_rad)


def compute_winding_factors(
    assignment: Sequence[CoilAssignment],
    poles: int,
    coil_count: int,
    spans_rad: Sequence[float],
    harmonics: Sequence[int],
    registry: Registry,
) -> dict[int, Traceable[float]]:
    """Return k_w,n for each harmonic order n as a Traceable value of EQ-08."""
    inputs = (
        InputRef(
            pointer="/winding/coil/coil_count", value=coil_count, unit=Unit.ONE, provenance=None, kind=None, label=None
        ),
        InputRef(pointer="/rotor/poles", value=poles, unit=Unit.ONE, provenance=None, kind=None, label=None),
        InputRef(
            pointer="result:turn_span_mean_rad",
            value=math.fsum(spans_rad) / len(spans_rad),
            unit=Unit.RAD,
            provenance=None,
            kind=None,
            label=None,
        ),
    )
    return {
        n: traced(
            f"winding_factor_{n}",
            distribution_factor(assignment, n, coil_count) * turn_averaged_pitch_factor(n, poles, spans_rad),
            Unit.ONE,
            eq_ids=("EQ-08",),
            inputs=inputs,
            registry=registry,
        )
        for n in harmonics
    }
