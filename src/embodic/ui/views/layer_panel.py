"""The Layers tab (`tab-layers`, screens.md section 4): copper count, vias, the stack-up and the spiral layer pairs."""

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from embodic.model.fields import FIELD_BY_KEY, FieldGroup
from embodic.model.vocabulary import TopologyKind
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import (
    PAIRS_POINTER,
    ROTATION_MODES,
    STACKUP_POINTER,
    DesignSession,
    LayerPair,
    RotationMode,
    alternate_rotation_rad,
    display_text,
    layer_pairs,
    pair_number,
    rotation_mode,
    series_groups,
)
from embodic.ui.views.coil_panel import FieldEditor, FieldPanel, Segment, fit_rows, fit_width, label_above, repolish
from embodic.ui.views.widgets import table_widget

COPPER_COUNTS = (2, 4, 6, 8)
LAYER_COLUMNS = ("layer", "kind", "thickness")
PAIR_COLUMNS = ("pair", "layers", "rotation")
ROTATION_COLUMN = PAIR_COLUMNS.index("rotation")
ROTATION_WIDGET = "param-pair-rotation"


@dataclass(frozen=True, slots=True)
class PairSlot:
    """One `pair-list` row: a pair the copper count makes, listed in the draft or deleted (``pair`` is None)."""

    number: int
    layer_in: str
    layer_out: str
    pair: LayerPair | None


