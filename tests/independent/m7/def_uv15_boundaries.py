"""DEF-UV15-01 and DEF-UV15-02 probes: the product at the exact D-006 and rule 2b boundaries (run with PYTHONPATH=src).

Each probe prints what the unmutated product reports at the boundary and one step either side. A survivor of V3-02 is
observable only if the boundary value itself is reachable, so this shows that V3-02-09 and V3-02-10 are not equivalent.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.unit.drc.layouts import layout, line, path, via
from tests.unit.drc.test_run_drc import RULES

from embodic.drc import DRC_EPSILON_MM, run_drc


def d006_boundary() -> None:
    """Two 0.2 mm traces whose clearance is rule - epsilon exactly, then 8.9e-17 mm closer or further."""
    threshold = RULES.trace_clearance_mm - DRC_EPSILON_MM
    for k in (-1, 0, 1):
        y = threshold + 0.2 + k * 2**-52 * 0.4
        report = run_drc(
            layout(paths=[path(0, [line(-5, 0, 5, 0)], net="A"), path(1, [line(-5, y, 5, y)], net="B")]), RULES
        )
        assert report is not None
        least = report.summaries[0].least_clearance_mm
        print(f"D-006 k={k:+d}: clearance {least!r}, equals rule - epsilon {least == threshold}, "
              f"violations {len(report.violations)}")  # fmt: skip


def tap_boundary() -> None:
    """Place a same-net via 0.29, 0.3 (pad_mm / 2) and 0.31 mm off a trunk centreline."""
    for offset in (0.29, 0.3, 0.31):
        trunk = path(0, [line(-5, 0, 5, 0)], net="A")
        report = run_drc(layout(paths=[trunk], vias=[via(0, 0, offset, net="A")]), RULES)
        assert report is not None
        print(f"rule 2b offset {offset}: {[(v.kind.value, v.objects) for v in report.violations]}")


if __name__ == "__main__":
    d006_boundary()
    tap_boundary()
