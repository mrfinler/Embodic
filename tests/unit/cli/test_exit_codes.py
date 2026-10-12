"""UT-CLI-02: each exit code of REQ-F-18 is shown by a command, and no other value comes out."""

import dataclasses
from pathlib import Path

import pytest

from embodic import api
from embodic.cli import ExitCode
from embodic.io.examples import load_example
from embodic.io.project import LoadedDraft, ProjectFile, save_project
from embodic.model.draft import draft_from_design

CF11 = "spiral_12c16p_default"
WAVE = "wave_16p_example"


def _save(path: Path, design, origin=None) -> Path:
    save_project(path, ProjectFile(design=design, origin=origin))
    return path


def test_exit_code_values_are_the_contract() -> None:
    """Catches a renumbered code: scripts compare against 0, 1, 2 and 3 (interfaces.md section 12)."""
    assert [(c.name, int(c)) for c in ExitCode] == [
        ("OK", 0),
        ("VALIDATION_ERRORS", 1),
        ("DRC_ERRORS", 2),
        ("INTERNAL_ERROR", 3),
    ]


@pytest.mark.req("REQ-F-18")
def test_exit_0_a_design_that_computes_and_passes_the_drc(run, project_of) -> None:
    """Catches a success path that returns a non-zero code."""
    code, _, err = run("compute", project_of(CF11))
    assert (code, err) == (0, "")


@pytest.mark.req("REQ-F-18")
def test_exit_1_an_unreadable_file_names_the_problem(run, tmp_path: Path) -> None:
    """Catches a traceback or a silent 0 for a file that is not a project: exit 1 and the catalogue sentence."""
    bad = tmp_path / "bad.embodic.json"
    bad.write_text("this is not json", encoding="utf-8")
    code, out, err = run("compute", bad)
    assert code == 1
    assert out == ""
    assert "error INVALID_PROJECT_FILE: The file is not an embodic project file or cannot be read." in err


@pytest.mark.req("REQ-F-18")
def test_exit_1_a_missing_file(run, tmp_path: Path) -> None:
    """Catches a missing file reported as an internal error (3) instead of a file the user must fix (1)."""
    code, _, err = run("compute", tmp_path / "absent.embodic.json")
    assert code == 1
    assert "error INVALID_PROJECT_NOT_FOUND: The project file does not exist." in err


@pytest.mark.req("REQ-F-18", "REQ-F-15")
def test_exit_1_an_incomplete_draft_lists_the_missing_pointers(run, tmp_path: Path) -> None:
    """Catches a draft computed with invented values, or a refusal that does not say which fields are missing."""
    _, design = load_example(CF11)
    values = dict(draft_from_design(design).values)
    del values["/winding/coil/trace_width_mm"], values["/rotor/poles"]
    path = tmp_path / "draft.embodic.json"
    save_project(path, LoadedDraft(draft=dataclasses.replace(draft_from_design(design), values=values), origin=None))
    code, out, err = run("compute", path)
    assert code == 1
    assert out == ""
    assert err.splitlines() == [
        "error MISSING_DESIGN_INCOMPLETE: The project holds an incomplete design; enter the missing values before "
        "computing.",
        "  at /winding/coil/trace_width_mm",
        "  at /rotor/poles",
    ]


@pytest.mark.req("REQ-F-18")
def test_exit_1_a_design_with_a_validation_error(run, tmp_path: Path) -> None:
    """Catches an invalid design that reaches geometry: 15 poles is odd, so the run stops at validation with 1."""
    ref, design = load_example(CF11)
    odd = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, poles=15))
    code, _, err = run("compute", _save(tmp_path / "odd.embodic.json", odd, ref))
    assert code == 1
    assert err.startswith("error INVALID_POLE_COUNT_ODD:")


@pytest.mark.req("REQ-F-18")
def test_exit_2_the_wave_example_fails_the_drc(run, project_of) -> None:
    """Catches a DRC failure that exits 0: the wave example has 186 violations (verified by running compute)."""
    code, out, _ = run("compute", project_of(WAVE))
    assert code == 2
    assert "Design rule check: FAILED, 186 violations" in out


@pytest.mark.req("REQ-F-18")
def test_no_drc_skips_the_check_so_the_wave_example_exits_0(run, project_of, tmp_path: Path) -> None:
    """Catches `--no-drc` that is parsed and ignored: the check is skipped, so the JSON holds no DRC reports."""
    out_json = tmp_path / "out.json"
    code, out, _ = run("compute", project_of(WAVE), "--no-drc", "--json", out_json)
    assert code == 0
    assert "Design rule check: not run" in out
    assert '"drc": null' in out_json.read_text(encoding="utf-8")


@pytest.mark.req("REQ-F-18")
def test_exit_3_an_internal_error_in_a_stage(run, project_of, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches an INTERNAL_* issue that exits 1 as if the user could fix it; the traceback must be on screen."""

    def broken(*_: object) -> None:
        raise RuntimeError("generator bug")

    monkeypatch.setattr(api, "build_layout", broken)
    code, _, err = run("compute", project_of(CF11))
    assert code == 3
    assert "error INTERNAL_GEOMETRY_FAILED:" in err
    assert "RuntimeError: generator bug" in err


@pytest.mark.req("REQ-F-18")
def test_exit_3_an_exception_outside_the_stages(run, project_of, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches an exception that escapes `main` as a traceback with the interpreter's own exit code 1."""

    def broken(_: object) -> None:
        raise ValueError("serializer bug")

    monkeypatch.setattr("embodic.cli.commands.outcome_to_json", broken)
    code, _, err = run("compute", project_of(CF11), "--json", "unused.json")
    assert code == 3
    assert "error INTERNAL_CLI_FAILED: The command stopped with an internal error; the traceback is attached." in err
    assert "ValueError: serializer bug" in err
