"""The spiral winding plan of a design: assignment, pattern, feasibility and winding factors (interfaces.md §4)."""

import cmath
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType

from embodic.errors import IssueCategory, Severity, Unbuildable, ValidationIssue, message_for
from embodic.model.design import DesignParameters
from embodic.model.vocabulary import ConnectionTopology, Phase
from embodic.model.winding_specs import CoilAssignmentInput, SpiralWindingSpec
from embodic.results import Registry, Traceable
from embodic.winding.feasibility import Feasibility, check_feasibility
from embodic.winding.star_of_slots import CoilAssignment, assign_phases, is_balanced, phasor_index
from embodic.winding.winding_factors import compute_winding_factors

PLAN_HARMONICS = (1, 3, 5, 7)
# EQ-08 tolerance (equations.v1.json): 1e-9. A smaller k_w3 is zero up to float noise, e.g. 12/16 gives 2.4e-16.
TRIPLEN_ZERO = 1e-9

_KIND_BY_PREFIX: Mapping[str, tuple[IssueCategory, Severity]] = MappingProxyType(
    {
        "UNBUILDABLE_": (IssueCategory.UNBUILDABLE, Severity.ERROR),
        "RANGE_": (IssueCategory.UNSUPPORTED_RANGE, Severity.WARNING),
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class SpiralWindingPlan:
    """Phase plan of one layer pair; with one phase per pair (M4) it is the template every pair repeats."""

    feasibility: Feasibility
    assignment: tuple[CoilAssignment, ...]
    pattern: str  # "AabBCcaABbcC", upper = +, lower = -
    winding_factors: Mapping[int, Traceable[float]]  # harmonic order -> k_w,n


def plan_spiral_winding(
    design: DesignParameters, spec: SpiralWindingSpec, registry: Registry
) -> SpiralWindingPlan | Unbuildable:
    """Plan the phases of a spiral design, or say why it cannot be built.

    The star of slots decides unless `spec.assignment` lists a manual assignment, which is accepted even when
    unbalanced (`plan_issues` warns). Winding factors use the outermost-turn span 2π/Q as in A2-TOP §2.2; the generator
    passes the real turn spans to `compute_winding_factors` for the turn-averaged values.
    """
    coils, poles = spec.coil.coil_count, design.rotor.poles
    phase_per_pair = bool(spec.layers.pairs) and all(
        pair.phases is not None and len(pair.phases) == 1 for pair in spec.layers.pairs
    )
    feasibility = check_feasibility(coils, poles, design.phases, phase_per_pair=phase_per_pair)
    issues: list[ValidationIssue] = []
    if spec.assignment is None:
        assignment = assign_phases(coils, poles, design.phases, spec.phase_sequence)
        if not feasibility.balanced:
            issues.append(_issue("UNBUILDABLE_UNBALANCED_WINDING", ["/winding/coil/coil_count", "/rotor/poles"]))
    elif sorted(c.coil_index for c in spec.assignment) != list(range(coils)):
        issues.append(_issue("UNBUILDABLE_ASSIGNMENT_COVERAGE", ["/winding/assignment"]))
        assignment = ()
    else:
        assignment = _manual(spec.assignment, coils, poles)
        if not phase_per_pair:
            feasibility = replace(feasibility, balanced=is_balanced(assignment, coils, spec.phase_sequence))
    if spec.parallel_paths > feasibility.max_parallel_paths:
        issues.append(
            _issue(
                "UNBUILDABLE_PARALLEL_PATHS_EXCEED_T",
                ["/winding/parallel_paths"],
                value=spec.parallel_paths,
                limit=feasibility.max_parallel_paths,
            )
        )
    if issues:
        return Unbuildable(issues=tuple(issues))
    return SpiralWindingPlan(
        feasibility=feasibility,
        assignment=assignment,
        pattern="".join(c.phase.value if c.polarity == 1 else c.phase.value.lower() for c in assignment),
        winding_factors=compute_winding_factors(
            assignment, poles, coils, (2 * math.pi / coils,), PLAN_HARMONICS, registry
        ),
    )


def plan_issues(plan: SpiralWindingPlan, design: DesignParameters) -> tuple[ValidationIssue, ...]:
    """Return the warnings a buildable plan carries: delta with k_w3 not zero, an unbalanced manual assignment."""
    issues: list[ValidationIssue] = []
    kw3 = plan.winding_factors[3].value
    if design.connection.topology is ConnectionTopology.DELTA and kw3 > TRIPLEN_ZERO:
        issues.append(_issue("RANGE_DELTA_TRIPLEN", ["/connection/topology"], value=kw3, limit=0))
    manual = isinstance(design.winding, SpiralWindingSpec) and design.winding.assignment is not None
    if manual and not plan.feasibility.balanced:
        spread = _phase_magnitude_spread(plan.assignment, plan.feasibility.coils)
        issues.append(_issue("RANGE_MANUAL_ASSIGNMENT_UNBALANCED", ["/winding/assignment"], value=spread))
    return tuple(issues)


def _issue(
    code: str, pointers: Sequence[str], *, value: float | int | None = None, limit: float | int | None = None
) -> ValidationIssue:
    """Build a winding issue; the code prefix sets category and severity (UNBUILDABLE_ error, RANGE_ warning)."""
    category, severity = next(kind for prefix, kind in _KIND_BY_PREFIX.items() if code.startswith(prefix))
    return ValidationIssue(
        code=code,
        category=category,
        severity=severity,
        message=message_for(code).format(limit=limit),
        pointers=tuple(pointers),
        value=value,
        limit=limit,
        eq_ids=("EQ-08",),
    )


def _manual(entries: Sequence[CoilAssignmentInput], coils: int, poles: int) -> tuple[CoilAssignment, ...]:
    return tuple(
        CoilAssignment(
            coil_index=e.coil_index,
            phasor_index=phasor_index(e.coil_index, coils, poles),
            phase=e.phase,
            polarity=e.polarity,
        )
        for e in sorted(entries, key=lambda e: e.coil_index)
    )


def _phase_magnitude_spread(assignment: Sequence[CoilAssignment], coils: int) -> float:
    """Return (max − min)/max of the fundamental phase EMF phasor magnitudes; 0 for a balanced winding."""
    magnitudes = [
        abs(sum(c.polarity * cmath.exp(2j * math.pi * c.phasor_index / coils) for c in assignment if c.phase is phase))
        for phase in Phase
    ]
    largest = max(magnitudes)
    return (largest - min(magnitudes)) / largest if largest > 0 else 0.0
