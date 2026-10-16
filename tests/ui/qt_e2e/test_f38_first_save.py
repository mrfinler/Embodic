"""F38-1 (V3-01 union ruling): the first Save after an example opens a Save As dialog and spares the packaged file."""

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog

from embodic.io.examples import EXAMPLE_SUFFIX, examples_dir

from .gallery import open_example_from_gallery
from .support import run_action

EXAMPLE_ID = "spiral_12c10p_d08"


@pytest.mark.req("REQ-F-38")
def test_f38_1_first_save_after_an_example_opens_save_as_and_leaves_the_packaged_file_alone(
    window, wait_drawn, qtbot, tmp_path
):
    """Catches Save writing over the packaged example, or Save without a dialog."""
    packaged = examples_dir() / f"{EXAMPLE_ID}{EXAMPLE_SUFFIX}"
    before = packaged.read_bytes()
    open_example_from_gallery(qtbot, window, wait_drawn, EXAMPLE_ID)
    chosen = tmp_path / "mine.embodic.json"
    seen: dict[str, object] = {}

    def answer() -> None:
        dialog = QApplication.activeModalWidget()
        if isinstance(dialog, QFileDialog):
            seen["accept_mode"] = dialog.acceptMode()
            seen["modal"] = dialog.isModal()
            dialog.selectFile(str(chosen))
            dialog.accept()

    QTimer.singleShot(0, answer)
    run_action(qtbot, window, "act-save")

    assert seen == {"accept_mode": QFileDialog.AcceptMode.AcceptSave, "modal": True}
    assert packaged.read_bytes() == before
    assert chosen.is_file()
