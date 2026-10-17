"""Widgets every view builds the same way."""

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QCheckBox, QTableWidget, QWidget


class _RowCheckBox(QCheckBox):
    def hitButton(self, pos: QPoint) -> bool:  # noqa: N802 (Qt override)
        return self.rect().contains(pos)


def check_box(label: str = "") -> QCheckBox:
    """Return a check box that takes a click anywhere in its 32 px row (m4_review_2.md ruling k, UX-AC-28).

    Under a style sheet Qt computes the click rectangle itself and never asks a proxy style, so the hit test lives in
    the widget.
    """
    return _RowCheckBox(label)


def table_widget(rows: int = 0, columns: int = 0) -> QTableWidget:
    """Return a table that the arrow keys move inside and Tab leaves (design_spec.md section 10).

    Qt's default lets Tab walk the cells and wrap from the last to the first, so focus never left the table.
    """
    table = QTableWidget(rows, columns)
    table.setTabKeyNavigation(False)
    return table


def repolish(widget: QWidget) -> None:
    """Re-apply the style sheet after a dynamic property changed (design_spec.md section 8)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def set_style_property(widget: QWidget, name: str, value: str) -> bool:
    """Set a property the style sheet selects on; re-apply the sheet and return True only when the value changed.

    Every refresh sets the properties again, and re-polishing 131 unchanged widgets was a third of the GUI thread's
    profiled time when a result arrived (DEF-U-M6a-01).
    """
    if widget.property(name) == value:
        return False
    widget.setProperty(name, value)
    repolish(widget)
    return True
