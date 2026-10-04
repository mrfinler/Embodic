# Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5
"""Evidence for interfaces.md section 9.1: degrees in the project file, radians in the model.

Run from anywhere (standard library only):
    python3 docs/phase2/architecture/checks/angle_round_trip.py

For two input sets it counts how often (a) the first save of a typed degree value prints a different number, (b) save,
load, save changes the saved number (REQ-F-15 needs 0), and (c) math.radians differs from Xcoil's d * Math.PI / 180
(engine.js l.171). It does this for the math pair (math.radians, math.degrees) and for Xcoil's expressions.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence

Pair = tuple[Callable[[float], float], Callable[[float], float]]
PAIRS: dict[str, Pair] = {
    "math.radians/degrees": (math.radians, math.degrees),
    "Xcoil d*pi/180, r*180/pi": (lambda d: d * math.pi / 180, lambda r: r * 180 / math.pi),
}


def counts(values: Sequence[float], pair: Pair) -> tuple[int, int]:
    to_rad, to_deg = pair
    first_save_differs = sum(to_deg(to_rad(d)) != d for d in values)
    unstable = 0
    for d in values:
        saved = to_deg(to_rad(d))
        unstable += to_deg(to_rad(saved)) != saved
    return first_save_differs, unstable


def main() -> int:
    random.seed(1)
    sets = {
        "0.01 deg grid -360..360": [k / 100 for k in range(-36000, 36001)],
        "200000 uniform -360..360 (seed 1)": [random.uniform(-360, 360) for _ in range(200_000)],
    }
    for name, values in sets.items():
        differs_from_xcoil = sum(math.radians(d) != d * math.pi / 180 for d in values)
        print(f"{name}: n={len(values)}; math.radians != Xcoil expression: {differs_from_xcoil}")
        for label, pair in PAIRS.items():
            first, unstable = counts(values, pair)
            print(f"  {label}: first save prints a different number: {first}; save-load-save changes: {unstable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
