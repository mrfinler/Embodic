"""The Coil tab, and the field-table-driven row widgets every inspector tab is built from (screens.md section 2).

A row binds to one `FieldSpec` through its `widget_id` and shows label, input, unit, provenance chip and message.
What a row shows comes from `DesignSession.rows()`; a row only parses the typed text and calls `DesignSession.edit`.
"""

from collections.abc import Callable, Mapping, Sequence

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QScrollArea,
    QTableWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from embodic.errors import IssueCategory, Severity
from embodic.model.fields import FieldGroup, FieldKind, FieldSpec
from embodic.model.provenance import MeasuredValue
from embodic.model.schema import Choice, JsonValue, ValueType
from embodic.ui.strings import STRINGS, text
from embodic.ui.viewmodels.session import (
    TAB_OF_GROUP,
    DesignSession,
    FieldRow,
    display_text,
    feasibility_hints,
    parse_text,
)

MIN_INPUT_PX = 72
TITLED_GROUPS = frozenset(
    {
        FieldGroup.OUTLINE,
        FieldGroup.FASTENERS,
        FieldGroup.STACKUP,
        FieldGroup.MANUFACTURING,
        FieldGroup.ROTOR,
        FieldGroup.OPERATING,
        FieldGroup.DRIVE,
        FieldGroup.COOLING,
    }
)
# Choice fields that screens.md sections 2 to 5 draw as an exclusive QToolButton segment; other choices are combo boxes.
SEGMENT_WIDGETS = frozenset(
    {
        "param-side-style",
        "param-end-style",
        "param-x-inward-sense",
        "param-phase-count",
        "param-connection",
        "param-phase-sequence",
        "param-terminal-location",
        "param-pair-connection",
        "param-stack-mode",
        "param-outline-shape",
        "param-magnet-shape",
    }
)


def repolish(widget: QWidget) -> None:
    """Re-apply the style sheet after a dynamic property changed (design_spec.md section 8)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def label_text(widget_id: str, topology: str, variant: str | None = None) -> str:
    """Return a field label: topology- or variant-specific when the catalogue has one."""
    for key in (f"{widget_id}.label.{topology}", f"{widget_id}.label.{variant}", f"{widget_id}.label"):
        if key in STRINGS:
            return STRINGS[key]
    return widget_id


def choice_text(value: JsonValue) -> str:
    """Return the English label of a choice value."""
    return STRINGS.get(f"design.choice.{value}", str(value))


def unit_text(spec: FieldSpec) -> str:
    """Return the unit shown next to an input; angles show in degrees."""
    return "" if spec.unit is None else STRINGS.get(f"design.unit.{spec.unit.value}", spec.unit.value)


class _NoWheelWithoutFocus(QObject):
    """The wheel never changes a value the user is not editing (design_spec.md section 10)."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 (Qt override)
        return event.type() == QEvent.Type.Wheel and isinstance(watched, QWidget) and not watched.hasFocus()


_WHEEL_GUARD = _NoWheelWithoutFocus()


class Segment(QWidget):
    """An exclusive QToolButton segment: the widget id names the row, `<id>-<choice>` names each button."""

    def __init__(self, widget_id: str, choices: Sequence[Choice], on_choose: Callable[[Choice], None]) -> None:
        super().__init__()
        self.setObjectName(widget_id)
        self.group = QButtonGroup(self)
        self.buttons: dict[Choice, QToolButton] = {}
        line = QHBoxLayout(self)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(2)
        for choice in choices:
            button = QToolButton()
            button.setObjectName(f"{widget_id}-{choice}")
            button.setText(choice_text(choice))
            button.setCheckable(True)
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.clicked.connect(lambda _checked=False, value=choice: on_choose(value))
            self.group.addButton(button)
            self.buttons[choice] = button
            line.addWidget(button)
        line.addStretch(1)
        self.setFocusProxy(self.buttons[choices[0]])

    def show_value(self, value: JsonValue) -> None:
        """Check the button of a value; a value no button has (a required segment not chosen yet) checks none."""
        self.group.setExclusive(False)
        for choice, button in self.buttons.items():
            button.setChecked(choice == value)
        self.group.setExclusive(True)
        checked = next((button for choice, button in self.buttons.items() if choice == value), None)
        self.setFocusProxy(checked or next(iter(self.buttons.values())))

    def value(self) -> Choice | None:
        """Return the checked choice, or None."""
        return next((choice for choice, button in self.buttons.items() if button.isChecked()), None)


