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
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
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
from embodic.ui.views.coil_panel import FieldEditor, FieldPanel, choice_text

BORE_CHOICES = ("none", "circle", "polygon")
HOLE_WIDGET = "param-screw-hole-diameter"
SCREW_COLUMNS = (
    ("size", "size"),
    ("fit", "fit"),
    ("hole_diameter_mm", "hole"),
    ("count", "count"),
    ("pitch_radius_mm", "pitch-radius"),
    ("angle_offset_rad", "angle-offset"),
)
_READ_ONLY_LEAF = "hole_diameter_mm"  # a required value needs its own field with unit, chip and error (screens.md 5)


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
            bore.setAccessibleName(text("param-bore.label"))
            self.helpers["param-bore"] = bore
            self._pending_bore = (QLabel(text("param-bore.label")), bore)
        if group is FieldGroup.MANUFACTURING:
            fields: tuple[tuple[str, StackupInput], ...] = (
                ("param-copper-weight", "copper_oz"),
                ("param-board-thickness", "board_thickness_mm"),
            )
            for name, field in fields:
                edit = QLineEdit()
                edit.setObjectName(name)
                edit.setPlaceholderText(text("design.unit.oz") if field == "copper_oz" else text("design.unit.mm"))
                edit.editingFinished.connect(lambda e=edit, f=field: self._stackup_input(e, f))
                edit.setAccessibleName(text(f"{name}.label"))
                form.addRow(QLabel(text(f"{name}.label")), edit)
                self.helpers[name] = edit

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
            form.insertRow(first_bore, *self._pending_bore)
        self._layout.insertWidget(2, self._fasteners())

    def _fasteners(self) -> QGroupBox:
        box = QGroupBox(text("design.group.fasteners"))
        box.setObjectName("tab-board-group-fasteners")
        table = QTableWidget(0, len(SCREW_COLUMNS))
        table.setObjectName("screw-table")
        table.setHorizontalHeaderLabels([text(f"screw-table.{key}") for _, key in SCREW_COLUMNS])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.itemChanged.connect(self._edit_cell)
        table.itemSelectionChanged.connect(self.refresh_helpers)
        add = QToolButton()
        add.setObjectName("btn-screw-add")
        add.setText(text("btn-screw-add.label"))
        add.clicked.connect(self.session.add_screw_pattern)
        remove = QToolButton()
        remove.setObjectName("btn-screw-remove")
        remove.setText(text("btn-screw-remove.label"))
        remove.clicked.connect(lambda: self.session.remove_screw_pattern(table.currentRow()))
        hole = FieldEditor(HOLE_WIDGET, FIELD_BY_KEY[f"{SCREWS_POINTER}/*/hole_diameter_mm"], self.session)
        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        column = QVBoxLayout(box)
        column.addWidget(table)
        column.addLayout(buttons)
        column.addWidget(hole)
        self.helpers.update({"screw-table": table, "btn-screw-remove": remove, HOLE_WIDGET: hole})
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
            first = next((k for k, pattern in enumerate(patterns) if _READ_ONLY_LEAF not in pattern), 0)
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

    def _show_screws(self, values: Mapping[str, JsonValue]) -> None:
        table, hole, remove = (self.helpers.get(name) for name in ("screw-table", HOLE_WIDGET, "btn-screw-remove"))
        if not isinstance(table, QTableWidget) or not isinstance(hole, FieldEditor) or remove is None:
            return
        patterns = screw_patterns(values)
        selected = len(patterns) - 1 if len(patterns) > table.rowCount() else table.currentRow()
        table.blockSignals(True)
        table.setRowCount(len(patterns))
        for r, pattern in enumerate(patterns):
            for c, (leaf, _) in enumerate(SCREW_COLUMNS):
                spec = FIELD_BY_KEY[f"{SCREWS_POINTER}/*/{leaf}"]
                value = pattern.get(leaf, spec.neutral_value)
                shown = choice_text(value) if spec.value_type is ValueType.CHOICE and value is not None else ""
                shown = shown or display_text(spec, value)
                if leaf == _READ_ONLY_LEAF and value is None:
                    shown = text("design.required.hint")
                item = QTableWidgetItem(shown)
                if leaf == _READ_ONLY_LEAF:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, c, item)
        if patterns and not 0 <= selected < len(patterns):
            selected = len(patterns) - 1
        if patterns:
            table.selectRow(selected)
        table.blockSignals(False)
        remove.setEnabled(bool(patterns))
        if patterns:
            row = self.session.item_row(HOLE_WIDGET, f"{SCREWS_POINTER}/{selected}/hole_diameter_mm")
            assert row is not None
            hole.show_row(row, str(self._topology))
        hole.setVisible(bool(patterns))
