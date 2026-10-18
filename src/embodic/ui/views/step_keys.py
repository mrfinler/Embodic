"""Up and Down in a numeric line edit (DEF-US11-04, DEF-US12-02; design_spec.md section 10)."""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit

from embodic.ui.viewmodels.stepping import SHIFT_STEPS, StepRule, stepped_text

_DIRECTION = {Qt.Key.Key_Up.value: 1, Qt.Key.Key_Down.value: -1}
_STEPS = {Qt.KeyboardModifier.NoModifier: 1, Qt.KeyboardModifier.ShiftModifier: SHIFT_STEPS}


def step_field(edit: QLineEdit, event: QEvent, rule: StepRule | None) -> bool:
    """Step ``edit`` on Up or Down (Shift: ten steps) and return True when the key is consumed.

    The key is consumed even when the text does not change: a QLineEdit lets Up and Down through, and the inspector
    scrolled by 20 px (DEF-US12-02). The new text goes in with `insert`, as typing does. `textEdited` then starts the
    300 ms preview wait, the field stays modified so a preview result does not overwrite the step, and Ctrl+Z in the
    field brings back the text before it (fix_wave_f2.md (b)). `setText` does none of the three.
    """
    if rule is None or event.type() != QEvent.Type.KeyPress or not isinstance(event, QKeyEvent):
        return False
    direction = _DIRECTION.get(event.key())
    count = _STEPS.get(event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier)
    if direction is None or count is None:
        return False
    stepped = stepped_text(rule, edit.text(), direction * count)
    if stepped is not None:
        edit.selectAll()
        edit.insert(stepped)
    return True


class StepKeys(QObject):
    """Steps a numeric line edit that is no field row, with a fixed rule (the stack-up generator inputs)."""

    def __init__(self, edit: QLineEdit, rule: StepRule) -> None:
        super().__init__(edit)
        self._rule = rule
        edit.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 (Qt override)
        """Step the edit on Up and Down; every other event goes on."""
        return isinstance(watched, QLineEdit) and step_field(watched, event, self._rule)