def pair_slots(copper: list[str], pairs: tuple[LayerPair, ...]) -> list[PairSlot]:
    """Return one slot per pair of copper layers 2k and 2k + 1 in stack order (D-024), deleted pairs included."""
    by_layers = {(pair.layer_in, pair.layer_out): pair for pair in pairs}
    slots = []
    for k in range(len(copper) // 2):
        names = (copper[2 * k], copper[2 * k + 1])
        pair = by_layers.get(names)
        slots.append(PairSlot(pair_number(pair) if pair else k + 1, *names, pair))
    return slots


def _table(name: str, columns: tuple[str, ...]) -> QTableWidget:
    table = table_widget(0, len(columns))
    table.setObjectName(name)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setHorizontalHeaderLabels([text(f"{name}.{column}") for column in columns])
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.verticalHeader().setVisible(False)
    return table


class LayerPanel(FieldPanel):
    """Layer rows from the field table, the copper count, the pair rotation helpers, the layer list and its notice."""

    def __init__(self, session: DesignSession) -> None:
        super().__init__("tab-layers", session)
        self._custom = False  # Custom chosen while the rotations still read as None or Alternate
        self._slots: list[PairSlot] = []

    def _rebuild(self, topology: str | None) -> None:
        self._custom = False
        super()._rebuild(topology)

    def add_helpers(self, group: FieldGroup, form: QFormLayout) -> None:
        """Add the copper count before the first layer row, and for spiral the pair rotation mode and field."""
        if group is not FieldGroup.LAYERS or "copper-count" in self.helpers:
            return
        wave = self._building is TopologyKind.WAVE
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
        form.addRow(label_above(text(f"{name}.label"), count))
        self.helpers["copper-count"] = count
        if self._building is TopologyKind.SPIRAL:
            mode = Segment(
                "param-rotation-mode",
                tuple(ROTATION_MODES),
                lambda c: self._choose_rotation_mode(ROTATION_MODES[str(c)]),
            )
            mode_row = label_above(text("param-rotation-mode.label"), mode)
            mode_row.setObjectName("param-rotation-mode-row")
            rotation = FieldEditor(ROTATION_WIDGET, FIELD_BY_KEY[f"{PAIRS_POINTER}/*/rotation_rad"], self.session)
            form.addRow(mode_row)
            form.addRow(rotation)
            self.helpers.update({"param-rotation-mode": mode, "param-rotation-mode-row": mode_row})
            self.helpers[ROTATION_WIDGET] = rotation

    def build(self) -> None:
        """Add the rows, the stack-up, the spiral pair list and the notice of what the last edit did to the pairs."""
        super().build()
        layers = _table("layer-list", LAYER_COLUMNS)
        pairs = _table("pair-list", PAIR_COLUMNS)
        pairs.itemSelectionChanged.connect(self.refresh_helpers)
        pairs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        pairs.customContextMenuRequested.connect(lambda pos: self._series_menu(pairs).popup(pairs.mapToGlobal(pos)))
        delete = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), pairs)
        delete.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete.activated.connect(lambda: self.delete_selected_pair(pairs))
        caption = QLabel(text("pair-list.caption"))
        caption.setBuddy(pairs)
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
        for widget in (layers, caption, pairs, notice):
            self._layout.addWidget(widget)
        self.helpers.update(
            {
                "layer-list": layers,
                "pair-list": pairs,
                "pair-list-caption": caption,
                "layer-pairs-notice": notice,
                "layer-pairs-notice-text": message,
            }
        )

    def delete_selected_pair(self, table: QTableWidget) -> None:
        """Delete: remove the selected pair, not its copper layers (screens.md section 4)."""
        slot = self._slot(table)
        if slot is not None and slot.pair is not None:
            self.session.delete_pair(slot.pair.position)

    def _slot(self, table: QTableWidget) -> PairSlot | None:
        return self._slots[table.currentRow()] if 0 <= table.currentRow() < len(self._slots) else None

    def _series_menu(self, table: QTableWidget) -> QMenu:
        """Return the row menu that sets the series group of the selected pair (`/winding/layers/series_groups`)."""
        menu = QMenu(text("pair-list.series-group"), table)
        menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        slot, document = self._slot(table), self.session.document
        if slot is None or slot.pair is None or document is None or not isinstance(slot.pair.index, int):
            return menu
        index = slot.pair.index
        number_of = {p.index: pair_number(p) for p in layer_pairs(document.draft.values)}
        menu.addSection(text("pair-list.series-group"))
        for position, group in enumerate(series_groups(document.draft.values)):
            others = [number_of.get(i, i + 1) for i in group if i != index]
            if not others:
                continue
            key = "pair-list.join-group" if len(others) == 1 else "pair-list.join-groups"
            action = menu.addAction(text(key, numbers=", ".join(map(str, others))))
            action.setCheckable(True)
            action.setChecked(index in group)
            action.triggered.connect(lambda _=False, p=position: self.session.set_series_group(index, p))
        alone = menu.addAction(text("pair-list.own-group"))
        alone.setCheckable(True)
        alone.setChecked([index] in series_groups(document.draft.values))
        alone.triggered.connect(lambda: self.session.set_series_group(index, None))
        return menu

    def _choose_rotation_mode(self, mode: RotationMode) -> None:
        self._custom = mode == "custom"
        self.session.set_rotation_mode(mode)
        self.refresh_helpers()

    def _selected_pair(self, table: QTableWidget) -> int | None:
        """Return the list position of the pair selected in `pair-list`, else of the first listed pair."""
        slot = self._slot(table)
        if slot is not None and slot.pair is not None:
            return slot.pair.position
        return next((s.pair.position for s in self._slots if s.pair is not None), None)

    def refresh_helpers(self) -> None:
        """Show the copper count, the stack-up, the spiral pairs, the rotation helpers and the notice."""
        document = self.session.document
        count = self.helpers.get("copper-count")
        layers, pairs = self.helpers.get("layer-list"), self.helpers.get("pair-list")
        if document is None or not isinstance(count, QComboBox):
            return
        assert isinstance(layers, QTableWidget) and isinstance(pairs, QTableWidget)
        inputs = self.session.stackup_inputs()
        count.setCurrentIndex(count.findData(inputs.copper_count) if inputs.copper_count is not None else -1)
        values = document.draft.values
        spiral = document.draft.topology is TopologyKind.SPIRAL
        rows: list[tuple[str, ...]] = []
        copper: list[str] = []
        position = 0
        while (kind := values.get(f"{STACKUP_POINTER}/{position}/kind")) is not None:
            name = str(values.get(f"{STACKUP_POINTER}/{position}/name"))
            thickness = values.get(f"{STACKUP_POINTER}/{position}/thickness_mm")
            micrometres = f"{thickness * 1000:.4g}" if isinstance(thickness, int | float) else ""
            rows.append((name, text(f"layer-list.{kind}"), micrometres))
            copper += [name] if kind == "copper" else []
            position += 1
        unpaired = copper[-1] if spiral and len(copper) % 2 else None
        _fill(layers, rows, {r: text("layer-list.unpaired") for r, row in enumerate(rows) if row[0] == unpaired})
        self._slots = pair_slots(copper, layer_pairs(values)) if spiral else []
        self._show_pairs(pairs)
        for widget in (pairs, self.helpers["pair-list-caption"]):
            widget.setVisible(spiral)
        self._show_rotation(pairs)
        notice, message = self.helpers["layer-pairs-notice"], self.helpers["layer-pairs-notice-text"]
        assert isinstance(message, QLabel)
        message.setText(self.session.pairs_notice.value or "")
        notice.setVisible(self.session.pairs_notice.value is not None)

    def _show_pairs(self, table: QTableWidget) -> None:
        """One row per pair slot; a deleted pair stays dimmed with "No coil"; the rotation cell carries its chip."""
        spec = FIELD_BY_KEY[f"{PAIRS_POINTER}/*/rotation_rad"]
        rows: list[tuple[str, ...]] = []
        tips: dict[int, str] = {}
        for r, slot in enumerate(self._slots):
            rotation = display_text(spec, slot.pair.rotation_rad) if slot.pair else text("layer-list.no-coil")
            rows.append(
                (
                    str(slot.number),
                    text("pair-list.layers-text", layer_in=slot.layer_in, layer_out=slot.layer_out),
                    rotation,
                )
            )
            tips[r] = text("layer-list.joins", number=slot.number, layer_in=slot.layer_in, layer_out=slot.layer_out)
        _fill(table, rows, tips)
        for r, slot in enumerate(self._slots):
            if slot.pair is None:
                for c in range(table.columnCount()):
                    item = table.item(r, c)
                    assert item is not None
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                table.removeCellWidget(r, ROTATION_COLUMN)
                continue
            row = self.session.item_row(ROTATION_WIDGET, f"{PAIRS_POINTER}/{slot.pair.position}/rotation_rad")
            chip = None if row is None else row.provenance
            provenance = "" if chip is None else chip.provenance.value
            word = text(f"design.prov.{provenance}") if provenance else ""
            table.setCellWidget(r, ROTATION_COLUMN, _value_with_chip(rows[r][ROTATION_COLUMN], word, provenance))
            cell = table.item(r, ROTATION_COLUMN)
            assert cell is not None
            cell.setText("")
            cell.setData(Qt.ItemDataRole.AccessibleTextRole, f"{rows[r][ROTATION_COLUMN]} {word}")
        fit_rows(table)
        fit_width(table)
        table.horizontalHeader().setStretchLastSection(True)

    def _show_rotation(self, table: QTableWidget) -> None:
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
        pair = self._selected_pair(table)
        if pair is not None:
            row = self.session.item_row(ROTATION_WIDGET, f"{PAIRS_POINTER}/{pair}/rotation_rad")
            assert row is not None
            rotation.show_row(row, document.draft.topology.value)
        rotation.setVisible(shown == "custom" and pair is not None)


