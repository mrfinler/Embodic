"""The Board and rotor tab (`tab-board`, screens.md section 5): outline, bore, stack-up, rules, rotor, operation."""

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel, QLineEdit, QVBoxLayout

from embodic.model.fields import FieldGroup
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import BORE_POINTER, DesignSession, bore_choice
from embodic.ui.views.coil_panel import FieldPanel, choice_text

BORE_CHOICES = ("none", "circle", "polygon")


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
            for name, field in (("param-copper-weight", "copper_oz"), ("param-board-thickness", "board_thickness_mm")):
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
                (i for i, item in enumerate(names) if item and item.widget().objectName().startswith("param-bore-")),
                form.rowCount(),
            )
            form.insertRow(first_bore, *self._pending_bore)
        fasteners = QGroupBox("Fasteners")
        fasteners.setObjectName("tab-board-group-fasteners")
        screws = QLabel(text("screw-table.empty"))
        screws.setObjectName("screw-table")
        screws.setProperty("class", "hint")
        screws.setWordWrap(True)
        QVBoxLayout(fasteners).addWidget(screws)
        self._layout.insertWidget(2, fasteners)

    def _choose_bore(self, choice: str) -> None:
        document = self.session.document
        if document is None or bore_choice(document.draft.values) == choice:
            return
        if choice == "none":
            self.session.edit(BORE_POINTER, None)
        else:
            self.session.edit(BORE_POINTER, {"shape": choice})

    def _stackup_input(self, edit: QLineEdit, field: str) -> None:
        try:
            value = float(edit.text()) if edit.text().strip() else None
        except ValueError:
            return
        current = getattr(self.session.stackup_inputs(), field)
        if value != current:
            self.session.set_stackup_input(**{field: value})

    def refresh_helpers(self) -> None:
        """Show the bore choice and the stack-up generator inputs."""
        document = self.session.document
        if document is None:
            return
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
