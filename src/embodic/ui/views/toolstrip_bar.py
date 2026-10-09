"""The MATLAB-style toolstrip: one tab per ToolstripTab, one captioned section per group, one button per action."""

from collections.abc import Callable, Mapping

from PySide6.QtCore import QEvent, QObject, QRect, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QTabBar,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from embodic.model.vocabulary import Phase
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.toolstrip import TOOLSTRIP, ToolstripAction, ToolstripTab
from embodic.ui.viewmodels.appearance import PhaseRenderMode
from embodic.ui.views.style import themed_icon

# None marks a command a later build implements: its button stays visible, disabled, with the reason.
CommandTable = Mapping[str, Callable[[], None] | None]

SWATCH_PX = 16
SWATCH_BORDER_PX = 2

_MOVE_KEYS = {Qt.Key.Key_Left: -1, Qt.Key.Key_Right: 1, Qt.Key.Key_Up: -1, Qt.Key.Key_Down: 1}


class UnknownCommandError(RuntimeError):
    """A TOOLSTRIP row names a command no view-model offers (a startup error, interfaces.md section 11)."""


def tooltip(action: ToolstripAction, available: bool) -> str:
    """Return "Label (Shortcut). Sentence." and, when unavailable, the reason."""
    label = text(f"{action.id}.label")
    head = f"{label} ({action.shortcut})." if action.shortcut else f"{label}."
    sentence = text(f"{action.id}.tooltip") if available else text("toolstrip.unavailable.reason")
    return f"{head} {sentence}"


def board_swatch(letter: Phase, tokens: ThemeTokens, mode: PhaseRenderMode) -> QIcon:
    """Return the swatch of a board item: the phase letter in ink on a surface square edged in the phase colour.

    The letter carries the meaning; the edge repeats it in colour, or in the phase's grey in greyscale mode (D-011).
    """
    style = tokens.phase_style(letter)
    edge = QColor(style.colour_hex if mode is PhaseRenderMode.COLOUR else style.grey_hex)
    pixmap = QPixmap(SWATCH_PX, SWATCH_PX)
    pixmap.fill(QColor(tokens.colours["surface"]))
    painter = QPainter(pixmap)
    painter.setPen(QPen(edge, 2 * SWATCH_BORDER_PX))
    painter.drawRect(0, 0, SWATCH_PX - 1, SWATCH_PX - 1)
    painter.setPen(QColor(tokens.colours["text-1"]))
    painter.drawText(QRect(0, 0, SWATCH_PX, SWATCH_PX), Qt.AlignmentFlag.AlignCenter, letter.value)
    painter.end()
    return QIcon(pixmap)


class _ArrowKeys(QObject):
    """Moves focus between the enabled buttons of one tab with the arrow keys, Home and End."""

    def __init__(self, buttons: list[QToolButton]) -> None:
        super().__init__()
        self._buttons = buttons

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 (Qt override)
        if event.type() != QEvent.Type.KeyPress or watched not in self._buttons:
            return False
        key = event.key()  # type: ignore[attr-defined]
        enabled = [b for b in self._buttons if b.isEnabled()]
        if key in _MOVE_KEYS and watched in enabled:
            enabled[(enabled.index(watched) + _MOVE_KEYS[key]) % len(enabled)].setFocus(Qt.FocusReason.TabFocusReason)
            return True
        if key in (Qt.Key.Key_Home, Qt.Key.Key_End) and enabled:
            enabled[0 if key == Qt.Key.Key_Home else -1].setFocus(Qt.FocusReason.TabFocusReason)
            return True
        return False