class FieldEditor(QWidget):
    """One inspector row: label, input (objectName = widget_id), unit, provenance chip, message and hint."""

    def __init__(self, widget_id: str, spec: FieldSpec, session: DesignSession) -> None:
        super().__init__()
        self.widget_id, self.spec, self.session = widget_id, spec, session
        self.pointer = spec.pointer
        self._present = False
        self.setObjectName(f"{widget_id}-row")
        self._shown = ""
        self.label = QLabel()
        self.label.setObjectName(f"{widget_id}-label")
        self.label.setWordWrap(True)
        self.input = self._make_input(spec)
        self.input.setObjectName(widget_id)
        self.label.setBuddy(self.input)
        self.unit = QLabel(unit_text(spec))
        self.unit.setObjectName(f"{widget_id}-unit")
        self.unit.setProperty("class", "unit")
        self.chip = QLabel()
        self.chip.setObjectName(f"{widget_id}-prov")
        self.chip.setProperty("class", "prov-chip")
        self.error = QLabel()
        self.error.setObjectName(f"{widget_id}-error")
        self.error.setProperty("class", "field-error")
        self.error.setWordWrap(True)
        self.hint = QLabel()
        self.hint.setObjectName(f"{widget_id}-hint")
        self.hint.setProperty("class", "hint")
        self.hint.setWordWrap(True)
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.addWidget(self.label, 1)
        line = QHBoxLayout()
        line.setContentsMargins(0, 0, 0, 0)
        line.addWidget(self.input, 1)
        line.addWidget(self.unit)
        # A segment needs the row's full width ("Single board", "One board per phase"), so its chip moves up a line.
        (head if isinstance(self.input, Segment) else line).addWidget(self.chip)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(2)
        column.addLayout(head)
        column.addLayout(line)
        column.addWidget(self.error)
        column.addWidget(self.hint)

    def _make_input(self, spec: FieldSpec) -> QWidget:
        if spec.value_type is ValueType.CHOICE and self.widget_id in SEGMENT_WIDGETS:
            return Segment(self.widget_id, spec.choices, self._commit)
        if spec.value_type is ValueType.CHOICE:
            box = QComboBox()
            box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            box.setMinimumContentsLength(8)
            box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            box.installEventFilter(_WHEEL_GUARD)
            for choice in spec.choices:
                box.addItem(choice_text(choice), choice)
            box.activated.connect(lambda index: self._commit(box.itemData(index)))
            return box
        if spec.value_type is ValueType.BOOL:
            check = QCheckBox()
            check.clicked.connect(lambda checked: self._commit(bool(checked)))
            return check
        edit = QLineEdit()
        edit.setMinimumWidth(MIN_INPUT_PX)
        edit.editingFinished.connect(self._commit_text)
        if spec.kind is FieldKind.PROPERTY and spec.value_type is ValueType.FLOAT:
            edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            edit.customContextMenuRequested.connect(lambda pos: self._show_context_menu(edit, pos))
        return edit

    def _commit(self, value: JsonValue) -> None:
        self.session.edit(self.pointer, value)

    def context_menu(self) -> QMenu:
        """Return the input's edit menu plus "Mark as measured" for a property field (D-007, screens.md conventions)."""
        assert isinstance(self.input, QLineEdit)
        menu = self.input.createStandardContextMenu()
        menu.addSeparator()
        action = menu.addAction(text("design.mark-measured"))
        action.setObjectName(f"{self.widget_id}-mark-measured")
        action.setEnabled(self._present)
        action.triggered.connect(self._ask_source)
        return menu

    def _show_context_menu(self, edit: QLineEdit, pos: QPoint) -> None:
        self.context_menu().exec(edit.mapToGlobal(pos))

    def _ask_source(self) -> None:
        source, accepted = QInputDialog.getText(
            self, text("design.mark-measured.title"), text("design.mark-measured.prompt")
        )
        if accepted:
            self.mark_measured(source)

    def mark_measured(self, source: str) -> None:
        """Mark this field measured with its source; a refusal shows its message under the field."""
        refused = self.session.mark_measured(self.pointer, source)
        if refused is not None:
            self.error.setText(refused.message)
            self.error.setVisible(True)

    def _commit_text(self) -> None:
        assert isinstance(self.input, QLineEdit)
        typed = self.input.text()
        if typed.strip() == self._shown:
            return
        self._commit(parse_text(self.spec, typed))

    def show_row(self, row: FieldRow, topology: str) -> None:
        """Show what the session says about this field."""
        self.spec, self.pointer, self._present = row.spec, row.pointer, row.present
        self.setVisible(row.visible)
        self.input.setEnabled(row.enabled)
        self.label.setText(label_text(self.widget_id, topology, str(row.spec.variant)))
        self.unit.setText(unit_text(row.spec))
        self._show_value(row)
        self._show_chip(row)
        self._show_message(row)
        self.input.setAccessibleName(self.label.text())
        self.input.setAccessibleDescription(" ".join(t for t in (self.unit.text(), self.hint.text()) if t))

    def _show_value(self, row: FieldRow) -> None:
        if isinstance(self.input, Segment):
            self.input.show_value(row.value if row.present or not row.spec.required else None)
        elif isinstance(self.input, QComboBox):
            self.input.blockSignals(True)
            self.input.setCurrentIndex(self.input.findData(row.value) if row.present or not row.spec.required else -1)
            self.input.setPlaceholderText(text("design.required.hint"))
            self.input.blockSignals(False)
        elif isinstance(self.input, QCheckBox):
            self.input.blockSignals(True)
            self.input.setChecked(bool(row.value))
            self.input.blockSignals(False)
        else:
            assert isinstance(self.input, QLineEdit)
            self._shown = display_text(row.spec, row.value)
            if self.input.text() != self._shown and not (self.input.hasFocus() and self.input.isModified()):
                self.input.setText(self._shown)
            self.input.setPlaceholderText(unit_text(row.spec) if row.spec.required else "")

    def _show_chip(self, row: FieldRow) -> None:
        chip = row.provenance
        self.chip.setVisible(chip is not None)
        if chip is not None:
            self.chip.setText(text(f"design.prov.{chip.provenance.value}"))
            self.chip.setProperty("provenance", chip.provenance.value)
            tip = text("design.prov.measured-tooltip", source=chip.source) if isinstance(chip, MeasuredValue) else ""
            self.chip.setToolTip(tip)
            repolish(self.chip)

    def _show_message(self, row: FieldRow) -> None:
        found = row.issue
        hint = row.hint
        if not row.present and row.spec.required:
            hint = text("design.required.hint") + (f" {hint}" if hint else "")
        invalid = found is not None and found.category is IssueCategory.INVALID
        if found is not None and found.severity is Severity.INFO:
            hint, found = found.message, None
        self.error.setVisible(found is not None)
        if found is not None:
            warning = found.severity is Severity.WARNING
            self.error.setText(text("design.warning.prefix", message=found.message) if warning else found.message)
            self.error.setProperty("state", "warn" if warning else "")
            repolish(self.error)
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))
        self.input.setProperty("invalid", "true" if invalid else "false")
        repolish(self.input)


