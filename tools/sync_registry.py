"""Copy the equation and evidence registries into resources/evidence and record their SHA-256 (REQ-T-04).

Usage, from anywhere::

    python tools/sync_registry.py           # write both copies and the manifest
    python tools/sync_registry.py --check   # exit 1 when a copy or the manifest differs from its source

The equation registry is copied byte for byte. The evidence register ships only its `phase2_scope` entries and the
documents they cite: the out-of-scope entries are the KiCad evidence that D-009 removed, and MT-07 forbids KiCad text
in shipped files. Nothing is edited by hand: Agent 2 owns the equation registry, Agent 5 the evidence register.
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DESTINATION = REPO / "resources" / "evidence"
MANIFEST = DESTINATION / "manifest.v1.json"


def verbatim(source: bytes) -> bytes:
    """Return the source unchanged."""
    return source


def phase2_scope(source: bytes) -> bytes:
    """Keep the entries Agent 5 marks `phase2_scope` and the documents those entries cite."""
    register = json.loads(source)
    entries = [e for e in register["entries"] if e["phase2_scope"]]
    cited = {d for e in entries for d in (*e["documents"], e["source"]["document"])}
    register["entries"] = entries
    register["documents"] = [d for d in register["documents"] if d["id"] in cited]
    return (json.dumps(register, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


SOURCES: dict[str, tuple[Path, Callable[[bytes], bytes]]] = {
    "equations.v1.json": (REPO / "docs" / "phase2" / "engineering" / "equation_registry.json", verbatim),
    "evidence.v1.json": (REPO / "docs" / "phase2" / "evidence" / "evidence_register.json", phase2_scope),
}


def sha256_of(data: bytes) -> str:
    """Return the hex SHA-256 of some bytes."""
    return hashlib.sha256(data).hexdigest()


def expected_copies() -> dict[str, bytes]:
    """Return the bytes each copy must hold, derived from the current sources."""
    return {name: transform(source.read_bytes()) for name, (source, transform) in SOURCES.items()}


def manifest_text(copies: dict[str, bytes]) -> str:
    """Return the manifest for the given copies: source path, filter and both hashes per file."""
    files = {
        name: {
            "source": source.relative_to(REPO).as_posix(),
            "filter": transform.__name__,
            "source_sha256": sha256_of(source.read_bytes()),
            "copy_sha256": sha256_of(copies[name]),
        }
        for name, (source, transform) in SOURCES.items()
    }
    return json.dumps({"schema": "embodic registry manifest v1", "files": files}, indent=1) + "\n"


def drift() -> list[str]:
    """Return one line per copy or manifest that differs from what the sources give."""
    copies = expected_copies()
    problems = []
    for name, data in copies.items():
        copy = DESTINATION / name
        if not copy.is_file():
            problems.append(f"{name}: missing")
        elif copy.read_bytes() != data:
            problems.append(f"{name}: differs from {SOURCES[name][0].relative_to(REPO)}")
    if not MANIFEST.is_file() or MANIFEST.read_text(encoding="utf-8") != manifest_text(copies):
        problems.append(f"{MANIFEST.name}: missing or stale")
    return problems


def sync() -> None:
    """Write every copy and the manifest; running it twice changes nothing."""
    DESTINATION.mkdir(parents=True, exist_ok=True)
    copies = expected_copies()
    for name, data in copies.items():
        (DESTINATION / name).write_bytes(data)
    MANIFEST.write_text(manifest_text(copies), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Sync, or with --check report drift; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift instead of writing")
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
