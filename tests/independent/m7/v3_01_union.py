"""List, for each live must REQ-F row, every collected test that carries the row's REQ marker or names a planned ID.

    python3 tests/independent/m7/v3_01_union.py REPORT [REQ-F-nn ...]

REPORT is a `--req-report` JSON of a collect-only run (`pytest --collect-only --req-report PATH tests`). The output
is the reading list behind v3_01_rulings_f.py: per row, the acceptance cell, the planned IDs, and per test file the
test functions with their `def` line and whether they carry the marker (`m`), name a planned ID in the test name
(`i`), name one in the function's source, docstring included (`d`), or were found for a planned ID under another
label in the V3-01 cause-B rulings (`b`).
"""

import ast
import importlib.util
import json
import re
import sys
from collections import defaultdict
from functools import cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REQUIREMENTS = REPO / "docs/phase2/architecture/requirements.md"
RULINGS = REPO / "tests/independent/m7/v3_01_rulings.py"
TEST_ID = re.compile(r"\b(?:UT-[A-Z]{2,3}-\d{2}|(?:PR|GR|OR|BV|UI|AX|LG|MT|TR|PK|PF)-\d{2})\b")


def must_f_rows() -> dict[str, tuple[str, tuple[str, ...]]]:
    """REQ id -> (acceptance, planned IDs) for every live must REQ-F row."""
    rows = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if (
            len(cells) == 9
            and re.fullmatch(r"REQ-F-\d{2}", cells[0])
            and cells[4] == "must"
            and cells[1] != "withdrawn"
        ):
            rows[cells[0]] = (cells[5], tuple(TEST_ID.findall(cells[8])))
    return rows


def id_pattern(test_id: str) -> re.Pattern[str]:
    """Match the ID in a lower-case test name, with or without underscores (ut_io_08, lg01)."""
    return re.compile(r"(?<![a-z0-9])" + "_?".join(test_id.lower().split("-")) + r"(?![0-9])")


@cache
def functions(path: Path) -> dict[str, tuple[int, str]]:
    """Return function name -> (def line, source text) for every function in a test file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    out = {}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            out[node.name] = (node.lineno, ast.get_source_segment(text, node) or "")
    return out


def mentions(test_id: str, text: str) -> bool:
    """Return True when text names the ID as UT-GEO-12, UT_GEO_12 or ut_geo_12."""
    parts = test_id.split("-")
    return any(sep.join(parts) in text for sep in ("-", "_")) or bool(id_pattern(test_id).search(text.lower()))


def cause_b_nodes(req_id: str) -> set[str]:
    """Node ids that the V3-01 cause-B rulings cite for a planned ID of the row."""
    spec = importlib.util.spec_from_file_location("v3_01_rulings", RULINGS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {n for (req, _), (*_, nodes) in module.CAUSE_B_RULINGS.items() if req == req_id for n in nodes}


def union(records, req_id: str, planned: tuple[str, ...]):
    """File -> sorted (def line, test name, flags) for the tests that carry req_id or name a planned ID."""
    found_b = cause_b_nodes(req_id)
    patterns = [id_pattern(t) for t in planned]
    out: dict[str, set[tuple[int, str, str]]] = defaultdict(set)
    for record in records:
        path, _, name = record["nodeid"].partition("::")
        leaf = name.split("::")[-1].split("[")[0]
        line, source = functions(REPO / path).get(leaf, (0, ""))
        marked = req_id in record["req"]
        named = any(p.search(leaf.lower()) for p in patterns)
        cited = any(mentions(t, source) for t in planned)
        found = record["nodeid"].split("[")[0] in found_b
        if marked or named or cited or found:
            flags = "".join(f for f, on in (("m", marked), ("i", named), ("d", cited), ("b", found)) if on)
            out[path].add((line, leaf, flags))
    return {path: sorted(tests) for path, tests in sorted(out.items())}


def main(argv: list[str]) -> int:
    """Print the reading list of each requested row."""
    records = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    rows = must_f_rows()
    wanted = argv[1:] or list(rows)
    for req_id in wanted:
        acceptance, planned = rows[req_id]
        files = union(records, req_id, planned)
        count = sum(len(t) for t in files.values())
        print(f"## {req_id}: {count} test functions in {len(files)} files; planned {', '.join(planned)}")
        print(f"Acceptance: {acceptance}")
        for path, tests in files.items():
            print(f"  {path}")
            for line, name, flags in tests:
                print(f"    l.{line} {name} [{flags}]")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
