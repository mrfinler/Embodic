"""``embodic-cli validate`` (REQ-F-18, UT-CLI-01): the design is checked against its rules and nothing is built."""

import dataclasses
from pathlib import Path

import pytest

from embodic import api
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, save_project

CF11 = "spiral_12c16p_default"
WAVE = "wave_16p_example"


@pytest.mark.req("REQ-F-18")
def test_validate_accepts_every_packaged_example(run, project_of, example_id: str) -> None:
    """UT-CLI-01. Catches an example the validator refuses; the wave example is valid, only its DRC fails."""
    code, out, err = run("validate", project_of(example_id))
    assert code == 0
    assert out.startswith("Valid: ")
    assert err == ""


@pytest.mark.req("REQ-F-18")
def test_validate_builds_nothing(run, project_of, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches `validate` that runs the whole pipeline: with a broken generator the design must still be valid."""

    def broken(*_: object) -> None:
        raise RuntimeError("generator must not run")

    monkeypatch.setattr(api, "build_layout", broken)
    code, out, _ = run("validate", project_of(CF11))
    assert (code, out.splitlines()[0]) == (0, "Valid: Spiral, 12 coils, 16 poles")


@pytest.mark.req("REQ-F-18")
def test_validate_reports_a_rule_violation_with_exit_1(run, tmp_path: Path) -> None:
    """Catches a validator whose findings never reach the exit code: 15 poles is odd."""
    ref, design = load_example(CF11)
    odd = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, poles=15))
    path = tmp_path / "odd.embodic.json"
    save_project(path, ProjectFile(design=odd, origin=ref))
    code, out, err = run("validate", path)
    assert code == 1
    assert "Valid" not in out
    assert err.startswith("error INVALID_POLE_COUNT_ODD:")


@pytest.mark.req("REQ-F-18")
def test_validate_of_an_unreadable_file_exits_1(run, tmp_path: Path) -> None:
    """Catches a validate that crashes on a missing file instead of reporting it."""
    code, _, err = run("validate", tmp_path / "absent.embodic.json")
    assert code == 1
    assert "error INVALID_PROJECT_NOT_FOUND:" in err
