"""Copy the equation and evidence registries into resources/evidence and record their SHA-256 (REQ-T-04).

Usage, from anywhere (the example step needs embodic importable, for example ``PYTHONPATH=src``)::

    python tools/sync_registry.py           # write both copies and the manifest, then regenerate the examples
    python tools/sync_registry.py --check   # exit 1 when a copy, the manifest or an example differs from its source

The equation registry is copied byte for byte. The evidence register ships only its `phase2_scope` entries and the
documents they cite: the out-of-scope entries are the KiCad evidence that D-009 removed, and MT-07 forbids KiCad text
in shipped files. Nothing is edited by hand: Agent 2 owns the equation registry, Agent 5 the evidence register.
Every text file is written with LF line ends, so the bytes are the same on Windows (DEF-W-09).

Every packaged example file carries `registry_version` (REQ-T-07, interfaces.md 9.1), which is built from the hashes
of the two copies. A registry change therefore changes the bytes of all examples, and this tool rewrites them with
the example builders under tests/ (D-056b).
"""

import argparse
import hashlib
import json
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DESTINATION = REPO / "resources" / "evidence"
MANIFEST_NAME = "manifest.v1.json"
EXAMPLES_DIR = REPO / "resources" / "examples"


def manifest_path() -> Path:
    """Return the manifest inside the destination in force now, so redirecting the destination redirects it too."""
    return DESTINATION / MANIFEST_NAME


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


def expected_examples(copies: dict[str, bytes]) -> dict[str, bytes]:
    """Return the bytes of each example file once the registry copies are `copies`: file name -> content.

    The registry version is read back from the copies by the loader that the program uses, so the format of the
    version string lives in one place. The builders write into a scratch folder and the packaged files stay as they are.
    """
    if str(REPO) not in sys.path:  # the builders import `tests.unit...`; a script run puts tools/ first, not the root
        sys.path.insert(0, str(REPO))
    from tests.unit.embodic_io.project.make_examples import write_examples
    from tests.unit.generators.serpentine.make_example import write_example as write_serpentine
    from tests.unit.generators.wave.make_example import write_example as write_wave

    from embodic.results import load_registry

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        evidence = root / "evidence"
        evidence.mkdir()
        for name, data in copies.items():
            (evidence / name).write_bytes(data)
        (evidence / MANIFEST_NAME).write_text(manifest_text(copies), encoding="utf-8", newline="\n")
        version = load_registry(root).version
        folder = root / "examples"
        folder.mkdir()
        written = [
            *write_examples(folder, registry_version=version),
            write_serpentine(folder, registry_version=version),
            write_wave(folder, registry_version=version),
        ]
        return {path.name: path.read_bytes() for path in written}


def example_drift(examples: dict[str, bytes]) -> list[str]:
    """Return one line per example file that is missing, differs from the builder output or has no builder."""
    problems = []
    for name, data in examples.items():
        packaged = EXAMPLES_DIR / name
        if not packaged.is_file():
            problems.append(f"{name}: missing")
        elif packaged.read_bytes() != data:
            problems.append(f"{name}: differs from the generator output")
    problems += [
        f"{path.name}: no builder writes it"
        for path in sorted(EXAMPLES_DIR.glob("*.embodic.json"))
        if path.name not in examples
    ]
    return problems


def drift() -> list[str]:
    """Return one line per copy, manifest or example that differs from what the sources give."""
    copies = expected_copies()
    problems = []
    for name, data in copies.items():
        copy = DESTINATION / name
        if not copy.is_file():
            problems.append(f"{name}: missing")
        elif copy.read_bytes() != data:
            problems.append(f"{name}: differs from {SOURCES[name][0].relative_to(REPO)}")
    manifest = manifest_path()
    if not manifest.is_file() or manifest.read_bytes() != manifest_text(copies).encode("utf-8"):
        problems.append(f"{MANIFEST_NAME}: missing or stale")
    return problems + example_drift(expected_examples(copies))


def sync() -> list[str]:
    """Write every copy, the manifest and each example whose bytes change; running it twice changes nothing.

    Returns the names of the example files that were rewritten.
    """
    DESTINATION.mkdir(parents=True, exist_ok=True)
    copies = expected_copies()
    for name, data in copies.items():
        (DESTINATION / name).write_bytes(data)
    manifest_path().write_text(manifest_text(copies), encoding="utf-8", newline="\n")
    rewritten = []
    for name, data in expected_examples(copies).items():
        packaged = EXAMPLES_DIR / name
        if not packaged.is_file() or packaged.read_bytes() != data:
            packaged.write_bytes(data)
            rewritten.append(name)
    return rewritten


def main(argv: list[str] | None = None) -> int:
    """Sync, or with --check report drift; return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift instead of writing")
    args = parser.parse_args(argv)
    if not args.check:
        for name in sync():
            print(f"{name}: rewritten")
    problems = drift()
    for line in problems:
        print(line)
    print(f"{len(SOURCES)} registry files, {len(problems)} drifted")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
