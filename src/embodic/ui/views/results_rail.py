"""The key results rail (``results-rail``): design and DRC verdicts, then full result cards for Ke and R_ph.

The objectNames of the U-M4b summary strip stay: ``sum-ok``, ``sum-drc``, ``sum-ke``, ``sum-r-phase`` and their
``-title``, ``-value``, ``-badge`` and ``-asm`` parts.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from embodic.results import Registry
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.viewmodels.outcome import SummaryItem
from embodic.ui.viewmodels.results import ResultsViewModel
from embodic.ui.views.results_view import ResultCard
from embodic.ui.views.status_badge import repolish

# Rail card name and the AnalysisResult field it shows.
KEY_CARDS: dict[str, str] = {"sum-ke": "ke_line_peak_v_s_per_rad", "sum-r-phase": "resistance_phase_operating_ohm"}
CHECK_CARDS = ("sum-ok", "sum-drc")


class CheckCard(QFrame):
    """A verdict cell: title and the check word with its state (pass or fail)."""

    def __init__(self, key: str) -> None:
        super().__init__()
        self.setObjectName(key)
        self.setProperty("class", "result-card")
        self.title = QLabel()
        self.title.setObjectName(f"{key}-title")
        self.value = QLabel()
        self.value.setObjectName(f"{key}-value")
        self.value.setProperty("class", "check-state")
        self.line = QHBoxLayout()
        self.line.addWidget(self.value)
        self.line.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(self.line)

    def show_item(self, item: SummaryItem) -> None:
        """Show a verdict of the summary strip."""
        self.title.setText(item.label)
        self.value.setText(item.value_text)
        self.value.setProperty("state", item.state or "")
        repolish(self.value)


class ResultsRail(QWidget):
    """The rail; ``show_drc`` asks the window to open the DRC tab."""

    show_drc = Signal()
    open_equation = Signal(str)

    def __init__(self, vm: ResultsViewModel, registry: Registry) -> None:
        super().__init__()
        self.setObjectName("results-rail")
        self.vm = vm
        layout = QVBoxLayout(self)
        title = QLabel(text("shell.results-rail.title"))
        title.setProperty("class", "section-title")
        self.empty = QLabel(text("shell.results-rail.empty"))
        self.empty.setObjectName("results-rail-empty")
        self.empty.setWordWrap(True)
        self.empty.setProperty("class", "hint")
        layout.addWidget(title)
        layout.addWidget(self.empty)
        self.checks = {key: CheckCard(key) for key in CHECK_CARDS}
        self.drc_link = QPushButton(text("results.tab-drc.label"))
        self.drc_link.setObjectName("btn-rail-drc")
        self.drc_link.setFlat(True)
        self.drc_link.clicked.connect(self.show_drc)
        self.checks["sum-drc"].line.addWidget(self.drc_link)
        self.cards = {key: ResultCard(key, key, registry, vm.copy_trace) for key in KEY_CARDS}
        for card in self.cards.values():
            card.open_equation.connect(self.open_equation)
        for widget in (*self.checks.values(), *self.cards.values()):
            layout.addWidget(widget)

    def show_summary(self, summary: tuple[SummaryItem, ...] | None, tokens: ThemeTokens, *, stale: bool) -> None:
        """Show the verdicts and the key cards of the outcome on screen; None shows the empty sentence."""
        self.empty.setVisible(summary is None)
        for widget in (*self.checks.values(), *self.cards.values()):
            widget.setVisible(summary is not None)
        if summary is None:
            return
        for item in summary:
            if item.key in self.checks:
                self.checks[item.key].show_item(item)
        drc = next(i for i in summary if i.key == "sum-drc")
        self.drc_link.setVisible(drc.state == "fail")
        for key, quantity in KEY_CARDS.items():
            try:
                row = self.vm.row(quantity)
            except KeyError:
                self.cards[key].setVisible(False)
                continue
            self.cards[key].show_row(row, tokens, stale=stale)
