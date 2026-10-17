"""The Phases tab (`tab-phases`, screens.md section 3): connection, sequence, terminals, assignment and the pattern."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embodic.model.fields import FieldGroup
from embodic.model.schema import JsonValue
from embodic.model.vocabulary import TopologyKind
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import ASSIGNMENT_MODES, ASSIGNMENT_POINTER, DesignSession, assignment_mode
from embodic.ui.views.coil_panel import FieldPanel, Segment, fit_rows, hint_label, label_above, repolish, show_hints
from embodic.ui.views.widgets import table_widget

PHASE_COLUMNS = ("coil_index", "phase", "polarity")
_EDIT_TRIGGERS = QAbstractItemView.EditTrigger.EditKeyPressed | QAbstractItemView.EditTrigger.DoubleClicked


class PhasePanel(FieldPanel):
    """Phase rows from the field table, the assignment mode and table, the pattern and the balance status."""

    FORM_ATTRIBUTES = ("pattern", "pattern_caption", "pattern_hint", "balance")

    def __init__(self, session: DesignSession) -> None:
        super().__init__("tab-phases", session)

    def add_helpers(self, group: FieldGroup, form: QFormLayout) -> None:
        """Add the assignment mode (spiral): Auto writes null, Manual writes the list from the computed pattern."""
        if group is not FieldGroup.PHASES or self._building is not TopologyKind.SPIRAL:
            return
        mode = Segment(
            "param-phase-assign-mode",
            tuple(ASSIGNMENT_MODES),
            lambda choice: self.session.set_assignment_mode(ASSIGNMENT_MODES[str(choice)]),
        )
        form.addRow(label_above(text("param-phase-assign-mode.label"), mode))
        self.helpers["param-phase-assign-mode"] = mode

    def build(self) -> None:
        """Add the phase rows, then the pattern, the balance status and the phase table (spiral)."""
        super().build()
        self.pattern = hint_label("phase-pattern-string")
        self.pattern.setProperty("class", "unit")
        self.pattern_caption = QLabel(text("phase-pattern-string.label"))
        self.pattern_caption.setBuddy(self.pattern)
        self.pattern_hint = QLabel(text("phase-pattern-string.hint"))
        self.pattern_hint.setProperty("class", "hint")
        self.pattern.setAccessibleName(self.pattern_caption.text())
        self.pattern.setAccessibleDescription(self.pattern_hint.text())
        self.balance = QLabel()
        self.balance.setObjectName("phase-balance-status")
        self.balance.setProperty("class", "check-state")
        self.balance.setWordWrap(True)
        self.balance.setToolTip(text("phase-balance-status.tooltip"))
        section = QWidget()
        column = QVBoxLayout(section)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self.pattern_caption)
        column.addWidget(self.pattern)
        column.addWidget(self.pattern_hint)
        column.addWidget(self.balance)
        if "param-phase-assign-mode" in self.helpers:
            table = table_widget(0, len(PHASE_COLUMNS))
            table.setObjectName("phase-table")
            table.setHorizontalHeaderLabels([text(f"phase-table.{c.split('_')[0]}") for c in PHASE_COLUMNS])
            table.verticalHeader().setVisible(False)
            table.itemChanged.connect(self._edit_cell)
            column.addWidget(table)
            self.helpers["phase-table"] = table
        self._layout.addWidget(section)

    def refresh_helpers(self) -> None:
        """Show the assignment mode, the phase table and what the last compute says about the pattern and balance."""
        show_hints({"phase-pattern-string": self.pattern, "phase-balance-status": self.balance}, self.session)
        for part in (self.pattern_caption, self.pattern_hint):
            part.setVisible(not self.pattern.isHidden())
        self.balance.setProperty(
            "state", "pass" if self.balance.text() == text("phase-balance-status.balanced") else "fail"
        )
        repolish(self.balance)
        mode, table = self.helpers.get("param-phase-assign-mode"), self.helpers.get("phase-table")
        document = self.session.document
        if not isinstance(mode, Segment) or not isinstance(table, QTableWidget) or document is None:
            return
        current = assignment_mode(document.draft.values)
        mode.show_value(current)
        can_start = current == "manual" or bool(self.session.auto_assignment())
        mode.buttons["manual"].setEnabled(can_start)
        mode.buttons["manual"].setToolTip("" if can_start else text("design.hint.manual-needs-result"))
        manual = current == "manual"
        table.setEditTriggers(_EDIT_TRIGGERS if manual else QAbstractItemView.EditTrigger.NoEditTriggers)
        rows = self.session.phase_assignment()
        table.blockSignals(True)
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, leaf in enumerate(PHASE_COLUMNS):
                item = QTableWidgetItem("" if getattr(row, leaf) is None else str(getattr(row, leaf)))
                if leaf == "coil_index" or not manual:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
        table.blockSignals(False)
        fit_rows(table)

    def _edit_cell(self, item: QTableWidgetItem) -> None:
        leaf = PHASE_COLUMNS[item.column()]
        typed = item.text().strip()
        if leaf == "phase":
            value: JsonValue = typed.upper()
        else:
            try:
                value = int(typed)
            except ValueError:
                value = typed
        self.session.edit(f"{ASSIGNMENT_POINTER}/{item.row()}/{leaf}", value)
