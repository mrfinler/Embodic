"""3-phase feasibility of Q concentrated coils under 2p poles, in integer arithmetic only (EQ-08)."""

from dataclasses import dataclass
from fractions import Fraction
from math import gcd

from embodic.winding.star_of_slots import assign_phases, is_balanced, require_three_phases


@dataclass(frozen=True, slots=True, kw_only=True)
class Feasibility:
    """Whether Q coils and 2p poles give a balanced winding, with q, t and the parallel-path limit."""

    coils: int
    poles: int
    phases: int
    q: Fraction
    periodicity: int  # t = gcd(Q, p)
    balanced: bool
    max_parallel_paths: int


def check_feasibility(coil_count: int, poles: int, phases: int = 3, *, phase_per_pair: bool = False) -> Feasibility:
    """Check a coil and pole count.

    All phases on every layer pair (FSCW): q = Q/(2p·m); balanced when the pre-check Q mod m = 0 and (Q/t) mod m = 0
    holds and the exact star of slots confirms it (EQ-08). One phase per layer pair (option M4): each phase owns all
    Q coils of its pair, so q = Q/(2p); only the full-pitch construction Q = 2p of A2-TOP §2.3 option B is balanced
    (phases B and C come from pair rotation by 2π/(m·p), not from the star of slots).
    """
    require_three_phases(phases)
    t = gcd(coil_count, poles // 2)
    if phase_per_pair:
        q = Fraction(coil_count, poles)
        balanced = coil_count == poles
    else:
        q = Fraction(coil_count, phases * poles)
        pre_check = coil_count % phases == 0 and (coil_count // t) % phases == 0
        balanced = pre_check and is_balanced(assign_phases(coil_count, poles, phases), coil_count)
    return Feasibility(
        coils=coil_count, poles=poles, phases=phases, q=q, periodicity=t, balanced=balanced, max_parallel_paths=t
    )


def balanced_coil_counts(poles: int, phases: int = 3, max_coils: int = 96) -> tuple[int, ...]:
    """Return every coil count from 1 to `max_coils` that gives a balanced FSCW winding under `poles` poles."""
    return tuple(q for q in range(1, max_coils + 1) if check_feasibility(q, poles, phases).balanced)
