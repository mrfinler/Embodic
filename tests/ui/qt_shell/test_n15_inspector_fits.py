"""REQ-N-15: every inspector form fits the inspector's width, since forms never scroll sideways.

Rows N15-1 to N15-6 of docs/phase3/design/fix_wave_f2.md section (a) (DEF-U-M7c-02, DEF-US12-01).

A form's horizontal scroll bar is always off, so a form wider than its viewport is cut at the right edge without a
scroll bar to show it; the N-15 scroll-bar check cannot see that.
"""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QComboBox, QPushButton, QToolButton

from embodic.ui.views.coil_panel import FieldEditor

from .conftest import D08
from .test_centre_split import resize

pytestmark = pytest.mark.req("REQ-N-15")

SERPENTINE = "serpentine_16p_example"
EXAMPLES = (D08, "spiral_12c14p", "spiral_12c16p_default", "wave_16p_example", SERPENTINE)
SIZES = ((960, 540), (1280, 800), (1920, 1080))


def show_tab(window, panel) -> None:
    """Select an inspector tab and let its layout settle."""
    window.inspector_tabs.setCurrentWidget(panel)
    for _ in range(5):
        QApplication.processEvents()


def open_example(make_shell, wait_ready, example, size):
    """Open an example in a shell window of ``size`` and return the window."""
    window = make_shell().window
    window.session.load_example(example)
    wait_ready(window)
    resize(window, size)
    return window


@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("example", EXAMPLES)
def test_n15_1_and_2_every_inspector_form_fits_and_no_combo_box_is_narrower_than_its_hint(
    make_shell, wait_ready, example, size
):
    """N15-1, N15-2. Catches a form wider than its viewport (e68d5ff: Board 327 px, serpentine Layers 306 px).

    It also catches a combo box squeezed below its size hint, which clips the chosen text.
    """
    window = open_example(make_shell, wait_ready, example, size)
    wider, squeezed = {}, {}
    for name, panel in window.panels.items():
        show_tab(window, panel)
        if panel.widget().width() > panel.viewport().width():
            wider[name] = (panel.widget().width(), panel.viewport().width())
        for box in panel.findChildren(QComboBox):
            if box.isVisibleTo(panel) and box.currentIndex() >= 0 and box.width() < box.sizeHint().width():
                squeezed[box.objectName()] = (box.width(), box.sizeHint().width())
    assert (wider, squeezed) == ({}, {})


def test_n15_3_a_field_chip_sits_on_the_label_line_above_the_input(make_shell, wait_ready):
    """N15-3. Catches a chip beside the input, which costs the control line 72 px of its 204 (DEF-U-M7c-02)."""
    window = open_example(make_shell, wait_ready, D08, (960, 540))
    checked = 0
    for panel in window.panels.values():
        show_tab(window, panel)
        for editor in panel.findChildren(FieldEditor):
            if not (editor.isVisibleTo(panel) and editor.chip.isVisibleTo(panel)):
                continue
            chip_bottom = editor.chip.mapTo(panel, QPoint(0, editor.chip.height())).y()
            input_top = editor.input.mapTo(panel, QPoint(0, 0)).y()
            assert chip_bottom <= input_top, (editor.widget_id, chip_bottom, input_top)
            checked += 1
    assert checked > 20, "the check must see the field rows of D08, which all carry an example chip"


def test_n15_5_the_stack_mode_buttons_stack_one_per_line_and_the_layers_tab_fits(make_shell, wait_ready):
    """N15-5, DEF-US12-01. Catches "Single board" and "One board per phase" on one 252 px line in a 258 px viewport."""
    window = open_example(make_shell, wait_ready, SERPENTINE, (960, 540))
    layers = window.panels["tab-layers"]
    show_tab(window, layers)
    first = layers.findChild(QToolButton, "param-stack-mode-single")
    second = layers.findChild(QToolButton, "param-stack-mode-one_board_per_phase")
    assert first.isVisibleTo(layers) and second.isVisibleTo(layers)
    first_bottom = first.mapTo(layers, QPoint(0, first.height())).y()
    assert first_bottom <= second.mapTo(layers, QPoint(0, 0)).y()
    assert first.mapTo(layers, QPoint(0, 0)).x() == second.mapTo(layers, QPoint(0, 0)).x()
    assert first.width() == second.width() == layers.editors["param-stack-mode"].input.width(), "at the row's width"
    assert layers.widget().width() <= layers.viewport().width()


def test_n15_5_up_and_down_move_between_the_stacked_stack_mode_choices_like_left_and_right(
    make_shell, wait_ready, qtbot
):
    """N15-5 (a) 4. Catches a stacked segment whose Up and Down keys do nothing, which Left and Right do."""
    window = open_example(make_shell, wait_ready, SERPENTINE, (960, 540))
    layers = window.panels["tab-layers"]
    show_tab(window, layers)
    segment = layers.editors["param-stack-mode"].input
    single, per_phase = segment.buttons["single"], segment.buttons["one_board_per_phase"]
    assert single.isChecked()
    single.setFocus(Qt.FocusReason.TabFocusReason)
    qtbot.keyClick(single, Qt.Key.Key_Down)
    assert (segment.value(), per_phase.hasFocus()) == ("one_board_per_phase", True)
    qtbot.keyClick(per_phase, Qt.Key.Key_Up)
    assert (segment.value(), single.hasFocus()) == ("single", True)


def test_n15_6_the_screw_buttons_read_add_and_remove_and_keep_the_long_accessible_names(make_shell, wait_ready):
    """N15-6. Catches the long visible labels back (127 px for both buttons), or an accessible name that drops "screw".

    Each accessible name starts with the visible label (WCAG SC 2.5.3 Label in Name, assumption in the ruling).
    """
    window = open_example(make_shell, wait_ready, D08, (960, 540))
    show_tab(window, window.panels["tab-board"])
    add = window.findChild(QPushButton, "btn-screw-add")
    remove = window.findChild(QPushButton, "btn-screw-remove")
    assert (add.text(), add.accessibleName()) == ("Add", "Add screw pattern")
    assert (remove.text(), remove.accessibleName()) == ("Remove", "Remove screw pattern")