class FieldPanel(QScrollArea):
    """One inspector tab: the field rows of that tab for the open topology, in form order, plus its helpers."""

    def __init__(self, tab: str, session: DesignSession) -> None:
        super().__init__()
        self.tab, self.session = tab, session
        self.setObjectName(tab)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # the inputs inside take focus, the scroll area does not
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.editors: dict[str, FieldEditor] = {}
        self.helpers: dict[str, QWidget] = {}
        self._topology: str | None = None
        self._body = QWidget()
        self._layout = QVBoxLayout(self._body)
        self.setWidget(self._body)
        self.empty = QLabel(text("inspector.empty"))
        self.empty.setObjectName(f"{tab}-empty")
        self.empty.setProperty("class", "hint")
        self.empty.setWordWrap(True)
        self._layout.addWidget(self.empty)
        self._layout.addStretch(1)

    def refresh(self) -> None:
        """Rebuild for a new topology, then show the session's rows."""
        document = self.session.document
        topology = None if document is None else document.draft.topology.value
        if topology != self._topology:
            self._rebuild(topology)
        if document is None:
            return
        for row in self.session.rows():
            if row.widget_id in self.editors:
                self.editors[row.widget_id].show_row(row, document.draft.topology.value)
        self.refresh_helpers()

    def _rebuild(self, topology: str | None) -> None:
        self._topology = topology
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item is not None and (widget := item.widget()) is not None and widget is not self.empty:
                widget.setParent(None)
                widget.deleteLater()
        self.editors, self.helpers = {}, {}
        self.empty.setVisible(topology is None)
        self._layout.addWidget(self.empty)
        if topology is not None:
            self.build()
        self._layout.addStretch(1)
        # A widget added to a shown layout appears only after a queued show; show the new sections now so focus
        # and visibility queries see them at once.
        for index in range(self._layout.count()):
            item = self._layout.itemAt(index)
            widget = None if item is None else item.widget()
            if widget is not None and widget is not self.empty:
                widget.show()

    def build(self) -> None:
        """Add the field rows of this tab, one group box per form group where the tab has several.

        A field placed on another tab than its group's (Poles on the Coil tab) joins that tab's untitled section.
        """
        sections: dict[str, QFormLayout] = {}
        for row in self.session.rows():
            if row.tab != self.tab:
                continue
            group = row.spec.group
            titled = group in TITLED_GROUPS and TAB_OF_GROUP.get(group) == self.tab
            title = text(f"design.group.{group.value}") if titled else ""
            if title not in sections:
                box = QGroupBox(title) if title else QWidget()
                box.setObjectName(f"{self.tab}-group-{group.value}")
                sections[title] = QFormLayout(box)
                self._layout.addWidget(box)
                self.add_helpers(group, sections[title])
            editor = FieldEditor(row.widget_id, row.spec, self.session)
            self.editors[row.widget_id] = editor
            sections[title].addRow(editor)

    def add_helpers(self, group: FieldGroup, form: QFormLayout) -> None:
        """Add the helper widgets of a form group before its field rows; tabs with helpers override this."""

    def refresh_helpers(self) -> None:
        """Show the session's values in the helper widgets; tabs with helpers override this."""

    def focus_widget(self, widget_id: str) -> bool:
        """Focus an input of this tab and scroll it into view; False when the tab has no such widget."""
        target = self._body.findChild(QWidget, widget_id)
        if target is None or not target.isVisibleTo(self):
            return False
        self.ensureWidgetVisible(target)
        target.setFocus(Qt.FocusReason.OtherFocusReason)
        return True

    def visible_inputs(self) -> set[str]:
        """Return the objectNames of the field inputs this tab shows (UI-28)."""
        return {widget_id for widget_id, editor in self.editors.items() if editor.isVisibleTo(self)}


