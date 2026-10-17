# Prepared by: Agent 6 - Software Architecture Specialist - model: claude-opus-5-5
"""List the issue codes that src defines or emits and interfaces.md does not name (unit U-D20, D-055).

Run from anywhere:
    python3 docs/phase2/architecture/checks/issue_code_coverage.py

A code counts as defined when it is a key of a `MESSAGES` dict under src/embodic/errors/catalogue, and as emitted when
the string literal appears in any other module under src/embodic. Each missing code is printed with the src lines that
hold the literal, so a reader can find its category, severity, pointers, limit and hint. Exit code 0 when interfaces.md
names every code, 1 otherwise.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ARCH = Path(__file__).resolve().parents[1]
REPO = ARCH.parents[2]
SRC = REPO / "src/embodic"
CATALOGUE = SRC / "errors/catalogue"
INTERFACES = ARCH / "interfaces.md"
CODE = re.compile(r"\b(?:INVALID|MISSING|RANGE|UNBUILDABLE|DRC|INTERNAL|INFO)_[A-Z0-9_]*[A-Z0-9]\b")


def catalogue_codes() -> dict[str, str]:
    codes: dict[str, str] = {}
    for path in sorted(CATALOGUE.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str) and CODE.fullmatch(key.value):
                        codes[key.value] = path.name
    return codes


def emitted_codes() -> dict[str, list[str]]:
    sites: dict[str, list[str]] = {}
    for path in sorted(SRC.rglob("*.py")):
        if CATALOGUE in path.parents:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        exported = {  # names in __all__, such as DRC_EPSILON_MM, are attributes, not issue codes
            id(c) for n in ast.walk(tree) if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets) for c in ast.walk(n.value)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and CODE.fullmatch(node.value):
                if id(node) not in exported:
                    sites.setdefault(node.value, []).append(f"{path.relative_to(REPO)}:{node.lineno}")
    return sites


def main() -> int:
    named = set(CODE.findall(INTERFACES.read_text(encoding="utf-8")))
    defined = catalogue_codes()
    emitted = emitted_codes()
    missing = sorted((set(defined) | set(emitted)) - named)
    never_emitted = sorted(set(defined) - set(emitted))
    print(f"catalogue codes: {len(defined)}; emitted as literals outside the catalogue: {len(emitted)}; "
          f"named in interfaces.md: {len(named & (set(defined) | set(emitted)))}")
    if never_emitted:
        print(f"catalogue codes with no literal outside the catalogue (built at run time or unused): {never_emitted}")
    for code in missing:
        print(f"MISSING {code} [{defined.get(code, 'not in catalogue')}] at {', '.join(emitted.get(code, ['-']))}")
    if missing:
        print(f"FAIL: {len(missing)} code(s) absent from interfaces.md")
        return 1
    print("PASS: interfaces.md names every catalogue code and every code literal in src")
    return 0


if __name__ == "__main__":
    sys.exit(main())
