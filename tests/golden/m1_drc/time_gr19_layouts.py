"""Time ``run_drc`` on the GR-19 raw Xcoil layouts in the DRC reading of U-M1b's mapper (measurement, not a test).

Usage, inside the project's virtual environment::

    python tests/golden/m1_drc/time_gr19_layouts.py [--runs 7]

Rules come from each layout's Xcoil parameters (one ``clearance`` for every clearance rule, as Xcoil applies it).
The mapper sets ``symmetry=None``, so the shortcut cannot apply; the script prints the method to show it.
``trace_via_net_mismatch`` counts overlapping (negative-clearance) TRACE_VIA hits by (path net, via net) where the
two nets differ: copper that touches a via but is not exempt because its net name differs (DEF-M1c-01).
"""

import argparse
import os
import platform
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

GOLDEN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOLDEN))

from harness import load_area  # noqa: E402
from m1_layout.xcoil_map import layout_from_xcoil, split_ic_chains  # noqa: E402

from embodic.drc import DrcCheckKind, DrcReport, run_drc  # noqa: E402
from embodic.geometry.layout import Layout  # noqa: E402
from embodic.model.drc_rules import DrcRules  # noqa: E402


def _cpu_model() -> str:
    for text in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
        if text.startswith("model name"):
            return text.split(":", 1)[1].strip()
    return platform.processor()


def _trace_via_net_mismatch(layout: Layout, report: DrcReport) -> dict[tuple[str, str], int]:
    hits: Counter[tuple[str, str]] = Counter()
    for violation in report.violations:
        if violation.kind is DrcCheckKind.TRACE_VIA and violation.measured_mm < 0:
            ids = dict(obj.split("/")[0].split(":") for obj in violation.objects)
            path_net, via_net = layout.paths[int(ids["path"])].net, layout.vias[int(ids["via"])].net
            if path_net != via_net:
                hits[(path_net, via_net)] += 1
    return dict(hits)


def main() -> int:
    """Print per-layout median and range of warm ``run_drc`` wall times, with the verdict counts."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=7)
    args = parser.parse_args()
    print(f"machine: nproc={os.cpu_count()} cpu={_cpu_model()!r} python={platform.python_version()}")
    for case in load_area("m1_layout").values():
        raw = case.calls[0].output
        params = raw["params"]
        clearance_mm = params["clearance"]
        rules = DrcRules(
            trace_clearance_mm=clearance_mm,
            via_clearance_mm=clearance_mm,
            edge_clearance_mm=clearance_mm,
            hole_clearance_mm=clearance_mm,
            min_trace_width_mm=0.1,
            min_drill_mm=0.2,
            min_annular_ring_mm=0.1,
        )
        layout = layout_from_xcoil(split_ic_chains(raw))
        report = run_drc(layout, rules)
        seconds = []
        for _ in range(args.runs):
            started = time.perf_counter()
            report = run_drc(layout, rules)
            seconds.append(time.perf_counter() - started)
        assert report is not None
        prims = sum(len(p.primitives) for p in layout.paths)
        pairs = sum(s.pairs_checked for s in report.summaries)
        kinds = dict(Counter(v.kind.value for v in report.violations))
        print(
            f"{case.case_id}: layers={len(layout.copper_layers)} prims={prims} vias={len(layout.vias)} "
            f"pads={len(layout.pads)} method={report.method} symmetry_claim={layout.symmetry is not None} "
            f"median={statistics.median(seconds):.3f}s range={min(seconds):.3f}-{max(seconds):.3f}s runs={args.runs} "
            f"checked={pairs} violations={report.violation_count} by_kind={kinds} "
            f"trace_via_net_mismatch={_trace_via_net_mismatch(layout, report)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
