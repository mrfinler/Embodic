"""DEF-UV18-01 probe: a path end of one net on the centreline of a net that has two paths on the layer (PYTHONPATH=src).

V3-02-07 (rule 5 widened: T-junctions across nets) survives the V3-02 suite on 0.0.4. `_junctions` visits only the
(layer, net) groups that hold two or more paths, and the unit test of the cross-net case gives each net one path, so a
junction search that ignores the net never runs there. This probe gives net A two paths, ends a net B path on the
middle of net A's first line and prints what run_drc reports. Run it once on src and once on a copy of src with the
V3-02-07 text applied: the product reports the overlap, the mutant reports nothing, so the mutant is not equivalent.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.unit.drc.layouts import layout, line, path
from tests.unit.drc.test_run_drc import RULES

import embodic
from embodic.drc import run_drc


def main() -> None:
    """Print the violations of the cross-net T on a layer where net A has two paths."""
    trunk = path(0, [line(-5, 0, 5, 0)], net="A")
    second = path(1, [line(-5, 3, 5, 3)], net="A")
    branch = path(2, [line(0, -4, 0, 0)], net="B")
    report = run_drc(layout(paths=[trunk, second, branch]), RULES)
    assert report is not None
    print(f"embodic from {Path(embodic.__file__).parent}")
    print(f"violations: {[(v.kind.value, v.objects, round(v.clearance_mm, 6)) for v in report.violations]}")


if __name__ == "__main__":
    main()
