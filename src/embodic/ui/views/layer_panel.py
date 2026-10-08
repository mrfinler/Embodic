"""The Layers tab (`tab-layers`, screens.md section 4): copper count, layer pairs, vias and the layer list."""

from PySide6.QtWidgets import QAbstractItemView, QComboBox, QFormLayout, QLabel, QTableWidget, QTableWidgetItem

from embodic.model.fields import FieldGroup
from embodic.model.vocabulary import TopologyKind
from embodic.ui.strings import text
from embodic.ui.viewmodels.session import STACKUP_POINTER, DesignSession
from embodic.ui.views.coil_panel import FieldPanel

COPPER_COUNTS = (2, 4, 6, 8)


class LayerPanel(FieldPanel):
    """Layer rows from the field table, the copper-count input of the stack-up generator and the layer list."""

    def __init__(self, session: DesignSession) -> None:
        super().__init__("tab-layers", session)

    def add_helpers(self, group: FieldGroup, form: QFormLayout) -> None:
        """Add the copper count before the first layer row (param-wave-layers for wave, param-layer-count else)."""
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

    def build(self) -> None:
        """Add the rows, then the read-only layer list."""
        super().build()
        table = QTableWidget(0, 4)
        table.setObjectName("layer-list")
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setHorizontalHeaderLabels(
            [text(f"layer-list.{column}") for column in ("layer", "kind", "thickness", "pair")]
        )
        table.verticalHeader().setVisible(False)
        self._layout.addWidget(table)
        self.helpers["layer-list"] = table

    def refresh_helpers(self) -> None:
        """Show the copper count and the stack-up with the layer pair of each copper layer."""
        document = self.session.document
        count = self.helpers.get("copper-count")
        if document is None or not isinstance(count, QComboBox):
            return
        inputs = self.session.stackup_inputs()
        count.setCurrentIndex(count.findData(inputs.copper_count) if inputs.copper_count is not None else -1)
        table = self.helpers["layer-list"]
        assert isinstance(table, QTableWidget)
        values = document.draft.values
        pair_of = {}
        k = 0
        while f"/winding/layers/pairs/{k}/layer_in" in values:
            for leaf in ("layer_in", "layer_out"):
                pair_of[values[f"/winding/layers/pairs/{k}/{leaf}"]] = text("layer-list.pair-n", number=k + 1)
            k += 1
        rows = []
        position = 0
        while (kind := values.get(f"{STACKUP_POINTER}/{position}/kind")) is not None:
            name = values.get(f"{STACKUP_POINTER}/{position}/name")
            thickness = values.get(f"{STACKUP_POINTER}/{position}/thickness_mm")
            micrometres = f"{thickness * 1000:.4g}" if isinstance(thickness, int | float) else ""
            pair = pair_of.get(name, text("layer-list.no-coil")) if kind == "copper" else ""
            if document.draft.topology is not TopologyKind.SPIRAL:
                pair = ""
            rows.append((str(name), text(f"layer-list.{kind}"), micrometres, pair))
            position += 1
        table.setRowCount(len(rows))
        for r, cells in enumerate(rows):
            for c, cell in enumerate(cells):
                table.setItem(r, c, QTableWidgetItem(cell))
        table.setColumnHidden(3, document.draft.topology is not TopologyKind.SPIRAL)
