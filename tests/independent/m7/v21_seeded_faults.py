"""U-V21: seed one fault per re-ruled row into a copy of release 0.0.5 and run the new tests that should kill it.

    python3 tests/independent/m7/v21_seeded_faults.py [--commit 42074f2] [--python <dev venv python>]

Each case extracts `git archive <commit>` into a new temporary folder, runs the case's tests on the unedited copy,
then applies one text edit to src and runs them again, with PYTHONPATH set to the copy's src so the edit is the code
under test. A case is `killed` when the clean run passes and the edited run fails; the first assertion line of the
failure is printed. The edits are Agent 4's choice for REQ-F-05 (a via analysed as two barrels) and REQ-F-13 (lower
layer copper stroked 0.1 mm thinner by the layer cue), independent of U-M8y's own seeded faults.
"""

import argparse
import io
import os
import re
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Case:
    """One seeded fault: the row, the file and the exact text it replaces, and the tests expected to fail."""

    req: str
    path: str
    old: str
    new: str
    tests: tuple[str, ...]


CASES = (
    Case(
        "REQ-F-05",
        "src/embodic/physics/analyse.py",
        "via_resistance_ohm(v.drill_mm, plating_um, length_mm, rho, 1)",
        "via_resistance_ohm(v.drill_mm, plating_um, length_mm, rho, 2)",
        ("tests/unit/physics/test_via_barrels.py",),
    ),
    Case(
        "REQ-F-13",
        "src/embodic/ui/views/layer_cue.py",
        "QPen(colour, width + grow_mm, Qt.PenStyle.SolidLine",
        "QPen(colour, width + grow_mm - 0.1, Qt.PenStyle.SolidLine",
        (
            "tests/ui/qt_shell/test_layer_cue.py::test_ui03_lower_layer_copper_the_cue_paints_keeps_its_trace_width_at_200x",
            "tests/ui/qt_shell/test_layer_cue.py::test_ui03_the_cue_strokes_lower_copper_at_its_trace_width_at_0_1x_and_200x",
        ),
    ),
)


def pytest(python: str, root: Path, tests: tuple[str, ...]) -> tuple[int, str]:
    """Run the tests in root against root/src; return the exit code and the summary plus the first assertion line."""
    env = {**os.environ, "PYTHONPATH": str(root / "src"), "QT_QPA_PLATFORM": "offscreen"}
    done = subprocess.run(
        [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", *tests],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    summary = re.findall(r"^\d+ (?:passed|failed).*$", done.stdout, re.MULTILINE)
    first = re.findall(r"^E\s+(.*)$", done.stdout, re.MULTILINE)
    return done.returncode, "; ".join([*summary[-1:], *first[:1]])


def main() -> int:
    """Print the clean and the seeded result of every case; exit 1 when a case is not killed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--commit", default="42074f2")
    parser.add_argument("--python", default="/home/claude/embodic/.venv/bin/python", help="the dev venv python")
    args = parser.parse_args()
    tar = subprocess.run(["git", "-C", str(REPO), "archive", args.commit], capture_output=True, check=True).stdout
    survivors = 0
    for case in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
                archive.extractall(root, filter="data")
            target = root / case.path
            text = target.read_text(encoding="utf-8")
            assert text.count(case.old) == 1, f"{case.path}: the seeded text moved"
            clean_code, clean = pytest(args.python, root, case.tests)
            target.write_text(text.replace(case.old, case.new), encoding="utf-8")
            seeded_code, seeded = pytest(args.python, root, case.tests)
        killed = clean_code == 0 and seeded_code != 0
        survivors += not killed
        print(f"{case.req} {case.path}: {case.old!r} -> {case.new!r}")
        print(f"  clean:  exit {clean_code}; {clean}")
        print(f"  seeded: exit {seeded_code}; {seeded}")
        print(f"  {'killed' if killed else 'NOT KILLED'}")
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
