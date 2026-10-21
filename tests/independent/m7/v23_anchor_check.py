"""Pre-run check of U-V23: every mutant's original text occurs once in the checkout, and every named killer collects.

Run from the repository root with the dev venv and ``PYTHONPATH=src``:

    python tests/independent/m7/v23_anchor_check.py V3-02 V3-03 V3-05 V3-06

V3-02 to V3-05 read ``product_mutant_tables.py`` against ``src/embodic``; V3-06 reads the ``MUTANTS`` of
``tests/independent/m1/mutants.py`` against ``tests/independent/m1``. Exit 1 when an anchor is missing or repeated, or a
named killer does not collect.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "tests/independent/m7"), str(REPO / "tests/independent/m1")]


def product(campaign: str) -> list[str]:
    """Return one problem line per anchor of ``campaign`` not exactly once in src, or per killer that won't collect."""
    from product_mutant_tables import CAMPAIGNS

    problems = []
    killers = []
    for m in CAMPAIGNS[campaign]:
        count = (REPO / "src/embodic" / m.file).read_text(encoding="utf-8").count(m.old)
        print(f"{campaign} {m.id}: anchor x{count} in {m.file}")
        if count != 1:
            problems.append(f"{m.id}: anchor occurs {count} times in {m.file}")
        killers += m.killers
    argv = [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *dict.fromkeys(killers)]
    done = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    print(f"{campaign} killers collect: exit {done.returncode}, {done.stdout.strip().splitlines()[-1]}")
    if done.returncode != 0:
        problems.append(f"{campaign}: named killers do not collect\n{done.stdout[-1500:]}{done.stderr[-500:]}")
    return problems


def instruments() -> list[str]:
    """Return one problem line per M1 instrument mutant whose original text is not exactly once in its file."""
    from mutants import MUTANTS

    problems = []
    for defect, name, old, _ in MUTANTS:
        count = (REPO / "tests/independent/m1" / name).read_text(encoding="utf-8").count(old)
        print(f"V3-06 {defect}: anchor x{count} in {name}")
        if count != 1:
            problems.append(f"{defect}: anchor occurs {count} times in {name}")
    print(f"V3-06: {len(MUTANTS)} mutants in the table")
    return problems


def main(campaigns: list[str]) -> int:
    """Check each named campaign and print every problem; exit 1 when there is one."""
    problems = [p for c in campaigns for p in (instruments() if c == "V3-06" else product(c))]
    for line in problems:
        print(f"PROBLEM {line}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
