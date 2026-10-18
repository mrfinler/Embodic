"""Smoke test of the PyInstaller one-folder bundle that `python tools/build_bundle.py` writes to build/bundle/embodic.

On Linux this is a smoke of the spec only; PK-05 counts only from the Windows folder (test_plan.md section 5.7).
Every test skips when the folder is absent, so the commit gate does not depend on a bundle build. The release profile
builds the folder first and sets EMBODIC_REQUIRE_BUNDLE=1, which turns each skip into a failure (bundle_gate.py).
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from tests.bundle import bundle_gate

from embodic.cli import main as cli_main
from embodic.results.registry import package_source_sha256
from embodic.selftest import SELFTESTS

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "build" / "bundle" / "embodic"
SUFFIX = ".exe" if sys.platform == "win32" else ""
FROZEN_CLI = FOLDER / f"embodic-cli{SUFFIX}"
FROZEN_GUI = FOLDER / f"embodic{SUFFIX}"
FROZEN_PACKAGE = FOLDER / "_internal" / "embodic"
EXAMPLE = Path("examples") / "spiral_12c16p_default.embodic.json"


@pytest.fixture(autouse=True)
def bundle_is_built() -> None:
    """Skip the test without a bundle, or fail it when the run requires one."""
    bundle_gate.require_bundle(FROZEN_CLI)


def run_frozen(executable: Path, *args: str | Path, timeout_s: float = 120.0) -> subprocess.CompletedProcess[str]:
    """Run a frozen executable and return the finished process with its output decoded as UTF-8."""
    command = [str(executable), *map(str, args)]
    return subprocess.run(command, capture_output=True, encoding="utf-8", timeout=timeout_s)


def without_export_time(svg: Path) -> str:
    """Return the SVG text with its generated_utc stamp blanked; the stamp is the export's wall-clock second."""
    return re.sub(r'generated_utc="[^"]*"', 'generated_utc=""', svg.read_text(encoding="utf-8"))


def design_hash_line(output: str) -> str:
    """Return the `Design hash:` line of `embodic-cli compute` output."""
    return next(line for line in output.splitlines() if line.startswith("Design hash: sha256:"))


@pytest.mark.req("REQ-N-06")
def test_frozen_cli_computes_the_default_example_like_the_source(capsys: pytest.CaptureFixture[str]) -> None:
    """Catches a frozen build that lost a module or a resource, or computes a different design than the source."""
    frozen = run_frozen(FROZEN_CLI, "compute", FROZEN_PACKAGE / "_resources" / EXAMPLE)
    assert cli_main(["compute", str(ROOT / "resources" / EXAMPLE)]) == 0
    source_output = capsys.readouterr().out

    assert (frozen.returncode, frozen.stderr) == (0, "")
    assert design_hash_line(frozen.stdout) == design_hash_line(source_output)
    assert "Design rule check: passed" in frozen.stdout


@pytest.mark.req("REQ-N-06")
def test_frozen_cli_exports_the_same_svg_as_the_source(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Catches a frozen SVG export that misses the theme tokens or draws differently from the source."""
    frozen_svg, source_svg = tmp_path / "frozen.svg", tmp_path / "source.svg"
    frozen = run_frozen(
        FROZEN_CLI, "export", FROZEN_PACKAGE / "_resources" / EXAMPLE, "--format", "svg", "-o", frozen_svg
    )
    assert cli_main(["export", str(ROOT / "resources" / EXAMPLE), "--format", "svg", "-o", str(source_svg)]) == 0
    capsys.readouterr()

    assert (frozen.returncode, frozen.stderr) == (0, "")
    assert without_export_time(frozen_svg) == without_export_time(source_svg)


@pytest.mark.req("REQ-N-06")
def test_frozen_gui_smoke_computes_and_quits(tmp_path: Path) -> None:
    """Catches a frozen app that cannot start Qt, load its example or compute; `--smoke` exits 1 or hangs then."""
    env = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        "HOME": str(tmp_path),
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
    }
    frozen = subprocess.run([str(FROZEN_GUI), "--smoke"], capture_output=True, encoding="utf-8", env=env, timeout=120)

    assert frozen.returncode == 0, frozen.stderr


@pytest.mark.slow
@pytest.mark.req("REQ-N-06")
def test_frozen_selftest_passes_every_check() -> None:
    """Catches a frozen build whose self-tests fail or find fewer checks than the source catalogue holds."""
    frozen = run_frozen(FROZEN_CLI, "selftest", timeout_s=600.0)

    assert frozen.returncode == 0, frozen.stdout
    assert frozen.stdout.splitlines()[-1] == f"{len(SELFTESTS)} tests: {len(SELFTESTS)} passed, 0 failed"


@pytest.mark.req("REQ-N-06")
def test_frozen_package_holds_no_python_source() -> None:
    """Catches a spec that collects .py files: the frozen app would then hash them and find every evidence stale.

    PyInstaller sets a frozen module's __file__ below _internal, so the registry hashes this folder (interfaces.md 3.1).
    """
    assert package_source_sha256(FROZEN_PACKAGE) is None


@pytest.mark.req("REQ-N-19")
def test_qt_libraries_are_separate_files() -> None:
    """Catches a build that packs Qt into the executable (one-file or UPX), which LGPL-3.0 R10 forbids."""
    found = {
        name: [p for p in FOLDER.rglob(f"*Qt6{name}.*") if p.is_file() and not p.is_symlink()]
        for name in ("Core", "Gui", "Widgets", "Svg")
    }

    assert [name for name, files in found.items() if not files] == []
