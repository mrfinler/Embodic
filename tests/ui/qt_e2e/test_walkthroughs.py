"""One user walkthrough per topology, through the widgets by objectName only (U-M4e row of work_breakdown.md).

Start, open a design (Examples gallery or New design), edit three inputs, recompute, open a result's disclosure, open
the DRC tab, export SVG and PDF into a folder, save the project, open it again: the design hash is the one saved
(the UI-21 path).
"""

import enum
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTabWidget,
    QWidget,
)

from embodic.io.canonical import design_document, design_hash
from embodic.model.schema import flatten
from embodic.ui.strings import text

from .support import answer_file_dialog, find, run_action, type_value


class Start(enum.Enum):
    """How the user reaches the design from the empty session."""

    EXAMPLES = "btn-empty-examples"
    NEW_DESIGN = "btn-empty-new"


@dataclass(frozen=True)
class Walkthrough:
    """One topology's route: the example it starts from, how it is opened, and three typed inputs."""

    example_id: str
    start: Start
    edits: tuple[tuple[str, str, float], ...]  # objectName, typed text, value the design must then hold


# Values no packaged example holds, so each chip must turn to "user" (a value equal to the example's turns it back).
OPERATING_EDITS = (
    ("param-speed", "1234", 1234.0),
    ("param-current", "1.7", 1.7),
    ("param-copper-temp", "65", 65.0),
)
POINTERS = {
    "param-speed": "/operating/speed_rpm",
    "param-current": "/operating/line_current_rms_a",
    "param-copper-temp": "/operating/winding_temperature_degc",
}
WALKTHROUGHS = {
    "spiral-d08": Walkthrough("spiral_12c10p_d08", Start.EXAMPLES, OPERATING_EDITS),
    "serpentine": Walkthrough("serpentine_16p_example", Start.NEW_DESIGN, OPERATING_EDITS),
    "wave": Walkthrough("wave_16p_example", Start.EXAMPLES, OPERATING_EDITS),
}


def _click(qtbot, widget: QWidget) -> None:
    assert widget.isEnabled() and widget.isVisible(), widget.objectName()
    # A stretched check box toggles on its indicator and text only, which sit at its left end.
    pos = QPoint(10, widget.height() // 2) if isinstance(widget, QCheckBox) else widget.rect().center()
    qtbot.mouseClick(widget, Qt.MouseButton.LeftButton, pos=pos)


def _open_design(qtbot, window, route: Walkthrough) -> None:
    _click(qtbot, find(window, route.start.value, QPushButton))
    if route.start is Start.EXAMPLES:
        gallery = find(window, "dlg-examples", QDialog)
        examples = find(gallery, "examples-list", QListWidget)
        row = next(
            r for r in range(examples.count()) if examples.item(r).data(Qt.ItemDataRole.UserRole) == route.example_id
        )
        examples.setCurrentRow(row)
        _click(qtbot, find(gallery, "btn-load-example", QPushButton))
        return
    dialog = find(window, "dlg-new-design", QDialog)
    qtbot.keyClicks(find(dialog, "param-design-name", QLineEdit), "Walkthrough stator")
    picker = find(dialog, "example-picker", QComboBox)
    picker.setCurrentIndex(picker.findData(route.example_id))
    _click(qtbot, find(dialog, "btn-create-design", QPushButton))


def _current_values(window) -> dict[str, object]:
    outcome = window.session.current_outcome()
    assert outcome is not None
    return flatten(design_document(outcome.design))


def _export_svg_and_pdf(qtbot, window, folder: Path) -> list[Path]:
    run_action(qtbot, window, "act-export-svg")
    dialog = find(window, "dlg-export", QDialog)
    for name in ("export-format-svg", "export-format-pdf"):
        box = find(dialog, name, QCheckBox)
        if not box.isChecked():
            _click(qtbot, box)
        assert box.isChecked(), name
    folder_field = find(dialog, "export-folder", QLineEdit)
    folder_field.selectAll()
    qtbot.keyClicks(folder_field, str(folder))
    _click(qtbot, find(dialog, "btn-export-run", QPushButton))
    confirm = window.findChild(QDialog, "dlg-export-confirm")
    if confirm is not None and confirm.isVisible():
        _click(qtbot, find(confirm, "btn-export-confirm-run", QPushButton))
    qtbot.waitUntil(lambda: find(dialog, "export-result", QWidget).isVisible(), timeout=60_000)
    written = sorted(folder.iterdir())
    assert len(written) == 2, find(dialog, "export-result", QLabel).text()
    _click(qtbot, find(dialog, "btn-export-close", QPushButton))
    return written


@pytest.mark.req("REQ-F-15", "REQ-F-31", "REQ-T-01")
@pytest.mark.parametrize("topology", list(WALKTHROUGHS))
def test_walkthrough_open_edit_recompute_inspect_export_save_and_reopen(topology, window, wait_drawn, qtbot, tmp_path):
    """Catches a step a user cannot finish, an edit the compute ignores, a missing export, or a hash that moves."""
    route = WALKTHROUGHS[topology]
    assert find(window, "empty-state").isVisible(), "the app starts in the empty session"
    _open_design(qtbot, window, route)
    wait_drawn(window)

    for name, typed, _ in route.edits:
        type_value(qtbot, window, name, typed)
    run_action(qtbot, window, "act-compute")
    wait_drawn(window)
    values = _current_values(window)
    assert {POINTERS[name]: values[POINTERS[name]] for name, _, _ in route.edits} == {
        POINTERS[name]: expected for name, _, expected in route.edits
    }
    assert {find(window, f"{name}-prov", QLabel).text() for name, _, _ in route.edits} == {text("design.prov.user")}

    window.show_results_tab("tab-results")
    toggle = find(window, "res-r-phase-how-toggle")
    _click(qtbot, toggle)
    assert find(window, "res-r-phase-how").isVisible(), "the disclosure opens"

    tabs = find(window, "results-tabs", QTabWidget)
    tabs.tabBar().setCurrentIndex(tabs.indexOf(find(window, "tab-drc")))
    assert tabs.currentWidget().objectName() == "tab-drc"
    assert find(window, "drc-summary", QLabel).text().startswith("DRC: ")

    exported = tmp_path / "export"
    exported.mkdir()
    written = _export_svg_and_pdf(qtbot, window, exported)
    assert sorted(p.suffix for p in written) == [".pdf", ".svg"]
    svg, pdf = sorted(written, key=lambda p: p.suffix, reverse=True)
    assert ET.parse(svg).getroot().tag.endswith("svg")
    assert pdf.read_bytes().startswith(b"%PDF-")

    saved_hash = design_hash(window.session.current_outcome().design)
    project = tmp_path / "walkthrough.embodic.json"
    QTimer.singleShot(0, lambda: answer_file_dialog(str(project)))
    run_action(qtbot, window, "act-save")
    assert project.is_file()

    type_value(qtbot, window, "param-speed", "900")
    wait_drawn(window)
    assert design_hash(window.session.current_outcome().design) != saved_hash, "an edit after the save"
    QTimer.singleShot(0, lambda: answer_file_dialog(str(project)))
    run_action(qtbot, window, "act-open")
    wait_drawn(window)
    assert design_hash(window.session.current_outcome().design) == saved_hash
