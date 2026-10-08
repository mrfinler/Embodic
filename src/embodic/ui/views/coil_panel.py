"""The Coil tab, and the field-table-driven row widgets every inspector tab is built from (screens.md section 2).

A row binds to one `FieldSpec` through its `widget_id` and shows label, input, unit, provenance chip and message.
What a row shows comes from `DesignSession.rows()`; a row only parses the typed text and calls `DesignSession.edit`.
"""

from collections.abc import Mapping

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from embodic.errors import IssueCategory, Severity
from embodic.model.fields import FieldGroup, FieldSpec
from embodic.model.provenance import MeasuredValue
from embodic.model.schema import JsonValue, ValueType
from embodic.ui.strings import STRINGS, text
from embodic.ui.viewmodels.session import (
    DesignSession,
    FieldRow,
    SessionComputed,
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


class FieldEditor(QWidget):
    """One inspector row: label, input (objectName = widget_id), unit, provenance chip, message and hint."""

    def __init__(self, widget_id: str, spec: FieldSpec, session: DesignSession) -> None:
        super().__init__()
        self.widget_id, self.spec, self.session = widget_id, spec, session
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
        line = QHBoxLayout()
        line.setContentsMargins(0, 0, 0, 0)
        line.addWidget(self.input, 1)
        line.addWidget(self.unit)
        line.addWidget(self.chip)
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(2)
        column.addWidget(self.label)
        column.addLayout(line)
        column.addWidget(self.error)
        column.addWidget(self.hint)

    def _make_input(self, spec: FieldSpec) -> QWidget:
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
        return edit

    def _commit(self, value: JsonValue) -> None:
        self.session.edit(self.spec.pointer, value)

    def _commit_text(self) -> None:
        assert isinstance(self.input, QLineEdit)
        typed = self.input.text()
        if typed.strip() == self._shown:
            return
        self._commit(parse_text(self.spec, typed))

    def show_row(self, row: FieldRow, topology: str) -> None:
        """Show what the session says about this field."""
        self.spec = row.spec
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
        if isinstance(self.input, QComboBox):
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
        """Add the field rows of this tab, one group box per form group where the tab has several."""
        sections: dict[str, QFormLayout] = {}
        for row in self.session.rows():
            if row.tab != self.tab:
                continue
            title = text(f"design.group.{row.spec.group.value}") if row.spec.group in TITLED_GROUPS else ""
            if title not in sections:
                box = QGroupBox(title) if title else QWidget()
                box.setObjectName(f"{self.tab}-group-{row.spec.group.value}")
                sections[title] = QFormLayout(box)
                self._layout.addWidget(box)
                self.add_helpers(row.spec.group, sections[title])
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
    """Fill hint labels from the outcome of the current design; hide them while there is none or it is stale."""
    state = session.state.value
    outcome = state.outcome if isinstance(state, SessionComputed) and not state.stale else None
    hints = feasibility_hints(outcome) if outcome is not None else {}
    for name, label in labels.items():
        label.setText(hints.get(name, ""))
        label.setVisible(name in hints)
