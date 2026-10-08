"""UT-DRC-02: exact line and arc distance kernels against closed forms and dense sampling."""

import math

import numpy as np
import pytest

from embodic.drc import min_distance_arc_arc, min_distance_line_arc, min_distance_line_line

pytestmark = pytest.mark.req("REQ-F-10")


def _line(x1: float, y1: float, x2: float, y2: float) -> list[float]:
    return [x1, y1, x2, y2, 0.0]


def _arc(cx: float, cy: float, r: float, start: float, sweep: float) -> list[float]:
    return [cx, cy, r, start, sweep, 0.0]


def _rows(*rows: list[float]) -> np.ndarray:
    return np.array(rows, dtype=np.float64)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (_line(0, 0, 2, 0), _line(0, 1, 2, 1), 1.0),
        (_line(0, 0, 2, 2), _line(0, 2, 2, 0), 0.0),
        (_line(0, 0, 1, 0), _line(3, 0, 4, 0), 2.0),
        (_line(0, 0, 1, 0), _line(0.5, 0.25, 0.5, 3), 0.25),
    ],
    ids=["parallel", "crossing", "collinear-gap", "t-junction-short"],
)
def test_ut_drc_02_line_line_closed_forms(a: list[float], b: list[float], expected: float) -> None:
    """Catches a line kernel that misses a crossing or measures end points only on the wrong segment."""
    assert min_distance_line_line(_rows(a), _rows(b))[0] == pytest.approx(expected, abs=1e-15)


# DEF-M2d3-01: CF-11 with radial sides and arc ends, leg on layer L2 against the mirrored right side. The cross product
# of the two direction vectors is -2.7e-15 mm^2, which is rounding noise on lengths of 19 mm and 1 mm, not a crossing.
_CF11_SIDE = _line(4.384504814773052, -17.715490891568088, 9.069318178503163, -36.64437157022988)
_CF11_LEG = _line(9.489750147043045, -38.34311727216107, 9.249503307877399, -37.372405442486105)


def test_ut_drc_02_nearly_collinear_disjoint_pair_reports_its_gap() -> None:
    """Catches DEF-M2d3-01: an absolute cross-product threshold turns rounding noise into a crossing (distance 0).

    The real centre distance is 0.75 mm: half widths 0.25 and 0.30 plus the 0.2 mm design gap.
    """
    a, b = np.array(_CF11_SIDE), np.array(_CF11_LEG)
    exact = min_distance_line_line(a[None, :], b[None, :])[0]
    pa, pb = _samples(a, False, 20001), _samples(b, False, 20001)
    sampled = min(
        float(np.sqrt(((chunk[:, None, :] - pb[None, :, :]) ** 2).sum(-1)).min()) for chunk in np.array_split(pa, 40)
    )
    assert sampled == pytest.approx(0.75, abs=1e-6)
    assert exact == pytest.approx(0.75, abs=1e-9)


def _collinear_rows(gap_mm: float, overlap_mm: float) -> tuple[np.ndarray, np.ndarray]:
    """Two 20 mm segments on one line in each of 720 directions: ``gap_mm`` apart, or b ``overlap_mm`` over a."""
    angle_rad = np.deg2rad(np.arange(0.0, 360.0, 0.5)) + 0.01
    ux, uy = np.cos(angle_rad), np.sin(angle_rad)
    ox, oy = np.full_like(ux, 9.1), np.full_like(uy, -36.6)
    start_b_mm = 20.0 + gap_mm - overlap_mm
    a = np.stack([ox, oy, ox + 20.0 * ux, oy + 20.0 * uy, 0 * ux], axis=1)
    b = np.stack(
        [
            ox + start_b_mm * ux,
            oy + start_b_mm * uy,
            ox + (start_b_mm + 20.0) * ux,
            oy + (start_b_mm + 20.0) * uy,
            0 * ux,
        ],
        axis=1,
    )
    return a, b


def test_ut_drc_02_collinear_disjoint_segments_measure_the_gap_in_every_direction() -> None:
    """Catches DEF-M2d3-01 at its root: collinear segments in any direction must fall back to the end-point distance.

    Collinear means exactly collinear in the real numbers, so the closed form is the 0.2 mm gap along the shared line.
    """
    a, b = _collinear_rows(gap_mm=0.2, overlap_mm=0.0)
    wrong = np.flatnonzero(np.abs(min_distance_line_line(a, b) - 0.2) > 1e-9)
    assert wrong.size == 0, f"{wrong.size} of {len(a)} directions report a false crossing, first at row {wrong[0]}"


def test_ut_drc_02_antiparallel_overlap_is_zero_in_every_direction() -> None:
    """Catches a fix that drops collinear pairs without the end-point path: b runs backwards over 1 mm of a."""
    a, b = _collinear_rows(gap_mm=0.0, overlap_mm=1.0)
    b = b[:, [2, 3, 0, 1, 4]]
    assert np.all(min_distance_line_line(a, b) <= 1e-12)


def test_ut_drc_02_collinear_ends_touching_is_zero_in_every_direction() -> None:
    """Catches a fix that loses the shared end point: the end of a is the start of b."""
    a, b = _collinear_rows(gap_mm=0.0, overlap_mm=0.0)
    assert np.all(min_distance_line_line(a, b) <= 1e-12)


