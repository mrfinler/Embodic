"""``dlg-guide``: guide topics, the equation register, status labels and keyboard shortcuts (screens.md section 12).

Non-modal. Every EQ chip opens it at its register entry; F1 opens it at the topic named by the focused widget's
``whatsThis`` (an EQ-ID or a topic id).
"""

import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QTextBrowser, QTreeWidget, QTreeWidgetItem, QWidget

from embodic.results import Registry
from embodic.ui.strings import text
from embodic.ui.strings.results import KEYBOARD_MAP
from embodic.ui.viewmodels.results import START_TOPIC, GuideTopic, guide_groups

TOPIC_ROLE = Qt.ItemDataRole.UserRole


def topic_html(topic: GuideTopic) -> str:
    """Return the body of a topic: its title, then one row per (heading, text), all escaped."""
    rows = "".join(
        f"<tr><th align='left' valign='top'>{html.escape(head)}</th><td>{html.escape(value)}</td></tr>"
        if head
        else f"<tr><td colspan='2'>{html.escape(value)}</td></tr>"
        for head, value in topic.rows
    )
    return f"<h2>{html.escape(topic.title)}</h2><table cellspacing='6'>{rows}</table>"


class GuideWindow(QWidget):
    """The guide and reference window."""

    def __init__(self, registry: Registry, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.WindowType.Window)
        self.setObjectName("dlg-guide")
        self.setWindowTitle(text("guide.title"))
        self.topics: dict[str, GuideTopic] = {}
        self.items: dict[str, QTreeWidgetItem] = {}
        self.toc = QTreeWidget()
        self.toc.setObjectName("guide-toc")
        self.toc.setHeaderHidden(True)
        self.body = QTextBrowser()
        self.body.setObjectName("guide-body")
        self.body.setOpenLinks(False)
        for group in guide_groups(registry, KEYBOARD_MAP):
            parent_item = QTreeWidgetItem([group.title])
            self.toc.addTopLevelItem(parent_item)
            for topic in group.topics:
                item = QTreeWidgetItem([topic.title])
                item.setData(0, TOPIC_ROLE, topic.topic_id)
                parent_item.addChild(item)
                self.topics[topic.topic_id] = topic
                self.items[topic.topic_id] = item
        self.toc.currentItemChanged.connect(self._item_changed)
        splitter = QSplitter()
        splitter.addWidget(self.toc)
        splitter.addWidget(self.body)
        splitter.setStretchFactor(1, 1)
        QHBoxLayout(self).addWidget(splitter)
        self.resize(900, 600)
        self.show_topic(START_TOPIC)

    def show_topic(self, topic_id: str) -> None:
        """Select a topic in the tree and show its body; an unknown id shows the start topic."""
        item = self.items.get(topic_id) or self.items[START_TOPIC]
        self.toc.setCurrentItem(item)
        self.toc.scrollToItem(item)
        self._show(item)

    def current_topic(self) -> str:
        """Return the id of the topic on show."""
        item = self.toc.currentItem()
        return str(item.data(0, TOPIC_ROLE)) if item is not None else START_TOPIC

    def _item_changed(self, item: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None) -> None:
        if item is not None and item.data(0, TOPIC_ROLE):
            self._show(item)

    def _show(self, item: QTreeWidgetItem) -> None:
        self.body.setHtml(topic_html(self.topics[str(item.data(0, TOPIC_ROLE))]))
