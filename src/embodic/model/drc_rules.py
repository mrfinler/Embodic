"""Manufacturing limits the DRC checks a Layout against (interfaces.md section 2.1, rule D-006)."""

import math
from dataclasses import dataclass, fields

from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for


@dataclass(frozen=True, slots=True, kw_only=True)
class DrcRules:
    """Clearances and minima in mm; a measured value below ``rule - DRC_EPSILON_MM`` is a violation."""

    trace_clearance_mm: float
    via_clearance_mm: float
    edge_clearance_mm: float
    hole_clearance_mm: float
    min_trace_width_mm: float
    min_drill_mm: float
    min_annular_ring_mm: float


def validate_drc_rules(rules: DrcRules, pointer: str = "/drc_rules") -> tuple[ValidationIssue, ...]:
    """Return one INVALID issue per field that is not a finite number >= 0; an empty tuple means the rules are usable.

    A NaN or negative rule would make every comparison pass silently, so the boundary refuses it before ``run_drc``.
    """
    issues: list[ValidationIssue] = []
    for f in fields(rules):
        value_mm = getattr(rules, f.name)
        code = "INVALID_DRC_RULE_NOT_FINITE" if not math.isfinite(value_mm) else "INVALID_DRC_RULE_NEGATIVE"
        if math.isfinite(value_mm) and value_mm >= 0:
            continue
        issues.append(
            ValidationIssue(
                code=code,
                category=IssueCategory.INVALID,
                severity=Severity.ERROR,
                message=message_for(code),
                pointers=(f"{pointer}/{f.name}",),
                value=value_mm,
                limit=0.0,
            )
        )
    return tuple(issues)
