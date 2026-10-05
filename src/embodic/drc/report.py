"""DRC result vocabulary (interfaces.md section 7) and the rule each check kind applies."""

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Literal

from embodic.model.drc_rules import DrcRules

DRC_EPSILON_MM: float = 1e-6
MAX_REPORTED_VIOLATIONS = 1000


class DrcCheckKind(StrEnum):
    """One family of DRC checks; ``issue_code`` names its message in the catalogue."""

    TRACE_TRACE = "trace_trace"
    TRACE_VIA = "trace_via"
    VIA_VIA = "via_via"
    PAD_TRACE = "pad_trace"
    PAD_PAD = "pad_pad"
    COPPER_EDGE = "copper_edge"
    COPPER_HOLE = "copper_hole"
    MIN_WIDTH = "min_width"
    MIN_DRILL = "min_drill"
    ANNULAR_RING = "annular_ring"

    @property
    def issue_code(self) -> str:
        """Return the catalogue code, e.g. ``DRC_TRACE_TRACE``."""
        return f"DRC_{self.name}"


# Xcoil applies one clearance to every pair (engine.js runDrc l.756); the split below is an embodic assumption:
# lands (vias and pads) keep the via clearance from each other, traces keep the trace clearance from traces and pads.
REQUIRED_MM: Mapping[DrcCheckKind, Callable[[DrcRules], float]] = MappingProxyType(
    {
        DrcCheckKind.TRACE_TRACE: lambda r: r.trace_clearance_mm,
        DrcCheckKind.TRACE_VIA: lambda r: r.via_clearance_mm,
        DrcCheckKind.VIA_VIA: lambda r: r.via_clearance_mm,
        DrcCheckKind.PAD_TRACE: lambda r: r.trace_clearance_mm,
        DrcCheckKind.PAD_PAD: lambda r: r.via_clearance_mm,
        DrcCheckKind.COPPER_EDGE: lambda r: r.edge_clearance_mm,
        DrcCheckKind.COPPER_HOLE: lambda r: r.hole_clearance_mm,
        DrcCheckKind.MIN_WIDTH: lambda r: r.min_trace_width_mm,
        DrcCheckKind.MIN_DRILL: lambda r: r.min_drill_mm,
        DrcCheckKind.ANNULAR_RING: lambda r: r.min_annular_ring_mm,
    }
)


def violates(measured_mm: float, required_mm: float, epsilon_mm: float = DRC_EPSILON_MM) -> bool:
    """Rule D-006: a violation is a measured value below ``required - epsilon``; there is no slack band."""
    return measured_mm < required_mm - epsilon_mm


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcViolation:
    """One failed check; ``objects`` are ids such as ``path:17/prim:4``, ``via:33``, ``pad:2``, ``hole:1``.

    Board edge ids name the loop: ``edge:outer/prim:5`` on the outer edge, ``edge:cutout0/prim:2`` on the first cutout.
    """

    kind: DrcCheckKind
    layer: str | None  # None for checks that hold on every layer (through vias, through-hole pads, drills)
    measured_mm: float
    required_mm: float
    at_mm: tuple[float, float]
    objects: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcCheckSummary:
    """Least measured value of one check kind over the pairs or objects it checked; None when it checked none."""

    kind: DrcCheckKind
    measured_min_mm: float | None
    required_mm: float
    pairs_checked: int


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcReport:
    """Outcome of ``run_drc``; ``violations`` holds the worst ``MAX_REPORTED_VIOLATIONS`` of ``violation_count``."""

    passed: bool
    summaries: tuple[DrcCheckSummary, ...]
    violations: tuple[DrcViolation, ...]
    violation_count: int
    method: Literal["grid+exact", "symmetric+grid+exact"]
    epsilon_mm: float = DRC_EPSILON_MM


class CancelToken:
    """Cooperative cancellation, checked between stages and inside chunked kernels. Thread-safe flag."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        """Ask the running check to stop; ``run_drc`` then returns None."""
        self._event.set()

    @property
    def cancelled(self) -> bool:
        """Return whether ``cancel`` was called."""
        return self._event.is_set()
