"""The Board and rotor tab (`tab-board`, screens.md section 5): outline, bore, stack-up, rules, rotor, operation."""

from collections.abc import Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embodic.model.fields import FIELD_BY_KEY, FieldGroup
from embodic.model.schema import JsonValue, ValueType
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import (
    BORE_POINTER,
    SCREWS_POINTER,
    DesignSession,
    StackupInput,
    bore_choice,
    display_text,
    parse_text,
    screw_patterns,
)
from embodic.ui.viewmodels.stepping import STACKUP_INPUT_RULES
from embodic.ui.views.coil_panel import (
    FieldEditor,
    FieldPanel,
    choice_text,
    fit_rows,
    fit_width,
    label_above,
    unit_text,
)
from embodic.ui.views.step_keys import StepKeys
from embodic.ui.views.widgets import table_widget

BORE_CHOICES = ("none", "circle", "polygon")
HOLE_WIDGET = "param-screw-hole-diameter"
SCREW_COLUMNS = (("size", "size"), ("count", "count"), ("pitch_radius_mm", "pitch-radius"))
# Each needs its unit, chip, hint and error label, which a cell cannot carry, so it is a field (U-S4e ruling c).
PATTERN_FIELDS = {
    "param-screw-fit": "fit",
    HOLE_WIDGET: "hole_diameter_mm",
    "param-screw-angle-offset": "angle_offset_rad",
}


def _name(widget: QWidget | None) -> str:
    return "" if widget is None else widget.objectName()


