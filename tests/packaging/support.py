"""Packaging helpers: wheel builds and clean virtual environments that install from the hashed lock file."""

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from embodic.results.registry import PASSED_TESTS_FILE

REPO = Path(__file__).resolve().parents[2]
LOCK = REPO / "requirements" / f"py3{sys.version_info.minor}.txt"
# PYTHONPATH pointing at src/ would make the venv import the working tree instead of the installed wheel.
CLEAN_ENV = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
BUILD_FILES = ("pyproject.toml", "README.md", "THIRD_PARTY_LICENSES.md", ".gitignore")
BUILD_FOLDERS = ("src", "resources")


def run(*argv: object, cwd: Path = REPO) -> str:
    """Run a command, fail the test with its output when it exits non-zero, and return stdout."""
    completed = subprocess.run(
        [str(a) for a in argv], cwd=cwd, env=CLEAN_ENV, capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, f"{argv} exited {completed.returncode}\n{completed.stdout}\n{completed.stderr}"
    return completed.stdout


def build_wheel(out_dir: Path) -> Path:
    """Build the wheel offline, the way package_layout.md section 5.2 does, and return its path.

    It builds from a copy of the build inputs without the evidence file a release run leaves in resources/evidence
    (D-045f). Only the release profile's own wheel carries that file, and PK-10 checks it there.
    """
    tree = out_dir / "tree"
    skip = shutil.ignore_patterns("__pycache__", PASSED_TESTS_FILE)
    for name in BUILD_FOLDERS:
        shutil.copytree(REPO / name, tree / name, ignore=skip)
    for name in BUILD_FILES:
        shutil.copy2(REPO / name, tree / name)
    run(sys.executable, "-m", "pip", "wheel", "--no-build-isolation", "--no-deps", "-q", ".", "-w", out_dir, cwd=tree)
    (wheel,) = out_dir.glob("embodic-*.whl")
    return wheel


def wheel_members(wheel: Path) -> dict[str, bytes]:
    """Return every member of a wheel with its bytes."""
    with zipfile.ZipFile(wheel) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


class CleanVenv:
    """A virtual environment that holds only the runtime lock file's packages and one embodic wheel."""

    def __init__(self, folder: Path, wheel: Path) -> None:
        run(sys.executable, "-m", "venv", folder)
        self.python = folder / ("Scripts" if sys.platform == "win32" else "bin") / "python"
        run(self.python, "-m", "pip", "install", "-q", "--require-hashes", "-r", LOCK)
        run(self.python, "-m", "pip", "install", "-q", "--no-deps", wheel)
        self.cli = self.python.parent / "embodic-cli"

    def evaluate(self, code: str) -> object:
        """Run Python code in the venv, outside the repository, and return the JSON it prints."""
        return json.loads(run(self.python, "-I", "-c", code, cwd=self.python.parent))

    def resource_root(self) -> Path:
        """Return the installed package's resource folder."""
        code = "import json; from embodic.paths import resource_root; print(json.dumps(str(resource_root())))"
        return Path(str(self.evaluate(code)))


# What `python -m venv` seeds before anything is installed; Python 3.11 adds setuptools, 3.12 and later do not.
VENV_SEED = ("pip", "setuptools")


def installed_distributions_code(value: str) -> str:
    """Return code that prints {normalised distribution name: value expression} for the venv's non-seed packages."""
    return (
        "import importlib.metadata as m, json, re; "
        "print(json.dumps({re.sub(r'[-_.]+', '-', d.metadata['Name']).lower(): " + value + " "
        f"for d in m.distributions() if d.metadata['Name'].lower() not in {VENV_SEED!r}}}))"
    )
