"""Packaging fixtures: one wheel and one clean venv per session."""

from pathlib import Path

import pytest
from tests.packaging.support import CleanVenv, build_wheel


@pytest.fixture(scope="session")
def built_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return a wheel built from the working tree once per session."""
    return build_wheel(tmp_path_factory.mktemp("wheel"))


@pytest.fixture(scope="session")
def clean_venv(tmp_path_factory: pytest.TempPathFactory, built_wheel: Path) -> CleanVenv:
    """Return a clean venv with the lock file and the session wheel installed (PK-02)."""
    return CleanVenv(tmp_path_factory.mktemp("venv") / "venv", built_wheel)
