"""``embodic-cli export`` (REQ-F-18, REQ-F-33, UT-CLI-01): each format on each example, and the DRC confirmation."""

import dataclasses
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
from ezdxf import recover
from pypdf import PdfReader

from embodic import api
from embodic.api import compute_project
from embodic.io.examples import load_example
from embodic.io.project import ProjectFile, save_project

CF11 = "spiral_12c16p_default"
WAVE = "wave_16p_example"  # fails the DRC with 186 violations
HOLES = {"serpentine_16p_example": 8, "wave_16p_example": 8}  # screw clearance holes; the other examples have none
FORMATS = ("svg", "dxf", "dxf-outline", "dxf-screws", "pdf", "readme", "bundle")


def export(run, project: Path, fmt: str, out: Path, *flags: str) -> tuple[int, str, str]:
    """Run ``embodic-cli export`` with the output path ``out``."""
    return run("export", project, "--format", fmt, "-o", out, *flags)


def dxf_entities(path: Path) -> list[str]:
    """Return the entity types of a DXF file after checking that ezdxf reads it with no audit error."""
    document, auditor = recover.readfile(str(path))
    assert not auditor.has_errors, auditor.errors
    return [entity.dxftype() for entity in document.modelspace()]


@pytest.mark.req("REQ-F-18", "REQ-F-33")
@pytest.mark.parametrize("fmt", FORMATS)
def test_every_format_of_every_example_is_written_and_readable(run, project_of, tmp_path, example_id, fmt) -> None:
    """UT-CLI-01. Catches a format that writes nothing, writes the wrong kind of file or cannot be read back."""
    name = f"motor.{fmt}"
    out = tmp_path / name
    holes = HOLES.get(example_id, 0)
    confirm = ("--allow-drc-errors",) if example_id == WAVE else ()
    code, stdout, stderr = export(run, project_of(example_id), fmt, out, *confirm)
    if fmt == "dxf-screws" and holes == 0:
        assert (code, out.exists()) == (1, False)
        assert "error INVALID_EXPORT_NO_SCREW_HOLES:" in stderr
        return
    assert code == 0, stderr
    assert f"Wrote {out}" in stdout
    design_hash = compute_project(project_of(example_id)).design_hash
    if fmt == "svg":
        assert ET.parse(out).getroot().tag.endswith("svg")
        assert design_hash in out.read_text(encoding="utf-8")
    elif fmt in ("dxf", "dxf-outline"):
        assert len(dxf_entities(out)) > 0
    elif fmt == "dxf-screws":
        assert dxf_entities(out) == ["CIRCLE"] * holes
    elif fmt == "pdf":
        reader = PdfReader(out)
        assert len(reader.pages) >= 1
        assert "Key results" in reader.pages[0].extract_text()
    elif fmt == "readme":
        text = out.read_text(encoding="utf-8")
        assert design_hash in text and "Units: millimetres (mm)." in text
    else:
        stem = out.stem
        expected = {f"{stem}.svg", f"{stem}.dxf", f"{stem}_outline.dxf", f"{stem}.embodic.json", f"{stem}_report.pdf"}
        expected |= {f"{stem}_screws.dxf"} if holes else set()
        with zipfile.ZipFile(out) as archive:
            assert set(archive.namelist()) == expected | {"README.txt"}
            assert archive.testzip() is None


@pytest.mark.req("REQ-F-18")
def test_dxf_formats_are_not_swapped(run, project_of, tmp_path) -> None:
    """Catches `dxf` and `dxf-outline` mapped to each other: the complete drawing holds more than the outline."""
    complete, outline = tmp_path / "complete.dxf", tmp_path / "outline.dxf"
    assert export(run, project_of(CF11), "dxf", complete)[0] == 0
    assert export(run, project_of(CF11), "dxf-outline", outline)[0] == 0
    assert len(dxf_entities(outline)) < len(dxf_entities(complete))


@pytest.mark.req("REQ-F-33")
@pytest.mark.parametrize("fmt", FORMATS)
def test_a_failed_drc_refuses_every_format_without_confirmation(run, project_of, tmp_path, fmt) -> None:
    """Catches an export that writes files for a design that fails the DRC: exit 2, nothing on disk, the fix named."""
    out = tmp_path / f"wave.{fmt}"
    code, stdout, stderr = export(run, project_of(WAVE), fmt, out)
    assert code == 2
    assert stdout == ""
    assert not out.exists()
    assert "error DRC_EXPORT_NOT_CONFIRMED:" in stderr
    assert "error DRC_CLI_EXPORT_REFUSED: Nothing was written. Run the command again with --allow-drc-errors" in stderr


@pytest.mark.req("REQ-F-33")
def test_allow_drc_errors_writes_the_file_and_warns(run, project_of, tmp_path) -> None:
    """Catches a flag that is parsed and ignored, or one that writes silently: exit 0 and a warning with the count."""
    out = tmp_path / "wave.svg"
    code, _, stderr = export(run, project_of(WAVE), "svg", out, "--allow-drc-errors")
    assert code == 0
    assert out.exists()
    assert "warning DRC_CLI_EXPORT_FORCED:" in stderr
    assert "  value: 186" in stderr


@pytest.mark.req("REQ-F-33")
def test_allow_drc_errors_is_silent_when_the_drc_passed(run, project_of, tmp_path) -> None:
    """Catches a warning about a failure that did not happen."""
    code, _, stderr = export(run, project_of(CF11), "svg", tmp_path / "a.svg", "--allow-drc-errors")
    assert (code, stderr) == (0, "")


@pytest.mark.req("REQ-F-18")
def test_a_design_that_does_not_build_is_not_exported(run, tmp_path) -> None:
    """Catches an export of a design with a validation error: exit 1, the issue on screen, no file."""
    ref, design = load_example(CF11)
    odd = dataclasses.replace(design, rotor=dataclasses.replace(design.rotor, poles=15))
    project = tmp_path / "odd.embodic.json"
    save_project(project, ProjectFile(design=odd, origin=ref))
    out = tmp_path / "odd.svg"
    code, _, stderr = export(run, project, "svg", out)
    assert (code, out.exists()) == (1, False)
    assert stderr.startswith("error INVALID_POLE_COUNT_ODD:")


@pytest.mark.req("REQ-F-18")
def test_an_internal_error_stops_the_export_with_exit_3(run, project_of, tmp_path, monkeypatch) -> None:
    """Catches an internal error that is reported as a missing layout (exit 1) and hides the traceback."""

    def broken(*_: object) -> None:
        raise RuntimeError("generator bug")

    monkeypatch.setattr(api, "build_layout", broken)
    out = tmp_path / "a.svg"
    code, _, stderr = export(run, project_of(CF11), "svg", out)
    assert (code, out.exists()) == (3, False)
    assert "RuntimeError: generator bug" in stderr


@pytest.mark.req("REQ-F-18")
def test_output_in_a_missing_folder_exits_1_before_computing(run, project_of, tmp_path, monkeypatch) -> None:
    """Catches a mistyped output path found only after the whole compute, or reported as an internal error."""

    def must_not_run(*_: object, **__: object) -> None:
        raise AssertionError("compute ran")

    monkeypatch.setattr("embodic.cli.commands.compute", must_not_run)
    code, _, stderr = export(run, project_of(CF11), "svg", tmp_path / "missing" / "a.svg")
    assert code == 1
    assert "error INVALID_CLI_OUTPUT_UNWRITABLE:" in stderr
