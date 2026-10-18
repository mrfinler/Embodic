"""The bundle's build venv is reused only when it was built from the lock file that is there now (REQ-N-06).

`ensure_build_venv()` keeps `.venv-bundle` between releases. It records the SHA-256 of the lock file it installed from
and rebuilds the venv when the record is missing or differs. Nothing here creates a venv or runs pip: `run` and the
import probe are replaced by recorders.
"""

import importlib.util
import subprocess
import types
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[3] / "tools" / "build_bundle.py"
spec = importlib.util.spec_from_file_location("build_bundle", TOOL)
assert spec is not None and spec.loader is not None
bb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bb)

pytestmark = pytest.mark.req("REQ-N-06")

OLD_LOCK = "numpy==2.2.0 --hash=sha256:aa\n"
NEW_LOCK = "numpy==2.2.1 --hash=sha256:bb\n"


class FakeBuild:
    """Stands in for the build venv: records the commands, creates a python file for `-m venv` and probes cleanly."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
        self.commands: list[list[str]] = []
        self.failing_step: str | None = None
        self.lock = root / "py311.txt"
        self.lock.write_text(OLD_LOCK)
        venv = root / ".venv-bundle"
        monkeypatch.setattr(bb, "VENV", venv)
        monkeypatch.setattr(bb, "VENV_PYTHON", venv / "bin" / "python")
        monkeypatch.setattr(bb, "LOCK_FILE", self.lock)
        monkeypatch.setattr(bb, "run", self.run)
        probe = types.SimpleNamespace(
            run=lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=f"{bb.PYINSTALLER_VERSION}\n")
        )
        monkeypatch.setattr(bb, "subprocess", probe)

    def run(self, command: list[str | Path]) -> None:
        """Record the command, make the venv python for `-m venv`, and fail the chosen step."""
        words = [str(part) for part in command]
        self.commands.append(words)
        if words[1:3] == ["-m", "venv"]:
            bb.VENV_PYTHON.parent.mkdir(parents=True)
            bb.VENV_PYTHON.write_bytes(b"")
        elif self.failing_step and self.failing_step in words:
            raise subprocess.CalledProcessError(1, words)

    def installs(self) -> list[list[str]]:
        """Return the recorded pip commands."""
        return [words for words in self.commands if "pip" in words]


@pytest.fixture
def build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FakeBuild:
    """Return a fake build whose venv, lock file and commands live under tmp_path."""
    return FakeBuild(monkeypatch, tmp_path)


def test_a_venv_built_from_the_current_lock_file_is_reused(build):
    """Catches a rebuild on every release, which costs a PySide6 download for nothing."""
    bb.ensure_build_venv()
    first_run = len(build.commands)

    bb.ensure_build_venv()

    assert len(build.commands) == first_run


def test_a_changed_lock_file_rebuilds_the_venv_from_nothing(build):
    """Catches a release that bundles the packages of an old lock file: pip would also leave removed ones behind."""
    bb.ensure_build_venv()
    leftover = bb.VENV / "lib" / "removed_package.py"
    leftover.parent.mkdir(parents=True)
    leftover.write_bytes(b"")
    build.lock.write_text(NEW_LOCK)
    build.commands.clear()

    bb.ensure_build_venv()

    assert not leftover.exists()
    assert any(words[1:3] == ["-m", "venv"] for words in build.commands)
    assert any(str(build.lock) in words and "--require-hashes" in words for words in build.installs())
    assert bb.build_venv_ready()


def test_a_venv_without_a_record_of_its_lock_file_is_rebuilt(build):
    """Catches a venv from before the record existed, or a half-built one, being taken for a good one."""
    bb.VENV_PYTHON.parent.mkdir(parents=True)
    bb.VENV_PYTHON.write_bytes(b"")

    assert not bb.build_venv_ready()
    bb.ensure_build_venv()

    assert any(words[1:3] == ["-m", "venv"] for words in build.commands)
    assert bb.build_venv_ready()


def test_a_failed_install_leaves_no_record_so_that_the_next_release_rebuilds(build):
    """Catches a record written before the install finished: the broken venv would pass as built from this lock."""
    build.failing_step = "--require-hashes"

    with pytest.raises(subprocess.CalledProcessError):
        bb.ensure_build_venv()

    assert not bb.build_venv_ready()
