"""List, per requirement row, the union of tests that carry its REQ marker or name one of its planned test IDs.

    python -m pytest --collect-only -q --req-report /tmp/req_collect.json tests
    python3 tests/independent/m7/v3_01_union.py /tmp/req_collect.json REQ-N-02 REQ-T-03

A test belongs to a row when it carries the row's REQ marker, when its test name holds a planned ID (ut_res_02, lg01),
or when its file names a planned ID and the test carries the marker. Each line prints `file:line test-name [REQ ...]`,
with the line of the `def`, so a reader can open every test that the V3-01 union ruling (v3_01_rulings_ntl.py) must
cover.
"""

import ast
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AUDIT = REPO / "docs/phase3/verification/checks/req_audit.py"


def _audit():
    spec = importlib.util.spec_from_file_location("req_audit", AUDIT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def def_lines(path: Path) -> dict[str, int]:
    """Test function name -> line of its def, for module-level functions and methods."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name: n.lineno for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}


def union(row, records, sources) -> list[dict]:
    """Return the records that belong to the row, in node-id order."""
    audit = _audit()
    picked = []
    for record in records:
        name = record["nodeid"].split("::")[-1].split("[")[0].lower()
        file = record["nodeid"].split("::")[0]
        marked = row.req_id in record["req"]
        named = any(audit.id_pattern(t).search(name) for t in row.tests)
        cited = marked and any(audit.file_mentions(t, sources[file]) for t in row.tests)
        if marked or named or cited:
            picked.append(record)
    return picked


def main(argv: list[str]) -> int:
    """Print the union of every row named on the command line."""
    audit = _audit()
    records = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    rows = {r.req_id: r for r in audit.parse_requirements(audit.REQUIREMENTS.read_text(encoding="utf-8"))}
    files = {r["nodeid"].split("::")[0] for r in records}
    sources = {f: (REPO / f).read_text(encoding="utf-8", errors="replace") for f in files}
    lines_of = {}
    for req_id in argv[1:]:
        row = rows[req_id]
        picked = union(row, records, sources)
        print(f"## {req_id} planned {', '.join(row.tests)}: {len(picked)} tests")
        seen = set()
        for record in picked:
            file, *_, name = record["nodeid"].split("::")
            base = name.split("[")[0]
            if (file, base) in seen:
                continue
            seen.add((file, base))
            if file not in lines_of:
                lines_of[file] = def_lines(REPO / file)
            print(f"{file}:{lines_of[file].get(base, 0)} {base} {record['req']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
