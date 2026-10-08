"""Plant one defect at a time in the U-M4d code and confirm that the named test fails; restore the file after each.

Run from the repository root with QT_QPA_PLATFORM=offscreen and PYTHONPATH=src:
``python tests/ui/qt_results/mutation_check.py``. Exit 1 when a planted defect is not caught.
"""

import subprocess
import sys
from pathlib import Path

VM = "src/embodic/ui/viewmodels/results.py"
EXPORT_VM = "src/embodic/ui/viewmodels/export.py"
VIEWS = "src/embodic/ui/views"
UNIT = "tests/unit/ui/results"
QT = "tests/ui/qt_results"

# (defect, file, original text, planted text, test node that must fail)
MUTANTS = (
    (
        "badge hard-coded",
        VM,
        "        status=t.status,\n        assumed_count",
        "        status=Status.NOT_TESTED,\n        assumed_count",
        f"{QT}/test_results_and_checks.py::test_ui06_the_badge_comes_from_the_data",
    ),
    (
        "unit dropped",
        VM,
        "    return number, unit_text or text(",
        '    return number, "" or text(',
        f"{UNIT}/test_results_viewmodel.py::test_ui06_every_row_shows_value_unit_and_the_badge_of_its_traceable",
    ),
    (
        "EC-05 bound word lost",
        VM,
        'bound=text(f"results.how.bound.{flag.metric_bound.value}")',
        'bound=text("results.how.bound.estimate")',
        f"{QT}/test_results_and_checks.py::test_ui33_ke_disclosure_in_the_window_shows_e_edge_at_least_assumption_and_the_cap",
    ),
    (
        "estimate label hidden",
        VM,
        "        estimate_label=t.label,",
        "        estimate_label=None,",
        f"{QT}/test_results_and_checks.py::test_ui07_estimate_cards_show_the_estimate_badge_and_their_label",
    ),
    (
        "delta sign dropped",
        VM,
        '    return f"+{text_value}" if delta > 0 else text_value',
        "    return text_value",
        f"{UNIT}/test_checks_charts_compare_guide.py::test_ui34_counts_are_integers_and_deltas_carry_sign_and_direction",
    ),
    (
        "register formula dropped",
        VM,
        '        ("guide.eq.formula", e.formula),\n',
        "",
        f"{QT}/test_charts_compare_guide_export.py::test_ui17_eq_chip_and_toolstrip_open_the_register_entry_with_the_registry_content",
    ),
    (
        "focus on Export anyway",
        f"{VIEWS}/dialogs.py",
        "        self.cancel.setFocus(Qt.FocusReason.OtherFocusReason)",
        "        self.proceed.setFocus(Qt.FocusReason.OtherFocusReason)",
        f"{QT}/test_charts_compare_guide_export.py::test_ui29_export_with_drc_failures_lists_them_with_focus_on_cancel",
    ),
    (
        "result list claims an unwritten file",
        EXPORT_VM,
        "        return ExportWritten(folder=folder, files=tuple(p for p in files if p.is_file()))",
        '        return ExportWritten(folder=folder, files=(*files, folder / "extra.txt"))',
        f"{QT}/test_charts_compare_guide_export.py::test_export_dialog_on_d08_writes_svg_dxf_pdf_readme_zip_and_lists_only_those_files",
    ),
    (
        "animation ignores the OS setting",
        f"{VIEWS}/results_view.py",
        "    if not shown or not animations_enabled():",
        "    if not shown:",
        f"{QT}/test_results_and_checks.py::test_ui31_disclosure_slides_only_when_the_os_allows_animation",
    ),
    (
        "illustrative stamp missing",
        f"{VIEWS}/charts.py",
        'return None if self.model is None or self.model.computed else text("chart.illustrative")',
        "return None",
        f"{QT}/test_charts_compare_guide_export.py::test_ui32_a_drawing_not_from_the_engine_carries_the_illustrative_stamp",
    ),
    (
        "legend missing",
        f"{VIEWS}/charts.py",
        "if len(model.series) >= 2 else ()",
        "if len(model.series) >= 9 else ()",
        f"{QT}/test_charts_compare_guide_export.py::test_ui30_back_emf_chart_has_one_unit_legend_end_labels_data_table_and_badge",
    ),
)


def run(node: str) -> bool:
    """Return True when the test passes."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", node, "-q", "-x", "-p", "no:cacheprovider"], capture_output=True
    )
    return result.returncode == 0


def main() -> int:
    """Check every mutant; print one line each."""
    missed = 0
    for name, path, original, planted, node in MUTANTS:
        file = Path(path)
        source = file.read_text(encoding="utf-8")
        if source.count(original) != 1:
            print(f"STALE   {name}: the original text is not in {path} exactly once")
            missed += 1
            continue
        file.write_text(source.replace(original, planted), encoding="utf-8")
        try:
            caught = not run(node)
        finally:
            file.write_text(source, encoding="utf-8")
        print(f"{'CAUGHT' if caught else 'MISSED'}  {name}")
        missed += not caught
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
