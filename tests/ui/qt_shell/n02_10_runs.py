r"""DEF-U-M6a-01 lever (U-M8n): the gap distribution of N02-10 over repeated runs, alone or beside a CPU-bound process.

Runs one N02-10 case in a fresh pytest process per run and prints, per run, the largest GUI tick gap, the verdict and
the results the test saw set; then the median and the max. ``--case cancel`` (the default) types over a preview in
flight; ``--case arrival`` types on as a preview result is set (DEF-U-M8n-03, U-M8o). With
``--hog``, a second Python process spins on one core for the whole run, as the release gate's other work does on a
2-core machine. ``--switch-interval S`` replaces the shell's GIL switch interval for the run (CPython's default is
0.005), the experiment that showed the gap waiting for the GIL (U-M8n).

Not a test. From the repository root, with the project's interpreter:

    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/ui/qt_shell/n02_10_runs.py --runs 10 [--case arrival] [--hog]
"""

import argparse
import re
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CASES = {
    "cancel": "test_n02_10_keystroke_echo_while_a_preview_result_arrives",
    "arrival": "test_n02_10_keystroke_echo_when_a_preview_result_lands_and_typing_goes_on",
}
LINE = re.compile(r"N02-10 largest GUI tick gap (\d+) ms; window .*? results set \(ms, r_inner\): (\[.*\])")
SPIN = "while True: pass"


def run_once(case: str, switch_interval_s: float | None) -> tuple[int, bool, str]:
    """Run the test of ``case`` once; return (largest gap ms, passed, results set)."""
    options = ["-p", "no:cacheprovider", "-q", "-s", f"tests/ui/qt_shell/test_n02_typing_preview.py::{CASES[case]}"]
    argv = [sys.executable, "-m", "pytest", *options]
    if switch_interval_s is not None:
        code = f"app.GIL_SWITCH_INTERVAL_S = {switch_interval_s!r}; sys.exit(pytest.main({options!r}))"
        argv = [sys.executable, "-c", f"import sys, pytest, embodic.ui.app as app; {code}"]
    completed = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, check=False)
    found = LINE.search(completed.stdout)
    if found is None:
        raise RuntimeError(f"no N02-10 line in the output:\n{completed.stdout[-3000:]}\n{completed.stderr[-3000:]}")
    return int(found.group(1)), completed.returncode == 0, found.group(2)


def main() -> None:
    """Run the test ``--runs`` times and print each gap and the summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--case", choices=sorted(CASES), default="cancel")
    parser.add_argument("--hog", action="store_true", help="spin a second CPU-bound process during every run")
    parser.add_argument("--switch-interval", type=float, help="the GIL switch interval of the shell, in seconds")
    args = parser.parse_args()
    hog = subprocess.Popen([sys.executable, "-c", SPIN]) if args.hog else None
    gaps = []
    try:
        for index in range(args.runs):
            gap, passed, results = run_once(args.case, args.switch_interval)
            gaps.append(gap)
            verdict = "pass" if passed else "FAIL"
            print(f"run {index + 1:>2}: gap {gap:>4} ms  {verdict}  results set {results}", flush=True)
    finally:
        if hog is not None:
            hog.kill()
            hog.wait()
    passes = sum(gap <= 100 for gap in gaps)
    label = f"{args.case}, " + ("with a CPU-bound process" if args.hog else "alone")
    print(f"== {label}: {passes}/{len(gaps)} pass; gap median {statistics.median(gaps)} ms, max {max(gaps)} ms")


if __name__ == "__main__":
    main()
