"""The DRC tab (screens.md section 7) and Locate: zoom the canvas to a failure, dim copper, draw the ink marker."""

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPainterPath, QPen, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsSimpleTextItem,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.viewmodels.results import DrcRow, DrcTable
from embodic.ui.views.geometry_view import DATA_KIND, GeometryView
from embodic.ui.views.status_badge import repolish
from embodic.ui.views.style import themed_icon

COLUMNS = ("number", "severity", "rule", "message", "measured", "required", "layer")
LOCATED_COPPER_OPACITY = 0.35
LOCATE_ZOOM = 12.0
MARKER_RADIUS_PX = 10
FAIL_BORDER_PX = 4


class _FailBorder(QStyledItemDelegate):
    """Draws the 4 px fail border on the first cell of a failing row (screens.md section 7)."""

    def __init__(self, colour: QColor) -> None:
        super().__init__()
        self.colour = colour

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> None:
        super().paint(painter, option, index)
        if index.column() == 0:
            painter.fillRect(option.rect.adjusted(0, 0, FAIL_BORDER_PX - option.rect.width(), 0), self.colour)


class _DrcTableView(QTableView):
    """The violations table; Enter locates the selected row."""

    locate = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt override)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.locate.emit()
            return
        super().keyPressEvent(event)


class DrcTab(QWidget):
    """``tab-drc``: summary with icon, violations table, Locate and the D-006 rule note."""

    locate_requested = Signal(object)  # DrcRow

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("tab-drc")
        self.tokens: ThemeTokens | None = None
        self.table_data: DrcTable | None = None
        self.icon = QLabel()
        self.icon.setObjectName("drc-summary-icon")
        self.summary = QLabel(text("drc.empty"))
        self.summary.setObjectName("drc-summary")
        self.summary.setProperty("class", "check-state")
        self.note = QLabel()
        self.note.setObjectName("drc-truncated")
        self.note.setProperty("class", "hint")
        self.model = QStandardItemModel(0, len(COLUMNS))
        self.model.setHorizontalHeaderLabels([text(f"drc.column.{c}") for c in COLUMNS])
        self.table = _DrcTableView()
        self.table.setObjectName("drc-table")
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.table.horizontalHeader().setSectionResizeMode(COLUMNS.index("message"), QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(lambda _: self.locate_selected())
        self.table.locate.connect(self.locate_selected)
        self.locate = QPushButton(text("drc.locate"))
        self.locate.setObjectName("btn-drc-locate")
        self.locate.setEnabled(False)
        self.locate.clicked.connect(self.locate_selected)
        self.table.selectionModel().selectionChanged.connect(
            lambda *_: self.locate.setEnabled(self.selected_row() is not None)
        )
        rule = QLabel(text("drc.rule-note"))
        rule.setObjectName("drc-rule-note")
        rule.setProperty("class", "hint")
        head = QHBoxLayout()
        head.addWidget(self.icon)
        head.addWidget(self.summary, 1)
        head.addWidget(self.locate)
        layout = QVBoxLayout(self)
        layout.addLayout(head)
        layout.addWidget(self.note)
        layout.addWidget(self.table, 1)
        layout.addWidget(rule)

    def show_table(self, table: DrcTable | None, tokens: ThemeTokens) -> None:
        """Show the DRC result of the outcome on screen, or the empty state."""
        if table == self.table_data and tokens is self.tokens:
            return
        self.table_data, self.tokens = table, tokens
        self.table.setItemDelegate(_FailBorder(QColor(tokens.colours["status-fail"])))
        state = "warn" if table is None else table.state
        self.summary.setText(text("drc.empty") if table is None else table.summary)
        self.summary.setProperty("state", {"not-run": "warn"}.get(state, state))
        repolish(self.summary)
        icon = themed_icon(
            "check-pass" if state == "pass" else "check-fail" if state == "fail" else "check-warn", tokens
        )
        self.icon.setVisible(table is not None and icon is not None)
        if icon is not None:
            self.icon.setPixmap(icon.pixmap(16, 16))
        note = table.note if table is not None else None
        self.note.setVisible(note is not None)
        self.note.setText(note or "")
        rows = table.rows if table is not None else ()
        self.model.setRowCount(0)
        fail_icon = themed_icon("check-fail", tokens)
        for row in rows:
            cells = [QStandardItem(str(row.number)), QStandardItem(text("drc.severity.error"))]
            cells += [QStandardItem(v) for v in (row.rule_code, row.message, row.measured_text, row.required_text)]
            cells.append(QStandardItem(row.layer_text))
            cells[3].setToolTip(row.message)
            if fail_icon is not None:
                cells[1].setIcon(fail_icon)
            cells[0].setData(row, Qt.ItemDataRole.UserRole)
            cells[0].setData("fail", Qt.ItemDataRole.UserRole + 1)
            self.model.appendRow(cells)
        self.table.resizeColumnsToContents()
        self.locate.setEnabled(False)

    def selected_row(self) -> DrcRow | None:
        """Return the selected violation."""
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        row = self.model.item(indexes[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return row if isinstance(row, DrcRow) else None

    def locate_selected(self) -> None:
        """Ask the window to show the selected failure on the canvas."""
        row = self.selected_row()
        if row is not None:
            self.locate_requested.emit(row)


def locate_on_canvas(canvas: GeometryView, row: DrcRow, tokens: ThemeTokens) -> None:
    """Zoom the canvas to a failure, dim copper to 35 % and draw the ink marker with its number (design_spec 3.1).

    The marker uses ``text-1`` with a ``canvas`` halo, never a status colour, so it cannot read as phase A copper.
    The next redraw of the canvas clears it.
    """
    scene = canvas.scene()
    for item in scene.items():
        kind = item.data(DATA_KIND)
        if kind == "drc-marker":
            scene.removeItem(item)
        elif kind == "copper":
            item.setOpacity(LOCATED_COPPER_OPACITY)
    x, y = row.at_mm[0], -row.at_mm[1]
    ring = QPainterPath()
    ring.addEllipse(QRectF(-MARKER_RADIUS_PX, -MARKER_RADIUS_PX, 2 * MARKER_RADIUS_PX, 2 * MARKER_RADIUS_PX))
    ink, halo = QColor(tokens.colours["text-1"]), QColor(tokens.colours["canvas"])
    marker = QGraphicsPathItem(ring)
    marker.setPen(QPen(halo, 6))
    marker.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
    marker.setPos(x, y)
    marker.setZValue(1_000)
    marker.setData(DATA_KIND, "drc-marker")
    QGraphicsPathItem(ring, marker).setPen(QPen(ink, 2))
    number = QGraphicsSimpleTextItem(str(row.number), marker)
    number.setBrush(ink)
    number.setPos(MARKER_RADIUS_PX + 20, -8)
    icon = themed_icon("check-fail", tokens)
    if icon is not None:
        QGraphicsPixmapItem(icon.pixmap(16, 16), marker).setPos(MARKER_RADIUS_PX + 2, -8)
    scene.addItem(marker)
    canvas.fit_view()
    canvas.zoom_by(LOCATE_ZOOM)
    canvas.centerOn(x, y)
