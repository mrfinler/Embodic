"""Keep-out checks of the screw holes (REQ-F-24, UT-GEO-21): hole to board edge or cutout, and hole to hole.

Copper to hole is the DRC's COPPER_HOLE check once the holes are on the outline. The hole-to-hole web uses the edge
clearance rule (`assumption`: no cited source gives a web rule; both gaps are board material between two cut edges).
Violations follow D-006: a gap below rule - epsilon, no slack.
"""

from collections.abc import Sequence
from itertools import combinations

from embodic.drc.report import violates
from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for
from embodic.geometry.fasteners import PlacedHole, edge_gap_mm, hole_gap_mm
from embodic.geometry.layout import BoardOutline
from embodic.model.drc_rules import DrcRules


def _issue(code: str, patterns: set[int]) -> ValidationIssue:
    pointers = tuple(f"/outline/screws/{k}/{leaf}" for k in sorted(patterns) for leaf in ("pitch_radius_mm",
                     "hole_diameter_mm"))  # fmt: skip
    return ValidationIssue(
        code=code, category=IssueCategory.UNBUILDABLE, severity=Severity.ERROR, message=message_for(code),
        pointers=pointers, limit=None,
    )  # fmt: skip


def keep_out_issues(
    placed: Sequence[PlacedHole], outline: BoardOutline, rules: DrcRules
) -> tuple[ValidationIssue, ...]:
    """One issue per keep-out kind that a hole breaks, pointing at the patterns involved; empty when all holes fit."""
    edge = {p.pattern for p in placed if violates(edge_gap_mm(p.hole, outline), rules.edge_clearance_mm)}
    pitch = {
        k
        for a, b in combinations(placed, 2)
        if violates(hole_gap_mm(a.hole, b.hole), rules.edge_clearance_mm)
        for k in (a.pattern, b.pattern)
    }
    found = (("UNBUILDABLE_SCREW_HOLE_EDGE", edge), ("UNBUILDABLE_SCREW_HOLE_PITCH", pitch))
    return tuple(_issue(code, patterns) for code, patterns in found if patterns)
