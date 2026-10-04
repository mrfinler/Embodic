"""Seeded-defect lever: apply each named defect to a temporary copy of the instruments and confirm a test fails.

Run from the repository root: ``python tests/independent/m1/mutants.py``. Exit status 1 when a mutant survives.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (defect, file, original text, defective text)
MUTANTS = [
    ("sagitta dropped from the bound", "brute_clearance.py",
     "return rows, 2.0 * p.r * np.sin(sweep / 4.0) ** 2", "return rows, 0.0 * sweep"),
    ("second half of a split piece never visited", "brute_clearance.py",
     "second_ps = np.where(split_p, ps + half_p, ps)", "second_ps = ps"),
    ("proper crossing not detected", "brute_clearance.py",
     "return np.where(crossing, 0.0, ends)", "return ends"),
    ("infinite-line distance instead of segment", "brute_clearance.py",
     "t = np.clip(t, 0.0, 1.0)", "t = t"),
    ("epsilon 0 in D-006", "brute_clearance.py",
     "threshold = rule_mm - epsilon_mm", "threshold = rule_mm"),
    ("Xcoil 0.004 mm slack in D-006", "brute_clearance.py",
     "threshold = rule_mm - epsilon_mm", "threshold = rule_mm - 0.004"),
    ("box cull ignores arc sagitta", "brute_clearance.py",
     "float((ys.max(axis=1) + sag).max()),", "float(ys.max()),"),
    ("clearance clamped at zero", "brute_clearance.py",
     "return centreline_bracket(p, q, tol=tol, threshold=centre_threshold).shifted(-half_widths)",
     "b = centreline_bracket(p, q, tol=tol, threshold=centre_threshold).shifted(-half_widths)\n"
     "    return Bracket(max(b.lo, 0.0), max(b.hi, 0.0))"),
    ("continuity compares start to start", "continuity.py",
     "end, nxt = end_point(here), start_point(there)", "end, nxt = start_point(here), start_point(there)"),
    ("continuity tolerance 1e-6 instead of 1e-9", "continuity.py",
     "CONTINUITY_TOL_MM = 1e-9", "CONTINUITY_TOL_MM = 1e-6"),
    ("continuity passes NaN", "continuity.py", "if not distance <= tol_mm:", "if distance > tol_mm:"),
    ("reader orders paths by file position", "board_dump_reader.py", "key=lambda p: p.seq", "key=lambda p: 0"),
    ("reader skips the end-point check", "board_dump_reader.py",
     'problems += _check_ends(where, prim, rec["start"], rec["end"])', "pass"),
    ("reader takes a2 as the sweep", "board_dump_reader.py", 'rec["a2"] - rec["a1"]', 'rec["a2"]'),
    ("reader skips object membership", "board_dump_reader.py",
     "problems += _check_membership(doc, primitives)", "pass"),
    ("reader keeps encoded non-finite numbers", "board_dump_reader.py",
     'return _NON_FINITE[value["$f"]]', "return value"),
]  # fmt: skip

PYTEST_INI = "[pytest]\naddopts = --import-mode=importlib -p no:cacheprovider\nmarkers =\n    req(*ids): REQ IDs\n"


def run_mutant(defect: str, name: str, old: str, new: str) -> tuple[bool, str]:
    """Return (killed, first failing test) for one mutant."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "m1"
        shutil.copytree(HERE, work, ignore=shutil.ignore_patterns("__pycache__", "mutants.py"))
        (Path(tmp) / "pytest.ini").write_text(PYTEST_INI, encoding="utf-8")
        target = work / name
        source = target.read_text(encoding="utf-8")
        if source.count(old) != 1:
            raise SystemExit(f"{defect}: original text must occur once in {name}")
        target.write_text(source.replace(old, new), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(work),
                "-q",
                "-x",
                "--rootdir",
                tmp,
                "-c",
                str(Path(tmp) / "pytest.ini"),
            ],
            capture_output=True,
            text=True,
        )
        failed = [line for line in result.stdout.splitlines() if line.startswith("FAILED")]
        return result.returncode == 1 and bool(failed), failed[0] if failed else result.stdout[-300:]


def main() -> int:
    """Run every mutant and print one line each."""
    survivors = 0
    for defect, name, old, new in MUTANTS:
        killed, detail = run_mutant(defect, name, old, new)
        survivors += not killed
        print(f"{'killed  ' if killed else 'SURVIVED'} {defect}: {detail}")
    print(f"{len(MUTANTS) - survivors}/{len(MUTANTS)} mutants killed")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
