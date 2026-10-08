"""Trust badge, EQ chip and assumptions tag: the three trust cues every result and chart carries (design_spec.md 8).

The badge shows the status word, its border style (solid, dashed, dotted) and a `status-*` icon, so colour is never
the only cue (design_spec.md section 3.3).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from embodic.results.status import Status
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.views.style import themed_icon

ICON_PX = 16


def badge_property(status: Status) -> str:
    """Return the style sheet's ``status`` property value of a trust badge."""
    return status.value.replace(" ", "-")


def repolish(widget: QWidget) -> None:
    """Re-apply the style sheet after a dynamic property changed."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class StatusBadge(QWidget):
    """The `status-*` icon and the badge word of one status; the word and border carry the status, not colour."""

    def __init__(self, name: str) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.icon = QLabel()
        self.icon.setObjectName(f"{name}-icon")
        self.label = QLabel()
        self.label.setObjectName(name)
        self.label.setProperty("class", "badge")
        layout.addWidget(self.icon)
        layout.addWidget(self.label)
        self.status: Status | None = None

    def show_status(self, status: Status, reasons: tuple[str, ...], tokens: ThemeTokens) -> None:
        """Show one status from the data (D-007); ``unresolved`` reads "estimate"."""
        self.status = status
        prop = badge_property(status)
        self.label.setText(text(f"shell.badge.{prop}"))
        self.label.setProperty("status", prop)
        self.label.setAccessibleName(f"Status: {status.value}")
        self.label.setToolTip("; ".join(reasons))
        icon = themed_icon(f"status-{prop}", tokens)
        self.icon.setVisible(icon is not None)
        if icon is not None:
            self.icon.setPixmap(icon.pixmap(ICON_PX, ICON_PX))
        repolish(self.label)


class EqChip(QLabel):
    """An EQ-ID chip that opens the equation register at its entry; a tag (input, derived, count) does not."""

    activated = Signal(str)

    def __init__(self, name: str) -> None:
        super().__init__()
        self.setObjectName(name)
        self.setProperty("class", "eq-chip")
        self.eq_id: str | None = None

    def show_eq(self, eq_ids: tuple[str, ...], kind_tag: str) -> None:
        """Show the first EQ-ID of a chain as a link, or the kind tag when there is none."""
        self.eq_id = eq_ids[0] if eq_ids else None
        self.setText(self.eq_id or text(f"results.eq.tag-{kind_tag}"))
        self.setWhatsThis(self.eq_id or "")
        self.setToolTip(", ".join(eq_ids))
        link = self.eq_id is not None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus if link else Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor if link else Qt.CursorShape.ArrowCursor)
        self.setAccessibleName(text("results.eq.accessible", eq_id=self.eq_id) if link else self.text())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 (Qt override)
        """Open the register entry."""
        if self.eq_id is not None and event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit(self.eq_id)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        """Enter or Space opens the register entry."""
        if self.eq_id is not None and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.activated.emit(self.eq_id)
            return
        super().keyPressEvent(event)


class AssumptionTag(QToolButton):
    """The "n assumptions" tag; checking it shows the list it names."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self.setObjectName(name)
        self.setProperty("class", "asm-tag")
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

    def show_count(self, count: int) -> None:
        """Show the count; "0 assumptions" stays plain and cannot open an empty list."""
        self.setText(text("results.asm.count-one") if count == 1 else text("results.asm.count", count=count))
        self.setEnabled(count > 0)
        if count == 0:
            self.setChecked(False)
