"""embodic.paths.resource_root() in the editable install and in a built wheel (package_layout.md section 1)."""

import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from embodic.paths import resource_root
from tests.packaging.support import CLEAN_ENV

REPO = Path(__file__).resolve().parents[3]


@pytest.mark.req("REQ-N-06")
def test_paths_resource_root_holds_icons_and_themes():
    """Catches a root that points at the package folder or a missing directory instead of the resources."""
    root = resource_root()
    assert (root / "icons" / "new.svg").is_file()
    assert (root / "themes").is_dir()


@pytest.mark.slow
@pytest.mark.req("REQ-N-06")
def test_paths_resource_root_in_built_wheel(tmp_path):
    """Catches a wheel that ships without resources/ (the force-include mapping) or a root that only works from src/.

    Builds the wheel with pip (hatchling from PyPI in an isolated build environment), installs it without
    dependencies into a fresh venv, and runs resource_root() there from a directory outside the repository.
    """
    wheel_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--quiet", "--wheel-dir", str(wheel_dir), str(REPO)],
        check=True,
        env=CLEAN_ENV,
    )
    (wheel,) = wheel_dir.glob("embodic-*.whl")
    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--no-deps", "--quiet", str(wheel)], check=True, env=CLEAN_ENV)
    probe = "import embodic.paths as p; r = p.resource_root(); print(r); print((r / 'icons' / 'new.svg').is_file())"
    result = subprocess.run(
        [str(python), "-c", probe], check=True, capture_output=True, text=True, cwd=tmp_path, env=CLEAN_ENV
    )
    root_line, icon_line = result.stdout.splitlines()
    assert Path(root_line).parts[-2:] == ("embodic", "_resources")
    assert REPO not in Path(root_line).parents
    assert icon_line == "True"
