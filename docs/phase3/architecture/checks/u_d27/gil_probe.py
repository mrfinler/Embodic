r"""U-D27: the Rust ``integrate_path`` end to end, and how long a second thread waits for the GIL while physics runs.

Not a test. ``PYTHONPATH=<tree>/src python gil_probe.py <libu_d27_emf.so> [--rounds 5]``, one process at a time.

- compute: ``compute_project`` of each example with the Python kernel and with the Rust wrapper of emf_bench.py,
  alternating, and the outcome JSON of both compared.
- GIL: a worker thread runs ``analyse`` while the main thread sleeps 1 ms in a loop, as an event loop waits for its next
  event; each wake needs the GIL, so the gap between wakes is how long the main thread waited. CPython asks the holder
  to drop the GIL every ``sys.getswitchinterval()`` (5 ms). ctypes releases the GIL while the Rust loop runs. This is a
  Linux proxy for the mechanism of DEF-W-12, not the Windows GUI latency itself.
"""

import argparse
import json
import statistics
import sys
import threading
import time
from pathlib import Path

from emf_bench import STEMS, TREE, analyse_module, load, record, rust_wrapper

from embodic.api import compute_project, outcome_to_json
from embodic.physics.analyse import analyse
from embodic.physics.emf import integrate_path


def ticks_during(work) -> list[float]:
    gaps: list[float] = []
    done = threading.Event()
    worker = threading.Thread(target=lambda: (work(), done.set()))
    last = time.perf_counter()
    worker.start()
    while not done.is_set():
        time.sleep(0.001)
        now = time.perf_counter()
        gaps.append(now - last)
        last = now
    worker.join()
    return gaps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lib")
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()
    wrap = rust_wrapper(load(args.lib))
    med = statistics.median
    report: dict[str, object] = {"switch_interval_s": sys.getswitchinterval()}
    for stem in STEMS:
        path = TREE / "resources" / "examples" / f"{stem}.embodic.json"
        want = json.dumps(outcome_to_json(compute_project(path)), sort_keys=True)
        analyse_module.integrate_path = wrap
        same = json.dumps(outcome_to_json(compute_project(path)), sort_keys=True) == want
        analyse_module.integrate_path = integrate_path
        times = {"python": [], "rust": []}
        for _ in range(args.rounds):
            for label, kernel in (("python", integrate_path), ("rust", wrap)):
                analyse_module.integrate_path = kernel
                started = time.perf_counter()
                compute_project(path)
                times[label].append(time.perf_counter() - started)
        analyse_module.integrate_path = integrate_path
        _, physics_args = record(stem)
        gil = {}
        for label, kernel in (("python", integrate_path), ("rust", wrap)):
            analyse_module.integrate_path = kernel
            runs = [ticks_during(lambda: analyse(*physics_args)) for _ in range(args.rounds)]
            analyse_module.integrate_path = integrate_path
            flat = sorted(g for run in runs for g in run)
            gil[label] = {
                "ticks": len(flat),
                "median_gap_ms": med(flat) * 1e3,
                "p99_gap_ms": flat[int(0.99 * (len(flat) - 1))] * 1e3,
                "max_gap_ms": flat[-1] * 1e3,
                "share_of_gaps_over_4ms": sum(g > 0.004 for g in flat) / len(flat),
            }
        ratios = [p / r for p, r in zip(times["python"], times["rust"], strict=True)]
        report[stem] = {"outcome_json_identical": same, "compute_s": times, "gil": gil}
        print(f"{stem}: outcome JSON identical {same}; compute python {med(times['python']) * 1e3:.0f} ms "
              f"[{min(times['python']) * 1e3:.0f}-{max(times['python']) * 1e3:.0f}], rust {med(times['rust']) * 1e3:.0f} "
              f"ms [{min(times['rust']) * 1e3:.0f}-{max(times['rust']) * 1e3:.0f}], same-round ratio median "
              f"{med(ratios):.2f} [{min(ratios):.2f}-{max(ratios):.2f}]")  # fmt: skip
        for label, g in gil.items():
            print(f"  GIL {label}: {g['ticks']} wakes, median gap {g['median_gap_ms']:.2f} ms, p99 "
                  f"{g['p99_gap_ms']:.2f} ms, max {g['max_gap_ms']:.2f} ms, gaps over 4 ms "
                  f"{100 * g['share_of_gaps_over_4ms']:.1f} %")  # fmt: skip
    Path(__file__).with_name("gil_probe.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
