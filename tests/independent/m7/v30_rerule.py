"""U-V30: check and pin the cites of v3_01_rulings_v30.py on release 0.0.6 (2bfca49).

    python3 tests/independent/m7/v30_rerule.py            # every test cite ran with the row's marker and passed
    python3 tests/independent/m7/v30_rerule.py --write    # also write records/V3-01_pins_2bfca49_v30.json

The records are those of Fable's 0.0.6 release gate as req_audit.py reads them. A test cite matches the records whose
node ID is that cite or that cite followed by a parameter list. A record cite must name a passed entry of the
manual-record index. The pins come from req_audit.py `cite_hash` on `git archive 2bfca49 tests`. Exit 1 when a cite
has no record, a record lacks the row's marker, a run did not pass, or a cited record is not a passed index entry.
"""

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def load(path: Path):
    """Import a module by path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load(REPO / "docs/phase3/verification/checks/req_audit.py")
V30 = load(HERE / "v3_01_rulings_v30.py")


def main(argv: list[str] | None = None) -> int:
    """Print one line per cite of each ruling; with --write, write the pins."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    records = AUDIT.read_reports(AUDIT.TARGETS["0.0.6"].reports)
    indexed = {e["record"] for e in json.loads(AUDIT.INDEX.read_text(encoding="utf-8")) if e["result"] == "passed"}
    bad, pins = 0, {}
    with tempfile.TemporaryDirectory() as tmp:
        tree = AUDIT.test_tree(V30.BASE, Path(tmp))
        for req, ruling in V30.RULINGS.items():
            print(f"{req}: {ruling.ruling}")
            for cite in ruling.cites:
                digest = AUDIT.cite_hash(cite, tree)
                pins.setdefault(req, {})[cite] = digest
                if cite.startswith("record:"):
                    ok = cite.removeprefix("record:") in indexed and digest != "missing"
                    print(f"  {'ok' if ok else 'BAD'} passed index entry {digest[:12]} {cite}")
                else:
                    runs = [r for r in records if r["nodeid"] == cite or r["nodeid"].startswith(cite + "[")]
                    unmarked = [r["nodeid"] for r in runs if req not in r["req"]]
                    outcomes = sorted({r["outcome"] for r in runs})
                    ok = bool(runs) and not unmarked and outcomes == ["passed"] and digest != "missing"
                    print(
                        f"  {'ok' if ok else 'BAD'} {len(runs)} run(s) {outcomes} {digest[:12]} {cite.split('::')[-1]}"
                    )
                bad += not ok
    if args.write and not bad:
        V30.PIN_FILE.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {V30.PIN_FILE.relative_to(REPO)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