def test_ut_drc_02_shallow_true_crossing_is_exactly_zero() -> None:
    """Catches a parallel tolerance so wide that a real crossing at 2e-7 rad is measured by its end points (5e-6 mm)."""
    a = _rows(_line(0, 0, 10, 0))
    b = _rows(_line(0, -1e-6, 10, 1e-6))
    assert min_distance_line_line(a, b)[0] == 0.0


@pytest.mark.parametrize(
    ("line", "arc", "expected"),
    [
        (_line(-1, 3, 1, 3), _arc(0, 0, 2, 0, math.pi), 1.0),
        (_line(-1, 1.5, 1, 1.5), _arc(0, 0, 2, 0, math.pi), 2 - math.hypot(1, 1.5)),
        (_line(-3, 1, 3, 1), _arc(0, 0, 2, 0, math.pi), 0.0),
        (_line(-1, -3, 1, -3), _arc(0, 0, 2, 0, math.pi), math.hypot(1, 3)),
        (_line(0, 0, 0, 0.5), _arc(0, 0, 2, 0, 2 * math.pi), 1.5),
    ],
    ids=["above-apex", "inside-chord", "crossing", "behind-arc-ends", "radius-from-centre"],
)
def test_ut_drc_02_line_arc_closed_forms(line: list[float], arc: list[float], expected: float) -> None:
    """Catches a missing foot-point candidate (above-apex) or an arc treated as its full circle (behind-arc-ends)."""
    assert min_distance_line_arc(_rows(line), _rows(arc))[0] == pytest.approx(expected, abs=1e-14)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (_arc(0, 0, 2, 0, math.pi), _arc(0, 0, 2.3, 0.5, 1.0), 0.3),
        (_arc(0, 0, 2, 0, 1.0), _arc(0, 0, 2.3, 2.0, 1.0), None),
        (_arc(0, 0, 1, -1, 2), _arc(3, 0, 1, math.pi - 1, 2), 1.0),
        (_arc(0, 0, 1, -1, 2), _arc(1.5, 0, 1, math.pi - 1, 2), 0.0),
        (_arc(0, 0, 1, 1, -2), _arc(3, 0, 1, math.pi + 1, -2), 1.0),
    ],
    ids=["concentric-overlap", "concentric-disjoint", "facing", "crossing", "facing-clockwise"],
)
def test_ut_drc_02_arc_arc_closed_forms(a: list[float], b: list[float], expected: float | None) -> None:
    """Catches a missing centre-line candidate (facing) or an overlap test that ignores sweep direction."""
    if expected is None:
        expected = math.dist((2 * math.cos(1.0), 2 * math.sin(1.0)), (2.3 * math.cos(2.0), 2.3 * math.sin(2.0)))
    assert min_distance_arc_arc(_rows(a), _rows(b))[0] == pytest.approx(expected, abs=1e-14)


def _samples(row: np.ndarray, is_arc: bool, count: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, count)
    if is_arc:
        angle = row[3] + t * row[4]
        return np.stack([row[0] + row[2] * np.cos(angle), row[1] + row[2] * np.sin(angle)], axis=1)
    return np.stack([row[0] + t * (row[2] - row[0]), row[1] + t * (row[3] - row[1])], axis=1)


def _spacing_mm(row: np.ndarray, is_arc: bool, count: int) -> float:
    length_mm = abs(row[4]) * row[2] if is_arc else math.hypot(row[2] - row[0], row[3] - row[1])
    return length_mm / (count - 1)


def _random_row(rng: np.random.Generator, is_arc: bool) -> np.ndarray:
    if is_arc:
        return np.array([*rng.uniform(-2, 2, 2), rng.uniform(0.1, 3), rng.uniform(-7, 7), rng.uniform(-7, 7), 0.0])
    return np.array([*rng.uniform(-3, 3, 4), 0.0])


@pytest.mark.parametrize(("a_is_arc", "b_is_arc"), [(False, False), (False, True), (True, True)])
def test_ut_drc_02_kernels_agree_with_dense_sampling(a_is_arc: bool, b_is_arc: bool) -> None:
    """Catches any kernel that under-reports (below the sampled bracket) or misses a closer pair (above it).

    Sampled distance s is an upper bound; the true distance is at least s minus half the two sample spacings.
    """
    rng = np.random.default_rng(1806)
    kernel = {
        (False, False): min_distance_line_line,
        (False, True): min_distance_line_arc,
        (True, True): min_distance_arc_arc,
    }
    count = 801
    for _ in range(100):
        a, b = _random_row(rng, a_is_arc), _random_row(rng, b_is_arc)
        exact = kernel[a_is_arc, b_is_arc](a[None, :], b[None, :])[0]
        pa, pb = _samples(a, a_is_arc, count), _samples(b, b_is_arc, count)
        sampled = math.inf
        for chunk in np.array_split(pa, 2):
            sampled = min(sampled, float(np.sqrt(((chunk[:, None, :] - pb[None, :, :]) ** 2).sum(-1)).min()))
        bound = (_spacing_mm(a, a_is_arc, count) + _spacing_mm(b, b_is_arc, count)) / 2
        assert sampled - bound - 1e-9 <= exact <= sampled + 1e-9, (a, b, exact, sampled, bound)
