"""Check that every reference in the Phase 4 acceptance plan resolves in this checkout.

    python3 docs/phase4/verification/checks/plan_refs.py [--self-test]

It checks decision rows (D-nnn and D-nnn plus a clause letter) against docs/decision_log.md, REQ IDs against
requirements.md, XD IDs against tests/golden/expected_diffs, DEF IDs against the docs, tests and CHANGELOG.md, and
every backticked repository path against the tree. It also fails on a long dash, a curly quote or a semicolon outside
code spans. Exit 0 when everything resolves.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PLAN = ROOT / "docs/phase4/verification/acceptance_plan.md"
NOT_YET = {"docs/phase4/design/uat_walkthrough.md"}
PATH_PREFIXES = ("docs/", "tests/", "tools/", "src/", "resources/", "requirements/")


def corpus(globs: tuple[str, ...]) -> str:
    files = (p for g in globs for p in ROOT.glob(g) if p.is_file() and "docs/phase4" not in p.as_posix())
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files)


def problems_of(text: str) -> list[str]:
    log = (ROOT / "docs/decision_log.md").read_text(encoding="utf-8")
    rows = set(re.findall(r"^\| (D-\d{3}[a-z]?) \|", log, re.M))
    reqs = set(
        re.findall(r"^\| (REQ-[A-Z]-\d\d) \|", (ROOT / "docs/phase2/architecture/requirements.md").read_text(), re.M)
    )
    diffs = corpus(("tests/golden/expected_diffs/*.toml",))
    defs = corpus(("docs/**/*.md", "tests/**/*.md", "CHANGELOG.md"))
    found = []
    for ref in sorted(set(re.findall(r"\bD-\d{3}[a-z]?\b", text))):
        if ref not in rows and ref.rstrip("abcdefghijklmnopqrstuvwxyz") not in rows:
            found.append(f"decision row {ref} is not in the log")
    for ref in sorted(set(re.findall(r"\bREQ-[A-Z]-\d\d\b", text)) - reqs):
        found.append(f"{ref} is not a requirement row")
    for ref in sorted(set(re.findall(r"\bXD-[A-Z0-9]+-\d{3}\b", text))):
        if ref not in diffs:
            found.append(f"{ref} is not in tests/golden/expected_diffs")
    for ref in sorted(set(re.findall(r"\bDEF-[A-Z0-9-]*\d\b", text))):
        if ref != "DEF-UAT-nn" and ref not in defs:
            found.append(f"{ref} is named nowhere in docs, tests or CHANGELOG.md")
    for path in sorted(set(re.findall(r"`([^`\s]+)`", text))):
        exists = any(ROOT.glob(path)) if "*" in path else (ROOT / path).exists()
        if path.startswith(PATH_PREFIXES) and path not in NOT_YET and not exists:
            found.append(f"path {path} does not exist")
    prose = re.sub(r"`[^`]*`", "", text)
    for mark, name in (
        ("\u2014", "em dash"),
        ("\u2013", "en dash"),
        ("\u201c", "curly quote"),
        ("\u2019", "curly quote"),
    ):
        if mark in prose:
            found.append(f"{name} in prose")
    for number, line in enumerate(prose.splitlines(), 1):
        if ";" in line:
            found.append(f"semicolon on line {number}")
    return found


def main() -> int:
    if "--self-test" in sys.argv:
        planted = "D-999 REQ-F-99 XD-PHY-999 DEF-ZZ-99 `docs/no_such_file.md` a; b \u2014"
        found = problems_of(planted)
        expected = ("D-999", "REQ-F-99", "XD-PHY-999", "DEF-ZZ-99", "no_such_file", "semicolon", "em dash")
        missed = [e for e in expected if not any(e in f for f in found)]
        print(f"self-test: {len(expected) - len(missed)} of {len(expected)} plants found", *missed)
        return 1 if missed else 0
    found = problems_of(PLAN.read_text(encoding="utf-8"))
    for problem in found:
        print(problem)
    print(f"{PLAN.name}: {len(found)} problems")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
