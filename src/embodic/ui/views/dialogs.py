"""Confirmation dialogs of the results area: export with DRC failures (REQ-F-33) and replacing the reference."""

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from embodic.drc import DrcViolation
from embodic.results.formatting import format_quantity
from embodic.ui.strings import text
from embodic.ui.viewmodels.results import DRC_FIGURES
from embodic.units import Unit

LISTED_FAILURES = 50


def failure_line(v: DrcViolation) -> str:
    """Return one failure of the confirmation list."""
    return text(
        "export.confirm.row",
        rule=v.kind.issue_code,
        layer=v.layer or text("drc.layer.all"),
        measured=format_quantity(v.measured_mm, Unit.MM, significant=DRC_FIGURES),
        required=format_quantity(v.required_mm, Unit.MM, significant=DRC_FIGURES),
    )


class ExportConfirmDialog(QDialog):
    """``dlg-export-confirm``: lists the DRC failures; Cancel has the focus and is the default button."""

    def __init__(self, failures: Sequence[DrcViolation], total: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dlg-export-confirm")
        self.setWindowTitle(text("export.confirm.title"))
        self.setModal(True)
        body = QLabel(text("export.confirm.body", count=total))
        body.setWordWrap(True)
        self.failures = QListWidget()
        self.failures.setObjectName("export-confirm-list")
        self.failures.addItems([failure_line(v) for v in failures[:LISTED_FAILURES]])
        if total > LISTED_FAILURES:
            self.failures.addItem(text("export.confirm.more", count=total - LISTED_FAILURES))
        self.cancel = QPushButton(text("export.confirm.cancel"))
        self.cancel.setObjectName("btn-export-confirm-cancel")
        self.cancel.setDefault(True)
        self.cancel.clicked.connect(self.reject)
        self.proceed = QPushButton(text("export.confirm.export"))
        self.proceed.setObjectName("btn-export-confirm-run")
        self.proceed.setAutoDefault(False)
        self.proceed.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.proceed)
        buttons.addWidget(self.cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(body)
        layout.addWidget(self.failures, 1)
        layout.addLayout(buttons)
        self.resize(560, 360)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt override)
        """Put the focus on Cancel each time the dialog opens."""
        super().showEvent(event)
        self.cancel.setFocus(Qt.FocusReason.OtherFocusReason)


def confirm_replace_reference(parent: QWidget) -> QMessageBox:
    """Return the question that guards replacing a stored reference; Cancel is the default."""
    box = QMessageBox(
        QMessageBox.Icon.Question,
        text("compare.confirm.title"),
        text("compare.confirm.body"),
        QMessageBox.StandardButton.Cancel,
        parent,
    )
    box.setObjectName("dlg-compare-confirm")
    replace = box.addButton(text("compare.confirm.replace"), QMessageBox.ButtonRole.AcceptRole)
    replace.setObjectName("btn-compare-replace")
    box.setDefaultButton(QMessageBox.StandardButton.Cancel)
    return box
