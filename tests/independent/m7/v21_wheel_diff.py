"""D-061d for a record made on a wheel: which members differ between the wheel it names and the release wheel (U-V21).

    python3 -I tests/independent/m7/v21_wheel_diff.py <wheel the record names> <release wheel>

`git diff` between two commits cannot see a build product such as the evidence file
`embodic/_resources/evidence/passed_tests.v1.json`, which `tools/record_passed_tests.py` writes into each wheel. This
script prints each wheel's SHA-256, the members only one wheel has, every member whose bytes differ, and for the
evidence file the keys whose values differ. Exit 0 when the wheels have the same members, 1 otherwise.
"""

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

EVIDENCE = "embodic/_resources/evidence/passed_tests.v1.json"


def main(argv: list[str] | None = None) -> int:
    """Print the member and evidence differences of two wheels."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("named", type=Path)
    parser.add_argument("release", type=Path)
    args = parser.parse_args(argv)
    for wheel in (args.named, args.release):
        print(f"{hashlib.sha256(wheel.read_bytes()).hexdigest()}  {wheel}")
    with zipfile.ZipFile(args.named) as a, zipfile.ZipFile(args.release) as b:
        names_a, names_b = set(a.namelist()), set(b.namelist())
        only = sorted(names_a ^ names_b)
        common = sorted(names_a & names_b)
        differ = [n for n in common if a.read(n) != b.read(n)]
        print(f"members: {len(names_a)} and {len(names_b)}; only in one: {only or 'none'}")
        print(f"members with other bytes: {len(differ)} of {len(common)}")
        for name in differ:
            print(f"  {name}")
        if EVIDENCE in differ:
            ev_a, ev_b = json.loads(a.read(EVIDENCE)), json.loads(b.read(EVIDENCE))
            for key in sorted(set(ev_a) | set(ev_b)):
                if ev_a.get(key) != ev_b.get(key):
                    print(f"  evidence {key}: {ev_a.get(key)!r} -> {ev_b.get(key)!r}")
            same = sorted(k for k in set(ev_a) & set(ev_b) if ev_a[k] == ev_b[k])
            print(f"  evidence keys equal: {', '.join(same)}")
    return 1 if only else 0


if __name__ == "__main__":
    sys.exit(main())
