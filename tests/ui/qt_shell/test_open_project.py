"""Toolstrip Open (act-open, Ctrl+O): open a saved project file in the inspector (UX-AC-09, F21)."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox

from embodic.ui.viewmodels.session import SessionComputed, SessionDrafting

D08 = "spiral_12c10p_d08"
pytestmark = pytest.mark.req("REQ-F-15", "REQ-F-21")


@pytest.fixture
def saved_d08(make_shell, wait_ready, tmp_path):
    """Return a D08 project file saved by the app, the way a user saved it before."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_ready(window)
    path = tmp_path / "rotor test.embodic.json"
    window.session.save_project(path)
    window.close()
    return path


def test_f21_open_loads_a_saved_d08_file_into_the_inspector_and_computes_it(
    make_shell, wait_ready, qtbot, monkeypatch, saved_d08
):
    """Catches a disabled Open, a dialog whose file is ignored, or a file that opens without its values or result."""
    window = make_shell().window
    open_button = window.toolstrip.buttons["act-open"]
    assert open_button.isEnabled()
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(saved_d08), ""))
    qtbot.mouseClick(open_button, Qt.MouseButton.LeftButton)
    wait_ready(window)
    qtbot.waitUntil(lambda: isinstance(window.session.state.value, SessionComputed), timeout=60_000)
    values = window.session.document.draft.values
    assert values["/winding/coil/coil_count"] == 12 and values["/rotor/poles"] == 10
    assert window.panels["tab-coil"].editors["param-coil-count"].input.text() == "12"
    assert window.windowTitle().startswith(values["/name"])
    assert window.findChildren(QMessageBox) == []


def test_f21_a_file_that_does_not_load_says_why_and_keeps_the_open_design(make_shell, wait_ready, tmp_path):
    """Catches a broken file that silently replaces the open design or opens with no word of what went wrong."""
    window = make_shell().window
    window.session.load_example(D08)
    wait_ready(window)
    before = window.session.document
    broken = tmp_path / "broken.embodic.json"
    broken.write_text("{ not json", encoding="utf-8")
    dialog = window.open_project_file(broken)
    assert dialog is not None and dialog.text().startswith("broken.embodic.json was not opened.")
    assert window.session.document is before
    assert not isinstance(window.session.state.value, SessionDrafting)
