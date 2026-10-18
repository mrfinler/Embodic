r"""DEF-U-M6a-01 lever (U-M8n): the gap distribution of N02-10 over repeated runs, alone or beside a CPU-bound process.

Runs ``test_n02_10_keystroke_echo_while_a_preview_result_arrives`` in a fresh pytest process per run and prints, per
run, the largest GUI tick gap, the verdict and the results the test saw set; then the median and the max. With
``--hog``, a second Python process spins on one core for the whole run, as the release gate's other work does on a
2-core machine.

Not a test. From the repository root, with the project's interpreter:

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/ui/qt_shell/n02_10_runs.py --runs 10 [--hog]
"""

import argparse
import re
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TEST = "tests/ui/qt_shell/test_n02_typing_preview.py::test_n02_10_keystroke_echo_while_a_preview_result_arrives"
LINE = re.compile(r"N02-10 largest GUI tick gap (\d+) ms; window .*? results set \(ms, r_inner\): (\[.*\])")
SPIN = "while True: pass"


def run_once() -> tuple[int, bool, str]:
    """Run the test once; return (largest gap ms, passed, results set)."""
    argv = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-s", TEST]
    completed = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=False)
    found = LINE.search(completed.stdout)
    if found is None:
        raise RuntimeError(f"no N02-10 line in the output:\n{completed.stdout[-3000:]}\n{completed.stderr[-3000:]}")
    return int(found.group(1)), completed.returncode == 0, found.group(2)


def main() -> None:
    """Run the test ``--runs`` times and print each gap and the summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--hog", action="store_true", help="spin a second CPU-bound process during every run")
    args = parser.parse_args()
    hog = subprocess.Popen([sys.executable, "-c", SPIN]) if args.hog else None
    gaps = []
    try:
        for index in range(args.runs):
            gap, passed, results = run_once()
            gaps.append(gap)
            print(f"run {index + 1:>2}: gap {gap:>4} ms  {'pass' if passed else 'FAIL'}  results set {results}", flush=True)
    finally:
        if hog is not None:
            hog.kill()
            hog.wait()
    passes = sum(gap <= 100 for gap in gaps)
    label = "with a CPU-bound process" if args.hog else "alone"
    print(f"== {label}: {passes}/{len(gaps)} pass; gap median {statistics.median(gaps)} ms, max {max(gaps)} ms")


if __name__ == "__main__":
    main()
