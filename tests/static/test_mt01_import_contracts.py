"""MT-01: each import-linter contract C1 to C4 breaks when a scratch module violates it (package_layout.md section 3).

The scratch modules go into a temporary copy of src/ and pyproject.toml, never into the working tree.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

LINT_IMPORTS = "import sys; from importlinter.cli import lint_imports_command; sys.exit(lint_imports_command())"

SCRATCH = {
    "C1": {
        "geometry/__init__.py": "",
        "generators/__init__.py": "",
        "geometry/scratch.py": "import embodic.generators\n",
    },
    "C2": {"physics/__init__.py": "", "physics/scratch.py": "import PySide6.QtCore\n"},
    "C3": {
        "ui/__init__.py": "",
        "ui/views/__init__.py": "",
        "ui/viewmodels/__init__.py": "",
        "ui/viewmodels/scratch.py": "import embodic.ui.views\n",
    },
    "C4": {"io/__init__.py": "", "io/scratch.py": "import pcbnew\n"},
}
CONTRACT_NAMES = {
    "C1": "Core layers",
    "C2": "Qt only in the Qt adapter modules",
    "C3": "UI layers: view-models know no widgets",
    "C4": "No KiCad and no other GUI toolkits",
}


def lint_imports_with_scratch(tmp_path, files: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Copy the package and its configuration, add the scratch files, and run lint-imports on the copy."""
    shutil.copy(REPO / "pyproject.toml", tmp_path / "pyproject.toml")
    shutil.copytree(REPO / "src", tmp_path / "src", ignore=shutil.ignore_patterns("__pycache__"))
    for relative, text in files.items():
        target = tmp_path / "src" / "embodic" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(tmp_path / "src")}
    return subprocess.run(
        [sys.executable, "-c", LINT_IMPORTS], cwd=tmp_path, env=env, capture_output=True, text=True, check=False
    )


@pytest.mark.req("REQ-N-08")
@pytest.mark.parametrize("contract", sorted(SCRATCH))
def test_mt01_contract_breaks_on_scratch_violation(tmp_path, contract):
    """Catches a contract that cannot fail, e.g. a layer made optional by mistake or a forbidden module misspelt."""
    result = lint_imports_with_scratch(tmp_path, SCRATCH[contract])
    print(result.stdout)
    assert result.returncode == 1
    assert f"{CONTRACT_NAMES[contract]} BROKEN" in result.stdout
    others = [name for key, name in CONTRACT_NAMES.items() if key != contract]
    assert all(f"{name} KEPT" in result.stdout for name in others)


@pytest.mark.req("REQ-N-08")
def test_mt01_qt_adapter_modules_may_import_qt(tmp_path):
    """Catches an ignore_imports pattern that does not match, which would fail the first real Qt view in M4."""
    adapter = {
        "ui/__init__.py": "",
        "ui/views/__init__.py": "from PySide6 import QtGui\n",
        "ui/views/main_window.py": "import PySide6.QtWidgets\nimport shiboken6\n",
        "ui/workers.py": "from PySide6.QtCore import QThreadPool\n",
        "ui/app.py": "from PySide6.QtWidgets import QApplication\n",
    }
    result = lint_imports_with_scratch(tmp_path, adapter)
    assert result.returncode == 0, result.stdout
    assert "Contracts: 4 kept, 0 broken." in result.stdout
