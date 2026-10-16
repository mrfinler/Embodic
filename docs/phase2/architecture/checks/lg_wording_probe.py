# Prepared by: Agent 6 - Software Architecture Specialist - model: claude-sonnet-5-5
"""Count the wording hits that LG-03 to LG-06 would meet in src string literals and shipped text resources (U-D18).

The patterns copy `tests/independent/m7/v3_14_scan.py` l.60-69, so the counts compare with Agent 4's record V3-14. The
probe reads two corpora: the non-docstring string constants of `src/embodic/**/*.py` and the text files of
`resources/` (JSON by key and by value). It does not scan exports, because that needs a compute run. It prints counts
per class, corpus and kind. A literal that is lower case with no space counts as `identifier`, the V3-14 exemption.

Run from the repository root:
    python3 -I docs/phase2/architecture/checks/lg_wording_probe.py
    python3 -I docs/phase2/architecture/checks/lg_wording_probe.py --show "wording: measur"

`--show CLASS` also lists each hit that is not an identifier literal, with its place and its first 110 characters.

A third corpus, `guide`, holds only the registry fields that `equation_topic` renders in the equation guide
(`src/embodic/ui/viewmodels/results.py` l.699-740): `name`, `formula`, `label`, the dominant assumptions, the name and
rule of each validity check, the name and source of each constant, the test IDs, and the document and location of each
cited evidence entry. A class with no row in that corpus has no hit in it.
"""

import argparse
import ast
import json
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
START = r"(?:(?<![a-z])|(?-i:(?<=[a-z])(?=[A-Z])))"
END = r"(?-i:(?![a-z]))"
WORDING = {
    "wording: measur": re.compile(START + r"measur\w*", re.IGNORECASE),
    "wording: balance, torque, efficiency": re.compile(
        START + r"(?:balanc\w*|torque\w*|efficien\w*|imbalanc\w*|unbalanc\w*)", re.IGNORECASE
    ),
    "name: xcoil": re.compile(r"xcoil", re.IGNORECASE),
    "name: other program": re.compile(
        START + r"(?:kicad|kimotor|magnetless|femm|elmer|matlab|ansys|comsol|motor-?cad|pcbnew)" + END, re.IGNORECASE
    ),
}
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HOME = re.compile(r"(?:[A-Za-z]:\\+Users\\+|/home/|/Users/)(?![%$<{])([^\\/\s\"'<>`]+)")
HOME_PLACEHOLDERS = {"user", "username", "you", "name", "runner", "me"}
IDENTIFIER = re.compile(r"^[a-z0-9_.\-/#$\[\]]+$")
TEXT_SUFFIXES = {".md", ".txt", ".qss", ".toml", ".svg", ".html", ".csv", ".css"}

Item = tuple[str, str, str, str]  # corpus, kind, place, text


def source_items() -> Iterator[Item]:
    """Yield every non-docstring string constant of src/embodic."""
    for path in sorted((REPO / "src" / "embodic").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {
            id(node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip():
                if id(node) not in docstrings:
                    kind = "identifier" if IDENTIFIER.match(node.value) else "literal"
                    yield "src", kind, f"{path.relative_to(REPO)}:{node.lineno}", node.value


def json_items(text: str, place: str) -> Iterator[Item]:
    """Yield every key and every string value of a JSON document."""

    def walk(obj: object, pointer: str) -> Iterator[Item]:
        if isinstance(obj, dict):
            for key, value in obj.items():
                yield "resources", "json-key", f"{place}#{pointer}/{key}", key
                yield from walk(value, f"{pointer}/{key}")
        elif isinstance(obj, list):
            for value in obj:
                yield from walk(value, f"{pointer}/[]")
        elif isinstance(obj, str):
            yield "resources", "json-value", f"{place}#{pointer}", obj

    yield from walk(json.loads(text), "")


def resource_items() -> Iterator[Item]:
    """Yield the texts of every JSON and plain text file under resources/."""
    for path in sorted((REPO / "resources").rglob("*")):
        place = str(path.relative_to(REPO))
        if path.suffix == ".json":
            yield from json_items(path.read_text(encoding="utf-8"), place)
        elif path.suffix in TEXT_SUFFIXES:
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if line.strip():
                    yield "resources", "text-line", f"{place}:{number}", line


def guide_items() -> Iterator[Item]:
    """Yield the registry texts that the equation guide shows for every equation."""
    evidence = json.loads((REPO / "resources" / "evidence" / "evidence.v1.json").read_text(encoding="utf-8"))
    entries = {entry["id"]: entry for entry in evidence["entries"]}
    equations = json.loads((REPO / "resources" / "evidence" / "equations.v1.json").read_text(encoding="utf-8"))
    for equation in equations["equations"]:
        where = f"equations.v1.json#{equation['id']}"
        texts = [equation.get(key) for key in ("name", "formula", "label", "implementation")]
        texts += [assumption.get("text") for assumption in equation.get("dominant_assumptions", [])]
        for check in equation.get("validity_checks", []):
            texts += [check.get("name"), check.get("rule")]
        for constant in equation.get("constants", []):
            texts += [constant.get("name"), constant.get("source")]
        texts += equation.get("tests", [])
        for source in equation.get("sources", []):
            entry = entries.get(source)
            if entry is not None:
                texts += [entry["source"]["document"], entry["location"]["text"]]
        for text in texts:
            if isinstance(text, str) and text:
                yield "guide", "guide-field", where, text


def classify(items: Iterator[Item]) -> tuple[Counter[tuple[str, str, str]], dict[str, list[tuple[str, str]]]]:
    """Return the counts per (class, corpus, kind) and the hits that are not identifier literals, per class."""
    counts: Counter[tuple[str, str, str]] = Counter()
    shown: dict[str, list[tuple[str, str]]] = {}
    for corpus, kind, place, text in items:
        found = [name for name, pattern in WORDING.items() if pattern.search(text)]
        found += ["personal: e-mail address"] * len(EMAIL.findall(text))
        found += [
            "personal: home path with an account name"
            for match in HOME.finditer(text)
            if match.group(1).lower() not in HOME_PLACEHOLDERS
        ]
        for name in found:
            counts[(name, corpus, kind)] += 1
            if kind != "identifier":
                shown.setdefault(name, []).append((place, " ".join(text.split())[:110]))
    return counts, shown


def main() -> int:
    """Print the counts, and the hits of one class with --show."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--show", metavar="CLASS", help="also list the hits of one class")
    args = parser.parse_args()
    items = [*source_items(), *resource_items()]
    guide = list(guide_items())
    counts, shown = classify(iter([*items, *guide]))
    print(f"text items scanned: {len(items)}; guide fields scanned: {len(guide)}")
    for (name, corpus, kind), number in sorted(counts.items()):
        print(f"{name:42} {corpus:10} {kind:11} {number:4}")
    if args.show:
        print()
        for place, text in shown.get(args.show, []):
            print(f"{place} | {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
