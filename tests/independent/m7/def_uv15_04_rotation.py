"""DEF-UV15-04 probe: a finite board rotation near 3.14e306 rad passes validation, then compute raises.

Run with PYTHONPATH=src from the repository root.

V3-07 seed 5 found it (PR-05). This replays the shrunk input on the CF-11 draft and prints what compute does at the
found value and at a few neighbours, so the bound where the error starts is visible.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.unit.property.strategies import cf11_draft_with

from embodic.api import compute
from embodic.model.draft import parse_draft
from embodic.model.provenance import derive_provenance
from embodic.results import load_registry

FOUND_RAD = 3.137566414384587e306  # V3-07 seed 5, PR-05 falsifying example

if __name__ == "__main__":
    registry = load_registry()
    print(f"found value x 180/pi = {FOUND_RAD * 180 / math.pi!r}; math.degrees = {math.degrees(FOUND_RAD)!r}")
    for value in (1e306, 3.13e306, FOUND_RAD, 1e307):
        parsed = parse_draft(cf11_draft_with({"/outline/board/shape": "polygon", "/outline/board/sides": 12,
                                              "/outline/board/across_flats_mm": 93.0,
                                              "/outline/board/corner_radius_mm": 0.0,
                                              "/outline/board/rotation_rad": value}))  # fmt: skip
        try:
            outcome = compute(parsed, derive_provenance(parsed, None, ()), registry=registry)
            codes = sorted({i.code for i in outcome.issues}) if outcome else None
            print(f"rotation_rad {value!r}: no exception; issues {codes}")
        except Exception as exc:
            print(f"rotation_rad {value!r}: {type(exc).__name__}: {exc}")
