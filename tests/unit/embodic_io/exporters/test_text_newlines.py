r"""DEF-W-09: every text file embodic writes ends its lines with LF on every platform (REQ-N-04).

The ``windows_text_mode`` fixture of tests/conftest.py makes this process write text files the way CPython writes them
on Windows.
"""

import zipfile
from collections.abc import Callable
from pathlib import Path

import pytest

from embodic.api import ComputeOutcome
from embodic.cli.commands import main
from embodic.io.board_dump import write_board_dump
from embodic.io.bundle import write_bundle
from embodic.io.dxf_writer import write_dxf
from embodic.io.examples import examples_dir, load_example
from embodic.io.exporters import ExportKind, ExportRefused, ExportSummary
from embodic.io.project import project_from_example, save_project
from embodic.io.readme_writer import write_readme
from embodic.io.svg_writer import write_svg

pytestmark = pytest.mark.req("REQ-N-04")

EXAMPLE = "serpentine_16p_example"  # the packaged example with screw holes, so the screws DXF is written
TEXT_KINDS = (
    ExportKind.SVG,
    ExportKind.DXF_COMPLETE,
    ExportKind.DXF_OUTLINE,
    ExportKind.DXF_SCREWS,
    ExportKind.PROJECT_JSON,
)


def _assert_lf_only(name: str, data: bytes) -> None:
    first_cr = data.find(b"\r")
    assert first_cr == -1, f"{name} holds a carriage return at byte {first_cr}: {data[max(0, first_cr - 8) :][:16]!r}"
    assert data.count(b"\n") > 1, f"{name} has fewer than two lines; the check would prove nothing"


@pytest.mark.usefixtures("windows_text_mode")
def test_windows_text_mode_reproduces_crlf_for_a_write_without_newline(tmp_path: Path) -> None:
    """Catches a fixture that no longer simulates Windows, which would let every check below pass vacuously."""
    plain, pinned = tmp_path / "plain.txt", tmp_path / "pinned.txt"
    plain.write_text("a\nb\n", encoding="utf-8")
    pinned.write_text("a\nb\n", encoding="utf-8", newline="\n")
    assert (plain.read_bytes(), pinned.read_bytes()) == (b"a\r\nb\r\n", b"a\nb\n")


@pytest.mark.usefixtures("windows_text_mode")
def test_board_dump_has_lf_line_ends_under_windows_text_mode(
    outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches the board-dump writer using the platform newline, so its bytes differ on Windows (DEF-W-09)."""
    boards = outcome_of(EXAMPLE).boards
    assert boards is not None
    path = tmp_path / "board.json"
    write_board_dump(boards.boards[0], path, case_id="def-w-09")
    _assert_lf_only(path.name, path.read_bytes())


@pytest.mark.usefixtures("windows_text_mode")
def test_every_export_file_has_lf_line_ends_under_windows_text_mode(
    outcome_of: Callable[[str], ComputeOutcome], tmp_path: Path
) -> None:
    """Catches any text exporter (SVG, DXF, project, README, bundle member) writing the platform newline."""
    outcome = outcome_of(EXAMPLE)
    written: list[ExportSummary] = []
    for summary in (
        write_svg(outcome, tmp_path / "m.svg"),
        write_dxf(outcome, tmp_path / "m.dxf", "complete"),
        write_dxf(outcome, tmp_path / "m_outline.dxf", "outline"),
        write_dxf(outcome, tmp_path / "m_screws.dxf", "screws"),
    ):
        assert isinstance(summary, ExportSummary), summary
        written.append(summary)
    written.append(write_readme(outcome, written, tmp_path / "README.txt"))
    project = project_from_example(load_example(EXAMPLE))
    save_project(tmp_path / "m.embodic.json", project, saved_utc="2026-10-17T00:00:00Z")
    for path in sorted(tmp_path.iterdir()):
        _assert_lf_only(path.name, path.read_bytes())

    bundle = tmp_path / "bundle" / "m.zip"
    bundle.parent.mkdir()
    assert not isinstance(write_bundle(outcome, TEXT_KINDS, bundle), ExportRefused)
    with zipfile.ZipFile(bundle) as archive:
        members = archive.namelist()
        assert "README.txt" in members
        for member in members:
            _assert_lf_only(member, archive.read(member))


@pytest.mark.usefixtures("windows_text_mode")
def test_compute_json_outcome_has_lf_line_ends_under_windows_text_mode(tmp_path: Path) -> None:
    """Catches the ``compute --json`` outcome file written with the platform newline."""
    out = tmp_path / "outcome.json"
    main(["compute", str(examples_dir() / f"{EXAMPLE}.embodic.json"), "--json", str(out)])
    _assert_lf_only(out.name, out.read_bytes())
