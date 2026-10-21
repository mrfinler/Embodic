"""U-V21: check and pin the cites of v3_01_rulings_v21.py on release 0.0.5 (42074f2).

    python3 tests/independent/m7/v21_rerule.py            # every cite ran with the row's marker and passed
    python3 tests/independent/m7/v21_rerule.py --write    # also write records/V3-01_pins_42074f2_v21.json

The records are those of Fable's 0.0.5 release gate as req_audit.py reads them (the main REQ report, with the latency
report's outcomes in place of `not run`), from docs/phase3/verification/inputs/. A cite `file::function` matches the
records whose node ID is that cite or that cite followed by a parameter list. The pins hash the function's source
segment on `git archive 42074f2 tests` with req_audit.py `cite_hash`. Exit 1 when a cite has no record, a record
lacks the row's marker, or one did not pass.
"""

import argparse
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
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
V21 = load(HERE / "v3_01_rulings_v21.py")


def main(argv: list[str] | None = None) -> int:
    """Print one line per cite of each `checks` ruling; with --write, write the pins."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    records = AUDIT.read_reports(AUDIT.TARGETS["0.0.5"].reports)
    tar = subprocess.run(["git", "-C", str(REPO), "archive", V21.BASE, "tests"], capture_output=True, check=True)
    bad, pins = 0, {}
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as archive:
            archive.extractall(tree, filter="data")
        for req, ruling in V21.RULINGS.items():
            print(f"{req}: {ruling.ruling}")
            for cite in ruling.cites:
                if cite.startswith("gate:"):
                    continue
                runs = [r for r in records if r["nodeid"] == cite or r["nodeid"].startswith(cite + "[")]
                unmarked = [r["nodeid"] for r in runs if req not in r["req"]]
                outcomes = sorted({r["outcome"] for r in runs})
                digest = AUDIT.cite_hash(cite, tree)
                ok = bool(runs) and not unmarked and outcomes == ["passed"] and digest != "missing"
                bad += not ok
                pins.setdefault(req, {})[cite] = digest
                print(f"  {'ok' if ok else 'BAD'} {len(runs)} run(s) {outcomes} {digest[:12]} {cite.split('::')[-1]}")
                for nodeid in unmarked:
                    print(f"    without {req}: {nodeid}")
    if args.write and not bad:
        V21.PIN_FILE.write_text(json.dumps(pins, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {V21.PIN_FILE.relative_to(REPO)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
