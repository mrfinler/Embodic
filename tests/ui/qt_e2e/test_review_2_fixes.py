"""The UI-worker requests of m4_review_2.md section 6: F2 (chip provenance), ruling i (screw buttons), ruling j."""

import pytest
from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget

from .support import find

C14, WAVE = "spiral_12c14p", "wave_16p_example"  # the wave example has a screw pattern
STRETCHED_TABLES = (("tab-layers", "layer-list"), ("tab-layers", "pair-list"), ("tab-board", "screw-table"))


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    high, low = sorted((_relative_luminance(a), _relative_luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@pytest.mark.req("REQ-F-38", "REQ-N-14")
def test_f2_the_pair_list_rotation_chip_carries_its_provenance_for_the_dashed_example_rule(window, wait_drawn, qtbot):
    """F2. Catches a chip with `class` but no `provenance`, which the QSS draws solid black instead of dashed grey."""
    window.session.load_example(C14)
    wait_drawn(window)
    window.inspector_tabs.setCurrentWidget(window.panels["tab-layers"])
    pairs = find(window, "pair-list", QTableWidget)
    chips = [
        chip
        for r in range(pairs.rowCount())
        if (cell := pairs.cellWidget(r, pairs.columnCount() - 1)) is not None
        for chip in cell.findChildren(QLabel)
        if chip.property("class") == "prov-chip"
    ]
    assert chips, "the example's pairs show rotation chips"
    assert {(chip.text(), chip.property("provenance")) for chip in chips} == {("example", "example")}


@pytest.mark.req("REQ-N-14")
def test_ruling_i_the_screw_buttons_are_push_buttons_with_a_3_to_1_boundary(window, wait_drawn, qtbot):
    """Ruling i (F3). Catches a borderless QToolButton that reads as plain text (UX-AC-08 asks 3:1 for a boundary)."""
    window.session.load_example(WAVE)
    wait_drawn(window)
    board = window.panels["tab-board"]
    window.inspector_tabs.setCurrentWidget(board)
    for name in ("btn-screw-add", "btn-screw-remove"):
        button = find(window, name, QPushButton)
        assert button.isEnabled() and button.property("class") in (None, ""), "enabled, styled as btn-drc-locate"
        board.ensureWidgetVisible(button)
        qtbot.wait(20)
        image = button.grab().toImage()
        mid = image.height() // 2
        edge = image.pixelColor(0, mid)
        inside = image.pixelColor(image.width() // 2, 2)
        assert _contrast(edge.getRgb()[:3], inside.getRgb()[:3]) >= 3.0, name


@pytest.mark.req("REQ-N-15")
@pytest.mark.parametrize("size", [(1280, 800), (960, 540)], ids=["1280x800", "960x540"])
def test_ruling_j_the_last_column_takes_the_remaining_width_so_no_header_cell_is_empty(window, wait_drawn, qtbot, size):
    """Ruling j (F1). Catches a table whose columns end short of its viewport and leave an empty header cell."""
    window.resize(*size)
    window.session.load_example(C14)
    wait_drawn(window)
    for tab, name in STRETCHED_TABLES:
        window.inspector_tabs.setCurrentWidget(window.panels[tab])
        qtbot.wait(20)
        table = find(window, name, QTableWidget)
        header = table.horizontalHeader()
        assert header.length() >= table.viewport().width(), (name, header.length(), table.viewport().width())
