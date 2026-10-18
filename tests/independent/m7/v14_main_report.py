"""Build one REQ report of main from a commit-gate report of an earlier commit and Agent 4's reruns (U-V14).

    python3 tests/independent/m7/v14_main_report.py --gate G.json --base 5099401 --collected C.json \
        --rerun R.json [--rerun R2.json ...] --target c0f4894 --out docs/phase3/verification/inputs/X.json.gz

C.json is a `pytest --collect-only -m "not manual" --ignore=tests/packaging/evidence --req-report` of the target, so
the node IDs and the REQ, EQ and EQT markers are the target's own. Each collected test takes its outcome from the first
rerun report that holds it; otherwise from the gate report when the test file is unchanged between base and target
(src, resources, tools, pyproject.toml and requirements must be unchanged, or the script refuses); otherwise it stays
`not run`. The summary line counts each source.
"""

import argparse
import gzip
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def changed_files(base: str, target: str, *paths: str) -> set[str]:
    """Return the repository paths that differ between two commits under the given paths."""
    argv = ["git", "-C", str(REPO), "diff", "--name-only", base, target, "--", *paths]
    return set(subprocess.run(argv, capture_output=True, text=True, check=True).stdout.split())


def main(argv: list[str] | None = None) -> int:
    """Write the merged report and print where each outcome came from."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--collected", type=Path, required=True)
    parser.add_argument("--rerun", type=Path, action="append", default=[])
    parser.add_argument("--target", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if changed_files(args.base, args.target, "src", "resources", "tools", "pyproject.toml", "requirements"):
        print(f"product files differ between {args.base} and {args.target}: the gate report does not stand for it")
        return 1
    changed = changed_files(args.base, args.target, "tests")
    gate = {r["nodeid"]: r["outcome"] for r in json.loads(args.gate.read_text(encoding="utf-8"))}
    reruns = [{r["nodeid"]: r["outcome"] for r in json.loads(p.read_text(encoding="utf-8"))} for p in args.rerun]
    merged, source = [], Counter()
    for record in json.loads(args.collected.read_text(encoding="utf-8")):
        node = record["nodeid"]
        rerun = next((run[node] for run in reruns if node in run), None)
        if rerun is not None:
            outcome, origin = rerun, "rerun"
        elif node in gate and node.split("::")[0] not in changed:
            outcome, origin = gate[node], "gate"
        else:
            outcome, origin = "not run", "not run"
        merged.append({**record, "outcome": outcome})
        source[origin] += 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(merged, indent=1, sort_keys=True).encode("utf-8")
    args.out.write_bytes(gzip.compress(payload, mtime=0))
    outcomes = Counter(r["outcome"] for r in merged)
    print(f"{len(merged)} tests; outcome from {dict(source)}; outcomes {dict(outcomes)}; wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