def fit_rows(table: QTableWidget) -> None:
    """Size a table to its rows, so the inspector scrolls instead of the table showing empty space."""
    chrome = table.horizontalHeader().sizeHint().height() + table.horizontalScrollBar().sizeHint().height()
    table.setFixedHeight(chrome + table.verticalHeader().length() + 2 * table.frameWidth())


def hint_label(name: str) -> QLabel:
    """Return a hint label with an objectName, for feasibility and pattern text."""
    label = QLabel()
    label.setObjectName(name)
    label.setProperty("class", "hint")
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class CoilPanel(FieldPanel):
    """The Coil tab (`tab-coil`) with the coil-combination and turns hints of the last compute (UI-19)."""

    def __init__(self, session: DesignSession) -> None:
        super().__init__("tab-coil", session)

    def build(self) -> None:
        """Add the coil rows and the feasibility hints under them."""
        super().build()
        self.hints = {name: hint_label(name) for name in ("hint-combination", "param-turns-hint")}
        for label in self.hints.values():
            self._layout.addWidget(label)

    def refresh_helpers(self) -> None:
        """Show the hints that follow the winding plan of the last compute."""
        show_hints(self.hints, self.session)


def show_hints(labels: Mapping[str, QLabel], session: DesignSession) -> None:
    """Fill hint labels from the result of the current design; hide them while there is none (computing, outdated)."""
    outcome = session.current_outcome()
    hints = feasibility_hints(outcome) if outcome is not None else {}
    for name, label in labels.items():
        label.setText(hints.get(name, ""))
        label.setVisible(name in hints)
