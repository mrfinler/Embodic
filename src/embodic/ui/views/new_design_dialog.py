"""The New design dialog `dlg-new-design` (screens.md section 1): name, topology, optional example."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from embodic.io.examples import list_examples
from embodic.model.vocabulary import TopologyKind
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import DesignSession

MIN_SIZE_PX = (560, 400)


class NewDesignDialog(QDialog):
    """Names the design and fixes its topology; every value is entered in the inspector afterwards."""

    def __init__(
        self, session: DesignSession, parent: QWidget | None = None, confirm_replace: Callable[[], bool] | None = None
    ) -> None:
        super().__init__(parent)
        self.session = session
        self._confirm_replace = confirm_replace or self._ask_replace
        self.setObjectName("dlg-new-design")
        self.setWindowTitle(text("dlg-new-design.title"))
        self.setMinimumSize(*MIN_SIZE_PX)
        self.examples = list_examples()
        intro = QLabel(text("dlg-new-design.intro"))
        intro.setProperty("class", "hint")
        intro.setWordWrap(True)
        self.name = QLineEdit()
        self.name.setObjectName("param-design-name")
        self.name.setPlaceholderText(text("param-design-name.placeholder"))
        self.name.textChanged.connect(self._update)
        self.topology_box = QWidget()
        self.topology_box.setObjectName("param-topology")
        self.topology_group = QButtonGroup(self)
        self.topology_group.setExclusive(True)
        self.topology_buttons: dict[TopologyKind, QToolButton] = {}
        buttons = QHBoxLayout(self.topology_box)
        buttons.setContentsMargins(0, 0, 0, 0)
        for topology in TopologyKind:
            button = QToolButton()
            button.setObjectName(f"param-topology-{topology.value}")
            button.setText(text(f"topology.{topology.value}"))
            button.setCheckable(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            self.topology_group.addButton(button)
            self.topology_buttons[topology] = button
            buttons.addWidget(button)
        self.topology_group.buttonToggled.connect(lambda *_: self._update())
        self.topology_hint = QLabel(text("param-topology.hint"))
        self.topology_hint.setObjectName("param-topology-hint")
        self.topology_hint.setProperty("class", "hint")
        self.example_picker = QComboBox()
        self.example_picker.setObjectName("example-picker")
        self.example_picker.addItem(text("example-picker.blank"), None)
        for info in self.examples:
            self.example_picker.addItem(info.title, info.example_id)
        self.example_picker.currentIndexChanged.connect(self._example_chosen)
        self.create_button = QPushButton(text("btn-create-design.label"))
        self.create_button.setObjectName("btn-create-design")
        self.create_button.setProperty("class", "primary")
        self.create_button.setDefault(True)
        self.create_button.clicked.connect(self.create_design)
        self.cancel_button = QPushButton(text("btn-cancel-new.label"))
        self.cancel_button.setObjectName("btn-cancel-new")
        self.cancel_button.clicked.connect(self.reject)
        form = QFormLayout()
        form.addRow(QLabel(text("param-design-name.label")), self.name)
        form.addRow(QLabel(text("param-topology.label")), self.topology_box)
        form.addRow(QLabel(""), self.topology_hint)
        form.addRow(QLabel(text("example-picker.label")), self.example_picker)
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.create_button)
        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(form)
        layout.addStretch(1)
        layout.addLayout(actions)
        self.name.setFocus()
        self._update()

    def chosen_topology(self) -> TopologyKind | None:
        """Return the topology button that is checked."""
        return next((t for t, button in self.topology_buttons.items() if button.isChecked()), None)

    def _example_chosen(self) -> None:
        example_id = self.example_picker.currentData()
        info = next((e for e in self.examples if e.example_id == example_id), None)
        for button in self.topology_buttons.values():
            button.setEnabled(info is None)
        if info is not None:
            self.topology_buttons[info.topology].setChecked(True)
        self._update()

    def _update(self) -> None:
        topology = self.chosen_topology()
        self.topology_hint.setVisible(topology is None)
        self.create_button.setEnabled(bool(self.name.text().strip()) and topology is not None)

    def _ask_replace(self) -> bool:
        answer = QMessageBox.question(
            self,
            text("dlg-new-design.replace.title"),
            text("dlg-new-design.replace.body"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def create_design(self) -> None:
        """Open the draft (blank, or the chosen example) in the inspector and close the dialog."""
        topology = self.chosen_topology()
        name = self.name.text().strip()
        if topology is None or not name:
            return
        if self.session.has_user_values() and not self._confirm_replace():
            return
        example_id = self.example_picker.currentData()
        if example_id is None:
            self.session.new_design(topology)
        else:
            self.session.load_example(example_id)
        self.session.edit("/name", name)
        self.accept()
