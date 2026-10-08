"""The Examples gallery `dlg-examples`: every packaged example with its topology and source note (REQ-F-25, F-38)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from embodic.io.examples import list_examples
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import DesignSession

MIN_SIZE_PX = (560, 400)


class ExamplesGallery(QDialog):
    """Lists `list_examples()`; loading one opens it as a new design whose values carry `example` chips."""

    def __init__(self, session: DesignSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("dlg-examples")
        self.setWindowTitle(text("dlg-examples.title"))
        self.setMinimumSize(*MIN_SIZE_PX)
        intro = QLabel(text("dlg-examples.intro"))
        intro.setProperty("class", "hint")
        intro.setWordWrap(True)
        self.list = QListWidget()
        self.list.setObjectName("examples-list")
        self.list.setAccessibleName(text("examples-list.accessible"))
        for info in list_examples():
            topology = text(f"topology.{info.topology.value}")
            item = QListWidgetItem(f"{info.title}\n{topology}. {info.source_note}")
            item.setData(Qt.ItemDataRole.UserRole, info.example_id)
            item.setToolTip(info.source_note)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        self.list.itemActivated.connect(lambda _item: self.load_selected())
        self.load = QPushButton(text("dlg-examples.load"))
        self.load.setObjectName("btn-load-example")
        self.load.setProperty("class", "primary")
        self.load.setDefault(True)
        self.load.clicked.connect(self.load_selected)
        cancel = QPushButton(text("dlg-examples.cancel"))
        cancel.setObjectName("btn-cancel-examples")
        cancel.clicked.connect(self.reject)
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(cancel)
        actions.addWidget(self.load)
        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addWidget(self.list, 1)
        layout.addLayout(actions)

    def example_ids(self) -> list[str]:
        """Return the example ids in list order."""
        return [self.list.item(row).data(Qt.ItemDataRole.UserRole) for row in range(self.list.count())]

    def load_selected(self) -> None:
        """Load the selected example into the session and close."""
        item = self.list.currentItem()
        if item is None:
            return
        self.session.load_example(item.data(Qt.ItemDataRole.UserRole))
        self.accept()
