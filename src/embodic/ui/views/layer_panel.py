"""The Layers tab (`tab-layers`, screens.md section 4): copper count, pairs and their rotation, vias, layer list."""

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from embodic.model.fields import FIELD_BY_KEY, FieldGroup
from embodic.model.vocabulary import TopologyKind
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import (
    PAIRS_POINTER,
    STACKUP_POINTER,
    DesignSession,
    RotationMode,
    alternate_rotation_rad,
    display_text,
    layer_pairs,
    pair_number,
    rotation_mode,
)
from embodic.ui.views.coil_panel import FieldEditor, FieldPanel, Segment, fit_rows

COPPER_COUNTS = (2, 4, 6, 8)
LAYER_COLUMNS = ("layer", "kind", "thickness", "pair", "rotation")
PAIR_COLUMNS = frozenset({"pair", "rotation"})  # spiral only (screens.md section 4)
ROTATION_WIDGET = "param-pair-rotation"


class LayerPanel(FieldPanel):
    """Layer rows from the field table, the copper count, the pair rotation helpers, the layer list and its notice."""

    def __init__(self, session: DesignSession) -> None:
        super().__init__("tab-layers", session)
        self._custom = False  # Custom chosen while the rotations still read as None or Alternate

    def _rebuild(self, topology: str | None) -> None:
        self._custom = False
        super()._rebuild(topology)

    def add_helpers(self, group: FieldGroup, form: QFormLayout) -> None:
        """Add the copper count before the first layer row, and for spiral the pair rotation mode and field."""
        document = self.session.document
        if group is not FieldGroup.LAYERS or document is None or "copper-count" in self.helpers:
            return
        wave = document.draft.topology is TopologyKind.WAVE
        name = "param-wave-layers" if wave else "param-layer-count"
        count = QComboBox()
        count.setObjectName(name)
        count.setPlaceholderText(text("design.required.hint"))
        for copper in COPPER_COUNTS:
            label = (
                text("param-wave-layers.parallel", count=copper, pairs=copper // 2)
                if wave and copper > 2
                else str(copper)
            )
            count.addItem(label, copper)
        count.activated.connect(lambda index: self.session.set_stackup_input("copper_count", count.itemData(index)))
        count.setAccessibleName(text(f"{name}.label"))
        form.addRow(QLabel(text(f"{name}.label")), count)
        self.helpers["copper-count"] = count
        if document.draft.topology is TopologyKind.SPIRAL:
            mode = Segment("param-rotation-mode", ("none", "alternate", "custom"), self._choose_rotation_mode)
            mode.setAccessibleName(text("param-rotation-mode.label"))
            mode_row = QWidget()
            mode_row.setObjectName("param-rotation-mode-row")
            column = QVBoxLayout(mode_row)
            column.setContentsMargins(0, 0, 0, 0)
            column.addWidget(QLabel(text("param-rotation-mode.label")))
            column.addWidget(mode)
            rotation = FieldEditor(ROTATION_WIDGET, FIELD_BY_KEY[f"{PAIRS_POINTER}/*/rotation_rad"], self.session)
            form.addRow(mode_row)
            form.addRow(rotation)
            self.helpers.update({"param-rotation-mode": mode, "param-rotation-mode-row": mode_row})
            self.helpers[ROTATION_WIDGET] = rotation

    def build(self) -> None:
        """Add the rows, then the layer list and the notice of what the last copper-count edit did to the pairs."""
        super().build()
        table = QTableWidget(0, len(LAYER_COLUMNS))
        table.setObjectName("layer-list")
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setHorizontalHeaderLabels([text(f"layer-list.{column}") for column in LAYER_COLUMNS])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.itemSelectionChanged.connect(self.refresh_helpers)
        notice = QFrame()
        notice.setObjectName("layer-pairs-notice")
        notice.setProperty("class", "notice")
        line = QHBoxLayout(notice)
        message = QLabel()
        message.setObjectName("layer-pairs-notice-text")
        message.setWordWrap(True)
        undo = QPushButton(text("design.notice.undo"))
        undo.setObjectName("btn-layer-pairs-undo")
        undo.clicked.connect(self.session.undo)
        line.addWidget(message, 1)
        line.addWidget(undo)
        notice.setVisible(False)
        self._layout.addWidget(table)
        self._layout.addWidget(notice)
        self.helpers.update({"layer-list": table, "layer-pairs-notice": notice, "layer-pairs-notice-text": message})

    def _choose_rotation_mode(self, mode: RotationMode) -> None:
        self._custom = mode == "custom"
        self.session.set_rotation_mode(mode)
        self.refresh_helpers()

    def _selected_pair(self, table: QTableWidget, pair_rows: dict[int, int]) -> int | None:
        """Return the list position of the pair whose copper layer is selected in the layer list, else the first."""
        if not pair_rows:
            return None
        return pair_rows.get(table.currentRow(), min(pair_rows.values()))

    def refresh_helpers(self) -> None:
        """Show the copper count, the stack-up with each copper layer's pair, the rotation helpers and the notice."""
        document = self.session.document
        count = self.helpers.get("copper-count")
        table = self.helpers.get("layer-list")
        if document is None or not isinstance(count, QComboBox) or not isinstance(table, QTableWidget):
            return
        inputs = self.session.stackup_inputs()
        count.setCurrentIndex(count.findData(inputs.copper_count) if inputs.copper_count is not None else -1)
        values = document.draft.values
        spiral = document.draft.topology is TopologyKind.SPIRAL
        pairs = layer_pairs(values)
        pair_of = {name: pair for pair in pairs for name in (pair.layer_in, pair.layer_out)}
        rotation_spec = FIELD_BY_KEY[f"{PAIRS_POINTER}/*/rotation_rad"]
        rows: list[tuple[str, ...]] = []
        pair_rows: dict[int, int] = {}
        position = 0
        while (kind := values.get(f"{STACKUP_POINTER}/{position}/kind")) is not None:
            name = values.get(f"{STACKUP_POINTER}/{position}/name")
            thickness = values.get(f"{STACKUP_POINTER}/{position}/thickness_mm")
            micrometres = f"{thickness * 1000:.4g}" if isinstance(thickness, int | float) else ""
            pair = pair_of.get(name) if kind == "copper" else None
            label = text("layer-list.pair-n", number=pair_number(pair)) if pair is not None else ""
            if kind == "copper" and pair is None:
                label = text("layer-list.no-coil")
            rotation = display_text(rotation_spec, pair.rotation_rad) if pair is not None else ""
            if pair is not None:
                pair_rows[len(rows)] = pair.position
            rows.append((str(name), text(f"layer-list.{kind}"), micrometres, label, rotation))
            position += 1
        selected = table.currentRow()
        table.blockSignals(True)
        table.setRowCount(len(rows))
        for r, cells in enumerate(rows):
            for c, cell in enumerate(cells):
                table.setItem(r, c, QTableWidgetItem(cell))
        if 0 <= selected < len(rows):
            table.selectRow(selected)
        table.blockSignals(False)
        fit_rows(table)
        for c, column in enumerate(LAYER_COLUMNS):
            table.setColumnHidden(c, column in PAIR_COLUMNS and not spiral)
        self._show_rotation(table, pair_rows)
        notice, message = self.helpers["layer-pairs-notice"], self.helpers["layer-pairs-notice-text"]
        assert isinstance(message, QLabel)
        message.setText(self.session.pairs_notice.value or "")
        notice.setVisible(self.session.pairs_notice.value is not None)

    def _show_rotation(self, table: QTableWidget, pair_rows: dict[int, int]) -> None:
        mode, mode_row, rotation = (
            self.helpers.get(n) for n in ("param-rotation-mode", "param-rotation-mode-row", ROTATION_WIDGET)
        )
        document = self.session.document
        if (
            not isinstance(mode, Segment)
            or not isinstance(rotation, FieldEditor)
            or mode_row is None
            or document is None
        ):
            return
        values = document.draft.values
        read = rotation_mode(values)
        shown = "custom" if self._custom or read == "custom" else read
        mode.show_value(shown)
        mode.buttons["alternate"].setEnabled(alternate_rotation_rad(values) is not None)
        mode_row.setVisible(read is not None)
        pair = self._selected_pair(table, pair_rows)
        if pair is not None:
            row = self.session.item_row(ROTATION_WIDGET, f"{PAIRS_POINTER}/{pair}/rotation_rad")
            assert row is not None
            rotation.show_row(row, document.draft.topology.value)
        rotation.setVisible(shown == "custom" and pair is not None)
