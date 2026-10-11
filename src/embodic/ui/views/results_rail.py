"""The key results rail (``results-rail``): the Inputs and DRC verdict cards, then full result cards for Ke and R_ph.

The verdict cards are ``rail-inputs`` and ``rail-drc`` (screens.md section 6.1). The key cards keep the objectNames
of the U-M4b summary strip: ``sum-ke``, ``sum-r-phase`` and their ``-title``, ``-value``, ``-badge`` and ``-asm`` parts.
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from embodic.results import Registry
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.viewmodels.results import ResultsViewModel, StatusCard
from embodic.ui.views.results_view import ResultCard
from embodic.ui.views.status_badge import repolish
from embodic.ui.views.style import themed_icon

# Rail card name and the AnalysisResult field it shows.
KEY_CARDS: dict[str, str] = {"sum-ke": "ke_line_peak_v_s_per_rad", "sum-r-phase": "resistance_phase_operating_ohm"}
CHECK_CARDS = ("rail-inputs", "rail-drc")
# Check state to the glyph file and the `state` value the style sheet colours (a check that did not run is a warning).
GLYPHS = {"pass": ("check-pass", "pass"), "fail": ("check-fail", "fail"), "not-run": ("check-warn", "warn")}
GLYPH_PX = 16


class CheckCard(QFrame):
    """A verdict cell: title, then the check glyph and the word of the state."""

    def __init__(self, key: str) -> None:
        super().__init__()
        self.setObjectName(key)
        self.setProperty("class", "result-card")
        self.title = QLabel()
        self.title.setObjectName(f"{key}-title")
        self.icon = QLabel()
        self.icon.setObjectName(f"{key}-icon")
        self.value = QLabel()
        self.value.setObjectName(f"{key}-value")
        self.value.setProperty("class", "check-state")
        self.line = QHBoxLayout()
        self.line.addWidget(self.icon)
        self.line.addWidget(self.value)
        self.line.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(self.line)

    def show_card(self, card: StatusCard, tokens: ThemeTokens) -> None:
        """Show a verdict: glyph and word of the check state."""
        stem, qss_state = GLYPHS[card.state]
        self.title.setText(card.title)
        self.value.setText(card.word)
        self.value.setProperty("state", qss_state)
        repolish(self.value)
        icon = themed_icon(stem, tokens)
        self.icon.setVisible(icon is not None)
        if icon is not None:
            self.icon.setPixmap(icon.pixmap(GLYPH_PX, GLYPH_PX))


class ResultsRail(QWidget):
    """The rail; ``show_drc`` asks the window to open the DRC tab."""

    show_drc = Signal()
    open_equation = Signal(str)

    def __init__(self, vm: ResultsViewModel, registry: Registry) -> None:
        super().__init__()
        self.setObjectName("results-rail")
        self.vm = vm
        layout = self.body = QVBoxLayout(self)
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
        self.checks["rail-drc"].line.addWidget(self.drc_link)
        self.cards = {key: ResultCard(key, key, registry, vm.copy_trace) for key in KEY_CARDS}
        for card in self.cards.values():
            card.open_equation.connect(self.open_equation)
        for widget in (*self.checks.values(), *self.cards.values()):
            layout.addWidget(widget)

    def show_cards(self, cards: tuple[StatusCard, ...] | None, tokens: ThemeTokens, *, stale: bool) -> None:
        """Show the verdicts and the key cards of the outcome on screen; None shows the empty sentence."""
        self.empty.setVisible(cards is None)
        shown = {card.key: card for card in cards or ()}
        for key, check in self.checks.items():
            check.setVisible(key in shown)
            if key in shown:
                check.show_card(shown[key], tokens)
        drc = shown.get("rail-drc")
        self.drc_link.setVisible(drc is not None and drc.state == "fail")
        for card in self.cards.values():
            card.setVisible(drc is not None)
        if drc is None:
            return
        for key, quantity in KEY_CARDS.items():
            try:
                row = self.vm.row(quantity)
            except KeyError:
                self.cards[key].setVisible(False)
                continue
            self.cards[key].show_row(row, tokens, stale=stale)
