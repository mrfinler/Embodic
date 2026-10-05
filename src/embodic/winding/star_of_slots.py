"""Exact star of slots for concentrated coils (EQ-08 `replace`; spiral_generator_spec.md step G7).

Angles are integers in units of 360°/(12Q) electrical, so a phasor on a belt edge is an exact tie, never a float
rounding accident (Xcoil `starOfSlots` defect C6, calculation_flow_and_port_notes.md section 2.3).
"""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, TypeAlias

from embodic.model.vocabulary import Phase
from embodic.model.winding_specs import PhaseSequence

Polarity: TypeAlias = Literal[1, -1]

THREE_PHASES = 3
_BELT_COUNT = 6

# Belt b covers [b·60° − 30°, b·60° + 30°); its phase and polarity, in the order of EQ-08.
BELTS: Mapping[PhaseSequence, tuple[tuple[Phase, Polarity], ...]] = MappingProxyType(
    {
        PhaseSequence.ABC: ((Phase.A, 1), (Phase.C, -1), (Phase.B, 1), (Phase.A, -1), (Phase.C, 1), (Phase.B, -1)),
        PhaseSequence.ACB: ((Phase.A, 1), (Phase.B, -1), (Phase.C, 1), (Phase.A, -1), (Phase.B, 1), (Phase.C, -1)),
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CoilAssignment:
    """Phase and polarity of one coil; its EMF phasor sits at `phasor_index`·2pi/Q electrical."""

    coil_index: int
    phasor_index: int
    phase: Phase
    polarity: Literal[1, -1]


def phasor_index(coil_index: int, coil_count: int, poles: int) -> int:
    """Return (k·p) mod Q, the exact electrical position of coil k in steps of 2pi/Q."""
    return coil_index * (poles // 2) % coil_count


def assign_phases(
    coil_count: int, poles: int, phases: int = 3, sequence: PhaseSequence = PhaseSequence.ABC
) -> tuple[CoilAssignment, ...]:
    """Assign phase and polarity to every coil by half-open 60° belts (EQ-08, G7).

    belt = floor((12·r + Q)/(2Q)) mod 6 with r = (k·p) mod Q; a coil on a belt edge goes to the belt that starts there.
    """
    require_three_phases(phases)
    assignment = []
    for k in range(coil_count):
        r = phasor_index(k, coil_count, poles)
        phase, polarity = BELTS[sequence][(12 * r + coil_count) // (2 * coil_count) % _BELT_COUNT]
        assignment.append(CoilAssignment(coil_index=k, phasor_index=r, phase=phase, polarity=polarity))
    return tuple(assignment)


def is_balanced(
    assignment: Iterable[CoilAssignment], coil_count: int, sequence: PhaseSequence = PhaseSequence.ABC
) -> bool:
    """Return True when the signed phasor sets of the lagging phases equal A's shifted by 120° and 240° exactly.

    A negative coil adds 180° to its phasor. The shift is 4Q and 8Q in units of 360°/(12Q).
    """
    turn = 12 * coil_count
    signed: dict[Phase, Counter[int]] = {phase: Counter() for phase in Phase}
    for c in assignment:
        signed[c.phase][(12 * c.phasor_index + (0 if c.polarity == 1 else 6 * coil_count)) % turn] += 1
    reference = signed[Phase.A]
    at_120 = signed[BELTS[sequence][2][0]]
    at_240 = signed[BELTS[sequence][4][0]]
    return (
        bool(reference)
        and at_120 == Counter({(a + 4 * coil_count) % turn: n for a, n in reference.items()})
        and at_240 == Counter({(a + 8 * coil_count) % turn: n for a, n in reference.items()})
    )


def require_three_phases(phases: int) -> None:
    """Raise for a phase count other than 3; the spiral model validation guarantees 3 (INVALID_SPIRAL_PHASES)."""
    if phases != THREE_PHASES:
        raise ValueError(f"the spiral star of slots is defined for 3 phases, got {phases}")
