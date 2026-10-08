"""The Phases tab (`tab-phases`, screens.md section 3): connection, sequence, terminals and the phase pattern."""

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel

from embodic.model.fields import FieldGroup
from embodic.model.vocabulary import TopologyKind
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import ASSIGNMENT_POINTER, DesignSession
from embodic.ui.views.coil_panel import FieldPanel, choice_text, hint_label, show_hints


class PhasePanel(FieldPanel):
    """Phase rows from the field table, the assignment mode and the pattern of the last compute."""

    def __init__(self, session: DesignSession) -> None:
        super().__init__("tab-phases", session)

    def add_helpers(self, group: FieldGroup, form: QFormLayout) -> None:
        """Add the assignment mode (spiral): Auto writes null; manual entry is not offered in this version."""
        document = self.session.document
        if group is not FieldGroup.PHASES or document is None or document.draft.topology is not TopologyKind.SPIRAL:
            return
        mode = QComboBox()
        mode.setObjectName("param-phase-assign-mode")
        mode.addItem(choice_text("auto"), "auto")
        mode.addItem(choice_text("manual"), "manual")
        mode.model().item(1).setEnabled(False)
        mode.setToolTip(text("design.hint.manual-assignment"))
        mode.setAccessibleName(text("param-phase-assign-mode.label"))
        form.addRow(QLabel(text("param-phase-assign-mode.label")), mode)
        self.helpers["param-phase-assign-mode"] = mode

    def build(self) -> None:
        """Add the phase rows and the pattern string under them."""
        super().build()
        self.pattern = hint_label("phase-pattern-string")
        self._layout.addWidget(self.pattern)

    def refresh_helpers(self) -> None:
        """Show the assignment mode of the draft and the pattern of the last compute."""
        mode = self.helpers.get("param-phase-assign-mode")
        document = self.session.document
        if isinstance(mode, QComboBox) and document is not None:
            manual = document.draft.values.get(ASSIGNMENT_POINTER) is not None or any(
                p.startswith(ASSIGNMENT_POINTER + "/") for p in document.draft.values
            )
            mode.setCurrentIndex(1 if manual else 0)
        show_hints({"phase-pattern-string": self.pattern}, self.session)
