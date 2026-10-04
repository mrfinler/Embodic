"""Status vocabulary and the badge rule of D-007: badge = calculation trust, never input provenance (ADR-0003).

The badge of a result is the weakest of three things over its equation chain: the evidence status of each equation
(gate `cannot verify yet` gives `unresolved`), the implementation test state, and the validity cap. `derive_badge` is
a pure function of exactly those inputs, so no value typed by the user can move a badge.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class Status(StrEnum):
    """The five status labels of every claim and result."""

    VERIFIED = "verified"
    INFERRED = "inferred"
    ASSUMPTION = "assumption"
    UNRESOLVED = "unresolved"
    NOT_TESTED = "not tested"


STATUS_ORDER_WEAKEST_FIRST: tuple[Status, ...] = (
    Status.UNRESOLVED,
    Status.NOT_TESTED,
    Status.ASSUMPTION,
    Status.INFERRED,
    Status.VERIFIED,
)


class GateVerdict(StrEnum):
    """Equation gate of `equation_registry.json`."""

    REUSE = "reuse"
    REUSE_WITH_CHANGE = "reuse with change"
    REPLACE = "replace"
    ADD = "add"
    CANNOT_VERIFY_YET = "cannot verify yet"


class ValidityEffect(StrEnum):
    """What a validity check does to the badge."""

    CAP = "cap"  # badge capped at unresolved
    LIMITATION = "limitation"  # badge unchanged; limitation listed, optional one-sided tolerance add-on


class MetricBound(StrEnum):
    """How the computed validity metric relates to the true value."""

    ESTIMATE = "estimate"
    LOWER_BOUND = "lower_bound"  # true value is at least the metric (EC-05: |B| proxy for B_z, DEF-23 a)
    UPPER_BOUND = "upper_bound"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidityFlag:
    """Outcome of one validity check for one design."""

    code: str  # "RANGE_SKIN_DEPTH", "EC-05"
    message: str
    eq_id: str
    effect: ValidityEffect
    metric: float | None = None
    metric_bound: MetricBound = MetricBound.ESTIMATE
    one_sided_addon: float | None = None
    calibration_status: Status | None = None  # EC-05: inferred (one D09 case)
    transfer_status: Status | None = None  # EC-05: assumption (calibration applied to this rotor)
    threshold_status: Status | None = None  # EC-05: assumption (10 % cap)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChainLink:
    """What the badge rule reads about one equation of a result's chain."""

    eq_id: str
    gate: GateVerdict
    evidence: Status
    tests_passed: bool  # every test the registry links to this equation passed in this build


def weakness(status: Status) -> int:
    """Return the rank of a status, 0 for the weakest (`unresolved`)."""
    return STATUS_ORDER_WEAKEST_FIRST.index(status)


def combine_status(first: Status, *rest: Status) -> Status:
    """Return the weakest of the given statuses."""
    return min((first, *rest), key=weakness)


def derive_badge(chain: Sequence[ChainLink], validity: Sequence[ValidityFlag]) -> tuple[Status, tuple[str, ...]]:
    """Return the badge and one English reason per factor that set or held it.

    Parameters
    ----------
    chain : Sequence[ChainLink]
        The equations the result is computed with. An empty chain (an `input`, `derived` or `count` value) has no
        test that could have checked it, so its badge is `not tested`.
    validity : Sequence[ValidityFlag]
        Validity outcomes of those equations for this design. Only `ValidityEffect.CAP` changes the badge.

    Returns
    -------
    tuple[Status, tuple[str, ...]]
        The badge and the reasons, for example ``("EQ-07 inferred", "EQ-07 tests not passed in this build")``.
    """
    statuses: list[Status] = [] if chain else [Status.NOT_TESTED]
    reasons: list[str] = [] if chain else ["no equation in the chain"]
    for link in chain:
        if link.gate is GateVerdict.CANNOT_VERIFY_YET:
            statuses.append(Status.UNRESOLVED)
            reasons.append(f"{link.eq_id} gate '{link.gate}'")
            continue
        statuses.append(link.evidence)
        reasons.append(f"{link.eq_id} {link.evidence}")
        if not link.tests_passed:
            statuses.append(Status.NOT_TESTED)
            reasons.append(f"{link.eq_id} tests not passed in this build")
    for flag in validity:
        if flag.effect is ValidityEffect.CAP:
            statuses.append(Status.UNRESOLVED)
            reasons.append(f"{flag.code} validity limit exceeded")
    return combine_status(*statuses), tuple(reasons)
