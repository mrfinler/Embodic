"""Seeded-defect lever: apply each named defect to a temporary copy of the instruments and confirm a test fails.

Run from the repository root: ``python tests/independent/m1/mutants.py [word ...]``; words pick mutants by name.
Exit status 1 when a mutant survives, 2 when the unmutated copy already fails.
"""

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]

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
    ("continuity tolerance 1e-5 instead of 1e-6", "continuity.py",
     "CONTINUITY_TOL_MM = 1e-6", "CONTINUITY_TOL_MM = 1e-5"),
    ("rule 1 back to abs(main) <= 1 for fillets", "drc_universe.py",
     "near = bool(owners[i] & owners[j])", "near = abs(min(owners[i]) - min(owners[j])) <= 1"),
    ("D-022c tap rule dropped", "drc_universe.py",
     "if path and _on_centreline(land, path):", "if False:"),
    ("rule 2b whole path instead of per primitive (D-037a)", "drc_universe.py",
     "yield from (frozenset((via.label, it.label)) for it in hits if it.net == via.net)",
     "yield from (frozenset((via.label, o.label)) for it in hits if it.net == via.net "
     "for o in traces.items if o.path == it.path)"),
    ("rule 2b without the net test", "drc_universe.py", "for it in hits if it.net == via.net)", "for it in hits)"),
    ("rule 2b reach is the pad diameter", "drc_universe.py",
     "hits = traces.within(disc_centre(via), via.prim.width / 2)",
     "hits = traces.within(disc_centre(via), via.prim.width)"),
    ("rule 5 dropped", "drc_universe.py", "yield from _pairs(e.group, paths[pid])", "yield from ()"),
    ("rule 5 without the net test", "drc_universe.py",
     "if it.path != e.path and it.net == e.net}", "if it.path != e.path}"),
    ("rule 5 exempts the whole stem path", "drc_universe.py",
     "yield from _pairs(e.group, paths[pid])", "yield from _pairs(paths[e.path], paths[pid])"),
    ("arc sweep read as counter-clockwise always", "drc_universe.py",
     "turned = math.copysign(1.0, prim.sweep) * (", "turned = ("),
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


def _mirror(tmp: Path) -> Path:
    """Lay out ``tmp`` like the repository: everything linked except a fresh copy of ``tests/independent/m1``.

    The instruments find the GR-19 fixtures through ``parents[3]`` of their own file, so a bare copy fails tests that
    have nothing to do with the mutant.
    """
    src, dst = REPO, tmp
    for part in ("tests", "independent"):
        for entry in src.iterdir():
            if entry.name != part:
                (dst / entry.name).symlink_to(entry)
        src, dst = src / part, dst / part
        dst.mkdir()
    for entry in src.iterdir():
        if entry.name != "m1":
            (dst / entry.name).symlink_to(entry)
    work = dst / "m1"
    shutil.copytree(HERE, work, ignore=shutil.ignore_patterns("__pycache__", "mutants.py"))
    (tmp / "pytest.ini").write_text(PYTEST_INI, encoding="utf-8")
    return work


def _pytest(edit: tuple[str, str, str] | None) -> subprocess.CompletedProcess[str]:
    """Run the m1 tests on a mirrored copy, with ``(file, original, defective)`` applied when given."""
    with tempfile.TemporaryDirectory() as tmp:
        work = _mirror(Path(tmp))
        if edit is not None:
            name, old, new = edit
            target = work / name
            source = target.read_text(encoding="utf-8")
            if source.count(old) != 1:
                raise SystemExit(f"original text must occur once in {name}: {old!r}")
            target.write_text(source.replace(old, new), encoding="utf-8")
        argv = [sys.executable, "-m", "pytest", str(work), "-q", "-x", "--rootdir", tmp, "-c", f"{tmp}/pytest.ini"]
        return subprocess.run(argv, capture_output=True, text=True, cwd=tmp)


def run_mutant(defect: str, name: str, old: str, new: str) -> tuple[bool, str]:
    """Return (killed, first failing test) for one mutant."""
    result = _pytest((name, old, new))
    failed = [line for line in result.stdout.splitlines() if line.startswith("FAILED")]
    return result.returncode == 1 and bool(failed), failed[0] if failed else result.stdout[-300:]


def main(only: Sequence[str] = ()) -> int:
    """Check the unmutated copy passes, then run every mutant (or those whose name holds one of ``only``)."""
    base = _pytest(None)
    if base.returncode != 0:
        print(f"unmutated copy fails, no mutant can be judged:\n{base.stdout[-600:]}")
        return 2
    chosen = [m for m in MUTANTS if not only or any(word in m[0] for word in only)]
    survivors = 0
    for defect, name, old, new in chosen:
        killed, detail = run_mutant(defect, name, old, new)
        survivors += not killed
        print(f"{'killed  ' if killed else 'SURVIVED'} {defect}: {detail}", flush=True)
    print(f"{len(chosen) - survivors}/{len(chosen)} mutants killed")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