def _fill(table: QTableWidget, rows: list[tuple[str, ...]], tips: dict[int, str]) -> None:
    """Show ``rows`` in a read-only table, keep its selection and size it to its rows and the inspector width."""
    selected = table.currentRow()
    table.blockSignals(True)
    table.setRowCount(len(rows))
    for r, cells in enumerate(rows):
        for c, cell in enumerate(cells):
            item = QTableWidgetItem(cell)
            item.setToolTip(tips.get(r, ""))
            table.setItem(r, c, item)
    if 0 <= selected < len(rows):
        table.selectRow(selected)
    table.blockSignals(False)
    fit_rows(table)
    fit_width(table)
    table.horizontalHeader().setStretchLastSection(True)  # ruling j: no empty header cell


def _value_with_chip(value: str, word: str, provenance: str) -> QWidget:
    """Return a rotation cell: the value and its provenance chip, styled per provenance (screens.md section 4)."""
    cell = QWidget()
    line = QHBoxLayout(cell)
    line.setContentsMargins(6, 0, 4, 0)
    line.setSpacing(6)
    shown = QLabel(value)
    chip = QLabel(word)
    chip.setProperty("class", "prov-chip")
    chip.setProperty("provenance", provenance)
    chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
    repolish(chip)
    line.addWidget(shown)
    line.addStretch(1)
    line.addWidget(chip)
    return cell
