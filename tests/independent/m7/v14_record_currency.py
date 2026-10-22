"""D-061d: whether each record of docs/phase3/verification/manual_records.json stands for a later build (U-V14).

    python3 tests/independent/m7/v14_record_currency.py [--target c0f4894]

A record stands when no file its subject depends on changed between the build the record names and the target
(`git diff --stat <build> <target> -- <files>` is empty). The files of a subject are its fixed paths (the guide, the
lock file, the example inputs, the corpus a word review read) plus the embodic modules that its instrument imports,
found by importing those modules from this checkout's src and listing the loaded files under src/embodic. The import
closure is a superset of what the subject reads, so a record this script calls stands is safe to carry over; one it
calls superseded may still give the same result, which only a rerun shows. A module that existed at the build and was
deleted since is not in the closure of this checkout (limit, `inferred` harmless: a deletion also edits an importer).
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INDEX = REPO / "docs/phase3/verification/manual_records.json"
WHEEL_INPUTS = ("pyproject.toml", "src/embodic", "resources")
INSTALL_GUIDE = ("README.md", "docs/install/INSTALL.md", "requirements/py311.txt", *WHEEL_INPUTS)
# A gate run on a checkout depends on the whole tree that pytest and tools/ci.py read. No test reads the records or the
# FEA results under tests/independent (`inferred` from grep of every test_*.py and conftest.py there, U-V30).
GATE_TREE = (
    *WHEEL_INPUTS,
    "requirements",
    "tools",
    "packaging",
    "tests",
    ":(exclude,glob)tests/independent/*/records/**",
    ":(exclude)tests/independent/m6/fea/results",
)


@dataclass(frozen=True)
class Subject:
    """What one record checked, against which build, and who redoes it when it is superseded."""

    record: str
    result: str
    build: str
    build_named_as: str
    paths: tuple[str, ...]
    imports: tuple[str, ...]
    redoer: str


SUBJECTS = (
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough.md",
        "passed",
        "5e74acc",
        "wheel f114a6e7 of release commit 5e74acc (record l.12-14)",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "docs/phase3/fable/windows_campaign_w1.md",
        "passed",
        "5e74acc",
        "the 0.0.1 wheel, build 0.0.1+g5e74acc4e79b (record l.4, l.31, l.45)",
        INSTALL_GUIDE,
        (),
        "the user (timed walkthrough on the Windows laptop)",
    ),
    Subject(
        "docs/phase3/fable/windows_campaign_w1.md",
        "failed",
        "5e74acc",
        "the 0.0.1 wheel, build 0.0.1+g5e74acc4e79b (record l.4, l.31, l.45)",
        INSTALL_GUIDE,
        (),
        "the user (timed walkthrough on the Windows laptop)",
    ),
    Subject(
        "tests/independent/m4/records/AX-05.md",
        "passed",
        "4fda98d",
        "main 4fda98d, worktree unit/U-V4 (record l.5)",
        ("resources/examples", "resources/themes"),
        ("embodic.api", "embodic.io.exporters", "embodic.io.svg_writer"),
        "Agent 4 (render and read the contact sheets)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12.md",
        "passed",
        "5e74acc",
        "release wheel f114a6e7 of 5e74acc, run from main f07d502 (record l.1, l.32-35)",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "tests/independent/m4/records/LG-01_word_review.md",
        "passed",
        "260191f",
        "main 260191f, worktree unit/U-V13 (record l.5)",
        (
            "src/embodic/ui/strings",
            "src/embodic/errors/catalogue",
            "src/embodic/io/report.py",
            "src/embodic/io/readme_writer.py",
        ),
        (),
        "Agent 4 (word review)",
    ),
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough_c0f4894.md",
        "passed",
        "c0f4894",
        "wheel cb4e51c2 built on main c0f4894 (record, Inputs)",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "tests/independent/m4/records/AX-05_c0f4894.md",
        "passed",
        "c0f4894",
        "main c0f4894, source tree (record l.5)",
        ("resources/examples", "resources/themes"),
        ("embodic.api", "embodic.io.exporters", "embodic.io.svg_writer"),
        "Agent 4 (render and read the contact sheets)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12_c0f4894.md",
        "passed",
        "c0f4894",
        "wheel cb4e51c2 built on main c0f4894 (record, What ran)",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "tests/independent/m4/records/LG-04_T-11_reviewer.md",
        "passed",
        "c0f4894",
        "main c0f4894, source tree, lg_allowlist.toml a19b5c80 (record l.5-12)",
        ("tests/static/lg_allowlist.toml", "resources/examples", "resources/evidence"),
        ("embodic.api", "embodic.io.report", "embodic.results.registry", "embodic.ui.viewmodels.results"),
        "Agent 4 (reviewer check)",
    ),
    Subject(
        "docs/phase3/fable/AX-06_narrator_0.0.3.md",
        "passed",
        "2fb2ec6",
        "the 0.0.3 source, editable install of the laptop checkout at 5f814d4 and 2fb2ec6 (record, Build)",
        ("pyproject.toml", "resources/examples", "resources/themes", "src/embodic/ui"),
        ("embodic.ui.app",),
        "the user (Windows Narrator walkthrough on the laptop)",
    ),
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough_c25d8a9.md",
        "passed",
        "c25d8a9",
        "release wheel 9bca49d8 of c25d8a9, tag v0.0.4 (record, Inputs)",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "tests/independent/m4/records/AX-05_c25d8a9.md",
        "passed",
        "c25d8a9",
        "main 705c1cb, src and resources equal to c25d8a9 (record l.5-7)",
        ("resources/examples", "resources/themes"),
        ("embodic.api", "embodic.io.exporters", "embodic.io.svg_writer"),
        "Agent 4 (render and read the contact sheets)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12_c25d8a9.md",
        "passed",
        "c25d8a9",
        "release wheel 9bca49d8 of c25d8a9 in /home/claude/wheelvenv-0.0.4 (record, What ran)",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "tests/independent/m4/records/LG-01_word_review_c25d8a9.md",
        "passed",
        "c25d8a9",
        "main 705c1cb, src equal to c25d8a9 (record l.5-6)",
        (
            "src/embodic/ui/strings",
            "src/embodic/errors/catalogue",
            "src/embodic/io/report.py",
            "src/embodic/io/readme_writer.py",
        ),
        (),
        "Agent 4 (word review)",
    ),
    Subject(
        "tests/independent/m4/records/LG-04_T-11_reviewer_c25d8a9.md",
        "passed",
        "c25d8a9",
        "main 705c1cb, src, resources and tests/static equal to c25d8a9 (record l.5-7)",
        ("tests/static/lg_allowlist.toml", "resources/examples", "resources/evidence"),
        ("embodic.api", "embodic.io.report", "embodic.results.registry", "embodic.ui.viewmodels.results"),
        "Agent 4 (reviewer check)",
    ),
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough_99d355d.md",
        "passed",
        "99d355d",
        "wheel 0dbac116 that Agent 4 built from 99d355d (record, Inputs); compare wheels with v21_wheel_diff.py",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "tests/independent/m4/records/AX-05_99d355d.md",
        "passed",
        "99d355d",
        "main 2cedac6, src and resources equal to 99d355d, source tree (record l.5-7)",
        ("resources/examples", "resources/themes"),
        ("embodic.api", "embodic.io.exporters", "embodic.io.svg_writer"),
        "Agent 4 (render and read the contact sheets)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12_99d355d.md",
        "passed",
        "99d355d",
        "wheel 0dbac116 of 99d355d in the PK-06 run 1 venv (record, What ran); compare wheels with v21_wheel_diff.py",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "tests/independent/m4/records/LG-04_T-11_reviewer_99d355d.md",
        "passed",
        "99d355d",
        "main 2cedac6, src, resources and tests/static equal to 99d355d, source tree (record l.5-7)",
        ("tests/static/lg_allowlist.toml", "resources/examples", "resources/evidence"),
        ("embodic.api", "embodic.io.report", "embodic.results.registry", "embodic.ui.viewmodels.results"),
        "Agent 4 (reviewer check)",
    ),
    Subject(
        "docs/phase3/fable/PF-01_windows_0.0.5.md",
        "failed",
        "bbeed84",
        "editable install of the laptop checkout bbeed84, embodic 0.0.5 (record, Build)",
        (
            "pyproject.toml",
            "resources/examples",
            "tests/performance/test_pf_baseline.py",
            "tests/performance/test_n01_pf01_budgets.py",
        ),
        ("embodic.api",),
        "Fable (PF-01 on the reference laptop)",
    ),
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough_42074f2.md",
        "passed",
        "42074f2",
        "release wheel a56eaebb of 42074f2, tag v0.0.5 (record, Inputs)",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12_42074f2.md",
        "passed",
        "42074f2",
        "release wheel a56eaebb of 42074f2 in /home/claude/wheelvenv-0.0.5 (record, What ran)",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough_6d50d0b.md",
        "passed",
        "6d50d0b",
        "wheel 5d891a26 that Agent 4 built from 6d50d0b (record, Inputs); compare wheels with v21_wheel_diff.py",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "tests/independent/m4/records/AX-05_6d50d0b.md",
        "passed",
        "6d50d0b",
        "worktree unit/U-V27, src and resources equal to 6d50d0b, source tree (record l.5-7)",
        ("resources/examples", "resources/themes"),
        ("embodic.api", "embodic.io.exporters", "embodic.io.svg_writer"),
        "Agent 4 (render and read the contact sheets)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12_6d50d0b.md",
        "passed",
        "6d50d0b",
        "wheel 5d891a26 of 6d50d0b in the PK-06 run 1 venv (record, What ran); compare wheels with v21_wheel_diff.py",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "tests/independent/m4/records/LG-01_word_review_6d50d0b.md",
        "passed",
        "6d50d0b",
        "worktree unit/U-V27, src equal to 6d50d0b (record l.5-6)",
        (
            "src/embodic/ui/strings",
            "src/embodic/errors/catalogue",
            "src/embodic/io/report.py",
            "src/embodic/io/readme_writer.py",
        ),
        (),
        "Agent 4 (word review)",
    ),
    Subject(
        "tests/independent/m4/records/LG-04_T-11_reviewer_6d50d0b.md",
        "passed",
        "6d50d0b",
        "worktree unit/U-V27, src, resources and tests/static equal to 6d50d0b, source tree (record l.5-7)",
        ("tests/static/lg_allowlist.toml", "resources/examples", "resources/evidence"),
        ("embodic.api", "embodic.io.report", "embodic.results.registry", "embodic.ui.viewmodels.results"),
        "Agent 4 (reviewer check)",
    ),
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough_672297e.md",
        "passed",
        "672297e",
        "wheel ad9e02c0 that Agent 4 built from 672297e (record, Inputs); compare wheels with v21_wheel_diff.py",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12_672297e.md",
        "passed",
        "672297e",
        "wheel ad9e02c0 of 672297e in the PK-06 run 1 venv (record, What ran); compare wheels with v21_wheel_diff.py",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "tests/independent/m4/records/LG-01_word_review_672297e.md",
        "passed",
        "672297e",
        "worktree unit/U-V28, src equal to 672297e, corpus equal to wheel ad9e02c0 (record l.5-7)",
        (
            "src/embodic/ui/strings",
            "src/embodic/errors/catalogue",
            "src/embodic/io/report.py",
            "src/embodic/io/readme_writer.py",
        ),
        (),
        "Agent 4 (word review)",
    ),
    Subject(
        "tests/independent/m4/records/LG-04_T-11_reviewer_672297e.md",
        "passed",
        "672297e",
        "wheel ad9e02c0 of 672297e and the source tree of worktree unit/U-V28 (record l.5-8)",
        ("tests/static/lg_allowlist.toml", "resources/examples", "resources/evidence"),
        ("embodic.api", "embodic.io.report", "embodic.results.registry", "embodic.ui.viewmodels.results"),
        "Agent 4 (reviewer check)",
    ),
    Subject(
        "tests/independent/m5/records/PK-06_walkthrough_2bfca49.md",
        "passed",
        "2bfca49",
        "release wheel fdb89189 of 2bfca49, tag v0.0.6 (record, title and Times per step)",
        INSTALL_GUIDE,
        (),
        "Agent 4 (Linux walkthrough in the container)",
    ),
    Subject(
        "tests/independent/m6/records/OR-11_OR-12_2bfca49.md",
        "passed",
        "2bfca49",
        "release wheel fdb89189 of 2bfca49 in /home/claude/wheelvenv-0.0.6 (record, What ran)",
        ("resources/evidence/equations.v1.json", "docs/phase2/engineering/oracle_cases.json"),
        ("embodic.api", "embodic.physics", "embodic.physics.emf", "embodic.geometry.primitives", "embodic.paths"),
        "Agent 4 (FEA rerun in GetDP)",
    ),
    Subject(
        "docs/phase3/fable/PK-06_windows_0.0.6.md",
        "passed",
        "2bfca49",
        "release wheel fdb89189 of 2bfca49 in a clean venv on the laptop, runs 11 and 12 (record, Build and Results)",
        INSTALL_GUIDE,
        (),
        "the user and Fable (timed walkthrough on the Windows laptop)",
    ),
    Subject(
        "docs/phase3/fable/windows_campaign_w2.md",
        "passed",
        "6ac95ac",
        "PK-04 on the release wheel fdb89189 and PK-05 on the bundle that the release run built, laptop checkout "
        "6ac95ac (record, Release 0.0.6)",
        (*WHEEL_INPUTS, "tools/build_bundle.py", "packaging"),
        (),
        "Fable (Windows laptop)",
    ),
    Subject(
        "docs/phase3/fable/windows_campaign_w2.md",
        "failed",
        "6ac95ac",
        "W7 commit profile and W8 release profile on the laptop checkout 6ac95ac (record, Release 0.0.6)",
        GATE_TREE,
        (),
        "Fable (Windows gates on the laptop)",
    ),
)


def import_closure(modules: tuple[str, ...]) -> list[str]:
    """Return the repository paths of the src/embodic files loaded when the modules are imported from this checkout."""
    if not modules:
        return []
    code = (
        "import importlib, sys\n"
        f"for m in {list(modules)!r}: importlib.import_module(m)\n"
        "print('\\n'.join(sorted({getattr(m, '__file__', None) or '' for m in sys.modules.values()})))"
    )
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "QT_QPA_PLATFORM": "offscreen"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, env=env).stdout
    root = (REPO / "src" / "embodic").resolve()
    return sorted(
        str(Path(f).resolve().relative_to(REPO)) for f in out.split() if f and Path(f).resolve().is_relative_to(root)
    )


def diff_stat(build: str, target: str, paths: list[str]) -> list[str]:
    """Return the `git diff --stat` lines of the paths between build and target, the summary line last."""
    argv = ["git", "-C", str(REPO), "diff", "--stat=200", build, target, "--", *paths]
    return subprocess.run(argv, capture_output=True, text=True, check=True).stdout.rstrip("\n").splitlines()


def main(argv: list[str] | None = None) -> int:
    """Print one block per index entry: build, files, diff summary and the verdict."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", default="c0f4894", help="the commit the next release gate builds")
    parser.add_argument("--index", type=Path, default=INDEX, help="manual-record index to judge")
    parser.add_argument("--verbose", action="store_true", help="also print every file and every diff --stat line")
    args = parser.parse_args(argv)

    by_key = {(s.record, s.result): s for s in SUBJECTS}
    entries = json.loads(args.index.read_text(encoding="utf-8"))
    for n, entry in enumerate(entries):
        subject = by_key.get((entry["record"], entry["result"]))
        if subject is None:
            print(f"[{n}] {entry['test_id']} {entry['record']} ({entry['result']}): no subject defined here")
            continue
        closure = import_closure(subject.imports)
        stat = diff_stat(subject.build, args.target, [*subject.paths, *closure])
        verdict = "stands" if not stat else f"superseded; redone by {subject.redoer}"
        print(f"[{n}] {entry['req']} {entry['test_id']} {entry['record']} ({entry['result']})")
        print(f"    build: {subject.build_named_as}")
        print(f"    files: {', '.join(subject.paths)}" + (f" + {len(closure)} imported modules" if closure else ""))
        print(f"    git diff --stat {subject.build}..{args.target}: {stat[-1].strip() if stat else 'no change'}")
        print(f"    verdict: {verdict}")
        if args.verbose:
            files = [f"      file {f}" for f in [*subject.paths, *closure]]
            print(*files, *(f"      {line}" for line in stat), sep="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
