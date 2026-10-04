"""Copy the equation and evidence registries into resources/evidence and record their SHA-256 (REQ-T-04).

Usage, from anywhere::

    python tools/sync_registry.py           # copy both files byte for byte and rewrite the manifest
    python tools/sync_registry.py --check   # exit 1 when a copy or the manifest differs from its source

The copies are never edited by hand: Agent 2 owns the equation registry, Agent 5 the evidence register.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DESTINATION = REPO / "resources" / "evidence"
MANIFEST = DESTINATION / "manifest.v1.json"
SOURCES = {
    "equations.v1.json": REPO / "docs" / "phase2" / "engineering" / "equation_registry.json",
    "evidence.v1.json": REPO / "docs" / "phase2" / "evidence" / "evidence_register.json",
}


def sha256_of(path: Path) -> str:
    """Return the hex SHA-256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_text() -> str:
    """Return the manifest that matches the current sources."""
    files = {
        name: {"source": source.relative_to(REPO).as_posix(), "sha256": sha256_of(source)}
        for name, source in SOURCES.items()
    }
    return json.dumps({"schema": "embodic registry manifest v1", "files": files}, indent=1) + "\n"


def drift() -> list[str]:
    """Return one line per copy or manifest entry that differs from its source."""
    problems = []
    for name, source in SOURCES.items():
        copy = DESTINATION / name
        if not copy.is_file():
            problems.append(f"{name}: missing")
        elif sha256_of(copy) != sha256_of(source):
            problems.append(f"{name}: differs from {source.relative_to(REPO)}")
    if not MANIFEST.is_file() or MANIFEST.read_text(encoding="utf-8") != manifest_text():
        problems.append(f"{MANIFEST.name}: missing or stale")
    return problems


def sync() -> None:
    """Copy every source byte for byte and write the manifest; running it twice changes nothing."""
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for name, source in SOURCES.items():
        (DESTINATION / name).write_bytes(source.read_bytes())
    MANIFEST.write_text(manifest_text(), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Sync, or with --check report drift; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift instead of copying")
    args = parser.parse_args(argv)
    if not args.check:
        sync()
    problems = drift()
    for line in problems:
        print(line)
    print(f"{len(SOURCES)} registry files, {len(problems)} drifted")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
