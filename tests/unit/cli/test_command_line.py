"""The command line itself (REQ-F-18): usage errors, output paths and the process entry points."""

import subprocess
import sys
from pathlib import Path

import pytest

CF11 = "spiral_12c16p_default"


@pytest.mark.req("REQ-F-18")
@pytest.mark.parametrize(
    "argv",
    [
        pytest.param([], id="no-command"),
        pytest.param(["frobnicate"], id="unknown-command"),
        pytest.param(["compute"], id="no-project"),
        pytest.param(["compute", "p.embodic.json", "--bogus"], id="unknown-option"),
        pytest.param(["export", "p.embodic.json", "-o", "x"], id="export-without-format"),
        pytest.param(["export", "p.embodic.json", "--format", "kicad", "-o", "x"], id="unknown-format"),
    ],
)
def test_a_usage_error_exits_1_and_never_2(run, argv: list[str]) -> None:
    """Catches argparse's own exit code 2, which scripts would read as 'the design rule check failed'."""
    code, out, err = run(*argv)
    assert code == 1
    assert out == ""
    assert "error INVALID_CLI_USAGE: The command line is not valid; run embodic-cli --help" in err


@pytest.mark.req("REQ-F-18")
def test_help_exits_0_and_lists_the_commands(run) -> None:
    """Catches a help request that is treated as a usage error."""
    code, out, _ = run("--help")
    assert code == 0
    assert "{compute,validate,export}" in out


@pytest.mark.req("REQ-F-18")
def test_json_to_a_missing_folder_exits_1_and_computes_nothing(run, project_of, tmp_path: Path) -> None:
    """Catches a FileNotFoundError traceback (exit 3) for a path the user mistyped."""
    target = tmp_path / "no_such_folder" / "out.json"
    code, out, err = run("compute", project_of(CF11), "--json", target)
    assert code == 1
    assert out == ""
    assert "error INVALID_CLI_OUTPUT_UNWRITABLE: The output file cannot be written;" in err
    assert f"  value: {target}" in err


@pytest.mark.req("REQ-F-18")
def test_json_to_a_folder_exits_1(run, project_of, tmp_path: Path) -> None:
    """Catches an output path that is a folder passing the check and failing later inside the write."""
    code, _, err = run("compute", project_of(CF11), "--json", tmp_path)
    assert code == 1
    assert "INVALID_CLI_OUTPUT_UNWRITABLE" in err


@pytest.mark.req("REQ-F-18")
def test_a_full_compute_loads_no_qt_module(project_of) -> None:
    """Catches a Qt import on the headless path: the process runs a full compute and then lists loaded Qt modules."""
    script = (
        "import sys\n"
        "from embodic.cli import main\n"
        f"code = main(['compute', {str(project_of(CF11))!r}])\n"
        "qt = sorted(m for m in sys.modules if m.split('.')[0] in ('PySide6', 'shiboken6'))\n"
        "ui = sorted(m for m in sys.modules if m.startswith('embodic.ui'))\n"
        "print(code, qt, ui)\n"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=False)
    assert result.stdout.splitlines()[-1] == "0 [] []", result.stderr


@pytest.mark.req("REQ-F-18")
def test_module_entry_point_returns_the_exit_code_to_the_shell(project_of) -> None:
    """Catches a `__main__` that drops main's return value: the wave example must end the process with 2."""
    wave = project_of("wave_16p_example")
    result = subprocess.run(
        [sys.executable, "-m", "embodic.cli", "compute", str(wave)], capture_output=True, check=False
    )
    assert result.returncode == 2
