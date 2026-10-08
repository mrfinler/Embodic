"""Export view-model: preflight, checklist, the DRC gate and a run whose file list equals the disk (UI-29). Qt-free."""

import zipfile

import pytest

from embodic.io.exporters import ExportKind, ExportRefused
from embodic.ui.viewmodels.export import (
    BUNDLE,
    PRESETS,
    ExportViewModel,
    ExportWritten,
    file_stem,
    selection_problem,
)

ALL_BUT_SCREWS = PRESETS["export_bundle"] - {ExportKind.DXF_SCREWS}


def vm_for(outcome, stale=False):
    """Return an export view-model over a fixed outcome."""
    return ExportViewModel(lambda: (outcome, stale))


@pytest.mark.req("REQ-F-33")
def test_d08_run_writes_svg_dxf_json_pdf_readme_and_zip_and_lists_exactly_the_files_on_disk(d08, tmp_path):
    """Catches a result list that names a file not written, misses one, or a ZIP without the README."""
    vm = vm_for(d08)
    assert ExportKind.DXF_SCREWS in vm.unavailable()
    folder = tmp_path / "out"
    result = vm.run(ALL_BUT_SCREWS, folder, confirmed_drc_errors=False)
    assert isinstance(result, ExportWritten)
    on_disk = sorted(p.name for p in folder.iterdir())
    assert sorted(p.name for p in result.files) == on_disk
    stem = file_stem(d08.design.name)
    assert set(on_disk) == {
        f"{stem}.svg",
        f"{stem}.dxf",
        f"{stem}_outline.dxf",
        f"{stem}.embodic.json",
        f"{stem}_report.pdf",
        f"{stem}.zip",
        "README.txt",
    }
    with zipfile.ZipFile(folder / f"{stem}.zip") as archive:
        assert "README.txt" in archive.namelist() and f"{stem}.svg" in archive.namelist()
    readme = (folder / "README.txt").read_text(encoding="utf-8")
    assert f"{stem}.svg" in readme and f"{stem}_report.pdf" in readme


@pytest.mark.req("REQ-F-33")
def test_ui29_wave_preflight_lists_the_failures_and_an_unconfirmed_run_writes_nothing(wave, tmp_path):
    """Catches an export that writes drawings of a failing design without the user's confirmation."""
    vm = vm_for(wave)
    pre = vm.preflight()
    assert (pre.drc_passed, pre.needs_confirmation, len(pre.failures)) == (False, True, 186)
    assert pre.failures[0] == wave.drc[0].violations[0]
    refused = vm.run(frozenset({ExportKind.SVG, ExportKind.README, BUNDLE}), tmp_path, confirmed_drc_errors=False)
    assert isinstance(refused, ExportRefused) and refused.reason == "drc_errors_not_confirmed"
    assert list(tmp_path.iterdir()) == []
    confirmed = vm.run(frozenset({ExportKind.SVG, ExportKind.README}), tmp_path, confirmed_drc_errors=True)
    assert sorted(p.name for p in confirmed.files) == sorted(p.name for p in tmp_path.iterdir())
    assert 'drc_passed="false"' in (tmp_path / f"{file_stem(wave.design.name)}.svg").read_text(encoding="utf-8")


@pytest.mark.req("REQ-F-33")
def test_checklist_states_stamp_drc_staleness_and_assumption_count(d08, wave):
    """Catches a checklist that hides a failed DRC, a stale result or the assumptions."""
    items = {i.key: i for i in vm_for(d08).checklist()}
    assert list(items) == ["stamp", "drc", "stale", "assumptions"]
    assert items["stamp"].text.startswith("Stamp: embodic 0.0.1, registry v1+")
    assert (items["drc"].state, items["stale"].state, items["assumptions"].state) == ("pass", "pass", "warn")
    assert items["assumptions"].text.split()[0].isdigit()
    wave_items = {i.key: i for i in vm_for(wave, stale=True).checklist()}
    assert (wave_items["drc"].state, wave_items["drc"].text) == (
        "fail",
        "DRC: 186 failures. Export asks you to confirm.",
    )
    assert wave_items["stale"].state == "warn"


@pytest.mark.req("REQ-F-33")
@pytest.mark.parametrize(
    ("formats", "folder", "problem"),
    [
        (frozenset(), "x", "Choose at least one file."),
        (frozenset({ExportKind.README}), "x", "README needs at least one other file."),
        (frozenset({ExportKind.README, BUNDLE}), "x", "README needs at least one other file."),
        (frozenset({ExportKind.SVG}), "  ", "Choose a folder."),
        (frozenset({ExportKind.SVG, ExportKind.README}), "x", None),
    ],
)
def test_run_needs_a_file_besides_readme_and_a_folder(formats, folder, problem):
    """Catches a run that starts with README alone or without a folder."""
    assert selection_problem(formats, folder) == problem


@pytest.mark.req("REQ-F-33")
def test_file_stem_keeps_only_safe_characters():
    """Catches a design name that puts a colon or a slash into a file name."""
    assert file_stem("Example: UGent D08 12-coil 10-pole spiral") == "Example_UGent_D08_12-coil_10-pole_spiral"
    assert file_stem("../") == "embodic_design"
