"""Item 6 (U-V3): V8 (Node) against glibc (CPython math) on 1000 seeded random angles, in units in the last place."""

import math
import random
import struct

from cases import run_node

FUNCTIONS = ("sin", "cos", "atan2", "tan")


def ulps(a: float, b: float) -> int:
    """Distance between two finite doubles of one sign in representable steps."""
    ia, ib = (struct.unpack("<q", struct.pack("<d", v))[0] for v in (a, b))
    if (ia < 0) != (ib < 0):
        return abs(ia & 0x7FFFFFFFFFFFFFFF) + abs(ib & 0x7FFFFFFFFFFFFFFF)
    return abs(ia - ib)


def angles(n: int = 1000, seed: int = 20261008) -> tuple[list[float], list[tuple[float, float]]]:
    """Uniform angles in [-8 pi, 8 pi] (Xcoil rotates by phase and pair), and atan2 inputs as layout coordinates."""
    rnd = random.Random(seed)
    xs = [rnd.uniform(-8 * math.pi, 8 * math.pi) for _ in range(n)]
    return xs, [(rnd.uniform(-60.0, 60.0), rnd.uniform(-60.0, 60.0)) for _ in range(n)]


def measure() -> dict[str, tuple[int, int, float]]:
    """Per function: worst ulp distance, number of angles that differ, worst absolute difference."""
    xs, pairs = angles()
    v8 = run_node({"angles": xs, "pairs": pairs})["trig"]
    out = {}
    for k, name in enumerate(FUNCTIONS):
        diffs = []
        for x, (y, xx), row in zip(xs, pairs, v8, strict=True):
            mine = (math.sin(x), math.cos(x), math.atan2(y, xx), math.tan(x))[k]
            diffs.append((ulps(mine, row[k]), abs(mine - row[k])))
        out[name] = (max(d for d, _ in diffs), sum(d > 0 for d, _ in diffs), max(a for _, a in diffs))
    return out


def main() -> None:
    """Print the ulp table."""
    for name, (worst, count, absolute) in measure().items():
        print(f"{name}: worst {worst} ulp, {count} of 1000 differ, worst |diff| {absolute:.3e}")


if __name__ == "__main__":
    main()
