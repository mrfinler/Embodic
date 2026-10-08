"""Item 1 and 3 (U-V3): per-case comparison of Xcoil's raw layout and embodic's BoardStack; prints the table."""

from dataclasses import dataclass
from typing import Any

from cases import xcoil_dumps
from own_map import (
    boards_from_embodic,
    boards_from_xcoil,
    compare_layer,
    match_lands,
    role_counts,
    role_lengths,
)
from subject import stack_for


@dataclass(frozen=True, slots=True)
class CaseDiff:
    """Everything item 1 compares for one case."""

    case_id: str
    boards: tuple[int, int]
    layers: tuple[tuple[int, int], ...]
    z_max_mm: float
    count_diffs: dict[str, int]
    length_max_mm: float
    sampled_max_mm: float
    width_mismatches: int
    role_mismatches: int
    samples: int
    vias: tuple[int, int]
    via_pos_mm: float
    pads: tuple[int, int]
    pad_pos_mm: float
    pad_dia_mm: float
    thickness: tuple[float, float]


def compare_case(case_id: str) -> CaseDiff:
    """Compare one case object by object."""
    dump = xcoil_dumps()[case_id]
    stack = stack_for(case_id)
    xs, es = boards_from_xcoil(dump), boards_from_embodic(stack)
    counts: dict[str, int] = {}
    z_max = length_max = sampled = 0.0
    widths = roles = samples = 0
    via_pos = pad_pos = pad_dia = 0.0
    for xb, eb in zip(xs, es, strict=False):
        z_max = max([z_max] + [abs(a - b) for a, b in zip(xb.z_mm, eb.z_mm, strict=False)])
        for xl, el in zip(xb.layers, eb.layers, strict=False):
            xc, ec = role_counts(xl), role_counts(el)
            for role in xc | ec:
                if xc[role] != ec[role]:
                    counts[role] = counts.get(role, 0) + ec[role] - xc[role]
            xlen, elen = role_lengths(xl), role_lengths(el)
            length_max = max([length_max] + [abs(xlen.get(r, 0) - elen.get(r, 0)) for r in xlen | elen])
            d = compare_layer(xl, el)
            sampled = max(sampled, d.max_xcoil_to_own_mm, d.max_own_to_xcoil_mm)
            widths, roles, samples = widths + d.width_mismatches, roles + d.role_mismatches, samples + d.samples
        if xb.vias and eb.vias:
            via_pos = max(via_pos, match_lands(xb.vias, eb.vias)[0])
        if xb.pads and eb.pads:
            p, dia = match_lands(xb.pads, eb.pads)
            pad_pos, pad_dia = max(pad_pos, p), max(pad_dia, dia)
    return CaseDiff(
        case_id,
        (len(xs), len(es)),
        tuple((len(x.layers), len(e.layers)) for x, e in zip(xs, es, strict=False)),
        z_max,
        counts,
        length_max,
        sampled,
        widths,
        roles,
        samples,
        (sum(len(b.vias) for b in xs), sum(len(b.vias) for b in es)),
        via_pos,
        (sum(len(b.pads) for b in xs), sum(len(b.pads) for b in es)),
        pad_pos,
        pad_dia,
        (dump["statorThickness"], _stack_thickness(stack)),
    )


def _stack_thickness(stack: Any) -> float:
    n = len(stack.boards)
    return n * stack.board_thickness_mm + (n - 1) * stack.board_gap_mm


def main() -> None:
    """Print the item 1 table."""
    print("| case | boards | z max | count diffs (own - xcoil) | length max | sampled max | width/role mism. "
          "| vias | via pos | pads | pad pos | thickness xcoil/own |")  # fmt: skip
    for cid in xcoil_dumps():
        d = compare_case(cid)
        print(f"| {cid} | {d.boards[0]}/{d.boards[1]} | {d.z_max_mm:.1e} | {d.count_diffs or '-'} "
              f"| {d.length_max_mm:.1e} | {d.sampled_max_mm:.1e} "
              f"| {d.width_mismatches}/{d.role_mismatches} of {d.samples} "
              f"| {d.vias[0]}/{d.vias[1]} | {d.via_pos_mm:.1e} | {d.pads[0]}/{d.pads[1]} | {d.pad_pos_mm:.1e} "
              f"| {d.thickness[0]:.4f}/{d.thickness[1]:.4f} |")  # fmt: skip


if __name__ == "__main__":
    main()
