r"""U-D27 option C samples: three identical-output variants of the coil-eye search against 0.0.4's, same rounds.

Not a test. ``PYTHONPATH=<tree>/src python eye_hoist.py [--rounds 5]``. Variants: ``_eye`` with its loop-invariant
min and max hoisted, ``_encloses`` stopping at the eighth sector, and ``_encloses`` on NumPy arrays. The marks of every
example must equal 0.0.4's (dataclass equality compares the floats exactly); the timed work is ``coil_marks`` and
``write_svg`` of each example. It first counts how many ``np.arctan2`` values differ in bits from ``math.atan2`` on the
first path of each board, since the NumPy variant is identical only where they agree.
"""

import argparse
import math
import statistics
import sys
import tempfile
import time

import numpy as np
from pathlib import Path

from embodic.api import compute_project
from embodic.io.svg_writer import write_svg

marks = sys.modules["embodic.geometry.marks"]
TREE = Path(__file__).resolve().parents[5]
STEMS = ("serpentine_16p_example", "spiral_12c10p_d08", "spiral_12c14p", "spiral_12c16p_default", "wave_16p_example")
ORIGINAL = marks._eye


def hoisted(turns, copper):
    points = [q for p in turns for q in marks._samples(p)]
    xs, ys = [x for x, _ in points], [y for _, y in points]
    steps = 24
    best = (math.fsum(xs) / len(xs), math.fsum(ys) / len(ys), 0.0)
    x_lo, x_hi, y_lo, y_hi = min(xs), max(xs), min(ys), max(ys)
    for i in range(1, steps):
        for j in range(1, steps):
            x = x_lo + (x_hi - x_lo) * i / steps
            y = y_lo + (y_hi - y_lo) * j / steps
            if marks._encloses(x, y, points) and (free := marks._free_radius_mm(x, y, turns)) > best[2]:
                best = (x, y, free)
    x, y, _ = best
    return x, y, marks.EYE_MARGIN * max(0.0, marks._free_radius_mm(x, y, copper))


def encloses_early(x_mm, y_mm, coil_points):
    """``_encloses`` that stops at the eighth sector; same sectors, same arithmetic, same answer."""
    seen = set()
    for px, py in coil_points:
        seen.add(int((math.atan2(py - y_mm, px - x_mm) + math.pi) / (math.tau / 8)) % 8)
        if len(seen) == 8:
            return True
    return False


def encloses_numpy(x_mm, y_mm, coil_points):
    """``_encloses`` on arrays: np.arctan2 and the same division, truncation and modulo; identical only if np.arctan2
    returns math.atan2's bits, which main() checks on every point and cell first."""
    pts = np.asarray(coil_points, dtype=float)
    sectors = ((np.arctan2(pts[:, 1] - y_mm, pts[:, 0] - x_mm) + math.pi) / (math.tau / 8)).astype(np.int64) % 8
    return len(np.unique(sectors)) == 8


ENCLOSES = marks._encloses
VARIANTS = {"0.0.4": (ORIGINAL, ENCLOSES), "hoisted": (hoisted, ENCLOSES), "early": (ORIGINAL, encloses_early),
            "numpy": (ORIGINAL, encloses_numpy)}  # fmt: skip


def atan2_bits_equal(layouts) -> tuple[int, int]:
    """Count of (point, cell) atan2 values over every coil of the layouts, and how many differ in bits."""
    calls, differ = 0, 0
    for layout in layouts:
        for path in layout.paths:
            pts = [q for p in path.primitives for q in marks._samples(p)]
            arr = np.asarray(pts, dtype=float)
            xs, ys = arr[:, 0], arr[:, 1]
            for i in range(1, 24):
                for j in range(1, 24):
                    x = xs.min() + (xs.max() - xs.min()) * i / 24
                    y = ys.min() + (ys.max() - ys.min()) * j / 24
                    vec = np.arctan2(ys - y, xs - x)
                    ref = np.array([math.atan2(py - y, px - x) for px, py in pts])
                    calls += len(pts)
                    differ += int(np.count_nonzero(vec.view(np.uint64) != ref.view(np.uint64)))
            break
    return calls, differ


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=5)
    rounds = parser.parse_args().rounds
    folder = Path(tempfile.mkdtemp(prefix="u_d27_eye_"))
    for stem in STEMS:
        outcome = compute_project(TREE / "resources" / "examples" / f"{stem}.embodic.json")
        layouts = outcome.boards.boards
        print(stem, "atan2 values compared, differing:", atan2_bits_equal(layouts))
        same = {}
        for label, (eye, encloses) in VARIANTS.items():
            marks._eye, marks._encloses = eye, encloses
            same[label] = [tuple(marks.coil_marks(b)) for b in layouts]
        same = all(v == same["0.0.4"] for v in same.values())
        times: dict[str, list[float]] = {f"{kind} {label}": [] for kind in ("marks", "svg") for label in VARIANTS}
        for _ in range(rounds):
            for label, (eye, encloses) in VARIANTS.items():
                marks._eye, marks._encloses = eye, encloses
                started = time.perf_counter()
                for b in layouts:
                    tuple(marks.coil_marks(b))
                times[f"marks {label}"].append(time.perf_counter() - started)
                started = time.perf_counter()
                write_svg(outcome, folder / f"{stem}.svg", allow_drc_errors=True)
                times[f"svg {label}"].append(time.perf_counter() - started)
        marks._eye, marks._encloses = ORIGINAL, ENCLOSES
        text = ", ".join(f"{k} {statistics.median(v) * 1e3:.1f} ms [{min(v) * 1e3:.1f}-{max(v) * 1e3:.1f}]"
                         for k, v in times.items())  # fmt: skip
        print(f"{stem}: marks identical {same}; {text}")


if __name__ == "__main__":
    main()
