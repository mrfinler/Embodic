"""PF baseline collector: each PF test adds its case; a release run with --record-baseline writes baseline.json."""

import datetime as dt
import json
import os
import platform
import subprocess
from pathlib import Path

import numpy
import pytest

import embodic

REPO = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "baseline.json"


def cpu_model() -> str:
    """Return the CPU model string of /proc/cpuinfo, or platform.processor() where that file does not exist."""
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def memory_gib() -> float | None:
    """Return the total memory from /proc/meminfo in GiB, or None where that file does not exist."""
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 2**20, 2)
    except OSError:
        pass
    return None


def machine() -> dict[str, object]:
    """Return the machine record of package_layout.md section 5.2: no host name, user name or path."""
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu_model(),
        "cpu_count": os.cpu_count(),
        "memory_gib": memory_gib(),
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        # The container is shared; a high load at the start explains slow numbers better than the code does.
        "load_average_1m_at_start": round(os.getloadavg()[0], 2) if hasattr(os, "getloadavg") else None,
    }


@pytest.fixture(scope="session")
def baseline_cases():
    """Collect the cases of this run and write baseline.json at the end when EMBODIC_RECORD_BASELINE is set."""
    cases: dict[str, object] = {}
    started = machine()
    yield cases
    if os.environ.get("EMBODIC_RECORD_BASELINE") != "1" or not cases:
        return
    commit = subprocess.run(("git", "rev-parse", "HEAD"), cwd=REPO, capture_output=True, text=True, check=False)
    document = {
        "format": "embodic.pf-baseline",
        "format_version": 1,
        "embodic_version": embodic.__version__,
        "git_commit": commit.stdout.strip(),
        "recorded_utc": f"{dt.datetime.now(dt.UTC):%Y-%m-%dT%H:%M:%SZ}",
        "machine": started,
        "cases": dict(sorted(cases.items())),
    }
    BASELINE.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
