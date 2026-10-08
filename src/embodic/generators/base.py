"""Generator plug-in protocol (interfaces.md section 6, ADR-0012)."""

import math
from collections.abc import Mapping
from typing import ClassVar, Protocol

from embodic.drc.report import violates
from embodic.errors import Unbuildable
from embodic.geometry.layout import BoardStack
from embodic.model.design import DesignParameters
from embodic.model.drc_rules import DrcRules
from embodic.model.vocabulary import TopologyKind
from embodic.results import Registry


class Generator(Protocol):
    """A topology generator. Pure; never raises for user input; deterministic (same design -> same stack_hash)."""

    kind: ClassVar[TopologyKind]

    def generate(self, design: DesignParameters, registry: Registry) -> BoardStack | Unbuildable:
        """Build the boards of ``design`` or say why it cannot be built."""
        ...


def unusable_sizes(positive: Mapping[str, float], trace_pointer: str, width_mm: float, rules: DrcRules) -> list[str]:
    """Pointers of sizes no geometry can be built from (D-030), so a generator refuses before it builds anything.

    A size in ``positive`` must be finite and above 0. The trace width must also not be below the DRC minimum: a
    denormal or sub-micron width drives the turn counts and the arithmetic of the builders out of range.
    """
    bad = [pointer for pointer, v in positive.items() if not (math.isfinite(v) and v > 0)]
    if not (math.isfinite(width_mm) and width_mm > 0) or violates(width_mm, rules.min_trace_width_mm):
        bad.append(trace_pointer)
    return bad
