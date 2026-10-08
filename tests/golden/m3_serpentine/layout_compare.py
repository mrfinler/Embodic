"""GR-20 comparators: one embodic board against the matching part of Xcoil's raw layout.

Xcoil makes one object per interconnect link (tap stubs and ring arc together). The port cuts the star ring at its
middle tap so that the tap is an end node under D-006 rule 3 (XD-SER-001); ``merge_ring_cuts`` joins the two arcs
again before the primitive streams are compared.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from harness import KERNEL_MM, Comparison, Diff, DiffKind, Tolerance, compare_scalar, compare_sequence
from m1_layout.xcoil_map import prim_from_record

from embodic.geometry.layout import Layout, ViaRole
from embodic.geometry.primitives import Arc, Line, Primitive, PrimitiveRole

SAMPLE_COUNT = 9
SAMPLED_MM = Tolerance("sampled_distance_mm", rel=0.0, abs=1e-6)  # test_plan.md section 3, layout paths
Z_MM = Tolerance("copper_z_mm", rel=0.0, abs=1e-12)  # UT-GEN-05


def merge_ring_cuts(prims: Sequence[Primitive]) -> list[Primitive]:
    """Join consecutive ring arcs that continue one circle into the single arc Xcoil draws."""
    out: list[Primitive] = []
    for p in prims:
        last = out[-1] if out else None
        if (
            isinstance(p, Arc)
            and isinstance(last, Arc)
            and p.role is PrimitiveRole.RING
            and last.role is PrimitiveRole.RING
            and math.isclose(p.r_mm, last.r_mm, abs_tol=1e-12)
            and math.isclose(p.start_rad, last.start_rad + last.sweep_rad, abs_tol=1e-9)
        ):
            out[-1] = replace(last, sweep_rad=last.sweep_rad + p.sweep_rad)
        else:
            out.append(p)
    return out


def _point(p: Primitive, t: float) -> tuple[float, float]:
    if isinstance(p, Line):
        return (p.x1_mm + (p.x2_mm - p.x1_mm) * t, p.y1_mm + (p.y2_mm - p.y1_mm) * t)
    return p.point_at(p.start_rad + p.sweep_rad * t)


def sampled_distance_mm(golden: Primitive, actual: Primitive) -> float:
    """Largest distance between points at equal fractions of two primitives, in mm."""
    return max(
        math.dist(_point(golden, k / (SAMPLE_COUNT - 1)), _point(actual, k / (SAMPLE_COUNT - 1)))
        for k in range(SAMPLE_COUNT)
    )


def compare_streams(golden: Sequence[Mapping[str, Any]], actual: Sequence[Primitive], path: str) -> Comparison:
    """Compare primitive counts, roles, widths and sampled positions of one layer's copper, in Xcoil's order."""
    if len(golden) != len(actual):
        return Comparison(diffs=(Diff(path, DiffKind.LENGTH, len(golden), len(actual), "primitive counts differ"),))
    diffs: list[Diff] = []
    for i, (record, mine) in enumerate(zip(golden, actual, strict=True)):
        theirs = prim_from_record(record)
        here = f"{path}[{i}]"
        if type(theirs) is not type(mine):
            diffs.append(Diff(here, DiffKind.TYPE, type(theirs).__name__, type(mine).__name__, "line vs arc"))
            continue
        if theirs.role is not mine.role:
            diffs.append(Diff(here, DiffKind.VALUE, theirs.role.value, mine.role.value, "role differs"))
        diffs += list(compare_scalar(theirs.width_mm, mine.width_mm, KERNEL_MM, path=f"{here}.width").diffs)
        diffs += list(compare_scalar(0.0, sampled_distance_mm(theirs, mine), SAMPLED_MM, path=f"{here}.sampled").diffs)
    return Comparison(diffs=tuple(diffs))


def xcoil_via_role(via: Mapping[str, Any]) -> ViaRole:
    """Role of an Xcoil winding via: terminal, or the centre via V, or a transfer between layer pairs."""
    if via["terminal"]:
        return ViaRole.TERMINAL
    return ViaRole.CENTRE if via["type"] == "V" else ViaRole.TRANSFER


def compare_points(
    golden: Sequence[tuple[float, float]], actual: Sequence[tuple[float, float]], path: str
) -> Comparison:
    """Compare point lists within the sampled-distance tolerance."""
    if len(golden) != len(actual):
        return Comparison(diffs=(Diff(path, DiffKind.LENGTH, len(golden), len(actual), "counts differ"),))
    return compare_sequence(
        [0.0] * len(golden), [math.dist(g, a) for g, a in zip(golden, actual, strict=True)], SAMPLED_MM
    )


def board_layers(layout: Layout) -> list[list[Primitive]]:
    """Primitives of each copper layer in layer order, path by path in id order."""
    return [
        [p for path in layout.paths if path.layer == name for p in path.primitives] for name in layout.copper_layers
    ]
