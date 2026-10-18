"""Run the gates of one CI profile and print a summary; the same command runs locally and in GitHub Actions.

Usage, from anywhere, inside the project's virtual environment::

    python tools/ci.py --profile commit     # every commit: lint, types, contracts, fast tests, trace matrix
    python tools/ci.py --profile nightly    # adds slow tests and the long Hypothesis profile
    python tools/ci.py --profile release    # adds the bundle build, performance and packaging tests, TR-01, then the
                                            # evidence and wheel

Every gate runs even after an earlier one fails, so one run shows every problem. Exit code 0 only when all pass.
The release profile deletes the evidence of passing tests and the previous bundle folder before its first gate. It
builds the PyInstaller one-folder bundle before pytest, and tests/bundle fails instead of skipping when the folder is
missing (REQ-N-06, D-068). Only when every gate passed does it record the evidence (interfaces.md section 3.1), build
the wheel and check the evidence inside it (PK-10).
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD = REPO / "build"
DIST = BUILD / "dist"
BUNDLE = BUILD / "bundle"  # tools/build_bundle.py writes the one-folder bundle to BUNDLE / "embodic"
REQ_REPORT = BUILD / "req_report.json"
EVIDENCE = REPO / "resources" / "evidence" / "passed_tests.v1.json"
MANUAL_RECORDS = REPO / "docs" / "phase3" / "verification" / "manual_records.json"
RELEASE_ONLY_TEST_DIRS = ("tests/performance", "tests/packaging")
EVIDENCE_TEST_DIR = "tests/packaging/evidence"  # PK-10 needs the evidence file, so it runs after the record step


@dataclass(frozen=True)
class Profile:
    """What separates the profiles: which tests run and how hard Hypothesis searches."""

    marker_expression: str
    hypothesis_profile: str
    ignored_test_dirs: tuple[str, ...]
    records_evidence: bool = False
    untested_through: str | None = None  # TR-01: the last milestone whose live must rows need a test or a manual record
    require_personal_tokens: bool = False  # LG-06 fails, not skips, when no personal-data token can be found
    builds_bundle: bool = False  # build the PyInstaller folder before pytest; tests/bundle fails, not skips, without it


PROFILES = {
    "commit": Profile("not slow and not manual", "commit", RELEASE_ONLY_TEST_DIRS),
    "nightly": Profile("not manual", "nightly", RELEASE_ONLY_TEST_DIRS),
    "release": Profile(
        "not manual",
        "nightly",
        (EVIDENCE_TEST_DIR,),
        records_evidence=True,
        untested_through="M5",
        require_personal_tokens=True,
        builds_bundle=True,
    ),
}


@dataclass(frozen=True)
class Gate:
    """One command; it passes when it exits 0."""

    name: str
    argv: tuple[str, ...]
    env: dict[str, str] = field(default_factory=dict)


def gates_for(profile: Profile, *, record_baseline: bool = False) -> list[Gate]:
    """Return the gates of a profile in run order."""
    python = sys.executable
    pytest_argv = [python, "-m", "pytest", "-p", "no:cacheprovider", "-m", profile.marker_expression]
    pytest_argv += [f"--ignore={d}" for d in profile.ignored_test_dirs]
    pytest_argv += [f"--req-report={REQ_REPORT}"]
    pytest_env = {"EMBODIC_HYPOTHESIS_PROFILE": profile.hypothesis_profile}
    if record_baseline:
        pytest_env["EMBODIC_RECORD_BASELINE"] = "1"
    if profile.require_personal_tokens:
        pytest_env["EMBODIC_REQUIRE_PERSONAL_TOKENS"] = "1"  # name read by tests/static/lg_scan.py
    if profile.builds_bundle:
        pytest_env["EMBODIC_REQUIRE_BUNDLE"] = "1"  # name read by tests/bundle/bundle_gate.py
    lint_imports = "import sys; from importlinter.cli import lint_imports_command; sys.exit(lint_imports_command())"
    trace_argv = [
        python,
        str(REPO / "tools" / "trace_matrix.py"),
        f"--report={REQ_REPORT}",
        f"--out={BUILD / 'trace_matrix.md'}",
    ]
    trace_name = "trace matrix (TR-02)"
    if profile.untested_through:
        trace_argv += [f"--fail-untested-through={profile.untested_through}", f"--manual-records={MANUAL_RECORDS}"]
        trace_name = "trace matrix (TR-01, TR-02)"
    gates = [
        Gate("ruff check (MT-03)", (python, "-m", "ruff", "check", ".")),
        Gate("ruff format (MT-03)", (python, "-m", "ruff", "format", "--check", ".")),
        Gate("import contracts C1-C4 (MT-01)", (python, "-c", lint_imports)),
        Gate("mypy strict (MT-02)", (python, "-m", "mypy")),
    ]
    if profile.builds_bundle:
        gates.append(Gate("bundle build (REQ-N-06)", (python, str(REPO / "tools" / "build_bundle.py"))))
    gates += [Gate("pytest", tuple(pytest_argv), pytest_env), Gate(trace_name, tuple(trace_argv))]
    return gates


def evidence_gates() -> list[Gate]:
    """Return the release steps that run, in order and each only after the previous passed, once every gate passed."""
    python = sys.executable
    record = (str(REPO / "tools" / "record_passed_tests.py"), f"--report={REQ_REPORT}", "--profile=release")
    return [
        Gate("passed-test evidence (TR-05)", (python, *record, f"--out={EVIDENCE}")),
        Gate("wheel build", (python, "-m", "pip", "wheel", "--no-build-isolation", "--no-deps", ".", "-w", str(DIST))),
        Gate("evidence in the wheel (PK-10)", (python, "-m", "pytest", "-p", "no:cacheprovider", EVIDENCE_TEST_DIR)),
    ]


def run_gate(gate: Gate) -> tuple[bool, float]:
    """Run one gate from the repository root with its output streamed; return (passed, seconds)."""
    print(f"\n=== {gate.name}: {' '.join(gate.argv)}", flush=True)
    started = time.perf_counter()
    completed = subprocess.run(gate.argv, cwd=REPO, env={**os.environ, **gate.env}, check=False)
    return completed.returncode == 0, time.perf_counter() - started


def main(argv: list[str] | None = None) -> int:
    """Run every gate of the chosen profile, print the summary table and return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profile", choices=sorted(PROFILES), default="commit")
    parser.add_argument(
        "--record-baseline", action="store_true", help="release only: rewrite tests/performance/baseline.json"
    )
    args = parser.parse_args(argv)
    profile = PROFILES[args.profile]
    if args.record_baseline and not profile.records_evidence:
        parser.error("--record-baseline needs --profile release")
    if profile.records_evidence:
        EVIDENCE.unlink(missing_ok=True)
        shutil.rmtree(DIST, ignore_errors=True)

    results = [(gate.name, *run_gate(gate)) for gate in gates_for(profile, record_baseline=args.record_baseline)]
    if profile.records_evidence and all(passed for _, passed, _ in results):
        for gate in evidence_gates():
            results.append((gate.name, *run_gate(gate)))
            if not results[-1][1]:
                break
    print(f"\n=== summary: profile {args.profile}")
    for name, passed, seconds in results:
        print(f"{'PASS' if passed else 'FAIL'}  {seconds:6.1f} s  {name}")
    failed = [name for name, passed, _ in results if not passed]
    print(f"{len(results) - len(failed)} of {len(results)} gates passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
