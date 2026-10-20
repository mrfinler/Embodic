"""U-V20 item 4: the static gates and the trace matrix of the release profile, run one by one on a tree (not ci.py).

    python3 tests/independent/m7/v20_pre_gate.py --tree <checkout of 99d355d> --reports <main.json> <latency.json> \
        --manual-records <index> --out <log>

The pytest processes run before this script, by hand, with the release marker expressions and --req-report. This
script runs the gates of tools/ci.py `gates_for(release)` that need no build: ruff check and format (MT-03), the import
contracts (MT-01), mypy (MT-02) and the trace matrix with --fail-untested-through=M5 (TR-01, TR-02). It does not build
the bundle, record the passed-test evidence (TR-05) or build the wheel (PK-10). The log ends with one PASS or FAIL line
per gate in the form of ci.py's summary, so req_audit.py reads the gate IDs from it; the first line says who wrote it.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

LINT_IMPORTS = "import sys; from importlinter.cli import lint_imports_command; sys.exit(lint_imports_command())"


def main(argv: list[str] | None = None) -> int:
    """Run each gate in the tree, write the log and return 1 when a gate failed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--reports", type=Path, nargs="+", required=True)
    parser.add_argument("--manual-records", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    py, tree = args.python, args.tree.resolve()
    trace = [py, str(tree / "tools/trace_matrix.py"), "--report", *map(str, args.reports)]
    trace += [f"--out={args.out.with_suffix('.trace_matrix.md')}", "--fail-untested-through=M5"]
    trace += [f"--manual-records={args.manual_records}"]
    gates = [
        ("ruff check (MT-03)", [py, "-m", "ruff", "check", "."]),
        ("ruff format (MT-03)", [py, "-m", "ruff", "format", "--check", "."]),
        ("import contracts C1-C4 (MT-01)", [py, "-c", LINT_IMPORTS]),
        ("mypy strict (MT-02)", [py, "-m", "mypy"]),
        ("trace matrix (TR-01, TR-02)", trace),
    ]
    lines = [f"U-V20 pre-gate log of {tree}, written by tests/independent/m7/v20_pre_gate.py, not tools/ci.py"]
    summary = []
    for name, argv_ in gates:
        start = time.monotonic()
        done = subprocess.run(argv_, cwd=tree, capture_output=True, text=True, check=False)
        took = time.monotonic() - start
        lines += [
            f"=== {name}: {' '.join(argv_)}",
            done.stdout.rstrip(),
            done.stderr.rstrip(),
            f"exit {done.returncode}",
        ]
        summary.append(f"{'PASS' if done.returncode == 0 else 'FAIL'} {took:7.1f} s  {name}")
    lines += ["=== summary: release-profile gates run one by one (no bundle, TR-05, wheel or PK-10)", *summary]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(summary))
    return 0 if all(line.startswith("PASS") for line in summary) else 1


if __name__ == "__main__":
    sys.exit(main())
