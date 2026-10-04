"""Run the gates of one CI profile and print a summary; the same command runs locally and in GitHub Actions.

Usage, from anywhere, inside the project's virtual environment::

    python tools/ci.py --profile commit     # every commit: lint, types, contracts, fast tests, trace matrix
    python tools/ci.py --profile nightly    # adds slow tests and the long Hypothesis profile
    python tools/ci.py --profile release    # adds performance and packaging tests

Every gate runs even after an earlier one fails, so one run shows every problem. Exit code 0 only when all pass.
"""

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD = REPO / "build"
RELEASE_ONLY_TEST_DIRS = ("tests/performance", "tests/packaging")


@dataclass(frozen=True)
class Profile:
    """What separates the profiles: which tests run and how hard Hypothesis searches."""

    marker_expression: str
    hypothesis_profile: str
    ignored_test_dirs: tuple[str, ...]


PROFILES = {
    "commit": Profile("not slow and not manual", "commit", RELEASE_ONLY_TEST_DIRS),
    "nightly": Profile("not manual", "nightly", RELEASE_ONLY_TEST_DIRS),
    "release": Profile("not manual", "nightly", ()),
}


@dataclass(frozen=True)
class Gate:
    """One command; it passes when it exits 0."""

    name: str
    argv: tuple[str, ...]
    env: dict[str, str] = field(default_factory=dict)


def gates_for(profile: Profile) -> list[Gate]:
    """Return the gates of a profile in run order."""
    python = sys.executable
    req_report = BUILD / "req_report.json"
    pytest_argv = [python, "-m", "pytest", "-p", "no:cacheprovider", "-m", profile.marker_expression]
    pytest_argv += [f"--ignore={d}" for d in profile.ignored_test_dirs]
    pytest_argv += [f"--req-report={req_report}"]
    lint_imports = "import sys; from importlinter.cli import lint_imports_command; sys.exit(lint_imports_command())"
    return [
        Gate("ruff check (MT-03)", (python, "-m", "ruff", "check", ".")),
        Gate("ruff format (MT-03)", (python, "-m", "ruff", "format", "--check", ".")),
        Gate("import contracts C1-C4 (MT-01)", (python, "-c", lint_imports)),
        Gate("mypy strict (MT-02)", (python, "-m", "mypy")),
        Gate("pytest", tuple(pytest_argv), {"EMBODIC_HYPOTHESIS_PROFILE": profile.hypothesis_profile}),
        Gate(
            "trace matrix (TR-01, TR-02)",
            (
                python,
                str(REPO / "tools" / "trace_matrix.py"),
                f"--report={req_report}",
                f"--out={BUILD / 'trace_matrix.md'}",
            ),
        ),
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
    args = parser.parse_args(argv)

    results = [(gate.name, *run_gate(gate)) for gate in gates_for(PROFILES[args.profile])]
    print(f"\n=== summary: profile {args.profile}")
    for name, passed, seconds in results:
        print(f"{'PASS' if passed else 'FAIL'}  {seconds:6.1f} s  {name}")
    failed = [name for name, passed, _ in results if not passed]
    print(f"{len(results) - len(failed)} of {len(results)} gates passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
