"""U-V30: index the Windows records of release 0.0.6 and name the platform of the records the NEEDS rule reads.

    python3 tests/independent/m7/v30_index.py            # print the index this unit writes
    python3 tests/independent/m7/v30_index.py --write    # write docs/phase3/verification/manual_records.json

The platform is the first item of the note in `embodic_version`, before the first comma or semicolon, as
`req_audit.py` reads it (`platform_of`). The script is idempotent: it starts from the seven entries of U-V29's index
(8e4159d), restamps the platform of the Linux PK-06 and the OR-11 and OR-12 entries, and appends the Windows entries of
D-098a, D-099a, D-100a and D-100c. Each Windows entry is `verified` by reading the Fable record it names and the
decision row in its note; none of them rests on a laptop log (order 6).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INDEX = REPO / "docs/phase3/verification/manual_records.json"
BASE = "8e4159d"
NOTE = "docs/phase3/verification/manual_records_0.0.6_windows.md"
W2 = "docs/phase3/fable/windows_campaign_w2.md"
PK06 = "docs/phase3/fable/PK-06_windows_0.0.6.md"
WHEEL = "release wheel fdb89189 of tag v0.0.6 on 2bfca49"
RESTAMP = {
    ("PK-06", "tests/independent/m5/records/PK-06_walkthrough_2bfca49.md"): "0.0.6 (Linux container, ",
    ("OR-11", "tests/independent/m6/records/OR-11_OR-12_2bfca49.md"): "0.0.6 (GetDP FEA of c25d8a9 on the Linux "
    "container against the ",
    ("OR-12", "tests/independent/m6/records/OR-11_OR-12_2bfca49.md"): "0.0.6 (GetDP FEA of c25d8a9 on the Linux "
    "container against the ",
}


def windows(what: str, rows: str) -> str:
    """Return the embodic_version of a Windows record: the version, the platform first, then the run and the rows."""
    return f"0.0.6 (Windows laptop, {what}, Fable; {rows}, {NOTE})"


ADDED = [
    ("REQ-N-04", "PK-04", W2, windows(f"{WHEEL} against U-V29's Linux reference", "D-098a"), "passed", None),
    (
        "REQ-N-06",
        "PK-05",
        W2,
        windows("bundle built from checkout 6ac95ac in the release run", "D-099a"),
        "passed",
        None,
    ),
    ("REQ-N-07", "PK-06", PK06, windows(f"{WHEEL}, runs 11 and 12", "D-100a"), "passed", None),
    ("REQ-N-05", "PK-02", PK06, windows(f"{WHEEL} in a clean venv, runs 11 and 12", "D-100a"), "passed", None),
    ("REQ-N-06", "PK-11", PK06, windows(f"{WHEEL} in a clean venv, run 11", "D-100a"), "passed", None),
    (
        "REQ-N-05",
        "PK-01",
        W2,
        windows("commit profile on checkout 6ac95ac, W7, 5 of 6", "D-098c, D-100c"),
        "failed",
        "D-100",
    ),
    (
        "REQ-N-05",
        "PK-02",
        W2,
        windows("release profile on checkout 6ac95ac, W8, 6 of 8", "D-099a, D-100c"),
        "failed",
        "D-100",
    ),
    (
        "REQ-N-06",
        "PK-11",
        W2,
        windows("release profile on checkout 6ac95ac, W8, 6 of 8", "D-099a, D-100c"),
        "failed",
        "D-100",
    ),
]


def build() -> list[dict]:
    """Return U-V29's index with the restamped platforms and the Windows entries appended."""
    base = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{BASE}:{INDEX.relative_to(REPO).as_posix()}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    entries = json.loads(base)
    for entry in entries:
        head = RESTAMP.get((entry["test_id"], entry["record"]))
        if head:
            entry["embodic_version"] = head + entry["embodic_version"].removeprefix("0.0.6 (")
    for req, test_id, record, version, result, accepted in ADDED:
        entry = {"req": req, "test_id": test_id, "record": record, "embodic_version": version, "result": result}
        entries.append({**entry, "accepted": accepted} if accepted else entry)
    return entries


def main(argv: list[str] | None = None) -> int:
    """Print the index, or write it."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="write manual_records.json")
    args = parser.parse_args(argv)
    text = json.dumps(build(), indent=1) + "\n"
    if args.write:
        INDEX.write_text(text, encoding="utf-8")
        print(f"wrote {INDEX.relative_to(REPO)}: {len(json.loads(text))} entries")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