class BoardRotorPanel(FieldPanel):
    """Board rows from the field table plus the bore choice and the copper weight and board thickness inputs."""

    def __init__(self, session: DesignSession) -> None:
        super().__init__("tab-board", session)

    def add_helpers(self, group: FieldGroup, form: QFormLayout) -> None:
        """Add the bore choice to the outline group and the stack-up generator inputs to the manufacturing group."""
        if group is FieldGroup.OUTLINE:
            bore = QComboBox()
            bore.setObjectName("param-bore")
            bore.setPlaceholderText(text("design.required.hint"))
            for choice in BORE_CHOICES:
                bore.addItem(choice_text(choice), choice)
            bore.activated.connect(lambda index: self._choose_bore(bore.itemData(index)))
            self.helpers["param-bore"] = bore
            self._pending_bore = label_above(text("param-bore.label"), bore)
        if group is FieldGroup.MANUFACTURING:
            fields: tuple[tuple[str, StackupInput, str], ...] = (
                ("param-copper-weight", "copper_oz", text("design.unit.oz")),
                ("param-board-thickness", "board_thickness_mm", text("design.unit.mm")),
            )
            for name, field, unit in fields:
                edit = QLineEdit()
                edit.setObjectName(name)
                edit.setPlaceholderText(unit)
                edit.editingFinished.connect(lambda e=edit, f=field: self._stackup_input(e, f))
                StepKeys(edit, STACKUP_INPUT_RULES[name])
                form.addRow(label_above(text(f"{name}.label"), edit, unit))
                self.helpers[name] = edit
            error = QLabel()
            error.setObjectName("param-board-thickness-error")
            error.setProperty("class", "field-error")
            error.setWordWrap(True)
            error.setVisible(False)
            form.addRow(error)
            self.helpers["param-board-thickness-error"] = error

    def build(self) -> None:
        """Add the rows, the bore choice after the outline rows and the empty screw table."""
        super().build()
        outline = self._body.findChild(QGroupBox, "tab-board-group-outline")
        if outline is not None and hasattr(self, "_pending_bore"):
            form = outline.layout()
            assert isinstance(form, QFormLayout)
            names = [form.itemAt(i, QFormLayout.ItemRole.SpanningRole) for i in range(form.rowCount())]
            first_bore = next(
                (i for i, item in enumerate(names) if item and _name(item.widget()).startswith("param-bore-")),
                form.rowCount(),
            )
            form.insertRow(first_bore, self._pending_bore)
        self._layout.insertWidget(2, self._fasteners())

    def _fasteners(self) -> QGroupBox:
        box = QGroupBox(text("design.group.fasteners"))
        box.setObjectName("tab-board-group-fasteners")
        table = table_widget(0, len(SCREW_COLUMNS))
        table.setObjectName("screw-table")
        table.setHorizontalHeaderLabels([text(f"screw-table.{key}") for _, key in SCREW_COLUMNS])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.itemChanged.connect(self._edit_cell)
        table.itemSelectionChanged.connect(self.refresh_helpers)
        add = QPushButton()
        add.setObjectName("btn-screw-add")
        add.setText(text("btn-screw-add.label"))
        add.setAccessibleName(text("btn-screw-add.name"))
        add.clicked.connect(self.session.add_screw_pattern)
        remove = QPushButton()
        remove.setObjectName("btn-screw-remove")
        remove.setText(text("btn-screw-remove.label"))
        remove.setAccessibleName(text("btn-screw-remove.name"))
        remove.clicked.connect(lambda: self.session.remove_screw_pattern(table.currentRow()))
        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        column = QVBoxLayout(box)
        column.addWidget(table)
        column.addLayout(buttons)
        self.helpers.update({"screw-table": table, "btn-screw-remove": remove})
        for widget_id, leaf in PATTERN_FIELDS.items():
            editor = FieldEditor(widget_id, FIELD_BY_KEY[f"{SCREWS_POINTER}/*/{leaf}"], self.session)
            column.addWidget(editor)
            self.helpers[widget_id] = editor
        return box

    def _edit_cell(self, item: QTableWidgetItem) -> None:
        document = self.session.document
        if document is None:
            return
        leaf = SCREW_COLUMNS[item.column()][0]
        spec = FIELD_BY_KEY[f"{SCREWS_POINTER}/*/{leaf}"]
        typed = item.text().strip()
        value: JsonValue = parse_text(spec, typed)
        if spec.value_type is ValueType.CHOICE:
            value = next((c for c in spec.choices if choice_text(c).lower() == typed.lower()), value)
        self.session.edit(f"{SCREWS_POINTER}/{item.row()}/{leaf}", value)

    def focus_widget(self, widget_id: str) -> bool:
        """Select the first pattern without a hole diameter before focusing its field (Go to first missing field)."""
        table = self.helpers.get("screw-table")
        document = self.session.document
        if widget_id == HOLE_WIDGET and isinstance(table, QTableWidget) and document is not None:
            patterns = screw_patterns(document.draft.values)
            first = next((k for k, pattern in enumerate(patterns) if "hole_diameter_mm" not in pattern), 0)
            table.selectRow(first)
        return super().focus_widget(widget_id)

    def _choose_bore(self, choice: str) -> None:
        document = self.session.document
        if document is None or bore_choice(document.draft.values) == choice:
            return
        if choice == "none":
            self.session.edit(BORE_POINTER, None)
        else:
            self.session.edit(BORE_POINTER, {"shape": choice})

    def _stackup_input(self, edit: QLineEdit, field: StackupInput) -> None:
        try:
            value = float(edit.text()) if edit.text().strip() else None
        except ValueError:
            return
        current = getattr(self.session.stackup_inputs(), field)
        if value != current:
            self.session.set_stackup_input(field, value)

    def refresh_helpers(self) -> None:
        """Show the bore choice, the screw patterns and the stack-up generator inputs."""
        document = self.session.document
        if document is None:
            return
        self._show_screws(document.draft.values)
        bore = self.helpers.get("param-bore")
        if isinstance(bore, QComboBox):
            choice = bore_choice(document.draft.values)
            bore.setCurrentIndex(-1 if choice is None else bore.findData(choice))
        inputs = self.session.stackup_inputs()
        for name, value in (
            ("param-copper-weight", inputs.copper_oz),
            ("param-board-thickness", inputs.board_thickness_mm),
        ):
            edit = self.helpers.get(name)
            if isinstance(edit, QLineEdit) and not edit.hasFocus():
                edit.setText("" if value is None else f"{value:.6g}")
        error = self.helpers.get("param-board-thickness-error")
        if isinstance(error, QLabel):
            error.setText("\n".join(found.message for found in self.session.stackup_issues.value))
            error.setVisible(bool(error.text()))

    def _show_screws(self, values: Mapping[str, JsonValue]) -> None:
        table, remove = self.helpers.get("screw-table"), self.helpers.get("btn-screw-remove")
        if not isinstance(table, QTableWidget) or remove is None:
            return
        patterns = screw_patterns(values)
        selected = len(patterns) - 1 if len(patterns) > table.rowCount() else table.currentRow()
        table.blockSignals(True)
        table.setRowCount(len(patterns))
        for r, pattern in enumerate(patterns):
            for c, (leaf, _) in enumerate(SCREW_COLUMNS):
                spec = FIELD_BY_KEY[f"{SCREWS_POINTER}/*/{leaf}"]
                item = QTableWidgetItem(display_text(spec, pattern.get(leaf, spec.neutral_value)))
                if spec.unit is not None:
                    item.setData(Qt.ItemDataRole.AccessibleDescriptionRole, unit_text(spec))
                table.setItem(r, c, item)
        if patterns and not 0 <= selected < len(patterns):
            selected = len(patterns) - 1
        if patterns:
            table.selectRow(selected)
        table.blockSignals(False)
        fit_rows(table)
        fit_width(table)
        table.horizontalHeader().setStretchLastSection(True)  # ruling j: no empty header cell
        remove.setEnabled(bool(patterns))
        for widget_id, leaf in PATTERN_FIELDS.items():
            editor = self.helpers[widget_id]
            assert isinstance(editor, FieldEditor)
            if patterns:
                row = self.session.item_row(widget_id, f"{SCREWS_POINTER}/{selected}/{leaf}")
                assert row is not None
                editor.show_row(row, str(self._topology))
            editor.setVisible(bool(patterns))
