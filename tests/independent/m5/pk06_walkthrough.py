"""PK-06 Linux walkthrough: run README.md / docs/install/INSTALL.md steps 1-6 in a new empty directory and time each.

Usage: python3.11 pk06_walkthrough.py --wheel W --lock L --workdir NEW_EMPTY_DIR --out run.json

Each step runs the guide's command verbatim in bash with the step-2 venv activated. The guide's expected text is
copied from INSTALL.md (base 1eb110d, identical to the release commit 5e74acc) and compared literally, so a
difference prints as the exact pair. PIP_CACHE_DIR points at a new empty folder so step 3 downloads like a first
install on a clean machine.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Step:
    """One guide step: its command, the guide's expected text and its timeout."""

    step_id: str
    guide_ref: str
    command: str
    expected: list[str]
    timeout_s: float = 900.0
    env_extra: dict[str, str] = field(default_factory=dict)
    in_criterion: bool = True


@dataclass
class StepResult:
    """What one step printed, its exit code and wall time."""

    step_id: str
    guide_ref: str
    command: str
    exit_code: int | None
    wall_s: float
    stdout: str
    stderr: str
    expected: list[str]
    missing_expected: list[str]
    load_before: str
    load_after: str
    in_criterion: bool


def loadavg() -> str:
    """Return /proc/loadavg as text."""
    return Path("/proc/loadavg").read_text().strip()


def run_step(step: Step, workdir: Path, env: dict[str, str], examples: str | None) -> StepResult:
    """Run one step in bash inside workdir, with the venv activated once it exists."""
    command = step.command.replace("<examples>", examples or "<examples>")
    activate = ". .venv/bin/activate && " if (workdir / ".venv" / "bin" / "activate").exists() else ""
    full_env = {**env, **step.env_extra}
    before = loadavg()
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            ["bash", "-c", activate + command],
            cwd=workdir,
            env=full_env,
            capture_output=True,
            text=True,
            timeout=step.timeout_s,
        )
        code, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        code = None
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    wall = time.monotonic() - t0
    combined = out + err
    missing = [line for line in step.expected if line not in combined]
    return StepResult(
        step.step_id,
        step.guide_ref,
        command,
        code,
        round(wall, 3),
        out,
        err,
        step.expected,
        missing,
        before,
        loadavg(),
        step.in_criterion,
    )


EXAMPLE = "<examples>/spiral_12c16p_default.embodic.json"

STEPS = [
    Step("1", "INSTALL.md §1", "python3.11 --version", ["Python 3.11."]),
    Step(
        "2",
        "INSTALL.md §2",
        "python3.11 -m venv .venv && . .venv/bin/activate && echo VIRTUAL_ENV=$VIRTUAL_ENV && command -v python",
        [],
    ),
    Step("3a", "INSTALL.md §3", "python -m pip install --require-hashes -r requirements/py311.txt", []),
    Step("3b", "INSTALL.md §3", "python -m pip install --no-deps embodic-0.0.1-py3-none-any.whl", []),
    Step(
        "3c",
        "INSTALL.md §3",
        "python -m pip list",
        ["embodic", "0.0.1", "numpy", "2.4.6", "PySide6_Essentials", "6.11.2", "shiboken6"],
    ),
    Step("4", "INSTALL.md §4", "embodic", [], timeout_s=30.0),
    Step(
        "4-offscreen",
        "INSTALL.md Troubleshooting on Linux (QT_QPA_PLATFORM=offscreen) + ui/app.py --smoke",
        "embodic --smoke",
        [],
        timeout_s=120.0,
        env_extra={"QT_QPA_PLATFORM": "offscreen"},
        in_criterion=False,
    ),
    Step(
        "5a",
        "INSTALL.md §5",
        "python -c \"from embodic.paths import resource_root; print(resource_root() / 'examples')\"",
        ["embodic/_resources/examples"],
    ),
    Step(
        "5b",
        "INSTALL.md §5",
        f"embodic-cli compute {EXAMPLE} --json outcome.json --timings",
        [
            "Design: Spiral, 12 coils, 16 poles",
            "Design hash: sha256:ac4fab5db06f9e8f733dc495080deeddfe0bcf58faa31ebb7ec841c1b27d9c09",
            "Topology: spiral, boards: 1",
            "Design rule check: passed",
            "Timings (s): validate",
        ],
    ),
    Step(
        "5c",
        "INSTALL.md §5",
        f"embodic-cli validate {EXAMPLE}",
        ["Valid: Spiral, 12 coils, 16 poles"],
        in_criterion=False,
    ),
    Step(
        "5d",
        "INSTALL.md §5",
        f"embodic-cli export {EXAMPLE} --format svg -o board.svg",
        ["Wrote board.svg"],
        in_criterion=False,
    ),
    Step(
        "6",
        "INSTALL.md §6 (guide: selftest not in this build); brief item 2 expects the summary",
        "embodic-cli selftest",
        ["45 tests: 45 passed, 0 failed"],
        timeout_s=600.0,
        in_criterion=False,
    ),
]


def main() -> int:
    """Prepare the empty folder, run every step, write the JSON record."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    workdir: Path = args.workdir
    workdir.mkdir(parents=True, exist_ok=False)
    (workdir / "requirements").mkdir()
    shutil.copy2(args.lock, workdir / "requirements" / "py311.txt")
    shutil.copy2(args.wheel, workdir / args.wheel.name)
    pip_cache = workdir.parent / (workdir.name + "-pip-cache")
    pip_cache.mkdir(exist_ok=False)

    env = {
        k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "DISPLAY", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM")
    }
    env["PIP_CACHE_DIR"] = str(pip_cache)
    env["PATH"] = ":".join(p for p in env["PATH"].split(":") if ".venv" not in p)

    results: list[StepResult] = []
    examples: str | None = None
    for step in STEPS:
        result = run_step(step, workdir, env, examples)
        if step.step_id == "5a" and result.exit_code == 0:
            examples = result.stdout.strip().splitlines()[-1]
        results.append(result)
        status = "ok" if result.exit_code == 0 and not result.missing_expected else "DIFF"
        print(f"[{result.step_id:>11}] {status:4} exit={result.exit_code} {result.wall_s:8.3f} s  {result.command}")
        for line in result.missing_expected:
            print(f"              expected text not found: {line!r}")

    criterion = [r for r in results if r.in_criterion]
    total = round(sum(r.wall_s for r in criterion), 3)
    record = {
        "workdir": str(workdir),
        "pip_cache_dir": str(pip_cache),
        "started_load": results[0].load_before,
        "steps": [asdict(r) for r in results],
        "total_to_first_computed_example_s": total,
        "criterion_steps": [r.step_id for r in criterion],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2))
    print(f"total to first computed example (steps {', '.join(r.step_id for r in criterion)}): {total:.3f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
