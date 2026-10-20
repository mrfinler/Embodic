"""V3-01 for release 0.0.4 (U-V18): the live must rows whose tests changed between two builds, with the changed files.

    python3 tests/independent/m7/v18_changed_rows.py --report R.json [--report L.json] [--base 0a74974] [--head c25d8a9]

A row is listed when a test .py file that `git diff --name-only <base> <head> -- tests` names holds a record that
carries the row's REQ marker in the reports. The product files under src/ that changed are printed too, each with the
rows whose changed tests name it (by module path in the test file's text), so a code change without a changed test
shows as a module with no row.
"""

import argparse
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REQUIREMENTS = REPO / "docs/phase2/architecture/requirements.md"


def live_must_rows() -> dict[str, str]:
    """Return {REQ id: disposition} of the must rows of requirements.md that are not withdrawn."""
    rows = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 9 and re.fullmatch(r"REQ-[FNKTL]-\d{2}", cells[0]) and cells[4] == "must":
            if cells[1] != "withdrawn":
                rows[cells[0]] = cells[1]
    return rows


def changed(base: str, head: str, folder: str) -> list[str]:
    """Return the paths under folder that differ between base and head."""
    argv = ["git", "-C", str(REPO), "diff", "--name-only", base, head, "--", folder]
    return subprocess.run(argv, capture_output=True, text=True, check=True).stdout.split()


def show(commit: str, path: str) -> str:
    """Return the text of path at commit, or "" when the file does not exist there."""
    done = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{path}"], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else ""


def main(argv: list[str] | None = None) -> int:
    """Print each changed test file with its must rows, then each must row with its changed files."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, action="append", required=True)
    parser.add_argument("--base", default="0a74974")
    parser.add_argument("--head", default="c25d8a9")
    args = parser.parse_args(argv)

    must = live_must_rows()
    reqs_of_file: dict[str, set[str]] = defaultdict(set)
    for report in args.report:
        for record in json.loads(report.read_text(encoding="utf-8")):
            reqs_of_file[record["nodeid"].split("::")[0]].update(record["req"])
    tests = [t for t in changed(args.base, args.head, "tests") if t.endswith(".py")]
    rows: dict[str, list[str]] = defaultdict(list)
    print(f"test .py files changed {args.base}..{args.head}: {len(tests)}")
    for path in tests:
        marked = sorted(r for r in reqs_of_file.get(path, ()) if r in must)
        print(f"  {path}: {', '.join(marked) if marked else '(no must marker in the reports)'}")
        for req in marked:
            rows[req].append(path)
    print(f"src files changed {args.base}..{args.head}:")
    for path in changed(args.base, args.head, "src"):
        module = path.removeprefix("src/").removesuffix(".py").replace("/", ".").removesuffix(".__init__")
        naming = [t for t in tests if module in show(args.head, t)]
        users = sorted({r for t in naming for r in reqs_of_file.get(t, ()) if r in must})
        print(f"  {path} ({module}): {', '.join(users) if users else 'no changed test names the module'}")
    print(f"live must rows with a changed test: {len(rows)} of {len(must)}")
    for req in sorted(rows):
        print(f"  {req}: {', '.join(rows[req])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
