"""``dlg-export``: format check boxes, folder, checklist, Run and the list of written files (screens.md section 11)."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from embodic.io.exporters import ExportRefused
from embodic.ui.strings import text
from embodic.ui.theme import ThemeTokens
from embodic.ui.viewmodels.export import FORMAT_OPTIONS, ExportFormat, ExportViewModel, ExportWritten, selection_problem
from embodic.ui.views.dialogs import ExportConfirmDialog
from embodic.ui.views.style import themed_icon

CHECK_ICONS = {"pass": "check-pass", "fail": "check-fail", "warn": "check-warn"}


class ExportDialog(QDialog):
    """The Export dialog; a run with DRC failures goes through ``dlg-export-confirm`` first (UI-29)."""

    def __init__(
        self, vm: ExportViewModel, preset: frozenset[ExportFormat], tokens: ThemeTokens, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("dlg-export")
        self.setWindowTitle(text("export.title"))
        self.vm, self.tokens = vm, tokens
        self.confirm: ExportConfirmDialog | None = None
        self.written: ExportWritten | None = None
        unavailable = vm.unavailable()
        self.boxes: dict[ExportFormat, QCheckBox] = {}
        formats = QVBoxLayout()
        title = QLabel(text("export.formats"))
        title.setProperty("class", "section-title")
        formats.addWidget(title)
        for option in FORMAT_OPTIONS:
            box = QCheckBox(option.label)
            box.setObjectName(option.widget_id)
            reason = unavailable.get(option.choice)
            box.setEnabled(reason is None)
            box.setToolTip(reason or "")
            box.setChecked(reason is None and option.choice in preset)
            box.toggled.connect(self._update_problem)
            self.boxes[option.choice] = box
            formats.addWidget(box)
        self.folder = QLineEdit()
        self.folder.setObjectName("export-folder")
        self.folder.setPlaceholderText(text("export.folder.placeholder"))
        self.folder.textChanged.connect(self._update_problem)
        browse = QToolButton()
        browse.setObjectName("btn-export-browse")
        browse.setText(text("export.folder.browse"))
        browse.clicked.connect(self._browse)
        folder_line = QHBoxLayout()
        folder_line.addWidget(QLabel(text("export.folder")))
        folder_line.addWidget(self.folder, 1)
        folder_line.addWidget(browse)
        checklist_title = QLabel(text("export.checklist"))
        checklist_title.setProperty("class", "section-title")
        self.checklist = QListWidget()
        self.checklist.setObjectName("export-checklist")
        for item in vm.checklist():
            row = QListWidgetItem(item.text)
            icon = themed_icon(CHECK_ICONS[item.state], tokens)
            if icon is not None:
                row.setIcon(icon)
            row.setData(0x0100, item.state)
            self.checklist.addItem(row)
        self.checklist.setMaximumHeight(110)
        self.problem = QLabel()
        self.problem.setObjectName("export-problem")
        self.problem.setProperty("class", "hint")
        self.result = QLabel()
        self.result.setObjectName("export-result")
        self.result.setWordWrap(True)
        self.open_folder = QPushButton(text("export.open-folder"))
        self.open_folder.setObjectName("btn-export-open-folder")
        self.open_folder.setVisible(False)
        self.open_folder.clicked.connect(self._open_folder)
        self.run = QPushButton(text("export.run"))
        self.run.setObjectName("btn-export-run")
        self.run.setProperty("class", "primary")
        self.run.clicked.connect(self.run_clicked)
        close = QPushButton(text("export.close"))
        close.setObjectName("btn-export-close")
        close.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(self.open_folder)
        buttons.addStretch(1)
        buttons.addWidget(close)
        buttons.addWidget(self.run)
        layout = QVBoxLayout(self)
        layout.addLayout(formats)
        layout.addLayout(folder_line)
        layout.addWidget(checklist_title)
        layout.addWidget(self.checklist)
        layout.addWidget(self.problem)
        layout.addWidget(self.result)
        layout.addLayout(buttons)
        self.resize(560, 560)
        self._update_problem()

    def selected(self) -> frozenset[ExportFormat]:
        """Return the checked formats."""
        return frozenset(choice for choice, box in self.boxes.items() if box.isChecked())

    def _update_problem(self) -> None:
        problem = (
            text("export.no-design")
            if self.vm.outcome() is None
            else selection_problem(self.selected(), self.folder.text())
        )
        self.problem.setText(problem or "")
        self.run.setEnabled(problem is None)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, text("export.folder"), self.folder.text())
        if folder:
            self.folder.setText(folder)

    def run_clicked(self) -> None:
        """Run the export; with DRC failures, open the confirmation first (focus on Cancel)."""
        preflight = self.vm.preflight()
        if not preflight.needs_confirmation:
            self._run(confirmed=False)
            return
        outcome = self.vm.outcome()
        total = sum(r.violation_count for r in outcome.drc or ()) if outcome is not None else 0
        self.confirm = ExportConfirmDialog(preflight.failures, total, self)
        self.confirm.accepted.connect(lambda: self._run(confirmed=True))
        self.confirm.open()

    def _run(self, *, confirmed: bool) -> None:
        folder = Path(self.folder.text().strip())
        try:
            result = self.vm.run(self.selected(), folder, confirmed_drc_errors=confirmed)
        except OSError as error:
            self.result.setText(text("export.result.error", reason=error.strerror or str(error)))
            return
        if isinstance(result, ExportRefused):
            reason = "; ".join(issue.message for issue in result.issues[:1])
            self.result.setText(text("export.result.refused", reason=reason))
            return
        self.written = result
        names = "\n".join(path.name for path in result.files)
        self.result.setText(f"{text('export.result.written', folder=result.folder)}\n{names}")
        self.open_folder.setVisible(True)

    def _open_folder(self) -> None:
        if self.written is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.written.folder)))
