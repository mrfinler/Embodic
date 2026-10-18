"""Turn the REQ report of one release gate run into the evidence of passing tests (interfaces.md section 3.1).

Usage, from the repository root after the release gate's pytest run::

    python tools/record_passed_tests.py --report build/req_report.json --profile release \
        --out resources/evidence/passed_tests.v1.json

Exit code 1, and nothing written, when the profile is not release, the report is missing or malformed, any test
failed, a test carries an eqt ID that the registry does not hold, or a `verified` equation has a linked test that did
not pass (REQ-T-05: the badge would read `not tested`). The message names each such equation with the registry test
IDs of it that passed in the run.
"""

import argparse
import dataclasses
import datetime as dt
import json
import os
import platform
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy

import embodic
from embodic.results.registry import PASSED_TESTS_FORMAT, Registry, load_registry, package_source_sha256
from embodic.results.status import Status

REPO = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True, kw_only=True)
class ReportRecord:
    """One test of the REQ report that tests/conftest.py writes."""

    nodeid: str
    outcome: str  # "passed", "failed", "skipped" or "not run"
    eqt: tuple[str, ...]


def parse_report(document: object) -> tuple[ReportRecord, ...]:
    """Read the report; a record without "eqt" (written before the markers existed) carries no registry test."""
    if not isinstance(document, list):
        raise ValueError("the REQ report is not a JSON list")
    return tuple(
        ReportRecord(nodeid=record["nodeid"], outcome=record["outcome"], eqt=tuple(record.get("eqt", ())))
        for record in document
    )


def passed_registry_tests(
    records: Sequence[ReportRecord], registry_test_ids: frozenset[str]
) -> tuple[frozenset[str], Mapping[str, tuple[str, ...]]]:
    """Return the registry test IDs that passed and, for each, the node IDs that carried it.

    An ID passes when at least one record carries it and every record that carries it passed. Raises ValueError for
    an ID that registry_test_ids does not hold, because a typo would otherwise never match and hide.
    """
    carriers: dict[str, list[ReportRecord]] = {}
    for record in records:
        for test_id in record.eqt:
            if test_id not in registry_test_ids:
                raise ValueError(f"{record.nodeid} carries {test_id!r}, which the registry does not link")
            carriers.setdefault(test_id, []).append(record)
    realised_by = {
        test_id: tuple(sorted(r.nodeid for r in carried))
        for test_id, carried in sorted(carriers.items())
        if all(r.outcome == "passed" for r in carried)
    }
    return frozenset(realised_by), realised_by


def evidence_document(
    realised_by: Mapping[str, tuple[str, ...]],
    *,
    registry: Registry,
    source_sha256: str,
    git_commit: str,
    git_dirty: bool,
    generated: dt.datetime,
) -> dict[str, object]:
    """Return the evidence file's content: the keys of interfaces.md section 3.1, nothing that names the host."""
    stamp = generated.astimezone(dt.UTC)
    return {
        "build_id": f"{embodic.__version__}+g{git_commit[:12]}.{stamp:%Y%m%dT%H%M%SZ}",
        "embodic_version": embodic.__version__,
        "format": PASSED_TESTS_FORMAT,
        "format_version": 1,
        "gate_profile": "release",
        "generated_utc": f"{stamp:%Y-%m-%dT%H:%M:%SZ}",
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "numpy": numpy.__version__,
        "passed_tests": sorted(realised_by),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "realised_by": {test_id: list(nodes) for test_id, nodes in sorted(realised_by.items())},
        "registry_version": registry.version,
        "source_sha256": source_sha256,
    }


def _git(*args: str) -> str:
    return subprocess.run(("git", *args), cwd=REPO, capture_output=True, text=True, check=True).stdout


def _write_atomically(path: Path, text: str) -> None:
    """Replace the file in one step, so a crash never leaves half a file for load_registry to read."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(text, encoding="utf-8", newline="\n")
    os.replace(partial, path)


def _refuse(message: str) -> int:
    print(f"record_passed_tests: {message}; no evidence written", file=sys.stderr)
    return 1


def record_main(argv: Sequence[str] | None = None) -> int:
    """Write the evidence file of one green release run, or refuse with exit code 1 and write nothing."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.profile != "release":
        return _refuse(f"profile {args.profile!r} is not release")
    try:
        records = parse_report(json.loads(args.report.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        return _refuse(f"cannot read the report {args.report}: {error}")
    failed = [r.nodeid for r in records if r.outcome == "failed"]
    if failed:
        return _refuse(f"{len(failed)} tests failed, first {failed[0]}")
    registry = load_registry()
    registry_test_ids = frozenset(t for entry in registry.equations.values() for t in entry.tests)
    try:
        passed, realised_by = passed_registry_tests(records, registry_test_ids)
    except ValueError as error:
        return _refuse(str(error))
    with_evidence = dataclasses.replace(registry, passed_tests=passed)
    unproven = [
        f"{eq_id} (passed: {', '.join(t for t in entry.tests if t in passed) or 'none'})"
        for eq_id, entry in registry.equations.items()
        if entry.status is Status.VERIFIED and not with_evidence.tests_passed(eq_id)
    ]
    if unproven:
        return _refuse(f"verified equations with a linked test that did not pass in this build: {', '.join(unproven)}")
    source_sha256 = package_source_sha256(Path(embodic.__file__).resolve().parent)
    if source_sha256 is None:
        return _refuse("the embodic package holds no .py file to hash")
    try:
        git_commit = _git("rev-parse", "HEAD").strip()
        git_dirty = bool(_git("status", "--porcelain").strip())
    except (OSError, subprocess.CalledProcessError) as error:
        return _refuse(f"git is unavailable: {error}")

    document = evidence_document(
        realised_by,
        registry=registry,
        source_sha256=source_sha256,
        git_commit=git_commit,
        git_dirty=git_dirty,
        generated=dt.datetime.now(dt.UTC),
    )
    _write_atomically(args.out, json.dumps(document, indent=1, sort_keys=True) + "\n")
    uncarried = len(registry_test_ids - {t for r in records for t in r.eqt})
    print(
        f"{len(passed)} of {len(registry_test_ids)} registry test IDs passed; {uncarried} carried by no test; "
        f"wrote {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(record_main())
