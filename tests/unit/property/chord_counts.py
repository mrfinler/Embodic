"""PR-14 with the chord counts held equal in both builds, compared at the round-off bound (U-E16, D-054a).

docs/phase3/engineering/pr14_and_reqf_texts.md part 1: a rotation recomputes every coordinate through sin and cos, so a
primitive whose ratio is a designed integer m lands a few ulp on either side of it, and ``ceil`` gives m or m + 1
chords depending on the platform's last bits (DEF-UE16-01). Snapping such a ratio to m on both boards takes that
decision out of the comparison (section 1.6 step 1). What remains is round-off, at most 2 (N + 10) u kappa relative
(section 1.5) with kappa = 1 (section 1.6 step 2).
"""

import math
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

import embodic.geometry.discretise as disc
from embodic.geometry.layout import BoardStack
from embodic.geometry.primitives import Primitive

# Section 1.6: designed integers land at most 5.1e-15 relative from m on Linux, and Windows on the same set.
DESIGNED_INTEGER_REL = 1e-9
UNIT_ROUNDOFF = 2.0**-53
TERM_ROUNDINGS = 10  # section 1.5: four rounded factors, exp and the interpolation of each chord term (assumption)


def _snapped(ratio: float) -> int:
    m = round(ratio)
    return m if m >= 1 and abs(ratio - m) <= DESIGNED_INTEGER_REL * m else math.ceil(ratio)


def _snapped_piece_count(
    p: Primitive,
    max_segment_mm: float = disc.DEFAULT_MAX_SEGMENT_MM,
    max_angle_rad: float = disc.DEFAULT_MAX_ANGLE_RAD,
    max_sagitta_mm: float = disc.DEFAULT_MAX_SAGITTA_MM,
) -> int:
    """``piece_count`` with every ratio within DESIGNED_INTEGER_REL of an integer m taken as m, others as ``ceil``."""
    return max(1, *(_snapped(r) for r in disc.piece_ratios(p, max_segment_mm, max_angle_rad, max_sagitta_mm)))


@contextmanager
def designed_integers_snapped() -> Iterator[None]:
    """Build and analyse inside this block so both boards cut every designed-integer primitive into m chords."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(disc, "piece_count", _snapped_piece_count)
        yield


def roundoff_rel(stack: BoardStack, max_segment_mm: float) -> float:
    """Return 2 (N + 10) u, the relative bound on Ke between two boards with equal chord counts (kappa = 1).

    N is the number of chords on every path of the stack, counted as the analysis cuts them.
    """
    chords = sum(len(disc.discretise_path(p.primitives, max_segment_mm)) for b in stack.boards for p in b.paths)
    return 2 * (chords + TERM_ROUNDINGS) * UNIT_ROUNDOFF
