"""The Examples gallery `dlg-examples`: every packaged example with its topology and source note (REQ-F-25, F-38)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
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
TITLE_WEIGHT = QFont.Weight.DemiBold  # 600 (ruling g 4)


def example_card(title: str, note: str) -> QWidget:
    """Return one gallery item: the title in text-1 weight 600 over the note in text-3 12 px (the hint style)."""
    card = QWidget()
    column = QVBoxLayout(card)
    column.setContentsMargins(8, 6, 8, 6)
    column.setSpacing(2)
    heading = QLabel(title)
    font = heading.font()
    font.setWeight(TITLE_WEIGHT)
    heading.setFont(font)
    body = QLabel(note)
    body.setProperty("class", "hint")
    body.setWordWrap(True)
    column.addWidget(heading)
    column.addWidget(body)
    return card


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
        self.list.setWordWrap(True)
        for info in list_examples():
            topology = text(f"topology.{info.topology.value}")
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, info.example_id)
            item.setData(Qt.ItemDataRole.AccessibleTextRole, f"{info.title}. {topology}. {info.display_note}")
            card = example_card(info.title, f"{topology}. {info.display_note}")
            item.setSizeHint(card.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, card)
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
