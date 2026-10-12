"""Shared fixtures of the CLI tests: the packaged example files and a runner that returns what the user would see."""

from collections.abc import Callable
from pathlib import Path

import pytest

from embodic.cli import main
from embodic.io.examples import examples_dir

EXAMPLE_IDS = tuple(sorted(path.name.split(".")[0] for path in examples_dir().glob("*.embodic.json")))


@pytest.fixture
def project_of() -> Callable[[str], Path]:
    """Return the packaged project file of an example id."""
    return lambda example_id: examples_dir() / f"{example_id}.embodic.json"


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str]) -> Callable[..., tuple[int, str, str]]:
    """Return a function that calls ``main`` with the arguments and returns (exit code, stdout, stderr)."""

    def call(*argv: object) -> tuple[int, str, str]:
        code = main([str(a) for a in argv])
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return call


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrise every test that takes ``example_id`` over all packaged examples."""
    if "example_id" in metafunc.fixturenames:
        metafunc.parametrize("example_id", EXAMPLE_IDS)