class ToolstripBar(QToolBar):
    """The toolstrip; every TOOLSTRIP row becomes a QAction (shortcut, command) and a QToolButton (objectName = id).

    The View tab also holds the board picker (screens.md section 4.1). It is a view choice, not an action, so it has
    no TOOLSTRIP row.
    """

    board_selected = Signal(object)  # int index of the board, or None for "All boards"

    def __init__(self, commands: CommandTable, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        unknown = sorted({a.command for a in TOOLSTRIP} - set(commands))
        if unknown:
            raise UnknownCommandError(f"TOOLSTRIP commands without a view-model command: {unknown}")
        self.setObjectName("toolstrip")
        self.setMovable(False)
        self.setFloatable(False)
        self.actions_by_id: dict[str, QAction] = {}
        self.buttons: dict[str, QToolButton] = {}
        self._filters: list[_ArrowKeys] = []
        self.board_picker = QComboBox()
        self._offered: tuple[tuple[Phase, ...], str, PhaseRenderMode] | None = None
        self.board_section = QFrame()
        self.tabs = QTabBar()
        self.tabs.setObjectName("toolstrip-tabs")
        self.tabs.setExpanding(False)
        self.pages = QStackedWidget()
        for tab in ToolstripTab:
            self.tabs.addTab(text(f"toolstrip.tab-{tab.value}.label"))
            self.pages.addWidget(self._page(tab, commands))
        self.tabs.currentChanged.connect(self.pages.setCurrentIndex)
        band = QWidget()
        layout = QVBoxLayout(band)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.tabs)
        layout.addWidget(self.pages)
        self.addWidget(band)

    def _action(self, row: ToolstripAction, command: Callable[[], None] | None) -> QAction:
        action = QAction(text(f"{row.id}.label"), self)
        action.setObjectName(row.id)
        action.setToolTip(tooltip(row, command is not None))
        action.setEnabled(command is not None)
        if row.shortcut:
            action.setShortcut(QKeySequence(row.shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        if command is not None:
            action.triggered.connect(command)
        self.actions_by_id[row.id] = action
        return action

    def _button(self, row: ToolstripAction, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setObjectName(row.id)
        button.setProperty("class", "ts-large")
        button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        button.setIconSize(QSize(24, 24))
        button.setAccessibleName(text(f"{row.id}.label"))
        button.setAccessibleDescription(action.toolTip())
        self.buttons[row.id] = button
        return button

    def _page(self, tab: ToolstripTab, commands: CommandTable) -> QWidget:
        page = QWidget()
        row_layout = QHBoxLayout(page)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        groups: dict[str, QHBoxLayout] = {}
        page_buttons: list[QToolButton] = []
        for row in (a for a in TOOLSTRIP if a.tab is tab):
            if row.group not in groups:
                section = QFrame()
                section.setProperty("class", "ts-section")
                section.setObjectName(f"ts-section-{row.group}")
                column = QVBoxLayout(section)
                column.setContentsMargins(0, 0, 0, 0)
                groups[row.group] = QHBoxLayout()
                column.addLayout(groups[row.group])
                caption = QLabel(text(f"toolstrip.group-{row.group}.label"))
                caption.setProperty("class", "ts-caption")
                caption.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                column.addWidget(caption)
                row_layout.addWidget(section)
            button = self._button(row, self._action(row, commands[row.command]))
            groups[row.group].addWidget(button)
            page_buttons.append(button)
        if tab is ToolstripTab.VIEW:
            row_layout.addWidget(self._board_section())
        row_layout.addStretch(1)
        arrows = _ArrowKeys(page_buttons)
        for button in page_buttons:
            button.installEventFilter(arrows)
        self._filters.append(arrows)
        return page

    def _board_section(self) -> QFrame:
        section = self.board_section
        section.setProperty("class", "ts-section")
        section.setObjectName("ts-section-board")
        column = QVBoxLayout(section)
        column.setContentsMargins(0, 0, 0, 0)
        picker = self.board_picker
        picker.setObjectName("board-picker")
        picker.setAccessibleName(text("shell.board-picker.accessible"))
        picker.setToolTip(text("shell.board-picker.tooltip"))
        picker.setIconSize(QSize(SWATCH_PX, SWATCH_PX))
        picker.currentIndexChanged.connect(lambda _: self.board_selected.emit(picker.currentData()))
        caption = QLabel(text("toolstrip.group-board.label"))
        caption.setProperty("class", "ts-caption")
        caption.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        column.addWidget(picker)
        column.addWidget(caption)
        section.setVisible(False)
        return section

    def show_boards(
        self, letters: tuple[Phase, ...], choice: int | None, tokens: ThemeTokens, mode: PhaseRenderMode
    ) -> None:
        """Offer "All boards" and one item per board letter, or hide the picker when the design has one board."""
        picker = self.board_picker
        picker.blockSignals(True)
        offered = (letters, tokens.name, mode)
        if offered != self._offered:
            self._offered = offered
            picker.clear()
            picker.addItem(text("shell.board-picker.all"), None)
            for index, letter in enumerate(letters):
                label = text("shell.board-picker.item", letter=letter.value)
                picker.addItem(board_swatch(letter, tokens, mode), label, index)
        picker.setCurrentIndex(0 if choice is None else choice + 1)
        picker.blockSignals(False)
        self.board_section.setVisible(bool(letters))

    def show_tab(self, tab: ToolstripTab) -> None:
        """Bring one tab to the front."""
        self.tabs.setCurrentIndex(list(ToolstripTab).index(tab))

    def apply_theme(self, tokens: ThemeTokens) -> None:
        """Redraw every icon in the theme's colours; a button whose icon file is missing shows its label only."""
        for row in TOOLSTRIP:
            icon = themed_icon(row.icon, tokens)
            button = self.buttons[row.id]
            if icon is None:
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
                continue
            self.actions_by_id[row.id].setIcon(icon)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
