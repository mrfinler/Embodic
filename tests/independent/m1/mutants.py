"""Seeded-defect lever: apply each named defect to a temporary copy of the instruments and confirm a test fails.

Run from the repository root: ``python tests/independent/m1/mutants.py [--tests=FILE] [word ...]``; words pick mutants
by name, and ``--tests`` runs one test file of the copy instead of the whole m1 suite.
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
    ("leading fillet or taper also belongs to main 1 (DEF-UD25-01)", "drc_universe.py",
     "out.append(frozenset(m for m in (seen - 1, seen) if 0 <= m < total))",
     "out.append(frozenset(m for m in ((seen - 1, seen) if seen else (0, 1)) if 0 <= m < total))"),
    ("rule 2 tap dropped", "drc_universe.py", "elif it.path in interconnect:", "elif False:"),
    ("rule 2 tap whole path (D-022c before D-078)", "drc_universe.py",
     "yield frozenset((via.label, it.label)), Rule.INTERCONNECT_TAP",
     "yield from ((frozenset((via.label, o.label)), Rule.INTERCONNECT_TAP) for o in traces.items "
     "if o.path == it.path)"),
    ("rule 2 tap and rule 2b over pads too (Q3)", "drc_universe.py",
     "if via.cls is Cls.VIA:", "if via.cls in (Cls.VIA, Cls.PAD):"),
    ("rule 2b whole path instead of per primitive (D-037a)", "drc_universe.py",
     "yield frozenset((via.label, it.label)), Rule.VIA_TAP",
     "yield from ((frozenset((via.label, o.label)), Rule.VIA_TAP) for o in traces.items if o.path == it.path)"),
    ("rule 2b without the net test", "drc_universe.py", "if it.net == via.net:", "if True:"),
    ("rule 2b reach is the pad diameter", "drc_universe.py",
     "for it in traces.within(disc_centre(via), via.prim.width / 2):",
     "for it in traces.within(disc_centre(via), via.prim.width):"),
    ("rule 5 dropped", "drc_universe.py",
     "yield from _pairs(e.group, _landing_group(path, owners[it.path], path.index(it)))", "yield from ()"),
    ("rule 5 without the net test", "drc_universe.py",
     "if it.path != e.path and it.net == e.net and it.layer == e.layer:",
     "if it.path != e.path and it.layer == e.layer:"),
    ("rule 5 exempts the whole stem path", "drc_universe.py",
     "yield from _pairs(e.group, _landing_group(path, owners[it.path], path.index(it)))",
     "yield from _pairs(paths[e.path], _landing_group(path, owners[it.path], path.index(it)))"),
    ("rule 5 exempts the whole other path (DEF-UV16-01)", "drc_universe.py",
     "yield from _pairs(e.group, _landing_group(path, owners[it.path], path.index(it)))",
     "yield from _pairs(e.group, path)"),
    ("rule 5 landing group is the hit primitive alone", "drc_universe.py",
     "yield from _pairs(e.group, _landing_group(path, owners[it.path], path.index(it)))",
     "yield from _pairs(e.group, [it])"),
    ("rule 5 landing group of a main reaches its rule 1 neighbours", "drc_universe.py",
     "return [it for j, it in enumerate(path) if j == k or (it.corner and owners[k] <= owners[j])]",
     "return [it for j, it in enumerate(path) if bool(owners[k] & owners[j]) "
     "or (not it.corner and abs(min(owners[j]) - min(owners[k])) <= 1)]"),
    ("arc sweep read as counter-clockwise always", "drc_universe.py",
     "turned = math.copysign(1.0, prim.sweep) * (", "turned = ("),
    ("continuity passes NaN", "continuity.py", "if not distance <= tol_mm:", "if distance > tol_mm:"),
    ("GR-19 ic objects mapped unsplit (DEF-M1V-03)", "gr19.py",
     "mapper.layout_from_xcoil(split_interconnect_chains(raw))", "mapper.layout_from_xcoil(raw)"),
    ("GR-19 ic objects cut at every primitive", "gr19.py",
     'runs = chains([_centreline(rec) for rec in obj["prims"]])',
     'runs = [range(k, k + 1) for k in range(len(obj["prims"]))]'),
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


def _pytest(edit: tuple[str, str, str] | None, tests: str = "") -> subprocess.CompletedProcess[str]:
    """Run the m1 tests (or the file ``tests``) on a mirrored copy, with ``(file, original, defective)`` applied."""
    with tempfile.TemporaryDirectory() as tmp:
        work = _mirror(Path(tmp))
        if edit is not None:
            name, old, new = edit
            target = work / name
            source = target.read_text(encoding="utf-8")
            if source.count(old) != 1:
                raise SystemExit(f"original text must occur once in {name}: {old!r}")
            target.write_text(source.replace(old, new), encoding="utf-8")
        argv = [
            sys.executable,
            "-m",
            "pytest",
            str(work / tests),
            "-q",
            "-x",
            "--rootdir",
            tmp,
            "-c",
            f"{tmp}/pytest.ini",
        ]
        return subprocess.run(argv, capture_output=True, text=True, cwd=tmp)


def run_mutant(defect: str, name: str, old: str, new: str, tests: str = "") -> tuple[bool, str]:
    """Return (killed, first failing test) for one mutant."""
    result = _pytest((name, old, new), tests)
    failed = [line for line in result.stdout.splitlines() if line.startswith("FAILED")]
    return result.returncode == 1 and bool(failed), failed[0] if failed else result.stdout[-300:]


def main(only: Sequence[str] = ()) -> int:
    """Check the unmutated copy passes, then run every mutant (or those whose name holds one of ``only``)."""
    tests = next((w.removeprefix("--tests=") for w in only if w.startswith("--tests=")), "")
    only = [w for w in only if not w.startswith("--tests=")]
    base = _pytest(None, tests)
    if base.returncode != 0:
        print(f"unmutated copy fails, no mutant can be judged:\n{base.stdout[-600:]}")
        return 2
    chosen = [m for m in MUTANTS if not only or any(word in m[0] for word in only)]
    survivors = 0
    for defect, name, old, new in chosen:
        killed, detail = run_mutant(defect, name, old, new, tests)
        survivors += not killed
        print(f"{'killed  ' if killed else 'SURVIVED'} {defect}: {detail}", flush=True)
    print(f"{len(chosen) - survivors}/{len(chosen)} mutants killed")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
